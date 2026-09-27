"""Render checked-in SVG previews/icons to PNG for GitHub's README.

Development helper only: pip install pymupdf
The desktop pet itself uses only Python's standard library.
"""

from pathlib import Path

import pymupdf


def main() -> None:
    base = Path(__file__).parent
    sources = [base / "preview.svg", base / "characters-preview.svg", base / "power-preview.svg"]
    sources.extend(sorted((base / "icons").glob("*.svg")))
    for source in sources:
        document = pymupdf.open(source)
        scale = 2 if source.parent == base else 1.5
        document[0].get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False).save(
            source.with_suffix(".png")
        )


if __name__ == "__main__":
    main()
