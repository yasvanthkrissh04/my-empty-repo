"""Request and response shapes used by the API."""

from datetime import datetime
import re

from pydantic import BaseModel, Field, field_validator


# Deliberately small, practical validation for a recruitment assignment.
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class RegistrationCreate(BaseModel):
    """Information a student submits when registering."""

    name: str = Field(
        ..., min_length=2, max_length=100, description="Student's full name"
    )
    email: str = Field(..., max_length=254, description="Student's email address")
    college_department: str | None = Field(
        default=None,
        max_length=150,
        description="College and/or department (optional)",
    )

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Name must contain at least 2 characters")
        return value

    @field_validator("email")
    @classmethod
    def clean_and_validate_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not EMAIL_PATTERN.fullmatch(value):
            raise ValueError("Please provide a valid email address")
        return value

    @field_validator("college_department")
    @classmethod
    def clean_optional_department(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class Registration(BaseModel):
    """A registration stored in the database."""

    id: int
    name: str
    email: str
    college_department: str | None
    registered_at: datetime


class EventStatus(BaseModel):
    name: str
    date: str
    capacity: int
    registered_count: int
    remaining_seats: int


class RegistrationCreated(BaseModel):
    message: str
    registration: Registration
    event: EventStatus


class RegistrationList(BaseModel):
    event: EventStatus
    registrations: list[Registration]


class HealthCheck(BaseModel):
    status: str
