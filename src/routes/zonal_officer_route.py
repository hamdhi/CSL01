from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.schemas.report_schema import ReportRequestSchema, ReportResponseSchema
from src.schemas.standerd_response_schema import StandardResponseSchema
from src.schemas.teacher_schema import TeacherCreateRequestSchema, TeacherResponseSchema
from src.services.zonal_officer_service import ZonalOfficerService

router = APIRouter(prefix="/zonal", tags=["Zonal Officers"])


@router.post(
    "/teachers",
    response_model=StandardResponseSchema[TeacherResponseSchema],
    status_code=status.HTTP_201_CREATED,
)
async def add_teacher(
    request: TeacherCreateRequestSchema,
    _service: Annotated[ZonalOfficerService, Depends()],
):
    result = _service.add_teacher(request.model_dump())

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
):
    result = _service.get_monthly_report(request.start_date, request.end_date)

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
):
    result = _service.get_three_month_report(
        request.start_date, request.end_date
    )

    return StandardResponseSchema(
        data=ReportResponseSchema.model_validate(result),
        message="Three-month zonal report retrieved successfully",
        status_code=status.HTTP_200_OK,
    )
