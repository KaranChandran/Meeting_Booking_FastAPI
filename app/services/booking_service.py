from fastapi import HTTPException
from app.repositories.booking_repository import BookingRepository
from app.models.booking import BookingUpdate


class BookingService:
    def __init__(self):
        self.repository = BookingRepository()

    def update_booking(
        self,
        booking_id: int,
        update_data: BookingUpdate,
        expected_version: int
    ):
        # Fetch current booking
        current_booking = self.repository.get_by_id(booking_id)

        if not current_booking:
            raise HTTPException(status_code=404, detail="Booking not found")

        if getattr(current_booking, "deleted_at", None) is not None:
            raise HTTPException(status_code=404, detail="Booking was deleted")

        # Optimistic locking
        if current_booking.version != expected_version:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "OPTIMISTIC_LOCK_FAILURE",
                    "message": "Booking was modified by another process",
                    "expected_version": expected_version,
                    "current_version": current_booking.version
                }
            )

        updated_booking = self.repository.update_with_version(
            booking_id=booking_id,
            update_data=update_data,
            current_version=expected_version,
            new_version=expected_version + 1
        )

        return updated_booking
