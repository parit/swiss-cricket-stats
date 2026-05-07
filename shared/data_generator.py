"""Generate output/<season>/data.json — all data needed by the web component."""
import hashlib
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.parent

import sys
sys.path.insert(0, str(ROOT / "shared"))
from utils import (normalize_tournament, normalize_pt_team, title_to_folder,
                   load_team_ids, load_tournament_abbreviations)

_ABBREV_PATH = ROOT / "data" / "tournament_abbreviations.tsv"
_TEAMS_TSV   = ROOT / "data" / "teams.tsv"

_PALETTE = [
    "#3498db", "#e74c3c", "#2ecc71", "#f39c12",
    "#9b59b6", "#1abc9c", "#e67e22", "#e91e63",
    "#607d8b", "#795548", "#00bcd4",
]


def _tourn_color(name: str) -> str:
    h = int(hashlib.md5(name.encode()).hexdigest(), 16)
    return _PALETTE[h % len(_PALETTE)]


def _normalize_pt_rows(data: dict) -> dict:
    """Apply normalize_pt_team() to 'Team' field in all PT rows."""
    return {
        group: [{**row, "Team": normalize_pt_team(row.get("Team", ""))} for row in rows]
        for group, rows in data.items()
    }


def generate_data_json(pt_manifest: list, sc_manifest: dict, out_dir: str) -> str:
    """Merge PT and SC manifests into a single data.json for the web component."""
    abbrevs  = load_tournament_abbreviations(_ABBREV_PATH)
    team_ids = load_team_ids(_TEAMS_TSV)

    pt_by_name: dict[str, dict] = {}
    for entry in pt_manifest:
        name = normalize_tournament(entry["title"])
        pt_by_name[name] = _normalize_pt_rows(entry["data"])

    past_by_name: dict[str, list] = {}
    for m in sc_manifest.get("past", []):
        name = normalize_tournament(m["tournament"])
        past_by_name.setdefault(name, []).append(m)

    upcoming_by_name: dict[str, list] = {}
    for m in sc_manifest.get("upcoming", []):
        name = normalize_tournament(m["tournament"])
        upcoming_by_name.setdefault(name, []).append(m)

    all_names = sorted(
        set(pt_by_name) | set(past_by_name) | set(upcoming_by_name)
    )

    tournaments = []
    for name in all_names:
        slug = title_to_folder(name)
        past = [
            {k: v for k, v in m.items() if k != "tournament"}
            for m in past_by_name.get(name, [])
        ]
        upcoming = [
            {k: v for k, v in m.items() if k != "tournament"}
            for m in upcoming_by_name.get(name, [])
        ]
        tournaments.append({
            "name":             name,
            "abbreviation":     abbrevs.get(name, ""),
            "color":            _tourn_color(name),
            "slug":             slug,
            "points_table":     pt_by_name.get(name, {}),
            "past_matches":     past,
            "upcoming_matches": upcoming,
        })

    teams = [{"id": tid, "name": name} for name, tid in sorted(team_ids.items())]

    data = {
        "season":      Path(out_dir).name,
        "generated":   str(date.today()),
        "tournaments": tournaments,
        "teams":       teams,
    }

    out_path = Path(out_dir) / "data.json"
    out_path.write_text(json.dumps(data, indent=2))
    print(f"[data] → {out_path}")
    return str(out_path)
