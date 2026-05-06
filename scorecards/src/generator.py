"""Rendering primitives for scorecard match data."""
import hashlib
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

_UTC = timezone.utc
_SWISS = ZoneInfo("Europe/Zurich")
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))
from utils import title_to_folder, normalize_tournament, load_tournament_abbreviations

_ABBREV_PATH = Path(__file__).resolve().parents[2] / "data" / "tournament_abbreviations.tsv"
_ABBREVIATIONS: dict[str, str] = load_tournament_abbreviations(_ABBREV_PATH)


def _tourn_display(name: str) -> str:
    """Abbreviation if defined, otherwise stripped short name."""
    return _ABBREVIATIONS.get(normalize_tournament(name)) or _short_tournament(name)

# Stable colour palette for tournament differentiation
_PALETTE = [
    "#3498db", "#e74c3c", "#2ecc71", "#f39c12",
    "#9b59b6", "#1abc9c", "#e67e22", "#e91e63",
    "#607d8b", "#795548", "#00bcd4",
]


def _tourn_color(tournament: str) -> str:
    h = int(hashlib.md5(tournament.encode()).hexdigest(), 16)
    return _PALETTE[h % len(_PALETTE)]


def _team_link(name: str, team_url_map: dict | None) -> str:
    if not team_url_map:
        return name
    url = team_url_map.get(name.lower())
    return f'<a href="{url}" class="team-link">{name}</a>' if url else name


def _short_tournament(name: str) -> str:
    """Strip parenthetical suffixes and trailing year from tournament name."""
    name = re.sub(r"\s*\([^)]*\)", "", name)    # remove (...)
    name = re.sub(r"[\s-]+\d{4}\s*$", "", name)  # remove trailing year
    return name.strip()


HEADERS              = ["Date", "Ground", "Batting 1st", "Score", "Batting 2nd", "Score", "Result"]
HEADERS_WITH_TOURN   = HEADERS + ["Tournament"]
_UPCOMING_HEADERS              = ["Date", "Ground", "Team 1", "Team 2"]
_UPCOMING_HEADERS_WITH_TOURN   = _UPCOMING_HEADERS + ["Tournament"]


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


def _tourn_pill(tournament: str, tourn_url_prefix: str | None) -> str:
    color = _tourn_color(tournament)
    label = _tourn_display(tournament)
    style = f'class="tourn-pill" style="background:{color}"'
    if tourn_url_prefix:
        url = f"{tourn_url_prefix}{title_to_folder(tournament)}/stats.html"
        return f'<a href="{url}" {style}>{label}</a>'
    return f'<span {style}>{label}</span>'


def render_row(m: dict, show_tournament: bool = False, team_url_map: dict | None = None, tourn_url_prefix: str | None = None) -> str:
    teams = f'{m["team_1st"]}|{m["team_2nd"]}'
    t1 = _team_link(m["team_1st"], team_url_map)
    t2 = _team_link(m["team_2nd"], team_url_map)
    if show_tournament:
        color = _tourn_color(m["tournament"])
        date_td = f'<td class="dt" style="border-left:5px solid {color};padding-left:10px">{_fmt_date(m["date"])}</td>'
        tourn_td = f'<td>{_tourn_pill(m["tournament"], tourn_url_prefix)}</td>'
    else:
        date_td = f'<td class="dt">{_fmt_date(m["date"])}</td>'
        tourn_td = ""
    return (
        f'<tr data-teams="{teams}">'
        f'{date_td}'
        f'<td>{m["ground"]}</td>'
        f'<td class="team">{t1}</td>'
        f'<td class="score">{m["score_1st"]}</td>'
        f'<td class="team">{t2}</td>'
        f'<td class="score">{m["score_2nd"]}</td>'
        f'<td class="result">{m["result"]}</td>'
        f'{tourn_td}'
        f'</tr>'
    )


def render_table(matches: list[dict], show_tournament: bool = False, team_url_map: dict | None = None, tourn_url_prefix: str | None = None) -> str:
    headers = HEADERS_WITH_TOURN if show_tournament else HEADERS
    header_cells = "".join(f"<th>{h}</th>" for h in headers)
    thead = f"  <thead><tr>{header_cells}</tr></thead>"
    rows = "\n".join(render_row(m, show_tournament, team_url_map, tourn_url_prefix) for m in sort_matches(matches))
    tbody = f"  <tbody>\n{rows}\n  </tbody>"
    return f'<table class="scorecards-table">\n{thead}\n{tbody}\n</table>'


def render_card(m: dict, show_tournament: bool = False, team_url_map: dict | None = None, tourn_url_prefix: str | None = None) -> str:
    winner = _winner(m)
    s1_cls = " winner" if winner and winner.lower() == m["team_1st"].lower() else ""
    s2_cls = " winner" if winner and winner.lower() == m["team_2nd"].lower() else ""
    meta = f'{m["ground"]} &middot; {_fmt_date(m["date"])}'
    teams = f'{m["team_1st"]}|{m["team_2nd"]}'
    t1 = _team_link(m["team_1st"], team_url_map)
    t2 = _team_link(m["team_2nd"], team_url_map)
    if show_tournament:
        color = _tourn_color(m["tournament"])
        card_style = f' style="border-top:5px solid {color}"'
        tourn_html = f'<div class="card-tournament">{_tourn_pill(m["tournament"], tourn_url_prefix)}</div>'
    else:
        card_style = ""
        tourn_html = ""
    return (
        f'<div class="match-card" data-teams="{teams}"{card_style}>'
        f'<div class="card-meta"><span>{meta}</span><span class="card-badge">Past</span></div>'
        f'{tourn_html}'
        f'<div class="card-scores">'
        f'<div class="card-team-row">'
        f'<span class="card-team bold">{t1}</span>'
        f'<span class="card-score{s1_cls}">{m["score_1st"]}</span>'
        f'</div>'
        f'<div class="card-team-row">'
        f'<span class="card-team">{t2}</span>'
        f'<span class="card-score{s2_cls}">{m["score_2nd"]}</span>'
        f'</div>'
        f'</div>'
        f'<div class="card-result">{m["result"] or "—"}</div>'
        f'</div>'
    )


def render_upcoming_row(m: dict, show_tournament: bool = False, team_url_map: dict | None = None, tourn_url_prefix: str | None = None) -> str:
    home = m.get("home_team") or m.get("team_1st", "")
    away = m.get("away_team") or m.get("team_2nd", "")
    teams = f"{home}|{away}"
    time_str = m.get("time", "")
    date_cell = f'{_fmt_date(m["date"])}' + (f' <span class="match-time">{time_str}</span>' if time_str and time_str != "TBD" else "")
    home_html = _team_link(home, team_url_map)
    away_html = _team_link(away, team_url_map)
    if show_tournament:
        color = _tourn_color(m["tournament"])
        date_td = f'<td class="dt" style="border-left:5px solid {color};padding-left:10px">{date_cell}</td>'
        tourn_td = f'<td>{_tourn_pill(m["tournament"], tourn_url_prefix)}</td>'
    else:
        date_td = f'<td class="dt">{date_cell}</td>'
        tourn_td = ""
    return (
        f'<tr data-teams="{teams}">'
        f'{date_td}'
        f'<td>{m["ground"]}</td>'
        f'<td class="team">{home_html}</td>'
        f'<td class="team">{away_html}</td>'
        f'{tourn_td}'
        f'</tr>'
    )


def render_upcoming_table(matches: list[dict], show_tournament: bool = False, team_url_map: dict | None = None, tourn_url_prefix: str | None = None) -> str:
    if not matches:
        return '<p class="empty-msg">No upcoming matches scheduled yet.</p>'
    headers = _UPCOMING_HEADERS_WITH_TOURN if show_tournament else _UPCOMING_HEADERS
    header_cells = "".join(f"<th>{h}</th>" for h in headers)
    thead = f"  <thead><tr>{header_cells}</tr></thead>"
    rows = "\n".join(render_upcoming_row(m, show_tournament, team_url_map, tourn_url_prefix) for m in sorted(matches, key=lambda m: m["date"]))
    tbody = f"  <tbody>\n{rows}\n  </tbody>"
    return f'<table class="scorecards-table">\n{thead}\n{tbody}\n</table>'


def render_upcoming_card(m: dict, show_tournament: bool = False, team_url_map: dict | None = None, tourn_url_prefix: str | None = None) -> str:
    home = m.get("home_team") or m.get("team_1st", "")
    away = m.get("away_team") or m.get("team_2nd", "")
    teams = f"{home}|{away}"
    time_str = m.get("time", "")
    time_part = f" &middot; {time_str}" if time_str and time_str != "TBD" else ""
    meta = f'{m["ground"]} &middot; {_fmt_date(m["date"])}{time_part}'
    home_html = _team_link(home, team_url_map)
    away_html = _team_link(away, team_url_map)
    if show_tournament:
        color = _tourn_color(m["tournament"])
        card_style = f' style="border-top:5px solid {color}"'
        tourn_html = f'<div class="card-tournament">{_tourn_pill(m["tournament"], tourn_url_prefix)}</div>'
    else:
        card_style = ""
        tourn_html = ""
    return (
        f'<div class="match-card" data-teams="{teams}"{card_style}>'
        f'<div class="card-meta"><span>{meta}</span><span class="card-badge upcoming-badge">Upcoming</span></div>'
        f'{tourn_html}'
        f'<div class="card-scores">'
        f'<div class="card-team-row"><span class="card-team bold">{home_html}</span></div>'
        f'<div class="card-team-row"><span class="card-team">{away_html}</span></div>'
        f'</div>'
        f'</div>'
    )


def render_cards_grid(matches: list[dict], show_tournament: bool = False, team_url_map: dict | None = None, tourn_url_prefix: str | None = None) -> str:
    cards = "\n".join(render_card(m, show_tournament, team_url_map, tourn_url_prefix) for m in sort_matches(matches))
    return f'<div class="cards-grid">\n{cards}\n</div>'


def render_upcoming_cards_grid(matches: list[dict], show_tournament: bool = False, team_url_map: dict | None = None, tourn_url_prefix: str | None = None) -> str:
    if not matches:
        return '<p class="empty-msg">No upcoming matches scheduled yet.</p>'
    cards = "\n".join(render_upcoming_card(m, show_tournament, team_url_map, tourn_url_prefix) for m in sorted(matches, key=lambda m: m["date"]))
    return f'<div class="cards-grid">\n{cards}\n</div>'
