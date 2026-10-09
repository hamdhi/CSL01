import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.core.security import (
    AuthenticatedPrincipal,
    get_current_principal,
    require_roles,
)
from src.schemas.report_schema import ReportRequestSchema, ReportResponseSchema
from src.schemas.standerd_response_schema import StandardResponseSchema
from src.schemas.student_schema import StudentRegistrationDecisionSchema
from src.schemas.teacher_schema import TeacherCreateRequestSchema, TeacherResponseSchema
from src.services.zonal_officer_service import ZonalOfficerService

router = APIRouter(
    prefix="/zonal",
    tags=["Zonal Officers"],
    dependencies=[Depends(require_roles("ZONAL"))],
)


@router.post(
    "/teachers",
    response_model=StandardResponseSchema[TeacherResponseSchema],
    status_code=status.HTTP_201_CREATED,
)
async def add_teacher(
    request: TeacherCreateRequestSchema,
    _service: Annotated[ZonalOfficerService, Depends()],
    principal: Annotated[
        AuthenticatedPrincipal, Depends(get_current_principal)
    ],
):
    if principal.zone_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The zonal officer is not assigned to a zone.",
        )
    request_data = request.model_dump()
    request_data["zonal_id"] = principal.zone_id
    result = _service.add_teacher(request_data)

    return StandardResponseSchema(
        data=TeacherResponseSchema.model_validate(result),
        message="Teacher added successfully",
        status_code=status.HTTP_201_CREATED,
    )


@router.post(
    "/reports/monthly",
    response_model=StandardResponseSchema[ReportResponseSchema],
    status_code=status.HTTP_200_OK,
)
async def get_monthly_report(
    request: ReportRequestSchema,
    _service: Annotated[ZonalOfficerService, Depends()],
    principal: Annotated[
        AuthenticatedPrincipal, Depends(get_current_principal)
    ],
):
    if principal.zone_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The zonal officer is not assigned to a zone.",
        )
    result = _service.get_monthly_report(
        request.start_date, request.end_date, principal
    )

    return StandardResponseSchema(
        data=ReportResponseSchema.model_validate(result),
        message="Monthly zonal report retrieved successfully",
        status_code=status.HTTP_200_OK,
    )


@router.post(
    "/reports/three-month",
    response_model=StandardResponseSchema[ReportResponseSchema],
    status_code=status.HTTP_200_OK,
)
async def get_three_month_report(
    request: ReportRequestSchema,
    _service: Annotated[ZonalOfficerService, Depends()],
    principal: Annotated[
        AuthenticatedPrincipal, Depends(get_current_principal)
    ],
):
    result = _service.get_three_month_report(
        request.start_date, request.end_date, principal
    )
    return StandardResponseSchema(
        data=ReportResponseSchema.model_validate(result),
        message="Three-month zonal report retrieved successfully",
        status_code=status.HTTP_200_OK,
    )


@router.patch(
    "/teachers/{teacher_id}/registration",
    response_model=StandardResponseSchema[TeacherResponseSchema],
    status_code=status.HTTP_200_OK,
)
async def decide_teacher_registration(
    teacher_id: uuid.UUID,
    request: StudentRegistrationDecisionSchema,
    _service: Annotated[ZonalOfficerService, Depends()],
    principal: Annotated[
        AuthenticatedPrincipal, Depends(get_current_principal)
    ],
):
    if principal.zone_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The zonal officer is not assigned to a zone.",
        )
    result = _service.decide_teacher_registration(
        str(teacher_id), request.approved, principal.zone_id
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found.",
        )
    return StandardResponseSchema(
        data=TeacherResponseSchema.model_validate(result),
        message="Teacher registration decision saved successfully",
        status_code=status.HTTP_200_OK,
    )


@router.get(
    "/reports",
    response_model=StandardResponseSchema[list[ReportResponseSchema]],
)
async def list_saved_reports(
    _service: Annotated[ZonalOfficerService, Depends()],
    principal: Annotated[
        AuthenticatedPrincipal, Depends(get_current_principal)
    ],
):
    result = _service.list_saved_reports(principal)
    return StandardResponseSchema(
        data=result,
        message="Saved zonal reports retrieved successfully",
        status_code=status.HTTP_200_OK,
    )


@router.get(
    "/reports/{report_id}",
    response_model=StandardResponseSchema[ReportResponseSchema],
)
async def get_saved_report(
    report_id: uuid.UUID,
    _service: Annotated[ZonalOfficerService, Depends()],
    principal: Annotated[
        AuthenticatedPrincipal, Depends(get_current_principal)
    ],
):
    result = _service.get_saved_report(report_id, principal)
    return StandardResponseSchema(
        data=ReportResponseSchema.model_validate(result),
        message="Saved zonal report retrieved successfully",
        status_code=status.HTTP_200_OK,
    )
