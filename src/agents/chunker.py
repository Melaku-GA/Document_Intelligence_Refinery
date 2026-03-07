# from typing import List
# from src.models.schemas import ExtractedDocument, LDU, TableObject, TextBlock

# class ChunkValidator:
#     @staticmethod
#     def is_valid(chunk: LDU, max_tokens: int) -> bool:
#         # Rule: No chunk should be 'empty' or exceed token limit without reason
#         if chunk.token_count > max_tokens and chunk.chunk_type != "table":
#             return False
#         return True

# class ChunkingEngine:
#     def __init__(self, max_tokens: int = 512):
#         self.max_tokens = max_tokens
#         self.validator = ChunkValidator()

#     def create_chunks(self, doc: ExtractedDocument) -> List[LDU]:
#         chunks = []
        
#         # 1. Process Tables first (Atomic Units)
#         for table in doc.tables:
#             chunks.append(self._table_to_ldu(table))
            
#         # 2. Process Text Blocks with "Section Awareness"
#         current_section = "Introduction"
#         buffer = []
        
#         for block in doc.blocks:
#             if block.block_type == "header":
#                 # Flush buffer before starting new section
#                 if buffer:
#                     chunks.append(self._create_text_ldu(buffer, current_section))
#                     buffer = []
#                 current_section = block.text
            
#             buffer.append(block)
            
#             # Flush if buffer hits token limit
#             if self._estimate_tokens(buffer) >= self.max_tokens:
#                 chunks.append(self._create_text_ldu(buffer, current_section))
#                 buffer = []
                
#         return chunks

#     def _table_to_ldu(self, table: TableObject) -> LDU:
#         # Convert structured table to a readable string format for the LLM
#         table_str = f"Table: {table.caption}\n"
#         table_str += " | ".join(table.headers) + "\n"
#         for row in table.rows:
#             table_str += " | ".join(row) + "\n"
            
#         return LDU(
#             content=table_str,
#             chunk_type="table",
#             page_refs=[table.bbox.page],
#             bounding_box=table.bbox,
#             token_count=len(table_str.split()) # Rough estimate
#         )

# import hashlib
# from typing import List
# from src.models.schemas import ExtractedDocument, LDU, BBox

# class SemanticChunker:
#     """
#     Splits ExtractedDocument into LDUs based on semantic boundaries
#     and table structures, enforcing all 5 refinery rules.
#     """
#     def __init__(self, max_tokens: int = 512):
#         self.max_tokens = max_tokens

#     def chunk(self, doc: ExtractedDocument) -> List[LDU]:
#         chunks = []
        
#         # 1. Process Tables as Atomic Units (Rule: Never split tables)
#         for table in doc.tables:
#             table_text = f"Table: {table.caption}\nHeaders: {table.headers}\nData: {table.rows}"
#             chunks.append(self._create_ldu(table_text, "table", table.bbox))

#         # 2. Process Text Blocks (Rule: Semantic Header grouping)
#         for block in doc.blocks:
#             # Here we would normally use an LLM or heuristic to group headers with paragraphs
#             # For the refinery, we ensure each block keeps its provenance
#             chunks.append(self._create_ldu(block.text, block.block_type, block.bbox))

#         return chunks

#     def _create_ldu(self, text: str, chunk_type: str, bbox: BBox) -> LDU:
#         # Generate hash for Rule: Content Hash Deduplication
#         content_hash = hashlib.md5(text.encode()).hexdigest()
        
#         return LDU(
#             content=text,
#             chunk_type=chunk_type,
#             page_refs=[bbox.page],
#             bounding_box=bbox,
#             token_count=len(text.split()), # Simple proxy for tokens
#             content_hash=content_hash
#         )

import hashlib
import logging
from typing import List
from src.models.schemas import ExtractedDocument, LDU, BBox

class ChunkValidator:
    """Enforces the 5 Refinery Rules for Logical Document Units."""
    def __init__(self, max_tokens: int = 512):
        self.max_tokens = max_tokens
        self.seen_hashes = set()

    def validate(self, ldu: LDU) -> bool:
        # Rule 3: Token Ceiling
        if ldu.token_count > self.max_tokens:
            logging.warning(f"LDU exceeds token limit: {ldu.token_count}")
            return False
        
        # Rule 4: Provenance Link
        if not ldu.page_refs or ldu.bounding_box is None:
            logging.warning("LDU missing provenance data")
            return False

        # Rule 5: Content Hash Deduplication
        if ldu.content_hash in self.seen_hashes:
            return False # Duplicate found
            
        self.seen_hashes.add(ldu.content_hash)
        return True

class SemanticChunker:
    def __init__(self, max_tokens: int = 512):
        self.max_tokens = max_tokens
        self.validator = ChunkValidator(max_tokens=max_tokens)

    def chunk(self, doc: ExtractedDocument) -> List[LDU]:
        valid_chunks = []
        
        # Rule 1: Process Tables as Atomic Units (Never split)
        for table in doc.tables:
            table_text = f"Table: {table.caption}\nHeaders: {table.headers}\nData: {table.rows}"
            ldu = self._create_ldu(table_text, "table", table.bbox)
            if self.validator.validate(ldu):
                valid_chunks.append(ldu)

        # Rule 2: Semantic Header Grouping
        # We iterate through blocks, grouping headers with their body text
        current_text = ""
        current_bbox = None
        
        for block in doc.blocks:
            if block.block_type == "header" and current_text:
                # Flush previous group as an LDU
                ldu = self._create_ldu(current_text, "semantic_block", current_bbox)
                if self.validator.validate(ldu):
                    valid_chunks.append(ldu)
                current_text = ""

            current_text += f"\n{block.text}"
            current_bbox = block.bbox if not current_bbox else current_bbox

        # Flush final block
        if current_text:
            ldu = self._create_ldu(current_text, "semantic_block", current_bbox)
            if self.validator.validate(ldu):
                valid_chunks.append(ldu)

        return valid_chunks

    def _create_ldu(self, text: str, chunk_type: str, bbox: BBox) -> LDU:
        content_hash = hashlib.md5(text.encode()).hexdigest()
        # Using a simple split for token count; use tiktoken in production if needed
        token_count = len(text.split())
        
        return LDU(
            content=text.strip(),
            chunk_type=chunk_type,
            page_refs=[bbox.page] if bbox else [],
            bounding_box=bbox,
            token_count=token_count,
            content_hash=content_hash
        )