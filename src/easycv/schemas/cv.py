"""CV data models.

NOTE: This is a placeholder schema from the early prototype.
It will be rewritten to match the design in spec/PROJECT_CONTEXT.md:
- Sections with `kind`, `heading`, `layout` (discriminated union)
- Layouts: entries, labeled_list, flat_list, paragraph
- Layout registry in configs/layouts.yml
"""

from pydantic import BaseModel, Field


class ContactInfo(BaseModel):
    phone: str | None = None
    email: str | None = None
    linkedin_url: str | None = None
    portfolio_url: str | None = None


class ExperienceItem(BaseModel):
    company: str
    role: str
    start_date: str
    end_date: str  # e.g., "Present" or a date
    description: list[str] = Field(
        description="A list of bullet points describing the responsibilities and achievements."
    )


class EducationItem(BaseModel):
    institution: str
    degree: str
    grad_year: str


class Language(BaseModel):
    name: str
    level: str  # e.g., "C1", "Fluent", "Native"


class CVData(BaseModel):
    first_name: str
    last_name: str
    generalities: dict = Field(
        description="Contains birth date, location, and other general personal info."
    )
    contact_info: ContactInfo
    personal_presentation: str
    technical_skills: list[str]
    soft_skills: list[str]  # Also known as soft skills
    work_experience: list[ExperienceItem]
    education: list[EducationItem]
    international_experience: list[str]  # Specific segment for international projects or roles
    languages: list[Language]
