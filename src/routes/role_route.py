import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from src.schemas.role_schema import RoleResponseSchema
from src.schemas.standerd_response_schema import StandardResponseSchema
from src.services.role_service import RoleService

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.get(
    "",
    response_model=StandardResponseSchema[list[RoleResponseSchema]],
    status_code=status.HTTP_200_OK,
)
async def get_roles(
    role_service: Annotated[RoleService, Depends()],
):
    roles = role_service.list_roles()
    return StandardResponseSchema[list[RoleResponseSchema]](
        status_code=status.HTTP_200_OK,
        message="Roles retrieved successfully.",
        data=[RoleResponseSchema.model_validate(role) for role in roles],
    )


@router.get(
    "/{role_id}",
    response_model=StandardResponseSchema[RoleResponseSchema],
    status_code=status.HTTP_200_OK,
)
async def get_role(
    role_id: uuid.UUID,
    response: Response,
    role_service: Annotated[RoleService, Depends()],
):
    role = role_service.get_role(role_id)
    if role is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return StandardResponseSchema[RoleResponseSchema](
            status_code=status.HTTP_404_NOT_FOUND,
            message="Role not found.",
            data=None,
        )
    return StandardResponseSchema[RoleResponseSchema](
        status_code=status.HTTP_200_OK,
        message="Role retrieved successfully.",
        data=RoleResponseSchema.model_validate(role),
    )
