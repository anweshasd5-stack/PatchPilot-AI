"""AST-based, heuristic security scanner for Python source code.

This is a lightweight educational scanner, not a replacement for a dedicated SAST tool.
"""
from __future__ import annotations

import ast
import re
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class Finding:
    rule_id: str
    title: str
    severity: str
    line: int
    column: int
    evidence: str
    explanation: str
    recommendation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


RULES = {
    "PP001": "Avoid eval() and exec() on dynamic input.",
    "PP002": "Avoid shell=True when invoking subprocess with untrusted input.",
    "PP003": "Potential hardcoded credential or API key.",
    "PP004": "Avoid pickle.load() on untrusted data.",
    "PP005": "Avoid unsafe YAML loading; use yaml.safe_load().",
    "PP006": "Avoid assert for runtime security checks.",
}

_SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|password|passwd|token)\s*=\s*(['\"])([^'\"]{6,})\2"),
    re.compile(r"\b(?:AKIA[0-9A-Z]{16})\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
]


def _source_lines(source: str) -> list[str]:
    return source.splitlines()


def scan_python(source: str) -> list[Finding]:
    """Scan source using Python AST and conservative line-based secret patterns."""
    findings: list[Finding] = []
    lines = _source_lines(source)

    def add(rule_id: str, title: str, severity: str, line: int, col: int,
            evidence: str, explanation: str, recommendation: str) -> None:
        findings.append(Finding(rule_id, title, severity, max(1, line), max(0, col),
                                evidence.strip()[:500], explanation, recommendation))

    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        add("PP000", "Source could not be parsed", "INFO", exc.lineno or 1,
            (exc.offset or 1) - 1, (lines[(exc.lineno or 1) - 1] if lines else ""),
            f"Python could not parse this source: {exc.msg}.",
            "Fix the syntax error before relying on AST-based scan results.")
        return findings

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = node.func.id if isinstance(node.func, ast.Name) else (
                node.func.attr if isinstance(node.func, ast.Attribute) else "")
            line = getattr(node, "lineno", 1)
            col = getattr(node, "col_offset", 0)
            evidence = lines[line - 1] if 0 < line <= len(lines) else ast.unparse(node)
            if name in {"eval", "exec"}:
                add("PP001", f"Dynamic code execution via {name}()", "CRITICAL", line, col,
                    evidence, f"{name}() interprets a string as Python code. If the value can be influenced by an attacker, it may enable arbitrary code execution.",
                    "Avoid dynamic evaluation. Replace it with explicit parsing, a safe mapping, or a narrowly defined operation.")
            if name == "Popen" or name in {"run", "call", "check_call", "check_output"}:
                shell_true = any(k.arg == "shell" and isinstance(k.value, ast.Constant) and k.value.value is True for k in node.keywords)
                if shell_true:
                    add("PP002", "Subprocess called with shell=True", "HIGH", line, col, evidence,
                        "shell=True passes a command through a shell. Concatenated or attacker-controlled input can become command injection.",
                        "Pass an argument list with shell=False (the default), validate each argument, and avoid string concatenation for commands.")
            if name == "load" and isinstance(node.func, ast.Attribute) and node.func.attr == "load":
                if isinstance(node.func.value, ast.Name) and node.func.value.id == "pickle":
                    add("PP004", "Potential unsafe pickle deserialization", "HIGH", line, col, evidence,
                        "Unpickling untrusted bytes can execute attacker-controlled code during deserialization.",
                        "Do not unpickle untrusted data. Prefer JSON or another non-executable data format.")
                if isinstance(node.func.value, ast.Name) and node.func.value.id == "yaml":
                    loader = next((k.value for k in node.keywords if k.arg == "Loader"), None)
                    if not (isinstance(loader, ast.Attribute) and loader.attr == "SafeLoader"):
                        add("PP005", "Potential unsafe YAML deserialization", "MEDIUM", line, col, evidence,
                            "yaml.load() without a safe loader may construct arbitrary Python objects, depending on the YAML library/version.",
                            "Use yaml.safe_load() or yaml.load(data, Loader=yaml.SafeLoader) for untrusted YAML.")
        if isinstance(node, ast.Assert):
            line = getattr(node, "lineno", 1)
            evidence = lines[line - 1] if 0 < line <= len(lines) else "assert"
            add("PP006", "Security check implemented with assert", "LOW", line, getattr(node, "col_offset", 0), evidence,
                "Python can remove assert statements when optimization is enabled, so they should not enforce runtime security or input validation.",
                "Use an explicit if-check and raise a suitable exception for security-sensitive validation.")

    for line_no, line in enumerate(lines, start=1):
        for pattern in _SECRET_PATTERNS:
            match = pattern.search(line)
            if match:
                value = match.group(0)
                # Do not include the full suspected secret in the finding evidence.
                redacted = re.sub(r"(['\"])[^'\"]+(['\"])", r"\1[REDACTED]\2", value)
                add("PP003", "Possible hardcoded secret", "HIGH", line_no, match.start(),
                    line.replace(value, redacted),
                    "A credential-like value appears to be assigned directly in source code. This is heuristic and may be a false positive.",
                    "Rotate any real exposed credential, remove it from source history where appropriate, and load it from an environment variable or secret manager.")
                break

    # Stable order makes reports reproducible and avoids duplicate line/rule findings.
    unique: dict[tuple[str, int, str], Finding] = {}
    for finding in findings:
        unique[(finding.rule_id, finding.line, finding.title)] = finding
    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
    return sorted(unique.values(), key=lambda f: (severity_order.get(f.severity, 9), f.line, f.rule_id))
