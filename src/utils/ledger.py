import json
import os
from datetime import datetime

def log_to_ledger(entry: dict, ledger_path: str = ".refinery/extraction_ledger.jsonl"):
    """Appends a single processing record to the JSONL ledger."""
    os.makedirs(os.path.dirname(ledger_path), exist_ok=True)
    
    # Add a timestamp for auditability
    entry["timestamp"] = datetime.now().isoformat()
    
    with open(ledger_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")