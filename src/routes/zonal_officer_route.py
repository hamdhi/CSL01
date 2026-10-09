import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response

from src.core.security import (
    AuthenticatedPrincipal,
    get_current_principal,
    require_roles,
)
from src.schemas.pagination_schema import PaginatedDataSchema
from src.schemas.report_schema import (
    ReportPeriodParam,
    ReportRequestSchema,
    ReportResponseSchema,
)
from src.schemas.standerd_response_schema import StandardResponseSchema
from src.schemas.student_schema import (
    MonthlyRecordResponseSchema,
    StudentRegistrationDecisionSchema,
    StudentResponseSchema,
)
from src.schemas.subject_schema import SubjectResponseSchema
from src.schemas.teacher_schema import TeacherCreateRequestSchema, TeacherResponseSchema
from src.schemas.zonal_officer_schema import ZonalOfficerResponseSchema
from src.services.zonal_officer_service import ZonalOfficerService

router = APIRouter(
    prefix="/zonal",
    tags=["Zonal Officers"],
    dependencies=[Depends(require_roles("ZONAL"))],
)


@router.get(
    "/subjects",
    response_model=StandardResponseSchema[list[SubjectResponseSchema]],
)
async def list_zone_subjects(
    _service: Annotated[ZonalOfficerService, Depends()],
    grade: str | None = None,
    stream: str | None = None,
):
    subjects = _service.list_subjects(grade, stream)
    return StandardResponseSchema(
        data=[
            SubjectResponseSchema.model_validate(subject)
            for subject in subjects
        ],
        message="Available subjects retrieved successfully",
        status_code=status.HTTP_200_OK,
    )


@router.get(
    "/officers",
    response_model=StandardResponseSchema[
        PaginatedDataSchema[ZonalOfficerResponseSchema]
    ],
)
async def list_zonal_officers(
    _service: Annotated[ZonalOfficerService, Depends()],
    principal: Annotated[
        AuthenticatedPrincipal, Depends(get_current_principal)
    ],
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
):
    result = _service.list_zonal_officers(principal.actor_id, offset, limit)
    result["items"] = [
        ZonalOfficerResponseSchema.model_validate(item)
        for item in result["items"]
    ]
    return StandardResponseSchema(
        data=result,
        message="Zonal officers retrieved successfully",
        status_code=status.HTTP_200_OK,
    )


@router.get(
    "/teachers",
    response_model=StandardResponseSchema[
        PaginatedDataSchema[TeacherResponseSchema]
    ],
)
async def list_teachers(
    _service: Annotated[ZonalOfficerService, Depends()],
    principal: Annotated[
        AuthenticatedPrincipal, Depends(get_current_principal)
    ],
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
):
    if principal.zone_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The zonal officer is not assigned to a zone.",
        )
    result = _service.list_teachers(principal.zone_id, offset, limit)
    result["items"] = [
        TeacherResponseSchema.model_validate(item)
        for item in result["items"]
    ]
    return StandardResponseSchema(
        data=result,
        message="Teachers retrieved successfully",
        status_code=status.HTTP_200_OK,
    )


@router.get(
    "/students",
    response_model=StandardResponseSchema[
        PaginatedDataSchema[StudentResponseSchema]
    ],
)
async def list_students(
    _service: Annotated[ZonalOfficerService, Depends()],
    principal: Annotated[
        AuthenticatedPrincipal, Depends(get_current_principal)
    ],
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
):
    if principal.zone_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The zonal officer is not assigned to a zone.",
        )
    result = _service.list_students(principal.zone_id, offset, limit)
    result["items"] = [
        StudentResponseSchema.model_validate(item)
        for item in result["items"]
    ]
    return StandardResponseSchema(
        data=result,
        message="Students retrieved successfully",
        status_code=status.HTTP_200_OK,
    )


@router.get(
    "/monthly-records",
    response_model=StandardResponseSchema[
        PaginatedDataSchema[MonthlyRecordResponseSchema]
    ],
)
async def list_monthly_records(
    _service: Annotated[ZonalOfficerService, Depends()],
    principal: Annotated[
        AuthenticatedPrincipal, Depends(get_current_principal)
    ],
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
):
    if principal.zone_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The zonal officer is not assigned to a zone.",
        )
    result = _service.list_monthly_records(
        principal.zone_id, offset, limit
    )
    result["items"] = [
        MonthlyRecordResponseSchema.model_validate(item)
        for item in result["items"]
    ]
    return StandardResponseSchema(
        data=result,
        message="Monthly records retrieved successfully",
        status_code=status.HTTP_200_OK,
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
    start_date, end_date = request.resolve_period()
    result = _service.get_monthly_report(
        start_date, end_date, principal
    )

    return StandardResponseSchema(
        data=ReportResponseSchema.model_validate(result),
        message="Monthly zonal report retrieved successfully",
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


@router.get("/reports/pdf", status_code=status.HTTP_200_OK)
async def get_zone_report_pdf(
    _service: Annotated[ZonalOfficerService, Depends()],
    principal: Annotated[AuthenticatedPrincipal, Depends(get_current_principal)],
    period: ReportPeriodParam,
):
    """Generate a PDF with the whole zonal performance and teacher performance
    in the zone for the selected period (defaults to current month/year)."""
    if principal.zone_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The zonal officer is not assigned to a zone.",
        )
    pdf_bytes = _service.generate_zone_pdf(principal, period)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                "attachment; filename=zonal-performance-report.pdf"
            )
        },
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
