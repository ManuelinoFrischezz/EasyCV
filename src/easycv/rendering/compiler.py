"""Compile LaTeX source to PDF using Tectonic.

Tectonic is a self-contained LaTeX engine that automatically downloads
required packages. It produces PDF output without needing a full TeX
distribution installed.

Example:
    >>> latex_source = r"\\documentclass{article}\\begin{document}Hello\\end{document}"
    >>> pdf_bytes = compile_latex(latex_source)
    >>> pdf_bytes[:4]
    b'%PDF'
"""

import subprocess
import tempfile
from pathlib import Path


class LatexCompilationError(Exception):
    """Raised when LaTeX compilation fails.

    Attributes:
        latex_source: The LaTeX source that failed to compile.
        stderr: The error output from Tectonic.
    """

    def __init__(self, message: str, latex_source: str, stderr: str) -> None:
        super().__init__(message)
        self.latex_source = latex_source
        self.stderr = stderr


def compile_latex(latex_source: str, timeout: int = 120) -> bytes:
    """Compile LaTeX source to PDF bytes using Tectonic.

    Args:
        latex_source: LaTeX source code as a string.
        timeout: Maximum time in seconds to wait for compilation.

    Returns:
        PDF file content as bytes.

    Raises:
        LatexCompilationError: If compilation fails.
        FileNotFoundError: If Tectonic is not installed.
        subprocess.TimeoutExpired: If compilation exceeds timeout.

    Example:
        >>> source = r'''
        ... \\documentclass{article}
        ... \\begin{document}
        ... Hello, World!
        ... \\end{document}
        ... '''
        >>> pdf = compile_latex(source)
        >>> len(pdf) > 0
        True
    """
    # Check if tectonic is available
    _check_tectonic_installed()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        tex_file = tmppath / "cv.tex"
        pdf_file = tmppath / "cv.pdf"

        # Write LaTeX source to temp file
        tex_file.write_text(latex_source, encoding="utf-8")

        # Run Tectonic
        result = subprocess.run(
            [
                "tectonic",
                "-X",
                "compile",
                str(tex_file),
                "--outdir",
                str(tmppath),
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=tmppath,
            check=False,  # We handle errors manually below
        )

        if result.returncode != 0:
            raise LatexCompilationError(
                f"Tectonic compilation failed with exit code {result.returncode}",
                latex_source=latex_source,
                stderr=result.stderr,
            )

        if not pdf_file.exists():
            raise LatexCompilationError(
                "Tectonic completed but PDF file was not created",
                latex_source=latex_source,
                stderr=result.stderr,
            )

        return pdf_file.read_bytes()


def compile_latex_to_file(latex_source: str, output_path: Path, timeout: int = 120) -> Path:
    """Compile LaTeX source and save PDF to a file.

    Args:
        latex_source: LaTeX source code as a string.
        output_path: Path where the PDF should be saved.
        timeout: Maximum time in seconds to wait for compilation.

    Returns:
        Path to the created PDF file.

    Raises:
        LatexCompilationError: If compilation fails.
        FileNotFoundError: If Tectonic is not installed.
    """
    pdf_bytes = compile_latex(latex_source, timeout=timeout)

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(pdf_bytes)

    return output_path


def _check_tectonic_installed() -> None:
    """Verify that Tectonic is installed and accessible.

    Raises:
        FileNotFoundError: If Tectonic is not found in PATH.
    """
    try:
        result = subprocess.run(
            ["tectonic", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if result.returncode != 0:
            raise FileNotFoundError("Tectonic returned non-zero exit code")
    except FileNotFoundError:
        raise FileNotFoundError(
            "Tectonic is not installed. Install it with: brew install tectonic"
        ) from None
