# tests/test_e2e_flow.py

import pytest
import subprocess
import time
import requests
from playwright.sync_api import Page, expect
from backend.database import clear_db, DB_FILE, get_db_connection, init_db

# Define server URLs
BACKEND_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://127.0.0.1:8501"

def wait_for_server(url: str, timeout: int = 20):
    """Polls a health check endpoint until the server is ready."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            if requests.get(f"{url}/health").status_code == 200:
                print(f"Server at {url} is healthy.")
                return
        except requests.ConnectionError:
            time.sleep(1)
    pytest.fail(f"Server at {url} did not become healthy within {timeout} seconds.")

@pytest.fixture(scope="session", autouse=True)
def http_servers():
    """Fixture to start and stop both backend and frontend servers correctly."""
    clear_db()
    
    backend_process = subprocess.Popen(
        ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
    )

    frontend_process = subprocess.Popen(
        ["streamlit", "run", "app.py", "--server.port", "8501", "--server.headless", "true"],
        cwd="frontend"
    )

    wait_for_server(BACKEND_URL)
    time.sleep(5)
    
    yield
    
    backend_process.terminate()
    frontend_process.terminate()
    clear_db()

def test_full_user_journey(page: Page):
    """
    Tests the entire user flow from registration to viewing the dashboard.
    """
    page.goto(FRONTEND_URL)
    
    # --- REGISTRATION ---
    expect(page.get_by_text("Register New User")).to_be_visible()
    
    # Use the more specific 'get_by_role' to avoid ambiguity
    page.get_by_role("textbox", name="Username").fill("e2e_playwright_user")
    page.get_by_role("textbox", name="Password").fill("SuperSecure123!")
    
    page.get_by_role("button", name="Register").click()
    expect(page.get_by_text("Registration successful! Please log in.")).to_be_visible()

    # --- LOGIN ---
    page.get_by_text("Login", exact=True).click()
    expect(page.get_by_text("Login")).to_be_visible()
    
    page.get_by_role("textbox", name="Username").fill("e2e_playwright_user")
    page.get_by_role("textbox", name="Password").fill("SuperSecure123!")
    
    page.get_by_role("button", name="Login").click()

    # --- VERIFY DASHBOARD ---
    expect(page.get_by_role("heading", name="Welcome, e2e_playwright_user!")).to_be_visible()
    expect(page.get_by_text("This is your secret dashboard.")).to_be_visible()

def test_login_with_invalid_credentials(page: Page):
    """
    Tests that the server correctly rejects a login attempt with a wrong password.
    """
    page.goto(FRONTEND_URL)
    
    # --- REGISTRATION (for the user we will test against) ---
    page.get_by_role("textbox", name="Username").fill("test_user_2")
    page.get_by_role("textbox", name="Password").fill("correct_password")
    page.get_by_role("button", name="Register").click()
    expect(page.get_by_text("Registration successful! Please log in.")).to_be_visible()

    # --- LOGIN with wrong credentials ---
    page.get_by_text("Login", exact=True).click()
    page.get_by_role("textbox", name="Username").fill("test_user_2")
    page.get_by_role("textbox", name="Password").fill("wrong_password")
    page.get_by_role("button", name_re="Login").click()

    # --- VERIFY FAILURE ---
    expect(page.get_by_text("Login failed: Invalid credentials.")).to_be_visible()