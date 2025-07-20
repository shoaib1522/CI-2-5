# frontend/app.py
import streamlit as st
import requests

API_BASE_URL = "http://127.0.0.1:8000" # The address of our FastAPI backend

st.set_page_config(layout="centered")

# Initialize session state for login status and token
if 'token' not in st.session_state:
    st.session_state['token'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = None

def register_page():
    st.header("Register New User")
    with st.form("register_form"):
        username = st.text_input("Username", key="reg_user")
        password = st.text_input("Password", type="password", key="reg_pass")
        submitted = st.form_submit_button("Register")
        if submitted:
            try:
                response = requests.post(
                    f"{API_BASE_URL}/register",
                    json={"username": username, "password": password}
                )
                if response.status_code == 200:
                    st.success("Registration successful! Please log in.")
                else:
                    st.error(f"Registration failed: {response.json().get('detail')}")
            except requests.ConnectionError:
                st.error("Could not connect to the backend API.")

def login_page():
    st.header("Login")
    with st.form("login_form"):
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        submitted = st.form_submit_button("Login")
        if submitted:
            try:
                response = requests.post(
                    f"{API_BASE_URL}/login",
                    json={"username": username, "password": password}
                )
                if response.status_code == 200:
                    data = response.json()
                    st.session_state['token'] = data.get("token")
                    st.session_state['username'] = username
                    st.rerun() # Re-run the script to show the dashboard
                else:
                    st.error("Login failed: Invalid credentials.")
            except requests.ConnectionError:
                st.error("Could not connect to the backend API.")

def dashboard_page():
    st.header(f"Welcome, {st.session_state.get('username')}!")
    st.success("You are logged in.")
    st.balloons()
    st.subheader("This is your secret dashboard.")
    if st.button("Logout"):
        st.session_state['token'] = None
        st.session_state['username'] = None
        st.rerun()

# Main app logic
if st.session_state['token']:
    dashboard_page()
else:
    page = st.sidebar.radio("Navigation", ["Register", "Login"])
    if page == "Register":
        register_page()
    else:
        login_page()