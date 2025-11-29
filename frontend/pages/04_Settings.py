import streamlit as st
import os

st.set_page_config(
    page_title="Settings - Task Manager",
    page_icon="⚙️",
    layout="wide"
)

st.title("⚙️ Settings")

# Configuration section
st.subheader("API Configuration")

api_url = st.text_input(
    "API URL",
    value=os.getenv("API_URL", "http://localhost:8000/api/v1"),
    help="Backend API endpoint URL"
)

if st.button("Save API URL"):
    # In a real app, you'd save this to a config file or environment
    st.success("API URL saved! (Note: Restart the app for changes to take effect)")

st.markdown("---")

# Notification settings
st.subheader("Notification Settings")

notification_enabled = st.checkbox("Enable Notifications", value=True)
reminder_time = st.time_input("Default Reminder Time", value=None)

if st.button("Save Notification Settings"):
    st.success("Notification settings saved!")

st.markdown("---")

# Display settings
st.subheader("Display Settings")

tasks_per_page = st.slider("Tasks per page", min_value=10, max_value=100, value=50)
default_view = st.selectbox("Default View", ["List View", "Calendar View"])

if st.button("Save Display Settings"):
    st.success("Display settings saved!")

st.markdown("---")

# About section
st.subheader("About")

st.markdown("""
**Task Manager Agent**

A powerful task management system powered by:
- **Backend**: FastAPI + LangChain
- **Frontend**: Streamlit
- **Database**: Supabase + ChromaDB
- **AI**: OpenAI GPT-4

**Version**: 1.0.0
""")

# System info
with st.expander("System Information"):
    st.json({
        "API URL": api_url,
        "Python Version": os.sys.version,
        "Platform": os.name
    })

