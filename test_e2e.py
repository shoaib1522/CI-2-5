# test_e2e.py

import pytest
import subprocess
import time
import requests
import os
from app.database import DB_FILE, clear_db, init_db, get_db_connection

BASE_URL = "http://127.0.0.1:8000"

@pytest.fixture(scope="module", autouse=True)
def api_server():
    """
    Starts the FastAPI server as a background process and waits for it to be healthy.
    """
    # --- Setup ---
    clear_db()
    conn = get_db_connection()
    init_db(conn)
    conn.close()

    server_process = subprocess.Popen(
        ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
    )
    
    # --- THIS IS THE FIX: Replace time.sleep() with a polling loop ---
    start_time = time.time()
    while time.time() - start_time < 20:  # Max wait time of 20 seconds
        try:
            response = requests.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                print("Server is up and running!")
                break  # Exit the loop if the server is healthy
        except requests.exceptions.ConnectionError:
            time.sleep(1) # Wait 1 second before trying again
    else:
        # This block runs if the loop completes without a 'break'
        server_process.terminate()
        pytest.fail("Server did not become healthy within 20 seconds.")
    # ----------------------------------------------------------------

    yield # Pass control to the tests
    
    # --- Teardown ---
    server_process.terminate()
    clear_db()

# --- THE ACTUAL TESTS REMAIN UNCHANGED ---

def test_full_user_flow():
    """
    An end-to-end test simulating a full user journey: register, then log in.
    """
    register_payload = {"username": "e2e_user", "password": "a_secure_password_123"}
    register_response = requests.post(f"{BASE_URL}/register", json=register_payload)
    assert register_response.status_code == 200

    login_payload = {"username": "e2e_user", "password": "a_secure_password_123"}
    login_response = requests.post(f"{BASE_URL}/login", json=login_payload)
    assert login_response.status_code == 200
    assert "token" in login_response.json()

def test_login_with_invalid_credentials():
    """
    Tests that the server correctly rejects a login attempt with a wrong password.
    """
    requests.post(f"{BASE_URL}/register", json={"username": "test_user_2", "password": "correct_password"})
    invalid_login_payload = {"username": "test_user_2", "password": "wrong_password"}
    login_response = requests.post(f"{BASE_URL}/login", json=invalid_login_payload)
    assert login_response.status_code == 401