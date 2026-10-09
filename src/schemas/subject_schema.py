import uuid

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SubjectCreateRequestSchema(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    grade: str = Field(min_length=1, max_length=20)
    stream: str = Field(default="", max_length=50)

    @model_validator(mode="after")
    def validate_stream(self):
        self.grade = self.grade.strip()
        self.stream = " ".join(self.stream.split()).casefold()
        if self.grade not in {"12", "13"} and self.stream:
            raise ValueError("A stream can only be assigned for Grades 12 or 13.")
        if self.grade in {"12", "13"} and not self.stream:
            raise ValueError("A stream is required for Grades 12 and 13.")
        return self


class SubjectResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    subject_id: uuid.UUID
    name: str
    grade: str
    stream: str
    active: bool


class SubjectUpdateRequestSchema(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    active: bool | None = None

    @model_validator(mode="after")
    def require_an_update(self):
        if self.name is None and self.active is None:
            raise ValueError("At least one subject field must be updated.")
        return self
