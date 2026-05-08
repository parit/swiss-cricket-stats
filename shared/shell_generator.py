"""Generate thin web-component shell pages for output/2026/."""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "shared"))
from utils import load_team_ids

_TEAMS_TSV = ROOT / "data" / "teams.tsv"


def _shell(title: str, css: str, js: str, back: str | None, attrs: str) -> str:
    back_html = f'\n  <a href="{back}" class="season-link">&larr; Season 2026</a>' if back else ''
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <link rel="stylesheet" href="{css}">
</head>
<body>{back_html}
  <script src="{js}"></script>
  <cricket-stats {attrs}></cricket-stats>
</body>
</html>"""


def generate_combined_shell(out_dir: str) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    html = _shell(
        title="Cricket Switzerland 2026",
        css="assets/style.css",
        js="assets/cricket-stats.js",
        back=None,
        attrs='season="2026" src="data.json"',
    )
    (out / "index.html").write_text(html)
    print(f"[shell] Combined → {out / 'index.html'}")


def generate_per_tournament_shells(tournaments: list[tuple[str, str]], out_dir: str) -> None:
    """tournaments: list of (display_name, slug) pairs."""
    out = Path(out_dir)
    for name, slug in tournaments:
        d = out / slug
        d.mkdir(parents=True, exist_ok=True)
        html = _shell(
            title=name,
            css="../assets/style.css",
            js="../assets/cricket-stats.js",
            back="../index.html",
            attrs=f'season="2026" src="../data.json" tournament="{slug}"',
        )
        (d / "stats.html").write_text(html)
        print(f"[shell] Tournament → {d / 'stats.html'}")


def generate_per_team_shells(out_dir: str) -> None:
    """Reads data/teams.tsv directly. Removes stale team dirs not in TSV."""
    import shutil
    out = Path(out_dir)
    ids = load_team_ids(_TEAMS_TSV)
    valid_ids = set(ids.values())
    teams_dir = out / "teams"
    if teams_dir.exists():
        for d in teams_dir.iterdir():
            if d.is_dir() and d.name not in valid_ids:
                shutil.rmtree(d)
    for name, tid in ids.items():
        d = out / "teams" / tid
        d.mkdir(parents=True, exist_ok=True)
        html = _shell(
            title=name,
            css="../../assets/style.css",
            js="../../assets/cricket-stats.js",
            back="../../index.html",
            attrs=f'season="2026" src="../../data.json" team="{name}"',
        )
        (d / "index.html").write_text(html)
    print(f"[shell] Teams → {len(ids)} pages")
