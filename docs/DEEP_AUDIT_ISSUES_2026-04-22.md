# Deep Audit Remediation Issues (Generated from 2026-04-22 Audit)

This backlog translates the findings in `docs/DEEP_CODE_AUDIT_2026-04-22.md` into actionable GitHub issues.

## How to use
- Create one GitHub issue per section below.
- Keep issue titles exactly as written (or close) for traceability.
- Link each issue back to the audit report section.

---

## P0 (Blockers)

### 1) Fix fatal syntax regression in `app_simple.py`
**Labels:** `bug`, `p0`, `stability`

**Problem**
`app_simple.py` has indentation/syntax errors around lines ~1728–1857, preventing clean static parsing and likely breaking app execution paths.

**Acceptance criteria**
- `app_simple.py` parses successfully.
- `ruff check .` no longer reports `invalid-syntax` for this file.
- Audio upload control flow works for both standard and enhanced upload branches.

**References**
- Syntax Audit + Ruff output in `docs/DEEP_CODE_AUDIT_2026-04-22.md`.

---

### 2) Establish baseline CI gate for syntax + tests
**Labels:** `devops`, `p0`, `quality`

**Problem**
Critical syntax regressions were not blocked before merge.

**Acceptance criteria**
- CI job runs `python -m pytest -q` and a syntax parse pass (`python -m py_compile` or equivalent).
- PRs fail on syntax regressions.
- Add status badge/reference in README.

---

## P1 (High priority)

### 3) Reduce `core/` strict typing debt (mypy: 264 errors)
**Labels:** `tech-debt`, `typing`, `p1`

**Problem**
`mypy --strict core` reports 264 errors across 16 files.

**Acceptance criteria**
- Split into child issues by module cluster (see Issues 4–9).
- Each child issue includes before/after error counts.
- Parent issue tracks burn-down to zero.

---

### 4) Type harden `core/content_generation.py` and `core/utils.py`
**Labels:** `typing`, `p1`

**Acceptance criteria**
- Resolve implicit Optional/default mismatches.
- Add missing return annotations.
- Remove `Any` returns where strict types are declared.

---

### 5) Type harden `core/file_upload.py`
**Labels:** `typing`, `p1`, `large-files`

**Acceptance criteria**
- Add missing argument/return type annotations.
- Resolve undefined symbols (e.g., `AudioSegment`).
- Fix incorrect imports/exports causing type and attr errors.

---

### 6) Type harden `core/session_manager.py` + `core/auth_wrapper.py`
**Labels:** `typing`, `auth`, `p1`

**Acceptance criteria**
- Fix union-indexing and attr access on ambiguous session-state types.
- Add concrete typed wrappers for auth/session accessors.
- Eliminate strict-mode call-to-untyped warnings in this area.

---

### 7) Type harden streaming pipeline modules
**Labels:** `typing`, `pipeline`, `p1`

**Scope**
- `core/streaming_pipeline.py`
- `core/streaming_results.py`

**Acceptance criteria**
- Fix mismatched function signatures (`Too many arguments` errors).
- Annotate render/helpers and remove untyped call chains.
- Ensure JSON-like structures are typed before indexed access.

---

### 8) Type harden monitoring/logging modules
**Labels:** `typing`, `observability`, `p1`

**Scope**
- `core/logging_config.py`
- `core/monitoring.py`
- `core/streamlit_monitoring.py`

**Acceptance criteria**
- Fix `LoggerAdapter` type parameter/inheritance mismatches.
- Add missing generic parameters (`Dict`, `Callable`, etc.).
- Remove strict-mode override incompatibilities.

---

### 9) Type harden integration modules
**Labels:** `typing`, `integration`, `p1`

**Scope**
- `core/supabase_integration.py`
- `core/health_check.py`
- `core/metrics_exporter.py`

**Acceptance criteria**
- Fix missing stubs/import typing strategy.
- Resolve Optional/default mismatches.
- Remove `Any` return leaks for declared concrete return types.

---

### 10) Lint cleanup pass for unused imports/variables and invalid f-strings
**Labels:** `lint`, `p1`, `cleanup`

**Problem**
Ruff reports many `F401`, `F841`, `F541`, etc.

**Acceptance criteria**
- Remove dead imports/locals and unnecessary f-strings.
- No Ruff errors in files touched by the PR.
- Introduce `ruff --fix` in pre-commit (optional in CI initially).

---

### 11) Security tooling enablement (Bandit)
**Labels:** `security`, `p1`, `tooling`

**Problem**
Bandit is missing from environment, so SAST findings are unknown.

**Acceptance criteria**
- Add Bandit to dev requirements and CI.
- Run Bandit on `core/`, `shared/`, and app entrypoints.
- Triage and create follow-up issues for true positives.

---

### 12) Triage risky API usage (`exec`, `eval`, subprocess)
**Labels:** `security`, `p1`

**Problem**
Heuristic scan found non-trivial risky API usage counts.

**Acceptance criteria**
- Inventory all `exec`/`eval`/shell execution usages.
- Document justification or replace with safer alternatives.
- Add tests guarding against user-controlled code execution.

---

## P2 (Medium priority)

### 13) Dependency update campaign
**Labels:** `dependencies`, `p2`

**Problem**
Multiple outdated packages listed in audit output.

**Acceptance criteria**
- Update dependencies in safe batches.
- Run tests after each batch.
- Note breaking changes and pin rationale in changelog.

---

### 14) Secrets scanning policy and false-positive handling
**Labels:** `security`, `p2`, `tooling`

**Problem**
One test credential-like string was flagged; policy unclear.

**Acceptance criteria**
- Add secret scanning tool configuration and suppression workflow.
- Replace literal test credential strings with clearly fake fixtures/constants.
- Document process in CONTRIBUTING.

---

### 15) TODO/FIXME governance
**Labels:** `process`, `p2`

**Problem**
TODO/FIXME comments are present and currently unmanaged.

**Acceptance criteria**
- Require TODO entries to include issue IDs.
- Add periodic TODO audit script/check.
- Create issues for unresolved TODO clusters.

---

## Suggested execution order
1. Issue 1 (syntax blocker)
2. Issue 2 (CI guardrail)
3. Issues 4–9 in parallel (typed module clusters)
4. Issue 10 (lint stabilization)
5. Issues 11–12 (security tooling + risky API triage)
6. Issues 13–15 (dependency/process hardening)
