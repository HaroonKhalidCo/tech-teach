"""
Agents module for Tech-Teach.

The teaching agent orchestrates tool usage for content generation.
Uses Google ADK with Gemini models.
"""

from .teaching_agent import TeachingAgent, teaching_agent

__all__ = ["TeachingAgent", "teaching_agent"]
