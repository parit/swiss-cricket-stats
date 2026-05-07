# Swiss Cricket Stats — Season 2026

Automated pipeline that parses Cricket Switzerland data from PDFs and publishes clean HTML pages and an embeddable web component via GitHub Pages.

## What It Produces

| Output | URL | Content |
|--------|-----|---------|
| Combined page | `/2026/index.html` | All tournaments — dropdown + Points Table / Matches tabs |
| Per-tournament | `/2026/<slug>/stats.html` | Single tournament — PT standings + past/upcoming matches |
| Per-team | `/2026/teams/<id>/index.html` | Single team — their matches + PT rows |
| Data file | `/2026/data.json` | All data merged — consumed by the web component |
| Web component | `/component/cricket-stats.js` | Embeddable `<cricket-stats>` Custom Element |
| Demo page | `/component/` | Live demo of the web component |

All HTML pages share a **list / card view** toggle and a **team filter** dropdown.

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

Runs both parse pipelines, generates all HTML pages, `data.json`, and the component demo. Cleans up stale files.

## Data Inputs

| Path | Purpose | Committed? |
|------|---------|-----------|
| `data/points_table/*.pdf` | Points table PDFs | No |
| `data/scorecards/<tournament>/*.pdf` | Scorecard PDFs | No |
| `data/scorecards/schedule.json` | Full match schedule (350 entries) | Yes |
| `data/teams.tsv` | Team ID ↔ name registry | Yes |
| `data/tournament_abbreviations.tsv` | Tournament short labels | Yes |
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

## Web Component

Embed Cricket Switzerland stats in any webpage — no server, no framework, no dependencies.

**Live demo:** `https://<you>.github.io/swiss-cricket-stats/component/`

**Include the component:**
```html
<script src="https://<you>.github.io/swiss-cricket-stats/component/cricket-stats.js"></script>
```

**Embed (season auto-resolves `data.json` from script location):**
```html
<cricket-stats season="2026"></cricket-stats>
```

**Explicit base URL (when hosted on a different domain):**
```html
<cricket-stats
  base-url="https://<you>.github.io/swiss-cricket-stats"
  season="2026">
</cricket-stats>
```

**Fully explicit src (overrides season/base-url):**
```html
<cricket-stats
  src="https://<you>.github.io/swiss-cricket-stats/2026/data.json">
</cricket-stats>
```

**Pre-select a tournament (optional):**
```html
<cricket-stats season="2026" tournament="csrl"></cricket-stats>
```

**Theme with CSS custom properties:**
```css
cricket-stats {
  --cs-accent:  #e74c3c;   /* brand colour */
  --cs-bg:      #1a1a2e;   /* page background */
  --cs-surf:    #16213e;   /* card/table background */
  --cs-text:    #eee;      /* body text */
}
```

**Attribute reference:**

| Attribute | Required | Description |
|-----------|----------|-------------|
| `season` | one of `season`/`src` | Season year — component resolves `{base-url}/{season}/data.json` |
| `base-url` | No | Base URL override; defaults to script directory parent |
| `src` | one of `season`/`src` | Explicit full URL to `data.json`; overrides `season`/`base-url` |
| `tournament` | No | Slug fragment to pre-select on load (e.g. `csrl`) |

**Data file URL pattern:** `https://<you>.github.io/<repo>/<season>/data.json`

## Local Preview

Serve the site locally — mirrors the GitHub Pages structure exactly:

```bash
python3 -m http.server 8000 --directory output
```

Then open:
- Combined: `http://localhost:8000/2026/`
- Per-tournament: `http://localhost:8000/2026/<slug>/stats.html`
- Per-team: `http://localhost:8000/2026/teams/<id>/`
- Web component demo: `http://localhost:8000/component/`

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

| File | Tests | What it covers |
|------|-------|---------------|
| `tests/test_stats_html.py` | 43 | HTML structure, tournament completeness, per-tournament/team pages, schedule consistency |
| `tests/test_data_json.py` | 9 | `data.json` schema, match counts, abbreviations |
| `tests/test_component.py` | 44 | Component files, JS structure and features, data↔component consistency |
| `tests/scorecards/test_generator.py` | 24 | Scorecard HTML rendering primitives incl. links, tournament pills, cards |
| `tests/scorecards/test_parser.py` | 10 | Scorecard PDF label-anchored parser |
| `tests/shared/test_utils.py` | 6 | `title_to_folder()` slug generation |

## Theming

**Static pages** — all colours are CSS variables in `assets/style.css`. Edit `:root` to restyle all pages at once — never modify it programmatically.

```css
:root {
  --group-header-bg: #00b5ad;   /* brand accent */
  --page-bg:         #f4f4f4;
  --nrr-pos-color:   #27ae60;
  --nrr-neg-color:   #e74c3c;
}
```

**Web component** — override via CSS custom properties on the element (see Web Component section above).
