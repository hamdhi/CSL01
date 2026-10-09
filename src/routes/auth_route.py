from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.core.security import (
    AuthenticatedPrincipal,
    get_current_principal,
)
from src.schemas.auth_schema import (
    AuthTokenResponseSchema,
    GoogleLoginRequestSchema,
    PasswordLoginRequestSchema,
    PasswordUpdateRequestSchema,
    RefreshTokenRequestSchema,
)
from src.schemas.standerd_response_schema import StandardResponseSchema
from src.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=StandardResponseSchema[AuthTokenResponseSchema],
)
async def login(
    request: PasswordLoginRequestSchema,
    _service: Annotated[AuthService, Depends()],
):
    result = _service.login_with_password(
        str(request.email), request.password
    )
    return StandardResponseSchema(
        data=AuthTokenResponseSchema.model_validate(result),
        message="Login successful",
        status_code=status.HTTP_200_OK,
    )


@router.post(
    "/google",
    response_model=StandardResponseSchema[AuthTokenResponseSchema],
)
async def login_with_google(
    request: GoogleLoginRequestSchema,
    _service: Annotated[AuthService, Depends()],
):
    result = _service.login_with_google(request.id_token)
    return StandardResponseSchema(
        data=AuthTokenResponseSchema.model_validate(result),
        message="Google login successful",
        status_code=status.HTTP_200_OK,
    )


@router.post(
    "/refresh",
    response_model=StandardResponseSchema[AuthTokenResponseSchema],
)
async def refresh(
    request: RefreshTokenRequestSchema,
    _service: Annotated[AuthService, Depends()],
):
    result = _service.refresh(request.refresh_token)
    return StandardResponseSchema(
        data=AuthTokenResponseSchema.model_validate(result),
        message="Tokens refreshed successfully",
        status_code=status.HTTP_200_OK,
    )


@router.post("/logout", response_model=StandardResponseSchema[None])
async def logout(
    principal: Annotated[
        AuthenticatedPrincipal, Depends(get_current_principal)
    ],
    _service: Annotated[AuthService, Depends()],
):
    if principal.session_id is not None:
        _service.logout(principal.session_id)
    return StandardResponseSchema(
        data=None,
        message="Logged out successfully",
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
