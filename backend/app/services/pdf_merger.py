from pypdf import PdfWriter, PdfReader
import os

class PDFMerger:
    def merge_assessment_and_answers(self, original_pdf_path: str, answer_pdf_path: str, output_pdf_path: str):
        """
        Merges the original assessment PDF and the AI-generated answers PDF.
        The original assessment must appear first.
        """
        if not os.path.exists(original_pdf_path):
            raise FileNotFoundError(f"Original PDF not found at {original_pdf_path}")
            
        if not os.path.exists(answer_pdf_path):
            raise FileNotFoundError(f"Answer PDF not found at {answer_pdf_path}")
            
        merger = PdfWriter()

        # Add original PDF first
        merger.append(original_pdf_path)
        
        # Add generated answer PDF second
        merger.append(answer_pdf_path)
        
        # Write out the merged PDF
        with open(output_pdf_path, "wb") as output_file:
            merger.write(output_file)
            
        merger.close()

pdf_merger = PDFMerger()
