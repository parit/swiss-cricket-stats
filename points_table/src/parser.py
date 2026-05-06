"""OCR the table image and parse into structured data."""
import re
import json
import pytesseract
from PIL import Image
from pathlib import Path


HEADERS = ["#", "Team", "M", "W", "L", "D", "T", "NR", "NRR", "For", "Against", "Pt.", "Last 5"]
NUMERIC_COLS = {"#", "M", "W", "L", "D", "T", "NR", "NRR", "Pt."}


def ocr_image(image_path: str) -> str:
    img = Image.open(image_path)
    # PSM 6 = assume uniform block of text
    text = pytesseract.image_to_string(img, config="--psm 6")
    print(f"[parser] OCR complete, {len(text)} chars")
    return text


def is_row_start(token: str) -> bool:
    """True if token looks like a row number (1-20)."""
    return re.fullmatch(r"\d{1,2}", token) is not None


STAT_COLS = ["M", "W", "L", "D", "T", "NR", "NRR", "For", "Against", "Pt.", "Last 5"]
STATS_BEFORE_FOR = 7  # M W L D T NR NRR


def parse_row(tokens: list[str]) -> dict | None:
    """Parse tokens into a row dict.

    Anchor strategy: locate the "For" column by finding the first token that
    contains "/" (runs/overs format) or is "-" preceded by a numeric token.
    The team name occupies everything before (for_idx - STATS_BEFORE_FOR).
    """
    tokens = [clean_token(t) for t in tokens]
    if not tokens or not is_row_start(tokens[0]):
        return None

    row = {"#": tokens[0]}
    data = tokens[1:]  # everything after the row number

    # Locate For column: primary anchor = first "/" or "-" after a numeric token
    for_idx = None
    for i, t in enumerate(data):
        if "/" in t:
            for_idx = i
            break
        if t == "-" and i > 0 and re.fullmatch(r"-?\d+(\.\d+)?", data[i - 1]):
            for_idx = i
            break

    # Fallback: For/Against both OCR'd as single digits (no - or / present).
    # Detect by scanning from the right: last token is Pt. (0|10) or Last5 (alpha).
    if for_idx is None:
        last = data[-1]
        has_last5 = bool(re.fullmatch(r"[WLwl][\-WLwl]*", last))
        stats_count = 11 if has_last5 else 10
        stats_start_fb = len(data) - stats_count
        if stats_start_fb >= 0:
            for_idx = stats_start_fb + STATS_BEFORE_FOR

    if for_idx is None or for_idx < STATS_BEFORE_FOR:
        return None

    stats_start = for_idx - STATS_BEFORE_FOR
    row["Team"] = " ".join(data[:stats_start])

    stat_tokens = data[stats_start:]
    for col, val in zip(STAT_COLS, stat_tokens):
        row[col] = val
    for col in STAT_COLS[len(stat_tokens):]:
        row[col] = ""

    return row


def clean_token(t: str) -> str:
    """Fix per-token OCR misreads."""
    t = t.strip()
    if t in ("©", "c", "C"):
        return "-"
    if t in ("WwW", "Ww"):
        return "W"
    if t in ("LL",):
        return "L-L"
    # NRR=0 rendered in red → OCR misreads: (0) i) 1) () 0) etc
    if re.fullmatch(r"[\(\[]?[0oi1l][\)\]]+", t, re.IGNORECASE):
        return "0"
    return t


def clean_ocr_artifacts(text: str) -> str:
    """Fix known OCR misreads at line level."""
    # '5' alone as a stat value where '-' expected is caught per-token in parse_row
    text = re.sub(r"\bLL\b", "L-L", text)
    return text


def split_groups(text: str) -> dict[str, list[str]]:
    """Split OCR text into groups by detecting row-number reset (7 → 1)."""
    text = clean_ocr_artifacts(text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    groups = {}
    group_labels = ["Group A", "Group B", "Group C", "Group D"]
    current_group_idx = 0
    current_lines = []
    last_row_num = 0

    for line in lines:
        tokens = line.split()
        if not tokens:
            continue
        if re.fullmatch(r"\d{1,2}", tokens[0]):
            row_num = int(tokens[0])
            # Row number reset = new group
            if row_num <= last_row_num and current_lines:
                groups[group_labels[current_group_idx]] = current_lines
                current_group_idx += 1
                current_lines = []
            last_row_num = row_num
            current_lines.append(line)

    if current_lines:
        groups[group_labels[current_group_idx]] = current_lines

    return groups


def validate_row(row: dict) -> dict:
    """Fix values that are impossible given context."""
    # For/Against must be "NNN/NN" or "-"; single digits are OCR artifacts
    for col in ("For", "Against"):
        val = row.get(col, "")
        if val and re.fullmatch(r"\d{1,3}", val):
            row[col] = "-"
    return row


def parse_group(lines: list[str]) -> list[dict]:
    rows = []
    for line in lines:
        tokens = line.split()
        row = parse_row(tokens)
        if row:
            rows.append(validate_row(row))
    return rows


def parse(image_path: str, debug_dir: str = "tmp") -> dict:
    text = ocr_image(image_path)

    stem = Path(image_path).stem
    raw_path = str(Path(debug_dir) / f"{stem}_ocr_raw.txt")
    Path(debug_dir).mkdir(parents=True, exist_ok=True)
    Path(raw_path).write_text(text)
    print(f"[parser] Raw OCR saved → {raw_path}")

    groups_raw = split_groups(text)
    print(f"[parser] Groups found: {list(groups_raw.keys())}")

    result = {}
    for group_name, lines in groups_raw.items():
        rows = parse_group(lines)
        result[group_name] = rows
        print(f"[parser] {group_name}: {len(rows)} rows parsed")

    return result


if __name__ == "__main__":
    import json
    data = parse("tmp/points_table.png")
    print(json.dumps(data, indent=2))
