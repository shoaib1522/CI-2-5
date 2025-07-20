# tests/test_e2e_flow.py
import pytest
import subprocess
import time
import requests
from playwright.sync_api import Page, expect
from backend.database import clear_db

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

# tests/test_e2e_flow.py

# ... (imports are the same) ...

@pytest.fixture(scope="session", autouse=True)
def http_servers():
    """Fixture to start and stop both backend and frontend servers correctly."""
    clear_db()
    
    # --- THIS IS THE FIX FOR THE BACKEND ---
    # We tell Popen to run Python as a module (-m) with uvicorn.
    # We specify the app as 'backend.main:app'.
    # This makes Python's import system work correctly for relative imports.
    backend_process = subprocess.Popen(
        ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
    )

    # Start Frontend (Streamlit) - this command was correct.
    frontend_process = subprocess.Popen(
        ["streamlit", "run", "app.py", "--server.port", "8501", "--server.headless", "true"],
        cwd="frontend"
    )

    # Wait for both servers to be healthy
    wait_for_server(BACKEND_URL)
    time.sleep(5)
    
    yield
    
    backend_process.terminate()
    frontend_process.terminate()
    clear_db()

# ... (the rest of the test functions remain the same) ...
def test_full_user_journey(page: Page):
    """
    Tests the entire user flow from registration to viewing the dashboard.
    The 'page' argument is automatically provided by pytest-playwright.
    """
    # 1. Go to the Streamlit App's URL
    page.goto(FRONTEND_URL)
    
    # 2. Register a new user
    # Navigate to the registration page (it's the default)
    expect(page.get_by_text("Register New User")).to_be_visible()
    page.get_by_label("Username").fill("e2e_playwright_user")
    page.get_by_label("Password").fill("SuperSecure123!")
    page.get_by_role("button", name="Register").click()
    
    # Verify success message
    expect(page.get_by_text("Registration successful! Please log in.")).to_be_visible()

    # 3. Log in with the new user
    page.get_by_text("Login", exact=True).click() # Click the "Login" radio button in the sidebar
    expect(page.get_by_text("Login")).to_be_visible()
    page.get_by_label("Username").fill("e2e_playwright_user")
    page.get_by_label("Password").fill("SuperSecure123!")
    page.get_by_role("button", name="Login").click()

    # 4. Verify the dashboard is displayed
    # We expect the page to re-run and show the welcome header
    expect(page.get_by_role("heading", name="Welcome, e2e_playwright_user!")).to_be_visible()
    expect(page.get_by_text("This is your secret dashboard.")).to_be_visible()