import logging
from pathlib import Path
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from src.models.schemas import ExtractedDocument, TextBlock, TableObject, BBox

class LayoutExtractor:
    def __init__(self):
        self.logger = logging.getLogger("Refinery.StrategyB")
        
        # Configure Docling for high-fidelity table extraction
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_table_structure = True
        pipeline_options.do_ocr = False  # Strategy B is for digital PDFs; C handles OCR
        
        self.converter = DocumentConverter(
            format_options={
                "pdf": PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

    def extract(self, path: str) -> ExtractedDocument:
        self.logger.info(f"Starting Docling extraction for: {path}")
        
        # 1. Convert document
        result = self.converter.convert(path)
        doc = result.document
        
        # 2. Map Text Blocks
        blocks = []
        for item in doc.texts:
            # item.prov contains coordinates; item.text contains the content
            page_no = item.prov[0].page_no if item.prov else 1
            bbox_data = item.prov[0].bbox if item.prov else None
            
            blocks.append(TextBlock(
                text=item.text,
                block_type=getattr(item, "label", "paragraph"),
                bbox=self._map_bbox(page_no, bbox_data)
            ))
            
        # 3. Map Tables
        tables = []
        for table_item in doc.tables:
            # Docling can export directly to a Pandas DataFrame or Markdown
            #df = table_item.export_to_dataframe()
            df = table_item.export_to_dataframe(doc=doc)
            page_no = table_item.prov[0].page_no if table_item.prov else 1
            
            tables.append(TableObject(
                caption=getattr(table_item, "caption", None),
                headers=df.columns.tolist(),
                rows=df.values.tolist(),
                bbox=self._map_bbox(page_no, table_item.prov[0].bbox if table_item.prov else None)
            ))

        return ExtractedDocument(
            doc_id=Path(path).stem,
            blocks=blocks,
            tables=tables,
            extraction_strategy_used="Strategy B (Docling)",
            total_pages=len(doc.pages) if hasattr(doc, 'pages') else 1
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