"""
Tech-Teach - AI-Powered Teaching Assistant

Main application entry point using FastAPI.
Single unified API for content generation with various tools.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from app.core.config import settings
from app.api.v1 import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    # Startup
    print(f"[App] Starting {settings.APP_NAME}")
    print(f"[App] API available at {settings.API_V1_STR}")
    print("[App] Available tools: pdf, presentation, mind_map, ppt_video, flashcards")
    settings.ensure_directories()
    
    yield
    
    # Shutdown
    print(f"[App] Shutting down {settings.APP_NAME}")


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="""
Tech-Teach - AI-Powered Teaching Assistant

## Features
- **PDF Generation**: Create PDF documents with detailed content
- **Presentation**: Generate slides with AI images
- **Mind Map**: Create hierarchical mind maps (JSON)
- **PPT Video**: Generate videos with images and narration
- **Flashcards**: Create Q&A study cards (JSON)

## Usage
Send POST request to `/api/v1/generate/` with:
- `task_name`: lesson_plan (more coming soon)
- `tool_name`: pdf, presentation, mind_map, ppt_video, flashcards
- `instructions`: Your instructions for content generation
- `pdf_data`: Optional base64-encoded PDF as source material
""",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Serve static frontend files
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")


@app.get("/")
async def root():
    """Root endpoint with application information."""
    return {
        "app": settings.APP_NAME,
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
        "frontend": "/static/index.html",
        "api": {
            "generate": f"{settings.API_V1_STR}/generate/",
            "tools_list": f"{settings.API_V1_STR}/generate/tools"
        },
        "available_tools": ["pdf", "presentation", "mind_map", "ppt_video", "flashcards"],
        "current_tasks": ["lesson_plan"],
        "future_tasks": ["assessment_generation", "homework_generation"]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
