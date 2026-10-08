import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.schemas.report_schema import ReportRequestSchema, ReportResponseSchema
from src.schemas.standerd_response_schema import StandardResponseSchema
from src.schemas.zonal_officer_schema import (
    ZonalOfficerCreateRequestSchema,
    ZonalOfficerResponseSchema,
    ZonalOfficerUpdateRequestSchema,
)
from src.services.report_service import ReportService
from src.services.zonal_officer_service import ZonalOfficerService

router = APIRouter(prefix="/zonal", tags=["Zonal Officers"])


@router.post(
    "/officers",
    response_model=StandardResponseSchema[ZonalOfficerResponseSchema],
    status_code=status.HTTP_201_CREATED,
)
async def add_zonal_officer(
    request: ZonalOfficerCreateRequestSchema,
    _service: Annotated[ZonalOfficerService, Depends()],
):
    result = _service.add_zonal_officer(request.model_dump())

    return StandardResponseSchema(
        data=ZonalOfficerResponseSchema.model_validate(result),
        message="Zonal officer added successfully",
        status_code=status.HTTP_201_CREATED,
    )


@router.patch(
    "/officers/{officer_id}",
    response_model=StandardResponseSchema[ZonalOfficerResponseSchema],
    status_code=status.HTTP_200_OK,
)
async def update_zonal_officer(
    officer_id: uuid.UUID,
    request: ZonalOfficerUpdateRequestSchema,
    _service: Annotated[ZonalOfficerService, Depends()],
):
    result = _service.update_zonal_officer(
        str(officer_id), request.model_dump(exclude_unset=True)
    )

    return StandardResponseSchema(
        data=ZonalOfficerResponseSchema.model_validate(result),
        message="Zonal officer updated successfully",
        status_code=status.HTTP_200_OK,
    )


@router.delete(
    "/officers/{officer_id}",
    response_model=StandardResponseSchema[bool],
    status_code=status.HTTP_200_OK,
)
async def remove_zonal_officer(
    officer_id: uuid.UUID,
    _service: Annotated[ZonalOfficerService, Depends()],
):
    result = _service.remove_zonal_officer(str(officer_id))

    return StandardResponseSchema(
        data=result,
        message="Zonal officer removed successfully",
        status_code=status.HTTP_200_OK,
    )


@router.post(
    "/reports/monthly",
    response_model=StandardResponseSchema[ReportResponseSchema],
    status_code=status.HTTP_200_OK,
)
async def get_monthly_report(
    request: ReportRequestSchema,
    _service: Annotated[ReportService, Depends()],
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
    _service: Annotated[ReportService, Depends()],
):
    result = _service.get_three_month_report(
        request.start_date, request.end_date
    )

    return StandardResponseSchema(
        data=ReportResponseSchema.model_validate(result),
        message="Three-month zonal report retrieved successfully",
        status_code=status.HTTP_200_OK,
    )
