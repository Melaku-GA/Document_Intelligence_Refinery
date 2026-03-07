from pydantic import BaseModel, Field
from typing import List, Optional, Any
from enum import Enum


class OriginType(str, Enum):
    NATIVE_DIGITAL = "native_digital"
    SCANNED_IMAGE = "scanned_image"
    MIXED = "mixed"


class LayoutComplexity(str, Enum):
    SINGLE_COLUMN = "single_column"
    MULTI_COLUMN = "multi_column"
    TABLE_HEAVY = "table_heavy"
    MIXED = "mixed"


class BBox(BaseModel):
    page: int
    x0: float
    y0: float
    x1: float
    y1: float


class TextBlock(BaseModel):
    text: str
    bbox: BBox
    block_type: str


class TableObject(BaseModel):
    caption: Optional[str] = None
    headers: List[Any]  # Can be strings or integers
    rows: List[List[Any]]
    bbox: BBox


class DocumentProfile(BaseModel):
    doc_id: str
    origin_type: OriginType
    layout_complexity: LayoutComplexity
    language_code: str = "en"
    confidence_score: float = Field(default=0.95, ge=0, le=1)
    estimated_cost_tier: str  # "low", "medium", "high"
    selected_strategy: str  # "Strategy A", "Strategy B", "Strategy C"
    metadata: dict = {}


class LDU(BaseModel):
    content: str
    chunk_type: str
    page_refs: List[int]
    bounding_box: BBox
    token_count: int
    content_hash: str


class ExtractedDocument(BaseModel):
    doc_id: str
    blocks: List[TextBlock] = []
    tables: List[TableObject] = []
    extraction_strategy_used: str
    total_pages: int
    metadata: dict = {}


class SectionNode(BaseModel):
    title: str
    level: int  # 1 for Chapter, 2 for Sub-section
    page_start: int
    page_end: int
    summary: str  # 2-3 sentence LLM-generated summary
    entities: List[str] = []  # Key terms like "Revenue", "EBITDA", "Tax"
    children: List["SectionNode"] = []
    has_tables: bool = False
    has_figures: bool = False


SectionNode.update_forward_refs()


class PageIndex(BaseModel):
    doc_id: str
    root: List[SectionNode]
    total_pages: int


class ProvenanceChain(BaseModel):
    answer: str
    citations: List[dict]  # {doc: "CBE_Report.pdf", page: 42, bbox: [x0, y0, x1, y1], chunk_hash: "a1b2..."}
    confidence_score: float
    verification_status: str  # "Verified" | "Unverifiable"
