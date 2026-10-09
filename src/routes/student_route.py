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
    MonthlyRecordRequestSchema,
    MonthlyRecordResponseSchema,
    StudentDirectoryResponseSchema,
    StudentRegisterRequestSchema,
    StudentResponseSchema,
)
from src.schemas.subject_schema import SubjectResponseSchema
from src.schemas.teacher_schema import (
    TeacherAssignmentResponseSchema,
    TeacherLookupResponseSchema,
)
from src.services.student_service import StudentService

router = APIRouter(prefix="/students", tags=["Students"])


@router.get(
    "/teacher-assignments",
    response_model=StandardResponseSchema[list[TeacherAssignmentResponseSchema]],
    dependencies=[Depends(require_roles("STUDENT"))],
)
async def list_my_teacher_assignments(
    _service: Annotated[StudentService, Depends()],
    principal: Annotated[AuthenticatedPrincipal, Depends(get_current_principal)],
):
    result = _service.list_teacher_assignments(principal.actor_id)
    return StandardResponseSchema(
        data=[
            TeacherAssignmentResponseSchema.model_validate(assignment)
            for assignment in result
        ],
        message="Your teacher assignments retrieved successfully",
        status_code=status.HTTP_200_OK,
    )


@router.post(
    "/teachers/{teacher_code}/requests",
    response_model=StandardResponseSchema[TeacherAssignmentResponseSchema],
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_roles("STUDENT"))],
)
async def request_teacher_assignment(
    teacher_code: str,
    _service: Annotated[StudentService, Depends()],
    principal: Annotated[AuthenticatedPrincipal, Depends(get_current_principal)],
):
    assignment = _service.request_teacher_assignment(
        principal.actor_id, teacher_code
    )
    return StandardResponseSchema(
        data=TeacherAssignmentResponseSchema.model_validate(assignment),
        message="Teacher assignment request submitted for approval",
        status_code=status.HTTP_202_ACCEPTED,
    )


@router.get(
    "/teachers",
    response_model=StandardResponseSchema[
        PaginatedDataSchema[TeacherLookupResponseSchema]
    ],
)
async def list_registration_teachers(
    _service: Annotated[StudentService, Depends()],
    q: str | None = Query(default=None, min_length=1, max_length=100),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
):
    result = _service.list_available_teachers(q, offset, limit)
    result["items"] = [
        TeacherLookupResponseSchema.model_validate(teacher)
        for teacher in result["items"]
    ]
    return StandardResponseSchema(
        data=result,
        message="Approved teachers retrieved successfully",
        status_code=status.HTTP_200_OK,
    )


@router.get(
    "/teachers/{teacher_code}",
    response_model=StandardResponseSchema[TeacherLookupResponseSchema],
)
async def get_registration_teacher(
    teacher_code: str,
    _service: Annotated[StudentService, Depends()],
):
    teacher = _service.get_teacher_by_code(teacher_code)
    if teacher is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approved teacher not found.",
        )
    return StandardResponseSchema(
        data=TeacherLookupResponseSchema.model_validate(teacher),
        message="Approved teacher retrieved successfully",
        status_code=status.HTTP_200_OK,
    )


@router.get(
    "",
    response_model=StandardResponseSchema[
        PaginatedDataSchema[StudentDirectoryResponseSchema]
    ],
    dependencies=[Depends(require_roles("STUDENT"))],
)
async def list_students_in_zone(
    _service: Annotated[StudentService, Depends()],
    principal: Annotated[
        AuthenticatedPrincipal, Depends(get_current_principal)
    ],
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
):
    if principal.zone_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The student is not assigned to a zone.",
        )
    result = _service.list_zone_students(
        principal.zone_id, offset, limit
    )
    result["items"] = [
        StudentDirectoryResponseSchema.model_validate(item)
        for item in result["items"]
    ]
    return StandardResponseSchema(
        data=result,
        message="Students in your zone retrieved successfully",
        status_code=status.HTTP_200_OK,
    )


@router.get(
    "/monthly-records",
    response_model=StandardResponseSchema[
        PaginatedDataSchema[MonthlyRecordResponseSchema]
    ],
    dependencies=[Depends(require_roles("STUDENT"))],
)
async def list_own_monthly_records(
    _service: Annotated[StudentService, Depends()],
    principal: Annotated[
        AuthenticatedPrincipal, Depends(get_current_principal)
    ],
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
):
    result = _service.list_monthly_records(
        principal.actor_id, offset, limit
    )
    result["items"] = [
        MonthlyRecordResponseSchema.model_validate(record)
        for record in result["items"]
    ]
    return StandardResponseSchema(
        data=result,
        message="Your monthly marks retrieved successfully",
        status_code=status.HTTP_200_OK,
    )


@router.post(
    "/register",
    response_model=StandardResponseSchema[StudentResponseSchema],
    status_code=status.HTTP_201_CREATED,
)
async def register_student(
    request: StudentRegisterRequestSchema,
    _service: Annotated[StudentService, Depends()],
):
    result = _service.register_student(request.model_dump())

    return StandardResponseSchema(
        data=StudentResponseSchema.model_validate(result),
        message="Student registered successfully",
        status_code=status.HTTP_201_CREATED,
    )


@router.post(
    "/monthly-records",
    response_model=StandardResponseSchema[MonthlyRecordResponseSchema],
    status_code=status.HTTP_201_CREATED,
)
async def submit_monthly_record(
    request: MonthlyRecordRequestSchema,
    _service: Annotated[StudentService, Depends()],
    principal: Annotated[
        AuthenticatedPrincipal, Depends(require_roles("STUDENT"))
    ],
):
    request_data = request.model_dump()
    request_data["fk_stid"] = principal.actor_id
    result = _service.submit_monthly_record(request_data)

    return StandardResponseSchema(
        data=MonthlyRecordResponseSchema.model_validate(result),
        message="Monthly record submitted successfully",
        status_code=status.HTTP_201_CREATED,
    )


@router.get(
    "/subjects",
    response_model=StandardResponseSchema[list[SubjectResponseSchema]],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles("STUDENT"))],
)
async def list_subjects(
    _service: Annotated[StudentService, Depends()],
    principal: Annotated[
        AuthenticatedPrincipal, Depends(get_current_principal)
    ],
):
    result = _service.list_student_subjects(principal.actor_id)
    return StandardResponseSchema(
        data=result,
        message="Subjects retrieved successfully",
        status_code=status.HTTP_200_OK,
    )
