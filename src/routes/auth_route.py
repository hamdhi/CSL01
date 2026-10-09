import base64
import hashlib
import hmac
import logging
import secrets
from typing import Annotated, Literal, TypedDict
from urllib.parse import urlencode, urlsplit
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse, RedirectResponse

from src.core.config import settings
from src.core.security import (
    AuthenticatedPrincipal,
    get_current_principal,
)
from src.schemas.auth_schema import (
    AuthenticatedUserSchema,
    AuthSessionResponseSchema,
    PasswordLoginRequestSchema,
    PasswordUpdateRequestSchema,
    RefreshTokenRequestSchema,
)
from src.schemas.standerd_response_schema import StandardResponseSchema
from src.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])
ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"
OAUTH_STATE_COOKIE = "google_oauth_state"
OAUTH_VERIFIER_COOKIE = "google_oauth_verifier"
OAUTH_NONCE_COOKIE = "google_oauth_nonce"
OAUTH_RETRY_COOKIE = "google_oauth_retry"
# Scope the short-lived OAuth cookies to the whole site so they survive the
# Google round-trip regardless of proxy/path quirks (they are httponly and
# expire within minutes). Keeping a single constant means both set and delete
# paths stay in sync.
OAUTH_COOKIE_PATH = "/"
OAUTH_STATE_MAX_AGE = 900


class OAuthCookieOptions(TypedDict):
    httponly: bool
    secure: bool
    samesite: Literal["lax"]
    max_age: int
    path: str


logger = logging.getLogger(__name__)


@router.post(
    "/login",
    response_model=StandardResponseSchema[AuthSessionResponseSchema],
)
async def login(
    request: PasswordLoginRequestSchema,
    _service: Annotated[AuthService, Depends()],
    response: Response,
):
    result = _service.login_with_password(
        str(request.email), request.password
    )
    _set_auth_cookies(response, result)
    return StandardResponseSchema(
        data=_session_response(result),
        message="Login successful",
        status_code=status.HTTP_200_OK,
    )


@router.get(
    "/google/start",
    summary="Start Google sign-in",
    description=(
        "Open the [Google sign-in page]("
        f"{settings.GOOGLE_REDIRECT_URI.removesuffix('/auth/google/callback')}"
        "/auth/google/start) directly in your browser. Do not use **Try it out**: "
        "this endpoint redirects to Google, and Swagger's API request cannot "
        "follow that cross-site redirect because the response is not available "
        "to browser JavaScript. Use the same host consistently for Swagger and "
        "sign-in (for local development, use `localhost`, not `127.0.0.1`)."
    ),
)
def start_google_login(retry: bool = False):
    _validate_google_configuration()
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode("ascii")).digest()
    ).rstrip(b"=").decode("ascii")
    query = urlencode(
        {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "nonce": nonce,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
    )
    response = RedirectResponse(
        f"https://accounts.google.com/o/oauth2/v2/auth?{query}",
        status_code=status.HTTP_302_FOUND,
    )
    cookie_options = _oauth_cookie_options()
    response.set_cookie(
        OAUTH_STATE_COOKIE, state, **cookie_options
    )
    response.set_cookie(
        OAUTH_VERIFIER_COOKIE, code_verifier, **cookie_options
    )
    response.set_cookie(
        OAUTH_NONCE_COOKIE, nonce, **cookie_options
    )
    if retry:
        response.set_cookie(
            OAUTH_RETRY_COOKIE,
            "1",
            **cookie_options,
        )
    else:
        _clear_oauth_retry_cookie(response)
    return response


@router.get("/google/callback", include_in_schema=True)
def google_callback(
    request: Request,
    _service: Annotated[AuthService, Depends()],
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
):
    _validate_google_configuration()
    if error is not None or code is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google sign-in was cancelled or denied.",
        )
    expected_state = request.cookies.get(OAUTH_STATE_COOKIE)
    code_verifier = request.cookies.get(OAUTH_VERIFIER_COOKIE)
    nonce = request.cookies.get(OAUTH_NONCE_COOKIE)
    if (
        state is None
        or expected_state is None
        or not hmac.compare_digest(state, expected_state)
        or code_verifier is None
        or nonce is None
    ):
        logger.warning(
            "Google OAuth state check failed: host=%s, state_present=%s, "
            "expected_state_present=%s, states_match=%s, "
            "code_verifier_present=%s, nonce_present=%s. "
            "If expected_state_present is False the state cookie was not "
            "returned to the callback (often a host mismatch such as starting "
            "at 127.0.0.1 while GOOGLE_REDIRECT_URI uses localhost, or the "
            "cookie expired).",
            request.url.hostname,
            state is not None,
            expected_state is not None,
            expected_state is not None
            and state is not None
            and hmac.compare_digest(state, expected_state),
            code_verifier is not None,
            nonce is not None,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Google sign-in state is invalid or expired. Please retry, "
                "opening the sign-in URL directly in your browser and using "
                "the same host (localhost) all the way through. If this keeps "
                "happening, check the server log for the state check details."
            ),
        )
    try:
        result = _service.login_with_google_code(code, code_verifier, nonce)
    except HTTPException as auth_error:
        if (
            auth_error.status_code == status.HTTP_401_UNAUTHORIZED
            and auth_error.detail
            == (
                "Google returned an ID token that failed verification. "
                "Please start sign-in again. If this repeats, check the "
                "application server log for the verification reason."
            )
        ):
            if request.cookies.get(OAUTH_RETRY_COOKIE) != "1":
                response = RedirectResponse(
                    f"{_origin(settings.GOOGLE_REDIRECT_URI)}"
                    "/auth/google/start?retry=true",
                    status_code=status.HTTP_303_SEE_OTHER,
                )
                _clear_oauth_cookies(response)
                return response
            response = JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": (
                        "Google could not verify the sign-in after a retry. "
                        "Please start sign-in again. If this keeps happening, "
                        "check the application server log for the verification "
                        "reason, then confirm the Google OAuth client ID and "
                        "server clock."
                    )
                },
            )
            _clear_oauth_cookies(response)
            _clear_oauth_retry_cookie(response)
            return response
        raise
    response = RedirectResponse(
        settings.FRONTEND_URL,
        status_code=status.HTTP_303_SEE_OTHER,
    )
    _set_auth_cookies(response, result)
    _clear_oauth_cookies(response)
    _clear_oauth_retry_cookie(response)
    return response


@router.post(
    "/refresh",
    response_model=StandardResponseSchema[AuthSessionResponseSchema],
)
async def refresh(
    request: Request,
    response: Response,
    _service: Annotated[AuthService, Depends()],
    token_request: RefreshTokenRequestSchema | None = None,
):
    refresh_token = (
        token_request.refresh_token
        if token_request is not None
        else request.cookies.get(REFRESH_COOKIE)
    )
    if refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is required.",
        )
    result = _service.refresh(refresh_token)
    _set_auth_cookies(response, result)
    return StandardResponseSchema(
        data=_session_response(result),
        message="Tokens refreshed successfully",
        status_code=status.HTTP_200_OK,
    )


@router.post("/logout", response_model=StandardResponseSchema[None])
async def logout(
    principal: Annotated[
        AuthenticatedPrincipal, Depends(get_current_principal)
    ],
    _service: Annotated[AuthService, Depends()],
    response: Response,
):
    if principal.session_id is not None:
        _service.logout(principal.session_id)
    _clear_auth_cookies(response)
    return StandardResponseSchema(
        data=None,
        message="Logged out successfully",
        status_code=status.HTTP_200_OK,
    )


@router.get(
    "/me",
    response_model=StandardResponseSchema[AuthenticatedUserSchema],
)
async def current_user(
    principal: Annotated[
        AuthenticatedPrincipal, Depends(get_current_principal)
    ],
):
    return StandardResponseSchema(
        data=AuthenticatedUserSchema(
            account_id=principal.account_id,
            actor_id=principal.actor_id,
            actor_type=principal.actor_type,
            role=principal.role,
        ),
        message="Authenticated user",
        status_code=status.HTTP_200_OK,
    )


@router.put("/password", response_model=StandardResponseSchema[None])
async def update_password(
    request: PasswordUpdateRequestSchema,
    principal: Annotated[
        AuthenticatedPrincipal, Depends(get_current_principal)
    ],
    _service: Annotated[AuthService, Depends()],
):
    _service.update_password(principal.account_id, request.password)
    return StandardResponseSchema(
        data=None,
        message="Password updated successfully",
        status_code=status.HTTP_200_OK,
    )


def _validate_google_configuration() -> None:
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth client credentials are not configured.",
        )
    if (
        _origin(settings.FRONTEND_URL) not in settings.allowed_origins
        or _origin(settings.GOOGLE_REDIRECT_URI)
        not in settings.allowed_origins
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "FRONTEND_URL and the Google callback origin must be listed "
                "in ALLOWED_ORIGINS."
            ),
        )


def _origin(url: str) -> str:
    parsed = urlsplit(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def _oauth_cookie_options() -> OAuthCookieOptions:
    return {
        "httponly": True,
        "secure": settings.AUTH_COOKIE_SECURE,
        "samesite": "lax",
        "max_age": OAUTH_STATE_MAX_AGE,
        "path": OAUTH_COOKIE_PATH,
    }


def _set_auth_cookies(response: Response, result: dict[str, object]) -> None:
    common = {
        "httponly": True,
        "secure": settings.AUTH_COOKIE_SECURE,
        "samesite": "lax",
        "path": "/",
    }
    response.set_cookie(
        ACCESS_COOKIE,
        str(result["access_token"]),
        max_age=int(str(result["expires_in"])),
        **common,
    )
    response.set_cookie(
        REFRESH_COOKIE,
        str(result["refresh_token"]),
        max_age=settings.REFRESH_TOKEN_DAYS * 24 * 60 * 60,
        **common,
    )


def _clear_auth_cookies(response: Response) -> None:
    for name in (ACCESS_COOKIE, REFRESH_COOKIE):
        response.delete_cookie(
            name,
            path="/",
            secure=settings.AUTH_COOKIE_SECURE,
            httponly=True,
            samesite="lax",
        )


def _clear_oauth_cookies(response: Response) -> None:
    for name in (
        OAUTH_STATE_COOKIE,
        OAUTH_VERIFIER_COOKIE,
        OAUTH_NONCE_COOKIE,
    ):
        response.delete_cookie(
            name,
            path=OAUTH_COOKIE_PATH,
            secure=settings.AUTH_COOKIE_SECURE,
            httponly=True,
            samesite="lax",
        )


def _clear_oauth_retry_cookie(response: Response) -> None:
    response.delete_cookie(
        OAUTH_RETRY_COOKIE,
        path=OAUTH_COOKIE_PATH,
        secure=settings.AUTH_COOKIE_SECURE,
        httponly=True,
        samesite="lax",
    )


def _session_response(result: dict[str, object]) -> AuthSessionResponseSchema:
    return AuthSessionResponseSchema(
        expires_in=int(str(result["expires_in"])),
        account_id=UUID(str(result["account_id"])),
        actor_id=UUID(str(result["actor_id"])),
        role=str(result["role"]),
    )
