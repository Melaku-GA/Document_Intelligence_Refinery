# import os
# import json
# from src.agents.triage import TriageAgent


# def process_corpus(filepath="data/Consumer Price Index March 2025.pdf"):
#     triage = TriageAgent()

#     filename = os.path.basename(filepath)
#     profile = triage.analyze(filepath)

#     #Save Profile
#     name = os.path.splitext(filename)[0]
#     out_path = f".refinery/profiles/{name}.json"

#     with open(out_path, "w") as f:
#        f.write(profile.model_dump_json(indent=2))

#     print(f"✅ Profiled {filename} -> {profile.selected_strategy}")
 
# if __name__ == "__main__":
#    process_corpus()



# def process_corpus(directory="data"):
#     triage = TriageAgent()

#     for filename in os.listdir(directory):
#         if filename.endswith(".pdf"):
#             path = os.path.join(directory, filename)
#             profile = triage.analyze(path)

#             # Save Profile
#             os.makedirs(".refinery/profiles", exist_ok=True)
#             out_path = f".refinery/profiles/{filename}.json"

#             with open(out_path, "w") as f:
#                 f.write(profile.model_dump_json(indent=2))

#             print(f"✅ Profiled {filename} -> {profile.selected_strategy}")

# if __name__ == "__main__":
#     process_corpus()

# import os
# os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
# from src.agents.triage import TriageAgent
# from src.agents.extractor import ExtractionRouter

# def process_corpus(filepath="data/Consumer Price Index March 2025.pdf"):
#     # 1. Ensure output directories exist
#     os.makedirs(".refinery/profiles", exist_ok=True)
#     os.makedirs(".refinery/extractions", exist_ok=True)
    
#     # 2. Initialize Agents
#     triage = TriageAgent()
#     router = ExtractionRouter()

#     filename = os.path.basename(filepath)
#     name = os.path.splitext(filename)[0]

#     # --- STAGE 1: TRIAGE ---
#     print(f"🔍 Analyzing {filename}...")
#     profile = triage.analyze(filepath)
    
#     profile_path = f".refinery/profiles/{name}.json"
#     with open(profile_path, "w") as f:
#         f.write(profile.model_dump_json(indent=2))
#     print(f"✅ Profiled -> {profile.selected_strategy}")

#     # --- STAGE 2: EXTRACTION ---
#     print(f"⚙️  Executing {profile.selected_strategy}...")
#     extracted_doc = router.process(filepath, profile)
    
#     extraction_path = f".refinery/extractions/{name}_data.json"
#     with open(extraction_path, "w") as f:
#         f.write(extracted_doc.model_dump_json(indent=2))
    
#     print(f"🚀 Success! Data saved to {extraction_path}")
#     print(f"   Found {len(extracted_doc.blocks)} text blocks and {len(extracted_doc.tables)} tables.")

# if __name__ == "__main__":
#     # Note: Ensure the file actually exists in your data/ folder!
#     process_corpus()

# def process_all_data(folder_path="data/"):
#     for file in os.listdir(folder_path):
#         if file.endswith(".pdf"):
#             process_corpus(os.path.join(folder_path, file))


# import os
# # Silences symlink warnings on Windows
# os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# from src.agents.triage import TriageAgent
# from src.agents.extractor import ExtractionRouter
# from src.agents.chunker import SemanticChunker      # <--- New Phase 3 Agent
# from src.utils.vector_store import VectorStore      # <--- New Data Layer Tool

# def process_corpus(filepath="data/Consumer Price Index March 2025.pdf"):
#     # 1. Ensure all refinery directories exist
#     os.makedirs(".refinery/profiles", exist_ok=True)
#     os.makedirs(".refinery/extractions", exist_ok=True)
#     os.makedirs(".refinery/vector_db", exist_ok=True)

#     # 2. Initialize the full Agent stack
#     triage = TriageAgent()
#     router = ExtractionRouter()
#     chunker = SemanticChunker()
#     vstore = VectorStore()

#     filename = os.path.basename(filepath)
#     name = os.path.splitext(filename)[0]

#     # --- STAGE 1: TRIAGE ---
#     print(f"🔍 Analyzing {filename}...")
#     profile = triage.analyze(filepath)
    
#     with open(f".refinery/profiles/{name}.json", "w") as f:
#         f.write(profile.model_dump_json(indent=2))
#     print(f"✅ Profiled -> {profile.selected_strategy}")

#     # --- STAGE 2: EXTRACTION ---
#     print(f"⚙️  Executing Extraction...")
#     extracted_doc = router.process(filepath, profile)
    
#     with open(f".refinery/extractions/{name}_data.json", "w") as f:
#         f.write(extracted_doc.model_dump_json(indent=2))
#     print(f"✅ Extraction Complete: {len(extracted_doc.blocks)} blocks, {len(extracted_doc.tables)} tables.")

#     # --- STAGE 3: SEMANTIC CHUNKING (Phase 3) ---
#     print(f"✂️  Chunking into Logical Document Units (LDUs)...")
#     ldus = chunker.chunk(extracted_doc)
#     print(f"✅ Created {len(ldus)} LDUs.")

#     # --- STAGE 4: VECTOR INGESTION (Data Layer) ---
#     print(f"📦 Ingesting into Vector Store (ChromaDB)...")
#     vstore.ingest_ldus(ldus, doc_id=filename)
    
#     print(f"🚀 SUCCESS: {filename} is now indexed and searchable!")
#     return profile, extracted_doc

# if __name__ == "__main__":
#     # Check if the data folder is ready
#     if not os.path.exists("data/"):
#         print("❌ Error: 'data/' folder not found. Create it and add your PDFs.")
#     else:
#         process_corpus()

import os
# Silences symlink warnings on Windows
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

from src.agents.triage import TriageAgent
from src.agents.extractor import ExtractionRouter
from src.agents.chunker import SemanticChunker
from src.agents.indexer import PageIndexer           # <--- New Phase 4 Agent
from src.utils.vector_store import VectorStore

def process_corpus(filepath):
    # 1. Ensure all refinery directories exist
    os.makedirs(".refinery/profiles", exist_ok=True)
    os.makedirs(".refinery/extractions", exist_ok=True)
    os.makedirs(".refinery/vector_db", exist_ok=True)
    os.makedirs(".refinery/pageindex", exist_ok=True) # <--- For Tree Artifacts

    # 2. Initialize the full Agent stack
    triage = TriageAgent()
    router = ExtractionRouter()
    chunker = SemanticChunker()
    indexer = PageIndexer()
    vstore = VectorStore()

    filename = os.path.basename(filepath)
    name = os.path.splitext(filename)[0]

    # --- STAGE 1: TRIAGE ---
    print(f"\n[1] Analyzing {filename}...")
    profile = triage.analyze(filepath)
    
    with open(f".refinery/profiles/{name}.json", "w") as f:
        f.write(profile.model_dump_json(indent=2))
    print(f"[OK] Profiled -> {profile.selected_strategy}")

    # --- STAGE 2: EXTRACTION ---
    print(f"[2] Executing Extraction...")
    extracted_doc = router.process(filepath, profile)
    
    with open(f".refinery/extractions/{name}_data.json", "w") as f:
        f.write(extracted_doc.model_dump_json(indent=2))
    print(f"[OK] Extracted: {len(extracted_doc.blocks)} blocks, {len(extracted_doc.tables)} tables.")

    # --- STAGE 3: SEMANTIC CHUNKING ---
    print(f"[3] Chunking into LDUs...")
    ldus = chunker.chunk(extracted_doc)
    
    # --- STAGE 4: VECTOR INGESTION ---
    vstore.ingest_ldus(ldus, doc_id=filename)
    print(f"[OK] Ingested {len(ldus)} chunks into VectorStore.")

    # --- STAGE 5: PAGEINDEX TREE (Requirement: Artifacts) ---
    print(f"[4] Building PageIndex Tree...")
    tree = indexer.build_index(extracted_doc)
    print(f"[OK] Tree saved to .refinery/pageindex/{name}_tree.json")
    
    print(f"SUCCESS: {filename} refined.")
    return profile, extracted_doc

def run_batch(limit=12):
    """Processes multiple files to meet the Sunday artifact quota."""
    data_dir = "data/"
    if not os.path.exists(data_dir):
        print("Error: 'data/' folder not found.")
        return

    files = [f for f in os.listdir(data_dir) if f.endswith(".pdf")][:limit]
    print(f"Found {len(files)} files. Starting batch refinery...")
    
    for f in files:
        try:
            process_corpus(os.path.join(data_dir, f))
        except Exception as e:
            print(f"Failed to process {f}: {e}")

if __name__ == "__main__":
    # Set to True to process the whole folder at once
    DO_BATCH = True 
    
    if DO_BATCH:
        run_batch(limit=12)
    else:
        # Process a single specific file
        process_corpus("data/Consumer Price Index March 2025.pdf")