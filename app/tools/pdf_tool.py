"""
PDF Tool - Generate PDF documents and send to frontend.

Uses Gemini text model to generate content,
then ReportLab to create a professional PDF.
PDF is returned as base64 data (not saved locally).
"""

import io
import base64
from typing import Dict, Any, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER

from app.tools.base_tool import BaseTool


class PDFTool(BaseTool):
    """Generate professional PDF documents (sent directly to frontend)."""
    
    async def execute(
        self, 
        instructions: str, 
        source_content: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a PDF document and return as base64."""
        print(f"[PDFTool] Creating PDF for: {instructions[:50]}...")
        
        # Step 1: Generate content with Gemini text model
        content = await self._generate_content(instructions, source_content)
        
        # Step 2: Create PDF in memory and get base64
        pdf_base64 = self._create_pdf_base64(content, instructions)
        
        print(f"[PDFTool] PDF generated, size: {len(pdf_base64)} bytes (base64)")
        
        return {
            "status": "success",
            "tool": "pdf",
            "pdf_base64": pdf_base64,
            "content_preview": content[:500] + "..." if len(content) > 500 else content,
            "message": "PDF document generated successfully"
        }
    
    async def _generate_content(self, instructions: str, source: Optional[str]) -> str:
        """Generate PDF content using Gemini text model."""
        prompt = f"""Create detailed educational content for a PDF document.

Topic: {instructions}

{f'Reference material: {source[:2000]}' if source else ''}

Write comprehensive content with:
1. A clear title
2. Introduction paragraph
3. Multiple sections with headings (use ## for headings)
4. Detailed explanations
5. Key points and takeaways
6. Conclusion

Make it educational, well-structured, and informative.
Write at least 500 words of quality content."""

        return await self.generate_text(prompt)
    
    def _create_pdf_base64(self, content: str, title: str) -> str:
        """Create PDF in memory and return as base64 string."""
        # Create PDF in memory buffer
        buffer = io.BytesIO()
        
        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=60,
            leftMargin=60,
            topMargin=60,
            bottomMargin=60
        )
        
        # Styles
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=22,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1E3A5F')
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceBefore=15,
            spaceAfter=10,
            textColor=colors.HexColor('#2563EB')
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=11,
            leading=16,
            alignment=TA_JUSTIFY,
            spaceAfter=10
        )
        
        # Build content
        story = []
        
        # Add title
        clean_title = title[:80].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        story.append(Paragraph(clean_title, title_style))
        story.append(Spacer(1, 0.3 * inch))
        
        # Parse content
        paragraphs = content.split('\n')
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # Escape special characters
            para = para.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            # Check for headings
            if para.startswith('##'):
                text = para.lstrip('#').strip()
                story.append(Paragraph(text, heading_style))
            elif para.startswith('#'):
                text = para.lstrip('#').strip()
                story.append(Paragraph(text, heading_style))
            elif para.startswith('**') and para.endswith('**'):
                text = para.strip('*')
                story.append(Paragraph(text, heading_style))
            else:
                story.append(Paragraph(para, body_style))
        
        # Build PDF to buffer
        doc.build(story)
        
        # Get bytes and convert to base64
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return base64.b64encode(pdf_bytes).decode('utf-8')
