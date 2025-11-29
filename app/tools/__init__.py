"""
Tools module for the Teaching Agent.

Available Tools:
- pdf_tool: Generate PDF documents from text
- presentation_tool: Create presentations with AI-generated images
- mind_map_tool: Generate mind map JSON for frontend rendering
- ppt_video_tool: Create videos with images, text, and voice
- flashcards_tool: Generate Q&A flashcards JSON

Future Tools:
- homework_tool: Create homework assignments
- assessment_tool: Create assessments and tests
"""

from .pdf_tool import PDFTool
from .presentation_tool import PresentationTool
from .mind_map_tool import MindMapTool
from .ppt_video_tool import PPTVideoTool
from .flashcards_tool import FlashcardsTool

__all__ = [
    "PDFTool",
    "PresentationTool",
    "MindMapTool",
    "PPTVideoTool",
    "FlashcardsTool",
]
