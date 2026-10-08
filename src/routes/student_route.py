import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.schemas.standerd_response_schema import StandardResponseSchema
from src.schemas.student_schema import (
    GoogleLoginRequestSchema,
    MonthlyRecordCreateRequestSchema,
    MonthlyRecordResponseSchema,
    StudentRegisterRequestSchema,
    StudentRegistrationDecisionSchema,
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
    request: MonthlyRecordCreateRequestSchema,
    _service: Annotated[StudentService, Depends()],
):
    result = _service.submit_monthly_record(
        {"fk_stid": student_id, **request.model_dump(exclude={"fk_stid"})}
    )

    return StandardResponseSchema(
        data=MonthlyRecordResponseSchema.model_validate(result),
        message="Monthly record submitted successfully",
        status_code=status.HTTP_201_CREATED,
    )


@router.patch(
    "/{student_id}/registration",
    response_model=StandardResponseSchema[StudentResponseSchema],
    status_code=status.HTTP_200_OK,
)
async def decide_student_registration(
    student_id: uuid.UUID,
    request: StudentRegistrationDecisionSchema,
    _service: Annotated[StudentService, Depends()],
):
    result = _service.decide_student_registration(
        str(student_id), request.approved
    )

    return StandardResponseSchema(
        data=StudentResponseSchema.model_validate(result),
        message="Student registration decision saved successfully",
        status_code=status.HTTP_200_OK,
    )


@router.post(
    "/{student_id}/login/reset",
    response_model=StandardResponseSchema[None],
    status_code=status.HTTP_200_OK,
)
async def reset_student_login(
    student_id: uuid.UUID,
    _service: Annotated[StudentService, Depends()],
):
    _service.reset_student_login(str(student_id))

    return StandardResponseSchema(
        data=None,
        message="Student login reset successfully",
        status_code=status.HTTP_200_OK,
    )
