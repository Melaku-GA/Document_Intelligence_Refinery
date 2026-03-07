from src.strategies.layout_aware import LayoutExtractor

#class ExtractionRouter:
    #def __init__(self):
     #   self.strategies = {
     #       "Strategy A": FastTextExtractor(), # Basic pdfplumber
    #        "Strategy B": LayoutExtractor(),   # Docling
    #        "Strategy C": VisionExtractor()    # VLM
    #    }
    # ... (rest of the routing logic stays the same)

import logging
from typing import Protocol
from src.models.schemas import DocumentProfile, ExtractedDocument, OriginType
# Assume these are implemented in src/strategies/
from src.strategies.fast_text import FastTextExtractor
from src.strategies.layout_aware import LayoutExtractor
from src.strategies.vision_augmented import VisionExtractor
import time
from src.utils.ledger import log_to_ledger

# class ExtractorStrategy(Protocol):
#     def extract(self, path: str) -> ExtractedDocument:
#         ...

# #class ExtractionRouter:
# #    def __init__(self, config_path: str = "rubric/extraction_rules.yaml"):
# #        self.logger = logging.getLogger("Refinery.Extractor")
# #        self.strategies = {
# #            "Strategy A": FastTextExtractor(),
# #            "Strategy B": LayoutExtractor(),
# #            "Strategy C": VisionExtractor()
# #        }
# class ExtractionRouter:
#     def __init__(self):
#         self.strategies = {
#             "Strategy A": FastTextExtractor(), # Basic pdfplumber
#             "Strategy B": LayoutExtractor(),   # Docling
#             "Strategy C": VisionExtractor()    # VLM
#         }

#     def process(self, pdf_path: str, profile: DocumentProfile) -> ExtractedDocument:
#         selected_key = profile.selected_strategy
#         extractor = self.strategies.get(selected_key, self.strategies["Strategy A"])
        
#         self.logger.info(f"Executing {selected_key} for {pdf_path}")
#         result = extractor.extract(pdf_path)

#         # --- THE ESCALATION GUARD ---
#         # If Strategy A was used but returned "Gibberish" or low density
#         if selected_key == "Strategy A" and self._is_low_quality(result):
#             self.logger.warning(f"Strategy A failed quality gate for {pdf_path}. Escalating to Strategy B.")
#             return self.strategies["Strategy B"].extract(pdf_path)

#         # If Strategy B failed (e.g., table extraction failed to find columns)
#         if selected_key == "Strategy B" and not result.tables and profile.layout_complexity == "table_heavy":
#             self.logger.warning(f"Strategy B failed to extract tables. Escalating to Strategy C (VLM).")
#             return self.strategies["Strategy C"].extract(pdf_path)

#         return result

#     def _is_low_quality(self, doc: ExtractedDocument) -> bool:
#         """Heuristic check for encoding errors or 'garbage' text."""
#         if not doc.blocks:
#             return True
        
#         total_text = " ".join([b.text for b in doc.blocks])
#         if len(total_text) < 50: # Arbitrary threshold for 'empty' digital pages
#             return True
            
#         # Check for Mojibake (encoding errors common in old PDFs)
#         # If more than 20% of chars are non-printable/weird
#         special_chars = sum(1 for c in total_text if not c.isalnum() and not c.isspace())
#         if special_chars / len(total_text) > 0.3:
#             return True
            
#         return False

# import logging
# from typing import Protocol
# from src.models.schemas import DocumentProfile, ExtractedDocument, OriginType
# # Assume these are implemented in src/strategies/
# from src.strategies.fast_text import FastTextExtractor
# from src.strategies.layout_aware import LayoutExtractor
# from src.strategies.vision_augmented import VisionExtractor
# import time
# from src.utils.ledger import log_to_ledger

# class ExtractorStrategy(Protocol):
#     """Protocol ensures all strategies have an 'extract' method."""
#     def extract(self, path: str) -> ExtractedDocument:
#         ...

# class ExtractionRouter:
#     def __init__(self):
#         self.logger = logging.getLogger("Refinery.Extractor")
#         # Initialize all three strategies for quick hand-offs
#         self.strategies = {
#             "Strategy A": FastTextExtractor(),
#             "Strategy B": LayoutExtractor(),
#             "Strategy C": VisionExtractor()
#         }

#     def process(self, pdf_path: str, profile: DocumentProfile) -> ExtractedDocument:
#         selected_key = profile.selected_strategy
#         extractor = self.strategies.get(selected_key, self.strategies["Strategy A"])
        
#         self.logger.info(f"Executing {selected_key} for {pdf_path}")
#         result = extractor.extract(pdf_path)

#         # --- THE ESCALATION GUARD ---
#         # 1. Check for 'Gibberish' or Empty Text in Strategy A
#         if selected_key == "Strategy A" and self._is_low_quality(result):
#             self.logger.warning(f"Strategy A failed quality gate for {pdf_path}. Escalating to Strategy B.")
#             return self.strategies["Strategy B"].extract(pdf_path)

#         # 2. Check for Table failure in Strategy B for complex docs
#         if selected_key == "Strategy B" and not result.tables and profile.layout_complexity == "table_heavy":
#             self.logger.warning(f"Strategy B failed to extract tables. Escalating to Strategy C (VLM).")
#             return self.strategies["Strategy C"].extract(pdf_path)

#         return result

#     def _is_low_quality(self, doc: ExtractedDocument) -> bool:
#         """Heuristic check for encoding errors or 'garbage' text."""
#         if not doc.blocks:
#             return True
        
#         total_text = " ".join([b.text for b in doc.blocks])
#         if len(total_text) < 50: 
#             return True
            
#         # Check for Mojibake/Special Characters (Common in old digital PDFs)
#         if len(total_text) > 0:
#             special_chars = sum(1 for c in total_text if not c.isalnum() and not c.isspace())
#             if special_chars / len(total_text) > 0.3:
#                 return True
            
#         return False

import logging
import time
from typing import Protocol
from src.models.schemas import DocumentProfile, ExtractedDocument
from src.strategies.fast_text import FastTextExtractor
from src.strategies.layout_aware import LayoutExtractor
from src.strategies.vision_augmented import VisionExtractor
from src.utils.ledger import log_to_ledger

class ExtractorStrategy(Protocol):
    def extract(self, path: str) -> ExtractedDocument:
        ...

class ExtractionRouter:
    def __init__(self):
        self.logger = logging.getLogger("Refinery.Extractor")
        self.strategies = {
            "Strategy A": FastTextExtractor(),
            "Strategy B": LayoutExtractor(),
            "Strategy C": VisionExtractor()
        }

    def process(self, pdf_path: str, profile: DocumentProfile) -> ExtractedDocument:
        start_time = time.time()
        selected_key = profile.selected_strategy
        escalated = False
        
        # Initial Attempt
        extractor = self.strategies.get(selected_key, self.strategies["Strategy A"])
        self.logger.info(f"Executing {selected_key} for {pdf_path}")
        result = extractor.extract(pdf_path)

        # --- THE ESCALATION GUARD ---
        
        # 1. Strategy A -> B Escalation (Quality Gate)
        if selected_key == "Strategy A" and self._is_low_quality(result):
            self.logger.warning(f"Quality Gate Failed. Escalating Strategy A -> B for {pdf_path}")
            result = self.strategies["Strategy B"].extract(pdf_path)
            selected_key = "Strategy B (Escalated)"
            escalated = True

        # 2. Strategy B -> C Escalation (Table Density Gate)
        elif selected_key == "Strategy B" and not result.tables and profile.layout_complexity == "table_heavy":
            self.logger.warning(f"Table Detection Failed. Escalating Strategy B -> C for {pdf_path}")
            result = self.strategies["Strategy C"].extract(pdf_path)
            selected_key = "Strategy C (Escalated)"
            escalated = True

        # --- RECORD TO LEDGER ---
        duration = round(time.time() - start_time, 2)
        
        # Calculate confidence score based on extraction quality
        confidence = self._calculate_confidence(result)
        
        log_to_ledger({
            "doc_id": result.doc_id,
            "original_intent": profile.selected_strategy,
            "final_execution": selected_key,
            "duration_sec": duration,
            "blocks": len(result.blocks),
            "tables": len(result.tables),
            "confidence_score": confidence,
            "escalated": escalated
        })

        return result

    def _is_low_quality(self, doc: ExtractedDocument) -> bool:
        if not doc.blocks: return True
        total_text = " ".join([b.text for b in doc.blocks])
        if len(total_text) < 50: return True
        
        # Mojibake check
        special_chars = sum(1 for c in total_text if not c.isalnum() and not c.isspace())
        if special_chars / len(total_text) > 0.3: return True
        return False

    def _calculate_confidence(self, doc: ExtractedDocument) -> float:
        """Calculate confidence score based on extraction quality."""
        if not doc.blocks:
            return 0.0
        
        # Base confidence
        confidence = 0.5
        
        # Factor 1: Content presence
        total_chars = sum(len(b.text) for b in doc.blocks)
        if total_chars > 1000:
            confidence += 0.2
        
        # Factor 2: Table extraction success
        if doc.tables:
            confidence += 0.15
            confidence += min(0.1, len(doc.tables) * 0.02)
        
        # Factor 3: Text quality (low mojibake)
        total_text = " ".join([b.text for b in doc.blocks])
        if total_text:
            special_chars = sum(1 for c in total_text if not c.isalnum() and not c.isspace())
            quality_ratio = 1 - (special_chars / len(total_text))
            confidence += quality_ratio * 0.15
        
        return min(1.0, confidence)