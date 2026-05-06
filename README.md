# Swiss Cricket Stats — Season 2026

Automated pipeline that parses Cricket Switzerland data from PDFs and publishes clean HTML pages via GitHub Pages.

## What It Produces

| Page | URL | Content |
|------|-----|---------|
| Combined | `/output/2026/index.html` | All tournaments — dropdown + Points Table / Matches tabs |
| Per-tournament | `/output/<slug>/stats.html` | Single tournament — PT standings + past/upcoming matches |
| Per-team | `/output/teams/<id>/index.html` | Single team — their matches + PT rows |

All pages share a **list / card view** toggle and a **team filter** dropdown.

## Setup

**System dependency (OCR for points table PDFs):**
```bash
sudo apt install tesseract-ocr   # Debian/Ubuntu
sudo dnf install tesseract       # RHEL/Fedora
```

**Python dependencies:**
```bash
pip install pymupdf pytesseract pillow
```

## Build

```bash
python3 build.py
```

Runs both parse pipelines, generates all HTML pages, and cleans up stale files.

## Data Inputs

| Path | Purpose | Committed? |
|------|---------|-----------|
| `data/points_table/*.pdf` | Points table PDFs | No |
| `data/scorecards/<tournament>/*.pdf` | Scorecard PDFs | No |
| `data/scorecards/schedule.json` | Full match schedule (350 entries) | Yes |
| `data/teams.tsv` | Team ID ↔ name registry | Yes |
| `data/dashboard-2026.pdf` | Source for schedule (one-time use) | No |

## Managing the Schedule

```bash
# List matches
python3 scorecards/src/schedule_manager.py list
python3 scorecards/src/schedule_manager.py list --tournament CSRL
python3 scorecards/src/schedule_manager.py list --date 2026-06-07

# Add a match
python3 scorecards/src/schedule_manager.py add \
  --date 2026-06-07 --time 11:00 \
  --home "Basel CC" --away "Geneva CC" \
  --ground "Bachgraben, Basel" \
  --tournament "CRICKET SWITZERLAND PREMIER LEAGUE ( CSPL)-2026"

# Remove a match by id
python3 scorecards/src/schedule_manager.py remove --id 42
```

Past vs upcoming is determined automatically: a schedule entry is **past** once a matching scorecard PDF is added and the build runs.

## Adding Scorecards

Drop new scorecard PDFs into `data/scorecards/<tournament>/` and re-run `python3 build.py`. Matched schedule entries move from Upcoming to Past automatically.

## Deploy to GitHub Pages

```bash
python3 build.py    # generate output/
python3 deploy.py   # push output/ → gh-pages branch
```

First time only — enable Pages in GitHub: Settings → Pages → Branch: `gh-pages`, folder: `/ (root)`.

Site URL: `https://<you>.github.io/swiss-cricket-stats/2026/`

## Tests

Run after every build:
```bash
python3 -m pytest tests/ -v
```

`tests/test_stats_html.py` covers 24 QA checks: HTML structure, tournament completeness, per-tournament pages, per-team pages, and schedule/manifest consistency.

## Theming

All colours are CSS variables in `assets/style.css`. Edit `:root` to restyle all pages at once — never modify it programmatically.

```css
:root {
  --group-header-bg: #00b5ad;   /* brand accent */
  --page-bg:         #f4f4f4;
  --nrr-pos-color:   #27ae60;
  --nrr-neg-color:   #e74c3c;
}
```
