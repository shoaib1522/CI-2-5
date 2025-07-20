# backend/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .database import get_db_connection, init_db

app = FastAPI()
conn = get_db_connection()
init_db(conn)

class User(BaseModel):
    username: str
    password: str

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/register")
def register(user: User):
    cursor = conn.cursor()
    try:
        # --- THIS IS THE FIX ---
        # Ensure we are saving user.password, not a non-existent attribute.
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (user.username, user.password)
        )
        conn.commit()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": "User registered successfully"}

@app.post("/login")
def login(user: User):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (user.username, user.password)
    )
    if cursor.fetchone():
        return {"message": "Login successful", "token": f"fake-jwt-for-{user.username}"}
    raise HTTPException(status_code=401, detail="Invalid username or password")