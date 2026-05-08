"""Extract match details from a scorecard PDF (page 0 only)."""
import re
import sys
import fitz
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))
from utils import apply_corrections, normalize_ground

LABELS = {"Ground", "Date", "Match Result", "Toss", "Total", "Result"}

_SCORE_RE = re.compile(r"(\d+/\d+\s*\(\d+\.?\d*\s*Ov\))")


def parse_tournament(lines: list[str]) -> str:
    """Return the tournament name: first non-empty line after 'Cricket Switzerland'."""
    non_empty = [l.strip() for l in lines if l.strip()]
    for i, line in enumerate(non_empty):
        if line == "Cricket Switzerland" and i + 1 < len(non_empty):
            return non_empty[i + 1]
    return ""


def label_anchored_parse(lines: list[str]) -> dict:
    """Walk lines top-to-bottom; collect value lines under known labels."""
    result = {}
    current_label = None
    current_values = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped in LABELS:
            if current_label and current_label not in {"Match Result", "Toss"}:
                result[current_label] = current_values[:]
            current_label = stripped
            current_values = []
        else:
            inline = next((lbl for lbl in LABELS if stripped.startswith(lbl + " ")), None)
            if inline:
                if current_label and current_label not in {"Match Result", "Toss"}:
                    result[current_label] = current_values[:]
                current_label = inline
                current_values = [stripped[len(inline):].strip()]
            elif current_label:
                current_values.append(stripped)

    if current_label and current_label not in {"Match Result", "Toss"}:
        result[current_label] = current_values[:]

    return result


def parse_date(date_lines: list[str]) -> tuple[str, str]:
    """Split '2026-05-03, 09:58 AM UTC' → ('2026-05-03', '09:58 AM UTC')."""
    if not date_lines:
        return "", ""
    parts = date_lines[0].split(", ", 1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return date_lines[0].strip(), ""


def parse_total(total_lines: list[str]) -> tuple[str, str, str, str]:
    """Extract (team_1st, score_1st, team_2nd, score_2nd) from Total lines."""
    def split_line(line: str) -> tuple[str, str]:
        m = _SCORE_RE.search(line)
        if m:
            return line[:m.start()].strip(), m.group(1).strip()
        return line.strip(), ""

    t1, s1, t2, s2 = "", "", "", ""
    if len(total_lines) >= 1:
        t1, s1 = split_line(total_lines[0])
    if len(total_lines) >= 2:
        t2, s2 = split_line(total_lines[1])
    return t1, s1, t2, s2


def parse(pdf_path: str, debug_dir: str = "tmp") -> dict:
    """Parse match details from page 0 of a scorecard PDF."""
    doc = fitz.open(pdf_path)
    text = doc[0].get_text()

    stem = Path(pdf_path).stem
    Path(debug_dir).mkdir(parents=True, exist_ok=True)
    (Path(debug_dir) / f"{stem}_sc_raw.txt").write_text(text)

    lines = text.splitlines()
    tournament = parse_tournament(lines)
    fields = label_anchored_parse(lines)

    ground_lines = fields.get("Ground", [])
    date_lines = fields.get("Date", [])
    total_lines = fields.get("Total", [])
    result_lines = fields.get("Result", [])

    date, time = parse_date(date_lines)
    team_1st, score_1st, team_2nd, score_2nd = parse_total(total_lines)

    match = {
        "tournament": tournament,
        "date": date,
        "time": time,
        "ground": normalize_ground(apply_corrections(" ".join(ground_lines))),
        "team_1st": apply_corrections(team_1st),
        "score_1st": score_1st,
        "team_2nd": apply_corrections(team_2nd),
        "score_2nd": score_2nd,
        "result": apply_corrections(result_lines[0]) if result_lines else "",
    }

    print(f"[parser] {stem}: {team_1st} vs {team_2nd} → {match['result']}")
    return match
