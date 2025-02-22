# api_users/main.py
import os
import psycopg2
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI()

# Read database connection details from environment variables
DB_HOST = os.getenv("DATABASE_HOST", "172.31.82.228")
DB_PORT = os.getenv("DATABASE_PORT", "5432")
DB_NAME = os.getenv("DATABASE_NAME", "core_users")
DB_USER = os.getenv("DATABASE_USER", "postgres")
DB_PASSWORD = os.getenv("DATABASE_PASSWORD", "postgres")

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail="Database connection error")

class User(BaseModel):
    name: str
    email: str

@app.get("/users", response_model=List[User])
def get_users():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT name, email FROM users")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [User(name=row[0], email=row[1]) for row in rows]

@app.post("/users", response_model=dict)
def add_user(user: User):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (name, email) VALUES (%s, %s) RETURNING id",
        (user.name, user.email)
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return {"id": new_id, "name": user.name, "email": user.email}