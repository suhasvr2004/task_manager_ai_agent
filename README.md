# Task Manager Agent

An intelligent task management system powered by AI, featuring natural language task creation, semantic search, and automated reminders. Built with FastAPI, Streamlit, LangChain, Supabase, and ChromaDB.

## 🚀 Features

### Core Functionality
- **AI-Powered Task Management**: Create, update, and manage tasks using natural language
- **Intelligent Agent Chat**: Interact with an AI agent to manage tasks conversationally
- **Semantic Search**: Find tasks using natural language queries powered by ChromaDB embeddings
- **Task CRUD Operations**: Full Create, Read, Update, Delete functionality
- **Priority & Status Management**: Organize tasks by priority (low, medium, high, urgent) and status (pending, in_progress, completed, archived)
- **Due Date Management**: Set and track task due dates with relative date parsing (today, tomorrow, evening, etc.)
- **Time Estimation**: Track estimated hours and minutes for tasks
- **Tags & Categorization**: Organize tasks with custom tags
- **Reminders**: Create and manage task reminders
- **Calendar Integration Ready**: Schema prepared for Google Calendar sync

### User Interface
- **Interactive Dashboard**: View task metrics, recent tasks, and quick actions
- **Task Creation Form**: Intuitive form with hours/minutes time input
- **Task List View**: Filterable list with search and sorting
- **Calendar View**: Visual calendar representation of tasks
- **AI Agent Chat Interface**: Natural language interaction for task management

## 📋 Prerequisites

- Python 3.10 or higher
- Supabase account (for database)
- OpenAI API key (for AI agent functionality)
- (Optional) Anthropic API key (for Claude models)

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Suhas_projects
```

### 2. Create Virtual Environment

**Windows:**
```powershell
python -m venv venv
. venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements-final.txt
```

### 4. Set Up Environment Variables

Create a `.env` file in the project root:

```env
# API Configuration
API_TITLE=Task Manager Agent API
API_VERSION=1.0.0
DEBUG=False

# LLM Configuration (Required for AI Agent)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here  # Optional
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.7

# Database Configuration (Required)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_API_KEY=your_supabase_api_key_here
SUPABASE_DB_NAME=task_manager

# ChromaDB Configuration
CHROMADB_PERSIST_DIR=./chroma_data
CHROMADB_COLLECTION_NAME=task_embeddings

# External APIs (Optional)
GOOGLE_CALENDAR_API_KEY=your_google_calendar_key
NOTION_API_KEY=your_notion_key

# Scheduler Configuration
SCHEDULER_ENABLED=True
REMINDER_CHECK_INTERVAL_MINUTES=5

# Logging
LOG_LEVEL=INFO

# Frontend Configuration
API_URL=http://localhost:8000/api/v1
```

### 5. Set Up Supabase Database

1. Go to your Supabase project dashboard
2. Navigate to SQL Editor
3. Run the SQL script from `supabase_schema.sql` to create the required tables:
   - `tasks` - Main task storage
   - `reminders` - Task reminders (use `setup_reminders_table.sql` for quick setup)
   - `calendar_events` - Calendar integration (optional)

## 🚀 Running the Application

### Start Backend Server

```bash
# Activate virtual environment
. venv\Scripts\Activate.ps1  # Windows
# or
source venv/bin/activate      # Linux/Mac

# Start the backend
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

The backend API will be available at:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **API Base Path**: http://localhost:8000/api/v1

### Start Frontend Server

Open a new terminal and run:

```bash
# Activate virtual environment
. venv\Scripts\Activate.ps1  # Windows
# or
source venv/bin/activate      # Linux/Mac

# Start the frontend
streamlit run frontend/app.py --server.port 8501
```

The frontend will be available at: **http://localhost:8501**

## 📖 Usage

### AI Agent Chat

The AI agent can understand natural language commands:

- **Create Tasks**: 
  - "Create a task to review code tomorrow"
  - "Create a task to walk in the evening"
  - "Create a high priority task to finish the report today"

- **List Tasks**:
  - "List all high priority tasks"
  - "Show me all pending tasks"
  - "What tasks are due today?"

- **Manage Tasks**:
  - "Update task [ID] to completed"
  - "Delete task [ID]"
  - "Create a reminder for task [ID] in 1 hour"

### Manual Task Management

1. **Dashboard**: View overview of all tasks, metrics, and recent activity
2. **Create Task**: Use the form to create tasks with:
   - Title and description
   - Priority level
   - Due date
   - Estimated time (hours and minutes)
   - Tags
3. **Task List**: Browse, filter, and search all tasks
4. **Calendar View**: See tasks in a calendar format

## 🏗️ Project Structure

```
Suhas_projects/
├── backend/
│   ├── agents/              # AI agent implementation
│   │   ├── task_agent.py    # Main agent class
│   │   └── tools/           # Agent tools (CRUD, reminders)
│   ├── api/                 # FastAPI routes
│   │   └── routes.py        # API endpoints
│   ├── database/             # Database clients
│   │   └── client.py        # Supabase & ChromaDB clients
│   ├── models/              # Pydantic models
│   │   └── schemas.py       # Data schemas
│   ├── services/            # Business logic
│   │   └── task_service.py # Task service layer
│   ├── config.py            # Configuration management
│   └── main.py              # FastAPI application
├── frontend/
│   ├── app.py               # Main Streamlit app
│   ├── components/          # Reusable UI components
│   │   ├── task_form.py     # Task creation form
│   │   ├── task_display.py  # Task display components
│   │   └── calendar_view.py # Calendar visualization
│   ├── pages/               # Streamlit pages
│   │   ├── 01_Dashboard.py
│   │   ├── 02_Create_Task.py
│   │   ├── 03_Task_List.py
│   │   └── 04_Settings.py
│   └── utils/              # Frontend utilities
│       ├── api_client.py    # API client
│       └── time_utils.py   # Time formatting
├── supabase_schema.sql      # Database schema
├── setup_reminders_table.sql # Reminders table setup
├── setup_notifications_table.sql # Notifications table setup
├── requirements-final.txt   # Python dependencies
└── README.md                # This file
```

## 🔌 API Endpoints

### Task Management
- `POST /api/v1/tasks` - Create a new task
- `GET /api/v1/tasks` - List all tasks (with filters)
- `GET /api/v1/tasks/{task_id}` - Get a specific task
- `PUT /api/v1/tasks/{task_id}` - Update a task
- `DELETE /api/v1/tasks/{task_id}` - Delete a task

### AI Agent
- `POST /api/v1/agent/chat` - Chat with AI agent
- `GET /api/v1/agent/summary` - Get task summary
- `GET /api/v1/agent/next-task` - Get AI recommendation

### Search
- `GET /api/v1/search?q={query}` - Semantic search for tasks

## 🧪 Testing

Test scripts are available in the root directory:
- `test_backend.py` - Backend functionality tests
- `test_frontend.py` - Frontend component tests
- `test_databases.py` - Database connection tests
- `test_api.py` - API endpoint tests
- `test_agent_chat.py` - AI agent tests

Run tests:
```bash
python test_backend.py
python test_api.py
```

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

- **OPENAI_API_KEY**: Required for AI agent functionality
- **SUPABASE_URL** & **SUPABASE_API_KEY**: Required for database
- **LLM_MODEL**: Choose between `gpt-4o-mini`, `gpt-4`, `gpt-3.5-turbo`, or Claude models
- **LLM_TEMPERATURE**: Controls AI creativity (0.0-1.0)
- **CHROMADB_PERSIST_DIR**: Where to store vector embeddings

### Database Setup

The system uses:
- **Supabase (PostgreSQL)**: Primary task storage
- **ChromaDB**: Vector database for semantic search

Ensure both are properly configured in your `.env` file.

## 🐛 Troubleshooting

### Common Issues

1. **"OpenAI API Quota Exceeded"**
   - Check your OpenAI account usage: https://platform.openai.com/usage
   - Add billing or upgrade your plan
   - You can still use manual task creation without the AI agent

2. **"ModuleNotFoundError"**
   - Ensure virtual environment is activated
   - Run `pip install -r requirements-final.txt`

3. **Database Connection Errors**
   - Verify Supabase URL and API key in `.env`
   - Ensure database schema is set up (run `supabase_schema.sql`)

4. **Port Already in Use**
   - Backend default: 8000
   - Frontend default: 8501
   - Change ports in startup scripts if needed

### Backend Health Check

Visit http://localhost:8000/docs to verify the API is running.

## 📝 License

This project is part of an AI Agent Development Challenge.

## 🤝 Contributing

This is a development project. Contributions and improvements are welcome!

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review API documentation at `/docs` endpoint
3. Check backend logs for detailed error messages

## 🎯 Future Enhancements

- [ ] Google Calendar integration
- [ ] Notion integration
- [ ] Email notifications
- [ ] Task templates
- [ ] Team collaboration features
- [ ] Mobile app
- [ ] Advanced analytics and reporting

---

**Built with ❤️ using FastAPI, Streamlit, LangChain, Supabase, and ChromaDB**

#   t a s k _ m a n a g e r _ a i  
 