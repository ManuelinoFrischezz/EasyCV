"""Graph state definitions for the CV tailoring workflow.

This module defines the state that flows through the LangGraph graph,
including all intermediate data and conversation history.
"""

from typing import Annotated, Literal

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from easycv.schemas import CVData, ExtractedDocument


class JobAnalysis(BaseModel):
    """Analysis of a job description for CV tailoring.

    Example:
        >>> analysis = JobAnalysis(
        ...     title="Senior Data Scientist",
        ...     company="TechCorp",
        ...     required_skills=["Python", "Machine Learning", "SQL"],
        ...     nice_to_have_skills=["Kubernetes", "Spark"],
        ...     responsibilities=["Lead ML projects", "Mentor junior engineers"],
        ...     keywords=["AI", "production systems", "scalability"],
        ...     seniority="senior",
        ...     gaps=["No Kubernetes experience mentioned"],
        ... )
    """

    title: str = Field(description="Job title")
    company: str | None = Field(default=None, description="Company name if mentioned")
    required_skills: list[str] = Field(
        default_factory=list,
        description="Skills explicitly required",
    )
    nice_to_have_skills: list[str] = Field(
        default_factory=list,
        description="Skills mentioned as nice-to-have or preferred",
    )
    responsibilities: list[str] = Field(
        default_factory=list,
        description="Key responsibilities of the role",
    )
    keywords: list[str] = Field(
        default_factory=list,
        description="Important keywords to include in CV",
    )
    seniority: str | None = Field(
        default=None,
        description="Seniority level (junior, mid, senior, lead, etc.)",
    )
    gaps: list[str] = Field(
        default_factory=list,
        description="Skills/requirements from job that are missing in CV",
    )


# =============================================================================
# CV Operations - extensible system for CV modifications
# =============================================================================


class UpdateHeaderOp(BaseModel):
    """Update a field in the CV header.

    Example: Change location from "Milan" to "Remote"
    """

    op: Literal["update_header"] = "update_header"
    field: Literal["full_name", "email", "phone", "linkedin_url", "github_url", "portfolio_url", "location"]
    value: str | None = Field(description="New value for the field, or None to remove it")


class UpdateBulletOp(BaseModel):
    """Update a bullet point in an entry.

    Example: Reword a bullet to emphasize Python skills
    """

    op: Literal["update_bullet"] = "update_bullet"
    section_index: int = Field(description="Index of the section (0-based)")
    entry_index: int = Field(description="Index of the entry within the section (0-based)")
    bullet_index: int = Field(description="Index of the bullet within the entry (0-based)")
    new_text: str = Field(description="New text for the bullet")


class AddBulletOp(BaseModel):
    """Add a new bullet point to an entry.

    Example: Add a bullet about AI experience
    """

    op: Literal["add_bullet"] = "add_bullet"
    section_index: int = Field(description="Index of the section (0-based)")
    entry_index: int = Field(description="Index of the entry within the section (0-based)")
    text: str = Field(description="Text for the new bullet")
    position: int | None = Field(default=None, description="Position to insert at, or None to append")


class RemoveBulletOp(BaseModel):
    """Remove a bullet point from an entry.

    Example: Remove an irrelevant bullet
    """

    op: Literal["remove_bullet"] = "remove_bullet"
    section_index: int = Field(description="Index of the section (0-based)")
    entry_index: int = Field(description="Index of the entry within the section (0-based)")
    bullet_index: int = Field(description="Index of the bullet to remove (0-based)")


class UpdateEntryOp(BaseModel):
    """Update metadata of an entry (title, organization, dates, location).

    Example: Update job title to match job posting terminology
    """

    op: Literal["update_entry"] = "update_entry"
    section_index: int = Field(description="Index of the section (0-based)")
    entry_index: int = Field(description="Index of the entry within the section (0-based)")
    field: Literal["title", "organization", "start_date", "end_date", "location"]
    value: str | None = Field(description="New value for the field")


class UpdateTagsOp(BaseModel):
    """Update tags/technologies for an entry.

    Example: Add "LangChain" to the tags
    """

    op: Literal["update_tags"] = "update_tags"
    section_index: int = Field(description="Index of the section (0-based)")
    entry_index: int = Field(description="Index of the entry within the section (0-based)")
    tags: list[str] = Field(description="New list of tags")


class UpdateLabeledItemOp(BaseModel):
    """Update a labeled item in a labeled_list section (e.g., skills).

    Example: Add "Kubernetes" to the "Cloud" skills
    """

    op: Literal["update_labeled_item"] = "update_labeled_item"
    section_index: int = Field(description="Index of the section (0-based)")
    item_index: int = Field(description="Index of the labeled item (0-based)")
    label: str | None = Field(default=None, description="New label, or None to keep current")
    values: list[str] | None = Field(default=None, description="New values, or None to keep current")


class UpdateParagraphOp(BaseModel):
    """Update the text of a paragraph section.

    Example: Rewrite the professional summary
    """

    op: Literal["update_paragraph"] = "update_paragraph"
    section_index: int = Field(description="Index of the section (0-based)")
    text: str = Field(description="New paragraph text")


class UpdateSectionHeadingOp(BaseModel):
    """Update the heading of a section.

    Example: Rename "Work Experience" to "Professional Experience"
    """

    op: Literal["update_section_heading"] = "update_section_heading"
    section_index: int = Field(description="Index of the section (0-based)")
    heading: str = Field(description="New heading text")


class ReorderSectionsOp(BaseModel):
    """Reorder sections in the CV.

    Example: Move Skills section before Work Experience
    """

    op: Literal["reorder_sections"] = "reorder_sections"
    new_order: list[int] = Field(description="New order of section indices")


# Future: Layout/styling operations can be added here
# class UpdateSectionStyleOp(BaseModel):
#     """Update visual style of a section (future feature)."""
#     op: Literal["update_section_style"] = "update_section_style"
#     section_index: int
#     style: dict  # e.g., {"columns": 2, "bullet_style": "dash"}


# Union of all operations
CVOperation = (
    UpdateHeaderOp
    | UpdateBulletOp
    | AddBulletOp
    | RemoveBulletOp
    | UpdateEntryOp
    | UpdateTagsOp
    | UpdateLabeledItemOp
    | UpdateParagraphOp
    | UpdateSectionHeadingOp
    | ReorderSectionsOp
)


class AgentResponse(BaseModel):
    """Structured response from the CV tailoring agent.

    The agent returns a message to the user and a list of operations
    to apply to the CV. Operations are atomic changes that get applied
    in sequence.

    Example:
        >>> response = AgentResponse(
        ...     message="I've emphasized your Python experience.",
        ...     operations=[
        ...         UpdateBulletOp(
        ...             section_index=0,
        ...             entry_index=0,
        ...             bullet_index=0,
        ...             new_text="Led Python development for ML pipelines",
        ...         ),
        ...     ],
        ... )
    """

    message: str = Field(description="Response message to the user")
    operations: list[CVOperation] = Field(
        default_factory=list,
        description="List of operations to apply to the CV. Empty if no changes needed.",
    )


class GraphState(TypedDict):
    """State that flows through the CV tailoring graph.

    Attributes:
        pdf_bytes: Raw PDF file content.
        job_description: Job description text to tailor the CV for.
        extracted: Raw text and links extracted from PDF.
        original_cv: Parsed CV data (immutable reference).
        current_cv: Current version of the CV (modified by agent).
        job_analysis: Analysis of the job description.
        messages: Conversation history with the user.
        stage: Current stage of the workflow.
        rendered_pdf: Final PDF output.
    """

    # Input
    pdf_bytes: bytes
    job_description: str

    # Extracted/parsed data
    extracted: ExtractedDocument | None
    original_cv: CVData | None
    current_cv: CVData | None
    job_analysis: JobAnalysis | None

    # Conversation (uses add_messages reducer for automatic merging)
    messages: Annotated[list[BaseMessage], add_messages]

    # Control flow
    stage: Literal["init", "chat", "done"]

    # Output
    rendered_pdf: bytes | None
