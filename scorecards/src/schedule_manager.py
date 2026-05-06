"""CLI for managing data/scorecards/schedule.json.

Commands:
    python3 scorecards/src/schedule_manager.py list [--tournament T] [--date D]
    python3 scorecards/src/schedule_manager.py add --date D --time T --home H --away A --ground G --tournament N
    python3 scorecards/src/schedule_manager.py remove --id ID [--id ID ...]
"""
import argparse
import json
import sys
from pathlib import Path

ROOT          = Path(__file__).resolve().parents[2]
SCHEDULE_PATH = ROOT / "data" / "scorecards" / "schedule.json"


def load():
    if not SCHEDULE_PATH.exists():
        return []
    return json.loads(SCHEDULE_PATH.read_text())


def save(entries):
    SCHEDULE_PATH.write_text(json.dumps(entries, indent=2))


def next_id(entries):
    return max((e["id"] for e in entries), default=0) + 1


def cmd_list(args):
    entries = load()
    if args.tournament:
        q = args.tournament.lower()
        entries = [e for e in entries if q in e["tournament"].lower()]
    if args.date:
        entries = [e for e in entries if e["date"] == args.date]
    if not entries:
        print("No entries found.")
        return
    for e in entries:
        print(f"[{e['id']:>4}] {e['date']} {e.get('time','TBD'):<6}  "
              f"{e['home_team']} vs {e['away_team']}  |  {e['ground']}  |  {e['tournament']}")


def cmd_add(args):
    entries = load()
    entry = {
        "id":         next_id(entries),
        "tournament": args.tournament,
        "date":       args.date,
        "time":       args.time or "TBD",
        "ground":     args.ground,
        "home_team":  args.home,
        "away_team":  args.away,
    }
    entries.append(entry)
    entries.sort(key=lambda e: (e["date"], e.get("time", "")))
    save(entries)
    print(f"[schedule] Added id={entry['id']}: {entry['date']} {entry['home_team']} vs {entry['away_team']}")


def cmd_remove(args):
    entries = load()
    ids = set(args.id)
    kept    = [e for e in entries if e["id"] not in ids]
    removed = [e for e in entries if e["id"] in ids]
    if not removed:
        print(f"[schedule] No entries found with id(s): {ids}")
        return
    save(kept)
    for e in removed:
        print(f"[schedule] Removed id={e['id']}: {e['date']} {e['home_team']} vs {e['away_team']}")


def main():
    p = argparse.ArgumentParser(description="Manage schedule.json")
    sub = p.add_subparsers(dest="command", required=True)

    ls = sub.add_parser("list", help="List schedule entries")
    ls.add_argument("--tournament", help="Filter by tournament (substring match)")
    ls.add_argument("--date",       help="Filter by date (YYYY-MM-DD)")

    add = sub.add_parser("add", help="Add a match to the schedule")
    add.add_argument("--date",       required=True, help="YYYY-MM-DD")
    add.add_argument("--time",       default="TBD", help="HH:MM (24h) or TBD")
    add.add_argument("--home",       required=True, help="Home team name")
    add.add_argument("--away",       required=True, help="Away team name")
    add.add_argument("--ground",     required=True, help="Ground name")
    add.add_argument("--tournament", required=True, help="Full tournament name")

    rm = sub.add_parser("remove", help="Remove entry/entries by id")
    rm.add_argument("--id", type=int, nargs="+", required=True, help="Entry id(s)")

    args = p.parse_args()
    {"list": cmd_list, "add": cmd_add, "remove": cmd_remove}[args.command](args)


if __name__ == "__main__":
    main()
