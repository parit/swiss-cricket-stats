"""Structural tests for web-component shell pages."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUT  = ROOT / "output" / "2026"
DATA = ROOT / "data"
TMP  = ROOT / "tmp"

sys.path.insert(0, str(ROOT / "shared"))
from utils import load_team_ids, normalize_tournament, title_to_folder


def _read(p: Path) -> str:
    assert p.exists(), f"Missing (run build.py first): {p}"
    return p.read_text()

def _all_tournament_slugs() -> list[str]:
    pt_path = TMP / "pt_manifest.json"
    sc_path = TMP / "sc_manifest.json"
    assert pt_path.exists(), f"Missing manifest (run build.py first): {pt_path}"
    assert sc_path.exists(), f"Missing manifest (run build.py first): {sc_path}"
    pt = json.loads(pt_path.read_text())
    sc = json.loads(sc_path.read_text())
    names = set(normalize_tournament(e["title"]) for e in pt)
    names |= set(normalize_tournament(m["tournament"]) for m in sc["past"] + sc.get("upcoming", []))
    slugs = [title_to_folder(n) for n in names]
    assert slugs, "No tournament slugs found — manifests may be empty"
    return slugs


def test_combined_shell_exists():
    assert (OUT / "index.html").exists()

def test_combined_shell_has_cricket_stats_element():
    assert "<cricket-stats" in _read(OUT / "index.html")

def test_combined_shell_src_points_to_data_json():
    assert 'src="data.json"' in _read(OUT / "index.html")

def test_combined_shell_has_no_back_link():
    assert "season-link" not in _read(OUT / "index.html")

def test_per_tournament_shells_exist():
    for slug in _all_tournament_slugs():
        assert (OUT / slug / "stats.html").exists(), f"Missing: {slug}/stats.html"

def test_per_tournament_shells_have_cricket_stats_element():
    pages = list(OUT.glob("*/stats.html"))
    assert pages, "No stats.html files found under output/2026/"
    for p in pages:
        assert "<cricket-stats" in _read(p), f"Missing <cricket-stats in {p}"

def test_per_tournament_shells_have_tournament_attr():
    for p in OUT.glob("*/stats.html"):
        assert 'tournament="' in _read(p), f"Missing tournament= in {p}"

def test_per_tournament_shells_have_no_back_link():
    for p in OUT.glob("*/stats.html"):
        assert "season-link" not in _read(p), f"Stale season-link in {p}"

def test_per_team_shells_exist():
    ids = load_team_ids(DATA / "teams.tsv")
    for name, tid in ids.items():
        assert (OUT / "teams" / tid / "index.html").exists(), f"Missing: teams/{tid}/index.html"

def test_per_team_shells_have_team_attr():
    pages = list((OUT / "teams").glob("*/index.html"))
    assert pages, "No team index.html files found under output/2026/teams/"
    for p in pages:
        assert 'team="' in _read(p), f"Missing team= in {p}"

def test_per_team_shells_have_no_back_link():
    pages = list((OUT / "teams").glob("*/index.html"))
    assert pages, "No team index.html files found under output/2026/teams/"
    for p in pages:
        assert "season-link" not in _read(p), f"Stale season-link in {p}"
