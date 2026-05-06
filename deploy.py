"""Deploy output/ to the gh-pages branch.

Run after build.py:
    python3 deploy.py
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT   = Path(__file__).parent
OUTPUT = ROOT / "output"


def run(cmd, cwd):
    subprocess.run(cmd, check=True, cwd=cwd)


def main():
    if not OUTPUT.exists():
        print("[deploy] output/ not found — run python3 build.py first")
        sys.exit(1)

    try:
        remote = subprocess.check_output(
            ["git", "remote", "get-url", "origin"], cwd=ROOT
        ).decode().strip()
    except subprocess.CalledProcessError:
        print("[deploy] No git remote 'origin' found — add one first:")
        print("  git remote add origin https://github.com/<you>/swiss-cricket-stats.git")
        sys.exit(1)

    with tempfile.TemporaryDirectory() as tmp:
        site = Path(tmp) / "site"
        shutil.copytree(OUTPUT, site)

        run(["git", "init", "-b", "gh-pages"], cwd=site)
        run(["git", "add", "."],               cwd=site)
        run(["git", "commit", "-m", "Deploy"], cwd=site)
        run(["git", "remote", "add", "origin", remote], cwd=site)
        run(["git", "push", "-f", "origin", "gh-pages"], cwd=site)

    print("[deploy] Done — gh-pages branch updated")


if __name__ == "__main__":
    main()
