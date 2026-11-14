"""Render CVData to LaTeX source using Jinja2 templates.

This module provides the bridge between the structured CV data model
and LaTeX output. It uses Jinja2 templates with custom filters for
proper LaTeX escaping.

Example:
    >>> from easycv.schemas.cv_model import CVData, Header
    >>> cv = CVData(header=Header(full_name="Marco Rossi"))
    >>> latex_source = render_cv(cv)
    >>> print(latex_source[:50])
    \\documentclass[11pt,a4paper]{article}
"""

import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from easycv.schemas.cv_model import CVData

# LaTeX special characters that need escaping
LATEX_SPECIAL_CHARS: dict[str, str] = {
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
    "\\": r"\textbackslash{}",
}

# Regex pattern for LaTeX special characters
LATEX_ESCAPE_PATTERN = re.compile(
    "|".join(re.escape(char) for char in LATEX_SPECIAL_CHARS)
)


def latex_escape(text: str) -> str:
    """Escape special LaTeX characters in text.

    Args:
        text: Plain text that may contain LaTeX special characters.

    Returns:
        Text with special characters escaped for LaTeX.

    Example:
        >>> latex_escape("100% complete & working")
        '100\\\\% complete \\\\& working'
    """
    return LATEX_ESCAPE_PATTERN.sub(
        lambda match: LATEX_SPECIAL_CHARS[match.group()], text
    )


def _get_template_dir() -> Path:
    """Get the templates directory path.

    Returns:
        Path to the templates directory at project root.

    Raises:
        FileNotFoundError: If templates directory doesn't exist.
    """
    # Navigate from src/easycv/rendering/ to project root
    project_root = Path(__file__).parent.parent.parent.parent
    template_dir = project_root / "templates"

    if not template_dir.exists():
        raise FileNotFoundError(
            f"Templates directory not found at {template_dir}. "
            "Ensure the 'templates/' folder exists at project root."
        )

    return template_dir


def _create_jinja_env(template_dir: Path) -> Environment:
    """Create a Jinja2 environment configured for LaTeX rendering.

    Uses custom delimiters to avoid conflicts with LaTeX syntax:
    - Block: <% %> instead of {% %}
    - Variable: << >> instead of {{ }}
    - Comment: <# #> instead of {# #}

    Args:
        template_dir: Path to directory containing templates.

    Returns:
        Configured Jinja2 Environment.
    """
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(enabled_extensions=()),  # Disable HTML autoescape
        trim_blocks=True,
        lstrip_blocks=True,
        # Custom delimiters to avoid LaTeX conflicts
        block_start_string="<%",
        block_end_string="%>",
        variable_start_string="<<",
        variable_end_string=">>",
        comment_start_string="<#",
        comment_end_string="#>",
    )

    # Register custom filters
    env.filters["latex_escape"] = latex_escape

    return env


def render_cv(cv_data: CVData, template_name: str = "cv.tex.jinja") -> str:
    """Render CVData to LaTeX source code.

    Args:
        cv_data: The structured CV data to render.
        template_name: Name of the template file to use.

    Returns:
        LaTeX source code as a string.

    Raises:
        FileNotFoundError: If template directory or file doesn't exist.
        jinja2.TemplateError: If template rendering fails.

    Example:
        >>> from easycv.schemas.cv_model import CVData, Header, Section, ParagraphContent
        >>> cv = CVData(
        ...     header=Header(full_name="Marco Rossi", email="m@example.com"),
        ...     sections=[
        ...         Section(
        ...             kind="summary",
        ...             heading="Summary",
        ...             content=ParagraphContent(text="Experienced developer."),
        ...         )
        ...     ],
        ... )
        >>> latex = render_cv(cv)
        >>> "Marco Rossi" in latex
        True
    """
    template_dir = _get_template_dir()
    env = _create_jinja_env(template_dir)
    template = env.get_template(template_name)

    # Convert Pydantic model to dict for template rendering
    return template.render(
        header=cv_data.header.model_dump(),
        sections=[s.model_dump() for s in cv_data.sections],
    )
