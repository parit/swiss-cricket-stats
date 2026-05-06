"""Generate output/stats.html and output/<tournament>/stats.html."""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "shared"))
from utils import title_to_folder, normalize_tournament, normalize_pt_team, assign_team_ids, load_team_ids


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_pt = _load("pt_gen", ROOT / "points_table" / "src" / "generator.py")
_sc = _load("sc_gen", ROOT / "scorecards" / "src" / "generator.py")

_SC_CONTROLS = (
    '<div class="sc-controls">'
    '<div class="view-toggle">'
    '<button class="view-btn active" data-view="list">List</button>'
    '<button class="view-btn" data-view="cards">Cards</button>'
    '</div>'
    '<div class="team-filter">'
    '<label>Team:</label>'
    '<select class="sc-team-filter"><option value="">All teams</option></select>'
    '</div>'
    '</div>'
)

_PAGE_STYLE = """
  <style>
    .stats-selector { margin-bottom: 20px; }
    .stats-selector label { font-weight: 600; margin-right: 8px; font-size: 0.9rem; }
    .stats-selector select {
      padding: 8px 12px; font-size: 0.9rem;
      border: 1px solid #ccc; border-radius: 4px;
      background: #fff; cursor: pointer; min-width: 280px;
    }
  </style>"""


def _pt_content(data: dict, team_url_map: dict | None = None) -> str:
    return "\n\n".join(_pt.render_section(g, rows, team_url_map) for g, rows in data.items())


def _sc_content(past: list[dict], upcoming: list[dict], show_tournament: bool = False, team_url_map: dict | None = None, tourn_url_prefix: str | None = None) -> str:
    list_html  = f'<div class="list-view">{_sc.render_table(past, show_tournament, team_url_map, tourn_url_prefix)}</div>'
    cards_html = f'<div class="cards-view" style="display:none">{_sc.render_cards_grid(past, show_tournament, team_url_map, tourn_url_prefix)}</div>'
    past_section = (
        f'<div class="match-section">\n'
        f'  <h2 class="sc-subtitle">Past Matches</h2>\n'
        f'  {list_html}\n'
        f'  {cards_html}\n'
        f'</div>'
    )
    up_list  = f'<div class="list-view">{_sc.render_upcoming_table(upcoming, show_tournament, team_url_map, tourn_url_prefix)}</div>'
    up_cards = f'<div class="cards-view" style="display:none">{_sc.render_upcoming_cards_grid(upcoming, show_tournament, team_url_map, tourn_url_prefix)}</div>'
    upcoming_section = (
        f'<div class="match-section">\n'
        f'  <h2 class="sc-subtitle">Upcoming Matches</h2>\n'
        f'  {up_list}\n'
        f'  {up_cards}\n'
        f'</div>'
    )
    return f'{_SC_CONTROLS}\n{past_section}\n{upcoming_section}'


def _html_page(title: str, body: str, css: str, js: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <link rel="stylesheet" href="{css}">
{_PAGE_STYLE}
</head>
<body>
{body}
  <script src="{js}"></script>
</body>
</html>"""


def generate_stats(
    pt_tournaments: list[tuple[str, dict]],
    sc_matches: list[dict],
    sc_upcoming: list[dict] | None = None,
    out_dir: str = "output",
) -> str:
    """Generate output/stats.html — combined page with tournament dropdown + tabs."""
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    pt_by_name = {normalize_tournament(t): d for t, d in pt_tournaments}
    sc_by_name = _sc.group_by_tournament([{**m, "tournament": normalize_tournament(m["tournament"])} for m in sc_matches])

    sc_upcoming = sc_upcoming or []
    sc_upcoming_by_name = _sc.group_by_tournament([{**m, "tournament": normalize_tournament(m["tournament"])} for m in sc_upcoming]) if sc_upcoming else {}

    all_names = sorted(set(pt_by_name) | set(sc_by_name) | set(sc_upcoming_by_name))
    tmap = _team_url_map("teams/")

    options = "\n".join(
        f'      <option value="{title_to_folder(t)}">{t}</option>'
        for t in all_names
    )

    pt_sections, sc_sections = [], []
    for name in all_names:
        slug = title_to_folder(name)
        if name in pt_by_name:
            pt_sections.append(
                f'  <section class="pt-section" id="pt-{slug}" style="display:none">\n'
                f'    {_pt_content(pt_by_name[name], tmap)}\n'
                f'  </section>'
            )
        if name in sc_by_name or name in sc_upcoming_by_name:
            sc_sections.append(
                f'  <section class="sc-section" id="sc-{slug}" style="display:none">\n'
                f'    {_sc_content(sc_by_name.get(name, []), sc_upcoming_by_name.get(name, []), team_url_map=tmap)}\n'
                f'  </section>'
            )

    body = f"""  <h1>Cricket Switzerland — Season 2026</h1>

  <div class="stats-selector">
    <label for="stats-tournament-select">Tournament:</label>
    <select id="stats-tournament-select">
{options}
    </select>
  </div>

  <div class="tabs">
    <button class="tab-btn active" data-tab="points-table">Points Table</button>
    <button class="tab-btn" data-tab="scorecards">Matches</button>
  </div>

  <div class="tab-content active" id="tab-points-table">
{"".join(pt_sections)}
  </div>

  <div class="tab-content" id="tab-scorecards">
{"".join(sc_sections)}
  </div>"""

    html = _html_page("Cricket Switzerland — Season 2026", body, "assets/style.css", "assets/script.js")
    out_path = Path(out_dir) / "index.html"
    out_path.write_text(html)
    print(f"[stats] Combined → {out_path}")
    return str(out_path)


def generate_per_tournament_stats(
    pt_tournaments: list[tuple[str, dict]],
    sc_matches: list[dict],
    sc_upcoming: list[dict] | None = None,
    out_dir: str = "output",
) -> list[str]:
    """Generate output/<tournament>/stats.html for each tournament."""
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    sc_upcoming = sc_upcoming or []
    sc_upcoming_by_name = _sc.group_by_tournament([{**m, "tournament": normalize_tournament(m["tournament"])} for m in sc_upcoming]) if sc_upcoming else {}

    pt_by_name = {normalize_tournament(t): d for t, d in pt_tournaments}
    sc_by_name = _sc.group_by_tournament([{**m, "tournament": normalize_tournament(m["tournament"])} for m in sc_matches])
    all_names = sorted(set(pt_by_name) | set(sc_by_name) | set(sc_upcoming_by_name))
    tmap = _team_url_map("../teams/")

    out_paths = []
    for name in all_names:
        slug = title_to_folder(name)
        if not slug:
            continue

        has_pt = name in pt_by_name
        has_sc = name in sc_by_name or name in sc_upcoming_by_name
        show_tabs = has_pt and has_sc

        tab_btns, tab_contents = [], []
        first = True

        if has_pt:
            active = "active" if first else ""
            first = False
            tab_btns.append(f'<button class="tab-btn {active}" data-tab="points-table">Points Table</button>')
            tab_contents.append(
                f'  <div class="tab-content {active}" id="tab-points-table">\n'
                f'    {_pt_content(pt_by_name[name], tmap)}\n'
                f'  </div>'
            )

        if has_sc:
            active = "active" if first else ""
            tab_btns.append(f'<button class="tab-btn {active}" data-tab="scorecards">Matches</button>')
            tab_contents.append(
                f'  <div class="tab-content {active}" id="tab-scorecards">\n'
                f'    {_sc_content(sc_by_name.get(name, []), sc_upcoming_by_name.get(name, []), team_url_map=tmap)}\n'
                f'  </div>'
            )

        tabs_html = (
            f'  <div class="tabs">\n    {"".join(tab_btns)}\n  </div>\n'
            if show_tabs else ""
        )

        body = f'  <a href="../index.html" class="season-link">&larr; Season 2026</a>\n  <h1>{name}</h1>\n{tabs_html}{"".join(tab_contents)}'
        html = _html_page(name, body, "../assets/style.css", "../assets/script.js")

        out_path = Path(out_dir) / slug / "stats.html"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html)
        print(f"[stats] Per-tournament → {out_path}")
        out_paths.append(str(out_path))

    return out_paths


_TEAMS_TSV = ROOT / "data" / "teams.tsv"


def _team_url_map(prefix: str) -> dict:
    """Build {team_name_lower: relative_url} with the given path prefix."""
    ids = load_team_ids(_TEAMS_TSV)
    return {name.lower(): f"{prefix}{tid}/index.html" for name, tid in ids.items()}


def generate_per_team_stats(
    pt_tournaments: list[tuple[str, dict]],
    sc_matches: list[dict],
    sc_upcoming: list[dict] | None = None,
    out_dir: str = "output",
) -> list[str]:
    """Generate output/teams/<team_id>/index.html for each team."""
    sc_upcoming = sc_upcoming or []

    pt_by_name = {normalize_tournament(t): d for t, d in pt_tournaments}
    sc_past_norm     = [{**m, "tournament": normalize_tournament(m["tournament"])} for m in sc_matches]
    sc_upcoming_norm = [{**m, "tournament": normalize_tournament(m["tournament"])} for m in sc_upcoming]

    # Collect all known teams from scorecard data
    teams: set[str] = set()
    for m in sc_past_norm:
        teams.update([m["team_1st"], m["team_2nd"]])
    for m in sc_upcoming_norm:
        teams.update(filter(None, [m.get("home_team", ""), m.get("away_team", "")]))

    team_ids = assign_team_ids(sorted(t for t in teams if t.strip()), _TEAMS_TSV)
    tmap = _team_url_map("../")

    out_paths = []
    for team in sorted(teams):
        if not team.strip():
            continue
        team_id = team_ids.get(team)
        if not team_id:
            continue

        t = team.lower()

        team_past = [m for m in sc_past_norm
                     if m["team_1st"].lower() == t or m["team_2nd"].lower() == t]
        team_upcoming = [m for m in sc_upcoming_norm
                         if m.get("home_team", "").lower() == t or m.get("away_team", "").lower() == t]

        # PT tournaments where this team appears (normalize PT team names for matching)
        team_pt: list[tuple[str, dict]] = []
        for name, groups in pt_by_name.items():
            if any(normalize_pt_team(r.get("Team", "")).lower() == t for rows in groups.values() for r in rows):
                team_pt.append((name, groups))

        has_sc = bool(team_past or team_upcoming)
        has_pt = bool(team_pt)
        if not has_sc and not has_pt:
            continue

        tab_btns, tab_contents = [], []
        first = True

        # Scorecards tab first — primary interest for team pages
        if has_sc:
            active = "active" if first else ""
            first = False
            tab_btns.append(f'<button class="tab-btn {active}" data-tab="scorecards">Matches</button>')
            tab_contents.append(
                f'  <div class="tab-content {active}" id="tab-scorecards">\n'
                f'    {_sc_content(team_past, team_upcoming, show_tournament=True, team_url_map=tmap, tourn_url_prefix="../../")}\n'
                f'  </div>'
            )

        if has_pt:
            active = "active" if first else ""
            pt_html = "\n\n".join(
                f'<h2 class="sc-subtitle">{name}</h2>\n{_pt_content(groups, tmap)}'
                for name, groups in team_pt
            )
            tab_btns.append(f'<button class="tab-btn {active}" data-tab="points-table">Points Table</button>')
            tab_contents.append(
                f'  <div class="tab-content {active}" id="tab-points-table">\n'
                f'    {pt_html}\n'
                f'  </div>'
            )

        show_tabs = has_sc and has_pt
        tabs_html = (
            f'  <div class="tabs">\n    {"".join(tab_btns)}\n  </div>\n'
            if show_tabs else ""
        )

        body = f'  <a href="../../index.html" class="season-link">&larr; Season 2026</a>\n  <h1>{team}</h1>\n{tabs_html}{"".join(tab_contents)}'
        html = _html_page(team, body, "../../assets/style.css", "../../assets/script.js")

        out_path = Path(out_dir) / "teams" / team_id / "index.html"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html)
        print(f"[stats] Team {team_id} → {team}")
        out_paths.append(str(out_path))

    return out_paths
