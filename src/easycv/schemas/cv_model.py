"""CV data model with section-based layout system.

This module defines the structured representation of a CV. The LLM parses
extracted PDF text into this schema, and the rendering layer converts it
to LaTeX using templates for each layout type.

Key concepts:
- Header: fixed structure for name and contact info
- Section: has a `kind` (semantic meaning), `heading` (display title), and `layout`
- Layout: determines how content is rendered (entries, labeled_list, flat_list, paragraph)

Example CVData:
    >>> cv = CVData(
    ...     header=Header(
    ...         full_name="Marco Rossi",
    ...         email="marco.rossi@email.com",
    ...         linkedin_url="https://linkedin.com/in/marco-rossi",
    ...     ),
    ...     sections=[
    ...         Section(
    ...             kind="work_experience",
    ...             heading="Work Experience",
    ...             content=EntriesContent(entries=[
    ...                 Entry(
    ...                     title="Data Scientist",
    ...                     organization="TechCorp",
    ...                     start_date="2023",
    ...                     end_date=None,  # Present
    ...                     bullets=[Bullet(text="Built ML pipelines")],
    ...                 )
    ...             ])
    ...         ),
    ...         Section(
    ...             kind="skills",
    ...             heading="Technical Skills",
    ...             content=LabeledListContent(items=[
    ...                 LabeledItem(label="Languages", values=["Python", "SQL"]),
    ...             ])
    ...         ),
    ...     ]
    ... )
"""

from typing import Annotated, Literal

from pydantic import BaseModel, Field

# =============================================================================
# Header
# =============================================================================


class Header(BaseModel):
    """CV header with personal and contact information.

    Example:
        >>> header = Header(
        ...     full_name="Marco Rossi",
        ...     email="marco.rossi@email.com",
        ...     phone="+39 123 456 7890",
        ...     linkedin_url="https://linkedin.com/in/marco-rossi",
        ...     github_url="https://github.com/mrossi",
        ...     location="Milan, Italy",
        ... )
    """

    full_name: str = Field(description="Full name as displayed on the CV")
    email: str | None = Field(default=None, description="Email address")
    phone: str | None = Field(default=None, description="Phone number")
    linkedin_url: str | None = Field(default=None, description="LinkedIn profile URL")
    github_url: str | None = Field(default=None, description="GitHub profile URL")
    portfolio_url: str | None = Field(default=None, description="Portfolio or personal website URL")
    location: str | None = Field(default=None, description="City, country or region")


# =============================================================================
# Layout: Entries (for work experience, education, projects)
# =============================================================================


class Bullet(BaseModel):
    """A bullet point, optionally with a URL and nested children.

    Example:
        >>> bullet = Bullet(
        ...     text="Built ML pipeline reducing processing time by 40%",
        ...     url="https://github.com/example/project",
        ...     children=[Bullet(text="Used Apache Airflow for orchestration")],
        ... )
    """

    text: str = Field(description="Bullet point text")
    url: str | None = Field(default=None, description="Optional URL for this bullet")
    children: list["Bullet"] = Field(
        default_factory=list,
        description="Nested bullets (max 1 level recommended)",
    )


class Entry(BaseModel):
    """An entry in a timeline-based section (experience, education, projects).

    Example:
        >>> entry = Entry(
        ...     title="Senior Data Scientist",
        ...     organization="TechCorp S.p.A",
        ...     start_date="05/2023",
        ...     end_date=None,  # Means "Present"
        ...     location="Milan, Italy",
        ...     bullets=[
        ...         Bullet(text="Led team of 3 data scientists"),
        ...         Bullet(text="Deployed models serving 1M requests/day"),
        ...     ],
        ...     tags=["Python", "AWS", "LangChain"],
        ... )
    """

    title: str = Field(description="Role, degree, or project name")
    organization: str = Field(description="Company, university, or organization name")
    start_date: str = Field(description="Start date (format flexible, e.g. '2023', '05/2023')")
    end_date: str | None = Field(
        default=None,
        description="End date, or None for 'Present'",
    )
    location: str | None = Field(default=None, description="Location if relevant")
    bullets: list[Bullet] = Field(
        default_factory=list,
        description="Bullet points describing responsibilities/achievements",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Tags like tools/technologies used (from 'Tools: X, Y' lines)",
    )


class EntriesContent(BaseModel):
    """Content for sections using the 'entries' layout.

    Example:
        >>> content = EntriesContent(entries=[
        ...     Entry(title="Data Scientist", organization="TechCorp", start_date="2023"),
        ...     Entry(title="ML Engineer Intern", organization="StartupXYZ", start_date="2022", end_date="2023"),
        ... ])
    """

    layout: Literal["entries"] = "entries"
    entries: list[Entry] = Field(description="List of entries in reverse chronological order")


# =============================================================================
# Layout: Labeled List (for skills, languages)
# =============================================================================


class LabeledItem(BaseModel):
    """A labeled group of items.

    Example:
        >>> item = LabeledItem(
        ...     label="Programming Languages",
        ...     values=["Python", "SQL", "Java"],
        ... )
    """

    label: str = Field(description="Category label")
    values: list[str] = Field(description="Items in this category")


class LabeledListContent(BaseModel):
    """Content for sections using the 'labeled_list' layout.

    Example:
        >>> content = LabeledListContent(items=[
        ...     LabeledItem(label="Languages", values=["Python", "SQL"]),
        ...     LabeledItem(label="Frameworks", values=["LangChain", "FastAPI"]),
        ...     LabeledItem(label="Cloud", values=["AWS", "GCP"]),
        ... ])
    """

    layout: Literal["labeled_list"] = "labeled_list"
    items: list[LabeledItem] = Field(description="List of labeled item groups")


# =============================================================================
# Layout: Flat List (for simple lists)
# =============================================================================


class FlatListContent(BaseModel):
    """Content for sections using the 'flat_list' layout.

    Example:
        >>> content = FlatListContent(items=[
        ...     "AWS Certified Solutions Architect",
        ...     "Google Cloud Professional Data Engineer",
        ...     "Certified Kubernetes Administrator",
        ... ])
    """

    layout: Literal["flat_list"] = "flat_list"
    items: list[str] = Field(description="Simple list of strings")


# =============================================================================
# Layout: Paragraph (for free-form text)
# =============================================================================


class ParagraphContent(BaseModel):
    """Content for sections using the 'paragraph' layout.

    Example:
        >>> content = ParagraphContent(
        ...     text="Experienced data scientist with 5+ years in ML and AI. "
        ...          "Passionate about building production systems that scale."
        ... )
    """

    layout: Literal["paragraph"] = "paragraph"
    text: str = Field(description="Free-form text content")


# =============================================================================
# Section (discriminated union)
# =============================================================================

SectionContent = Annotated[
    EntriesContent | LabeledListContent | FlatListContent | ParagraphContent,
    Field(discriminator="layout"),
]


class Section(BaseModel):
    """A CV section with semantic kind, display heading, and typed content.

    The `content` field is a discriminated union based on the `layout` field
    inside each content type.

    Example:
        >>> section = Section(
        ...     kind="work_experience",
        ...     heading="Work Experience",
        ...     content=EntriesContent(entries=[
        ...         Entry(title="Data Scientist", organization="TechCorp", start_date="2023")
        ...     ]),
        ... )
    """

    kind: str = Field(
        description="Semantic type of section (e.g. 'work_experience', 'education', 'skills')"
    )
    heading: str = Field(description="Display heading as shown on the CV")
    content: SectionContent = Field(description="Section content, layout determined by content type")


# =============================================================================
# CVData (root model)
# =============================================================================


class CVData(BaseModel):
    """Complete CV data model.

    This is the root model that the LLM produces from extracted PDF text,
    and that the rendering layer converts to LaTeX.

    Example:
        >>> cv = CVData(
        ...     header=Header(full_name="Marco Rossi", email="m@example.com"),
        ...     sections=[
        ...         Section(
        ...             kind="personal_profile",
        ...             heading="Personal Profile",
        ...             content=ParagraphContent(text="Experienced engineer..."),
        ...         ),
        ...     ],
        ... )
    """

    header: Header = Field(description="Personal and contact information")
    sections: list[Section] = Field(
        default_factory=list,
        description="CV sections in display order",
    )
