import json
import os
import time
from typing import List, Dict, Any
from google import genai
from google.genai import types
from src.utils.config import settings
from src.models.schemas import ExtractedDocument, SectionNode, PageIndex


class PageIndexer:
    """Builds hierarchical PageIndex trees for documents."""
    
    def __init__(self, model_id: str = "gemini-2.0-flash", max_retries: int = 3):
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model_id = model_id
        self.max_retries = max_retries

    def build_index(self, doc: ExtractedDocument) -> dict:
        """
        Generates a hierarchical PageIndex tree with LLM summaries.
        Falls back to heuristic-based indexing if API is unavailable.
        """
        # Prepare context from document
        context_snippet = self._prepare_context(doc)
        
        # Try LLM-based indexing with retries (only 1 retry to avoid rate limits)
        for attempt in range(1):
            try:
                prompt = f"""
                Analyze the following document structure and create a hierarchical Table of Contents (PageIndex).
                For each section, provide:
                - title: The section name
                - page_start: The first page of the section
                - summary: A one-sentence technical summary of the content
                - children: Any sub-sections (nested)

                Format the output as a strict JSON tree.
                Document Context:
                {context_snippet}
                """

                response = self.client.models.generate_content(
                    model=self.model_id,
                    contents=prompt,
                    config=types.GenerateContentConfig(response_mime_type="application/json")
                )
                
                tree = json.loads(response.text)
                self._save_tree(doc.doc_id, tree)
                return tree
                
            except Exception as e:
                error_str = str(e)
                if "RESOURCE_EXHAUSTED" in error_str or "429" in error_str:
                    print(f"Rate limited, using heuristic fallback.")
                    break
                else:
                    # For other errors, fall back to heuristic
                    print(f"Indexing error: {e}. Using heuristic fallback.")
                    break
        
        # Fallback: Create a simple heuristic-based index
        tree = self._create_heuristic_index(doc)
        self._save_tree(doc.doc_id, tree)
        return tree

    def _create_heuristic_index(self, doc: ExtractedDocument) -> dict:
        """Create a simple index based on document structure when API is unavailable."""
        sections = []
        current_section = {"title": "Document Start", "page_start": 1, "children": []}
        
        # Group blocks by page and identify headers
        for block in doc.blocks:
            page = block.bbox.page if block.bbox else 1
            text = block.text[:50] if block.text else ""
            
            # Heuristic: headers are usually shorter and have specific block types
            if block.block_type in ["header", "section_header", "heading"]:
                if current_section.get("title") != "Document Start":
                    sections.append(current_section)
                current_section = {
                    "title": text,
                    "page_start": page,
                    "children": []
                }
        
        # Add final section
        if current_section:
            sections.append(current_section)
        
        # If no sections found, create a default one
        if not sections:
            sections = [{"title": "Document Content", "page_start": 1, "children": []}]
        
        return {
            "sections": sections,
            "total_pages": doc.total_pages,
            "index_type": "heuristic_fallback"
        }

    def _prepare_context(self, doc: ExtractedDocument) -> str:
        # Only send headers and first lines of blocks to save tokens
        headers = []
        for b in doc.blocks:
            if b.bbox and b.block_type in ["header", "section_header", "heading"]:
                headers.append(f"Page {b.bbox.page}: {b.text[:100]}")
            elif b.bbox and b.block_type == "page_content":
                # Also include first line of page content
                headers.append(f"Page {b.bbox.page}: {b.text[:100]}")
                break  # Just first line per page
        
        return "\n".join(headers[:20])  # Limit to 20 entries

    def _save_tree(self, doc_id, tree):
        filename = os.path.splitext(doc_id)[0] if doc_id else "unknown"
        # Ensure the pageindex directory exists
        os.makedirs(".refinery/pageindex", exist_ok=True)
        path = f".refinery/pageindex/{filename}_tree.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(tree, f, indent=2, ensure_ascii=False)
