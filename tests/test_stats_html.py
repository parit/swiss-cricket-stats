"""QA tests for generated HTML output.

Validates structure, data completeness, and cross-file consistency of
output/ after a build. Run after `python3 build.py`:

    python3 -m pytest tests/test_stats_html.py -v

Grouped into five areas:
  1. Combined stats.html — structure and labels
  2. Combined stats.html — tournament completeness
  3. Per-tournament pages
  4. Per-team pages
  5. Schedule / manifest / registry consistency
"""
import json
import re
import sys
from pathlib import Path

ROOT     = Path(__file__).parent.parent
OUTPUT   = ROOT / "output" / "2026"
COMBINED = OUTPUT / "index.html"
TMP      = ROOT / "tmp"
DATA     = ROOT / "data"

sys.path.insert(0, str(ROOT / "shared"))
from utils import load_team_ids, title_to_folder, normalize_tournament


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read(path: Path) -> str:
    assert path.exists(), f"Missing file (run build.py first): {path}"
    return path.read_text()

def _sc_sections(html: str) -> list[str]:
    return re.findall(r'<section class="sc-section"[^>]*>(.*?)</section>', html, re.DOTALL)

def _pt_sections(html: str) -> list[str]:
    return re.findall(r'<section class="pt-section"[^>]*>.*?</section>', html, re.DOTALL)

def _option_values(html: str) -> list[str]:
    return re.findall(r'<option value="([^"]+)">', html)

def _load_sc():  return json.loads(_read(TMP / "sc_manifest.json"))
def _load_pt():  return json.loads(_read(TMP / "pt_manifest.json"))
def _load_sched(): return json.loads(_read(DATA / "scorecards" / "schedule.json"))
def _load_teams(): return load_team_ids(DATA / "teams.tsv")


# ---------------------------------------------------------------------------
# 1. Combined stats.html — structure and labels
# ---------------------------------------------------------------------------

def test_combined_exists():
    """output/stats.html must exist — indicates build completed."""
    assert (COMBINED).exists()


def test_combined_has_tournament_dropdown():
    """Combined page must have the tournament selector that drives tab sync."""
    assert 'id="stats-tournament-select"' in _read(COMBINED)


def test_combined_tab_says_matches_not_scorecards():
    """Tab label must read 'Matches'; 'Scorecards' is the old name."""
    html = _read(COMBINED)
    assert '>Matches<' in html
    assert '>Scorecards<' not in html


def test_combined_has_season_title():
    """Page title and h1 must include 'Season 2026'."""
    assert 'Season 2026' in _read(COMBINED)


def test_combined_pt_section_count_matches_manifest():
    """One pt-section per tournament in pt_manifest — no extras or missing."""
    html = _read(COMBINED)
    assert len(_pt_sections(html)) == len(_load_pt())


# ---------------------------------------------------------------------------
# 2. Combined stats.html — tournament completeness
# ---------------------------------------------------------------------------

def test_every_dropdown_option_has_at_least_one_section():
    """Every selectable tournament must have a pt-section, sc-section, or both.
    A tournament with a dropdown entry but no section would show a blank page."""
    html = _read(COMBINED)
    for slug in _option_values(html):
        assert f'id="pt-{slug}"' in html or f'id="sc-{slug}"' in html, \
            f"Dropdown option '{slug}' has no matching pt- or sc-section"


def test_every_sc_section_has_sc_controls():
    """Each sc-section must contain the view toggle and team filter controls."""
    html = _read(COMBINED)
    for i, section in enumerate(_sc_sections(html)):
        assert 'sc-controls' in section,    f"sc-section #{i} missing sc-controls"
        assert 'sc-team-filter' in section, f"sc-section #{i} missing team filter"


def test_every_sc_section_has_past_and_upcoming_headings():
    """Each sc-section must render both sub-sections even when one is empty."""
    html = _read(COMBINED)
    for i, section in enumerate(_sc_sections(html)):
        assert 'Past Matches'     in section, f"sc-section #{i} missing 'Past Matches'"
        assert 'Upcoming Matches' in section, f"sc-section #{i} missing 'Upcoming Matches'"


def test_no_dbmt_in_combined():
    """DBMT 2026 matches are intentionally excluded from all output."""
    assert 'DBMT' not in _read(COMBINED)


def test_combined_past_row_count_at_least_manifest_count():
    """Total <tr data-teams= rows in combined page must cover all past matches.
    Each past match produces one table row in its sc-section."""
    html = _read(COMBINED)
    sc = _load_sc()
    rows = re.findall(r'<tr data-teams=', html)
    assert len(rows) >= len(sc['past'])


def test_combined_has_upcoming_badges():
    """If upcoming matches exist they must render with the 'upcoming-badge' class."""
    sc = _load_sc()
    if sc['upcoming']:
        assert 'upcoming-badge' in _read(COMBINED)


# ---------------------------------------------------------------------------
# 3. Per-tournament pages — structure
# ---------------------------------------------------------------------------

def test_per_tournament_pages_exist_for_all_dropdown_options():
    """Every tournament in the combined dropdown must have its own stats.html."""
    html = _read(COMBINED)
    for slug in _option_values(html):
        page = OUTPUT / slug / "stats.html"
        assert page.exists(), f"Missing per-tournament page: output/{slug}/stats.html"


def test_per_tournament_has_season_back_link():
    """Per-tournament pages must have a ← Season 2026 link pointing to ../index.html."""
    html = _read(COMBINED)
    for slug in _option_values(html):
        page_html = _read(OUTPUT / slug / "stats.html")
        assert 'href="../index.html"' in page_html, \
            f"{slug}: missing season back-link (../index.html)"


def test_per_tournament_team_names_are_links():
    """Team names in per-tournament pages must be <a class=team-link> elements."""
    html = _read(COMBINED)
    for slug in _option_values(html):
        page_html = _read(OUTPUT / slug / "stats.html")
        if '<tr>' in page_html:  # has PT or SC table rows
            assert 'class="team-link"' in page_html, \
                f"{slug}: no team-link found"


def test_per_tournament_correct_asset_paths():
    """Per-tournament pages sit one level inside output/ → must use ../assets/."""
    html = _read(COMBINED)
    for slug in _option_values(html):
        page_html = _read(OUTPUT / slug / "stats.html")
        assert '../assets/style.css' in page_html, f"{slug}: wrong CSS path"
        assert '../assets/script.js'  in page_html, f"{slug}: wrong JS path"


def test_per_tournament_h1_contains_tournament_name():
    """Per-tournament page h1 must contain the tournament name."""
    pt = _load_pt()
    pt_by_slug = {title_to_folder(e['title']): e['title'] for e in pt}
    html = _read(COMBINED)
    for slug in _option_values(html):
        page_html = _read(OUTPUT / slug / "stats.html")
        if slug in pt_by_slug:
            assert pt_by_slug[slug] in page_html, \
                f"{slug}/stats.html: h1 missing tournament name '{pt_by_slug[slug]}'"


def test_per_tournament_tab_says_matches():
    """All per-tournament pages with a scorecards tab must label it 'Matches'."""
    html = _read(COMBINED)
    for slug in _option_values(html):
        page_html = _read(OUTPUT / slug / "stats.html")
        if 'data-tab="scorecards"' in page_html:
            assert '>Matches<' in page_html, \
                f"output/{slug}/stats.html: scorecards tab has wrong label"


def test_per_tournament_sc_tab_has_controls():
    """Per-tournament pages with a Matches tab must contain sc-controls."""
    html = _read(COMBINED)
    for slug in _option_values(html):
        page_html = _read(OUTPUT / slug / "stats.html")
        if 'id="tab-scorecards"' in page_html:
            assert 'sc-controls' in page_html, \
                f"output/{slug}/stats.html: Matches tab missing sc-controls"


def test_per_tournament_view_toggle_present_when_matches_tab_exists():
    """Tournaments with a Matches tab must have the List / Cards toggle."""
    html = _read(COMBINED)
    for slug in _option_values(html):
        page_html = _read(OUTPUT / slug / "stats.html")
        if 'id="tab-scorecards"' in page_html:
            assert 'data-view="list"'  in page_html, f"{slug}: missing List button"
            assert 'data-view="cards"' in page_html, f"{slug}: missing Cards button"


def test_per_tournament_pt_tab_present_when_pt_data_exists():
    """If a tournament has PT data its page must expose a Points Table tab."""
    pt = _load_pt()
    pt_slugs = {title_to_folder(e['title']) for e in pt}
    html = _read(COMBINED)
    for slug in _option_values(html):
        if slug in pt_slugs:
            page_html = _read(OUTPUT / slug / "stats.html")
            assert 'data-tab="points-table"' in page_html, \
                f"{slug}: missing Points Table tab despite PT data"


def test_per_tournament_pt_table_row_count():
    """Points table must render one row per team entry in the manifest."""
    pt = _load_pt()
    for entry in pt:
        slug = title_to_folder(entry['title'])
        page = OUTPUT / slug / "stats.html"
        if not page.exists():
            continue
        html = page.read_text()
        total_teams = sum(len(rows) for rows in entry['data'].values())
        # Each team produces one <tr> in the points table body
        tr_count = len(re.findall(r'<tr>', html))
        assert tr_count >= total_teams, \
            f"{slug}: {tr_count} <tr> elements, expected at least {total_teams} team rows"


def test_per_tournament_past_and_upcoming_counts():
    """Past row count and upcoming-badge count must match sc_manifest for the tournament."""
    sc = _load_sc()
    html = _read(COMBINED)
    for slug in _option_values(html):
        page_html = _read(OUTPUT / slug / "stats.html")
        if 'id="tab-scorecards"' not in page_html:
            continue
        # Derive tournament name from slug by scanning manifests
        tourn = next(
            (e['title'] for e in _load_pt() if title_to_folder(e['title']) == slug),
            None
        )
        if tourn is None:
            continue
        past_expected = sum(1 for m in sc['past']
            if title_to_folder(normalize_tournament(m['tournament'])) == slug)
        upcoming_expected = sum(1 for m in sc['upcoming']
            if title_to_folder(normalize_tournament(m['tournament'])) == slug)
        actual_rows   = len(re.findall(r'<tr data-teams=', page_html))
        actual_badges = page_html.count('upcoming-badge')
        assert actual_rows   == past_expected + upcoming_expected, \
            f"{slug}: expected {past_expected + upcoming_expected} match rows, got {actual_rows}"
        assert actual_badges == upcoming_expected, \
            f"{slug}: expected {upcoming_expected} upcoming-badge, got {actual_badges}"


# ---------------------------------------------------------------------------
# 4. Per-team pages — structure
# ---------------------------------------------------------------------------

def test_per_team_has_season_back_link():
    """Per-team pages must have a ← Season 2026 link pointing to ../../index.html."""
    for name, tid in _load_teams().items():
        page = OUTPUT / "teams" / tid / "index.html"
        if not page.exists():
            continue
        assert 'href="../../index.html"' in page.read_text(), \
            f"Team {tid} ({name}): missing season back-link (../../index.html)"


def test_per_team_pages_have_team_links():
    """Team pages must contain <a class=team-link> elements (opponent names are links)."""
    for name, tid in _load_teams().items():
        page = OUTPUT / "teams" / tid / "index.html"
        if not page.exists():
            continue
        html = page.read_text()
        if 'data-teams=' in html:
            assert 'class="team-link"' in html, \
                f"Team {tid} ({name}): has match rows but no team-link"


def test_per_team_pages_have_tournament_pill_links():
    """Team pages must have <a class=tourn-pill> linking to tournament pages."""
    for name, tid in _load_teams().items():
        page = OUTPUT / "teams" / tid / "index.html"
        if not page.exists():
            continue
        html = page.read_text()
        if 'tourn-pill' in html:
            assert 'href="../../' in html and 'stats.html' in html, \
                f"Team {tid} ({name}): tourn-pill not a valid link"


def test_per_team_pages_exist_for_all_registered_teams():
    """Every team in teams.tsv must have output/teams/<id>/index.html."""
    for name, tid in _load_teams().items():
        page = OUTPUT / "teams" / tid / "index.html"
        assert page.exists(), f"Missing team page for '{name}' (id={tid})"


def test_per_team_pages_have_correct_h1():
    """Team page h1 must exactly match the canonical name from teams.tsv."""
    for name, tid in _load_teams().items():
        page = OUTPUT / "teams" / tid / "index.html"
        if page.exists():
            assert f'<h1>{name}</h1>' in page.read_text(), \
                f"Team page {tid}: h1 does not match '{name}'"


def test_per_team_pages_have_correct_asset_paths():
    """Team pages sit two levels inside output/ (output/teams/<id>/) → ../../assets/.
    One level shallower than before since assets now live inside output/."""
    for name, tid in _load_teams().items():
        page = OUTPUT / "teams" / tid / "index.html"
        if not page.exists():
            continue
        html = page.read_text()
        assert '../../assets/style.css' in html, \
            f"Team page {tid}: wrong CSS path (must be ../../assets/style.css)"
        assert '../../assets/script.js' in html, \
            f"Team page {tid}: wrong JS path (must be ../../assets/script.js)"


def test_per_team_pages_label_scorecards_tab_matches():
    """Team pages that have a scorecards tab must label it 'Matches'."""
    for name, tid in _load_teams().items():
        page = OUTPUT / "teams" / tid / "index.html"
        if not page.exists():
            continue
        html = page.read_text()
        if 'data-tab="scorecards"' in html:
            assert '>Matches<' in html, \
                f"Team page {tid} ({name}): scorecards tab has wrong label"


def test_per_team_view_toggle_present_when_matches_tab_exists():
    """Team pages with a Matches tab must include the List / Cards toggle."""
    for name, tid in _load_teams().items():
        page = OUTPUT / "teams" / tid / "index.html"
        if not page.exists():
            continue
        html = page.read_text()
        if 'id="tab-scorecards"' in html:
            assert 'data-view="list"'  in html, f"Team {tid} ({name}): missing List button"
            assert 'data-view="cards"' in html, f"Team {tid} ({name}): missing Cards button"


def test_per_team_dirs_are_numeric_ids():
    """output/teams/ must contain only numeric-ID directories (no slug leftovers)."""
    teams_dir = OUTPUT / "teams"
    if teams_dir.exists():
        for d in teams_dir.iterdir():
            if d.is_dir():
                assert d.name.isdigit(), \
                    f"Non-numeric team directory: output/teams/{d.name}"


# ---------------------------------------------------------------------------
# 4b. Per-team pages — content correctness
# ---------------------------------------------------------------------------

def test_per_team_all_match_rows_include_team():
    """Every data-teams attribute in a team page must include that team.
    Catches filter bugs where another team's solo matches bleed in."""
    for name, tid in _load_teams().items():
        page = OUTPUT / "teams" / tid / "index.html"
        if not page.exists():
            continue
        html = page.read_text()
        for attr in re.findall(r'data-teams="([^"]+)"', html):
            teams_in_match = [t.strip().lower() for t in attr.split('|')]
            assert name.lower() in teams_in_match, \
                f"Team {tid} ({name}): match row found that doesn't include this team — '{attr}'"


def test_per_team_upcoming_badge_count_matches_manifest():
    """upcoming-badge count must equal the team's upcoming entry count in sc_manifest.
    Each upcoming card produces exactly one badge."""
    sc = _load_sc()
    for name, tid in _load_teams().items():
        page = OUTPUT / "teams" / tid / "index.html"
        if not page.exists():
            continue
        html = page.read_text()
        t = name.lower()
        expected = sum(1 for m in sc['upcoming']
            if m.get('home_team', '').lower() == t or m.get('away_team', '').lower() == t)
        actual = html.count('upcoming-badge')
        assert actual == expected, \
            f"Team {tid} ({name}): expected {expected} upcoming-badge, got {actual}"


def test_per_team_total_match_row_count_matches_manifest():
    """<tr data-teams= row count must equal past + upcoming for this team.
    Rows appear in the list-view table for both past and upcoming sections."""
    sc = _load_sc()
    for name, tid in _load_teams().items():
        page = OUTPUT / "teams" / tid / "index.html"
        if not page.exists():
            continue
        html = page.read_text()
        t = name.lower()
        past_count     = sum(1 for m in sc['past']
            if m['team_1st'].lower() == t or m['team_2nd'].lower() == t)
        upcoming_count = sum(1 for m in sc['upcoming']
            if m.get('home_team', '').lower() == t or m.get('away_team', '').lower() == t)
        expected_rows = past_count + upcoming_count
        actual_rows   = len(re.findall(r'<tr data-teams=', html))
        assert actual_rows == expected_rows, \
            f"Team {tid} ({name}): expected {expected_rows} rows " \
            f"(past={past_count} + upcoming={upcoming_count}), got {actual_rows}"


# ---------------------------------------------------------------------------
# 5. Schedule / manifest / registry consistency
# ---------------------------------------------------------------------------

def test_schedule_contains_no_dbmt():
    """DBMT 2026 entries must have been excluded at conversion time."""
    for entry in _load_sched():
        assert 'DBMT' not in entry['tournament'], \
            f"DBMT entry found in schedule.json: {entry}"


def test_upcoming_matches_are_in_schedule():
    """Every upcoming match in sc_manifest must trace back to schedule.json.
    Catches cases where schedule edits diverge from manifest generation."""
    sc = _load_sc()
    sched_keys = {
        (e['date'], e['home_team'].lower(), e['away_team'].lower())
        for e in _load_sched()
    }
    for m in sc['upcoming']:
        key = (m['date'], m['home_team'].lower(), m['away_team'].lower())
        assert key in sched_keys, f"Upcoming match not in schedule.json: {m}"


def test_past_matches_have_required_fields():
    """Each past match dict must contain all fields needed by the generator."""
    required = {'tournament', 'date', 'team_1st', 'team_2nd', 'result'}
    for m in _load_sc()['past']:
        missing = required - m.keys()
        assert not missing, f"Past match missing {missing}: {m}"


def test_upcoming_matches_have_required_fields():
    """Each upcoming match dict must contain all fields needed by the generator."""
    required = {'tournament', 'date', 'home_team', 'away_team', 'ground'}
    for m in _load_sc()['upcoming']:
        missing = required - m.keys()
        assert not missing, f"Upcoming match missing {missing}: {m}"


def test_teams_tsv_has_no_duplicate_ids():
    """Duplicate team IDs would cause one team's page to overwrite another's."""
    tsv = _read(DATA / "teams.tsv")
    ids = [line.split('\t')[0] for line in tsv.splitlines()[1:] if line.strip()]
    assert len(ids) == len(set(ids)), "Duplicate IDs found in teams.tsv"


def test_teams_tsv_has_no_duplicate_names():
    """Duplicate names would mean two different IDs point to the same team."""
    tsv = _read(DATA / "teams.tsv")
    names = [line.split('\t')[1] for line in tsv.splitlines()[1:] if '\t' in line]
    assert len(names) == len(set(names)), "Duplicate names found in teams.tsv"
