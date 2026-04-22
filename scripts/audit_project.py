"""WhisperForge deep audit script.

Produces a markdown report with quality, security, and reliability checks.
"""

from __future__ import annotations

import argparse
import ast
import json
import logging
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Sequence

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[1]
REPORT_HEADER = "# WhisperForge Deep Audit Report\n"
TODO_PATTERN = re.compile(r"\b(TODO|FIXME)\b")
SECRET_PATTERN = re.compile(
    r"(api[_-]?key|token|secret|password)\s*=\s*['\"][^'\"]{16,}['\"]",
    re.IGNORECASE,
)
RISKY_PATTERN = re.compile(r"\b(eval|exec|pickle\.loads|yaml\.load\(|subprocess\.run\()")

IGNORED_DIRS = {".git", "venv", ".venv", "__pycache__", ".mypy_cache", ".pytest_cache"}


def iter_python_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*.py"):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        files.append(path)
    return sorted(files)


def _run(cmd: Sequence[str], timeout: int = 60) -> tuple[int, str, str]:
    """Run command and return (code, stdout, stderr)."""
    LOGGER.info("Running: %s", " ".join(cmd))
    try:
        proc = subprocess.run(
            list(cmd),
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except subprocess.TimeoutExpired:
        return 124, "", f"Timed out after {timeout}s: {' '.join(cmd)}"


def _section(title: str, body: str) -> str:
    return f"\n## {title}\n\n{body}\n"


def _code_block(text: str) -> str:
    return f"```\n{text or '(no output)'}\n```"


def unit_tests() -> str:
    rc, out, err = _run([sys.executable, "-m", "pytest", "-q"])
    output = "\n".join(p for p in [out, err] if p).strip()
    return f"**Status:** {'✅' if rc == 0 else '❌'}\n\n{_code_block(output)}"


def static_analysis() -> str:
    checks: list[tuple[str, Sequence[str]]] = [
        ("Ruff", ["ruff", "check", "."]),
        ("Mypy (strict core)", ["mypy", "--strict", "core"]),
        ("Bandit", [sys.executable, "-m", "bandit", "-q", "-r", "core", "shared", "app.py", "app_simple.py"]),
    ]
    parts: list[str] = []
    for name, cmd in checks:
        rc, out, err = _run(cmd)
        output = "\n".join(p for p in [out, err] if p).strip()
        parts.append(f"### {name}\nExit code: {rc}\n\n{_code_block(output)}")
    return "\n\n".join(parts)


def syntax_audit() -> str:
    failures: list[str] = []
    for file_path in iter_python_files():
        rel = file_path.relative_to(ROOT)
        try:
            source = file_path.read_text(encoding="utf-8")
            ast.parse(source)
        except SyntaxError as exc:
            failures.append(f"- {rel}:{exc.lineno}:{exc.offset} {exc.msg}")

    if failures:
        return "**Status:** ❌ Syntax errors detected\n\n" + "\n".join(failures)
    return "**Status:** ✅ All Python files parse successfully."


def secret_scan() -> str:
    hits: list[str] = []
    for file_path in iter_python_files():
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        for match in SECRET_PATTERN.finditer(content):
            rel = file_path.relative_to(ROOT)
            snippet = content[max(0, match.start() - 18): match.end() + 18].replace("\n", " ")
            hits.append(f"- {rel}: `{snippet.strip()}`")
    if hits:
        return "**Status:** ❌ Potential hard-coded secrets found\n\n" + "\n".join(hits)
    return "**Status:** ✅ No obvious hard-coded credentials found."


def risky_api_scan() -> str:
    counts: Counter[str] = Counter()
    locations: list[str] = []
    for file_path in iter_python_files():
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        for match in RISKY_PATTERN.finditer(content):
            token = match.group(1)
            counts[token] += 1
            locations.append(f"- {file_path.relative_to(ROOT)}: `{token}`")

    if not counts:
        return "No risky APIs detected by heuristic scan."

    summary = "\n".join(f"- `{k}`: {v}" for k, v in counts.most_common())
    sample = "\n".join(locations[:25])
    return f"### Counts\n{summary}\n\n### Sample locations\n{sample}"


def dependency_freshness() -> str:
    rc, out, err = _run([sys.executable, "-m", "pip", "list", "--outdated", "--format", "json"], timeout=90)
    if rc != 0:
        output = "\n".join(p for p in [out, err] if p).strip()
        return f"Unable to collect outdated dependencies.\n\n{_code_block(output)}"

    raw = out.strip()
    if not raw:
        return "Could not parse pip outdated output (empty stdout)."
    start = raw.find("[")
    end = raw.rfind("]")
    if start == -1 or end == -1 or end < start:
        return f"Could not parse pip outdated output.\n\n{_code_block(raw)}"
    packages = json.loads(raw[start:end+1])
    if not packages:
        return "All installed packages are up to date."
    lines = [f"- {p['name']} {p['version']} → {p['latest_version']}" for p in packages]
    return "Outdated packages:\n" + "\n".join(lines)


def todo_tally() -> str:
    total = 0
    by_file: list[tuple[str, int]] = []
    for file_path in iter_python_files():
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        count = len(TODO_PATTERN.findall(content))
        if count:
            by_file.append((str(file_path.relative_to(ROOT)), count))
            total += count

    top = "\n".join(f"- {path}: {count}" for path, count in by_file[:20]) or "- none"
    return f"Total TODO/FIXME markers: **{total}**\n\n{top}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a deep audit and write a Markdown report.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(f"AUDIT_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"),
    )
    args = parser.parse_args()

    report_parts = [REPORT_HEADER]
    report_parts.append(
        _section(
            "Metadata",
            f"Generated: {datetime.now().isoformat()}\n\nRoot: `{ROOT}`",
        )
    )
    report_parts.append(_section("Unit Tests", unit_tests()))
    report_parts.append(_section("Syntax Audit", syntax_audit()))
    report_parts.append(_section("Static Analysis", static_analysis()))
    report_parts.append(_section("Secrets Scan", secret_scan()))
    report_parts.append(_section("Risky API Scan", risky_api_scan()))
    report_parts.append(_section("Dependency Freshness", dependency_freshness()))
    report_parts.append(_section("TODO / FIXME Tally", todo_tally()))

    args.output.write_text("\n".join(report_parts), encoding="utf-8")
    print(f"Audit report written to {args.output}")


if __name__ == "__main__":
    main()
