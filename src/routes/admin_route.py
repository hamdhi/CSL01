import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.core.security import (
    AuthenticatedPrincipal,
    get_current_principal,
    require_roles,
)
from src.schemas.admin_schema import AdminResponseSchema
from src.schemas.ministry_schema import (
    MinistryCreateRequestSchema,
    MinistryRequestSchema,
    MinistryResponseSchema,
)
from src.schemas.pagination_schema import PaginatedDataSchema
from src.schemas.report_schema import ReportResponseSchema
from src.schemas.standerd_response_schema import StandardResponseSchema
from src.schemas.student_schema import StudentRegistrationDecisionSchema
from src.services.admin_service import AdminService

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(require_roles("ADMIN"))],
)


@router.get(
    "/admins",
    response_model=StandardResponseSchema[
        PaginatedDataSchema[AdminResponseSchema]
    ],
)
async def list_admins(
    _service: Annotated[AdminService, Depends()],
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
):
    result = _service.list_admins(offset, limit)
    result["items"] = [
        AdminResponseSchema.model_validate(item) for item in result["items"]
    ]
    return StandardResponseSchema(
        data=result,
        message="Admins retrieved successfully",
        status_code=status.HTTP_200_OK,
    )


@router.get(
    "/ministry-officers",
    response_model=StandardResponseSchema[
        PaginatedDataSchema[MinistryResponseSchema]
    ],
)
async def list_ministry_officers(
    _service: Annotated[AdminService, Depends()],
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
):
    result = _service.list_ministry_officers(offset, limit)
    result["items"] = [
        MinistryResponseSchema.model_validate(item)
        for item in result["items"]
    ]
    return StandardResponseSchema(
        data=result,
        message="Ministry officers retrieved successfully",
        status_code=status.HTTP_200_OK,
    )


@router.post(
    "/ministry-officers",
    response_model=StandardResponseSchema[MinistryResponseSchema],
    status_code=status.HTTP_201_CREATED,
)
async def add_ministry_officer(
    _request: MinistryCreateRequestSchema,
    _service: Annotated[AdminService, Depends()],
    principal: Annotated[
        AuthenticatedPrincipal, Depends(get_current_principal)
    ],
):
    request_data = _request.model_dump()
    request_data["admin_id"] = principal.actor_id
    result = await _service.addMinistry(request_data)
    
    return StandardResponseSchema(
        data=MinistryResponseSchema.model_validate(result),
        message="Ministry officer added successfully",
        status_code=status.HTTP_201_CREATED,
    )


@router.patch(
    "/ministry-officers/{officer_id}/registration",
    response_model=StandardResponseSchema[MinistryResponseSchema],
    status_code=status.HTTP_200_OK,
)
async def decide_ministry_officer_registration(
    officer_id: uuid.UUID,
    request: StudentRegistrationDecisionSchema,
    _service: Annotated[AdminService, Depends()],
):
    result = _service.decide_ministry_officer(
        str(officer_id), request.approved
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ministry officer not found.",
        )
    return StandardResponseSchema(
        data=MinistryResponseSchema.model_validate(result),
        message="Ministry officer registration decision saved successfully",
        status_code=status.HTTP_200_OK,
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
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ministry officer not found.",
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
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ministry officer not found.",
        )

    return StandardResponseSchema(
        data=result,
        message="Ministry officer removed successfully",
        status_code=status.HTTP_200_OK,
    )


@router.get(
    "/reports",
    response_model=StandardResponseSchema[list[ReportResponseSchema]],
    status_code=status.HTTP_200_OK,
)
async def view_any_report(
    _service: Annotated[AdminService, Depends()],
    principal: Annotated[
        AuthenticatedPrincipal, Depends(get_current_principal)
    ],
):
    result = _service.view_any_report(principal)

    return StandardResponseSchema(
        data=result,
        message="Reports retrieved successfully",
        status_code=status.HTTP_200_OK,
    )


@router.get(
    "/reports/{report_id}",
    response_model=StandardResponseSchema[ReportResponseSchema],
    status_code=status.HTTP_200_OK,
)
async def get_report(
    report_id: uuid.UUID,
    _service: Annotated[AdminService, Depends()],
    principal: Annotated[
        AuthenticatedPrincipal, Depends(get_current_principal)
    ],
):
    result = _service.get_report(report_id, principal)
    return StandardResponseSchema(
        data=ReportResponseSchema.model_validate(result),
        message="Report retrieved successfully",
        status_code=status.HTTP_200_OK,
    )
