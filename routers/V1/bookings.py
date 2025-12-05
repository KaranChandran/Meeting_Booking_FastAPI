from fastapi import APIRouter, HTTPException
from models.models import Booking
from database import get_connection, sqlite3
from datetime import datetime
from logger import logger

router = APIRouter(tags=["Bookings - v1"])

#Create Booking
@router.post("/")
def create_booking(b: Booking):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO bookings (customer_name, customer_email, customer_phone, date, time, description)
            VALUES (?, ?, ?, ?, ?, ?)""", (b.customer_name, b.customer_email, b.customer_phone, str(b.date), str(b.time), b.description))
    
        conn.commit()
        
        booking_id = cursor.lastrowid
        logger.info(f"New booking created with ID: {booking_id} for customer: {b.customer_name} on {b.date} at {b.time}")
        return {"status": "success", 
                "booking_id": booking_id, "message":"Your Booking Is Created Successfully..!", "info": b}
    
    except sqlite3.IntegrityError:
        logger.error(f"Failed to create booking for customer: {b.customer_name} on {b.date} at {b.time} - Slot already booked")
        raise HTTPException(status_code=400, detail="This slot is already booked!")
    
    except Exception as e:
        logger.exception("Unexpected error while creating booking")
        raise HTTPException(status_code=500, detail="Internal server error")
    
    finally:
        conn.close()

#Pagination + Filtering by date and customer_name
@router.get("/")
def get_bookings(
    page: int = 1,
    limit: int = 5,
    date_filter: str | None = None,          #filter by specific date (YYYY-MM-DD)
    customer: str | None = None            #filter by customer name (partial allowed)
    
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
            valid_date = datetime.strptime(date_filter, "%Y-%m-%d").date()
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
        raise HTTPException(status_code=400, detail="Invalid coustomer name | Try again..!")

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
    return {
        "total_records": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit,
        "bookings": [dict(row) for row in rows]
    }

#search by ID or NAME
@router.get("/search/{search_value}")
def get_booking(search_value : str):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        booking_id = int(search_value)
        cursor.execute("SELECT * FROM bookings WHERE id = ?",(booking_id,))
        row = cursor.fetchone()
        logger.info(f"Searching booking by ID: {booking_id}")
        
        if not row:
            logger.warning(f"Booking not found for ID: {booking_id}")
            raise HTTPException(status_code=404, detail="Booking not found")
        
        #return single row for ID
        logger.info(f"Booking found for ID: {booking_id}")
        return {"search_type": "id", "result": dict(row)}

    except ValueError:
        logger.info(f"Searching bookings by customer name containing: {search_value}")
        cursor.execute("""
        SELECT * FROM bookings
        WHERE LOWER(customer_name) LIKE LOWER(?)
        """,(f"%{search_value}%",))

        rows = cursor.fetchall()

        if not rows:
            logger.error(f"No bookings found for customer name containing: {search_value}")
            raise HTTPException(status_code=404, detail="Booking Not Found That Name... | Try Again..")
        
        #return multiple result(for name)
        logger.info(f"Found {len(rows)} bookings for customer name containing: {search_value}")
        return{
                "search_type": "name",
                "total_results": len(rows),
                "results": [dict(row) for row in rows]
        }
    finally:
        conn.close()

# Update Booking
@router.put("/{booking_id}")
def update_booking(booking_id: int, b: Booking):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
    old = cursor.fetchone()
    if not old:
        conn.close()
        logger.warning(f"Booking not found for update with ID: {booking_id}")
        raise HTTPException(status_code=404, detail="Booking not found")

    try:
        logger.info(f"Updating booking with ID: {booking_id}")
        cursor.execute("""
            UPDATE bookings
            SET customer_name=?, customer_email=?, customer_phone=?, date=?, time=?, description=?, version=version+1, updated_at=CURRENT_TIMESTAMP
            WHERE id=?""", (b.customer_name, b.customer_email, b.customer_phone, str(b.date), str(b.time), b.description, booking_id))
        conn.commit()

    except sqlite3.IntegrityError:
        conn.close()
        logger.error(f"Failed to update booking ID: {booking_id} - Slot already booked")
        raise HTTPException(status_code=400, detail="Slot already booked!")
    
    finally:
        conn.close()

    logger.info(f"Booking with ID: {booking_id} updated successfully")
    return{
            "status": "success",
            "info": {
                "booking_id": ["id"],
                "customer_name":["customer_name"],
                "customer_email": ["customer_email"],
                "customer_phone": ["customer_phone"],
                "date": ["date"],
                "time": ["time"],
                "description": ["description"],
                "version": ["version"],
                "updated_at": ["updated_at"]
            }
        }


#Cancel Booking
@router.delete("/{booking_id}")
def delete_booking(booking_id: int):
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
    return {"message": "Your Booking Is Canceled Successfully...!"}
