import json
from collections.abc import Iterable
from typing import ClassVar
from urllib.parse import urlsplit

from starlette.types import ASGIApp, Message, Receive, Scope, Send


class TrustedOriginMiddleware:
    """Reject unsafe browser requests from origins outside the allowlist."""

    _UNSAFE_METHODS: ClassVar[frozenset[str]] = frozenset(
        {"POST", "PUT", "PATCH", "DELETE"}
    )

    def __init__(self, app: ASGIApp, allowed_origins: Iterable[str]) -> None:
        self.app = app
        self.allowed_origins = frozenset(allowed_origins)

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        if scope["type"] != "http" or scope["method"] not in self._UNSAFE_METHODS:
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        origin = headers.get(b"origin")
        referer = headers.get(b"referer")
        fetch_site = headers.get(b"sec-fetch-site", b"").lower()

        request_origin = (
            origin.decode("latin-1") if origin is not None else None
        )
        if request_origin is None and referer is not None:
            parsed_referer = urlsplit(referer.decode("latin-1"))
            if parsed_referer.scheme and parsed_referer.netloc:
                request_origin = (
                    f"{parsed_referer.scheme}://{parsed_referer.netloc}"
                )

        is_untrusted = (
            request_origin is not None
            and request_origin not in self.allowed_origins
        )
        is_untrusted_fetch_site = (
            fetch_site in {b"cross-site", b"same-site"}
            and request_origin not in self.allowed_origins
        )
        if is_untrusted or is_untrusted_fetch_site:
            await self._reject(send)
            return

        await self.app(scope, receive, send)

    @staticmethod
    async def _reject(send: Send) -> None:
        body = json.dumps(
            {"detail": "Request origin is not allowed."}
        ).encode("utf-8")
        response_start: Message = {
            "type": "http.response.start",
            "status": 403,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode("ascii")),
            ],
        }
        await send(response_start)
        await send({"type": "http.response.body", "body": body})
