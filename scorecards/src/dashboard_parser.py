"""Parse Dashboard.pdf to extract upcoming match schedule."""
import sys
from collections import defaultdict
from datetime import datetime, date
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "shared"))

# Column x-boundaries derived from PDF header row
COLS = {
    "date":       (75,  136),
    "time":       (136, 181),
    "home":       (181, 321),
    "away":       (321, 504),
    "ground":     (504, 624),
    "tournament": (624, 900),
}

# Short names in Dashboard → canonical team names used elsewhere
TEAM_ALIAS = {
    "Nomads-Embrach Cricket Acade": "Nomads-Embrach Cricket Academy",
    "Nomads Embrach":               "Nomads-Embrach Cricket Academy",
    "Basel Dragon JCC-2":           "Basel Dragons JCC 2",
    "Basel Dragons CC":             "Basel Dragons JCC",
    "GICC":                         "Geneva International CC",
    "GICC-2":                       "Geneva International CC-2",
    "GESLCC":                       "Geneva Sri Lanka CC",
    "CC Wettingen-1":               "Cricket Club Wettingen-1",
    "CC Wettingen-2":               "Cricket Club Wettingen-2",
    "Geneva Eagles CC":             "Geneva Eagles Cricket Club",
    "CV Zug":                       "CVZ",
    "Luzern CC":                    "Luzern Cricket Club",
    "Zurich Mavericks Adliswil":    "Zurich Mavericks Adliswil CC",
    "Pakhtoon Zalmi":               "Pakhtoon Zalmi CC",
    "Olten Gosgen":                 "Olten Gosgen CC",
    "Sports Club Roche":            "Sports Club Roche Cricket",
    "Zug CC":                       "Zug Cricket Club",
    "Basel Cricket Club":           "Basel CC",
    "Zurich Nomads":                "ZURICH NOMADS",
    "Geneva XI stars":              "Geneva XI Stars",
    "Geneva XI stars - U19":        "Geneva XI Stars - U19",
    "Geneva XI stars U17":          "Geneva XI Stars U17",
    "Zurich Crickets CC 1":         "Zurich Crickets CC-1",
    "Bern CC":                      "Berne CC",
}

GROUND_MAP = {
    "Deutweg":               "Deutweg, Winterthur",
    "Baumlihof":             "Baumlihof, Basel",
    "Bachgraben":            "Bachgraben, Basel",
    "Bout du Monde":         "Bout-du-monde, Geneva (Switzerland)",
    "Luzern Cricket Ground": "Luzern Cricket Ground, Luzern",
    "Embrach Cricket Ground":"Embrach Cricket Ground, Zurich",
    "Obergosgen":            "Obergosgen, Solothurn",
    "Brugg":                 "Brugg, Aargau",
    "Birsfelden":            "Birsfelden, Basel",
    "Kantonsschule-Solothurn":"Kantonsschule Solothurn, Solothurn",
    "Kreuzzleg Wettingen":   "Kreuzzleg, Aargau",
    "En Marche":             "En Marche, Cossonay",
    "Schonau":               "Schonau, Bern",
    "Hunnenberg":            "Hunnenberg, Zug",
    "Hedingen":              "Hedingen, Zurich",
    "Pfaffikon":             "Pfaffikon, Zurich",
    "Tufi":                  "Tufi, Zurich",
    "Onex":                  "Onex, Geneva",
    "En Prevessin":          "En Prevessin, Geneva",
    "Chopfli Athletic Field":"Chopfli Athletic Field, Geneva",
    "Grundenmoos":           "Grundenmoos, St. Gallen",
    "Staad-SG":              "Staad, St. Gallen",
    "Other":                 "Unknown",
}

TOURN_MAP = {
    "CricketerPro":       "CRICKETER PRO T20 COMPETITION (DIVISION 2)-2026",
    "PickWick":           "PICKWICK CUP T20 COMPETITIONS (ELITE DIVISION)-2026",
    "CSRL":               "CRICKET SWITZERLAND REGIONAL LEAGUE ( CSRL)-2026",
    "CSNL":               "CRICKET SWITZERLAND NATIONAL LEAGUE ( CSNL)-2026",
    "CSPL":               "CRICKET SWITZERLAND PREMIER LEAGUE ( CSPL)-2026",
    "CSWL T20":           "CRICKET SWITZERLAND WOMEN T20 LEAGUE (CSWL T20)",
    "CSWL T20 ":          "CRICKET SWITZERLAND WOMEN T20 LEAGUE (CSWL T20)",
    "CSWL T10":           "CRICKET SWITZERLAND WOMEN T10 LEAGUE 2026 (CSWL T10)",
    "CSYL U19":           "CRICKET SWITZERLAND YOUTH LEAGUE (CSYL 2026)",
    "T20 U19":            "CRICKET SWITZERLAND T20 U19 (League Matches)",
    "CSYL U17 20 overs":  "CRICKET SWITZERLAND YOUTH LEAGUE (CSYL U17 20 overs)",
    "CSYL U17 50 overs":  "CRICKET SWITZERLAND YOUTH LEAGUE (CSYL U17 50 overs)",
}

IGNORE_TOURNAMENTS = {"DBMT 2026"}


def _col_for_x(x):
    for col, (lo, hi) in COLS.items():
        if lo <= x < hi:
            return col
    return None


def _parse_date(s):
    try:
        d = datetime.strptime(f"{s.strip()}-2026", "%d-%b-%Y")
        return date(2026, d.month, d.day)
    except Exception:
        return None


def parse_dashboard(pdf_path, cutoff_date):
    """Return list of upcoming match dicts from Dashboard.pdf, date >= cutoff_date."""
    doc = fitz.open(str(pdf_path))
    upcoming = []

    for page in doc:
        paths = page.get_drawings()
        struck_ys = {p["rect"].y0 for p in paths if p["rect"].height < 2}

        char_list = []
        for b in page.get_text("rawdict")["blocks"]:
            if b["type"] != 0:
                continue
            for line in b["lines"]:
                for span in line["spans"]:
                    for ch in span["chars"]:
                        cx = (ch["bbox"][0] + ch["bbox"][2]) / 2
                        cy = (ch["bbox"][1] + ch["bbox"][3]) / 2
                        char_list.append((cx, cy, ch["c"]))

        rows_chars = defaultdict(list)
        for cx, cy, c in char_list:
            rows_chars[round(cy / 5) * 5].append((cx, cy, c))

        for y_key in sorted(rows_chars.keys()):
            chars = sorted(rows_chars[y_key], key=lambda t: t[0])

            cols_text = defaultdict(list)
            for cx, cy, c in chars:
                col = _col_for_x(cx)
                if col:
                    cols_text[col].append((cx, c))
            row = {col: "".join(c for _, c in sorted(pairs)) for col, pairs in cols_text.items()}

            date_raw = row.get("date", "").strip()
            if date_raw.startswith("Date") or not date_raw:
                continue

            actual_y = rows_chars[y_key][0][1]
            if any(abs(sy - actual_y) < 5 for sy in struck_ys):
                continue  # cancelled

            d = _parse_date(date_raw)
            if not d or d < cutoff_date:
                continue

            tourn_raw = row.get("tournament", "").strip()
            if tourn_raw in IGNORE_TOURNAMENTS:
                continue

            time_str = row.get("time", "").strip()
            if time_str == "-":
                time_str = "TBD"

            home_raw = row.get("home", "").strip()
            away_raw = row.get("away", "").strip()

            upcoming.append({
                "tournament": TOURN_MAP.get(tourn_raw, tourn_raw),
                "date":       str(d),
                "time":       time_str,
                "ground":     GROUND_MAP.get(row.get("ground", "").strip(), row.get("ground", "").strip()),
                "home_team":  TEAM_ALIAS.get(home_raw, home_raw),
                "away_team":  TEAM_ALIAS.get(away_raw, away_raw),
            })

    return upcoming
