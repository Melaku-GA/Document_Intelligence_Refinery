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

        extractor = self.strategies.get(selected_key, self.strategies["Strategy A"])
        self.logger.info(f"Executing {selected_key} for {pdf_path}")

        # SAFE EXTRACTION EXECUTION
        try:
            result = extractor.extract(pdf_path)
        except Exception as e:
            self.logger.error(f"{selected_key} failed for {pdf_path}: {e}")
            self.logger.warning("Falling back to Strategy A (FastTextExtractor)")
            extractor = self.strategies["Strategy A"]
            result = extractor.extract(pdf_path)
            selected_key = "Strategy A (Fallback)"
            escalated = True

        # ESCALATION GUARDS
        # Strategy A -> B Escalation
        if selected_key == "Strategy A" and self._is_low_quality(result):
            try:
                self.logger.warning(f"Quality Gate Failed. Escalating Strategy A -> B for {pdf_path}")
                result = self.strategies["Strategy B"].extract(pdf_path)
                selected_key = "Strategy B (Escalated)"
                escalated = True
            except Exception as e:
                self.logger.error(f"Strategy B escalation failed: {e}")
                self.logger.warning("Continuing with Strategy A output")

        # Strategy B -> C Escalation
        elif selected_key == "Strategy B" and not result.tables and profile.layout_complexity == "table_heavy":
            try:
                self.logger.warning(f"Table Detection Failed. Escalating Strategy B -> C for {pdf_path}")
                result = self.strategies["Strategy C"].extract(pdf_path)
                selected_key = "Strategy C (Escalated)"
                escalated = True
            except Exception as e:
                self.logger.error(f"Strategy C escalation failed: {e}")
                self.logger.warning("Continuing with Strategy B output")

        # LEDGER LOGGING
        duration = round(time.time() - start_time, 2)
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
        if not doc.blocks:
            return True
        total_text = " ".join([b.text for b in doc.blocks])
        if len(total_text) < 50:
            return True
        special_chars = sum(1 for c in total_text if not c.isalnum() and not c.isspace())
        if special_chars / len(total_text) > 0.3:
            return True
        return False

    def _calculate_confidence(self, doc: ExtractedDocument) -> float:
        """Calculate confidence score based on extraction quality."""
        if not doc.blocks:
            return 0.0
        confidence = 0.5
        total_chars = sum(len(b.text) for b in doc.blocks)
        if total_chars > 1000:
            confidence += 0.2
        if doc.tables:
            confidence += 0.15
            confidence += min(0.1, len(doc.tables) * 0.02)
        total_text = " ".join([b.text for b in doc.blocks])
        if total_text:
            special_chars = sum(1 for c in total_text if not c.isalnum() and not c.isspace())
            quality_ratio = 1 - (special_chars / len(total_text))
            confidence += quality_ratio * 0.15
        return min(1.0, confidence)
