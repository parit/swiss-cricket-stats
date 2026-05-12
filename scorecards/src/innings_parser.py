"""Parse full innings details (batting + bowling) from scorecard PDFs (pages 2+)."""
import re
import fitz

_INNINGS_HDR = re.compile(r'^(.+?)\s+(\d+/\d+)\s+\(([\d.]+)\s+Ov\)\s+\((1st|2nd) Innings\)$')
_HAND        = re.compile(r'^(.+?)\s+\(([LR]HB)\)$')
_EXTRAS      = re.compile(r'^Extras:\s*(?:\(([^)]*)\))?$')
_TOTAL       = re.compile(r'^Total:\s*Overs\s+([\d.]+),\s*Wickets\s+(\d+)$')
_TOTAL_RUNS  = re.compile(r'^(\d+)\s+\(CRR:\s*([\d.]+)\)$')


def _parse_extras(raw):
    out = {}
    for part in raw.split(','):
        p = part.strip().split()
        if len(p) == 2:
            out[p[0]] = int(p[1])
    return out


def _is_header(line, keyword):
    """Match column header lines like 'Batsman', 'No Batsman', 'Bowler', 'No Bowler'."""
    return line == keyword or line == f"No {keyword}"


def parse_innings(pdf_path: str) -> list[dict]:
    """Return a list of innings dicts (one per innings page) from a scorecard PDF."""
    doc = fitz.open(pdf_path)
    innings_list = []

    for page_num in range(2, len(doc)):
        lines = [l.strip() for l in doc[page_num].get_text().splitlines() if l.strip()]

        innings = None
        state = "SKIP"
        bat_buf = []
        bowl_buf = []

        i = 0
        while i < len(lines):
            line = lines[i]

            # innings header
            m = _INNINGS_HDR.match(line)
            if m:
                innings = {
                    "team": m.group(1).strip(),
                    "score": m.group(2),
                    "overs": m.group(3),
                    "batting": [],
                    "extras": {},
                    "total": {},
                    "fall_of_wickets": "",
                    "bowling": [],
                }
                state = "AFTER_HEADER"
                i += 1
                continue

            if innings is None:
                i += 1
                continue

            # bowling header (check before batting — both may start with "No")
            if _is_header(line, "Bowler"):
                state = "SKIP_BOWL_HDR"
                bowl_buf = []
                i += 1
                continue

            # batting header
            if state == "AFTER_HEADER" and _is_header(line, "Batsman"):
                state = "SKIP_BAT_HDR"
                bat_buf = []
                i += 1
                continue

            # skip remaining column header lines, enter section on first integer row
            if state == "SKIP_BAT_HDR":
                if line.isdigit():
                    state = "BATTING"
                    bat_buf = [line]
                i += 1
                continue

            if state == "SKIP_BOWL_HDR":
                if line.isdigit():
                    state = "BOWLING"
                    bowl_buf = [line]
                i += 1
                continue

            if state == "BATTING":
                if line.startswith("Extras:"):
                    state = "EXTRAS"
                    # fall through to EXTRAS handler below
                else:
                    bat_buf.append(line)
                    if len(bat_buf) == 9:
                        hm = _HAND.match(bat_buf[1])
                        innings["batting"].append({
                            "no":      int(bat_buf[0]),
                            "name":    hm.group(1).strip() if hm else bat_buf[1],
                            "hand":    hm.group(2) if hm else "",
                            "status":  bat_buf[2],
                            "runs":    int(bat_buf[3]),
                            "balls":   int(bat_buf[4]),
                            "minutes": int(bat_buf[5]),
                            "fours":   int(bat_buf[6]),
                            "sixes":   int(bat_buf[7]),
                            "sr":      float(bat_buf[8]),
                        })
                        bat_buf = []
                    i += 1
                    continue

            if state == "EXTRAS":
                m2 = _EXTRAS.match(line)
                if m2:
                    innings["extras"] = _parse_extras(m2.group(1) or "")
                    state = "EXTRAS_TOTAL"
                i += 1
                continue

            if state == "EXTRAS_TOTAL":
                if line.isdigit():
                    innings["extras"]["total"] = int(line)
                    state = "TOTAL"
                i += 1
                continue

            if state == "TOTAL":
                m3 = _TOTAL.match(line)
                if m3:
                    innings["total"]["overs"]   = m3.group(1)
                    innings["total"]["wickets"] = int(m3.group(2))
                    state = "TOTAL_RUNS"
                i += 1
                continue

            if state == "TOTAL_RUNS":
                m4 = _TOTAL_RUNS.match(line)
                if m4:
                    innings["total"]["runs"] = int(m4.group(1))
                    innings["total"]["crr"]  = float(m4.group(2))
                    state = "PRE_FOW"
                i += 1
                continue

            if state == "PRE_FOW":
                # skip "To Bat:" and any continuation lines until "Fall of Wickets"
                if line == "Fall of Wickets":
                    state = "FOW"
                i += 1
                continue

            if state == "FOW":
                if line != "-" and not _is_header(line, "Bowler"):
                    innings["fall_of_wickets"] += (" " if innings["fall_of_wickets"] else "") + line
                i += 1
                continue

            if state == "BOWLING":
                bowl_buf.append(line)
                if len(bowl_buf) == 12:
                    innings["bowling"].append({
                        "no":      int(bowl_buf[0]),
                        "name":    bowl_buf[1],
                        "overs":   bowl_buf[2],
                        "maidens": int(bowl_buf[3]),
                        "runs":    int(bowl_buf[4]),
                        "wickets": int(bowl_buf[5]),
                        "dots":    int(bowl_buf[6]),
                        "fours":   int(bowl_buf[7]),
                        "sixes":   int(bowl_buf[8]),
                        "wides":   int(bowl_buf[9]),
                        "noballs": int(bowl_buf[10]),
                        "eco":     float(bowl_buf[11]),
                    })
                    bowl_buf = []
                i += 1
                continue

            i += 1

        if innings:
            _ordinals = ["1st", "2nd", "3rd", "4th"]
            innings["innings"] = _ordinals[len(innings_list)] if len(innings_list) < 4 else f"{len(innings_list)+1}th"
            innings_list.append(innings)

    return innings_list


if __name__ == "__main__":
    import json, sys
    path = sys.argv[1] if len(sys.argv) > 1 else \
        "data/scorecards/cricket_switzerland_premier_league_cspl_2026/Scorecard_24551286.pdf"
    result = parse_innings(path)
    print(json.dumps(result, indent=2))
