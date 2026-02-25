from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from db_connect import get_connection, get_connection_without_db, DB_NAME

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def ensure_database_and_table():
    # connect without specifying database to create it if needed
    conn = get_connection_without_db()
    try:
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        cursor.close()
    finally:
        conn.close()

    # connect to the database and ensure table exists
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS reservations (
              id INT AUTO_INCREMENT PRIMARY KEY,
              name VARCHAR(100),
              email VARCHAR(100),
              phone VARCHAR(20),
              date DATE,
              time VARCHAR(20),
              number_of_guests INT,
              message TEXT
            )
            """
        )
        cursor.close()
    finally:
        conn.close()


@app.on_event("startup")
def on_startup():
    try:
        ensure_database_and_table()
    except Exception as e:
        print("Warning: could not connect to MySQL at startup:", e)
        print("The app will still run. Start MySQL and retry requests.")


class Reservation(BaseModel):
    name: str
    email: str
    phone: str
    date: str
    time: str
    number_of_guests: int
    message: str = ""


@app.post("/reservations")
def create_reservation(r: Reservation):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        sql = "INSERT INTO reservations (name,email,phone,date,time,number_of_guests,message) VALUES (%s,%s,%s,%s,%s,%s,%s)"
        cursor.execute(sql, (r.name, r.email, r.phone, r.date, r.time, r.number_of_guests, r.message))
        cursor.close()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@app.get("/reservations")
def get_reservations(page: int = 1, limit: int = 20, search: Optional[str] = None, date: Optional[str] = None):
    """Return reservations with optional pagination and simple filtering.

    Query params:
    - page: page number (1-based)
    - limit: items per page
    - search: substring to match against `name`
    - date: exact date (YYYY-MM-DD)
    """
    offset = max(page - 1, 0) * max(limit, 1)
    base_where = []
    params = []
    if search:
        base_where.append("name LIKE %s")
        params.append(f"%{search}%")
    if date:
        base_where.append("date = %s")
        params.append(date)

    where_clause = ("WHERE " + " AND ".join(base_where)) if base_where else ""

    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        # total count
        count_sql = f"SELECT COUNT(*) as total FROM reservations {where_clause}"
        cursor.execute(count_sql, params)
        total = cursor.fetchone().get("total", 0)

        # fetch page
        data_sql = f"SELECT id, name, email, phone, date, time, number_of_guests, message FROM reservations {where_clause} ORDER BY date DESC, time DESC LIMIT %s OFFSET %s"
        cursor.execute(data_sql, params + [limit, offset])
        reservations = cursor.fetchall()
        cursor.close()

        return {"reservations": reservations, "total": total, "page": page, "limit": limit}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
