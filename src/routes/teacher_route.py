import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.core.security import (
    AuthenticatedPrincipal,
    get_current_principal,
    require_roles,
)
from src.schemas.standerd_response_schema import StandardResponseSchema
from src.schemas.student_schema import (
    MonthlyRecordResponseSchema,
    StudentRegistrationDecisionSchema,
    StudentResponseSchema,
)
from src.schemas.teacher_schema import (
    MonthlyRecordDecisionSchema,
)
from src.services.teacher_service import TeacherService

router = APIRouter(
    prefix="/teachers",
    tags=["Teachers"],
    dependencies=[Depends(require_roles("TEACHER"))],
)


@router.patch(
    "/students/{student_id}/registration",
    response_model=StandardResponseSchema[StudentResponseSchema],
    status_code=status.HTTP_200_OK,
)
async def decide_student_registration(
    student_id: uuid.UUID,
    request: StudentRegistrationDecisionSchema,
    _service: Annotated[TeacherService, Depends()],
    principal: Annotated[
        AuthenticatedPrincipal, Depends(get_current_principal)
    ],
):
    if principal.zone_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The teacher is not assigned to a zone.",
        )
    result = _service.decide_student_registration(
        str(student_id), request.approved, principal.zone_id
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found.",
        )

    return StandardResponseSchema(
        data=StudentResponseSchema.model_validate(result),
        message="Student registration decision saved successfully",
        status_code=status.HTTP_200_OK,
    )


@router.patch(
    "/monthly-records/{record_id}",
    response_model=StandardResponseSchema[MonthlyRecordResponseSchema],
    status_code=status.HTTP_200_OK,
)
async def decide_monthly_record(
    record_id: uuid.UUID,
    request: MonthlyRecordDecisionSchema,
    _service: Annotated[TeacherService, Depends()],
    principal: Annotated[
        AuthenticatedPrincipal, Depends(get_current_principal)
    ],
):
    if principal.zone_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The teacher is not assigned to a zone.",
        )
    result = _service.decide_monthly_record(
        str(record_id), request.approved, principal.zone_id
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monthly record not found.",
        )

    return StandardResponseSchema(
        data=MonthlyRecordResponseSchema.model_validate(result),
        message="Monthly record decision saved successfully",
        status_code=status.HTTP_200_OK,
    )


@router.post(
    "/students/{student_id}/login/reset",
    response_model=StandardResponseSchema[None],
    status_code=status.HTTP_200_OK,
)
async def reset_student_login(
    student_id: uuid.UUID,
    _service: Annotated[TeacherService, Depends()],
    principal: Annotated[
        AuthenticatedPrincipal, Depends(get_current_principal)
    ],
):
    if principal.zone_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The teacher is not assigned to a zone.",
        )
    if principal.zone_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The teacher is not assigned to a zone.",
        )
    result = _service.reset_student_login(str(student_id), principal.zone_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found.",
        )

    return StandardResponseSchema(
        data=None,
        message="Student login sessions revoked successfully",
        status_code=status.HTTP_200_OK,
    )


@router.post(
    "/students/{student_id}/monthly-record/reset",
    response_model=StandardResponseSchema[None],
    status_code=status.HTTP_200_OK,
)
async def reset_monthly_record(
    student_id: uuid.UUID,
    _service: Annotated[TeacherService, Depends()],
    principal: Annotated[
        AuthenticatedPrincipal, Depends(get_current_principal)
    ],
):
    if principal.zone_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The teacher is not assigned to a zone.",
        )
    result = _service.reset_monthly_record(str(student_id), principal.zone_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student monthly records not found.",
        )

    return StandardResponseSchema(
        data=None,
        message="Student monthly record reset successfully",
        status_code=status.HTTP_200_OK,
    )
