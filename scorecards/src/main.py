"""Parse all PDFs in data/scorecards/ and write tmp/sc_manifest.json.

Past matches  = successfully parsed scorecard PDFs.
Upcoming matches = schedule.json entries with no matching scorecard.
"""
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "shared"))

from parser import parse
from utils import normalize_tournament, title_to_folder

DATA_DIR      = ROOT / "data" / "scorecards"
SCHEDULE_PATH = DATA_DIR / "schedule.json"
DEBUG_DIR     = ROOT / "tmp"


def _match_key(date, team1, team2, tournament):
    return (date, frozenset([team1.strip().lower(), team2.strip().lower()]), normalize_tournament(tournament))


def _upcoming(schedule, sc_past):
    """Return schedule entries that have no matching parsed scorecard."""
    past_keys = {
        _match_key(m["date"][:10], m["team_1st"], m["team_2nd"], m["tournament"])
        for m in sc_past
    }
    upcoming = []
    for entry in schedule:
        key = _match_key(
            entry["date"],
            entry["home_team"],
            entry["away_team"],
            entry["tournament"],
        )
        if key not in past_keys:
            upcoming.append({k: v for k, v in entry.items() if k != "id"})
    return upcoming


def sort_new_matches(data_dir: Path) -> None:
    """Parse PDFs in new-matches/, derive tournament slug, move to correct folder."""
    new_dir = data_dir / "new-matches"
    if not new_dir.exists():
        return
    pdfs = sorted(new_dir.glob("*.pdf"))
    if not pdfs:
        return
    print(f"[sort] {len(pdfs)} PDF(s) in new-matches/\n")
    for pdf in pdfs:
        match = parse(str(pdf), debug_dir=str(DEBUG_DIR))
        tournament = match.get("tournament", "")
        if not tournament:
            print(f"[sort] WARNING: no tournament found in {pdf.name} — left in new-matches/")
            continue
        slug = title_to_folder(normalize_tournament(tournament))
        dest_dir = data_dir / slug
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / pdf.name
        if dest.exists():
            print(f"[sort] SKIP {pdf.name} — already exists in {slug}/")
            continue
        shutil.move(str(pdf), str(dest))
        print(f"[sort] {pdf.name} → {slug}/\n")


def run():
    sort_new_matches(DATA_DIR)
    pdfs = sorted(p for p in DATA_DIR.rglob("*.pdf"))
    if not pdfs:
        print(f"[sc] No PDFs found in {DATA_DIR}")

    print(f"[sc] Found {len(pdfs)} PDF(s)\n")
    sc_past = []
    for pdf in pdfs:
        print(f"--- {pdf.name} ---")
        match = parse(str(pdf), debug_dir=str(DEBUG_DIR))
        match["scorecard_id"] = pdf.stem
        json_path = DEBUG_DIR / f"{pdf.stem}_sc.json"
        json_path.write_text(json.dumps(match, indent=2))
        print(f"[sc] Parsed → {json_path.name}")
        sc_past.append(match)

    schedule = json.loads(SCHEDULE_PATH.read_text()) if SCHEDULE_PATH.exists() else []
    if not schedule:
        print("[sc] schedule.json missing — run dashboard_to_schedule.py first")

    upcoming = _upcoming(schedule, sc_past)
    print(f"\n[sc] Schedule: {len(schedule)} entries | past: {len(sc_past)} | upcoming: {len(upcoming)}")

    manifest = {"past": sc_past, "upcoming": upcoming}
    (DEBUG_DIR / "sc_manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"[sc] Manifest → tmp/sc_manifest.json")
    return manifest


if __name__ == "__main__":
    run()
