# api_transactions/main.py
import os
from fastapi import FastAPI, HTTPException, Path
from pydantic import BaseModel
from typing import List, Optional
import psycopg2

app = FastAPI(title="API Transactions")

# Database connection for CORE TRANSACTIONS
DB_HOST = os.getenv("DATABASE_HOST", "172.31.82.228")
DB_PORT = os.getenv("DATABASE_PORT", "5433")
DB_NAME = os.getenv("DATABASE_NAME", "core_transactions")
DB_USER = os.getenv("DATABASE_USER", "postgres")
DB_PASSWORD = os.getenv("DATABASE_PASSWORD", "postgres")

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT,
            dbname=DB_NAME, user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail="Database connection error")

# ----- Models for Transaction Management -----
class Transaction(BaseModel):
    user_id: int
    amount: float
    merchant: str
    account_type: str
    status: Optional[str] = "active"
    # In a real scenario, you might include a field to indicate which transaction table to use.

class TransactionUpdate(BaseModel):
    amount: Optional[float] = None
    merchant: Optional[str] = None
    account_type: Optional[str] = None
    status: Optional[str] = None

# ----- Models for Operations Management -----
class Operation(BaseModel):
    user_id: int
    description: str

class OperationUpdate(BaseModel):
    description: Optional[str] = None

# ---------- Endpoints for Transaction Management ----------

@app.get("/transactions/{transaction_id}")
def get_transaction(transaction_id: int = Path(..., title="Transaction ID")):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # For demonstration, we query the transactions_mastercard table.
        cur.execute("SELECT id, user_id, amount, merchant, account_type, status FROM transactions_mastercard WHERE id = %s", (transaction_id,))
        trx = cur.fetchone()
        if not trx:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return {
            "id": trx[0],
            "user_id": trx[1],
            "amount": float(trx[2]),
            "merchant": trx[3],
            "account_type": trx[4],
            "status": trx[5]
        }
    finally:
        cur.close()
        conn.close()

@app.get("/users/{user_id}/transactions")
def get_user_transactions(user_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Here we union transactions from three tables for demonstration.
        query = """
            SELECT id, user_id, amount, merchant, account_type, status FROM transactions_mastercard WHERE user_id = %s
            UNION
            SELECT id, user_id, amount, merchant, account_type, status FROM transactions_paypal WHERE user_id = %s
            UNION
            SELECT id, user_id, amount, merchant, account_type, status FROM transactions_internal WHERE user_id = %s
        """
        cur.execute(query, (user_id, user_id, user_id))
        transactions = cur.fetchall()
        return [
            {
                "id": row[0],
                "user_id": row[1],
                "amount": float(row[2]),
                "merchant": row[3],
                "account_type": row[4],
                "status": row[5]
            } for row in transactions
        ]
    finally:
        cur.close()
        conn.close()

@app.post("/transactions", status_code=201)
def create_transaction(trx: Transaction):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # For demonstration, we insert into transactions_mastercard.
        cur.execute(
            "INSERT INTO transactions_mastercard (user_id, amount, merchant, account_type, status) VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (trx.user_id, trx.amount, trx.merchant, trx.account_type, trx.status)
        )
        trx_id = cur.fetchone()[0]
        conn.commit()
        return {"id": trx_id}
    finally:
        cur.close()
        conn.close()

@app.put("/transactions/{transaction_id}")
def update_transaction(transaction_id: int, trx_update: TransactionUpdate):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Update fields in transactions_mastercard table as an example.
        if trx_update.amount is not None:
            cur.execute("UPDATE transactions_mastercard SET amount = %s WHERE id = %s", (trx_update.amount, transaction_id))
        if trx_update.merchant:
            cur.execute("UPDATE transactions_mastercard SET merchant = %s WHERE id = %s", (trx_update.merchant, transaction_id))
        if trx_update.account_type:
            cur.execute("UPDATE transactions_mastercard SET account_type = %s WHERE id = %s", (trx_update.account_type, transaction_id))
        if trx_update.status:
            cur.execute("UPDATE transactions_mastercard SET status = %s WHERE id = %s", (trx_update.status, transaction_id))
        conn.commit()
        return {"message": "Transaction updated successfully"}
    finally:
        cur.close()
        conn.close()

@app.delete("/transactions/{transaction_id}")
def delete_transaction(transaction_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Logical deletion: update status to 'deleted' in all transaction tables (example using transactions_mastercard).
        cur.execute("UPDATE transactions_mastercard SET status = 'deleted' WHERE id = %s", (transaction_id,))
        conn.commit()
        return {"message": "Transaction logically deleted"}
    finally:
        cur.close()
        conn.close()

# ---------- Endpoints for Operations Management ----------

@app.get("/operations/{operation_id}")
def get_operation(operation_id: int = Path(..., title="Operation ID")):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, user_id, description FROM operations WHERE id = %s", (operation_id,))
        op = cur.fetchone()
        if not op:
            raise HTTPException(status_code=404, detail="Operation not found")
        return {"id": op[0], "user_id": op[1], "description": op[2]}
    finally:
        cur.close()
        conn.close()

@app.get("/users/{user_id}/operations")
def get_user_operations(user_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, description FROM operations WHERE user_id = %s", (user_id,))
        ops = cur.fetchall()
        return [{"id": row[0], "description": row[1]} for row in ops]
    finally:
        cur.close()
        conn.close()

@app.post("/operations", status_code=201)
def create_operation(op: Operation):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO operations (user_id, description) VALUES (%s, %s) RETURNING id",
            (op.user_id, op.description)
        )
        op_id = cur.fetchone()[0]
        conn.commit()
        return {"id": op_id}
    finally:
        cur.close()
        conn.close()

@app.put("/operations/{operation_id}")
def update_operation(operation_id: int, op_update: OperationUpdate):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        if op_update.description:
            cur.execute("UPDATE operations SET description = %s WHERE id = %s", (op_update.description, operation_id))
        conn.commit()
        return {"message": "Operation updated successfully"}
    finally:
        cur.close()
        conn.close()