"""Parse all PDFs in data/points_table/ and write tmp/pt_manifest.json."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "shared"))

from extractor import extract
from parser import parse

DATA_DIR  = ROOT / "data" / "points_table"
DEBUG_DIR = ROOT / "tmp"


def run():
    pdfs = sorted(DATA_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"[pt] No PDFs found in {DATA_DIR}")
        return []

    print(f"[pt] Found {len(pdfs)} PDF(s)\n")
    tournaments = []
    for pdf in pdfs:
        print(f"--- {pdf.name} ---")
        img_path, title = extract(str(pdf), tmp_dir=str(DEBUG_DIR))
        if not title:
            title = pdf.stem.replace("_", " ").title()
        data = parse(img_path, debug_dir=str(DEBUG_DIR))
        json_path = DEBUG_DIR / f"{pdf.stem}.json"
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(data, indent=2))
        print(f"[pt] Parsed → {json_path.name}")
        tournaments.append((title, data))

    manifest = [{"title": t, "data": d} for t, d in tournaments]
    (DEBUG_DIR / "pt_manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"\n[pt] Manifest → tmp/pt_manifest.json")
    return tournaments


if __name__ == "__main__":
    run()
