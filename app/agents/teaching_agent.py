"""
Teaching Agent using Google ADK

This agent orchestrates tool usage for educational content generation.
It receives task requests and delegates to appropriate tools.
"""

from typing import Dict, Any, Optional

from google.adk.agents import LlmAgent

from app.core.config import settings
from app.tools import (
    PDFTool,
    PresentationTool,
    MindMapTool,
    PPTVideoTool,
    FlashcardsTool,
)


class TeachingAgent:
    """
    Teaching Agent that orchestrates educational content generation.
    
    This agent:
    1. Receives requests with task_name, tool_name, and instructions
    2. Processes source material (from PDF if provided)
    3. Delegates to appropriate tool for content generation
    4. Returns generated content to the user
    """
    
    def __init__(self):
        self.tools = {
            "pdf": PDFTool(),
            "presentation": PresentationTool(),
            "mind_map": MindMapTool(),
            "ppt_video": PPTVideoTool(),
            "flashcards": FlashcardsTool(),
        }
        
        # Initialize LLM Agent for orchestration (when needed)
        self.llm_agent = LlmAgent(
            model=settings.TEXT_MODEL,
            name="teaching_agent",
            description="An AI teaching assistant that creates educational content.",
            instruction="""You are an AI Teaching Assistant specialized in creating educational content.

Your role is to help educators by:
1. Understanding their content requirements
2. Processing source materials they provide
3. Generating high-quality educational content

Available output formats:
- PDF: Detailed documents with formatted text
- Presentation: Slides with AI-generated images
- Mind Map: Hierarchical concept visualization
- PPT Video: Video with slides, images, and narration  
- Flashcards: Question and answer study cards

Always create content that is:
- Educational and accurate
- Appropriate for the target audience
- Well-structured and engaging
""",
            tools=[],  # Tools are handled programmatically
        )
    
    async def generate(
        self,
        task_name: str,
        tool_name: str,
        instructions: str,
        source_content: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate educational content using the specified tool.
        
        Args:
            task_name: Type of task (lesson_plan, assessment, homework)
            tool_name: Type of content to generate
            instructions: User instructions for generation
            source_content: Extracted text from source PDF
            **kwargs: Additional parameters for the tool
            
        Returns:
            Generated content data
        """
        print(f"[TeachingAgent] Processing: task={task_name}, tool={tool_name}")
        
        # Get the appropriate tool
        tool = self.tools.get(tool_name)
        if not tool:
            return {
                "status": "error",
                "message": f"Unknown tool: {tool_name}",
                "available_tools": list(self.tools.keys())
            }
        
        # Execute the tool
        try:
            result = await tool.execute(
                instructions=instructions,
                source_content=source_content,
                **kwargs
            )
            return result
        except Exception as e:
            print(f"[TeachingAgent] Error: {e}")
            return {
                "status": "error",
                "message": str(e)
            }


# Singleton instance
teaching_agent = TeachingAgent()
