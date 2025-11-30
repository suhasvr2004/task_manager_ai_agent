from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import uvicorn
from loguru import logger
import sys
import time

from backend.config import get_settings
from backend.database.client import DatabaseManager
from backend.api.routes import router
from backend.services.reminder_scheduler import get_reminder_scheduler
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://taskmanageraiagent.streamlit.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logger - only log warnings and errors in production
settings = get_settings()
log_level = "INFO" if settings.DEBUG else "WARNING"
logger.remove()
logger.add(
    sys.stdout,
    format="<level>{level: <8}</level> | <cyan>{name}</cyan>:{function}:{line} - <level>{message}</level>",
    level=log_level
)

db_manager = DatabaseManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    logger.info("Starting Task Manager Agent API")
    await db_manager.initialize_schema()
    
    # Start reminder scheduler
    reminder_scheduler = get_reminder_scheduler()
    reminder_scheduler.start()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Task Manager Agent API")
    reminder_scheduler.stop()

# Create FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    lifespan=lifespan
)

# Response compression - reduces payload size significantly
app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Optimized logging middleware - only log in debug mode
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Only log slow requests or in debug mode
    if settings.DEBUG or process_time > 1.0:
        logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    
    # Add performance headers
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Include routers
app.include_router(router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Task Manager Agent API",
        "version": settings.API_VERSION,
        "docs": "/docs"
    }

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.DEBUG else False,
        log_level=settings.LOG_LEVEL.lower()
    )
