"""Tests for output/component/ web component files.

Validates structure of cricket-stats.js and component/index.html
after a build. Run after `python3 build.py`:

    python3 -m pytest tests/test_component.py -v

Areas:
  1. Output files exist
  2. Demo page structure
  3. JS component definition and attributes
  4. JS component features (views, navigation, rendering)
  5. data.json <-> component consistency
"""
import json
import re
import sys
from pathlib import Path

ROOT      = Path(__file__).parent.parent
OUTPUT    = ROOT / "output"
COMP_DIR  = OUTPUT / "component"
COMP_JS   = COMP_DIR / "cricket-stats.js"
COMP_HTML = COMP_DIR / "index.html"
DATA_JSON = OUTPUT / "2026" / "data.json"
TMP       = ROOT / "tmp"

sys.path.insert(0, str(ROOT / "shared"))
from utils import normalize_tournament, title_to_folder


def _read(path: Path) -> str:
    assert path.exists(), f"Missing file (run build.py first): {path}"
    return path.read_text()


def _load_data():
    return json.loads(_read(DATA_JSON))


# ---------------------------------------------------------------------------
# 1. Output files exist
# ---------------------------------------------------------------------------

def test_component_dir_exists():
    assert COMP_DIR.exists(), "output/component/ directory missing"


def test_component_js_exists():
    assert COMP_JS.exists(), "output/component/cricket-stats.js missing"


def test_component_demo_html_exists():
    assert COMP_HTML.exists(), "output/component/index.html missing"


# ---------------------------------------------------------------------------
# 2. Demo page structure
# ---------------------------------------------------------------------------

def test_demo_has_cricket_stats_element():
    assert '<cricket-stats' in _read(COMP_HTML)


def test_demo_loads_component_js():
    assert 'src="cricket-stats.js"' in _read(COMP_HTML)


def test_demo_uses_season_not_src():
    """Demo must use season= attribute — src= would hardcode a URL."""
    html = _read(COMP_HTML)
    tag = html.split('<cricket-stats')[1].split('>')[0]
    assert 'season="' in tag, "Demo <cricket-stats> missing season attribute"
    assert 'src="' not in tag, "Demo should use season= not src="


def test_demo_has_charset_utf8():
    assert 'charset="UTF-8"' in _read(COMP_HTML)


def test_demo_has_cricket_title():
    html = _read(COMP_HTML)
    assert '<title>' in html and 'Cricket' in html


# ---------------------------------------------------------------------------
# 3. JS component definition and attributes
# ---------------------------------------------------------------------------

def test_js_defines_custom_element():
    assert "customElements.define('cricket-stats'" in _read(COMP_JS)


def test_js_extends_html_element():
    assert "extends HTMLElement" in _read(COMP_JS)


def test_js_observed_attributes():
    js = _read(COMP_JS)
    for attr in ('src', 'season', 'base-url', 'tournament', 'team'):
        assert f"'{attr}'" in js, f"observedAttributes missing '{attr}'"


def test_js_team_attr_sets_initial_team_view():
    """team attribute must cause _load() to start in team view, not home."""
    js = _read(COMP_JS)
    assert "getAttribute('team')" in js, "Component does not read 'team' attribute"


def test_js_initial_view_respects_team_attr():
    """_load() must set navStack to team view when team attribute present."""
    js = _read(COMP_JS)
    load_body = js[js.index('async _load('):js.index('_onClick(e) {')]
    assert "type: 'team'" in load_body, \
        "_load() must initialise nav stack with team view when team attr is set"


def test_js_initial_view_respects_tournament_attr():
    """_load() must set navStack to tournament view (not home) when tournament attribute present."""
    js = _read(COMP_JS)
    load_body = js[js.index('async _load('):js.index('_onClick(e) {')]
    assert "type: 'tournament'" in load_body, \
        "_load() must initialise nav stack with tournament view when tournament attr is set"


def test_js_has_shadow_dom():
    assert "attachShadow" in _read(COMP_JS)


def test_js_captures_script_base_at_load_time():
    """_scriptBase must be captured at IIFE execution time, not inside a method."""
    assert "document.currentScript" in _read(COMP_JS)


def test_js_has_resolve_url():
    assert "_resolveUrl" in _read(COMP_JS)


def test_js_resolve_url_handles_src():
    assert "getAttribute('src')" in _read(COMP_JS)


def test_js_resolve_url_handles_season():
    assert "getAttribute('season')" in _read(COMP_JS)


def test_js_resolve_url_handles_base_url():
    assert "getAttribute('base-url')" in _read(COMP_JS)


# ---------------------------------------------------------------------------
# 4. JS component features
# ---------------------------------------------------------------------------

def test_js_has_view_router():
    js = _read(COMP_JS)
    for method in ('_navTo', '_back', '_renderView'):
        assert method in js, f"Missing view router method: {method}"


def test_js_has_three_view_types():
    js = _read(COMP_JS)
    for view in ("'home'", "'tournament'", "'team'"):
        assert view in js, f"Missing view type: {view}"


def test_js_has_home_view():
    js = _read(COMP_JS)
    assert "_homeHTML" in js and "_wireHome" in js


def test_js_has_tournament_view():
    assert "_tournHTML" in _read(COMP_JS)


def test_js_has_team_view():
    assert "_teamHTML" in _read(COMP_JS)


def test_js_has_tab_switching():
    assert "_switchTab" in _read(COMP_JS)


def test_js_has_view_toggle():
    assert "_switchView" in _read(COMP_JS)


def test_js_has_team_filter():
    assert "_wireTeamFilter" in _read(COMP_JS)


def test_js_has_pt_renderer():
    assert "_renderPT" in _read(COMP_JS)


def test_js_has_sc_renderer():
    assert "_renderSC" in _read(COMP_JS)


def test_js_has_all_match_renderers():
    js = _read(COMP_JS)
    for method in ('_pastTable', '_pastCards', '_upcomingTable', '_upcomingCards'):
        assert method in js, f"Missing match renderer: {method}"


def test_js_has_winner_detection():
    assert "_winner" in _read(COMP_JS)


def test_js_has_winner_css():
    assert ".card-score.winner" in _read(COMP_JS)


def test_js_has_tournament_pill():
    assert "_pill" in _read(COMP_JS)


def test_js_back_button_uses_entity():
    js = _read(COMP_JS)
    assert "data-cs-back" in js
    assert "&larr;" in js


def test_js_back_button_conditional_on_nav_depth():
    """Back button must only render when nav stack has >1 entry (not when view is root)."""
    js = _read(COMP_JS)
    tourn_body = js[js.index('_tournHTML(slug)'):js.index('_teamHTML(name)')]
    assert "_navStack.length" in tourn_body, \
        "_tournHTML must guard back button with _navStack.length check"
    team_body = js[js.index('_teamHTML(name)'):js.index('_renderPT(groups)')]
    assert "_navStack.length" in team_body, \
        "_teamHTML must guard back button with _navStack.length check"


def test_js_observed_attributes_includes_venue():
    js = _read(COMP_JS)
    obs = js[js.index('observedAttributes'):js.index('observedAttributes') + 100]
    assert "'venue'" in obs, "observedAttributes missing 'venue'"


def test_js_venue_attr_reads_attribute():
    js = _read(COMP_JS)
    assert "getAttribute('venue')" in js, "Component does not read 'venue' attribute"


def test_js_initial_view_respects_venue_attr():
    """_load() must set navStack to venue view when venue attribute present."""
    js = _read(COMP_JS)
    load_body = js[js.index('async _load('):js.index('_onClick(e) {')]
    assert "type: 'venue'" in load_body, \
        "_load() must initialise nav stack with venue view when venue attr is set"


def test_js_has_venue_view():
    assert "_venueHTML" in _read(COMP_JS)


def test_js_venue_navigation_attribute():
    assert "data-cs-venue" in _read(COMP_JS)


def test_js_venue_btn_css():
    assert ".cs-venue-btn" in _read(COMP_JS)


def test_js_hidden_attribute_not_overridden_by_display_flex():
    """Shadow CSS must enforce [hidden]{display:none!important} — otherwise display:flex on
    .match-card overrides the browser's hidden attribute rule and cards don't filter correctly."""
    js = _read(COMP_JS)
    assert '[hidden]' in js and 'display: none !important' in js, \
        "Shadow CSS must include [hidden]{display:none!important}"


def test_js_no_raw_unicode_arrow():
    """Raw ← causes encoding issues when JS file is served without explicit UTF-8."""
    assert '←' not in _read(COMP_JS)


def test_js_no_raw_unicode_middot():
    """Raw · causes encoding issues when JS file is served without explicit UTF-8."""
    assert '·' not in _read(COMP_JS)


def test_js_team_and_tourn_navigation_attributes():
    js = _read(COMP_JS)
    assert "data-cs-team" in js, "Team navigation attribute missing"
    assert "data-cs-tourn" in js, "Tournament navigation attribute missing"


# ---------------------------------------------------------------------------
# 5. data.json <-> component consistency
# ---------------------------------------------------------------------------

def test_data_json_tournament_count_matches_manifest_union():
    """data.json must have exactly one entry per unique tournament across PT + SC."""
    pt = json.loads((TMP / "pt_manifest.json").read_text())
    sc = json.loads((TMP / "sc_manifest.json").read_text())
    pt_names = {normalize_tournament(e["title"]) for e in pt}
    sc_names = {normalize_tournament(m["tournament"]) for m in sc["past"] + sc["upcoming"]}
    expected = len(pt_names | sc_names)
    actual   = len(_load_data()["tournaments"])
    assert actual == expected, \
        f"data.json has {actual} tournaments, expected {expected}"


def test_data_json_past_match_count_matches_manifest():
    """Total past matches in data.json must equal sc_manifest past count."""
    sc = json.loads((TMP / "sc_manifest.json").read_text())
    total = sum(len(t["past_matches"]) for t in _load_data()["tournaments"])
    assert total == len(sc["past"]), \
        f"data.json has {total} past matches, sc_manifest has {len(sc['past'])}"


def test_data_json_upcoming_match_count_matches_manifest():
    """Total upcoming matches in data.json must equal sc_manifest upcoming count."""
    sc = json.loads((TMP / "sc_manifest.json").read_text())
    total = sum(len(t["upcoming_matches"]) for t in _load_data()["tournaments"])
    assert total == len(sc["upcoming"]), \
        f"data.json has {total} upcoming, sc_manifest has {len(sc['upcoming'])}"


def test_data_json_team_registry_matches_teams_tsv():
    """Every team in teams.tsv must appear in data.json with the same ID."""
    from utils import load_team_ids
    tsv_teams  = load_team_ids(ROOT / "data" / "teams.tsv")
    data_teams = {t["name"]: t["id"] for t in _load_data()["teams"]}
    for name, tid in tsv_teams.items():
        assert name in data_teams, f"teams.tsv team '{name}' missing from data.json"
        assert data_teams[name] == tid, \
            f"ID mismatch for '{name}': data.json={data_teams[name]}, tsv={tid}"


def test_data_json_colors_are_valid_hex():
    """Tournament colors must be 6-digit lowercase hex codes."""
    for t in _load_data()["tournaments"]:
        color = t.get("color", "")
        assert re.match(r'^#[0-9a-f]{6}$', color), \
            f"Invalid color '{color}' for tournament '{t['name']}'"


def test_data_json_pt_team_names_are_normalized():
    """PT team names in data.json must not contain known pre-normalization OCR variants."""
    raw_names = {
        "At Sports Club", "Basel Cricket Club", "Basel CC- Colts",
        "Basel CC Juniors", "CERN CC", "COSSONAY CC",
        "St Gallen CC", "Zurich Crickets CC 1", "Nomads Embrach",
    }
    for t in _load_data()["tournaments"]:
        for rows in t.get("points_table", {}).values():
            for row in rows:
                name = row.get("Team", "")
                assert name not in raw_names, \
                    f"Un-normalized PT name '{name}' in data.json ({t['name']})"


def test_data_json_slugs_are_unique():
    """Each tournament slug must be unique — duplicates would overwrite pages."""
    slugs = [t["slug"] for t in _load_data()["tournaments"]]
    assert len(slugs) == len(set(slugs)), "Duplicate tournament slugs in data.json"


def test_data_json_team_ids_are_unique():
    """Each team ID in data.json must be unique."""
    ids = [t["id"] for t in _load_data()["teams"]]
    assert len(ids) == len(set(ids)), "Duplicate team IDs in data.json"


def test_component_js_matches_season_assets_copy():
    """output/component/cricket-stats.js must be identical to output/2026/assets/cricket-stats.js."""
    comp   = COMP_JS.read_bytes()
    assets = (OUTPUT / "2026" / "assets" / "cricket-stats.js").read_bytes()
    assert comp == assets, \
        "output/component/cricket-stats.js differs from output/2026/assets/cricket-stats.js — build.py copy mismatch"
