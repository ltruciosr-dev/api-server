# api_metas/main.py
import os
import psycopg2
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI()

DB_HOST = os.getenv("DATABASE_HOST", "172.31.82.228")
DB_PORT = os.getenv("DATABASE_PORT", "5434")
DB_NAME = os.getenv("DATABASE_NAME", "ml_metas")
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

class Campaign(BaseModel):
    name: str
    goal: float
    cashback_percentage: float
    start_date: str  # Use ISO format (YYYY-MM-DD)
    end_date: str

@app.get("/campaigns", response_model=List[Campaign])
def get_campaigns():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT name, goal, cashback_percentage, start_date, end_date FROM campaigns")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        Campaign(
            name=row[0],
            goal=float(row[1]),
            cashback_percentage=float(row[2]),
            start_date=str(row[3]),
            end_date=str(row[4])
        ) for row in rows
    ]

@app.post("/campaigns", response_model=dict)
def add_campaign(campaign: Campaign):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO campaigns (name, goal, cashback_percentage, start_date, end_date) VALUES (%s, %s, %s, %s, %s) RETURNING id",
        (campaign.name, campaign.goal, campaign.cashback_percentage, campaign.start_date, campaign.end_date)
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return {"id": new_id}