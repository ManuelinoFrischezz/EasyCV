"""LaTeX rendering utilities.

This module provides functionality to convert CVData to LaTeX and compile to PDF.

Example:
    >>> from easycv.schemas.cv_model import CVData, Header
    >>> from easycv.rendering import render_cv, compile_latex
    >>>
    >>> cv = CVData(header=Header(full_name="Marco Rossi"))
    >>> latex_source = render_cv(cv)
    >>> pdf_bytes = compile_latex(latex_source)
"""

from easycv.rendering.compiler import (
    LatexCompilationError,
    compile_latex,
    compile_latex_to_file,
)
from easycv.rendering.latex import latex_escape, render_cv

__all__ = [
    "LatexCompilationError",
    "compile_latex",
    "compile_latex_to_file",
    "latex_escape",
    "render_cv",
]
