import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.core.security import (
    AuthenticatedPrincipal,
    get_current_principal,
    require_roles,
)
from src.schemas.ministry_schema import MinistryResponseSchema
from src.schemas.pagination_schema import PaginatedDataSchema
from src.schemas.report_schema import ReportRequestSchema, ReportResponseSchema
from src.schemas.standerd_response_schema import StandardResponseSchema
from src.schemas.student_schema import StudentRegistrationDecisionSchema
from src.schemas.subject_schema import (
    SubjectCreateRequestSchema,
    SubjectResponseSchema,
    SubjectUpdateRequestSchema,
)
from src.schemas.zonal_officer_schema import (
    ZonalOfficerCreateRequestSchema,
    ZonalOfficerResponseSchema,
    ZonalOfficerUpdateRequestSchema,
)
from src.schemas.zone_schema import (
    ProvinceResponseSchema,
    ZoneCreateRequestSchema,
    ZoneResponseSchema,
)
from src.services.ministry_service import MinistryService

router = APIRouter(
    prefix="/ministry",
    tags=["Ministry"],
    dependencies=[Depends(require_roles("MINISTRY"))],
)


@router.get(
    "/zonal-officers",
    response_model=StandardResponseSchema[
        PaginatedDataSchema[ZonalOfficerResponseSchema]
    ],
)
async def list_zonal_officers(
    _service: Annotated[MinistryService, Depends()],
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
    "/officers",
    response_model=StandardResponseSchema[
        PaginatedDataSchema[MinistryResponseSchema]
    ],
)
async def list_ministry_officers(
    _service: Annotated[MinistryService, Depends()],
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
    "/zones",
    response_model=StandardResponseSchema[ZoneResponseSchema],
    status_code=status.HTTP_201_CREATED,
)
async def create_zone(
    request: ZoneCreateRequestSchema,
    _service: Annotated[MinistryService, Depends()],
):
    zone = _service.create_zone(request.name, request.prov_id)
    return StandardResponseSchema(
        data=ZoneResponseSchema(
            zone_id=zone.zone_id,
            name=zone.name,
            prov_id=zone.prov_id,
        ),
        message="Zone created successfully",
        status_code=status.HTTP_201_CREATED,
    )


@router.get(
    "/zones",
    response_model=StandardResponseSchema[PaginatedDataSchema[ZoneResponseSchema]],
)
async def list_zones(
    _service: Annotated[MinistryService, Depends()],
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
):
    result = _service.list_zones(offset, limit)
    result["items"] = [
        ZoneResponseSchema(
            zone_id=zone.zone_id,
            name=zone.name,
            prov_id=zone.prov_id,
        )
        for zone in result["items"]
    ]
    return StandardResponseSchema(
        data=result,
        message="Zones retrieved successfully",
        status_code=status.HTTP_200_OK,
    )


@router.get(
    "/provinces",
    response_model=StandardResponseSchema[
        PaginatedDataSchema[ProvinceResponseSchema]
    ],
)
async def list_provinces(
    _service: Annotated[MinistryService, Depends()],
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
):
    result = _service.list_provinces(offset, limit)
    result["items"] = [
        ProvinceResponseSchema(
            prov_id=province.prov_id,
            name=province.Province_name,
        )
        for province in result["items"]
    ]
    return StandardResponseSchema(
        data=result,
        message="Provinces retrieved successfully",
        status_code=status.HTTP_200_OK,
    )


@router.post(
    "/subjects",
    response_model=StandardResponseSchema[SubjectResponseSchema],
    status_code=status.HTTP_201_CREATED,
)
async def create_subject(
    request: SubjectCreateRequestSchema,
    _service: Annotated[MinistryService, Depends()],
):
    result = _service.create_subject(request.model_dump())
    return StandardResponseSchema(
        data=SubjectResponseSchema.model_validate(result),
        message="Subject added successfully",
        status_code=status.HTTP_201_CREATED,
    )


@router.get(
    "/subjects",
    response_model=StandardResponseSchema[list[SubjectResponseSchema]],
    status_code=status.HTTP_200_OK,
)
async def list_subjects(
    _service: Annotated[MinistryService, Depends()],
    grade: str | None = None,
    stream: str | None = None,
    include_inactive: bool = False,
):
    result = _service.list_subjects(grade, stream, include_inactive)
    return StandardResponseSchema(
        data=result,
        message="Subjects retrieved successfully",
        status_code=status.HTTP_200_OK,
    )


@router.patch(
    "/subjects/{subject_id}",
    response_model=StandardResponseSchema[SubjectResponseSchema],
    status_code=status.HTTP_200_OK,
)
async def update_subject(
    subject_id: uuid.UUID,
    request: SubjectUpdateRequestSchema,
    _service: Annotated[MinistryService, Depends()],
):
    result = _service.update_subject(
        str(subject_id), request.model_dump(exclude_unset=True)
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found.",
        )
    return StandardResponseSchema(
        data=SubjectResponseSchema.model_validate(result),
        message="Subject updated successfully",
        status_code=status.HTTP_200_OK,
    )

@router.post(
    "/zonal-officers",
    response_model=StandardResponseSchema[ZonalOfficerResponseSchema],
    status_code=status.HTTP_201_CREATED,
)
async def add_zonal_officer(
    request: ZonalOfficerCreateRequestSchema,
    _service: Annotated[MinistryService, Depends()],
    principal: Annotated[
        AuthenticatedPrincipal, Depends(get_current_principal)
    ],
):
    request_data = request.model_dump()
    request_data["mini_id"] = principal.actor_id
    result = _service.addZonalOfficer(request_data)

    return StandardResponseSchema(
        data=ZonalOfficerResponseSchema.model_validate(result),
        message="Zonal officer added successfully",
        status_code=status.HTTP_201_CREATED,
    )


@router.patch(
    "/zonal-officers/{officer_id}/registration",
    response_model=StandardResponseSchema[ZonalOfficerResponseSchema],
    status_code=status.HTTP_200_OK,
)
async def decide_zonal_officer_registration(
    officer_id: uuid.UUID,
    request: StudentRegistrationDecisionSchema,
    _service: Annotated[MinistryService, Depends()],
):
    result = _service.decide_zonal_officer(
        str(officer_id), request.approved
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zonal officer not found.",
        )
    return StandardResponseSchema(
        data=ZonalOfficerResponseSchema.model_validate(result),
        message="Zonal officer registration decision saved successfully",
        status_code=status.HTTP_200_OK,
    )


@router.patch(
    "/zonal-officers/{officer_id}",
    response_model=StandardResponseSchema[ZonalOfficerResponseSchema],
    status_code=status.HTTP_200_OK,
)
async def update_zonal_officer(
    officer_id: uuid.UUID,
    request: ZonalOfficerUpdateRequestSchema,
    _service: Annotated[MinistryService, Depends()],
    principal: Annotated[
        AuthenticatedPrincipal, Depends(get_current_principal)
    ],
):
    changes = request.model_dump(exclude_unset=True)
    changes["mini_id"] = principal.actor_id
    result = _service.update_zonal_officer(
        str(officer_id), changes
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zonal officer not found.",
        )
    return StandardResponseSchema(
        data=ZonalOfficerResponseSchema.model_validate(result),
        message="Zonal officer updated successfully",
        status_code=status.HTTP_200_OK,
    )


@router.delete(
    "/zonal-officers/{officer_id}",
    response_model=StandardResponseSchema[bool],
    status_code=status.HTTP_200_OK,
)
async def remove_zonal_officer(
    officer_id: uuid.UUID,
    _service: Annotated[MinistryService, Depends()],
):
    result = _service.remove_zonal_officer(str(officer_id))
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zonal officer not found.",
        )
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
async def get_monthly_province_report(
    request: ReportRequestSchema,
    _service: Annotated[MinistryService, Depends()],
    principal: Annotated[
        AuthenticatedPrincipal, Depends(get_current_principal)
    ],
):
    result = _service.get_monthly_province_report(
        request.start_date, request.end_date, principal
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
    _service: Annotated[MinistryService, Depends()],
    principal: Annotated[
        AuthenticatedPrincipal, Depends(get_current_principal)
    ],
):
    result = _service.get_three_month_province_report(
        request.start_date, request.end_date, principal
    )
    return StandardResponseSchema(
        data=ReportResponseSchema.model_validate(result),
        message="Three-month province report retrieved successfully",
        status_code=status.HTTP_200_OK,
    )


@router.get(
    "/reports",
    response_model=StandardResponseSchema[list[ReportResponseSchema]],
)
async def list_saved_reports(
    _service: Annotated[MinistryService, Depends()],
    principal: Annotated[
        AuthenticatedPrincipal, Depends(get_current_principal)
    ],
):
    result = _service.list_saved_reports(principal)
    return StandardResponseSchema(
        data=result,
        message="Saved province reports retrieved successfully",
        status_code=status.HTTP_200_OK,
    )


@router.get(
    "/reports/{report_id}",
    response_model=StandardResponseSchema[ReportResponseSchema],
)
async def get_saved_report(
    report_id: uuid.UUID,
    _service: Annotated[MinistryService, Depends()],
    principal: Annotated[
        AuthenticatedPrincipal, Depends(get_current_principal)
    ],
):
    result = _service.get_saved_report(report_id, principal)
    return StandardResponseSchema(
        data=ReportResponseSchema.model_validate(result),
        message="Saved province report retrieved successfully",
        status_code=status.HTTP_200_OK,
    )
