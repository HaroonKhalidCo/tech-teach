"""
Unified Generation API Endpoint

Single endpoint for all content generation:
- User sends: task_name, tool_name, instructions, pdf_data (optional)
- Agent processes and returns generated content

Video generation uses background task with polling for status.
"""

import os
import base64
import asyncio
import uuid
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
import pypdf
import io

from app.schemas import (
    TaskType,
    ToolType,
    GenerateRequest,
    GenerateResponse,
)
from app.tools import (
    PDFTool,
    PresentationTool,
    MindMapTool,
    PPTVideoTool,
    FlashcardsTool,
)
from app.core.config import settings

router = APIRouter()

# Store for video generation tasks
VIDEO_TASKS: Dict[str, Dict[str, Any]] = {}


class VideoTaskRequest(BaseModel):
    instructions: str
    source_content: Optional[str] = None

# Tool instances
TOOLS = {
    ToolType.PDF: PDFTool(),
    ToolType.PRESENTATION: PresentationTool(),
    ToolType.MIND_MAP: MindMapTool(),
    ToolType.PPT_VIDEO: PPTVideoTool(),
    ToolType.FLASHCARDS: FlashcardsTool(),
}


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text content from PDF bytes."""
    try:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        print(f"[PDF Extract] Error: {e}")
        return ""


@router.post("/", response_model=GenerateResponse)
async def generate_content(request: GenerateRequest) -> GenerateResponse:
    """
    Unified endpoint for content generation.
    
    Request body:
    - task_name: Type of task (lesson_plan, assessment_generation, homework_generation)
    - tool_name: Type of content to generate (pdf, presentation, mind_map, ppt_video, flashcards)
    - instructions: Description/instructions for content generation
    - pdf_data: Optional base64-encoded PDF as source material
    - additional_params: Optional tool-specific parameters
    
    Returns:
    - Generated content data based on tool type
    """
    print(f"[Generate API] Task: {request.task_name}, Tool: {request.tool_name}")
    
    # Validate task (for future expansion)
    if request.task_name not in [TaskType.LESSON_PLAN]:
        return GenerateResponse(
            status="error",
            task_name=request.task_name.value,
            tool_name=request.tool_name.value,
            message=f"Task '{request.task_name.value}' is not yet implemented. Currently only 'lesson_plan' is available.",
            data=None
        )
    
    # Get tool instance
    tool = TOOLS.get(request.tool_name)
    if not tool:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown tool: {request.tool_name}"
        )
    
    # Extract source content from PDF if provided
    source_content = None
    if request.pdf_data:
        try:
            pdf_bytes = base64.b64decode(request.pdf_data)
            source_content = extract_text_from_pdf(pdf_bytes)
            print(f"[Generate API] Extracted {len(source_content)} chars from PDF")
        except Exception as e:
            print(f"[Generate API] Failed to process PDF: {e}")
    
    # Execute tool
    try:
        result = await tool.execute(
            instructions=request.instructions,
            source_content=source_content,
            **request.additional_params
        )
        
        # Build file URL if file was generated
        file_url = None
        if result.get("file_path") and result.get("file_name"):
            file_url = f"/api/v1/generate/download/{result.get('file_name')}"
        
        return GenerateResponse(
            status=result.get("status", "success"),
            task_name=request.task_name.value,
            tool_name=request.tool_name.value,
            message=result.get("message", "Content generated successfully"),
            data=result,
            file_url=file_url
        )
        
    except Exception as e:
        print(f"[Generate API] Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload", response_model=GenerateResponse)
async def generate_with_upload(
    task_name: TaskType = Form(...),
    tool_name: ToolType = Form(...),
    instructions: str = Form(...),
    pdf_file: Optional[UploadFile] = File(None)
) -> GenerateResponse:
    """
    Alternative endpoint that accepts file upload directly.
    
    Use multipart/form-data to upload PDF file.
    """
    print(f"[Generate Upload API] Task: {task_name}, Tool: {tool_name}")
    
    # Validate task
    if task_name not in [TaskType.LESSON_PLAN]:
        return GenerateResponse(
            status="error",
            task_name=task_name.value,
            tool_name=tool_name.value,
            message=f"Task '{task_name.value}' is not yet implemented.",
            data=None
        )
    
    # Get tool
    tool = TOOLS.get(tool_name)
    if not tool:
        raise HTTPException(status_code=400, detail=f"Unknown tool: {tool_name}")
    
    # Extract source content from uploaded PDF
    source_content = None
    if pdf_file:
        try:
            pdf_bytes = await pdf_file.read()
            source_content = extract_text_from_pdf(pdf_bytes)
            print(f"[Generate Upload API] Extracted {len(source_content)} chars from PDF")
        except Exception as e:
            print(f"[Generate Upload API] Failed to process PDF: {e}")
    
    # Execute tool
    try:
        result = await tool.execute(
            instructions=instructions,
            source_content=source_content
        )
        
        # Build file URL if file was generated
        file_url = None
        if result.get("file_path") and result.get("file_name"):
            file_url = f"/api/v1/generate/download/{result.get('file_name')}"
        
        return GenerateResponse(
            status=result.get("status", "success"),
            task_name=task_name.value,
            tool_name=tool_name.value,
            message=result.get("message", "Content generated successfully"),
            data=result,
            file_url=file_url
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{filename}")
async def download_file(filename: str, download: bool = False):
    """
    Serve generated files (PDF, video, etc.)
    
    Args:
        filename: Name of the file to serve
        download: If True, force download. If False, show inline (preview)
    """
    
    file_path = os.path.join(settings.OUTPUT_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")
    
    file_size = os.path.getsize(file_path)
    
    # Determine media type based on extension
    if filename.endswith('.pdf'):
        media_type = "application/pdf"
    elif filename.endswith('.mp4'):
        media_type = "video/mp4"
    elif filename.endswith('.png'):
        media_type = "image/png"
    elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
        media_type = "image/jpeg"
    elif filename.endswith('.wav'):
        media_type = "audio/wav"
    else:
        media_type = "application/octet-stream"
    
    # Set Content-Disposition based on download flag
    # inline = show in browser (preview)
    # attachment = force download
    if download:
        content_disposition = f'attachment; filename="{filename}"'
    else:
        content_disposition = f'inline; filename="{filename}"'
    
    # Use FileResponse with proper headers
    return FileResponse(
        path=file_path,
        media_type=media_type,
        headers={
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size),
            "Content-Disposition": content_disposition,
            "Cache-Control": "no-cache"
        }
    )


@router.get("/stream/{filename}")
async def stream_video(filename: str):
    """Stream video file for better playback."""
    
    file_path = os.path.join(settings.OUTPUT_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")
    
    def iterfile():
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):  # 64KB chunks
                yield chunk
    
    file_size = os.path.getsize(file_path)
    
    return StreamingResponse(
        iterfile(),
        media_type="video/mp4",
        headers={
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size)
        }
    )


@router.post("/video/start")
async def start_video_generation(request: VideoTaskRequest, background_tasks: BackgroundTasks):
    """
    Start video generation as a background task.
    Returns task_id for polling status.
    """
    task_id = str(uuid.uuid4())
    
    VIDEO_TASKS[task_id] = {
        "status": "pending",
        "progress": 0,
        "stage": "starting",
        "message": "Starting video generation...",
        "result": None
    }
    
    # Start background task
    background_tasks.add_task(
        generate_video_background,
        task_id,
        request.instructions,
        request.source_content
    )
    
    return {"task_id": task_id, "status": "started"}


@router.get("/video/status/{task_id}")
async def get_video_status(task_id: str):
    """Get the status of a video generation task."""
    if task_id not in VIDEO_TASKS:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = VIDEO_TASKS[task_id]
    
    response = {
        "task_id": task_id,
        "status": task["status"],
        "progress": task["progress"],
        "stage": task["stage"],
        "message": task["message"]
    }
    
    # If complete, include result
    if task["status"] == "complete" and task["result"]:
        response["result"] = task["result"]
        response["file_url"] = f"/api/v1/generate/download/{task['result'].get('file_name', '')}"
    
    # If error, include error message
    if task["status"] == "error":
        response["error"] = task.get("error", "Unknown error")
    
    return response


async def generate_video_background(task_id: str, instructions: str, source_content: Optional[str]):
    """Background task to generate video with progress updates."""
    
    def update_progress(progress: int, stage: str, message: str):
        VIDEO_TASKS[task_id]["progress"] = progress
        VIDEO_TASKS[task_id]["stage"] = stage
        VIDEO_TASKS[task_id]["message"] = message
        print(f"[VideoTask {task_id[:8]}] {progress}% - {stage}: {message}")
    
    try:
        VIDEO_TASKS[task_id]["status"] = "processing"
        update_progress(5, "init", "Initializing video generation...")
        
        tool = PPTVideoTool()
        
        # Execute with progress callback
        result = await tool.execute(
            instructions=instructions,
            source_content=source_content,
            progress_callback=update_progress
        )
        
        if result.get("status") == "success":
            VIDEO_TASKS[task_id]["status"] = "complete"
            VIDEO_TASKS[task_id]["result"] = result
            update_progress(100, "complete", "Video ready!")
        else:
            VIDEO_TASKS[task_id]["status"] = "error"
            VIDEO_TASKS[task_id]["error"] = result.get("message", "Generation failed")
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        VIDEO_TASKS[task_id]["status"] = "error"
        VIDEO_TASKS[task_id]["error"] = str(e)
        VIDEO_TASKS[task_id]["message"] = f"Error: {str(e)}"


@router.get("/tools")
async def list_available_tools():
    """List all available tools and their descriptions."""
    return {
        "available_tasks": [
            {"name": "lesson_plan", "description": "Create lesson plan content", "status": "active"}
        ],
        "future_tasks": [
            {"name": "assessment_generation", "description": "Create assessments", "status": "coming_soon"},
            {"name": "homework_generation", "description": "Create homework", "status": "coming_soon"}
        ],
        "available_tools": [
            {
                "name": "pdf",
                "description": "Generate PDF documents with detailed text content",
                "output": "Downloadable PDF file with viewer"
            },
            {
                "name": "presentation",
                "description": "Create presentation with 5 AI-generated slides/images",
                "output": "JSON with slide data and base64 images"
            },
            {
                "name": "mind_map",
                "description": "Generate hierarchical mind map structure",
                "output": "JSON for frontend rendering"
            },
            {
                "name": "ppt_video",
                "description": "Create video with slides, images, and narration",
                "output": "Downloadable MP4 video with player"
            },
            {
                "name": "flashcards",
                "description": "Generate Q&A flashcards for studying",
                "output": "JSON with question-answer pairs"
            }
        ]
    }
