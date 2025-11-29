import streamlit as st
import os
import sys
import time
from dotenv import load_dotenv

# Add project root to path for imports (for pages to work)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

load_dotenv()

# Page config
st.set_page_config(
    page_title="Task Manager Agent",
    page_icon="✅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API configuration - use optimized client with connection pooling
from frontend.utils.api_client import APIClient

# Create singleton API client instance (reused across all requests)
api_client = APIClient()

# Helper function to check backend health
def check_backend_health():
    """Check if backend is running"""
    # Use session state to cache health check result (check every 5 seconds)
    if 'backend_health_check' in st.session_state:
        last_check, was_healthy = st.session_state.backend_health_check
        if (time.time() - last_check) < 5:
            return was_healthy
    
    try:
        # Use the api_client's base URL
        health_url = f"{api_client.base_url}/health"
        
        # Use the persistent client from api_client for better performance
        response = api_client._client.get(health_url, timeout=3)
        is_healthy = response.status_code == 200
        
        # Cache the result
        st.session_state.backend_health_check = (time.time(), is_healthy)
        return is_healthy
    except Exception:
        # Cache the failure
        st.session_state.backend_health_check = (time.time(), False)
        return False

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("🤖 Task Manager Agent")
st.sidebar.markdown("---")

# Check for notifications
if check_backend_health():
    try:
        unread_count = api_client.get_unread_count()
        if unread_count > 0:
            st.sidebar.markdown(f"🔔 **{unread_count} unread notification{'s' if unread_count != 1 else ''}**")
    except:
        pass

page = st.sidebar.radio(
    "Navigate",
    ["📊 Dashboard", "✏️ Create Task", "📋 Task List", "💬 Agent Chat", "🔍 Search", "🔔 Notifications"]
)

# ============================================================================
# DASHBOARD PAGE
# ============================================================================
if page == "📊 Dashboard":
    st.title("📊 Dashboard")
    
    # Check backend health
    if not check_backend_health():
        st.error("⚠️ Backend server is not running!")
        st.info("Please start the backend server:\n```bash\npython -m uvicorn backend.main:app --reload\n```")
        st.stop()
    
    try:
        tasks = api_client.list_tasks()
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        total = len(tasks)
        pending = len([t for t in tasks if t['status'] == 'pending'])
        in_progress = len([t for t in tasks if t['status'] == 'in_progress'])
        completed = len([t for t in tasks if t['status'] == 'completed'])
        
        with col1:
            st.metric("Total Tasks", total)
        with col2:
            st.metric("Pending", pending)
        with col3:
            st.metric("In Progress", in_progress)
        with col4:
            st.metric("Completed", completed)
        
        st.markdown("---")
        
        # Recent tasks
        st.subheader("Recent Tasks")
        if tasks:
            for task in tasks[:5]:
                with st.expander(f"**{task['title']}** - {task['priority'].upper()}"):
                    st.write(f"**Description:** {task.get('description', 'No description')}")
                    st.write(f"**Status:** {task['status']}")
                    st.write(f"**Due Date:** {task.get('due_date', 'No due date')}")
        else:
            st.info("No tasks yet. Create your first task!")
    
    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")

# ============================================================================
# CREATE TASK PAGE
# ============================================================================
elif page == "✏️ Create Task":
    st.title("✏️ Create New Task")
    
    # Check backend health
    if not check_backend_health():
        st.error("⚠️ Backend server is not running!")
        st.info("Please start the backend server:\n```bash\npython -m uvicorn backend.main:app --reload\n```")
        st.stop()
    
    with st.form("task_form"):
        title = st.text_input("Task Title*", max_chars=255)
        description = st.text_area("Description")
        
        col1, col2 = st.columns(2)
        with col1:
            priority = st.selectbox("Priority", ["low", "medium", "high", "urgent"])
        with col2:
            due_date = st.date_input("Due Date")
        
        # Estimated time in hours and minutes
        st.write("**Estimated Time**")
        est_time_col1, est_time_col2 = st.columns(2)
        
        with est_time_col1:
            estimated_hours_input = st.number_input(
                "Hours",
                min_value=0,
                max_value=23,
                value=0,
                step=1,
                help="Number of hours"
            )
        
        with est_time_col2:
            estimated_minutes_input = st.number_input(
                "Minutes",
                min_value=0,
                max_value=59,
                value=30,
                step=5,
                help="Number of minutes"
            )
        
        # Calculate total time in hours (for backend storage)
        estimated_hours = estimated_hours_input + (estimated_minutes_input / 60.0)
        
        # Display total time
        if estimated_hours > 0:
            if estimated_hours_input > 0 and estimated_minutes_input > 0:
                st.caption(f"Total: {estimated_hours_input}h {estimated_minutes_input}m ({estimated_hours:.2f} hours)")
            elif estimated_hours_input > 0:
                st.caption(f"Total: {estimated_hours_input} hour(s)")
            elif estimated_minutes_input > 0:
                st.caption(f"Total: {estimated_minutes_input} minute(s)")
        tags = st.multiselect("Tags", ["work", "personal", "urgent", "important", "meeting"])
        
        submitted = st.form_submit_button("Create Task", type="primary")
        
        if submitted:
            if not title:
                st.error("Task title is required!")
            else:
                try:
                    task_data = {
                        "title": title,
                        "description": description,
                        "priority": priority,
                        "due_date": due_date.isoformat() if due_date else None,
                        "estimated_hours": estimated_hours,
                        "tags": tags,
                        "created_by": "user"
                    }
                    
                    with st.spinner("Creating task..."):
                        try:
                            result = api_client.create_task(task_data)
                            
                            if result and "id" in result:
                                st.success(f"✅ Task created successfully! ID: {result['id']}")
                                st.balloons()
                                # Clear form
                                st.rerun()
                            else:
                                st.error(f"Failed to create task. Response: {result}")
                        except httpx.HTTPStatusError as e:
                            error_detail = e.response.text if hasattr(e.response, 'text') else str(e)
                            st.error(f"HTTP Error {e.response.status_code}: {error_detail}")
                        except Exception as e:
                            st.error(f"Error creating task: {str(e)}")
                            import traceback
                            st.code(traceback.format_exc())
                
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# ============================================================================
# TASK LIST PAGE
# ============================================================================
elif page == "📋 Task List":
    st.title("📋 Task List")
    
    # Check backend health
    if not check_backend_health():
        st.error("⚠️ Backend server is not running!")
        st.info("Please start the backend server:\n```bash\npython -m uvicorn backend.main:app --reload\n```")
        st.stop()
    
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox("Filter by Status", ["All", "pending", "in_progress", "completed", "archived"])
    with col2:
        priority_filter = st.selectbox("Filter by Priority", ["All", "low", "medium", "high", "urgent"])
    
    try:
        with st.spinner("Loading tasks..."):
            tasks = api_client.list_tasks(
                status=None if status_filter == "All" else status_filter,
                priority=None if priority_filter == "All" else priority_filter
            )
        
        if tasks:
            st.write(f"Found {len(tasks)} task(s)")
            
            for task in tasks:
                task_id = task['id']
                with st.expander(f"**{task['title']}** - Priority: {task['priority'].upper()}"):
                    # Task ID - prominently displayed
                    st.code(f"Task ID: {task_id}", language=None)
                    st.caption("💡 Copy this ID to use in commands like 'Create a reminder for task [ID]'")
                    
                    st.write(f"**Description:** {task.get('description', 'No description')}")
                    st.write(f"**Status:** {task['status']}")
                    st.write(f"**Due Date:** {task.get('due_date', 'No due date')}")
                    st.write(f"**Tags:** {', '.join(task.get('tags', []))}")
                    
                    # Check for delete confirmation
                    delete_confirm_key = f"delete_confirm_{task_id}"
                    if delete_confirm_key in st.session_state and st.session_state[delete_confirm_key]:
                        st.warning(f"⚠️ Are you sure you want to delete: **{task['title']}**?")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✅ Yes, Delete", key=f"confirm_delete_{task_id}", type="primary"):
                                try:
                                    if api_client.delete_task(task_id):
                                        st.success("Task deleted successfully!")
                                        if delete_confirm_key in st.session_state:
                                            del st.session_state[delete_confirm_key]
                                        st.rerun()
                                    else:
                                        st.error("Failed to delete task")
                                except Exception as e:
                                    st.error(f"Error deleting task: {str(e)}")
                        with col2:
                            if st.button("❌ Cancel", key=f"cancel_delete_{task_id}"):
                                if delete_confirm_key in st.session_state:
                                    del st.session_state[delete_confirm_key]
                                st.rerun()
                    else:
                        col1, col2, col3 = st.columns([1, 1, 2])
                        with col1:
                            if st.button("🗑️ Delete", key=f"delete_{task_id}", type="secondary"):
                                st.session_state[delete_confirm_key] = True
                                st.rerun()
                        with col2:
                            status = task.get("status", "pending")
                            if status == "pending":
                                if st.button("▶️ Start", key=f"start_{task_id}"):
                                    try:
                                        result = api_client.update_task(task_id, {"status": "in_progress"})
                                        if result:
                                            st.success("Task started!")
                                            st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
                            elif status == "in_progress":
                                if st.button("✅ Complete", key=f"complete_{task_id}"):
                                    try:
                                        result = api_client.update_task(task_id, {"status": "completed"})
                                        if result:
                                            st.success("Task completed!")
                                            st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
        else:
            st.info("No tasks found.")
    
    except Exception as e:
        st.error(f"Error loading tasks: {str(e)}")

# ============================================================================
# AGENT CHAT PAGE
# ============================================================================
elif page == "💬 Agent Chat":
    st.title("💬 AI Agent Chat")
    
    # Check backend health
    if not check_backend_health():
        st.error("⚠️ Backend server is not running!")
        st.info("Please start the backend server:\n```bash\npython -m uvicorn backend.main:app --reload\n```")
        st.stop()
    
    st.info("""
    💡 **Try these commands:**
    
    **Create Tasks:**
    - "Create a task to review code tomorrow"
    - "Create a high priority task to finish the report by Friday"
    - "Create a task to walk in the evening with description: Take a 30-minute walk"
    
    **Organize & Track:**
    - "List all high priority tasks"
    - "List all pending tasks"
    - "Show me tasks due today"
    - "Update task [task_id] status to in_progress"
    - "Update task [task_id] priority to urgent"
    
    **Search:**
    - "Search for tasks about code review"
    - "Find tasks with tag 'work'"
    - "Show me all tasks related to meetings"
    
    **Reminders:**
    - "Create a reminder for task [task_id] in 1 hour"
    - "Create a reminder for task [task_id] tomorrow at 9am"
    - "List reminders for task [task_id]"
    """)
    
    # Show warning if OpenAI quota might be an issue
    if st.session_state.get("show_quota_warning", False):
        st.warning("⚠️ **Note**: If you see quota errors, check your OpenAI account billing. You can still create tasks manually using the 'Create Task' page!")
    
    # Chat messages
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about your tasks..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get agent response
        with st.chat_message("assistant"):
            with st.spinner("🤖 Thinking..."):
                try:
                    # Prepare conversation history (last 5 messages for context)
                    history = []
                    if len(st.session_state.messages) > 0:
                        # Convert messages to history format
                        for msg in st.session_state.messages[-5:]:  # Last 5 messages
                            if msg["role"] == "user":
                                history.append({"user": msg["content"], "assistant": ""})
                            elif msg["role"] == "assistant" and len(history) > 0:
                                history[-1]["assistant"] = msg["content"]
                    
                    response = api_client.agent_chat(prompt, history=history)
                    
                    # Handle response
                    if response.get("status") == "error":
                        error_output = response.get("output", response.get("error", "An error occurred"))
                        
                        # Check for quota error
                        if "quota" in error_output.lower() or "429" in str(response.get("error", "")):
                            st.error("❌ **OpenAI API Quota Exceeded**")
                            st.markdown(error_output)  # This will show the formatted message from backend
                            st.info("💡 **Tip**: You can still create tasks manually using the 'Create Task' page!")
                            
                            # Add helpful links
                            with st.expander("🔗 Quick Links"):
                                st.markdown("""
                                - [Check Usage](https://platform.openai.com/usage)
                                - [Billing Settings](https://platform.openai.com/account/billing)
                                - [API Documentation](https://platform.openai.com/docs)
                                """)
                        else:
                            st.error(f"❌ {error_output}")
                        
                        assistant_message = error_output
                    else:
                        assistant_message = response.get("output", "I've processed your request.")
                        st.write(assistant_message)
                        
                        # If task was created, show success
                        if "created" in assistant_message.lower() or ("task" in assistant_message.lower() and "id" in assistant_message.lower()):
                            st.success("✅ Task operation completed!")
                    
                    st.session_state.messages.append({"role": "assistant", "content": assistant_message})
                except Exception as e:
                    error_msg = str(e)
                    if "429" in error_msg or "quota" in error_msg.lower():
                        st.error("❌ **OpenAI API Quota Exceeded**")
                        st.markdown("""
                        Your OpenAI API key has reached its usage limit. 
                        
                        **To resolve:**
                        1. Check your usage at https://platform.openai.com/usage
                        2. Add billing at https://platform.openai.com/account/billing
                        3. Upgrade your plan if needed
                        
                        **Alternative**: Use the 'Create Task' page to add tasks manually!
                        """)
                    else:
                        st.error(f"❌ Error: {error_msg}")
                        st.info("💡 Tip: Make sure the backend server is running and OpenAI API key is configured.")
                    st.session_state.messages.append({"role": "assistant", "content": f"Error: {error_msg}"})

# ============================================================================
# SEARCH PAGE
# ============================================================================
elif page == "🔍 Search":
    st.title("🔍 Search Tasks")
    
    # Check backend health
    if not check_backend_health():
        st.error("⚠️ Backend server is not running!")
        st.info("Please start the backend server:\n```bash\npython -m uvicorn backend.main:app --reload\n```")
        st.stop()
    
    search_query = st.text_input("Search tasks using natural language", placeholder="e.g., urgent tasks about coding")
    
    if st.button("Search"):
        if search_query:
            try:
                with st.spinner("Searching..."):
                    results = api_client.search_tasks(search_query)
                
                st.write(f"Found {len(results.get('results', {}).get('ids', [[]])[0])} result(s)")
                
                # Display results
                ids = results.get('results', {}).get('ids', [[]])[0]
                if ids:
                    for task_id in ids:
                        task = api_client.get_task(task_id)
                        with st.expander(f"**{task['title']}**"):
                            st.write(task.get('description', 'No description'))
                            st.write(f"**Priority:** {task['priority']}")
                            st.write(f"**Status:** {task['status']}")
                else:
                    st.info("No tasks found matching your search.")
            except Exception as e:
                st.error(f"Search error: {str(e)}")

# ============================================================================
# NOTIFICATIONS PAGE
# ============================================================================
elif page == "🔔 Notifications":
    st.title("🔔 Notifications")
    
    # Check backend health
    if not check_backend_health():
        st.error("⚠️ Backend server is not running!")
        st.info("Please start the backend server:\n```bash\npython -m uvicorn backend.main:app --reload\n```")
        st.stop()
    
    try:
        # Get notifications
        notifications_data = api_client.get_notifications(limit=100)
        notifications = notifications_data.get("notifications", [])
        
        if not notifications:
            st.info("📭 No notifications yet. You'll see reminders and estimated time completions here!")
        else:
            # Filter options
            col1, col2 = st.columns(2)
            with col1:
                filter_read = st.selectbox("Filter", ["All", "Unread", "Read"])
            with col2:
                if st.button("🔄 Refresh"):
                    st.rerun()
            
            # Filter notifications
            if filter_read == "Unread":
                notifications = [n for n in notifications if not n.get("is_read", False)]
            elif filter_read == "Read":
                notifications = [n for n in notifications if n.get("is_read", False)]
            
            # Display notifications
            for notif in notifications:
                notif_id = notif.get("id")
                title = notif.get("title", "Notification")
                message = notif.get("message", "")
                category = notif.get("notification_category", "reminder")
                is_read = notif.get("is_read", False)
                created_at = notif.get("created_at", "")
                
                # Format date
                try:
                    from datetime import datetime
                    if created_at:
                        dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        formatted_date = dt.strftime("%d/%m/%Y %I:%M %p")
                    else:
                        formatted_date = "Unknown"
                except:
                    formatted_date = created_at
                
                # Color based on category
                if category == "reminder":
                    icon = "⏰"
                    color = "blue"
                elif category == "estimated_time":
                    icon = "⏱️"
                    color = "orange"
                else:
                    icon = "📢"
                    color = "gray"
                
                # Display notification
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        if not is_read:
                            st.markdown(f"**{icon} {title}**")
                        else:
                            st.markdown(f"{icon} {title}")
                        st.caption(message)
                        st.caption(f"📅 {formatted_date}")
                    
                    with col2:
                        if not is_read:
                            if st.button("✓ Mark Read", key=f"read_{notif_id}"):
                                api_client.mark_notification_read(notif_id)
                                st.rerun()
                    
                    with col3:
                        if st.button("🗑️ Delete", key=f"delete_{notif_id}"):
                            api_client.delete_notification(notif_id)
                            st.rerun()
                    
                    st.divider()
            
            # Bulk actions
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Mark All as Read"):
                    for notif in notifications:
                        if not notif.get("is_read", False):
                            api_client.mark_notification_read(notif.get("id"))
                    st.rerun()
            with col2:
                if st.button("Clear All Read"):
                    for notif in notifications:
                        if notif.get("is_read", False):
                            api_client.delete_notification(notif.get("id"))
                    st.rerun()
    
    except Exception as e:
        error_msg = str(e)
        if "does not exist" in error_msg.lower() or "not found" in error_msg.lower():
            st.warning("⚠️ Notifications table not set up yet.")
            st.info("""
            **To enable notifications:**
            1. Go to your Supabase Dashboard → SQL Editor
            2. Run the SQL from `setup_notifications_table.sql`
            3. Restart your backend server
            """)
        else:
            st.error(f"Error loading notifications: {error_msg}")

# Footer
st.sidebar.markdown("---")
st.sidebar.info("🤖 Powered by LangChain + FastAPI")