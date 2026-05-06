import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scorecards" / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))

from generator import group_by_tournament, sort_matches, render_table, render_card, render_upcoming_table, render_upcoming_card

MATCH_A1 = {
    "tournament": "TEST LEAGUE-2026",
    "date": "2026-05-01",
    "time": "09:00 AM UTC",
    "ground": "Ground A",
    "team_1st": "Team Alpha",
    "score_1st": "150/5 (20.0 Ov)",
    "team_2nd": "Team Beta",
    "score_2nd": "120/8 (20.0 Ov)",
    "result": "Team Alpha won by 30 runs",
}

MATCH_A2 = {
    "tournament": "TEST LEAGUE-2026",
    "date": "2026-05-01",
    "time": "11:00 AM UTC",
    "ground": "Ground A",
    "team_1st": "Team Gamma",
    "score_1st": "200/3 (20.0 Ov)",
    "team_2nd": "Team Delta",
    "score_2nd": "180/6 (20.0 Ov)",
    "result": "Team Gamma won by 20 runs",
}

MATCH_B = {
    "tournament": "OTHER LEAGUE-2026",
    "date": "2026-05-04",
    "time": "10:00 AM UTC",
    "ground": "Ground C",
    "team_1st": "Team X",
    "score_1st": "100/10 (18.0 Ov)",
    "team_2nd": "Team Y",
    "score_2nd": "101/2 (15.0 Ov)",
    "result": "Team Y won by 8 wickets",
}

UPCOMING = {
    "tournament": "TEST LEAGUE-2026",
    "date": "2026-09-01",
    "time": "10:00",
    "ground": "Ground A",
    "home_team": "Team Alpha",
    "away_team": "Team Beta",
}


# --- group_by_tournament ---

def test_group_by_tournament():
    groups = group_by_tournament([MATCH_A1, MATCH_A2, MATCH_B])
    assert set(groups.keys()) == {"TEST LEAGUE-2026", "OTHER LEAGUE-2026"}
    assert len(groups["TEST LEAGUE-2026"]) == 2
    assert len(groups["OTHER LEAGUE-2026"]) == 1


def test_group_by_tournament_empty():
    assert group_by_tournament([]) == {}


# --- sort_matches ---

def test_sort_by_date():
    m_late  = {**MATCH_A1, "date": "2026-05-03"}
    m_early = {**MATCH_A1, "date": "2026-05-01"}
    assert sort_matches([m_late, m_early]) == [m_early, m_late]


def test_sort_by_ground_within_date():
    m_b = {**MATCH_A1, "ground": "Ground B"}
    m_a = {**MATCH_A1, "ground": "Ground A"}
    assert sort_matches([m_b, m_a]) == [m_a, m_b]


def test_sort_by_time_within_date_and_ground():
    m_late  = {**MATCH_A1, "time": "11:00 AM UTC"}
    m_early = {**MATCH_A1, "time": "09:00 AM UTC"}
    assert sort_matches([m_late, m_early]) == [m_early, m_late]


def test_sort_noon_before_1pm():
    m_noon = {**MATCH_A1, "time": "12:00 PM UTC"}
    m_1pm  = {**MATCH_A1, "time": "01:00 PM UTC"}
    assert sort_matches([m_1pm, m_noon]) == [m_noon, m_1pm]


# --- render_table (past matches) ---

def test_render_table_has_all_headers():
    html = render_table([MATCH_A1])
    for header in ["Date", "Ground", "Batting 1st", "Score", "Result"]:
        assert header in html


def test_render_table_has_match_data():
    html = render_table([MATCH_A1])
    assert "Team Alpha" in html
    assert "150/5 (20.0 Ov)" in html
    assert "Team Beta" in html
    assert "120/8 (20.0 Ov)" in html
    assert "Team Alpha won by 30 runs" in html


def test_render_table_has_data_teams_attribute():
    html = render_table([MATCH_A1])
    assert 'data-teams="Team Alpha|Team Beta"' in html


def test_render_table_sorted_by_time():
    # MATCH_A1 is 09:00 (Team Alpha), MATCH_A2 is 11:00 (Team Gamma) — same date+ground
    html = render_table([MATCH_A2, MATCH_A1])
    assert html.index("Team Alpha") < html.index("Team Gamma")


def test_render_table_empty_returns_table():
    html = render_table([])
    assert "<table" in html


# --- render_card (past match card) ---

def test_render_card_has_teams():
    html = render_card(MATCH_A1)
    assert "Team Alpha" in html
    assert "Team Beta" in html


def test_render_card_has_result():
    html = render_card(MATCH_A1)
    assert "Team Alpha won by 30 runs" in html


def test_render_card_winner_has_winner_class():
    html = render_card(MATCH_A1)
    # Team Alpha won — their score span should have the winner class
    assert "winner" in html


def test_render_card_has_past_badge():
    html = render_card(MATCH_A1)
    assert "Past" in html


def test_render_card_has_data_teams():
    html = render_card(MATCH_A1)
    assert 'data-teams="Team Alpha|Team Beta"' in html


# --- render_upcoming_table ---

def test_render_upcoming_table_has_headers():
    html = render_upcoming_table([UPCOMING])
    for header in ["Date", "Ground", "Team 1", "Team 2"]:
        assert header in html


def test_render_upcoming_table_has_match_data():
    html = render_upcoming_table([UPCOMING])
    assert "Team Alpha" in html
    assert "Team Beta" in html
    assert "Ground A" in html


def test_render_upcoming_table_shows_time():
    html = render_upcoming_table([UPCOMING])
    assert "10:00" in html


def test_render_upcoming_table_empty_returns_message():
    html = render_upcoming_table([])
    assert "No upcoming matches" in html


# --- render_upcoming_card ---

def test_render_upcoming_card_has_teams():
    html = render_upcoming_card(UPCOMING)
    assert "Team Alpha" in html
    assert "Team Beta" in html


def test_render_upcoming_card_has_upcoming_badge():
    html = render_upcoming_card(UPCOMING)
    assert "Upcoming" in html
    assert "upcoming-badge" in html


def test_render_upcoming_card_has_ground_and_date():
    html = render_upcoming_card(UPCOMING)
    assert "Ground A" in html
    assert "2026" in html


def test_render_upcoming_card_has_data_teams():
    html = render_upcoming_card(UPCOMING)
    assert 'data-teams="Team Alpha|Team Beta"' in html
