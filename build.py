"""Build all output HTML. Run with: python3 build.py"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "shared"))
from stats_generator import generate_stats, generate_per_tournament_stats, generate_per_team_stats

OUT_DIR = ROOT / "output" / "2026"
TMP_DIR = ROOT / "tmp"


def _run(script: Path):
    subprocess.run([sys.executable, str(script)], check=True)


def _copy_assets():
    import shutil
    dest = OUT_DIR / "assets"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(ROOT / "assets", dest)
    print(f"[build] Assets → {dest.relative_to(ROOT)}")


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
    pt_tournaments = [(e["title"], e["data"]) for e in json.loads((TMP_DIR / "pt_manifest.json").read_text())]
    sc_manifest = json.loads((TMP_DIR / "sc_manifest.json").read_text())
    sc_past     = sc_manifest["past"]
    sc_upcoming = sc_manifest.get("upcoming", [])

    generate_stats(pt_tournaments, sc_past, sc_upcoming, out_dir=str(OUT_DIR))
    generate_per_tournament_stats(pt_tournaments, sc_past, sc_upcoming, out_dir=str(OUT_DIR))
    generate_per_team_stats(pt_tournaments, sc_past, sc_upcoming, out_dir=str(OUT_DIR))

    print()
    print("=" * 50)
    print("ASSETS + CLEANUP")
    print("=" * 50)
    _copy_assets()
    _cleanup_old_files()

    print("\n[build] Done.")
