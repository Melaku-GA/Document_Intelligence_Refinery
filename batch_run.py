import os
import pandas as pd
from tqdm import tqdm
from main import process_corpus

def run_full_refinery(data_dir="data/"):
    files = [f for f in os.listdir(data_dir) if f.endswith(".pdf")]
    stats = []

    print(f"🚀 Starting Batch Process on {len(files)} documents...")
    
    # Progress bar makes for a great demo video!
    for filename in tqdm(files, desc="Refining Corpus", unit="doc"):
        path = os.path.join(data_dir, filename)
        try:
            # We modify your existing main logic slightly to return results
            profile, doc = process_corpus(path) 
            stats.append({
                "File": filename,
                "Strategy": profile.selected_strategy,
                "Blocks": len(doc.blocks),
                "Tables": len(doc.tables)
            })
        except Exception as e:
            print(f"❌ Failed {filename}: {e}")

    # Create a summary dashboard
    df = pd.DataFrame(stats)
    df.to_csv(".refinery/extraction_summary.csv", index=False)
    print("\n✅ Batch Complete! Summary saved to .refinery/extraction_summary.csv")
    print(df.groupby("Strategy").size())

if __name__ == "__main__":
    run_full_refinery()