# tests/test_e2e_flow.py

import pytest
import subprocess
import time
import requests
import re
from playwright.sync_api import Page, expect
from backend.database import clear_db, DB_FILE, get_db_connection, init_db

BACKEND_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://127.0.0.1:8501"

def wait_for_server(url: str, timeout: int = 20):
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
    clear_db()
    backend_process = subprocess.Popen(
        ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
    )
    frontend_process = subprocess.Popen(
        ["streamlit", "run", "app.py", "--server.port", "8501", "--server.headless", "true"],
        cwd="frontend"
    )
    wait_for_server(BACKEND_URL)
    # Give streamlit an initial generous sleep, the test will handle the rest.
    time.sleep(5)
    yield
    backend_process.terminate()
    frontend_process.terminate()
    clear_db()

# --- THE FIXES ARE IN THESE TWO TEST FUNCTIONS ---

def test_full_user_journey(page: Page):
    page.goto(FRONTEND_URL)
    
    # --- REGISTRATION ---
    # EXPLICIT WAIT: Wait for the main header to appear before doing anything else.
    # This ensures the Streamlit app has loaded.
    expect(page.get_by_role("heading", name="Register New User")).to_be_visible(timeout=15000)

    # Now that we know the page is ready, we can use simpler selectors.
    # Streamlit uses unique keys for inputs, which we can leverage.
    page.locator('input[aria-label="Username"]').first.fill("e2e_user")
    page.locator('input[aria-label="Password"]').first.fill("SuperSecure123!")
    page.get_by_role("button", name="Register").click()
    
    expect(page.get_by_text("Registration successful! Please log in.")).to_be_visible()

    # --- LOGIN ---
    page.get_by_text("Login", exact=True).click()
    expect(page.get_by_role("heading", name="Login")).to_be_visible()
    
    # Use the same robust selector strategy for the login form.
    page.locator('input[aria-label="Username"]').last.fill("e2e_user")
    page.locator('input[aria-label="Password"]').last.fill("SuperSecure123!")
    page.get_by_role("button", name="Login").click()

    # --- VERIFY DASHBOARD ---
    expect(page.get_by_role("heading", name=re.compile("Welcome, e2e_user"))).to_be_visible()
    expect(page.get_by_text("This is your secret dashboard.")).to_be_visible()

def test_login_with_invalid_credentials(page: Page):
    page.goto(FRONTEND_URL)
    
    # --- REGISTRATION ---
    expect(page.get_by_role("heading", name="Register New User")).to_be_visible(timeout=15000)
    page.locator('input[aria-label="Username"]').first.fill("test_user_2")
    page.locator('input[aria-label="Password"]').first.fill("correct_password")
    page.get_by_role("button", name="Register").click()
    expect(page.get_by_text("Registration successful! Please log in.")).to_be_visible()

    # --- LOGIN with wrong credentials ---
    page.get_by_text("Login", exact=True).click()
    expect(page.get_by_role("heading", name="Login")).to_be_visible()

    # We use .last because the login form now appears second on the page's DOM.
    page.locator('input[aria-label="Username"]').last.fill("test_user_2")
    page.locator('input[aria-label="Password"]').last.fill("wrong_password")
    page.get_by_role("button", name="Login").click()

    # --- VERIFY FAILURE ---
    expect(page.get_by_text("Login failed: Invalid credentials.")).to_be_visible()