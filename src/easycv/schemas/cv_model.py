"""CV data models."""

from typing import Any

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
    generalities: dict[str, Any] = Field(
        description="Contains birth date, location, and other general personal info."
    )
    contact_info: ContactInfo
    personal_presentation: str
    technical_skills: list[str]
    soft_skills: list[str]
    work_experience: list[ExperienceItem]
    education: list[EducationItem]
    international_experience: list[str]
    languages: list[Language]
