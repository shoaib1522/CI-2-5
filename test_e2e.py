# test_e2e.py

import pytest
import subprocess
import time
import requests
import os
from app.database import DB_FILE, clear_db, init_db, get_db_connection

# Define the base URL for the running server
BASE_URL = "http://127.0.0.1:8000"

@pytest.fixture(scope="module", autouse=True)
def api_server():
    """
    A module-scoped fixture to start and stop the FastAPI server once for all tests.
    This is much more efficient than starting a server for every single test.
    """
    # --- Setup ---
    # Ensure a clean state before starting the server
    clear_db()
    conn = get_db_connection()
    init_db(conn)
    conn.close()

    # Start the Uvicorn server as a background subprocess
    # We run it from the 'app' directory context.
    server_process = subprocess.Popen(
        ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd="app"
    )

    # Give the server a moment to start up
    time.sleep(3)
    
    # The 'yield' passes control to the tests
    yield
    
    # --- Teardown ---
    # After all tests in the module are done, terminate the server process
    server_process.terminate()
    clear_db()

def test_full_user_flow():
    """
    An end-to-end test simulating a full user journey: register, then log in.
    """
    # --- Step 1: Register a new user ---
    register_payload = {"username": "e2e_user", "password": "a_secure_password_123"}
    try:
        register_response = requests.post(f"{BASE_URL}/register", json=register_payload)
        # Assert that the registration was successful
        assert register_response.status_code == 200
        assert register_response.json() == {"message": "User registered successfully"}
    except requests.exceptions.ConnectionError as e:
        pytest.fail(f"Could not connect to the API server at {BASE_URL}. Is it running? Error: {e}")

    # --- Step 2: Attempt to log in with the new credentials ---
    login_payload = {"username": "e2e_user", "password": "a_secure_password_123"}
    login_response = requests.post(f"{BASE_URL}/login", json=login_payload)

    # Assert that the login was successful and a token was returned
    assert login_response.status_code == 200
    assert "token" in login_response.json()

def test_login_with_invalid_credentials():
    """
    Tests that the server correctly rejects a login attempt with a wrong password.
    """
    # --- Step 1: Register a user first ---
    # (This user is created fresh because the fixture cleans the DB for each module)
    requests.post(f"{BASE_URL}/register", json={"username": "test_user_2", "password": "correct_password"})

    # --- Step 2: Attempt to log in with the wrong password ---
    invalid_login_payload = {"username": "test_user_2", "password": "wrong_password"}
    login_response = requests.post(f"{BASE_URL}/login", json=invalid_login_payload)

    # Assert that the server returns a 401 Unauthorized error
    assert login_response.status_code == 401
    assert "Invalid username or password" in login_response.json()["detail"]