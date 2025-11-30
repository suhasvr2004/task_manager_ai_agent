# backend/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
from loguru import logger
import sys
import time
import os

from backend.config import get_settings
from backend.database.client import DatabaseManager
from backend.api.routes import router
from backend.services.reminder_scheduler import get_reminder_scheduler

# ---------------- SETTINGS & LOGGER ----------------
settings = get_settings()
log_level = "INFO" if settings.DEBUG else "WARNING"
logger.remove()
logger.add(
    sys.stdout,
    format="<level>{level: <8}</level> | <cyan>{name}</cyan>:{function}:{line} - <level>{message}</level>",
    level=log_level
)

# ---------------- DATABASE ----------------
db_manager = DatabaseManager()

# ---------------- LIFESPAN ----------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("Starting Task Manager Agent API")
    await db_manager.initialize_schema()
    
    reminder_scheduler = get_reminder_scheduler()
    reminder_scheduler.start()
    
    yield
    
    logger.info("Shutting down Task Manager Agent API")
    reminder_scheduler.stop()

# ---------------- FASTAPI APP ----------------
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    lifespan=lifespan
)

# GZip middleware for response compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS middleware
origins = [
    "*",
    "http://localhost:8501",
    "https://taskmanageraiagent.streamlit.app"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Optimized request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    if settings.DEBUG or process_time > 1.0:
        logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")

    response.headers["X-Process-Time"] = str(process_time)
    return response

# ---------------- ROUTES ----------------
@app.get("/")
async def root():
    return {
        "message": "Task Manager Agent API",
        "version": settings.API_VERSION,
        "docs": "/docs"
    }

@app.get("/tasks")
async def get_tasks():
    """Return example tasks JSON"""
    tasks = [
        {"id": 1, "title": "Task 1", "completed": False},
        {"id": 2, "title": "Task 2", "completed": True}
    ]
    return {"tasks": tasks}

# Include other routers
app.include_router(router)

# ---------------- UVICORN ENTRY ----------------
if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True if settings.DEBUG else False,
        log_level=settings.LOG_LEVEL.lower()
    )
