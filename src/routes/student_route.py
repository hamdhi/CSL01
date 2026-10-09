import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.core.security import AuthenticatedPrincipal, require_roles
from src.schemas.standerd_response_schema import StandardResponseSchema
from src.schemas.student_schema import (
    MonthlyRecordRequestSchema,
    MonthlyRecordResponseSchema,
    StudentRegisterRequestSchema,
    StudentResponseSchema,
)
from src.schemas.subject_schema import SubjectResponseSchema
from src.services.student_service import StudentService

router = APIRouter(prefix="/students", tags=["Students"])


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
    "/{student_id}/monthly-records",
    response_model=StandardResponseSchema[MonthlyRecordResponseSchema],
    status_code=status.HTTP_201_CREATED,
)
async def submit_monthly_record(
    student_id: uuid.UUID,
    request: MonthlyRecordRequestSchema,
    _service: Annotated[StudentService, Depends()],
    principal: Annotated[
        AuthenticatedPrincipal, Depends(require_roles("STUDENT"))
    ],
):
    if principal.actor_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only submit your own monthly record.",
        )
    request_data = request.model_dump()
    request_data["fk_stid"] = student_id
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
)
async def list_subjects(
    grade: str,
    _service: Annotated[StudentService, Depends()],
    stream: str = "",
):
    result = _service.list_subjects(grade, stream)
    return StandardResponseSchema(
        data=result,
        message="Subjects retrieved successfully",
        status_code=status.HTTP_200_OK,
    )
