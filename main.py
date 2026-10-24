"""FastAPI application for the Celestius event registration task."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status

import database
from config import EVENT_CAPACITY, EVENT_DATE, EVENT_NAME
from schemas import (
    EventStatus,
    HealthCheck,
    Registration,
    RegistrationCreate,
    RegistrationCreated,
    RegistrationList,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    database.initialize_database()
    yield


app = FastAPI(
    title="Celestius Event Registration API",
    description=(
        "A small backend for registering students for the Backend Development Workshop."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


def event_status() -> EventStatus:
    """Return event information with live availability figures."""
    registered_count = database.count_registrations()
    return EventStatus(
        name=EVENT_NAME,
        date=EVENT_DATE,
        capacity=EVENT_CAPACITY,
        registered_count=registered_count,
        remaining_seats=max(EVENT_CAPACITY - registered_count, 0),
    )


@app.get("/", tags=["General"])
def root() -> dict:
    return {
        "message": "Welcome to the Celestius Event Registration API",
        "documentation": "/docs",
    }


@app.get("/health", response_model=HealthCheck, tags=["General"])
def health_check() -> HealthCheck:
    """A small endpoint to confirm that the service is running."""
    return HealthCheck(status="ok")


@app.get("/event", response_model=EventStatus, tags=["Event"])
def get_event() -> EventStatus:
    """View event details and the number of seats currently available."""
    return event_status()


@app.post(
    "/register",
    response_model=RegistrationCreated,
    status_code=status.HTTP_201_CREATED,
    tags=["Registrations"],
    responses={
        409: {
            "description": "The email is already registered or the event is full."
        }
    },
)
def register_student(payload: RegistrationCreate) -> RegistrationCreated:
    """Register a student if their email is new and a seat is available."""
    try:
        registration = database.create_registration(**payload.model_dump())
    except database.DuplicateRegistrationError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A registration already exists for this email address.",
        )
    except database.EventFullError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Event is full. All 50 seats have been filled.",
        )

    return RegistrationCreated(
        message="Registration successful.",
        registration=registration,
        event=event_status(),
    )


@app.get("/registrations", response_model=RegistrationList, tags=["Registrations"])
def get_registrations() -> RegistrationList:
    """List every registered participant, oldest registration first."""
    return RegistrationList(
        event=event_status(),
        registrations=database.list_registrations(),
    )


@app.get(
    "/registrations/{registration_id}",
    response_model=Registration,
    tags=["Registrations"],
    responses={404: {"description": "Registration not found."}},
)
def get_registration(registration_id: int) -> Registration:
    """Retrieve one registration by its numeric ID."""
    registration = database.get_registration(registration_id)
    if registration is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registration not found.",
        )
    return Registration(**registration)
