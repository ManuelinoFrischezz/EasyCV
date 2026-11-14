"""Tests for PDF extraction functionality."""

from pathlib import Path

import pytest

from easycv.extraction import extract_pdf
from easycv.schemas import ExtractedDocument, ExtractedLink, ExtractedPage


class TestExtractPdf:
    """Tests for the extract_pdf function."""

    def test_extracts_from_path(self, sample_pdf_path: Path) -> None:
        """Should extract content when given a file path."""
        result = extract_pdf(sample_pdf_path)

        assert isinstance(result, ExtractedDocument)
        assert len(result.pages) >= 1

    def test_extracts_from_bytes(self, sample_pdf_bytes: bytes) -> None:
        """Should extract content when given raw PDF bytes."""
        result = extract_pdf(sample_pdf_bytes)

        assert isinstance(result, ExtractedDocument)
        assert len(result.pages) >= 1

    def test_page_numbers_are_one_indexed(self, sample_pdf_bytes: bytes) -> None:
        """Page numbers should start at 1, not 0."""
        result = extract_pdf(sample_pdf_bytes)

        assert result.pages[0].page_number == 1

    def test_extracts_header_name(self, sample_pdf_bytes: bytes) -> None:
        """Should extract the candidate's name from header."""
        result = extract_pdf(sample_pdf_bytes)

        full_text = result.full_text
        assert "Marco Rossi" in full_text

    def test_extracts_work_experience_content(self, sample_pdf_bytes: bytes) -> None:
        """Should extract work experience section content."""
        result = extract_pdf(sample_pdf_bytes)

        full_text = result.full_text
        assert "Data Scientist" in full_text
        assert "TechCorp" in full_text
        assert "LangChain" in full_text

    def test_extracts_education_content(self, sample_pdf_bytes: bytes) -> None:
        """Should extract education section content."""
        result = extract_pdf(sample_pdf_bytes)

        full_text = result.full_text
        assert "MSc" in full_text
        assert "Computer Engineering" in full_text
        assert "110/110" in full_text

    def test_extracts_multiple_links(self, sample_pdf_bytes: bytes) -> None:
        """Should extract all hyperlinks from the document."""
        result = extract_pdf(sample_pdf_bytes)

        all_links = result.all_links
        urls = [link.url for link in all_links]

        # Should have email, LinkedIn, GitHub, and publication links
        assert any("mailto:" in url for url in urls), "Should have email link"
        assert any("linkedin.com" in url for url in urls), "Should have LinkedIn link"
        assert any("github.com" in url for url in urls), "Should have GitHub link"
        assert any("scholar.google" in url for url in urls), "Should have publication link"

    def test_extracts_linkedin_anchor_text(self, sample_pdf_bytes: bytes) -> None:
        """Should extract anchor text for LinkedIn link."""
        result = extract_pdf(sample_pdf_bytes)

        linkedin_links = [
            link for link in result.all_links if "linkedin.com" in link.url
        ]
        assert len(linkedin_links) == 1

        anchor = linkedin_links[0].anchor_text
        assert anchor is not None
        assert "linkedin" in anchor.lower()

    def test_extracts_github_anchor_text(self, sample_pdf_bytes: bytes) -> None:
        """Should extract anchor text for GitHub link."""
        result = extract_pdf(sample_pdf_bytes)

        github_links = [
            link for link in result.all_links if "github.com" in link.url
        ]
        assert len(github_links) == 1

        anchor = github_links[0].anchor_text
        assert anchor is not None
        assert "github" in anchor.lower()

    def test_full_text_property(self, sample_pdf_bytes: bytes) -> None:
        """full_text property should concatenate all pages."""
        result = extract_pdf(sample_pdf_bytes)

        full_text = result.full_text
        # Should contain content from various sections
        assert "Personal Profile" in full_text or "Marco Rossi" in full_text
        assert "Education" in full_text

    def test_all_links_property(self, sample_pdf_bytes: bytes) -> None:
        """all_links property should collect links from all pages."""
        result = extract_pdf(sample_pdf_bytes)

        all_links = result.all_links
        assert len(all_links) >= 4  # email, linkedin, github, publication

    def test_raises_file_not_found_for_missing_path(self, tmp_path: Path) -> None:
        """Should raise FileNotFoundError for non-existent paths."""
        missing_path = tmp_path / "does_not_exist.pdf"

        with pytest.raises(FileNotFoundError):
            extract_pdf(missing_path)

    def test_result_is_immutable(self, sample_pdf_bytes: bytes) -> None:
        """Extracted data should be immutable (frozen dataclasses)."""
        result = extract_pdf(sample_pdf_bytes)

        with pytest.raises(AttributeError):
            result.pages = ()  # type: ignore[misc]

        with pytest.raises(AttributeError):
            result.pages[0].text = "modified"  # type: ignore[misc]


class TestExtractPdfMinimal:
    """Tests using minimal PDF fixture for edge cases."""

    def test_single_page_extraction(self, minimal_pdf_bytes: bytes) -> None:
        """Should handle single-page PDFs."""
        result = extract_pdf(minimal_pdf_bytes)

        assert len(result.pages) == 1
        assert result.pages[0].page_number == 1

    def test_extracts_email_link(self, minimal_pdf_bytes: bytes) -> None:
        """Should extract mailto links."""
        result = extract_pdf(minimal_pdf_bytes)

        links = result.all_links
        assert len(links) == 1
        assert links[0].url == "mailto:test@example.com"


class TestExtractedDataclasses:
    """Tests for the extracted data structures."""

    def test_extracted_link_equality(self) -> None:
        """Two links with same content should be equal."""
        link1 = ExtractedLink(url="https://example.com", anchor_text="Example")
        link2 = ExtractedLink(url="https://example.com", anchor_text="Example")

        assert link1 == link2

    def test_extracted_link_with_none_anchor(self) -> None:
        """Links can have None anchor text."""
        link = ExtractedLink(url="https://example.com", anchor_text=None)

        assert link.anchor_text is None

    def test_extracted_page_contains_expected_fields(
        self, sample_pdf_bytes: bytes
    ) -> None:
        """ExtractedPage should have all expected fields."""
        result = extract_pdf(sample_pdf_bytes)
        page = result.pages[0]

        assert isinstance(page, ExtractedPage)
        assert hasattr(page, "page_number")
        assert hasattr(page, "text")
        assert hasattr(page, "links")

    def test_extracted_document_pages_are_tuple(
        self, sample_pdf_bytes: bytes
    ) -> None:
        """Pages should be a tuple for immutability."""
        result = extract_pdf(sample_pdf_bytes)

        assert isinstance(result.pages, tuple)

    def test_extracted_page_links_are_tuple(
        self, sample_pdf_bytes: bytes
    ) -> None:
        """Page links should be a tuple for immutability."""
        result = extract_pdf(sample_pdf_bytes)

        assert isinstance(result.pages[0].links, tuple)
