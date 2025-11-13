from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, validator
from datetime import date, time
from database import get_connection, sqlite3

app = FastAPI()

class Booking(BaseModel):
    customer_name: str
    date: date        # Validates YYYY-MM-DD
    time: time        # Validates HH:MM (24-hour)
    description: str | None = None



#Validator: do not allow past dates
@validator("date")
def prevent_past_date(cls, value):
    if value < date.today():
        raise ValueError("Cannot book past dates!")
    return value

#Validator: restrict time to 08:00–20:00 for real-world booking
@validator("time")
def valid_time_range(cls, value):
    if value < time(8, 0) or value > time(20, 0):#8:00AM to 8:00PM
        raise ValueError("Booking allowed only between 08:00 and 20:00")
    return value


#Create Booking
@app.post("/bookings")
def create_booking(b: Booking):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO bookings (customer_name, date, time, description)
            VALUES (?, ?, ?, ?)""", (b.customer_name, str(b.date), str(b.time), b.description))
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="This slot is already booked!")

    conn.commit()
    booking_id = cursor.lastrowid
    conn.close()

    return {"message": "Your Booking Is Created Successfully..!", 
            "booking_id": booking_id, 
            "data": b}


#Pagination + Filtering by date and customer_name
@app.get("/bookings")
def get_bookings(
    page: int = 1,
    limit: int = 5,
    date_filter: str | None = None,          #filter by specific date (YYYY-MM-DD)
    customer: str | None = None              #filter by customer name (partial allowed)
):
    #Validate pagination input
    if page < 1 or limit < 1:
        raise HTTPException(status_code=400, detail="page & limit must be positive numbers.")

    offset = (page - 1) * limit

    conn = get_connection()
    cursor = conn.cursor()

    #Build the WHERE conditions dynamically
    where_clauses = []
    params = []

    #Filter by date (exact match)
    if date_filter:
        where_clauses.append("date = ?")
        params.append(date_filter)
    else:
        raise HTTPException(status_code=400, detail="Invalid date format | use this YYYY-MM-DD")


    #Filter by customer name (partial search)
    if customer:
        where_clauses.append("customer_name LIKE ?")
        params.append(f"%{customer}%")  # partial match
        #raise HTTPException(status_code=400, detail="Invalid coustomer name | Try again..!")

    #If filters exist, join with AND
    where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    #1) Count total filtered records
    count_query = f"SELECT COUNT(*) FROM bookings{where_sql}"
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

    return {
        "total_records": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit,
        "bookings": [dict(row) for row in rows]
    }

#Get Single Booking
@app.get("/bookings/{booking_id}")
def get_booking(booking_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Booking not found")

    return dict(row)


# Update Booking
@app.put("/bookings/{booking_id}")
def update_booking(booking_id: int, b: Booking):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Booking not found")

    try:
        cursor.execute("""
            UPDATE bookings
            SET customer_name=?, date=?, time=?, description=?
            WHERE id=?""", (b.customer_name, str(b.date), str(b.time), b.description, booking_id))
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Slot already booked!")


    conn.commit()
    conn.close()

    return {"message": "Your Booking Is Updated Successfully...!", "data": b}


#Cancel Booking
@app.delete("/bookings/{booking_id}")
def delete_booking(booking_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Booking not found")

    cursor.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
    conn.commit()
    conn.close()

    return {"message": "Your Booking Is Canceled Successfully...!"}
