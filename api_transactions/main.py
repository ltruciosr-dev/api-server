# api_transactions/main.py
import os
import psycopg2
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI()

DB_HOST = os.getenv("DATABASE_HOST", "172.31.82.228")
DB_PORT = os.getenv("DATABASE_PORT", "5433")
DB_NAME = os.getenv("DATABASE_NAME", "core_transactions")
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

class Transaction(BaseModel):
    user_id: int
    amount: float
    merchant: str
    account_type: str
    status: str

@app.get("/transactions/mastercard", response_model=List[Transaction])
def get_mastercard_transactions():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id, amount, merchant, account_type, status FROM transactions_mastercard")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        Transaction(
            user_id=row[0],
            amount=float(row[1]),
            merchant=row[2],
            account_type=row[3],
            status=row[4]
        ) for row in rows
    ]

@app.post("/transactions/mastercard", response_model=dict)
def add_mastercard_transaction(trx: Transaction):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO transactions_mastercard (user_id, amount, merchant, account_type, status) VALUES (%s, %s, %s, %s, %s) RETURNING id",
        (trx.user_id, trx.amount, trx.merchant, trx.account_type, trx.status)
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return {"id": new_id}