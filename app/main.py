# app/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .database import get_db_connection, init_db

# Create the FastAPI app instance
app = FastAPI()
# Establish a single, shared database connection for the app's lifecycle
conn = get_db_connection()
# Ensure the 'users' table exists when the app starts
init_db(conn)

# Pydantic models for request validation
class User(BaseModel):
    username: str
    password: str

@app.post("/register")
def register(user: User):
    """Endpoint to register a new user."""
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (user.username, user.fget)
        )
        conn.commit()
    except Exception as e:
        # A simple catch-all for errors, like a duplicate username
        raise HTTPException(status_code=400, detail=f"Could not register user. Error: {e}")
    return {"message": "User registered successfully"}

@app.post("/login")
def login(user: User):
    """Endpoint to log in a user and return a fake token."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (user.username, user.password)
    )
    result = cursor.fetchone()
    if result:
        # In a real app, you would generate a real JWT here.
        return {"message": "Login successful", "token": "fake-jwt-token-for-e2e-test"}
    
    # If no user is found, raise an authentication error.
    raise HTTPException(status_code=401, detail="Invalid username or password")