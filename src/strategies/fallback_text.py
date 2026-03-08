import fitz  # PyMuPDF
import uuid
from src.models.schemas import ExtractedDocument


class FallbackTextExtractor:

    def extract(self, pdf_path: str) -> ExtractedDocument:

        doc = fitz.open(pdf_path)

        blocks = []

        for page_num, page in enumerate(doc):

            text = page.get_text()

            blocks.append({
                "text": text,
                "page": page_num,
                "bbox": None
            })

        return ExtractedDocument(
            doc_id=str(uuid.uuid4()),
            blocks=blocks,
            tables=[]
        )