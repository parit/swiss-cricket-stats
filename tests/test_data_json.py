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


def test_past_match_team_names_are_normalized():
    """SC team names in data.json past matches must be normalised (no GENEVA CC etc.)."""
    from utils import normalize_pt_team
    for t in _load()["tournaments"]:
        for m in t["past_matches"]:
            for key in ("team_1st", "team_2nd"):
                name = m.get(key, "")
                assert normalize_pt_team(name) == name, \
                    f"Un-normalized team name '{name}' in data.json past match ({t['name']})"


def test_no_switzerland_suffix_in_venues():
    """All Geneva venues must say 'Geneva' not 'Geneva (Switzerland)'."""
    for t in _load()["tournaments"]:
        for m in t["past_matches"] + t["upcoming_matches"]:
            ground = m.get("ground", "")
            assert "(Switzerland)" not in ground, \
                f"Venue still has '(Switzerland)' suffix: '{ground}'"


def test_abbreviations_populated():
    abbrevs = load_tournament_abbreviations(DATA / "tournament_abbreviations.tsv")
    for t in _load()["tournaments"]:
        norm = normalize_tournament(t["name"])
        assert t["abbreviation"] == abbrevs.get(norm, ""), \
            f"Abbreviation mismatch for {t['name']}"


# ---------------------------------------------------------------------------
# Schedule / manifest / registry consistency (moved from test_stats_html.py)
# ---------------------------------------------------------------------------

def _load_sc():
    return json.loads((TMP / "sc_manifest.json").read_text())

def _load_sched():
    return json.loads((DATA / "scorecards" / "schedule.json").read_text())

def _read_raw(path: Path) -> str:
    return path.read_text()


def test_schedule_contains_no_dbmt():
    for entry in _load_sched():
        assert 'DBMT' not in entry['tournament'], \
            f"DBMT entry found in schedule.json: {entry}"


def test_upcoming_matches_are_in_schedule():
    sc = _load_sc()
    sched_keys = {
        (e['date'], e['home_team'].lower(), e['away_team'].lower())
        for e in _load_sched()
    }
    for m in sc['upcoming']:
        key = (m['date'], m['home_team'].lower(), m['away_team'].lower())
        assert key in sched_keys, f"Upcoming match not in schedule.json: {m}"


def test_sc_past_matches_have_required_fields():
    required = {'tournament', 'date', 'team_1st', 'team_2nd', 'result'}
    for m in _load_sc()['past']:
        missing = required - m.keys()
        assert not missing, f"Past match missing {missing}: {m}"


def test_sc_upcoming_matches_have_required_fields():
    required = {'tournament', 'date', 'home_team', 'away_team', 'ground'}
    for m in _load_sc()['upcoming']:
        missing = required - m.keys()
        assert not missing, f"Upcoming match missing {missing}: {m}"


def test_teams_tsv_has_no_duplicate_ids():
    tsv = _read_raw(DATA / "teams.tsv")
    ids = [line.split('\t')[0] for line in tsv.splitlines()[1:] if line.strip()]
    assert len(ids) == len(set(ids)), "Duplicate IDs found in teams.tsv"


def test_teams_tsv_has_no_duplicate_names():
    tsv = _read_raw(DATA / "teams.tsv")
    names = [line.split('\t')[1] for line in tsv.splitlines()[1:] if '\t' in line]
    assert len(names) == len(set(names)), "Duplicate names found in teams.tsv"


def test_teams_tsv_no_case_variant_duplicates():
    tsv = _read_raw(DATA / "teams.tsv")
    names_lower = [line.split('\t')[1].lower() for line in tsv.splitlines()[1:] if '\t' in line]
    assert len(names_lower) == len(set(names_lower)), \
        "teams.tsv has entries that differ only in case"


def test_tournament_abbreviations_tsv_exists():
    assert (DATA / "tournament_abbreviations.tsv").exists()


def test_tournament_abbreviations_all_entries_have_values():
    tsv = _read_raw(DATA / "tournament_abbreviations.tsv")
    for i, line in enumerate(tsv.splitlines()[1:], start=2):
        parts = line.split('\t')
        assert len(parts) == 2 and parts[1].strip(), \
            f"tournament_abbreviations.tsv line {i} has no abbreviation: {repr(line)}"


def test_sc_manifest_past_matches_have_scorecard_id():
    manifest = json.loads((TMP / "sc_manifest.json").read_text())
    for m in manifest["past"]:
        assert "scorecard_id" in m, f"Missing scorecard_id in {m}"
        assert m["scorecard_id"].startswith("Scorecard_"), f"Bad scorecard_id: {m['scorecard_id']}"
