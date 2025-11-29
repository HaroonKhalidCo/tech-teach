"""
Flashcards Tool - Generate Q&A flashcards JSON.

This tool:
1. Takes instructions and source content
2. Uses Gemini to generate question-answer pairs
3. Returns JSON with flashcards for frontend rendering
"""

from typing import Dict, Any, Optional, List
import json

from app.tools.base_tool import BaseTool


class FlashcardsTool(BaseTool):
    """Tool for generating flashcards with questions and answers."""
    
    DEFAULT_NUM_CARDS = 10
    
    async def execute(
        self, 
        instructions: str, 
        source_content: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate flashcards with Q&A pairs.
        
        Args:
            instructions: User instructions for flashcards
            source_content: Extracted text from uploaded PDF
            
        Returns:
            Dict with flashcards array
        """
        print(f"[FlashcardsTool] Executing with instructions: {instructions[:100]}...")
        
        num_cards = kwargs.get("num_cards", self.DEFAULT_NUM_CARDS)
        difficulty = kwargs.get("difficulty", "medium")
        
        # Generate flashcards using Gemini
        flashcards = await self._generate_flashcards(
            instructions, source_content, num_cards, difficulty
        )
        
        return {
            "status": "success",
            "tool": "flashcards",
            "flashcards": flashcards,
            "total_cards": len(flashcards),
            "difficulty": difficulty,
            "message": f"Generated {len(flashcards)} flashcards"
        }
    
    async def _generate_flashcards(
        self, 
        instructions: str, 
        source_content: Optional[str],
        num_cards: int,
        difficulty: str
    ) -> List[Dict[str, str]]:
        """Generate flashcard Q&A pairs."""
        prompt = f"""Create educational flashcards for studying.

Instructions: {instructions}

"""
        if source_content:
            prompt += f"""
Source material:
{source_content[:4000]}

"""
        
        prompt += f"""
Generate exactly {num_cards} flashcards with difficulty level: {difficulty}

Return JSON in this exact format:
{{
    "flashcards": [
        {{
            "id": 1,
            "question": "Clear, concise question",
            "answer": "Accurate, informative answer"
        }}
    ]
}}

Requirements:
1. Questions should test understanding, not just memorization
2. Answers should be clear and complete
3. Difficulty should match: {difficulty}
4. Cover different aspects of the topic
5. Questions should be self-contained

Return ONLY valid JSON, no other text."""

        response = await self.generate_text(prompt)
        
        # Parse JSON from response
        try:
            # Clean response
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.startswith('```'):
                response = response[3:]
            if response.endswith('```'):
                response = response[:-3]
            
            data = json.loads(response.strip())
            return data.get("flashcards", [])
        except json.JSONDecodeError as e:
            print(f"[FlashcardsTool] JSON parse error: {e}")
            # Return default structure
            return [
                {
                    "id": i + 1,
                    "question": f"Question {i + 1} about the topic",
                    "answer": "Answer pending - please try again"
                }
                for i in range(min(3, num_cards))
            ]

