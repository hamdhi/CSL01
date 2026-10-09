import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.core.security import (
    AuthenticatedPrincipal,
    get_current_principal,
    require_roles,
)
from src.schemas.pagination_schema import PaginatedDataSchema
from src.schemas.standerd_response_schema import StandardResponseSchema
from src.schemas.student_schema import (
    MonthlyRecordResponseSchema,
    StudentDirectoryResponseSchema,
    StudentRegistrationDecisionSchema,
    StudentResponseSchema,
    TeacherAddStudentRequestSchema,
)
from src.schemas.subject_schema import SubjectResponseSchema
from src.schemas.teacher_schema import (
    MonthlyRecordDecisionSchema,
    TeacherAssignmentDecisionSchema,
    TeacherResponseSchema,
)
from src.services.teacher_service import TeacherService

router = APIRouter(
    prefix="/teachers",
    tags=["Teachers"],
    dependencies=[Depends(require_roles("TEACHER"))],
)


@router.post(
    "/students",
    response_model=StandardResponseSchema[StudentResponseSchema],
    status_code=status.HTTP_201_CREATED,
)
async def add_student(
    request: TeacherAddStudentRequestSchema,
    _service: Annotated[TeacherService, Depends()],
    principal: Annotated[AuthenticatedPrincipal, Depends(get_current_principal)],
):
    student = _service.add_student(principal.actor_id, request.model_dump())
    return StandardResponseSchema(
        data=StudentResponseSchema.model_validate(student),
        message="Student registered and assigned successfully",
        status_code=status.HTTP_201_CREATED,
    )


@router.get(
    "/subjects",
    response_model=StandardResponseSchema[SubjectResponseSchema],
)
async def get_assigned_subject(
    _service: Annotated[TeacherService, Depends()],
    principal: Annotated[
        AuthenticatedPrincipal, Depends(get_current_principal)
    ],
):
    subject = _service.get_assigned_subject(principal.actor_id)
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subject is assigned to this teacher.",
        )
    return StandardResponseSchema(
        data=SubjectResponseSchema.model_validate(subject),
        message="Assigned subject retrieved successfully",
        status_code=status.HTTP_200_OK,
    )


@router.get(
    "/colleagues",
    response_model=StandardResponseSchema[
        PaginatedDataSchema[TeacherResponseSchema]
    ],
)
async def list_colleagues(
    _service: Annotated[TeacherService, Depends()],
    principal: Annotated[
        AuthenticatedPrincipal, Depends(get_current_principal)
    ],
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
):
    if principal.zone_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The teacher is not assigned to a zone.",
        )
    result = _service.list_colleagues(principal.zone_id, offset, limit)
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
        PaginatedDataSchema[StudentDirectoryResponseSchema]
    ],
)
async def list_assigned_students(
    _service: Annotated[TeacherService, Depends()],
    principal: Annotated[
        AuthenticatedPrincipal, Depends(get_current_principal)
    ],
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
):
    result = _service.list_assigned_students(
        principal.actor_id, offset, limit
    )
    result["items"] = [
        StudentDirectoryResponseSchema.model_validate(item)
        for item in result["items"]
    ]
    return StandardResponseSchema(
        data=result,
        message="Assigned students retrieved successfully",
        status_code=status.HTTP_200_OK,
    )


@router.get(
    "/student-assignment-requests",
    response_model=StandardResponseSchema[
        PaginatedDataSchema[StudentDirectoryResponseSchema]
    ],
)
async def list_student_assignment_requests(
    _service: Annotated[TeacherService, Depends()],
    principal: Annotated[AuthenticatedPrincipal, Depends(get_current_principal)],
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
):
    result = _service.list_student_assignment_requests(
        principal.actor_id, offset, limit
    )
    result["items"] = [
        StudentDirectoryResponseSchema.model_validate(student)
        for student in result["items"]
    ]
    return StandardResponseSchema(
        data=result,
        message="Student assignment requests retrieved successfully",
        status_code=status.HTTP_200_OK,
    )


@router.patch(
    "/students/{student_id}/assignment",
    response_model=StandardResponseSchema[StudentDirectoryResponseSchema],
)
async def decide_student_assignment(
    student_id: uuid.UUID,
    request: TeacherAssignmentDecisionSchema,
    _service: Annotated[TeacherService, Depends()],
    principal: Annotated[AuthenticatedPrincipal, Depends(get_current_principal)],
):
    student = _service.decide_student_assignment(
        student_id, principal.actor_id, request.approved
    )
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher assignment request not found.",
        )
    return StandardResponseSchema(
        data=StudentDirectoryResponseSchema.model_validate(student),
        message="Student assignment decision saved successfully",
        status_code=status.HTTP_200_OK,
    )


@router.get(
    "/monthly-records",
    response_model=StandardResponseSchema[
        PaginatedDataSchema[MonthlyRecordResponseSchema]
    ],
)
async def list_teacher_monthly_records(
    _service: Annotated[TeacherService, Depends()],
    principal: Annotated[
        AuthenticatedPrincipal, Depends(get_current_principal)
    ],
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
):
    if principal.zone_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The teacher is not assigned to a zone.",
        )
    result = _service.list_monthly_records(
        principal.actor_id, principal.zone_id, offset, limit
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
        str(record_id),
        request.approved,
        principal.actor_id,
        principal.zone_id,
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
