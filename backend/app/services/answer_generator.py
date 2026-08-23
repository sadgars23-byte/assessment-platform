import os
import requests
import urllib.parse
import google.generativeai as genai
from app.config import settings
from app.models.assessment import QuestionData, GeneratedAnswer, AssessmentData

class AnswerGenerator:
    def __init__(self):
        self.api_key = settings.AI_API_KEY
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-pro')
        else:
            self.model = None

    def generate_diagram(self, prompt: str) -> str:
        """
        Generates an image using Pollinations.ai (free, no auth required)
        based on the prompt. Returns the URL of the generated image.
        """
        encoded_prompt = urllib.parse.quote(prompt)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=600&nologo=true"
        return image_url

    def generate_answer(self, assessment: AssessmentData, question: QuestionData) -> GeneratedAnswer:
        if not self.model:
            return self._mock_answer(question)
            
        context_prompt = f"""
        You are an academic expert generating an answer for a student's assessment.
        Course: {assessment.course_name} ({assessment.course_code})
        Assessment Type: {assessment.assessment_type}
        
        Question {question.question_number}: {question.question_text}
        Marks: {question.marks}
        Depth Expected: {question.answer_depth}
        
        Instructions:
        1. Generate a comprehensive answer appropriate for {question.marks} marks.
        2. If the question requires code ({question.requires_code}), include a robust code snippet.
        3. If the question requires a diagram ({question.requires_diagram}), provide a short visual description prompt suitable for an AI Image Generator at the very end in a special tag: <DIAGRAM_PROMPT>description here</DIAGRAM_PROMPT>.
        4. Format the output clearly.
        """
        
        response = self.model.generate_content(context_prompt)
        
        answer_text = response.text
        diagram_prompt = None
        diagram_url = None
        code_snippet = None
        
        if "<DIAGRAM_PROMPT>" in answer_text and "</DIAGRAM_PROMPT>" in answer_text:
            start_idx = answer_text.find("<DIAGRAM_PROMPT>") + len("<DIAGRAM_PROMPT>")
            end_idx = answer_text.find("</DIAGRAM_PROMPT>")
            diagram_prompt = answer_text[start_idx:end_idx].strip()
            answer_text = answer_text[:answer_text.find("<DIAGRAM_PROMPT>")].strip()
            
            diagram_url = self.generate_diagram(diagram_prompt)
            
        return GeneratedAnswer(
            question_number=question.question_number,
            answer_text=answer_text,
            code_snippet=code_snippet,
            diagram_prompt=diagram_prompt,
            diagram_url=diagram_url,
            marks=question.marks
        )

    def _mock_answer(self, question: QuestionData) -> GeneratedAnswer:
        prompt = f"A diagram illustrating {question.question_text}"
        return GeneratedAnswer(
            question_number=question.question_number,
            answer_text=f"This is a mock answer for question {question.question_number} worth {question.marks} marks. It covers all the points expected.",
            diagram_prompt=prompt if question.requires_diagram else None,
            diagram_url=self.generate_diagram(prompt) if question.requires_diagram else None,
            marks=question.marks
        )

answer_generator = AnswerGenerator()
