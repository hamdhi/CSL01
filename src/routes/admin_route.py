import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.schemas.ministry_schema import MinistryRequestSchema, MinistryResponseSchema
from src.schemas.standerd_response_schema import StandardResponseSchema
from src.services.admin_service import AdminService

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


@router.post(
    "/ministry-officers",
    response_model=StandardResponseSchema[MinistryResponseSchema],
    status_code=status.HTTP_201_CREATED,
)
async def add_ministry_officer(
    _request: MinistryRequestSchema,
    _service: Annotated[AdminService, Depends()],
):
    result = await _service.addMinistry(_request.model_dump())
    
    return StandardResponseSchema(
        data=MinistryResponseSchema.model_validate(result),
        message="Ministry officer added successfully",
        status_code=status.HTTP_201_CREATED,
    )


@router.patch(
    "/ministry-officers/{officer_id}",
    response_model=StandardResponseSchema[MinistryResponseSchema],
    status_code=status.HTTP_200_OK,
)
async def update_ministry_officer(
    officer_id: uuid.UUID,
    _request: MinistryRequestSchema,
    _service: Annotated[AdminService, Depends()],
):
    result = _service.update_ministry_officer(
        str(officer_id), _request.model_dump(exclude_unset=True)
    )

    return StandardResponseSchema(
        data=MinistryResponseSchema.model_validate(result),
        message="Ministry officer updated successfully",
        status_code=status.HTTP_200_OK,
    )


@router.delete(
    "/ministry-officers/{officer_id}",
    response_model=StandardResponseSchema[bool],
    status_code=status.HTTP_200_OK,
)
async def remove_ministry_officer(
    officer_id: uuid.UUID,
    _service: Annotated[AdminService, Depends()],
):
    result = _service.remove_ministry_officer(str(officer_id))

    return StandardResponseSchema(
        data=result,
        message="Ministry officer removed successfully",
        status_code=status.HTTP_200_OK,
    )
