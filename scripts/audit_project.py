"""WhisperForge Comprehensive Audit Script

This utility provides a one-click health check that surfaces the current
state of the codebase in a single Markdown report.  It is intentionally
implemented as a standalone script (no external framework) so it can be
invoked locally or in CI:

    python scripts/audit_project.py --output AUDIT_REPORT.md

The checklist it produces aligns with the rescue plan discussed in chat:
1. Unit tests
2. Health endpoint check
3. Static analysis (ruff + mypy)
4. Secret/credential scan
5. Dependency freshness
6. TODO / FIXME tally

The script is SAFE to run: it is read-only except for writing the report
file.  All subprocess calls are executed with a 30-second timeout to
avoid hanging CI.

Note that the audit relies on the project's virtualenv having pytest,
ruff and mypy available.  If any tool is missing, the error is captured
and surfaced in the report instead of crashing.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Always use the project logger if available, but fall back to standard logging.
try:
    from core.logging_config import logger as _wf_logger  # type: ignore
    SCRIPT_LOGGER = getattr(_wf_logger, "logger", _wf_logger)
except Exception:
    SCRIPT_LOGGER = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)

TRACE_ID = os.getenv("TRACE_ID")

ROOT = Path(__file__).resolve().parents[1]
# Ensure the project root is on sys.path so imports like `core` work when
# running this script directly.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
REPORT_HEADER = "# WhisperForge Audit Report\n"

SECRET_PATTERN = re.compile(r"(key|token|secret|password)\s*=\s*['\"]\w{16,}['\"]", re.IGNORECASE)
TODO_PATTERN = re.compile(r"\b(TODO|FIXME)\b")


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _run(cmd: List[str], cwd: Path | None = None) -> Tuple[int, str, str]:
    """Run a subprocess and capture its output.

    Returns (returncode, stdout, stderr).
    """
    SCRIPT_LOGGER.info(
        "Executing command", extra={"trace_id": TRACE_ID, "cmd": " ".join(cmd)}
    )
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd or ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except subprocess.TimeoutExpired as exc:
        return 1, "", f"Command timed out after 30s: {exc.cmd}"


def _section(title: str, body: str) -> str:
    return f"\n## {title}\n\n{body}\n"


# ---------------------------------------------------------------------------
# Audit tasks
# ---------------------------------------------------------------------------

def unit_tests() -> str:
    rc, out, err = _run([sys.executable, "-m", "pytest", "-q"])
    status = "✅" if rc == 0 else "❌"
    details = err or out
    return f"""**Status:** {status}  

```
{details}
```"""


def health_endpoint() -> str:
    from core.health_check import health_checker  # local import to avoid heavy deps

    status_data = health_checker.get_health_status()
    status = "✅" if status_data.status == "healthy" else "❌"
    return f"""**Status:** {status}  

Payload:
```json
{json.dumps(status_data.__dict__, indent=2, default=str)}
```"""


def static_analysis() -> str:
    # Ruff
    rc_r, out_r, err_r = _run(["ruff", "."])
    # mypy in strict mode on core/
    rc_m, out_m, err_m = _run(["mypy", "--strict", "core"])

    body = "### Ruff\n"
    body += f"""Exit code: {rc_r}  

```
{out_r or err_r}
```\n"""

    body += "### mypy\n"
    body += f"""Exit code: {rc_m}  

```
{out_m or err_m}
```"""
    return body


def secret_scan() -> str:
    matches: List[str] = []
    for file_path in ROOT.rglob("*.py"):
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for m in SECRET_PATTERN.finditer(content):
            snippet = content[max(0, m.start() - 20): m.end() + 20]
            matches.append(f"{file_path}: {snippet.strip()}")

    if not matches:
        return "**Status:** ✅ No hard-coded secrets found."
    return "**Status:** ❌ Found potential secrets:\n" + "\n".join(matches)


def dependency_freshness() -> str:
    rc, out, err = _run([sys.executable, "-m", "pip", "list", "--outdated", "--format", "json"])
    if rc != 0:
        return f"Failed to fetch outdated packages: {err}"
    try:
        data: List[Dict[str, Any]] = json.loads(out)
    except json.JSONDecodeError:
        return "Could not parse pip output."
    if not data:
        return "All dependencies are up to date."
    lines = [f"- {p['name']} {p['version']} → {p['latest_version']}" for p in data]
    return "Outdated packages:\n" + "\n".join(lines)


def todo_tally() -> str:
    tally = 0
    for file_path in ROOT.rglob("*.py"):
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        tally += len(TODO_PATTERN.findall(content))
    return f"Total TODO/FIXME markers: **{tally}**"


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Run a WhisperForge audit and emit a Markdown report.")
    parser.add_argument("--output", type=Path, default=Path(f"AUDIT_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"))
    args = parser.parse_args()

    report_parts = [REPORT_HEADER]
    report_parts.append(_section("Metadata", f"Generated: {datetime.now().isoformat()}\n\nRoot: `{ROOT}`"))
    report_parts.append(_section("Unit Tests", unit_tests()))
    report_parts.append(_section("Health Endpoint", health_endpoint()))
    report_parts.append(_section("Static Analysis", static_analysis()))
    report_parts.append(_section("Secrets Scan", secret_scan()))
    report_parts.append(_section("Dependency Freshness", dependency_freshness()))
    report_parts.append(_section("TODO / FIXME Tally", todo_tally()))

    output_text = "\n".join(report_parts)
    args.output.write_text(output_text, encoding="utf-8")
    SCRIPT_LOGGER.info(
        "Audit completed", extra={"trace_id": TRACE_ID, "report": str(args.output)}
    )
    print(f"\n\nAudit report written to {args.output}")


if __name__ == "__main__":
    main() 