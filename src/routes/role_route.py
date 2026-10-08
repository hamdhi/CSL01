import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.exc import IntegrityError

from src.schemas.role_schema import (
    RoleCreateRequestSchema,
    RoleResponseSchema,
    RoleUpdateRequestSchema,
)
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


@router.post(
    "",
    response_model=StandardResponseSchema[RoleResponseSchema],
    status_code=status.HTTP_201_CREATED,
)
async def create_role(
    request: RoleCreateRequestSchema,
    response: Response,
    role_service: Annotated[RoleService, Depends()],
):
    try:
        role = role_service.create_role(request.name)
    except IntegrityError:
        response.status_code = status.HTTP_409_CONFLICT
        return StandardResponseSchema[RoleResponseSchema](
            status_code=status.HTTP_409_CONFLICT,
            message="A role with this name already exists.",
            data=None,
        )
    return StandardResponseSchema[RoleResponseSchema](
        status_code=status.HTTP_201_CREATED,
        message="Role created successfully.",
        data=RoleResponseSchema.model_validate(role),
    )


@router.put(
    "/{role_id}",
    response_model=StandardResponseSchema[RoleResponseSchema],
    status_code=status.HTTP_200_OK,
)
async def update_role(
    role_id: uuid.UUID,
    request: RoleUpdateRequestSchema,
    response: Response,
    role_service: Annotated[RoleService, Depends()],
):
    try:
        role = role_service.update_role(role_id, request.name)
    except IntegrityError:
        response.status_code = status.HTTP_409_CONFLICT
        return StandardResponseSchema[RoleResponseSchema](
            status_code=status.HTTP_409_CONFLICT,
            message="A role with this name already exists.",
            data=None,
        )
    if role is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return StandardResponseSchema[RoleResponseSchema](
            status_code=status.HTTP_404_NOT_FOUND,
            message="Role not found.",
            data=None,
        )
    return StandardResponseSchema[RoleResponseSchema](
        status_code=status.HTTP_200_OK,
        message="Role updated successfully.",
        data=RoleResponseSchema.model_validate(role),
    )


@router.delete(
    "/{role_id}",
    response_model=StandardResponseSchema[bool],
    status_code=status.HTTP_200_OK,
)
async def delete_role(
    role_id: uuid.UUID,
    response: Response,
    role_service: Annotated[RoleService, Depends()],
):
    deleted = role_service.delete_role(role_id)
    if not deleted:
        response.status_code = status.HTTP_404_NOT_FOUND
        return StandardResponseSchema[bool](
            status_code=status.HTTP_404_NOT_FOUND,
            message="Role not found.",
            data=False,
        )
    return StandardResponseSchema[bool](
        status_code=status.HTTP_200_OK,
        message="Role deleted successfully.",
        data=True,
    )
