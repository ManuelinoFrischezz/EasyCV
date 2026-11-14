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


class AgentResponse(BaseModel):
    """Structured response from the CV tailoring agent.

    The agent returns both a message to the user and optionally
    an updated CV. If updated_cv is None, the CV wasn't modified.

    Example:
        >>> response = AgentResponse(
        ...     message="I've emphasized your Python experience in the skills section.",
        ...     updated_cv=modified_cv_data,
        ... )
    """

    message: str = Field(description="Response message to the user")
    updated_cv: CVData | None = Field(
        default=None,
        description="Modified CV, or None if no changes were made",
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
