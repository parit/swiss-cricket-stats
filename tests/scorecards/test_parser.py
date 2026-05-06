import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scorecards" / "src"))

from parser import parse_tournament, parse_date, parse_total, label_anchored_parse

PAGE0_FIXTURE = """
Cricket Switzerland
PICKWICK CUP T20 COMPETITIONS (ELITE DIVISION)-2026
(League Matches)
5/5/26, 10:41 AM
1 of 4
Match Details
Match
ZURICH NOMADS vs
Winterthur CC
Ground
Deutweg..,
Winterthur
Date
2026-05-03, 09:58 AM UTC
Match Result
Toss
ZURICH NOMADS opt to bat
Total
ZURICH NOMADS 272/5 (20.0 Ov)
Winterthur CC 147/10 (16.4 Ov)
Result
ZURICH NOMADS won by 125 runs
Best Performances - Batsmen
Players Name
R
B
"""


def test_parse_tournament():
    lines = PAGE0_FIXTURE.splitlines()
    assert parse_tournament(lines) == "PICKWICK CUP T20 COMPETITIONS (ELITE DIVISION)-2026"


def test_parse_date_splits_correctly():
    date, time = parse_date(["2026-05-03, 09:58 AM UTC"])
    assert date == "2026-05-03"
    assert time == "09:58 AM UTC"


def test_parse_date_empty():
    date, time = parse_date([])
    assert date == ""
    assert time == ""


def test_parse_total_extracts_teams_and_scores():
    lines = ["ZURICH NOMADS 272/5 (20.0 Ov)", "Winterthur CC 147/10 (16.4 Ov)"]
    t1, s1, t2, s2 = parse_total(lines)
    assert t1 == "ZURICH NOMADS"
    assert s1 == "272/5 (20.0 Ov)"
    assert t2 == "Winterthur CC"
    assert s2 == "147/10 (16.4 Ov)"


def test_parse_total_single_digit_wickets():
    lines = ["Team Alpha 150/5 (20.0 Ov)", "Team Beta 120/8 (20.0 Ov)"]
    t1, s1, t2, s2 = parse_total(lines)
    assert t1 == "Team Alpha"
    assert s1 == "150/5 (20.0 Ov)"


def test_label_anchored_parse_match():
    # "Match" was removed from LABELS (dead data flow); it must not appear in output
    lines = PAGE0_FIXTURE.splitlines()
    fields = label_anchored_parse(lines)
    assert "Match" not in fields


def test_label_anchored_parse_ground():
    lines = PAGE0_FIXTURE.splitlines()
    fields = label_anchored_parse(lines)
    assert fields["Ground"] == ["Deutweg..,", "Winterthur"]


def test_label_anchored_parse_date():
    lines = PAGE0_FIXTURE.splitlines()
    fields = label_anchored_parse(lines)
    assert fields["Date"] == ["2026-05-03, 09:58 AM UTC"]


def test_label_anchored_parse_total():
    lines = PAGE0_FIXTURE.splitlines()
    fields = label_anchored_parse(lines)
    assert fields["Total"] == ["ZURICH NOMADS 272/5 (20.0 Ov)", "Winterthur CC 147/10 (16.4 Ov)"]


def test_label_anchored_parse_result_first_line():
    lines = PAGE0_FIXTURE.splitlines()
    fields = label_anchored_parse(lines)
    assert fields["Result"][0] == "ZURICH NOMADS won by 125 runs"
