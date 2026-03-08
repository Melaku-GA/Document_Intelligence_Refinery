import os
import logging
import sys

# Fix Unicode issues on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from src.agents.triage import TriageAgent
from src.agents.extractor import ExtractionRouter

# Setup minimal logging to see the "Escalation Guard" in action
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

def run_diagnostic(test_file="data/CBE ANNUAL REPORT 2023-24.pdf"):
    print("\n--- STARTING REFINERY DIAGNOSTIC ---")
    
    if not os.path.exists(test_file):
        print(f"❌ Error: {test_file} not found. Please place it in the data/ folder.")
        return

    # 1. Test Triage
    triage = TriageAgent()
    print(f"Step 1: Analyzing {test_file}...")
    profile = triage.analyze(test_file)
    print(f"   > Result: {profile.selected_strategy} ({profile.origin_type})")

    # 2. Test Router & Extraction
    router = ExtractionRouter()
    print(f"Step 2: Executing Extraction Strategy...")
    try:
        doc = router.process(test_file, profile)
        
        # 3. Verify Output
        print(f"\n--- ✅ DIAGNOSTIC COMPLETE ---")
        print(f"Document ID: {doc.doc_id}")
        print(f"Strategy Used: {doc.extraction_strategy_used}")
        print(f"Blocks Extracted: {len(doc.blocks)}")
        print(f"Tables Found: {len(doc.tables)}")
        
        if len(doc.blocks) > 0:
            print(f"Sample Text: {doc.blocks[0].text[:100]}...")
            
    except Exception as e:
        print(f" Extraction Failed: {str(e)}")

if __name__ == "__main__":
    run_diagnostic()