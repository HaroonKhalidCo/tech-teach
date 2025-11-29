"""
Presentation Tool - Generate professional slides using Gemini 2.0 Flash.

Uses Gemini 2.0 Flash for:
- Text generation (slide content)
- Image generation (slide visuals with text)
"""

import base64
import asyncio
from typing import Dict, Any, Optional, List
import json

from app.tools.base_tool import BaseTool


class PresentationTool(BaseTool):
    """Generate professional presentation slides with Gemini 2.0 Flash."""
    
    NUM_SLIDES = 5
    
    async def execute(
        self, 
        instructions: str, 
        source_content: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate 5 professional slides."""
        print(f"[PresentationTool] Creating slides for: {instructions[:50]}...")
        
        # Step 1: Generate slide content with Gemini text
        slides_content = await self._generate_content(instructions, source_content)
        
        # Step 2: Generate images with Gemini 2.0 Flash
        slides = await self._generate_slide_images(slides_content, instructions)
        
        return {
            "status": "success",
            "tool": "presentation",
            "slides": slides,
            "total_slides": len(slides),
            "message": f"Generated {len(slides)} professional slides"
        }
    
    async def _generate_content(self, instructions: str, source: Optional[str]) -> List[Dict]:
        """Generate slide content using Gemini text model."""
        prompt = f"""Create 5 professional presentation slides about: {instructions}

{f'Reference: {source[:1500]}' if source else ''}

Return JSON:
{{
    "slides": [
        {{
            "number": 1,
            "title": "What is [Topic]?",
            "content": "Clear explanation in 2-3 sentences about this topic.",
            "visual": "Describe what illustration should be shown - be SPECIFIC (e.g., for photosynthesis: green plant with sun rays, CO2 arrows going in, O2 arrows coming out)"
        }}
    ]
}}

Make each slide different:
- Slide 1: Introduction/Definition
- Slide 2: Key components or concepts
- Slide 3: How it works/Process
- Slide 4: Examples or applications  
- Slide 5: Summary/Takeaways

Return ONLY valid JSON."""

        response = await self.generate_text(prompt)
        
        try:
            text = response.strip()
            if '```' in text:
                text = text.split('```')[1].replace('json', '', 1)
            data = json.loads(text.strip())
            return data.get("slides", [])
        except:
            return [
                {"number": i+1, "title": f"Slide {i+1}", "content": f"About {instructions}", "visual": "Educational diagram"}
                for i in range(5)
            ]
    
    async def _generate_slide_images(self, slides: List[Dict], topic: str) -> List[Dict]:
        """Generate professional slide images using Gemini 2.0 Flash."""
        
        # Color schemes for variety
        colors = [
            "light green background (#E8F5E9), teal text box (#0D9488), yellow title (#FFD93D)",
            "light blue background (#E3F2FD), navy text box (#1E3A5F), white title",
            "cream background (#FFF8E1), purple text box (#7C3AED), white title",
            "white background, emerald accents (#059669), dark text",
            "light lavender background (#F3E5F5), dark blue box (#0F172A), cyan title (#06B6D4)"
        ]
        
        # Layouts for variety
        layouts = [
            "LEFT: colorful cartoon illustration (40%). RIGHT: rounded rectangle text box with title and content (60%)",
            "LEFT: text box (40%). RIGHT: detailed diagram/infographic (60%)",
            "CENTER TOP: title. CENTER: large educational diagram. BOTTOM: text summary",
            "LEFT: process flowchart or icons. RIGHT: explanation text box",
            "TOP: bold title banner. CENTER: key points as cards/icons. Clean summary layout"
        ]
        
        async def create_slide(slide: Dict, index: int) -> Dict:
            result = {
                "slide_number": slide.get("number", index + 1),
                "title": slide.get("title", ""),
                "content": slide.get("content", ""),
                "image_base64": None
            }
            
            try:
                prompt = f"""Create a professional educational presentation slide image.

TOPIC: {topic}
SLIDE {index + 1} of 5

DESIGN:
- Style: Modern educational infographic like Khan Academy or professional textbook
- Colors: {colors[index % len(colors)]}
- Layout: {layouts[index % len(layouts)]}
- Must be 16:9 aspect ratio
- High quality, clean, professional

CONTENT TO INCLUDE ON THE SLIDE:
- TITLE: "{slide.get('title', '')}" (large, bold, prominent)
- TEXT: "{slide.get('content', '')[:200]}"
- SLIDE NUMBER: {index + 1} (in corner badge)

ILLUSTRATION:
{slide.get('visual', 'Educational diagram related to the topic')}

IMPORTANT:
- Make topic-specific illustrations (fitness=dumbbells/gym, nature=trees/plants, science=diagrams/molecules, etc.)
- Include the title text ON the image
- Include explanation text ON the image in a text box
- Professional quality suitable for classroom use
- Each slide should look different from others"""

                image_bytes = await self.generate_image(prompt)
                result["image_base64"] = base64.b64encode(image_bytes).decode('utf-8')
                print(f"[PresentationTool] Slide {index+1} generated")
                
            except Exception as e:
                print(f"[PresentationTool] Slide {index+1} error: {e}")
                result["image_base64"] = None
            
            return result
        
        # Generate all slides in parallel
        tasks = [create_slide(slide, i) for i, slide in enumerate(slides)]
        return await asyncio.gather(*tasks)
