"""Tests for scripts.audit_project.
Just ensures that main() executes without raising and produces a report file in a temp dir.
"""

from pathlib import Path
import tempfile
import sys

from scripts import audit_project


def test_audit_main_runs(monkeypatch):
    """Smoke test: the audit script should run and create a file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = Path(tmpdir) / "report.md"

        # Patch ROOT to current repo root so the audit finds files
        monkeypatch.setattr(audit_project, "ROOT", Path(".").resolve())

        # Inject custom argv so main() writes to our tmpdir
        monkeypatch.setattr(sys, "argv", ["audit_project.py", "--output", str(report_path)])

        # Avoid recursive pytest invocation inside audit during test run
        monkeypatch.setattr(audit_project, "unit_tests", lambda: "**Status:** ✅ (skipped in test)")

        # Execute the script; it should not raise
        audit_project.main()

        # Verify report file got created
        assert report_path.exists() and report_path.stat().st_size > 0 