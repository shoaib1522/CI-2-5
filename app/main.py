# app/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .database import get_db_connection, init_db

# ... (rest of the file is the same) ...

app = FastAPI()
conn = get_db_connection()
init_db(conn)

class User(BaseModel):
    username: str
    password: str

# --- ADD THIS NEW ENDPOINT ---
@app.get("/health")
def health_check():
    """A simple endpoint to verify that the API is running."""
    return {"status": "ok"}
# -----------------------------

@app.post("/register")
def register(user: User):
    # ... (rest of the function is the same) ...
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (user.username, user.password)
        )
        conn.commit()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not register user. Error: {e}")
    return {"message": "User registered successfully"}


@app.post("/login")
def login(user: User):
    # ... (rest of the function is the same) ...
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (user.username, user.password)
    )
    result = cursor.fetchone()
    if result:
        return {"message": "Login successful", "token": "fake-jwt-token-for-e2e-test"}
    
    raise HTTPException(status_code=401, detail="Invalid username or password")