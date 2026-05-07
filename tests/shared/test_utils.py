import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))

from utils import title_to_folder, normalize_pt_team

ROOT = Path(__file__).parent.parent.parent
TEAMS_TSV = ROOT / "data" / "teams.tsv"


def test_basic_conversion():
    assert title_to_folder("PICKWICK CUP T20 COMPETITIONS (ELITE DIVISION)-2026") == "pickwick_t20_elite_division_2026"


def test_removes_cup():
    assert title_to_folder("PICKWICK CUP T20 2026") == "pickwick_t20_2026"


def test_removes_competitions():
    assert title_to_folder("T20 COMPETITIONS LEAGUE 2026") == "t20_league_2026"


def test_no_double_underscore():
    assert title_to_folder("CRICKET SWITZERLAND NATIONAL LEAGUE ( CSNL)-2026") == "cricket_switzerland_national_league_csnl_2026"


def test_all_noise_returns_empty():
    assert title_to_folder("CUP COMPETITIONS") == ""


def test_empty_input():
    assert title_to_folder("") == ""


def test_normalize_pt_team_geneva_cc():
    assert normalize_pt_team("GENEVA CC") == "Geneva CC"


def test_teams_tsv_no_case_insensitive_duplicates():
    lines = [l for l in TEAMS_TSV.read_text().splitlines()[1:] if '\t' in l]
    names_lower = [l.split('\t')[1].lower() for l in lines]
    assert len(names_lower) == len(set(names_lower)), \
        "teams.tsv has entries that differ only in case"
