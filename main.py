from fastapi import FastAPI
from routers.V1.bookings import router as bookings_v1

app = FastAPI(
    title="Booking API",
    version="1.0.0",
    description="A simple versioned Booking API using FastAPI"
)

# API Versioning
app.include_router(bookings_v1)

@app.get("/")
def root():
    return {
        "message": "Welcome to the Booking API",
        "available_versions": ["/v1/bookings"]
    }
