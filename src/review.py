"""Critical-only diff review.

Rules are stand-ins for a model call with a strict prompt. The discipline
is the same either way: flag only what would break production, ignore the
rest, and say when the diff was truncated.
"""
from __future__ import annotations

import re

MAX_DIFF_CHARS = 30000
CLEAN = "NO_CRITICAL_ISSUES"

SECRET_RE = re.compile(
    r"\b(api[_-]?key|password|secret|token)\s*=\s*[\"'][^\"']{8,}[\"']",
    re.IGNORECASE)
SQL_FSTRING_RE = re.compile(
    r"""(f["'].*\b(SELECT|INSERT|UPDATE|DELETE)\b.*\{.*\}.*["']|"""
    r"""\.execute\(\s*f["'])""", re.IGNORECASE)
EVAL_RE = re.compile(r"\b(eval|exec)\s*\(")
DESTRUCTIVE_RE = re.compile(
    r"\b(DROP\s+TABLE|DELETE\s+FROM\s+\w+\s*;|rm\s+-rf\s+/)", re.IGNORECASE)


def review_diff(diff: str) -> str:
    """Return findings text, or NO_CRITICAL_ISSUES when clean.

    Style, naming, minor improvements, and missing tests are deliberately
    not reviewed here — they are not critical.
    """
    truncated = len(diff) > MAX_DIFF_CHARS
    text = diff[:MAX_DIFF_CHARS] if truncated else diff
    findings = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        if SECRET_RE.search(line):
            findings.append(f"Line {lineno}: hardcoded secret committed in source.")
        elif SQL_FSTRING_RE.search(line):
            findings.append(f"Line {lineno}: SQL built with string interpolation (injection risk).")
        elif EVAL_RE.search(line):
            findings.append(f"Line {lineno}: eval()/exec() runs a string as code.")
        elif DESTRUCTIVE_RE.search(line):
            findings.append(f"Line {lineno}: destructive operation without a guard.")
    if not findings:
        if truncated:
            return (CLEAN + "\n\n(Diff truncated at 30,000 characters — "
                    "only the first part of the change was reviewed.)")
        return CLEAN
    out = "\n".join(f"- {f}" for f in findings)
    if truncated:
        out += ("\n\n(Diff truncated at 30,000 characters — findings above "
                "cover only the first part of the change.)")
    return out
