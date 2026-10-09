import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.schemas.standerd_response_schema import StandardResponseSchema
from src.schemas.student_schema import (
    GoogleLoginRequestSchema,
    MonthlyRecordResponseSchema,
    StudentRegisterRequestSchema,
    StudentResponseSchema,
)
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
    "/login/google",
    response_model=StandardResponseSchema[dict[str, str]],
    status_code=status.HTTP_200_OK,
)
async def login_with_google(
    request: GoogleLoginRequestSchema,
    _service: Annotated[StudentService, Depends()],
):
    result = _service.login_with_google(request.id_token)

    return StandardResponseSchema(
        data=result,
        message="Google login successful",
        status_code=status.HTTP_200_OK,
    )


@router.post(
    "/{student_id}/monthly-records",
    response_model=StandardResponseSchema[MonthlyRecordResponseSchema],
    status_code=status.HTTP_201_CREATED,
)
async def submit_monthly_record(
    student_id: uuid.UUID,
    _service: Annotated[StudentService, Depends()],
):
    result = _service.submit_monthly_record({"fk_stid": student_id})

    return StandardResponseSchema(
        data=MonthlyRecordResponseSchema.model_validate(result),
        message="Monthly record submitted successfully",
        status_code=status.HTTP_201_CREATED,
    )

