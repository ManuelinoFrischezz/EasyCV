from pathlib import Path

import pymupdf
from pymupdf import Page


class FileManager:
    """Class to read and extract raw information from the selected PDF file.

    Attributes:
        file_name(str): name of the PDF file
       _pdf_file_path(Path): path where the PDF file is saved
       _txt_file_path(Path): path where the txt file containing the information extracted from the PDF is saved
    """

    BASE_DIR = Path(__file__).resolve().parents[2]

    def __init__(self, file_name:str):
        self.file_name = file_name
        self._pdf_file_path = self.BASE_DIR / "data/input" / file_name
        self._txt_file_path = self.BASE_DIR / "data/output/raw_data.txt"

    @property
    def pdf_file_path(self) -> Path:
        """Getter method for the _pdf_file_path attribute"""
        return self._pdf_file_path

    @property
    def txt_file_path(self) -> Path:
        """Getter method for the _txt_file_path attribute"""
        return self._txt_file_path

    @staticmethod
    def _extract_text(page: Page) -> str:
        return page.get_text(option="text")

    @staticmethod
    def _extract_links(page: Page) -> list[str]:
        return [
            link["uri"]
            for link in page.get_links()
            if "uri" in link
        ]

    def extract_pdf_info(self) -> None:
        """Method to extract raw information from a PDF file and save it in a txt file"""
        doc = pymupdf.open(self._pdf_file_path)

        with open(self._txt_file_path, "w", encoding="utf-8") as f:
            for page in doc:
                f.write(self._extract_text(page))
                f.write("Page hypertextual elements:\n")

                for link in self._extract_links(page):
                    f.writelines(f"{link}\n")

                f.write("\f")
