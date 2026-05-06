"""Extract the main table image and title from a PDF."""
import fitz
from pathlib import Path


def extract(pdf_path: str, tmp_dir: str = "tmp") -> tuple[str, str]:
    """Return (image_path, title) for the given PDF."""
    doc = fitz.open(pdf_path)
    page = doc[0]

    # Extract title from text blocks
    title = ""
    for block in page.get_text("dict")["blocks"]:
        if block["type"] == 0:  # text
            for line in block["lines"]:
                for span in line["spans"]:
                    t = span["text"].strip()
                    if t:
                        title = t
                        break

    # Extract largest image (the points table)
    images = page.get_images(full=True)
    largest = max(images, key=lambda img: doc.extract_image(img[0])["width"])
    xref = largest[0]
    img_data = doc.extract_image(xref)

    stem = Path(pdf_path).stem
    img_path = str(Path(tmp_dir) / f"{stem}.png")
    Path(tmp_dir).mkdir(parents=True, exist_ok=True)
    with open(img_path, "wb") as f:
        f.write(img_data["image"])

    print(f"[extractor] {stem}: title={repr(title)}, image={img_data['width']}x{img_data['height']} → {img_path}")
    return img_path, title


if __name__ == "__main__":
    extract("data/points_table.pdf")
