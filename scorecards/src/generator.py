"""Rendering primitives for scorecard match data."""
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

_UTC = timezone.utc
_SWISS = ZoneInfo("Europe/Zurich")
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))
from utils import title_to_folder

HEADERS = ["Date", "Ground", "Batting 1st", "Score", "Batting 2nd", "Score", "Result"]


def group_by_tournament(matches: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {}
    for m in matches:
        groups.setdefault(m["tournament"], []).append(m)
    return groups


def _parse_time(time_str: str) -> datetime:
    clean = time_str.replace(" UTC", "").strip()
    for fmt in ("%I:%M %p", "%H:%M %p", "%H:%M"):
        try:
            return datetime.strptime(clean, fmt)
        except ValueError:
            continue
    return datetime.min


def _fmt_date(date_str: str) -> str:
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%-d %b %Y")
    except ValueError:
        return date_str


def sort_matches(matches: list[dict]) -> list[dict]:
    return sorted(matches, key=lambda m: (m["date"], m["ground"], _parse_time(m["time"])))


def _winner(m: dict) -> str:
    result = m.get("result", "")
    idx = result.lower().find(" won by")
    return result[:idx].strip() if idx > 0 else ""


def render_row(m: dict) -> str:
    teams = f'{m["team_1st"]}|{m["team_2nd"]}'
    return (
        f'<tr data-teams="{teams}">'
        f'<td class="dt">{_fmt_date(m["date"])}</td>'
        f'<td>{m["ground"]}</td>'
        f'<td class="team">{m["team_1st"]}</td>'
        f'<td class="score">{m["score_1st"]}</td>'
        f'<td class="team">{m["team_2nd"]}</td>'
        f'<td class="score">{m["score_2nd"]}</td>'
        f'<td class="result">{m["result"]}</td>'
        f'</tr>'
    )


def render_table(matches: list[dict]) -> str:
    header_cells = "".join(f"<th>{h}</th>" for h in HEADERS)
    thead = f"  <thead><tr>{header_cells}</tr></thead>"
    rows = "\n".join(render_row(m) for m in sort_matches(matches))
    tbody = f"  <tbody>\n{rows}\n  </tbody>"
    return f'<table class="scorecards-table">\n{thead}\n{tbody}\n</table>'


def render_card(m: dict) -> str:
    winner = _winner(m)
    s1_cls = " winner" if winner and winner.lower() == m["team_1st"].lower() else ""
    s2_cls = " winner" if winner and winner.lower() == m["team_2nd"].lower() else ""
    meta = f'{m["ground"]} &middot; {_fmt_date(m["date"])}'
    teams = f'{m["team_1st"]}|{m["team_2nd"]}'
    return (
        f'<div class="match-card" data-teams="{teams}">'
        f'<div class="card-meta"><span>{meta}</span><span class="card-badge">Past</span></div>'
        f'<div class="card-scores">'
        f'<div class="card-team-row">'
        f'<span class="card-team bold">{m["team_1st"]}</span>'
        f'<span class="card-score{s1_cls}">{m["score_1st"]}</span>'
        f'</div>'
        f'<div class="card-team-row">'
        f'<span class="card-team">{m["team_2nd"]}</span>'
        f'<span class="card-score{s2_cls}">{m["score_2nd"]}</span>'
        f'</div>'
        f'</div>'
        f'<div class="card-result">{m["result"] or "—"}</div>'
        f'</div>'
    )


_UPCOMING_HEADERS = ["Date", "Ground", "Team 1", "Team 2"]


def render_upcoming_row(m: dict) -> str:
    home = m.get("home_team") or m.get("team_1st", "")
    away = m.get("away_team") or m.get("team_2nd", "")
    teams = f"{home}|{away}"
    time_str = m.get("time", "")
    date_cell = f'{_fmt_date(m["date"])}' + (f' <span class="match-time">{time_str}</span>' if time_str and time_str != "TBD" else "")
    return (
        f'<tr data-teams="{teams}">'
        f'<td class="dt">{date_cell}</td>'
        f'<td>{m["ground"]}</td>'
        f'<td class="team">{home}</td>'
        f'<td class="team">{away}</td>'
        f'</tr>'
    )


def render_upcoming_table(matches: list[dict]) -> str:
    if not matches:
        return '<p class="empty-msg">No upcoming matches scheduled yet.</p>'
    header_cells = "".join(f"<th>{h}</th>" for h in _UPCOMING_HEADERS)
    thead = f"  <thead><tr>{header_cells}</tr></thead>"
    rows = "\n".join(render_upcoming_row(m) for m in sorted(matches, key=lambda m: m["date"]))
    tbody = f"  <tbody>\n{rows}\n  </tbody>"
    return f'<table class="scorecards-table">\n{thead}\n{tbody}\n</table>'


def render_upcoming_card(m: dict) -> str:
    home = m.get("home_team") or m.get("team_1st", "")
    away = m.get("away_team") or m.get("team_2nd", "")
    teams = f"{home}|{away}"
    time_str = m.get("time", "")
    time_part = f" &middot; {time_str}" if time_str and time_str != "TBD" else ""
    meta = f'{m["ground"]} &middot; {_fmt_date(m["date"])}{time_part}'
    return (
        f'<div class="match-card" data-teams="{teams}">'
        f'<div class="card-meta"><span>{meta}</span><span class="card-badge upcoming-badge">Upcoming</span></div>'
        f'<div class="card-scores">'
        f'<div class="card-team-row"><span class="card-team bold">{home}</span></div>'
        f'<div class="card-team-row"><span class="card-team">{away}</span></div>'
        f'</div>'
        f'</div>'
    )


def render_cards_grid(matches: list[dict]) -> str:
    cards = "\n".join(render_card(m) for m in sort_matches(matches))
    return f'<div class="cards-grid">\n{cards}\n</div>'


def render_upcoming_cards_grid(matches: list[dict]) -> str:
    if not matches:
        return '<p class="empty-msg">No upcoming matches scheduled yet.</p>'
    cards = "\n".join(render_upcoming_card(m) for m in sorted(matches, key=lambda m: m["date"]))
    return f'<div class="cards-grid">\n{cards}\n</div>'
