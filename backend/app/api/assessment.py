from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict
import shutil
import os
import uuid
import tempfile
import asyncio

from app.services.assessment_analyzer import assessment_analyzer
from app.services.answer_generator import answer_generator
from app.services.answer_pdf_generator import answer_pdf_generator
from app.services.pdf_merger import pdf_merger
from app.models.assessment import FinalAssessment

router = APIRouter()

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# In-memory storage for MVP
assessments_db: Dict[str, dict] = {}

class AnalyzeResponse(BaseModel):
    assessment_id: str
    analysis: dict

def process_assessment_task(assessment_id: str, file_path: str):
    assessments_db[assessment_id]["status"] = "Analyzing assessment..."
    assessments_db[assessment_id]["progress"] = 30
    
    # Analyze the PDF using AI
    assessment_data = assessment_analyzer.analyze_pdf(file_path)
    
    assessments_db[assessment_id]["analysis_data"] = assessment_data.model_dump()
    assessments_db[assessment_id]["status"] = "Analysis complete. Ready to generate."
    assessments_db[assessment_id]["progress"] = 50

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_assessment(
    background_tasks: BackgroundTasks,
    student_name: str = Form(...),
    registration_number: str = Form(...),
    assessment_pdf: UploadFile = File(...)
):
    if not assessment_pdf.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Please upload a valid PDF assessment.")
    
    assessment_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{assessment_id}.pdf")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(assessment_pdf.file, buffer)
        
    assessments_db[assessment_id] = {
        "student_name": student_name,
        "registration_number": registration_number,
        "file_path": file_path,
        "status": "Reading assessment",
        "progress": 10,
        "analysis_data": None,
        "generated_answers": [],
        "final_pdf_path": None
    }
    
    background_tasks.add_task(process_assessment_task, assessment_id, file_path)
    
    return AnalyzeResponse(
        assessment_id=assessment_id,
        analysis={"message": "Analysis started"}
    )

@router.get("/{assessment_id}/status")
async def get_status(assessment_id: str):
    if assessment_id not in assessments_db:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    assessment = assessments_db[assessment_id]
    return {
        "status": assessment.get("status", "Unknown"),
        "progress": assessment.get("progress", 0)
    }

def generate_answers_task(assessment_id: str):
    try:
        assessments_db[assessment_id]["status"] = "Generating answers..."
        assessments_db[assessment_id]["progress"] = 60
        
        # Load the AssessmentData
        import app.models.assessment as models
        assessment_data = models.AssessmentData(**assessments_db[assessment_id]["analysis_data"])
        
        generated_answers = []
        total_questions = len(assessment_data.questions)
        
        for idx, question in enumerate(assessment_data.questions):
            # Update progress incrementally
            progress_incr = 60 + int((idx / total_questions) * 20)
            assessments_db[assessment_id]["progress"] = progress_incr
            assessments_db[assessment_id]["status"] = f"Generating answer for question {question.question_number}..."
            
            answer = answer_generator.generate_answer(assessment_data, question)
            generated_answers.append(answer)
            
        assessments_db[assessment_id]["generated_answers"] = [ans.model_dump() for ans in generated_answers]
        
        # Validation could go here (re-generating if failed)
        
        assessments_db[assessment_id]["status"] = "Creating answer PDF..."
        assessments_db[assessment_id]["progress"] = 85
        
        final_assessment = models.FinalAssessment(
            assessment_data=assessment_data,
            answers=generated_answers
        )
        
        answer_pdf_path = os.path.join(OUTPUT_DIR, f"{assessment_id}_answers.pdf")
        answer_pdf_generator.generate_pdf(final_assessment, answer_pdf_path)
        
        assessments_db[assessment_id]["status"] = "Combining PDFs..."
        assessments_db[assessment_id]["progress"] = 95
        
        final_pdf_path = os.path.join(OUTPUT_DIR, f"{assessment_id}_final.pdf")
        original_pdf_path = assessments_db[assessment_id]["file_path"]
        
        pdf_merger.merge_assessment_and_answers(original_pdf_path, answer_pdf_path, final_pdf_path)
        
        assessments_db[assessment_id]["final_pdf_path"] = final_pdf_path
        assessments_db[assessment_id]["status"] = "Final PDF ready"
        assessments_db[assessment_id]["progress"] = 100
        
    except Exception as e:
        print(f"Error in generation task: {e}")
        assessments_db[assessment_id]["status"] = "Generation failed"
        assessments_db[assessment_id]["progress"] = 0

@router.post("/{assessment_id}/generate")
async def generate_answers(assessment_id: str, background_tasks: BackgroundTasks):
    if assessment_id not in assessments_db:
        raise HTTPException(status_code=404, detail="Assessment not found")
        
    background_tasks.add_task(generate_answers_task, assessment_id)
    
    return {"message": "Generation started"}

@router.get("/{assessment_id}/preview")
async def preview_assessment(assessment_id: str):
    if assessment_id not in assessments_db:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    return assessments_db[assessment_id].get("analysis_data", {})

from fastapi.responses import FileResponse

@router.get("/{assessment_id}/download")
async def download_pdf(assessment_id: str):
    if assessment_id not in assessments_db:
        raise HTTPException(status_code=404, detail="Assessment not found")
        
    file_path = assessments_db[assessment_id].get("final_pdf_path")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Final PDF not ready")
        
    student_name = assessments_db[assessment_id]["student_name"].replace(" ", "_")
    reg_number = assessments_db[assessment_id]["registration_number"].replace(" ", "_")
    filename = f"{student_name}_{reg_number}_Assessment.pdf"
    
    return FileResponse(file_path, filename=filename, media_type="application/pdf")
