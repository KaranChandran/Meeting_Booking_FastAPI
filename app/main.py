from contextlib import asynccontextmanager
from logging import getLogger
from fastapi import FastAPI

from app.api.v1.booking import router as bookings_v1
from app.utils.database import create_tables

logger = getLogger("booking_logger")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up the Booking API server...")
    create_tables()
    logger.info("Database tables created")

    yield  # App runs here

    # Shutdown
    logger.info("Shutting down the Booking API server...")


app = FastAPI(
    title="Booking API",
    version="1.0.0",
    description="A simple versioned Booking API using FastAPI",
    lifespan=lifespan
)

app.include_router(bookings_v1, prefix="/api/v1/bookings")
