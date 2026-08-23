import os
import json
import google.generativeai as genai
from app.config import settings
from app.models.assessment import AssessmentData, QuestionData

class AssessmentAnalyzer:
    def __init__(self):
        self.api_key = settings.AI_API_KEY
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-pro')
        else:
            self.model = None

    def analyze_pdf(self, file_path: str) -> AssessmentData:
        if not self.model:
            return self._mock_analysis()

        pdf_file = genai.upload_file(path=file_path)

        prompt = """
        Analyze this uploaded assessment PDF.
        Extract the following information in JSON format exactly matching this structure:
        {
          "institution": "Name of institution if present",
          "assessment_type": "Type of assessment (e.g. Class Test, Final Exam)",
          "course_name": "Name of the course",
          "course_code": "Course code",
          "course_outcomes": ["List of course outcomes (e.g. CO4)"],
          "taxonomy": "Overall taxonomy level if present",
          "total_questions": 10,
          "total_marks": 30,
          "sections": ["Part A", "Part B"],
          "rubric": ["Any rubric information found"],
          "instructions": ["Any special instructions"],
          "questions": [
            {
              "question_number": "1",
              "question_text": "Text of the question",
              "section": "Section name if applicable",
              "marks": 5,
              "question_type": "Classification (e.g. Analytical, Definition, Design, Programming)",
              "command_verb": "e.g. Explain, Compare, Design",
              "taxonomy_level": "e.g. Level 4",
              "course_outcome": "e.g. CO4",
              "requires_diagram": true,
              "requires_concept_map": false,
              "requires_code": false,
              "requires_formula": false,
              "requires_table": false,
              "answer_depth": "General depth string based on marks, e.g., 'Medium', 'Comprehensive'"
            }
          ]
        }
        Do not include markdown blocks around the JSON output, just output the raw JSON string.
        Ensure all questions are accurately extracted from the document.
        """

        response = self.model.generate_content([pdf_file, prompt])
        
        try:
            # Strip markdown json blocks if Gemini adds them despite instructions
            text = response.text
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            
            data = json.loads(text.strip())
            return AssessmentData(**data)
        except Exception as e:
            print(f"Error parsing JSON from Gemini: {e}")
            return self._mock_analysis()

    def _mock_analysis(self) -> AssessmentData:
        return AssessmentData(
            institution="SIMATS Engineering",
            assessment_type="Class Test",
            course_name="Cloud Computing and Big Data Analytics",
            course_code="CSA15",
            total_marks=30,
            questions=[
                QuestionData(
                    question_number="1",
                    question_text="Explain Big Data Architecture in detail.",
                    marks=10,
                    question_type="Analytical",
                    requires_diagram=True,
                    answer_depth="Comprehensive"
                )
            ]
        )

assessment_analyzer = AssessmentAnalyzer()
