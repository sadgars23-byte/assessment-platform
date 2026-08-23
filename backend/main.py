import os
import io
import json
from typing import List, Optional
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

load_dotenv()

app = FastAPI(title="AI Dynamic Assessment Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY not found in environment or .env file.")

client = genai.Client(api_key=api_key)

# ----------------- Data Contracts -----------------

class QuestionMetadata(BaseModel):
    q_no: str = Field(description="Question label, e.g., 'Q1' or '1(a)'")
    question_text: str = Field(description="The extracted question text")
    marks: int = Field(description="Allocated marks for this specific question")
    section: Optional[str] = Field(default="General", description="Section or Part")
    question_type: str = Field(description="Analytical, Descriptive, Coding, Design, etc.")
    taxonomy_level: str = Field(description="Bloom's Taxonomy Level: Remember, Apply, Analyze, Design, etc.")
    depth_budget: str = Field(description="'short' (1-2m), 'medium' (3-5m), 'comprehensive' (8-10m), 'deep' (>10m)")
    requires_diagram: bool = Field(default=False)
    requires_code: bool = Field(default=False)

class AssessmentStructure(BaseModel):
    course_name: str
    course_code: str
    assessment_type: str
    total_marks: int
    total_questions: int
    course_outcome: Optional[str] = "General CO"
    taxonomy_summary: Optional[str] = "Standard Bloom's Matrix"
    questions: List[QuestionMetadata]

class GeneratedAnswer(BaseModel):
    q_no: str
    marks: int
    taxonomy: str
    question_text: str
    answer_text: str
    diagram_mermaid: Optional[str] = None
    code_snippet: Optional[str] = None
    rubric_evidence: List[str]

class GenerationResponse(BaseModel):
    student_name: str
    reg_number: str
    metadata: AssessmentStructure
    answers: List[GeneratedAnswer]

# ----------------- Endpoints -----------------

@app.post("/api/analyze-assessment", response_model=AssessmentStructure)
async def analyze_assessment(file: UploadFile = File(...)):
    """Extracts layout, question tables, taxonomy, and mark allocations."""
    try:
        content = await file.read()
        mime_type = file.content_type or "application/pdf"
        
        prompt = """
        Analyze this uploaded assessment document completely without assuming a fixed format:
        1. Extract Course Name, Course Code, Assessment Type, Total Marks, Total Questions.
        2. Detect all sections, question tables, internal choices, and marks per question.
        3. For each question:
           - Extract exact text and marks.
           - Classify Bloom's Taxonomy Level (e.g., BL1 Remember, BL3 Apply, BL4 Analyze, BL6 Create/Design).
           - Compute depth budget: 'short' for <=2m, 'medium' for 3-5m, 'comprehensive' for 8-10m, 'deep' for >10m.
           - Determine boolean flags for requires_diagram and requires_code.
        Return strictly valid JSON adhering to the schema.
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                types.Part.from_bytes(data=content, mime_type=mime_type),
                prompt
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=AssessmentStructure,
            ),
        )
        return json.loads(response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Assessment extraction failed: {str(e)}")

@app.post("/api/generate-answers", response_model=GenerationResponse)
async def generate_answers(
    student_name: str = Form(...),
    reg_number: str = Form(...),
    assessment_schema_json: str = Form(...)
):
    """Produces answers calibrated against marks, taxonomy, code, and diagrams."""
    try:
        schema_dict = json.loads(assessment_schema_json)
        metadata = AssessmentStructure(**schema_dict)
        
        prompt = f"""
        You are an expert academic evaluator. Generate complete, high-scoring solutions for this assessment.

        STRICT RULES:
        1. MARKS DICTATE EVIDENCE DEPTH:
           - 1-2 Marks: Direct definitions, short formula, or 2 key points.
           - 3-5 Marks: Structured explanation with 1 core example or brief architecture overview.
           - 8-10+ Marks: In-depth technical breakdown, multi-step analysis, design trade-offs, architecture, and conclusion.
        2. DIAGRAMS: If requires_diagram is true, provide valid Mermaid.js diagram syntax in 'diagram_mermaid'.
        3. CODE: If requires_code is true, provide clean, commented source code with sample input/output in 'code_snippet'.
        4. RUBRIC: Detail key technical criteria fulfilled in 'rubric_evidence'.

        Assessment Context:
        {json.dumps(schema_dict, indent=2)}
        """

        class AnswerList(BaseModel):
            answers: List[GeneratedAnswer]

        response = client.models.generate_content(
            model='gemini-2.5-pro',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=AnswerList,
            ),
        )
        
        result_data = json.loads(response.text)
        return GenerationResponse(
            student_name=student_name,
            reg_number=reg_number,
            metadata=metadata,
            answers=result_data["answers"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Answer generation failed: {str(e)}")

@app.post("/api/download-pdf")
async def download_pdf(payload: GenerationResponse):
    """Generates an academic-format submission PDF."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#0f172a'))
    meta_style = ParagraphStyle('DocMeta', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#475569'))
    q_title = ParagraphStyle('QTitle', parent=styles['Heading2'], fontSize=11, textColor=colors.HexColor('#1e293b'))
    body_style = ParagraphStyle('BodyTextCustom', parent=styles['Normal'], fontSize=9, leading=13, textColor=colors.HexColor('#334155'))
    code_style = ParagraphStyle('CodeCustom', parent=styles['Code'], fontSize=8, leading=10, textColor=colors.HexColor('#0f172a'))

    elements = []
    
    elements.append(Paragraph(f"{payload.metadata.course_name} ({payload.metadata.course_code})", title_style))
    elements.append(Paragraph(f"<b>Assessment:</b> {payload.metadata.assessment_type} | <b>Total Marks:</b> {payload.metadata.total_marks}", meta_style))
    elements.append(Paragraph(f"<b>Student:</b> {payload.student_name} | <b>Reg No:</b> {payload.reg_number}", meta_style))
    elements.append(Spacer(1, 15))

    for ans in payload.answers:
        elements.append(Paragraph(f"<b>{ans.q_no}</b> [{ans.marks} Marks] &mdash; <i>{ans.taxonomy}</i>", q_title))
        elements.append(Paragraph(f"<b>Q:</b> {ans.question_text}", meta_style))
        elements.append(Spacer(1, 4))
        elements.append(Paragraph(ans.answer_text.replace('\n', '<br/>'), body_style))
        elements.append(Spacer(1, 4))
        
        if ans.diagram_mermaid:
            elements.append(Paragraph("<b>[Mermaid Diagram Spec]:</b>", meta_style))
            elements.append(Preformatted(ans.diagram_mermaid, code_style))
            elements.append(Spacer(1, 4))
            
        if ans.code_snippet:
            elements.append(Paragraph("<b>[Code Implementation]:</b>", meta_style))
            elements.append(Preformatted(ans.code_snippet, code_style))
            elements.append(Spacer(1, 4))

        elements.append(Spacer(1, 10))

    doc.build(elements)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={payload.metadata.course_code}_Answers.pdf"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
