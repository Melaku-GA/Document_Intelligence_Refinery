# import base64
# import json
# from typing import List
# from src.models.schemas import ExtractedDocument, TextBlock, TableObject, BBox

# class VisionExtractor:
#     def __init__(self, model_name: str = "gemini-1.5-flash"):
#         self.model_name = model_name
#         # Using a specialized prompt to enforce the schema
#         self.system_prompt = """
#         You are an expert Document Intelligence Agent. 
#         Extract all text and tables from the provided document page.
#         Return ONLY a JSON object following this structure:
#         {
#           "blocks": [{"text": "...", "type": "paragraph/header", "bbox": [x0, y0, x1, y1]}],
#           "tables": [{"caption": "...", "headers": [], "rows": [[]], "bbox": [x0, y0, x1, y1]}]
#         }
#         Coordinates should be normalized 0-1000.
#         """

#     def extract_page(self, image_path: str, page_num: int) -> ExtractedDocument:
#         # 1. Encode Image
#         encoded_image = self._encode_image(image_path)
        
#         # 2. Call VLM (Generic wrapper for Gemini/OpenRouter)
#         response_json = self._call_vlm_api(encoded_image)
        
#         # 3. Parse into Pydantic
#         return self._map_to_schema(response_json, page_num)

#     def _map_to_schema(self, data: dict, page_num: int) -> ExtractedDocument:
#         blocks = [
#             TextBlock(
#                 text=b["text"],
#                 bbox=BBox(page=page_num, x0=b["bbox"][0], y0=b["bbox"][1], x1=b["bbox"][2], y1=b["bbox"][3]),
#                 block_type=b["type"]
#             ) for b in data.get("blocks", [])
#         ]
        
#         tables = [
#             TableObject(
#                 caption=t.get("caption"),
#                 headers=t["headers"],
#                 rows=t["rows"],
#                 bbox=BBox(page=page_num, x0=t["bbox"][0], y0=t["bbox"][1], x1=t["bbox"][2], y1=t["bbox"][3])
#             ) for t in data.get("tables", [])
#         ]
        
#         return ExtractedDocument(
#             doc_id="VLM_EXTRACT",
#             blocks=blocks,
#             tables=tables,
#             extraction_strategy_used="Strategy C (Vision)",
#             total_pages=1
#         )
# import os
# import pymupdf  # fitz
# from PIL import Image
# import io
# import google.generativeai as genai
# from src.utils.config import settings
# from src.models.schemas import ExtractedDocument, TextBlock, TableObject, BBox

# class VisionExtractor:
#     def __init__(self, model_name: str = "gemini-1.5-flash"):
#         # Configure Gemini
#         genai.configure(api_key=settings.gemini_api_key)
#         self.model = genai.GenerativeModel(model_name=model_name)
        
#         self.system_prompt = """
#         You are an expert Document Intelligence Agent. 
#         Extract all text and tables from the provided document image.
#         Return ONLY a JSON object following this structure:
#         {
#           "blocks": [{"text": "...", "type": "paragraph/header", "bbox": [ymin, xmin, ymax, xmax]}],
#           "tables": [{"caption": "...", "headers": [], "rows": [[]], "bbox": [ymin, xmin, ymax, xmax]}]
#         }
#         Coordinates MUST be normalized integers [0-1000].
#         """

#     def extract(self, pdf_path: str) -> ExtractedDocument:
#         """Processes the whole PDF via Vision (Page by Page)."""
#         all_blocks = []
#         all_tables = []
        
#         doc = pymupdf.open(pdf_path)
#         for page_num in range(len(doc)):
#             # 1. Convert PDF page to Image (High DPI for better OCR)
#             page = doc.load_page(page_num)
#             pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2)) # 2x Zoom for clarity
#             img = Image.open(io.BytesIO(pix.tobytes()))
            
#             # 2. Call VLM
#             response = self.model.generate_content([self.system_prompt, img])
            
#             # 3. Clean and Parse JSON
#             try:
#                 # Remove markdown code blocks if the LLM includes them
#                 json_str = response.text.replace("```json", "").replace("```", "").strip()
#                 data = json.loads(json_str)
                
#                 # 4. Map to Schema
#                 page_data = self._map_to_schema(data, page_num + 1)
#                 all_blocks.extend(page_data.blocks)
#                 all_tables.extend(page_data.tables)
#             except Exception as e:
#                 print(f"Vision error on page {page_num+1}: {e}")

#         doc.close()
#         return ExtractedDocument(
#             doc_id=os.path.basename(pdf_path),
#             blocks=all_blocks,
#             tables=all_tables,
#             extraction_strategy_used="Strategy C (Vision)",
#             total_pages=len(doc)
#         )

#     def _map_to_schema(self, data: dict, page_num: int) -> ExtractedDocument:
#         blocks = [
#             TextBlock(
#                 text=b["text"],
#                 bbox=BBox(page=page_num, x0=b["bbox"][1], y0=b["bbox"][0], x1=b["bbox"][3], y1=b["bbox"][2]),
#                 block_type=b["type"]
#             ) for b in data.get("blocks", [])
#         ]
#         tables = [
#             TableObject(
#                 caption=t.get("caption"),
#                 headers=t["headers"],
#                 rows=t["rows"],
#                 bbox=BBox(page=page_num, x0=t["bbox"][1], y0=t["bbox"][0], x1=t["bbox"][3], y1=t["bbox"][2])
#             ) for t in data.get("tables", [])
#         ]
#         return ExtractedDocument(blocks=blocks, tables=tables, doc_id="temp", total_pages=1)


import os
import io
import json
import pymupdf  # fitz
from PIL import Image
from google import genai
from google.genai import types
from src.utils.config import settings
from src.models.schemas import ExtractedDocument, TextBlock, TableObject, BBox

class VisionExtractor:
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        # Initialize the new 2026 GenAI Client
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model_id = model_name
        
        self.system_prompt = """
        You are an expert Document Intelligence Agent. 
        Extract all text and tables from the provided document image.
        Return ONLY a JSON object following this structure:
        {
          "blocks": [{"text": "...", "type": "paragraph/header", "bbox": [ymin, xmin, ymax, xmax]}],
          "tables": [{"caption": "...", "headers": [], "rows": [[]], "bbox": [ymin, xmin, ymax, xmax]}]
        }
        Coordinates MUST be normalized integers [0-1000].
        """

    def extract(self, pdf_path: str) -> ExtractedDocument:
        all_blocks = []
        all_tables = []
        
        doc = pymupdf.open(pdf_path)
        for page_num in range(len(doc)):
            # 1. Convert PDF page to Image
            page = doc.load_page(page_num)
            pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2)) 
            img_bytes = pix.tobytes("png")
            
            # 2. Call the New GenAI Client
            # The new SDK handles PIL Images or bytes directly
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=[
                    self.system_prompt,
                    types.Part.from_bytes(data=img_bytes, mime_type="image/png")
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json" # Forces JSON output
                )
            )
            
            # 3. Parse and Map
            try:
                # The new SDK response.parsed is often cleaner, 
                # but we'll use response.text for explicit control
                data = json.loads(response.text)
                page_data = self._map_to_schema(data, page_num + 1)
                all_blocks.extend(page_data.blocks)
                all_tables.extend(page_data.tables)
            except Exception as e:
                print(f" Vision error on page {page_num+1}: {e}")

        doc.close()
        return ExtractedDocument(
            doc_id=os.path.basename(pdf_path),
            blocks=all_blocks,
            tables=all_tables,
            extraction_strategy_used="Strategy C (Vision Augmented)",
            total_pages=len(doc)
        )

    def _map_to_schema(self, data: dict, page_num: int) -> ExtractedDocument:
        blocks = [
            TextBlock(
                text=b["text"],
                bbox=BBox(page=page_num, x0=b["bbox"][1], y0=b["bbox"][0], x1=b["bbox"][3], y1=b["bbox"][2]),
                block_type=b["type"]
            ) for b in data.get("blocks", [])
        ]
        tables = [
            TableObject(
                caption=t.get("caption"),
                headers=t["headers"],
                rows=t["rows"],
                bbox=BBox(page=page_num, x0=t["bbox"][1], y0=t["bbox"][0], x1=t["bbox"][3], y1=t["bbox"][2])
            ) for t in data.get("tables", [])
        ]
        return ExtractedDocument(blocks=blocks, tables=tables, doc_id="tmp", total_pages=1)