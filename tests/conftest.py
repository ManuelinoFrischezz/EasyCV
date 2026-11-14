"""Pytest fixtures for EasyCV tests."""

from pathlib import Path

import pymupdf
import pytest


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """Create a realistic CV PDF with multiple sections, links, and formatting.

    The PDF mimics a real CV structure with:
    - Header with name and contact links (email, LinkedIn, GitHub)
    - Personal profile section
    - Work experience with multiple entries and bullet points
    - Education with thesis and publication link
    - Soft skills paragraph
    - Languages list

    All data is fictional and anonymized.

    Returns:
        Raw PDF bytes.
    """
    doc = pymupdf.open()

    # Page 1
    page1 = doc.new_page(width=595, height=842)  # A4

    y = 50  # Current vertical position

    # === HEADER ===
    page1.insert_text((50, y), "Marco Rossi", fontsize=20, fontname="helv")
    y += 30

    # Contact links
    _insert_link(page1, 50, y, "marco.rossi@email.com", "mailto:marco.rossi@email.com")
    y += 15
    _insert_link(page1, 50, y, "linkedin.com/in/marco-rossi", "https://linkedin.com/in/marco-rossi")
    y += 15
    _insert_link(page1, 50, y, "github.com/mrossi", "https://github.com/mrossi")
    y += 30

    # === PERSONAL PROFILE ===
    page1.insert_text((50, y), "Personal Profile", fontsize=14, fontname="helv")
    y += 20
    profile_text = (
        "Computer Engineer working as a Data Scientist, transitioning into AI Engineering. "
        "Experienced with agent systems, Generative AI, and production ML systems. "
        "Looking for opportunities to expand skills working with experienced professionals."
    )
    y = _insert_wrapped_text(page1, 50, y, profile_text, width=495, fontsize=10)
    y += 20

    # === WORK EXPERIENCE ===
    page1.insert_text((50, y), "Work Experience", fontsize=14, fontname="helv")
    y += 20

    # Job 1
    page1.insert_text((50, y), "Data Scientist/AI Engineer", fontsize=11, fontname="helv")
    page1.insert_text((400, y), "05/2024 - Present", fontsize=10)
    y += 15
    page1.insert_text((50, y), "TechCorp S.p.A", fontsize=10)
    y += 15
    job1_desc = (
        "Part of Data Science team designing and developing agents in financial services. "
        "Used Python, Git, LangChain, LangGraph for building agents. "
        "Monitoring with LangFuse and Datadog. AWS (S3, DynamoDB) for cloud resources. "
        "FastAPI for backend, Docker and Streamlit for testing interfaces."
    )
    y = _insert_wrapped_text(page1, 60, y, job1_desc, width=485, fontsize=9)
    y += 15

    # Job 2
    page1.insert_text((50, y), "Data Scientist - Internship", fontsize=11, fontname="helv")
    page1.insert_text((400, y), "11/2023 - 05/2024", fontsize=10)
    y += 15
    page1.insert_text((50, y), "TechCorp S.p.A", fontsize=10)
    y += 15
    job2_desc = (
        "Worked on income estimation from banking transaction data using Scikit-learn. "
        "Used PySpark for large-scale data processing and Spark ML for model training."
    )
    y = _insert_wrapped_text(page1, 60, y, job2_desc, width=485, fontsize=9)
    y += 15

    # Job 3
    page1.insert_text((50, y), "University Tutor", fontsize=11, fontname="helv")
    page1.insert_text((400, y), "10/2021 - 10/2023", fontsize=10)
    y += 15
    page1.insert_text((50, y), "University of Milan, Italy", fontsize=10)
    y += 15
    job3_desc = (
        "Tutored undergraduate students in Control Systems and core engineering subjects. "
        "Led study groups for Electronic and Computer Engineering students."
    )
    y = _insert_wrapped_text(page1, 60, y, job3_desc, width=485, fontsize=9)
    y += 25

    # === EDUCATION ===
    page1.insert_text((50, y), "Education", fontsize=14, fontname="helv")
    y += 20

    page1.insert_text((50, y), "MSc in Computer Engineering", fontsize=11, fontname="helv")
    page1.insert_text((450, y), "2022/23", fontsize=10)
    y += 15
    page1.insert_text((50, y), "University of Milan, Italy - Grade: 110/110", fontsize=10)
    y += 15
    page1.insert_text(
        (50, y), 'Thesis: "Optimization of Supply Chain with Predictive Control"', fontsize=9
    )
    y += 15
    page1.insert_text((50, y), "Related publication:", fontsize=9)
    _insert_link(
        page1,
        140,
        y,
        "Stochastic MPC for Supply Chains",
        "https://scholar.google.com/citations?view_op=view_citation&citation_id=abc123",
    )
    y += 20

    page1.insert_text((50, y), "BSc in Electronic & Computer Engineering", fontsize=11, fontname="helv")
    page1.insert_text((450, y), "2020/21", fontsize=10)
    y += 15
    page1.insert_text((50, y), "University of Milan, Italy - Grade: 100/110", fontsize=10)
    y += 25

    # === SOFT SKILLS ===
    page1.insert_text((50, y), "Soft Skills", fontsize=14, fontname="helv")
    y += 20
    skills_text = (
        "Strong analytical and problem-solving mindset. Comfortable in multicultural teams. "
        "Able to explain technical concepts to varying audiences. "
        "Proactive with genuine curiosity for emerging technologies."
    )
    y = _insert_wrapped_text(page1, 50, y, skills_text, width=495, fontsize=10)
    y += 20

    # === LANGUAGES ===
    page1.insert_text((50, y), "Languages", fontsize=14, fontname="helv")
    y += 20
    page1.insert_text((50, y), "Italian: Native", fontsize=10)
    y += 12
    page1.insert_text((50, y), "English: B2 (Upper-Intermediate)", fontsize=10)
    y += 12
    page1.insert_text((50, y), "Spanish: A1 (Beginner)", fontsize=10)

    pdf_bytes = doc.tobytes()
    doc.close()

    return pdf_bytes


def _insert_link(page: pymupdf.Page, x: float, y: float, text: str, url: str) -> None:
    """Insert text with a hyperlink at the specified position."""
    page.insert_text((x, y), text, fontsize=10, color=(0, 0, 0.8))
    # Approximate text width (rough estimate)
    text_width = len(text) * 5
    link_rect = pymupdf.Rect(x, y - 10, x + text_width, y + 2)
    page.insert_link({"kind": pymupdf.LINK_URI, "from": link_rect, "uri": url})


def _insert_wrapped_text(
    page: pymupdf.Page, x: float, y: float, text: str, *, width: float, fontsize: int
) -> float:
    """Insert text that wraps within the given width. Returns new y position."""
    # Rough character width estimate
    char_width = fontsize * 0.5
    chars_per_line = int(width / char_width)

    words = text.split()
    lines: list[str] = []
    current_line: list[str] = []

    for word in words:
        test_line = " ".join([*current_line, word])
        if len(test_line) <= chars_per_line:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]

    if current_line:
        lines.append(" ".join(current_line))

    for line in lines:
        page.insert_text((x, y), line, fontsize=fontsize)
        y += fontsize + 3

    return y


@pytest.fixture
def sample_pdf_path(tmp_path: Path, sample_pdf_bytes: bytes) -> Path:
    """Write sample PDF to a temporary file.

    Args:
        tmp_path: Pytest's temporary directory fixture.
        sample_pdf_bytes: The PDF bytes fixture.

    Returns:
        Path to the temporary PDF file.
    """
    pdf_path = tmp_path / "sample_cv.pdf"
    pdf_path.write_bytes(sample_pdf_bytes)
    return pdf_path


@pytest.fixture
def minimal_pdf_bytes() -> bytes:
    """Create a minimal single-page PDF for simple tests.

    Returns:
        Raw PDF bytes with just a name and one link.
    """
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)

    page.insert_text((50, 50), "Test Person", fontsize=16)
    page.insert_text((50, 80), "test@example.com", fontsize=10, color=(0, 0, 0.8))

    link_rect = pymupdf.Rect(50, 70, 200, 82)
    page.insert_link({"kind": pymupdf.LINK_URI, "from": link_rect, "uri": "mailto:test@example.com"})

    pdf_bytes = doc.tobytes()
    doc.close()

    return pdf_bytes
