# api_users/main.py
import os
from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import psycopg2

app = FastAPI(title="API Users")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can also use ["*"] to allow all origins, but be cautious in production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection for CORE USERS
DB_HOST = os.getenv("DATABASE_HOST", "172.31.82.228")
DB_PORT = os.getenv("DATABASE_PORT", "5432")
DB_NAME = os.getenv("DATABASE_NAME", "core_users")
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

# In-memory store for billetera_users (Wallet Management)
wallet_store = {}

# ----- Models for User Management -----
class User(BaseModel):
    name: str
    email: str
    # Additional fields for demographics, onboarding, etc. can be added here.

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None

# ----- Models for Account Management -----
class Account(BaseModel):
    account_type: str
    balance: float
    currency: str

class AccountUpdate(BaseModel):
    account_type: Optional[str] = None
    balance: Optional[float] = None
    currency: Optional[str] = None

# ----- Models for Credit Cards (maps to card_info) -----
class CreditCard(BaseModel):
    card_number: str
    expiration_date: str  # ISO date format: YYYY-MM-DD
    status: Optional[str] = "active"

class CreditCardUpdate(BaseModel):
    expiration_date: Optional[str] = None
    status: Optional[str] = None

# ----- Models for Wallet Management (NoSQL simulated) -----
class WalletItem(BaseModel):
    type: str  # e.g., "card" or "savings"
    details: dict

# ---------- Endpoints for User Management ----------

@app.get("/users/{user_id}")
def get_user(user_id: int = Path(..., title="The ID of the user to retrieve")):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, name, email FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        # In a real implementation, you would also join demographics, onboarding, and user_status.
        return {"id": user[0], "name": user[1], "email": user[2]}
    finally:
        cur.close()
        conn.close()

@app.post("/users", status_code=201)
def create_user(user: User):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (name, email) VALUES (%s, %s) RETURNING id",
            (user.name, user.email)
        )
        user_id = cur.fetchone()[0]
        conn.commit()
        # Here you would also insert default rows into demographics, onboarding, and user_status.
        return {"id": user_id, "name": user.name, "email": user.email}
    finally:
        cur.close()
        conn.close()

@app.put("/users/{user_id}")
def update_user(user_id: int, user: UserUpdate):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Update only provided fields (simplified update on users table)
        if user.name:
            cur.execute("UPDATE users SET name = %s WHERE id = %s", (user.name, user_id))
        if user.email:
            cur.execute("UPDATE users SET email = %s WHERE id = %s", (user.email, user_id))
        conn.commit()
        return {"message": "User updated successfully"}
    finally:
        cur.close()
        conn.close()

@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Logical deletion: update status to 'deleted' in user_status
        cur.execute("UPDATE user_status SET status = 'deleted' WHERE user_id = %s", (user_id,))
        conn.commit()
        return {"message": "User logically deleted"}
    finally:
        cur.close()
        conn.close()

# ---------- Endpoints for Account Management ----------

@app.get("/users/{user_id}/accounts")
def get_accounts(user_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, account_type, balance, currency FROM accounts WHERE user_id = %s", (user_id,))
        accounts = cur.fetchall()
        return [{"id": row[0], "account_type": row[1], "balance": float(row[2]), "currency": row[3]} for row in accounts]
    finally:
        cur.close()
        conn.close()

@app.post("/users/{user_id}/accounts", status_code=201)
def create_account(user_id: int, account: Account):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO accounts (user_id, account_type, balance, currency) VALUES (%s, %s, %s, %s) RETURNING id",
            (user_id, account.account_type, account.balance, account.currency)
        )
        account_id = cur.fetchone()[0]
        conn.commit()
        return {"id": account_id, **account.dict()}
    finally:
        cur.close()
        conn.close()

@app.put("/users/{user_id}/accounts/{account_id}")
def update_account(user_id: int, account_id: int, account: AccountUpdate):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        if account.account_type:
            cur.execute("UPDATE accounts SET account_type = %s WHERE id = %s AND user_id = %s", (account.account_type, account_id, user_id))
        if account.balance is not None:
            cur.execute("UPDATE accounts SET balance = %s WHERE id = %s AND user_id = %s", (account.balance, account_id, user_id))
        if account.currency:
            cur.execute("UPDATE accounts SET currency = %s WHERE id = %s AND user_id = %s", (account.currency, account_id, user_id))
        conn.commit()
        return {"message": "Account updated successfully"}
    finally:
        cur.close()
        conn.close()

@app.delete("/users/{user_id}/accounts/{account_id}")
def delete_account(user_id: int, account_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Logical deletion: update a status field (assuming accounts has a status column)
        cur.execute("UPDATE accounts SET status = 'deleted' WHERE id = %s AND user_id = %s", (account_id, user_id))
        conn.commit()
        return {"message": "Account logically deleted"}
    finally:
        cur.close()
        conn.close()

# ---------- Endpoints for Credit Cards (using card_info) ----------

@app.get("/users/{user_id}/credit-cards")
def get_credit_cards(user_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, card_number, expiration_date, status FROM card_info WHERE account_id IN (SELECT id FROM accounts WHERE user_id = %s)", (user_id,))
        cards = cur.fetchall()
        return [{"id": row[0], "card_number": row[1], "expiration_date": str(row[2]), "status": row[3]} for row in cards]
    finally:
        cur.close()
        conn.close()

@app.post("/users/{user_id}/credit-cards", status_code=201)
def create_credit_card(user_id: int, card: CreditCard):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # For simplicity, assume a user has a primary account and we get its id:
        cur.execute("SELECT id FROM accounts WHERE user_id = %s LIMIT 1", (user_id,))
        account = cur.fetchone()
        if not account:
            raise HTTPException(status_code=404, detail="User account not found")
        account_id = account[0]
        cur.execute(
            "INSERT INTO card_info (account_id, card_number, expiration_date, status) VALUES (%s, %s, %s, %s) RETURNING id",
            (account_id, card.card_number, card.expiration_date, card.status)
        )
        card_id = cur.fetchone()[0]
        conn.commit()
        return {"id": card_id}
    finally:
        cur.close()
        conn.close()

@app.put("/users/{user_id}/credit-cards/{card_id}")
def update_credit_card(user_id: int, card_id: int, card: CreditCardUpdate):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        if card.expiration_date:
            cur.execute("UPDATE card_info SET expiration_date = %s WHERE id = %s", (card.expiration_date, card_id))
        if card.status:
            cur.execute("UPDATE card_info SET status = %s WHERE id = %s", (card.status, card_id))
        conn.commit()
        return {"message": "Credit card updated successfully"}
    finally:
        cur.close()
        conn.close()

@app.delete("/users/{user_id}/credit-cards/{card_id}")
def delete_credit_card(user_id: int, card_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Logical deletion: update status to 'deleted'
        cur.execute("UPDATE card_info SET status = 'deleted' WHERE id = %s", (card_id,))
        conn.commit()
        return {"message": "Credit card logically deleted"}
    finally:
        cur.close()
        conn.close()

# # ---------- Endpoints for Wallet Management (NoSQL simulated) ----------

# @app.get("/users/{user_id}/wallet")
# def get_wallet(user_id: int):
#     # Retrieve wallet data from the in-memory store
#     wallet = wallet_store.get(user_id, [])
#     return {"wallet": wallet}

# @app.post("/users/{user_id}/wallet", status_code=201)
# def add_wallet_item(user_id: int, item: WalletItem):
#     wallet = wallet_store.get(user_id, [])
#     wallet.append(item.dict())
#     wallet_store[user_id] = wallet
#     return {"message": "Wallet item added", "wallet": wallet}

# @app.put("/users/{user_id}/wallet")
# def update_wallet(user_id: int, items: List[WalletItem]):
#     # Replace the current wallet data with the new list
#     wallet_store[user_id] = [item.dict() for item in items]
#     return {"message": "Wallet updated", "wallet": wallet_store[user_id]}