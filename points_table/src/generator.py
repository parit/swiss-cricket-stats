"""Rendering primitives for points table data."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))
from utils import title_to_folder

HEADERS = ["Team", "M", "W", "L", "D", "T", "NR", "NRR", "Pt."]


def nrr_class(value: str) -> str:
    try:
        return "pos" if float(value) > 0 else ("neg" if float(value) < 0 else "")
    except ValueError:
        return ""


def render_row(row: dict) -> str:
    cells = []
    for h in HEADERS:
        val = row.get(h, "")
        if h == "NRR":
            cls = nrr_class(val)
            cells.append(f'<td class="{cls}">{val}</td>' if cls else f"<td>{val}</td>")
        elif h == "Team":
            cells.append(f'<td class="team">{val}</td>')
        else:
            cells.append(f"<td>{val}</td>")
    return "    <tr>" + "".join(cells) + "</tr>"


def render_table(rows: list[dict]) -> str:
    header_cells = "".join(f"<th>{h}</th>" for h in HEADERS)
    thead = f"  <thead><tr>{header_cells}</tr></thead>"
    tbody_rows = "\n".join(render_row(r) for r in rows)
    tbody = f"  <tbody>\n{tbody_rows}\n  </tbody>"
    return f'<table class="points-table">\n{thead}\n{tbody}\n</table>'


def render_section(group_name: str, rows: list[dict]) -> str:
    title = group_name + " (League Matches)"
    table = render_table(rows)
    return f'<section>\n  <h2>{title}</h2>\n  {table}\n</section>'
