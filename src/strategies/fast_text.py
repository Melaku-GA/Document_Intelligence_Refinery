import pdfplumber
from pathlib import Path
from typing import List
from src.models.schemas import ExtractedDocument, TextBlock, TableObject, BBox

class FastTextExtractor:
    """
    Strategy A: High-speed extraction for native digital PDFs.
    Uses pdfplumber to extract text and basic tables directly from the PDF layer.
    """
    def __init__(self):
        pass

    def extract(self, path: str) -> ExtractedDocument:
        blocks: List[TextBlock] = []
        tables: List[TableObject] = []
        total_pages = 0

        with pdfplumber.open(path) as pdf:
            total_pages = len(pdf.pages)
            for page_idx, page in enumerate(pdf.pages):
                page_num = page_idx + 1
                
                # 1. Extract Text with Layout Preservation
                text_content = page.extract_text(layout=True)
                if text_content:
                    # For Strategy A, we treat the whole page as a block 
                    # unless more granular segmentation is needed.
                    blocks.append(TextBlock(
                        text=text_content,
                        block_type="page_content",
                        bbox=BBox(page=page_num, x0=0, y0=0, x1=page.width, y1=page.height)
                    ))

                # 2. Extract Tables (Basic Detection)
                # Strategy A uses pdfplumber's built-in table finder
                found_tables = page.extract_tables()
                for table in found_tables:
                    # Filter out empty tables
                    clean_table = [row for row in table if any(cell and cell.strip() for cell in row)]
                    if not clean_table:
                        continue

                    tables.append(TableObject(
                        headers=clean_table[0],
                        rows=clean_table[1:] if len(clean_table) > 1 else [],
                        bbox=BBox(page=page_num, x0=0, y0=0, x1=100, y1=100) # Placeholder coordinates
                    ))

        return ExtractedDocument(
            doc_id=Path(path).stem,
            blocks=blocks,
            tables=tables,
            extraction_strategy_used="Strategy A (pdfplumber)",
            total_pages=total_pages
        )