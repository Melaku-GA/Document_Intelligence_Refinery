# 🇪🇹 Ethiopian Financial Corpus Refinery (TRPW3)

A high-fidelity AI pipeline designed to extract, index, and query complex financial reports from Ethiopian institutions (CBE, DBE, NBE). This system implements a multi-strategy extraction router, semantic chunking, and a LangGraph-powered Query Agent with full provenance tracking.

---

## 🚀 System Architecture

The Refinery operates in four distinct phases:
1. **Triage & Routing**: Analyzes document complexity and selects the optimal extraction strategy (FastText, Layout-Aware, or Vision-Augmented VLM).
2. **Refinement (Extraction)**: Structured extraction of text and tables with an automatic escalation guard.
3. **LDU Engineering**: Implements **Semantic Chunking** to create Metadata-Rich Logical Document Units (LDUs) while enforcing 5 refinery rules via `ChunkValidator`.
4. **Agentic Retrieval**: A **LangGraph** agent utilizing three specialized tools:
   - `pageindex_navigate`: Hierarchical navigation of document trees.
   - `semantic_search`: Vector-based retrieval from ChromaDB.
   - `structured_query`: SQL-based FactTable lookup for numerical precision.

---

## 📂 Repository Structure

- `src/agents/`: Core AI logic (Triage, Extractor, Chunker, Indexer, QueryAgent).
- `src/strategies/`: Implementation of extraction engines (A, B, and C).
- `src/models/`: Pydantic schemas for data integrity.
- `src/utils/`: Infrastructure for Vector Stores, FactTables, and Ledgers.
- `.refinery/`: **[Artifacts]** Generated PageIndex trees, profiles, and extraction data.
- `data/`: Input PDF corpus.

---

## 🛠️ Installation & Setup

### Prerequisites
- **Python 3.13** (Required for ChromaDB/Pydantic V1 compatibility).
- **Docker** (Recommended for isolated execution).

### Environment Variables
Create a `.env` file in the root directory:
```env
Setup: Add your GEMINI_API_KEY to a .env file.

Manual Installation
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows
pip install -r requirements.txt

Use Python 3.13.
Run python main.py to refine the corpus.
Run python app.py to launch the Q&A Demo.


Docker (Recommended):

Bash
docker build -t ethiopian-refinery .
docker run -p 7860:7860 --env-file .env ethiopian-refinery
Manual: