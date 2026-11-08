"""Data structures for extracted PDF content.

These are plain dataclasses (not Pydantic) because they represent raw extracted
data, not validated domain models. They are immutable (frozen) since extraction
results should not be modified after creation.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ExtractedLink:
    """A hyperlink extracted from a PDF page.

    Attributes:
        url: The target URL of the link.
        anchor_text: The visible text that contains the link, if detectable.
            May be None if the link area doesn't contain readable text
            (e.g., linked images or icons).
    """

    url: str
    anchor_text: str | None


@dataclass(frozen=True)
class ExtractedPage:
    """Content extracted from a single PDF page.

    Attributes:
        page_number: 1-indexed page number.
        text: Full text content of the page.
        links: Hyperlinks found on the page, with their anchor text.
    """

    page_number: int
    text: str
    links: tuple[ExtractedLink, ...]  # Tuple for immutability


@dataclass(frozen=True)
class ExtractedDocument:
    """Complete extraction result from a PDF document.

    Attributes:
        pages: All pages extracted from the document.
    """

    pages: tuple[ExtractedPage, ...]  # Tuple for immutability

    @property
    def full_text(self) -> str:
        """Concatenate all page text with page separators."""
        return "\n\n".join(page.text for page in self.pages)

    @property
    def all_links(self) -> tuple[ExtractedLink, ...]:
        """Collect all links from all pages."""
        return tuple(link for page in self.pages for link in page.links)
