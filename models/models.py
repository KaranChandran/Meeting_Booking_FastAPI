from pydantic import BaseModel, field_validator
from datetime import date, time
import re

class Booking(BaseModel):
    customer_name: str
    date: date        # Validates YYYY-MM-DD
    time: time        # Validates HH:MM (24-hour)
    description: str | None = None


    #customer name format validation
    @field_validator("customer_name")
    def valid_name(cls, value):
        if not re.match(r"^[A-Za-z\s'-]+$", value):
            raise ValueError("Customer name should contain only letters and spaces.")
        return value

    #do not allow past dates
    @field_validator("date")
    def prevent_past_date(cls, value):
        if value < date.today():
            raise ValueError("Cannot book past dates!")
        return value

    #restrict time to 08:00–20:00 for real-world booking
    @field_validator("time")
    def valid_time_range(cls, value):
        if value.tzinfo is not None:
            value = value.replace(tzinfo=None)

        if value < time(8, 0) or value > time(20, 0):#8:00AM to 8:00PM
            raise ValueError("Booking allowed only between 08:00 and 20:00")
        return value
