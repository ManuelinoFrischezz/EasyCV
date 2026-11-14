"""CV parsing using LLM structured output.

This module transforms raw extracted PDF content (ExtractedDocument) into
structured CV data (CVData) using an LLM with structured output.

The parsing is "faithful": it extracts and structures what's in the document
without translation, rewriting, or interpretation. Translation to English
happens in a separate step.

Usage:
    >>> from easycv.extraction import extract_pdf
    >>> from easycv.llm.cv_parser import parse_cv
    >>> from easycv.settings import get_settings
    >>>
    >>> extracted = extract_pdf(Path("cv.pdf"))
    >>> cv_data = parse_cv(extracted, get_settings())
"""

from pathlib import Path

import yaml
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from easycv.llm.factory import create_llm
from easycv.schemas import CVData, ExtractedDocument
from easycv.settings import Settings

# Paths to config files
CONFIGS_DIR = Path(__file__).parents[3] / "configs"
PROMPTS_PATH = CONFIGS_DIR / "prompts" / "cv_parser.yml"
LAYOUTS_PATH = CONFIGS_DIR / "layouts.yml"


def parse_cv(
    extracted: ExtractedDocument,
    settings: Settings,
    *,
    llm: BaseChatModel | None = None,
) -> CVData:
    """Parse extracted PDF content into structured CV data.

    Args:
        extracted: Raw text and links extracted from a PDF.
        settings: Application settings (used to create LLM if not provided).
        llm: Optional pre-configured LLM instance. If not provided, one will
            be created from settings.

    Returns:
        Structured CV data ready for tailoring and rendering.

    Raises:
        LLMConfigurationError: If LLM creation fails due to missing API key.
        ValidationError: If the LLM output doesn't match the CVData schema.
        FileNotFoundError: If prompt config files are missing.

    Example:
        >>> extracted = extract_pdf(Path("resume.pdf"))
        >>> cv = parse_cv(extracted, get_settings())
        >>> print(cv.header.full_name)
        'Marco Rossi'
    """
    if llm is None:
        llm = create_llm(settings)

    # Use structured output to get validated CVData
    structured_llm = llm.with_structured_output(CVData)

    # Load prompts from config files
    prompts = _load_prompts()
    layout_descriptions = _load_layout_descriptions()
    page_content = _format_page_content(extracted)

    # Build messages with placeholder substitution
    system_prompt = prompts["system"].format(layout_descriptions=layout_descriptions)
    user_prompt = prompts["user"].format(page_content=page_content)

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    result = structured_llm.invoke(messages)

    # with_structured_output returns the parsed object directly
    return result  # type: ignore[return-value]


def _load_prompts() -> dict[str, str]:
    """Load prompt templates from config file."""
    if not PROMPTS_PATH.exists():
        raise FileNotFoundError(
            f"Prompt config not found: {PROMPTS_PATH}. "
            "Ensure configs/prompts/cv_parser.yml exists."
        )

    with PROMPTS_PATH.open() as f:
        prompts: dict[str, str] = yaml.safe_load(f)

    # Validate required keys
    required_keys = ["system", "user"]
    for key in required_keys:
        if key not in prompts:
            raise ValueError(f"Missing required prompt key: {key}")

    return prompts


def _load_layout_descriptions() -> str:
    """Load layout descriptions from the registry.

    Raises:
        FileNotFoundError: If layouts.yml config file is missing.
    """
    if not LAYOUTS_PATH.exists():
        raise FileNotFoundError(
            f"Layout config not found: {LAYOUTS_PATH}. "
            "Ensure configs/layouts.yml exists."
        )

    with LAYOUTS_PATH.open() as f:
        registry = yaml.safe_load(f)

    lines = []
    for name, config in registry.get("layouts", {}).items():
        desc = config.get("description", "No description").strip()
        lines.append(f"### {name}\n{desc}")

    return "\n\n".join(lines)


def _format_page_content(extracted: ExtractedDocument) -> str:
    """Format extracted document content for the prompt."""
    parts = []

    for page in extracted.pages:
        parts.append(f"--- Page {page.page_number} ---")
        parts.append(page.text)

        if page.links:
            parts.append("\nLinks found on this page:")
            for link in page.links:
                anchor = link.anchor_text or "(no anchor text)"
                parts.append(f"  - {anchor}: {link.url}")

        parts.append("")  # Empty line between pages

    return "\n".join(parts)
