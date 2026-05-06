"""Rendering primitives for points table data."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))
from utils import title_to_folder, normalize_pt_team

HEADERS = ["Team", "M", "W", "L", "D", "T", "NR", "NRR", "Pt."]


def nrr_class(value: str) -> str:
    try:
        return "pos" if float(value) > 0 else ("neg" if float(value) < 0 else "")
    except ValueError:
        return ""


def _pt_team_link(name: str, team_url_map: dict | None) -> str:
    if not team_url_map:
        return name
    url = team_url_map.get(normalize_pt_team(name).lower())
    return f'<a href="{url}" class="team-link">{name}</a>' if url else name


def render_row(row: dict, team_url_map: dict | None = None) -> str:
    cells = []
    for h in HEADERS:
        val = row.get(h, "")
        if h == "NRR":
            cls = nrr_class(val)
            cells.append(f'<td class="{cls}">{val}</td>' if cls else f"<td>{val}</td>")
        elif h == "Team":
            cells.append(f'<td class="team">{_pt_team_link(val, team_url_map)}</td>')
        else:
            cells.append(f"<td>{val}</td>")
    return "    <tr>" + "".join(cells) + "</tr>"


def render_table(rows: list[dict], team_url_map: dict | None = None) -> str:
    header_cells = "".join(f"<th>{h}</th>" for h in HEADERS)
    thead = f"  <thead><tr>{header_cells}</tr></thead>"
    tbody_rows = "\n".join(render_row(r, team_url_map) for r in rows)
    tbody = f"  <tbody>\n{tbody_rows}\n  </tbody>"
    return f'<table class="points-table">\n{thead}\n{tbody}\n</table>'


def render_section(group_name: str, rows: list[dict], team_url_map: dict | None = None) -> str:
    title = group_name + " (League Matches)"
    table = render_table(rows, team_url_map)
    return f'<section>\n  <h2>{title}</h2>\n  {table}\n</section>'
