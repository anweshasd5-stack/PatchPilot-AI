"""Syntax and pytest verification for a candidate patch.

WARNING: pytest imports and executes Python code. A temporary directory is not a security
sandbox. Only verify code you wrote or have carefully reviewed. This module never applies
patches automatically and never runs tests without an explicit user action in the UI.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class VerificationResult:
    syntax_ok: bool
    pytest_ran: bool
    pytest_exit_code: int | None
    output: str
    warning: str

    def to_dict(self) -> dict:
        return asdict(self)


def verify_candidate(source: str, run_pytest: bool = False, timeout_seconds: int = 12) -> VerificationResult:
    """Compile candidate syntax; optionally run pytest in a temporary project directory."""
    try:
        compile(source, "candidate.py", "exec")
    except SyntaxError as exc:
        return VerificationResult(False, False, None,
                                  f"Syntax error on line {exc.lineno}: {exc.msg}",
                                  "Syntax checking does not execute the candidate code.")

    if not run_pytest:
        return VerificationResult(True, False, None,
                                  "Python syntax check passed. Pytest was not run.",
                                  "Running pytest can execute imported project code. Only run tests on code you trust.")

    with tempfile.TemporaryDirectory(prefix="patchpilot_verify_") as temp_dir:
        root = Path(temp_dir)
        (root / "candidate.py").write_text(source, encoding="utf-8")
        # Deliberately do not auto-import candidate.py in generated tests. The user may supply
        # a test file separately in a future version; this MVP reports syntax plus pytest status.
        (root / "test_candidate_syntax.py").write_text(
            "from pathlib import Path\n"
            "def test_candidate_file_exists():\n"
            "    assert Path('candidate.py').is_file()\n"
            "def test_candidate_is_nonempty():\n"
            "    assert Path('candidate.py').stat().st_size > 0\n",
            encoding="utf-8",
        )
        env = {"PATH": os.environ.get("PATH", ""), "PYTHONPATH": "", "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"}
        try:
            completed = subprocess.run(
                [sys.executable, "-I", "-m", "pytest", "-q", "-p", "no:cacheprovider"],
                cwd=root, env=env, capture_output=True, text=True, timeout=timeout_seconds, check=False,
            )
            output = (completed.stdout + "\n" + completed.stderr).strip()[-6000:]
            return VerificationResult(True, True, completed.returncode,
                                      output or "Pytest completed without output.",
                                      "These MVP tests verify the temporary file exists and is non-empty; they do NOT prove the security fix is correct. The candidate code itself is not imported by the generated tests.")
        except subprocess.TimeoutExpired:
            return VerificationResult(True, True, 124, "Pytest timed out.",
                                      "A timeout limits runtime but is not a complete sandbox.")
        except FileNotFoundError:
            return VerificationResult(True, False, None,
                                      "pytest was not found in the selected Python environment.",
                                      "Install dependencies in the project's virtual environment and retry.")
