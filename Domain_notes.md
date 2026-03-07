DOMAIN_NOTES.md (Template)1. Extraction Strategy Decision TreeThis logic governs your TriageAgent and ExtractionRouter.FeatureStrategy A (Fast)Strategy B (Layout)Strategy C (Vision)TriggerDigital + Single ColDigital + Tables/Multi-colScanned OR Low ConfidenceToolpdfplumberDocling / MinerUGemini-1.5-FlashCost< $0.001 / page~$0.01 / page (Compute)~$0.02 / page (API)SignalChar Density > 100Table Detect = TrueChar Density < 52. Failure Modes by Document ClassBased on the target corpus provided, here is where the "Refinery" will likely break and how we mitigate it:Class A: CBE Annual Report (Native Digital)Failure: Multi-column text flow. pypdf will read across columns (Left Col Line 1 -> Right Col Line 1), creating a word salad.Mitigation: Strategy B (Docling) to perform Layout Analysis and reconstruct the reading order correctly.Class B: DBE Audit Report (Scanned/Image)Failure: "The Ghost Page." Strategy A returns 0 characters. Strategy B might see shapes but fail to OCR the text.Mitigation: Forced escalation to Strategy C (VLM). We treat the page as a JPEG and ask the vision model to "Markdown-ify" the content.Class C: FTA Technical Report (Mixed Layout)Failure: Tables with "Invisible Borders." Standard OCR sees numbers floating in space and loses the row-column relationship.Mitigation: Strategy B's Table Recognition models. We extract the table as a TableObject Pydantic model to preserve headers.Class D: Ethiopia Import Tax (Table-Heavy)Failure: Tables spanning multiple pages. The header is on page 4, but the data continues on page 5.Mitigation: The PageIndex must track "Open Tables" across page boundaries to merge them before chunking.3. Pipeline Diagram (Mermaid)Code snippetgraph TD
    A[Input PDF] --> B{Triage Agent}
    B -- "Digital/Simple" --> C[Strategy A: FastText]
    B -- "Digital/Complex" --> D[Strategy B: Docling]
    B -- "Scanned/Poor" --> E[Strategy C: VLM]
    
    C --> F{Confidence < 0.7?}
    F -- Yes --> D
    D --> G{Confidence < 0.5?}
    G -- Yes --> E
    
    C & D & E --> H[Normalized ExtractedDocument]
    H --> I[Semantic Chunker]
    I --> J[PageIndex Builder]
    J --> K[(Vector + SQL Store)]
4. The "Master Thinker" Insight: The VLM Decision BoundaryAs an FDE, you must explain to the client why we don't use GPT-4o for everything:Latency: A 500-page report would take 10+ minutes via VLM vs. 30 seconds via Docling.Tokens: Extracting every word via VLM is an inefficient use of the model's "reasoning" capabilities.The Hybrid Approach: Use Strategy B to get the text, and only send the Bounding Box of a messy table to Strategy C for "cleaning."


# 🇪🇹 Domain Intelligence Notes: The Ethiopian Financial Corpus
**Project:** Document Intelligence Refinery 
**Author:** 

---

## 1. Corpus Characterization
The target corpus consists of 50 documents from key Ethiopian institutions (CBE, DBE, Ministry of Finance, etc.). These documents present a "High Entropy" challenge due to four distinct document classes:

| Class | Document Type | Key Challenge |
| :--- | :--- | :--- |
| **Class A** | Modern Digital PDFs (e.g., 2024 CBE Report) | Native text layer exists but layout is multi-column. |
| **Class B** | Semi-Structured Reports (e.g., CPI March 2025) | Heavy reliance on nested tables and statistical grids. |
| **Class C** | Legacy Scanned Records (e.g., Older Audit Reports) | No text layer; requires Neural OCR/Vision. |
| **Class D** | "Invisible" Tables (e.g., Tax Expenditure Reports) | Tables without vector borders; text collapses in standard parsers. |

---

## 2. Why a 3-Strategy Approach?

### Strategy A: FastText (pdfplumber)
* **Purpose:** Cost-efficiency for Class A.
* **Logic:** If the document has a high character-to-image ratio and simple layout, we extract directly from the PDF stream. 
* **Benefit:** Zero API latency and 100% character accuracy for digital text.

### Strategy B: Layout-Aware (Docling)
* **Purpose:** Structural Integrity for Class B & D.
* **Logic:** Standard tools "flatten" multi-column Ethiopian reports into a jumbled mess. Docling uses layout models to identify headers and "re-thread" columns into the correct reading order.
* **Benefit:** Preserves "Table Atomicity"—ensuring rows stay with their headers.

### Strategy C: Vision-Augmented (Gemini 1.5 Flash)
* **Purpose:** Content Recovery for Class C.
* **Logic:** For scanned Ethiopian government documents with stamps and signatures, we rasterize pages to 300 DPI.
* **Benefit:** Spatial reasoning allows the model to "see" that a handwritten signature or a stamped date belongs to a specific audit finding.

---

## 3. The "Refinery" Innovation: The Escalation Guard
The core innovation of this refinery is the **Autonomous Escalation Guard** in `src/agents/extractor.py`. 
1. The system starts with the cheapest strategy. 
2. It performs a **Gibberish Check** (Mojibake detection).
3. If the quality score falls below 70%, it automatically re-extracts using a higher-tier strategy.

---

## 4. Key Metrics for Sunday
* **Provenance:** Every fact is mapped to a `[Page, x0, y0, x1, y1]` coordinate.
* **Fidelity:** 95%+ accuracy across the 50-document corpus.
* **Auditability:** A full `extraction_ledger.jsonl` tracks every decision made by the router.