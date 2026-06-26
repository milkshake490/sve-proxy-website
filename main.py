from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

@app.get("/cards")
def search_cards(name: str = ""):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT card_name, image_url, set_code, card_number FROM cards WHERE card_name ILIKE %s LIMIT 30",
        (f"%{name}%",)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {
            "card_name": r[0],
            "image_url": r[1],
            "set_code": r[2],
            "card_number": r[3]
        }
        for r in rows
    ]