from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import date, time
from email_validator import validate_email, EmailNotValidError

class Booking(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=100, pattern=r"^[A-Za-z]+([ '-][A-Za-z]+)*$")
    customer_email: str = Field(..., max_length=255)
    customer_phone: str = Field(..., max_length=15, pattern=r"^\+?[1-9]\d{9,14}$")
    date: date
    time: time
    description: Optional[str] = Field(None, max_length=500)
    version: int = 1

    @field_validator("customer_email")
    def validate_email_field(cls, v):
        try:
            validate_email(v)
        except EmailNotValidError:
            raise ValueError("Invalid email format")
        return v

    @field_validator("date")
    def validate_future_date(cls, v):
        if v < date.today():
            raise ValueError("Date must be in the future")
        return v

    @field_validator("time")
    def validate_business_hours(cls, v):
        if v.tzinfo is not None:
            v = v.replace(tzinfo=None)
        if v < time(8, 0) or v > time(20, 0):
            raise ValueError("Time must be between 08:00 and 20:00")
        return v
