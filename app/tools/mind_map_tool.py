"""
Mind Map Tool - Generate comprehensive, detailed mind maps.

This tool creates rich, hierarchical mind maps with:
- Multiple levels of depth (4+ levels)
- Many branches and sub-branches
- Detailed descriptions for each node
- Color coding for different levels
"""

from typing import Dict, Any, Optional, List
import json

from app.tools.base_tool import BaseTool


class MindMapTool(BaseTool):
    """Tool for generating comprehensive mind map structures."""
    
    # Color palette for different levels
    COLORS = [
        "#3b82f6",  # Blue - Root
        "#8b5cf6",  # Purple - Level 1
        "#ec4899",  # Pink - Level 2
        "#f59e0b",  # Amber - Level 3
        "#10b981",  # Emerald - Level 4
        "#06b6d4",  # Cyan - Level 5+
    ]
    
    async def execute(
        self, 
        instructions: str, 
        source_content: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive mind map structure.
        
        Args:
            instructions: User instructions for mind map
            source_content: Extracted text from uploaded PDF
            
        Returns:
            Dict with detailed hierarchical mind map
        """
        print(f"[MindMapTool] Creating detailed mind map: {instructions[:100]}...")
        
        # Use larger defaults for comprehensive maps
        depth = kwargs.get("depth", 4)
        branches = kwargs.get("branches", 6)
        
        # Generate detailed mind map
        mind_map = await self._generate_detailed_mind_map(instructions, source_content, depth, branches)
        
        # Add colors and metadata
        self._add_styling(mind_map, 0)
        
        total_nodes = self._count_nodes(mind_map)
        max_depth = self._get_max_depth(mind_map)
        
        print(f"[MindMapTool] Generated {total_nodes} nodes, {max_depth} levels deep")
        
        return {
            "status": "success",
            "tool": "mind_map",
            "mind_map": mind_map,
            "total_nodes": total_nodes,
            "max_depth": max_depth,
            "message": f"Comprehensive mind map generated with {total_nodes} nodes"
        }
    
    async def _generate_detailed_mind_map(
        self, 
        instructions: str, 
        source_content: Optional[str],
        depth: int,
        branches: int
    ) -> Dict[str, Any]:
        """Generate a comprehensive, detailed mind map."""
        
        prompt = f"""You are an expert educator creating a COMPREHENSIVE and DETAILED mind map.

TOPIC: {instructions}

"""
        if source_content:
            prompt += f"""
REFERENCE MATERIAL:
{source_content[:4000]}

"""
        
        prompt += f"""
Create a LARGE, DETAILED mind map with these specifications:

STRUCTURE REQUIREMENTS:
- Root node: Main topic with a clear, descriptive title
- Level 1: {branches} main branches covering ALL major aspects
- Level 2: Each Level 1 branch should have 3-5 sub-branches
- Level 3: Each Level 2 branch should have 2-4 detail nodes
- Level 4: Add specific examples, facts, or tips where appropriate
- Minimum total nodes: 40+

CONTENT REQUIREMENTS:
- Each node should have a clear, informative label (3-10 words)
- Each node should have a description (1-2 sentences explaining the concept)
- Include practical examples at deeper levels
- Cover the topic comprehensively - don't miss important aspects
- Make it educational and useful for learning

Return JSON in this EXACT format:
{{
    "id": "root",
    "label": "Main Topic Title",
    "description": "A comprehensive overview of the main topic",
    "children": [
        {{
            "id": "1",
            "label": "First Major Category",
            "description": "Explanation of this category",
            "children": [
                {{
                    "id": "1.1",
                    "label": "Sub-topic",
                    "description": "Details about this sub-topic",
                    "children": [
                        {{
                            "id": "1.1.1",
                            "label": "Specific Detail",
                            "description": "Explanation with example",
                            "children": []
                        }},
                        {{
                            "id": "1.1.2",
                            "label": "Another Detail",
                            "description": "More specific information",
                            "children": []
                        }}
                    ]
                }},
                {{
                    "id": "1.2",
                    "label": "Another Sub-topic",
                    "description": "More information here",
                    "children": [
                        {{
                            "id": "1.2.1",
                            "label": "Example or Tip",
                            "description": "Practical application",
                            "children": []
                        }}
                    ]
                }}
            ]
        }},
        {{
            "id": "2",
            "label": "Second Major Category",
            "description": "Explanation of second category",
            "children": [...]
        }}
    ]
}}

IMPORTANT:
- Create at least {branches} main branches (Level 1)
- Go at least {depth} levels deep
- Every node MUST have: id, label, description, children
- Generate a COMPREHENSIVE map - cover everything about the topic
- Make it educational and detailed

Return ONLY valid JSON, no markdown, no explanation."""

        response = await self.generate_text(prompt)
        
        # Parse JSON from response
        try:
            response = response.strip()
            # Remove markdown code blocks if present
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0]
            elif '```' in response:
                response = response.split('```')[1].split('```')[0]
            
            mind_map = json.loads(response.strip())
            
            # Validate structure
            if not isinstance(mind_map, dict) or 'children' not in mind_map:
                raise ValueError("Invalid structure")
                
            return mind_map
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"[MindMapTool] Parse error: {e}, generating fallback...")
            return await self._generate_fallback_map(instructions)
    
    async def _generate_fallback_map(self, instructions: str) -> Dict[str, Any]:
        """Generate a simpler fallback mind map if main generation fails."""
        
        # Try a simpler prompt
        prompt = f"""Create a mind map about: {instructions}

Return JSON with this structure:
{{"id":"root","label":"Topic","description":"Overview","children":[{{"id":"1","label":"Branch","description":"Info","children":[]}}]}}

Include 5 main branches, each with 3 sub-branches. Every node needs: id, label, description, children.
Return ONLY JSON."""

        response = await self.generate_text(prompt)
        
        try:
            response = response.strip()
            if '```' in response:
                response = response.split('```')[1].replace('json', '').split('```')[0]
            return json.loads(response.strip())
        except:
            # Ultimate fallback
            return {
                "id": "root",
                "label": instructions[:50] if instructions else "Main Topic",
                "description": f"Mind map about {instructions}",
                "children": [
                    {
                        "id": str(i),
                        "label": f"Category {i}",
                        "description": f"Main category {i} of the topic",
                        "children": [
                            {
                                "id": f"{i}.{j}",
                                "label": f"Subtopic {i}.{j}",
                                "description": f"Details for subtopic {i}.{j}",
                                "children": []
                            }
                            for j in range(1, 4)
                        ]
                    }
                    for i in range(1, 6)
                ]
            }
    
    def _add_styling(self, node: Dict[str, Any], level: int) -> None:
        """Add color and styling information to nodes."""
        node["level"] = level
        node["color"] = self.COLORS[min(level, len(self.COLORS) - 1)]
        node["expanded"] = level < 2  # Auto-expand first 2 levels
        
        for child in node.get("children", []):
            self._add_styling(child, level + 1)
    
    def _count_nodes(self, node: Dict[str, Any]) -> int:
        """Count total nodes in the mind map."""
        count = 1
        for child in node.get("children", []):
            count += self._count_nodes(child)
        return count
    
    def _get_max_depth(self, node: Dict[str, Any], current: int = 0) -> int:
        """Get the maximum depth of the mind map."""
        if not node.get("children"):
            return current
        
        max_child_depth = current
        for child in node.get("children", []):
            child_depth = self._get_max_depth(child, current + 1)
            max_child_depth = max(max_child_depth, child_depth)
        
        return max_child_depth

