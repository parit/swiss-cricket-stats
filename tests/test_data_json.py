"""Tests for output/2026/data.json structure and completeness."""
import json
import sys
from pathlib import Path

ROOT   = Path(__file__).parent.parent
OUTPUT = ROOT / "output" / "2026"
TMP    = ROOT / "tmp"
DATA   = ROOT / "data"

sys.path.insert(0, str(ROOT / "shared"))
from utils import normalize_tournament, load_tournament_abbreviations, title_to_folder


def _load():
    path = OUTPUT / "data.json"
    assert path.exists(), "output/2026/data.json missing — run build.py first"
    return json.loads(path.read_text())


def test_top_level_keys():
    d = _load()
    for key in ("season", "generated", "tournaments", "teams"):
        assert key in d, f"Missing top-level key: {key}"


def test_season_value():
    assert _load()["season"] == "2026"


def test_every_tournament_has_required_fields():
    for t in _load()["tournaments"]:
        for field in ("name", "abbreviation", "color", "slug", "past_matches", "upcoming_matches"):
            assert field in t, f"Tournament missing field '{field}': {t.get('name')}"


def test_tournament_slugs_match_title_to_folder():
    for t in _load()["tournaments"]:
        expected = title_to_folder(normalize_tournament(t["name"]))
        assert t["slug"] == expected, \
            f"Slug mismatch for '{t['name']}': got {t['slug']}, expected {expected}"


def test_past_match_fields():
    required = {"date", "ground", "team_1st", "score_1st", "team_2nd", "score_2nd", "result"}
    for t in _load()["tournaments"]:
        for m in t["past_matches"]:
            missing = required - m.keys()
            assert not missing, f"Past match missing {missing} in {t['name']}"


def test_upcoming_match_fields():
    required = {"date", "time", "ground", "home_team", "away_team"}
    for t in _load()["tournaments"]:
        for m in t["upcoming_matches"]:
            missing = required - m.keys()
            assert not missing, f"Upcoming match missing {missing} in {t['name']}"


def test_team_registry_present():
    teams = _load()["teams"]
    assert len(teams) > 0
    for team in teams:
        assert "id" in team and "name" in team


def test_all_sc_past_matches_in_data_json():
    """Every past match in sc_manifest must appear in data.json."""
    sc = json.loads((TMP / "sc_manifest.json").read_text())
    data = _load()
    data_past = [
        (t["slug"], m["date"], m["team_1st"].lower(), m["team_2nd"].lower())
        for t in data["tournaments"]
        for m in t["past_matches"]
    ]
    data_past_set = set(data_past)
    for m in sc["past"]:
        slug = title_to_folder(normalize_tournament(m["tournament"]))
        key = (slug, m["date"][:10], m["team_1st"].lower(), m["team_2nd"].lower())
        assert key in data_past_set, f"Past match missing from data.json: {m}"


def test_abbreviations_populated():
    abbrevs = load_tournament_abbreviations(DATA / "tournament_abbreviations.tsv")
    for t in _load()["tournaments"]:
        norm = normalize_tournament(t["name"])
        assert t["abbreviation"] == abbrevs.get(norm, ""), \
            f"Abbreviation mismatch for {t['name']}"
