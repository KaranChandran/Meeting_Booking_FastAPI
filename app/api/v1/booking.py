from fastapi import APIRouter, HTTPException, status, Depends
from app.models.booking import Booking
from app.utils.database import get_connection
from app.core.response import success_response, error_response
from app.core.idempotency import get_idempotency_key
from app.api.dependencies import admin_required
from app.core.logging import logger
from datetime import datetime
import sqlite3

router = APIRouter(tags=["Bookings - v1"])

#Create Booking
@router.post("/", status_code=status.HTTP_201_CREATED)
def create_booking(
    b: Booking,
    idempotency_key: str = Depends(get_idempotency_key),
):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO bookings
            (customer_name, customer_email, customer_phone, date, time, description)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            b.customer_name,
            b.customer_email,
            b.customer_phone,
            str(b.date),
            str(b.time),
            b.description,
        ))

        conn.commit()
        booking_id = cursor.lastrowid

        cursor.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
        row = dict(cursor.fetchone())

        return success_response(
            data=row,
            idempotency_key=idempotency_key,
        )

    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_response(
                code="SLOT_ALREADY_BOOKED",
                message=f"{b.customer_email} - This email ID is already reserved. Please use a different email.",
                details={"date": str(b.date), "time": str(b.time)},
            ),
        )

    finally:
        conn.close()


#Pagination + Filtering by date and customer_name
@router.get("/", status_code=status.HTTP_200_OK)
def get_bookings(
    page: int = 1,
    limit: int = 5,
    date_filter: str | None = None,          #filter by specific date (YYYY-MM-DD)
    customer: str | None = None,           #filter by customer name (partial allowed)
):
    
    #Validate pagination input
    if page < 1 or limit < 1:
        logger.warning(f"Invalid pagination parameters: page={page}, limit={limit}")
        raise HTTPException(status_code=400, detail="page & limit must be positive numbers.")

    offset = (page - 1) * limit

    conn = get_connection()
    cursor = conn.cursor()

    #Build the WHERE conditions dynamically
    where_clauses = []
    params = []

    #Filter by date (exact match)
    if date_filter:
        try:
            datetime.strptime(date_filter, "%Y-%m-%d")  # Validate date format
            where_clauses.append("date = ?")
            params.append(date_filter)
            logger.info(f"Filtering bookings by date: {date_filter}")
        
        except ValueError:
            logger.warning(f"Invalid date format provided for filtering: {date_filter}")
            raise HTTPException(status_code=400, detail="Invalid date format | use this YYYY-MM-DD")


    #Filter by customer name (partial search)
    if customer:
        where_clauses.append("customer_name LIKE ?")
        params.append(f"%{customer}%")  # partial match
        logger.info(f"Filtering bookings by customer name: {customer}")

    #If filters exist, join with AND----Build where clause
    where_sql = ""
    if where_clauses:
        where_sql = " WHERE " + " AND ".join(where_clauses)
    
    cursor.execute(f"SELECT * FROM bookings{where_sql}", params)
    rows = cursor.fetchall()
    
    if customer and not rows:
        logger.info(f"No bookings found for customer name filter: {customer}")
        raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="No bookings found for this customer"
)


    #1) Count total filtered records
    count_query = (f"SELECT COUNT(*) FROM bookings{where_sql}")
    cursor.execute(count_query, params)
    total = cursor.fetchone()[0]

    #2) Fetch paginated + filtered results
    data_query = f"""
        SELECT * FROM bookings
        {where_sql}
        ORDER BY id DESC
        LIMIT ? OFFSET ?
    """

    cursor.execute(data_query, (*params, limit, offset))

    rows = cursor.fetchall()
    conn.close()

    logger.info(f"Fetched bookings - page: {page}, limit: {limit}, total_records: {total}")
    return success_response(
        data={
        "total_records": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit,
        "bookings": [dict(row) for row in rows]
        },
    )

#search by ID or NAME
@router.get("/search/{search_value}", status_code=status.HTTP_200_OK)
def get_booking(booking_id_or_name : str):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        booking_id = int(booking_id_or_name)
        cursor.execute("SELECT * FROM bookings WHERE id = ?",(booking_id,))
        row = cursor.fetchone()
        logger.info(f"Searching booking by ID: {booking_id}")
        
        if not row:
            logger.warning(f"Booking not found for ID: {booking_id}")
            raise HTTPException(status_code=404, detail="Booking not found")
        
        #return single row for ID
        logger.info(f"Booking found for ID: {booking_id}")
        return success_response(
            data={"search_type": "id", "result": dict(row)},
        )

    except ValueError:
        logger.info(f"Searching bookings by customer name containing: {booking_id_or_name}")
        cursor.execute("""
        SELECT * FROM bookings
        WHERE LOWER(customer_name) LIKE LOWER(?)
        """,(f"%{booking_id_or_name}%",))

        rows = cursor.fetchall()

        if not rows:
            logger.error(f"No bookings found for customer name containing: {booking_id_or_name}")
            raise HTTPException(status_code=404, detail="Booking Not Found That ID | Name... | Try Again..")
        
        #return multiple result(for name)
        logger.info(f"Found {len(rows)} bookings for customer name containing: {booking_id_or_name}")
        return success_response(
            data={
                "search_type": "name",
                "total_results": len(rows),
                "results": [dict(row) for row in rows],
            }
)

    finally:
        conn.close()

# Update Booking
@router.put("/{booking_id}", status_code=status.HTTP_200_OK)
def update_booking(booking_id: int, b: Booking, idempotency_key: str = Depends(get_idempotency_key)):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
    old = cursor.fetchone()
    if not old:
        conn.close()
        logger.warning(f"Booking not found for update with ID: {booking_id}")
        raise HTTPException(status_code=404, detail="Booking not found")

    changed_fields = []

    if old["customer_name"] != b.customer_name:
        changed_fields.append("customer_name")

    if old["customer_email"] != b.customer_email:
        changed_fields.append("customer_email")

    if old["customer_phone"] != b.customer_phone:
        changed_fields.append("customer_phone")

    if old["date"] != str(b.date):
        changed_fields.append("date")

    if old["time"] != str(b.time):
        changed_fields.append("time")

    if old["description"] != b.description:
        changed_fields.append("description")

    try:
        # Update booking
        cursor.execute("""
            UPDATE bookings
            SET customer_name=?, customer_email=?, customer_phone=?,
                date=?, time=?, description=?,
                version=version+1,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        """, (
            b.customer_name,
            b.customer_email,
            b.customer_phone,
            str(b.date),
            str(b.time),
            b.description,
            booking_id
        ))

        # Save history
        if changed_fields:
            cursor.execute("""
                INSERT INTO booking_history
                (booking_id, updated_fields, updated_by)
                VALUES (?, ?, ?)
            """, (
                booking_id,
                ", ".join(changed_fields),
                "admin"
            ))

        conn.commit()

    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail=error_response(
                code="SLOT_ALREADY_BOOKED",
                message="Selected time slot already booked"
            )
        )
    finally:
        conn.close()

    logger.info(f"Booking with ID: {booking_id} updated successfully. Changed fields: {changed_fields}")
    return success_response(
        data={
            "info": b.dict(),
            "booking_id": booking_id,
            "updated_fields": changed_fields
        },
        idempotency_key=idempotency_key
    )

#Cancel Booking
@router.delete("/{booking_id}", status_code=status.HTTP_200_OK)
def delete_booking(booking_id: int, idempotency_key: str = Depends(get_idempotency_key)):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
    if not cursor.fetchone():
        conn.close()
        logger.warning(f"Booking not found for deletion with ID: {booking_id}")
        raise HTTPException(status_code=404, detail="Booking not found")

    cursor.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
    conn.commit()
    conn.close()

    logger.info(f"Booking with ID: {booking_id} deleted successfully")
    return success_response(
        data={"message": "Your Booking Is Canceled Successfully...!"},
        idempotency_key=idempotency_key
    )
# Get Booking Update History (Admin Only)
@router.get("/{booking_id}/history")
def booking_update_history(
    booking_id: int,
    _: str = Depends(admin_required)
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT updated_fields, updated_by, updated_at
        FROM booking_history
        WHERE booking_id = ?
        ORDER BY updated_at DESC
    """, (booking_id,))


    cursor.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
    if not cursor.fetchone():
        conn.close()
        logger.warning(f"Data not found for this ID: {booking_id}")
        raise HTTPException(status_code=404, detail="Data not found")

    rows = cursor.fetchall()
    conn.close()

    history = []
    for row in rows:
        history.append({
            "updated_fields": row["updated_fields"],
            "updated_by": row["updated_by"],
            "updated_at": row["updated_at"]
        })
    logger.info(f"Fetched update history for booking ID: {booking_id}, total records: {len(history)}")
    return success_response(
        data=history
    )