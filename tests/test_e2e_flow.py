# tests/test_e2e_flow.py

import pytest
import subprocess
import time
import requests
from playwright.sync_api import Page, expect
from backend.database import clear_db

# ... (the setup and fixture code remains exactly the same) ...
# ... (wait_for_server and http_servers fixtures are correct) ...

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

# --- THE FIX IS IN THIS TEST FUNCTION ---

def test_full_user_journey(page: Page):
    """
    Tests the entire user flow from registration to viewing the dashboard.
    """
    page.goto(FRONTEND_URL)
    
    # --- REGISTRATION ---
    expect(page.get_by_text("Register New User")).to_be_visible()
    
    # We are still looking for the label "Username", but we specify we want the input textbox.
    page.get_by_role("textbox", name="Username").fill("e2e_playwright_user")
    
    # THIS IS THE FIX: Be more specific. We want the textbox with the label "Password".
    # Playwright's `get_by_label` is good, but `get_by_role` is more precise here.
    page.get_by_role("textbox", name="Password").fill("SuperSecure123!")
    
    page.get_by_role("button", name="Register").click()
    expect(page.get_by_text("Registration successful! Please log in.")).to_be_visible()

    # --- LOGIN ---
    page.get_by_text("Login", exact=True).click()
    expect(page.get_by_text("Login")).to_be_visible()
    
    # Use the more specific selector here as well for consistency.
    page.get_by_role("textbox", name="Username").fill("e2e_playwright_user")
    page.get_by_role("textbox", name="Password").fill("SuperSecure123!")
    
    page.get_by_role("button", name="Login").click()

    # --- VERIFY DASHBOARD ---
    expect(page.get_by_role("heading", name="Welcome, e2e_playwright_user!")).to_be_visible()
    expect(page.get_by_text("This is your secret dashboard.")).to_be_visible()

# The second test can remain as it is, but for consistency, it's better to update it too.
def test_login_with_invalid_credentials(page: Page):
    """
    Tests that the server correctly rejects a login attempt with a wrong password.
    """
    page.goto(FRONTEND_URL)
    # Register the user first
    page.get_by_role("textbox", name="Username").fill("test_user_2")
    page.get_by_role("textbox", name