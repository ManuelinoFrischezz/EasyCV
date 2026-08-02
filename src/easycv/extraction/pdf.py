"""PDF text and link extraction using PyMuPDF.

NOTE: This module will be refactored to:
- Return an ExtractedDocument dataclass instead of writing to disk
- Include anchor text for links
- Support optional page images for scanned PDFs
- Remove BASE_DIR path handling (use dependency injection)

See spec/PROJECT_CONTEXT.md for the target design.
"""

from pathlib import Path

import pymupdf
from pymupdf import Page


class FileManager:
    """Class to read and extract raw information from the selected PDF file.

    Attributes:
        file_name: Name of the PDF file.
        _pdf_file_path: Path where the PDF file is saved.
        _txt_file_path: Path where the txt file containing extracted info is saved.

    NOTE: This class will be replaced by a function returning ExtractedDocument.
    """

    BASE_DIR = Path(__file__).resolve().parents[3]

    def __init__(self, file_name: str) -> None:
        self.file_name = file_name
        self._pdf_file_path = self.BASE_DIR / "data/input" / file_name
        self._txt_file_path = self.BASE_DIR / "data/output/raw_data.txt"

    @property
    def pdf_file_path(self) -> Path:
        """Getter method for the _pdf_file_path attribute."""
        return self._pdf_file_path

    @property
    def txt_file_path(self) -> Path:
        """Getter method for the _txt_file_path attribute."""
        return self._txt_file_path

    @staticmethod
    def _extract_text(page: Page) -> str:
        return page.get_text(option="text")

    @staticmethod
    def _extract_links(page: Page) -> list[str]:
        return [link["uri"] for link in page.get_links() if "uri" in link]

    def extract_pdf_info(self) -> None:
        """Extract raw information from a PDF file and save it in a txt file."""
        doc = pymupdf.open(self._pdf_file_path)

        with open(self._txt_file_path, "w", encoding="utf-8") as f:
            for page in doc:
                f.write(self._extract_text(page))
                f.write("Page hypertextual elements:\n")

                for link in self._extract_links(page):
                    f.writelines(f"{link}\n")

                f.write("\f")
