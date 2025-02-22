# api_metas/main.py
import os
from fastapi import FastAPI, HTTPException, Path
from pydantic import BaseModel
from typing import List
import psycopg2

app = FastAPI(title="API Metas")

# Database connection for ML METAS
DB_HOST = os.getenv("DATABASE_HOST", "172.31.82.228")
DB_PORT = os.getenv("DATABASE_PORT", "5434")
DB_NAME = os.getenv("DATABASE_NAME", "ml_metas")
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

# ----- Models for Campaigns Management -----
class Campaign(BaseModel):
    name: str
    goal: float
    cashback_percentage: float
    start_date: str  # ISO date string (YYYY-MM-DD)
    end_date: str
    # Optionally, you could include a "status" field

class CampaignUpdate(BaseModel):
    name: str = None
    goal: float = None
    cashback_percentage: float = None
    start_date: str = None
    end_date: str = None

# ---------- Endpoints for Campaigns Management ----------

@app.get("/campaigns/{campaign_id}")
def get_campaign(campaign_id: int = Path(..., title="Campaign ID")):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, name, goal, cashback_percentage, start_date, end_date FROM campaigns WHERE id = %s", (campaign_id,))
        camp = cur.fetchone()
        if not camp:
            raise HTTPException(status_code=404, detail="Campaign not found")
        return {
            "id": camp[0],
            "name": camp[1],
            "goal": float(camp[2]),
            "cashback_percentage": float(camp[3]),
            "start_date": str(camp[4]),
            "end_date": str(camp[5])
        }
    finally:
        cur.close()
        conn.close()

@app.get("/users/{user_id}/campaigns")
def get_user_campaigns(user_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Retrieve campaigns assigned to a user via the user_campaigns join table.
        query = """
            SELECT c.id, c.name, c.goal, c.cashback_percentage, c.start_date, c.end_date
            FROM campaigns c
            JOIN user_campaigns uc ON c.id = uc.campaign_id
            WHERE uc.user_id = %s
        """
        cur.execute(query, (user_id,))
        camps = cur.fetchall()
        return [
            {
                "id": row[0],
                "name": row[1],
                "goal": float(row[2]),
                "cashback_percentage": float(row[3]),
                "start_date": str(row[4]),
                "end_date": str(row[5])
            } for row in camps
        ]
    finally:
        cur.close()
        conn.close()

@app.post("/campaigns", status_code=201)
def create_campaign(campaign: Campaign):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO campaigns (name, goal, cashback_percentage, start_date, end_date) VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (campaign.name, campaign.goal, campaign.cashback_percentage, campaign.start_date, campaign.end_date)
        )
        camp_id = cur.fetchone()[0]
        conn.commit()
        return {"id": camp_id}
    finally:
        cur.close()
        conn.close()

@app.put("/campaigns/{campaign_id}")
def update_campaign(campaign_id: int, camp_update: CampaignUpdate):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        if camp_update.name:
            cur.execute("UPDATE campaigns SET name = %s WHERE id = %s", (camp_update.name, campaign_id))
        if camp_update.goal is not None:
            cur.execute("UPDATE campaigns SET goal = %s WHERE id = %s", (camp_update.goal, campaign_id))
        if camp_update.cashback_percentage is not None:
            cur.execute("UPDATE campaigns SET cashback_percentage = %s WHERE id = %s", (camp_update.cashback_percentage, campaign_id))
        if camp_update.start_date:
            cur.execute("UPDATE campaigns SET start_date = %s WHERE id = %s", (camp_update.start_date, campaign_id))
        if camp_update.end_date:
            cur.execute("UPDATE campaigns SET end_date = %s WHERE id = %s", (camp_update.end_date, campaign_id))
        conn.commit()
        return {"message": "Campaign updated successfully"}
    finally:
        cur.close()
        conn.close()

@app.delete("/campaigns/{campaign_id}")
def delete_campaign(campaign_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Logical deletion: update status to 'inactive'. Assuming campaigns table has a "status" column.
        cur.execute("UPDATE campaigns SET status = 'inactive' WHERE id = %s", (campaign_id,))
        conn.commit()
        return {"message": "Campaign logically deleted"}
    finally:
        cur.close()
        conn.close()