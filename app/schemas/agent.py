"""Schemas for agent-related API endpoints."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class ToolType(str, Enum):
    """Available tool types for the teaching agent."""
    PPT = "ppt"
    VIDEO = "video"
    MIND_MAP = "mind_map"
    FLASHCARDS = "flashcards"
    PDF = "pdf"
    LESSON_PLAN = "lesson_plan"


class AgentRequest(BaseModel):
    """Request schema for agent interactions."""
    message: str = Field(..., description="User message or query for the agent")
    tool_type: Optional[ToolType] = Field(None, description="Specific tool to use (optional)")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")


class AgentResponse(BaseModel):
    """Response schema for agent interactions."""
    response: str = Field(..., description="Agent's response message")
    tool_used: Optional[str] = Field(None, description="Name of the tool that was used")
    tool_output: Optional[Dict[str, Any]] = Field(None, description="Output from the tool")
    status: str = Field(default="success", description="Response status")


class ToolRequest(BaseModel):
    """Request schema for direct tool invocation."""
    tool_type: ToolType = Field(..., description="Type of tool to invoke")
    topic: str = Field(..., description="Main topic for content generation")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Tool-specific parameters")


class ToolResponse(BaseModel):
    """Response schema for tool invocation."""
    tool: str = Field(..., description="Name of the tool invoked")
    status: str = Field(..., description="Execution status")
    data: Dict[str, Any] = Field(..., description="Tool output data")
    message: Optional[str] = Field(None, description="Additional message")

