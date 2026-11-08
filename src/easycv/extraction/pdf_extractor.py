"""PDF text and link extraction using PyMuPDF.

For native PDFs (created from Word, LaTeX, etc.), text extraction works well.
Scanned PDFs (images) will return empty or minimal text; handling those with
vision models is a future enhancement.
"""

from pathlib import Path
from typing import Any

import pymupdf
from pymupdf import Document, Page, Rect

from easycv.schemas import ExtractedDocument, ExtractedLink, ExtractedPage

# PyMuPDF doesn't have complete type stubs, so we need some type: ignore comments


def extract_pdf(source: Path | bytes) -> ExtractedDocument:
    """Extract text and links from a PDF document.

    Args:
        source: Either a path to a PDF file or raw PDF bytes.

    Returns:
        ExtractedDocument containing all pages with their text and links.

    Raises:
        FileNotFoundError: If source is a Path that doesn't exist.
        pymupdf.FileDataError: If the PDF is corrupted or invalid.
    """
    doc = _open_document(source)

    try:
        extracted_pages: list[ExtractedPage] = []
        for page_num, page in enumerate(doc, start=1):  # type: ignore[arg-type, var-annotated]
            extracted_pages.append(_extract_page(page, page_num))
        pages = tuple(extracted_pages)
    finally:
        doc.close()  # type: ignore[no-untyped-call]

    return ExtractedDocument(pages=pages)


def _open_document(source: Path | bytes) -> Document:
    """Open a PDF document from path or bytes."""
    if isinstance(source, Path):
        if not source.exists():
            raise FileNotFoundError(f"PDF file not found: {source}")
        return pymupdf.open(source)  # type: ignore[no-untyped-call]

    # For bytes, PyMuPDF needs filetype hint
    return pymupdf.open(stream=source, filetype="pdf")  # type: ignore[no-untyped-call]


def _extract_page(page: Page, page_number: int) -> ExtractedPage:
    """Extract content from a single page."""
    text: str = page.get_text("text")  # type: ignore[no-untyped-call]
    links = tuple(_extract_links(page))

    return ExtractedPage(
        page_number=page_number,
        text=text,
        links=links,
    )


def _extract_links(page: Page) -> list[ExtractedLink]:
    """Extract all hyperlinks from a page with their anchor text.

    PyMuPDF's get_links() returns link annotations with their bounding rectangles.
    We use those rectangles to find the text underneath each link.
    """
    links: list[ExtractedLink] = []

    for link in page.get_links():
        # Skip non-URL links (e.g., internal page references)
        if "uri" not in link:
            continue

        url = link["uri"]
        anchor_text = _get_anchor_text(page, link)

        links.append(ExtractedLink(url=url, anchor_text=anchor_text))

    return links


def _get_anchor_text(page: Page, link: dict[str, Any]) -> str | None:
    """Extract the visible text under a link's bounding rectangle.

    Args:
        page: The page containing the link.
        link: Link dict from PyMuPDF with 'from' key containing the rectangle.

    Returns:
        The text found in the link area, stripped and normalized.
        None if no text is found (e.g., image links, icons).
    """
    # 'from' contains the link's bounding rectangle as (x0, y0, x1, y1)
    if "from" not in link:
        return None

    rect = Rect(link["from"])  # type: ignore[no-untyped-call]
    text: str = page.get_text("text", clip=rect).strip()  # type: ignore[no-untyped-call]

    # Normalize whitespace (links often span multiple lines)
    if text:
        return " ".join(text.split())

    return None
