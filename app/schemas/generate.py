"""Schemas for the unified generation API endpoint."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum


class TaskType(str, Enum):
    """Available task types."""
    LESSON_PLAN = "lesson_plan"
    ASSESSMENT_GENERATION = "assessment_generation"  # Future
    HOMEWORK_GENERATION = "homework_generation"  # Future


class ToolType(str, Enum):
    """Available tool types for content generation."""
    PDF = "pdf"
    PRESENTATION = "presentation"
    MIND_MAP = "mind_map"
    PPT_VIDEO = "ppt_video"
    FLASHCARDS = "flashcards"


class GenerateRequest(BaseModel):
    """
    Unified request schema for content generation.
    
    User sends:
    - task_name: The type of task (lesson_plan, assessment, homework)
    - tool_name: The type of output to generate
    - instructions: Text instructions on how to create the output
    - pdf_data: Optional base64 encoded PDF content as source material
    """
    task_name: TaskType = Field(..., description="Type of task to perform")
    tool_name: ToolType = Field(..., description="Type of content to generate")
    instructions: str = Field(..., description="Instructions describing how to create the output")
    pdf_data: Optional[str] = Field(None, description="Base64 encoded PDF data as source material")
    additional_params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional parameters")


class GenerateResponse(BaseModel):
    """Response schema for content generation."""
    status: str = Field(..., description="Status of the generation (success, error, processing)")
    task_name: str = Field(..., description="Task that was performed")
    tool_name: str = Field(..., description="Tool that was used")
    message: str = Field(..., description="Status message")
    data: Optional[Dict[str, Any]] = Field(None, description="Generated content data")
    file_url: Optional[str] = Field(None, description="URL to download generated file (for PDF, video)")
    

class FlashcardItem(BaseModel):
    """Single flashcard with question and answer."""
    question: str
    answer: str


class FlashcardsOutput(BaseModel):
    """Output schema for flashcards tool."""
    flashcards: List[FlashcardItem]
    topic: str
    total_cards: int


class MindMapNode(BaseModel):
    """Node in the mind map tree."""
    id: str
    label: str
    children: Optional[List["MindMapNode"]] = None


class MindMapOutput(BaseModel):
    """Output schema for mind map tool."""
    root: MindMapNode
    topic: str
    total_nodes: int


class PresentationSlide(BaseModel):
    """Single slide in a presentation."""
    slide_number: int
    title: str
    content: str
    image_url: Optional[str] = None
    image_base64: Optional[str] = None


class PresentationOutput(BaseModel):
    """Output schema for presentation tool."""
    slides: List[PresentationSlide]
    topic: str
    total_slides: int

