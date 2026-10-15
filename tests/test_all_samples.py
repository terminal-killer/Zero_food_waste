import os
import sys

# Configure UTF-8 for Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Ensure Python path includes the orchestrator
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../skills/annasetu-orchestrator/scripts")))
from orchestrate import run_annasetu_pipeline

def run_all_samples():
    sample_path = os.path.join(os.path.dirname(__file__), "../data/sample_listings.txt")
    with open(sample_path, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = content.split("LISTING_")
    samples = []
    for b in blocks:
        if b.strip():
            lines = b.strip().split("\n", 1)
            header = "LISTING_" + lines[0]
            body = lines[1].strip() if len(lines) > 1 else lines[0]
            samples.append((header, body))

    print(f"\n🚀 Running AnnaSetu Autonomous Verification across {len(samples)} Sample Listings...\n")

    results = []
    for idx, (header, text) in enumerate(samples, 1):
        print(f"\n>>>>>>>>>>>> RUNNING TEST CASE {idx}: {header} <<<<<<<<<<<<")
        res = run_annasetu_pipeline(text, record_ledger=True)
        results.append((header, res))

    print("\n" + "=" * 72)
    print(" 📋 TEST MATRIX SUMMARY & OUTCOMES")
    print("=" * 72)
    for header, res in results:
        status = res["status"]
        verdict = res["safety"]["verdict"] if res.get("safety") else ("NEEDS_INFO" if status == "NEEDS_INFO" else "N/A")
        donor = res["intake"].get("donor_name", "Pending Info")
        meals = res["intake"].get("total_quantity", 0)
        matches = res.get("matches")
        split = False
        if matches and matches.get("split_plan"):
            split = matches["split_plan"].get("required", False)
        
        split_str = " | SPLIT: 2 Shelters" if split else ""
        print(f"  • {header.split('(')[0].strip()}: Status=[{status}] Verdict=[{verdict}] Donor=[{donor}] Qty=[{meals} meals]{split_str}")
    print("=" * 72 + "\n")

if __name__ == "__main__":
    run_all_samples()
