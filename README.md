# Tech-Teach

AI-Powered Teaching Assistant using Google Gemini Models and FastAPI.

## Overview

Tech-Teach is an educational content generation system that uses three Google Gemini models to create various types of teaching materials.

## Gemini Models Used

| Model | Purpose | Usage |
|-------|---------|-------|
| `gemini-2.0-flash-exp` | Text Generation | Scripts, content, JSON structures |
| `imagen-3.0-generate-002` | Image Generation | Presentation slides, educational visuals |
| `gemini-2.5-flash-preview-tts` | Audio/TTS | Voice narration for videos |

## Features

### Available Tools

| Tool | Description | Output |
|------|-------------|--------|
| **PDF** | Generate detailed PDF documents | Downloadable PDF file |
| **Presentation** | Create 5 slides with AI images | JSON with base64 images |
| **Mind Map** | Hierarchical concept visualization | JSON for frontend rendering |
| **PPT Video** | 10-slide video with narration | Downloadable MP4 video |
| **Flashcards** | Q&A study cards | JSON with question-answer pairs |

### Future Tools (Coming Soon)

- **Homework Generation** - Create homework assignments
- **Assessment Generation** - Generate assessments and tests

## Project Structure

```
tech-teach/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI entry point
│   ├── agents/
│   │   └── teaching_agent.py      # Agent orchestration
│   ├── api/v1/
│   │   └── endpoints/
│   │       └── generate.py        # Unified API endpoint
│   ├── core/
│   │   ├── config.py              # Settings & model config
│   │   └── ai_service.py          # AI service singleton
│   ├── schemas/
│   │   └── generate.py            # Pydantic models
│   └── tools/
│       ├── base_tool.py           # Base class with Gemini integration
│       ├── pdf_tool.py            # PDF generation
│       ├── presentation_tool.py   # Presentation with images
│       ├── mind_map_tool.py       # Mind map JSON
│       ├── ppt_video_tool.py      # Video generation
│       └── flashcards_tool.py     # Flashcards JSON
├── frontend/
│   ├── index.html
│   ├── css/style.css
│   └── js/app.js
├── pyproject.toml
├── .env
└── README.md
```

## Quick Start

### 1. Create Virtual Environment

```bash
cd tech-teach
uv venv
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
uv sync
```

### 3. Configure Environment

Create `.env` file:
```
GOOGLE_API_KEY=your_api_key_here
```

### 4. Run Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Access Application

- **API Documentation**: http://localhost:8000/docs
- **Frontend**: http://localhost:8000/static/index.html
- **Health Check**: http://localhost:8000/health

## API Usage

### Single Endpoint for All Generation

**POST** `/api/v1/generate/`

```json
{
    "task_name": "lesson_plan",
    "tool_name": "pdf|presentation|mind_map|ppt_video|flashcards",
    "instructions": "Your instructions here",
    "pdf_data": "optional_base64_encoded_pdf"
}
```

### Example: Generate Flashcards

```bash
curl -X POST "http://localhost:8000/api/v1/generate/" \
  -H "Content-Type: application/json" \
  -d '{
    "task_name": "lesson_plan",
    "tool_name": "flashcards",
    "instructions": "Create flashcards about photosynthesis for 8th grade"
  }'
```

### Example: Generate PPT Video

```bash
curl -X POST "http://localhost:8000/api/v1/generate/" \
  -H "Content-Type: application/json" \
  -d '{
    "task_name": "lesson_plan",
    "tool_name": "ppt_video",
    "instructions": "Create a video about the solar system for elementary students"
  }'
```

## Architecture

```
User Request
     ↓
[FastAPI Endpoint] → /api/v1/generate/
     ↓
[Teaching Agent] → Orchestrates tool selection
     ↓
[Tool Execution]
     ├── PDF Tool → Text Model → ReportLab → PDF File
     ├── Presentation Tool → Text Model + Image Model → JSON
     ├── Mind Map Tool → Text Model → JSON
     ├── PPT Video Tool → Text + Image + Audio Models → MoviePy → MP4
     └── Flashcards Tool → Text Model → JSON
     ↓
[Response] → JSON with data or file URL
```

## Dependencies

- **FastAPI** - Web framework
- **Google GenAI** - Gemini API client
- **ReportLab** - PDF generation
- **MoviePy** - Video creation
- **Pillow** - Image processing
- **PyPDF** - PDF text extraction
