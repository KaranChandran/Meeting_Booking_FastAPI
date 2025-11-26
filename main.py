from fastapi import FastAPI
from logger import logger
from routers.V1.bookings import router as bookings_v1

app = FastAPI(
    title="Booking API",
    version="1.0.0",
    description="A simple versioned Booking API using FastAPI"
)
#server start_up
@app.on_event("startup")
def startup_event():
    logger.info("Starting up the Booking API server...")


# API Versioning
app.include_router(bookings_v1, prefix="/api/v1/bookings")