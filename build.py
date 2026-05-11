"""Build all output HTML. Run with: python3 build.py"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "shared"))
sys.path.insert(0, str(ROOT / "scorecards" / "src"))
from shell_generator import generate_combined_shell, generate_per_tournament_shells, generate_per_team_shells
from utils import normalize_tournament, title_to_folder
from data_generator import generate_data_json
from innings_parser import parse_innings

OUT_DIR = ROOT / "output" / "2026"
TMP_DIR = ROOT / "tmp"


def _run(script: Path):
    subprocess.run([sys.executable, str(script)], check=True)


def _component_demo_html(season: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Cricket Switzerland Stats — Web Component Demo</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: Arial, sans-serif; background: #f4f4f4; padding: 24px; color: #222; }}
    h1 {{ font-size: 1.2rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px; }}
    .subtitle {{ font-size: 0.85rem; color: #666; margin-bottom: 24px; }}
    cricket-stats {{ display: block; max-width: 1200px; }}
  </style>
</head>
<body>
  <h1>Cricket Switzerland Stats {season}</h1>
  <p class="subtitle">Embedded via &lt;cricket-stats&gt; web component &mdash; no framework required.</p>
  <script src="cricket-stats.js"></script>
  <cricket-stats season="{season}"></cricket-stats>
</body>
</html>"""


def _copy_assets():
    import shutil
    dest = OUT_DIR / "assets"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(ROOT / "assets", dest)

    # Remove stale root-level cricket-stats.js (moved to component/)
    stale = OUT_DIR.parent / "cricket-stats.js"
    if stale.exists():
        stale.unlink()

    comp_dir = OUT_DIR.parent / "component"
    comp_dir.mkdir(exist_ok=True)
    shutil.copy(ROOT / "assets" / "cricket-stats.js", comp_dir / "cricket-stats.js")

    season = OUT_DIR.name
    (comp_dir / "index.html").write_text(_component_demo_html(season))
    print(f"[build] Assets → {dest.relative_to(ROOT)}")
    print(f"[build] Component → {comp_dir.relative_to(ROOT)}")



def _cleanup_old_files():
    import shutil
    removed = []
    for pattern in ["points_table.html", "scorecards.html", "season-*.html"]:
        for f in OUT_DIR.rglob(pattern):
            f.unlink()
            removed.append(f.relative_to(ROOT))
    # Remove slug-named team dirs (old format — now use numeric IDs)
    teams_dir = OUT_DIR / "teams"
    if teams_dir.exists():
        for d in teams_dir.iterdir():
            if d.is_dir() and not d.name.isdigit():
                shutil.rmtree(d)
                removed.append(d.relative_to(ROOT))
    if removed:
        print(f"[build] Removed {len(removed)} old file(s)/dir(s)")


def generate_scorecard_jsons(sc_manifest: dict, out_dir: Path, data_dir: Path) -> None:
    """Write output/2026/scorecards/<scorecard_id>.json for each past match with a PDF."""
    sc_dir = out_dir / "scorecards"
    sc_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    for m in sc_manifest.get("past", []):
        sid = m.get("scorecard_id")
        if not sid:
            continue
        pdfs = list(data_dir.rglob(f"{sid}.pdf"))
        if not pdfs:
            print(f"[scorecard] WARNING: PDF not found for {sid}")
            continue
        try:
            innings = parse_innings(str(pdfs[0]))
        except Exception as e:
            print(f"[scorecard] WARNING: innings parse failed for {sid}: {e}")
            continue
        match_fields = {k: v for k, v in m.items() if k != "scorecard_id"}
        payload = {"match": match_fields, "innings": innings}
        (sc_dir / f"{sid}.json").write_text(json.dumps(payload, indent=2))
        written += 1
    print(f"[scorecard] {written} scorecard JSON(s) → {sc_dir.relative_to(out_dir.parent.parent)}")


if __name__ == "__main__":
    print("=" * 50)
    print("POINTS TABLE — parse")
    print("=" * 50)
    _run(ROOT / "points_table" / "src" / "main.py")

    print()
    print("=" * 50)
    print("SCORECARDS — parse")
    print("=" * 50)
    _run(ROOT / "scorecards" / "src" / "main.py")

    print()
    print("=" * 50)
    print("GENERATE HTML")
    print("=" * 50)
    pt_tournaments_raw = json.loads((TMP_DIR / "pt_manifest.json").read_text())
    pt_tournaments = [(e["title"], e["data"]) for e in pt_tournaments_raw]
    sc_manifest = json.loads((TMP_DIR / "sc_manifest.json").read_text())
    sc_past     = sc_manifest["past"]
    sc_upcoming = sc_manifest.get("upcoming", [])

    all_tourn_names = sorted(
        {normalize_tournament(t) for t, _ in pt_tournaments} |
        {normalize_tournament(m["tournament"]) for m in sc_past + sc_upcoming}
    )
    tournaments = [(name, title_to_folder(name)) for name in all_tourn_names]
    generate_combined_shell(out_dir=str(OUT_DIR))
    generate_per_tournament_shells(tournaments, out_dir=str(OUT_DIR))
    generate_per_team_shells(out_dir=str(OUT_DIR))
    generate_data_json(pt_tournaments_raw, sc_manifest, out_dir=str(OUT_DIR))
    generate_scorecard_jsons(sc_manifest, out_dir=OUT_DIR, data_dir=ROOT / "data" / "scorecards")

    print()
    print("=" * 50)
    print("ASSETS + CLEANUP")
    print("=" * 50)
    _copy_assets()
    _cleanup_old_files()

    print("\n[build] Done.")
