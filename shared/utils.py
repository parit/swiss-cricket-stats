import json
import re
from pathlib import Path

_NOISE = re.compile(r"\b(competitions|cup)\b", re.IGNORECASE)

_CORRECTIONS_PATH = Path(__file__).parent / "corrections.json"
_corrections: dict[str, str] | None = None


def _load_corrections() -> dict[str, str]:
    global _corrections
    if _corrections is None:
        _corrections = json.loads(_CORRECTIONS_PATH.read_text()) if _CORRECTIONS_PATH.exists() else {}
    return _corrections


def apply_corrections(text: str) -> str:
    for wrong, correct in _load_corrections().items():
        text = text.replace(wrong, correct)
    return text
_PT_TEAM_NORM: dict[str, str] = {
    "At Sports Club":        "A1 Sports Club",
    "Basel CC Juniors":      "Basel Juniors",
    "Basel CC- Colts":       "Basel CC Colts",
    "Basel Cricket Club":    "Basel CC",
    "CERN CC":               "Cern CC",
    "COSSONAY CC":           "Cossonay CC",
    "GENEVA CC":             "Geneva CC",
    "Nomads Embrach":        "Nomads-Embrach Cricket Academy",
    "Power WCC":             "Power Winterthur CC",
    "St Gallen CC":          "St. Gallen",
    "Zurich Crickets CC 1":  "Zurich Crickets CC-1",
    "Zurich Super Lions CC": "Zurich SuperLions",
}


def normalize_pt_team(name: str) -> str:
    return _PT_TEAM_NORM.get(name.strip(), name.strip())


_TOURN_NORM: dict[str, str] = {
    "CRICKET SWITZERLAND T20 U19":                     "CRICKET SWITZERLAND T20 U19 (League Matches)",
    "CRICKET SWITZERLAND WOMEN T10 LEAGUE 2026 (CSWL": "CRICKET SWITZERLAND WOMEN T10 LEAGUE 2026 (CSWL T10)",
}


def normalize_tournament(name: str) -> str:
    return _TOURN_NORM.get(name.strip(), name.strip())


_NONALNUM = re.compile(r"[^a-z0-9]+")
_MULTI_UNDERSCORE = re.compile(r"_+")


def load_tournament_abbreviations(tsv_path: Path) -> dict[str, str]:
    """Return {normalized_tournament_name: abbreviation} from tournament_abbreviations.tsv."""
    if not tsv_path.exists():
        return {}
    result = {}
    for line in tsv_path.read_text().splitlines()[1:]:  # skip header
        parts = line.split("\t", 1)
        if len(parts) == 2 and parts[1].strip():
            result[normalize_tournament(parts[0].strip())] = parts[1].strip()
    return result


def title_to_folder(title: str) -> str:
    t = _NOISE.sub("", title)
    t = _NONALNUM.sub("_", t.lower())
    t = _MULTI_UNDERSCORE.sub("_", t).strip("_")
    return t


# --- Team ID registry (data/teams.tsv) ---

def load_team_ids(tsv_path: Path) -> dict[str, str]:
    """Return {team_name: id} from teams.tsv. Creates empty mapping if missing."""
    if not tsv_path.exists():
        return {}
    lines = tsv_path.read_text().splitlines()
    result = {}
    for line in lines[1:]:  # skip header
        parts = line.split("\t", 1)
        if len(parts) == 2:
            result[parts[1]] = parts[0]
    return result


def save_team_ids(tsv_path: Path, mapping: dict[str, str]) -> None:
    """Write {team_name: id} to teams.tsv sorted by id."""
    rows = sorted(mapping.items(), key=lambda kv: kv[1])
    lines = ["id\tname"] + [f"{tid}\t{name}" for name, tid in rows]
    tsv_path.write_text("\n".join(lines) + "\n")


def assign_team_ids(teams: list[str], tsv_path: Path) -> dict[str, str]:
    """Load existing IDs, assign new ones for unknown teams, save and return {name: id}."""
    mapping = load_team_ids(tsv_path)
    new_teams = [t for t in teams if t not in mapping]
    if new_teams:
        next_num = max((int(v) for v in mapping.values()), default=0) + 1
        for team in sorted(new_teams):
            mapping[team] = f"{next_num:03d}"
            next_num += 1
        save_team_ids(tsv_path, mapping)
        print(f"[teams] Assigned {len(new_teams)} new id(s) → {tsv_path.name}")
    return mapping
