"""One-time converter: data/dashboard-2026.pdf → data/scorecards/schedule.json.

Run once:
    python3 scorecards/src/dashboard_to_schedule.py

Overwrites schedule.json. After that, use schedule_manager.py to edit entries.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "shared"))

from dashboard_parser import parse_dashboard
from datetime import date

SCHEDULE_PATH = ROOT / "data" / "scorecards" / "schedule.json"
DASHBOARD     = ROOT / "data" / "dashboard-2026.pdf"

EPOCH = date(2000, 1, 1)  # cutoff = all matches (no date filter)


def main():
    if not DASHBOARD.exists():
        print(f"[schedule] dashboard-2026.pdf not found at {DASHBOARD}")
        sys.exit(1)

    matches = parse_dashboard(DASHBOARD, cutoff_date=EPOCH)

    entries = []
    for i, m in enumerate(matches, start=1):
        entries.append({"id": i, **m})

    SCHEDULE_PATH.write_text(json.dumps(entries, indent=2))
    print(f"[schedule] Written {len(entries)} entries → {SCHEDULE_PATH}")


if __name__ == "__main__":
    main()
