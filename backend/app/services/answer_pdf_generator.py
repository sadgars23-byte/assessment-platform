from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.units import inch
from app.models.assessment import FinalAssessment, GeneratedAnswer
import os
import requests
import tempfile

class AnswerPDFGenerator:
    def generate_pdf(self, assessment_data: FinalAssessment, output_path: str):
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        styles = getSampleStyleSheet()
        # Create Times New Roman 12pt styles
        styles.add(ParagraphStyle(name='TimesNormal', fontName='Times-Roman', fontSize=12, leading=14, alignment=4)) # Justified
        styles.add(ParagraphStyle(name='TimesBold', fontName='Times-Bold', fontSize=12, leading=14))
        styles.add(ParagraphStyle(name='TimesTitle', fontName='Times-Bold', fontSize=16, leading=18, alignment=1)) # Center
        
        Story = []
        
        # Header
        Story.append(Paragraph("AI GENERATED ASSESSMENT ANSWERS", styles['TimesTitle']))
        Story.append(Spacer(1, 0.2 * inch))
        
        # We don't have student name in FinalAssessment object right now, we can pass it as a parameter,
        # but for simplicity we'll just put the course info
        Story.append(Paragraph(f"Course: {assessment_data.assessment_data.course_name or 'N/A'}", styles['TimesNormal']))
        Story.append(Paragraph(f"Course Code: {assessment_data.assessment_data.course_code or 'N/A'}", styles['TimesNormal']))
        Story.append(Paragraph(f"Assessment: {assessment_data.assessment_data.assessment_type or 'N/A'}", styles['TimesNormal']))
        Story.append(Spacer(1, 0.5 * inch))
        
        # Answers
        for answer in assessment_data.answers:
            Story.append(Paragraph(f"Question {answer.question_number}", styles['TimesBold']))
            Story.append(Paragraph(f"Marks: {answer.marks}", styles['TimesNormal']))
            Story.append(Spacer(1, 0.1 * inch))
            
            # Formatted answer text (handles some basic newlines)
            for para in answer.answer_text.split('\n'):
                if para.strip():
                    Story.append(Paragraph(para.strip(), styles['TimesNormal']))
                    Story.append(Spacer(1, 0.05 * inch))
            
            if answer.diagram_url:
                try:
                    # Download image to temp file
                    response = requests.get(answer.diagram_url)
                    if response.status_code == 200:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                            tmp.write(response.content)
                            tmp_path = tmp.name
                        
                        img = Image(tmp_path, width=4*inch, height=3*inch)
                        Story.append(Spacer(1, 0.1 * inch))
                        Story.append(img)
                        Story.append(Spacer(1, 0.1 * inch))
                        # We don't delete tmp here because ReportLab needs it during build.
                        # It can be cleaned up later.
                except Exception as e:
                    print(f"Failed to fetch image: {e}")
                    
            if answer.code_snippet:
                # Add code block with monospace font
                code_style = ParagraphStyle(name='Code', fontName='Courier', fontSize=10, leading=12)
                for line in answer.code_snippet.split('\n'):
                    Story.append(Paragraph(line, code_style))
                
            Story.append(Spacer(1, 0.3 * inch))
            
        doc.build(Story)

answer_pdf_generator = AnswerPDFGenerator()
