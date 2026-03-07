import pdfplumber
from src.models.schemas import DocumentProfile, OriginType, LayoutComplexity

# class TriageAgent:
#     def analyze(self, path: str) -> DocumentProfile:
#         with pdfplumber.open(path) as pdf:
#             text = "".join([p.extract_text() or "" for p in pdf.pages])
#             char_count = len(text)
#             img_count = sum([len(p.images) for p in pdf.pages])
            
#         # Logic: If text is sparse but images exist, it's a scan.
#         origin = OriginType.SCANNED_IMAGE if char_count < 200 else OriginType.NATIVE_DIGITAL
#         strategy = "Strategy C" if origin == OriginType.SCANNED_IMAGE else "Strategy A"
        
#         return DocumentProfile(
#             doc_id=path.split("/")[-1],
#             origin_type=origin,
#             layout_complexity=LayoutComplexity.SINGLE_COLUMN,
#             selected_strategy=strategy,
#             estimated_cost_tier="low" if strategy == "Strategy A" else "high"
#         )

from typing import Dict, Any
from src.models.schemas import DocumentProfile, OriginType, LayoutComplexity

class TriageAgent:
    def __init__(self, high_image_threshold: float = 0.5, low_char_threshold: int = 100):
        self.high_image_threshold = high_image_threshold
        self.low_char_threshold = low_char_threshold

    def analyze(self, pdf_path: str) -> DocumentProfile:
        stats = self._get_pdf_stats(pdf_path)
        
        # 1. Determine Origin Type
        origin = self._detect_origin(stats)
        
        # 2. Determine Layout Complexity
        complexity = self._detect_complexity(stats)
        
        # 3. Strategy Routing Logic
        strategy = "Strategy A" # Default
        if origin == OriginType.SCANNED_IMAGE:
            strategy = "Strategy C"
        elif complexity != LayoutComplexity.SINGLE_COLUMN:
            strategy = "Strategy B"

        return DocumentProfile(
            doc_id=pdf_path.split("/")[-1],
            origin_type=origin,
            layout_complexity=complexity,
            confidence_score=0.95, # Heuristic confidence
            estimated_cost_tier="low" if strategy == "Strategy A" else "medium",
            selected_strategy=strategy,
            metadata=stats
        )

    def _get_pdf_stats(self, path: str) -> Dict[str, Any]:
        char_count = 0
        total_page_area = 0
        total_image_area = 0
        max_cols = 1

        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                char_count += len(page.chars)
                total_page_area += (page.width * page.height)
                
                # Calculate image density
                for img in page.images:
                    total_image_area += (img['width'] * img['height'])
                
                # Simple column heuristic: find vertical whitespace gaps
                vertical_gaps = page.vertical_edges
                if len(vertical_gaps) > 5: # Threshold for potential multi-column
                    max_cols = max(max_cols, 2)

        return {
            "char_density": char_count / (total_page_area / 10000), # chars per 10k points
            "image_ratio": total_image_area / total_page_area,
            "avg_chars_per_page": char_count / len(pdf.pages),
            "detected_cols": max_cols
        }

    def _detect_origin(self, stats: Dict) -> OriginType:
        if stats["avg_chars_per_page"] < self.low_char_threshold:
            return OriginType.SCANNED_IMAGE
        if stats["image_ratio"] > self.high_image_threshold:
            return OriginType.MIXED
        return OriginType.NATIVE_DIGITAL

    def _detect_complexity(self, stats: Dict) -> LayoutComplexity:
        if stats["detected_cols"] > 1:
            return LayoutComplexity.MULTI_COLUMN
        # Additional checks for table-heavy could go here
        return LayoutComplexity.SINGLE_COLUMN