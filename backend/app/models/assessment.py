from pydantic import BaseModel, Field
from typing import List, Optional, Any

class QuestionData(BaseModel):
    question_number: str
    question_text: str
    section: Optional[str] = None
    marks: float
    question_type: str
    command_verb: Optional[str] = None
    taxonomy_level: Optional[str] = None
    course_outcome: Optional[str] = None
    requires_diagram: bool = False
    requires_concept_map: bool = False
    requires_code: bool = False
    requires_formula: bool = False
    requires_table: bool = False
    answer_depth: Optional[str] = None

class AssessmentData(BaseModel):
    institution: Optional[str] = None
    assessment_type: Optional[str] = None
    course_name: Optional[str] = None
    course_code: Optional[str] = None
    course_outcomes: List[str] = []
    taxonomy: Optional[str] = None
    total_questions: int = 0
    total_marks: float = 0
    sections: List[str] = []
    rubric: List[Any] = []
    instructions: List[str] = []
    questions: List[QuestionData] = []

class GenerationStatus(BaseModel):
    status: str
    message: str
    progress: int

class GeneratedAnswer(BaseModel):
    question_number: str
    answer_text: str
    code_snippet: Optional[str] = None
    diagram_prompt: Optional[str] = None
    diagram_url: Optional[str] = None
    marks: float

class FinalAssessment(BaseModel):
    assessment_data: AssessmentData
    answers: List[GeneratedAnswer]
