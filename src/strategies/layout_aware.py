import logging
import warnings
import pdfplumber
from pathlib import Path
from typing import List, Optional
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from src.models.schemas import ExtractedDocument, TextBlock, TableObject, BBox

# Suppress specific warnings
warnings.filterwarnings("ignore", category=UserWarning)

# Page threshold to use pdfplumber instead of Docling (to avoid memory issues)
DOCLING_PAGE_THRESHOLD = 20


class LayoutExtractor:
    def __init__(self):
        self.logger = logging.getLogger("Refinery.StrategyB")
        
        # Configure Docling pipeline for table extraction
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_table_structure = True
        pipeline_options.do_ocr = False  # Strategy B is for digital PDFs
        
        self.converter = DocumentConverter(
            format_options={
                "pdf": PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

    def extract(self, path: str) -> ExtractedDocument:
        self.logger.info(f"Starting extraction for: {path}")
        
        # First, check page count to determine best extraction method
        try:
            with pdfplumber.open(path) as pdf:
                page_count = len(pdf.pages)
                
            self.logger.info(f"Document has {page_count} pages")
            
            # For large documents, use pdfplumber directly to avoid Docling memory issues
            if page_count > DOCLING_PAGE_THRESHOLD:
                self.logger.info(f"Large document detected ({page_count} pages), using pdfplumber for stability")
                return self._extract_with_pdfplumber(path)
            else:
                # For smaller documents, try Docling first then fallback
                return self._extract_with_docling_or_fallback(path)
                
        except Exception as e:
            self.logger.warning(f"Could not determine page count: {e}")
            return self._extract_with_pdfplumber(path)
    
    def _extract_with_docling_or_fallback(self, path: str) -> ExtractedDocument:
        """Try Docling, fallback to pdfplumber on failure."""
        try:
            return self._extract_with_docling(path)
        except Exception as e:
            self.logger.error(f"Docling extraction failed: {e}")
            self.logger.info("Falling back to pdfplumber for text extraction")
            return self._extract_with_pdfplumber(path)

    def _extract_with_docling(self, path: str) -> ExtractedDocument:
        """Extract using Docling."""
        result = self.converter.convert(path)
        doc = result.document
        
        # Map Text Blocks
        blocks = []
        for item in doc.texts:
            page_no = item.prov[0].page_no if item.prov else 1
            bbox_data = item.prov[0].bbox if item.prov else None
            
            blocks.append(TextBlock(
                text=item.text,
                block_type=getattr(item, "label", "paragraph"),
                bbox=self._map_bbox(page_no, bbox_data)
            ))
            
        # Map Tables
        tables = []
        for table_item in doc.tables:
            df = table_item.export_to_dataframe(doc=doc)
            page_no = table_item.prov[0].page_no if table_item.prov else 1
            
            tables.append(TableObject(
                caption=getattr(table_item, "caption", None),
                headers=df.columns.tolist() if df is not None else [],
                rows=df.values.tolist() if df is not None else [],
                bbox=self._map_bbox(page_no, table_item.prov[0].bbox if table_item.prov else None)
            ))

        return ExtractedDocument(
            doc_id=Path(path).stem,
            blocks=blocks,
            tables=tables,
            extraction_strategy_used="Strategy B (Docling)",
            total_pages=len(doc.pages) if hasattr(doc, 'pages') else 1
        )

    def _extract_with_pdfplumber(self, path: str) -> ExtractedDocument:
        """Fallback extraction using pdfplumber - more memory efficient."""
        self.logger.info(f"Using pdfplumber for: {path}")
        
        all_blocks = []
        all_tables = []
        
        with pdfplumber.open(path) as pdf:
            total_pages = len(pdf.pages)
            self.logger.info(f"Processing {total_pages} pages with pdfplumber")
            
            for page_num, page in enumerate(pdf.pages, 1):
                try:
                    # Extract text
                    text = page.extract_text() or ""
                    if text.strip():
                        all_blocks.append(TextBlock(
                            text=text,
                            block_type="paragraph",
                            bbox=BBox(page=page_num, x0=0, y0=0, x1=0, y1=0)
                        ))
                    
                    # Extract tables with simple default settings
                    tables = page.extract_tables()
                    
                    for table_data in tables:
                        if table_data and len(table_data) > 0:
                            # Filter out empty rows and clean up
                            cleaned_rows = []
                            for row in table_data:
                                # Skip rows that are mostly empty or None
                                if row and any(cell is not None and str(cell).strip() for cell in row):
                                    cleaned_row = [str(cell).strip() if cell else "" for cell in row]
                                    cleaned_rows.append(cleaned_row)
                            
                            if cleaned_rows:
                                headers = cleaned_rows[0] if cleaned_rows else []
                                rows = cleaned_rows[1:] if len(cleaned_rows) > 1 else []
                                
                                all_tables.append(TableObject(
                                    caption=None,
                                    headers=headers,
                                    rows=rows,
                                    bbox=BBox(page=page_num, x0=0, y0=0, x1=0, y1=0)
                                ))
                    
                except Exception as e:
                    self.logger.warning(f"Failed to extract page {page_num}: {e}")
                    continue
        
        return ExtractedDocument(
            doc_id=Path(path).stem,
            blocks=all_blocks,
            tables=all_tables,
            extraction_strategy_used="Strategy B (PdfPlumber)",
            total_pages=total_pages
        )

    def _map_bbox(self, page: int, docling_bbox) -> BBox:
        """Normalizes Docling coordinates to our schema."""
        if not docling_bbox:
            return BBox(page=page, x0=0, y0=0, x1=0, y1=0)
        return BBox(
            page=page,
            x0=docling_bbox.l,
            y0=docling_bbox.t,
            x1=docling_bbox.r,
            y1=docling_bbox.b
        )