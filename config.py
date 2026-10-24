"""Central configuration for the event registration service."""

from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
DATABASE_PATH = PROJECT_DIR / "event_registrations.db"

EVENT_NAME = "Backend Development Workshop"
EVENT_DATE = "20 October 2026"
EVENT_CAPACITY = 50
