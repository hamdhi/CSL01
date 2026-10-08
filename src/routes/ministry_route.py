from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.schemas.report_schema import ReportRequestSchema, ReportResponseSchema
from src.schemas.standerd_response_schema import StandardResponseSchema
from src.schemas.zonal_officer_schema import (
    ZonalOfficerCreateRequestSchema,
    ZonalOfficerResponseSchema,
)
from src.services.ministry_service import MinistryService
from src.services.report_service import ReportService

router = APIRouter(prefix="/ministry", tags=["Ministry"])


@router.post(
    "/zonal-officers",
    response_model=StandardResponseSchema[ZonalOfficerResponseSchema],
    status_code=status.HTTP_201_CREATED,
)
async def add_zonal_officer(
    request: ZonalOfficerCreateRequestSchema,
    _service: Annotated[MinistryService, Depends()],
):
    result = _service.addZonalOfficer(request.model_dump())

    return StandardResponseSchema(
        data=ZonalOfficerResponseSchema.model_validate(result),
        message="Zonal officer added successfully",
        status_code=status.HTTP_201_CREATED,
    )


@router.post(
    "/reports/monthly",
    response_model=StandardResponseSchema[ReportResponseSchema],
    status_code=status.HTTP_200_OK,
)
async def get_monthly_province_report(
    request: ReportRequestSchema,
    _service: Annotated[ReportService, Depends()],
):
    result = _service.get_province_report(
        request.start_date, request.end_date
    )

    return StandardResponseSchema(
        data=ReportResponseSchema.model_validate(result),
        message="Monthly province report retrieved successfully",
        status_code=status.HTTP_200_OK,
    )


@router.post(
    "/reports/three-month",
    response_model=StandardResponseSchema[ReportResponseSchema],
    status_code=status.HTTP_200_OK,
)
async def get_three_month_province_report(
    request: ReportRequestSchema,
    _service: Annotated[ReportService, Depends()],
):
    result = _service.get_three_month_report(
        request.start_date, request.end_date
    )

    return StandardResponseSchema(
        data=ReportResponseSchema.model_validate(result),
        message="Three-month province report retrieved successfully",
        status_code=status.HTTP_200_OK,
    )


@router.get(
    "/reports",
    response_model=StandardResponseSchema[list[ReportResponseSchema]],
    status_code=status.HTTP_200_OK,
)
async def view_any_report(_service: Annotated[MinistryService, Depends()]):
    result = _service.view_any_report()

    return StandardResponseSchema(
        data=result,
        message="Reports retrieved successfully",
        status_code=status.HTTP_200_OK,
    )
