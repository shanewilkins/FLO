# Contributing to FLO

Thanks for your interest in contributing.
This document provides the minimum workflow to contribute safely and consistently.

## Ground Rules

- Be respectful and constructive in issues and pull requests.
- Keep changes scoped to one concern whenever possible.
- Include or update tests for behavior changes.
- Keep docs aligned with user-visible changes.

## Local Setup

From the repository root:

```bash
uv sync --dev --locked
npm ci --ignore-scripts --no-audit --no-fund
```

Python 3.14 or newer is required.
CI's Python, Node.js, and pinned uv setup is centralized in
[the toolchain action](.github/actions/setup/action.yml). CI enforces `UV_LOCKED`;
use `uv add`, `uv remove`, or an intentional lock update when changing dependencies.

## Standard Validation

Run the same gates expected in CI:

```bash
uv run --locked pre-commit run --all-files
```

Pre-commit runs the full test suite without coverage instrumentation. CI and
publication skip only the plain pytest hook and run the same suite once with
coverage, retaining the 90% threshold. Other quality gates are shared unchanged.
Every local Python hook uses `uv run --locked`, so checks cannot silently rewrite
the lockfile. Ruff formatting and linting cover `src`, `tests`, and `scripts`.
Configuration and lockfile changes trigger the relevant local gates even when
no Python file changes. The same hooks also check YAML, merge-conflict markers,
trailing whitespace, and GitHub Actions workflows with actionlint. Pre-commit
manages the pinned hook environments, including Go for actionlint if needed.
Markdown hard line breaks and generated golden/render artifacts are preserved.
Refresh hook revisions intentionally with `uv run --locked pre-commit autoupdate`, then
review the changes and rerun the gates. Review the pinned uv version in the
toolchain action when updating CI tooling.

Useful focused checks:

```bash
uv run --locked pytest -q
uv run --locked pytest --cov=src/flo --cov-report=term-missing --cov-fail-under=90
uv run --locked ruff check src tests scripts --select ANN401 --exit-zero
```

`ANN401` reports explicit `Any` annotations in function signatures. It is an
optional review command, not a commit gate. Vulture and its whitelist are no
longer maintained. Ruff detects unused imports and local variables, but does not
replace Vulture's cross-function detection of unused functions or attributes.

Ruff's correctness checks include `PLE`, timezone-aware datetime usage (`DTZ`),
logging checks (`LOG`, `G`), specific suppression codes (`PGH`), and implicit
string concatenation (`ISC`). Intentional concatenation in collections must be
parenthesized. Subprocess calls must explicitly choose `check=True` or
`check=False` (`PLW1510`); use the latter when the caller handles return codes.
Exception tests use `PT011`, `PT012`, and `PT017` to keep expectations specific
and exception-catching blocks focused.

Docstrings are checked by Ruff's `D` rules with the `pep257` convention, replacing
the separate pydocstyle hook. Files named `test_*.py` remain exempt from docstring
rules, matching the previous checker's default scope; other rules still apply.
Support modules such as `conftest.py` remain subject to docstring checks.

Ruff's Bandit-derived `S` rules apply to `src`, `tests`, and `scripts`. Only `S101`
(assertions) is exempt throughout tests. Other intentional uses require narrow,
explained exceptions: trusted renderer-generated SVG parsing, non-credential SVG
labels, and fixed subprocess invocations without a shell. Non-security hashes
must declare `usedforsecurity=False`; stable palette choices must not change.
Optional telemetry remains best-effort, with failures recorded at debug level.
The trace-enrichment logging processor cannot log its own failures recursively
and retains a narrowly scoped exception. These lint checks do not replace a
security review or dependency vulnerability alerts.

Ruff also enforces function complexity through `C901`, with a maximum McCabe
complexity of 15 across `src`, `tests`, and `scripts`. It runs in the existing Ruff hook;
there is no separate complexity checker or complexity-specific file exclusion.
Refactor functions that exceed the limit rather than raising the threshold.

This replaces the former Radon function/class gate, not its numeric metric.
Ruff does not provide Radon's class scores or Xenon's aggregate thresholds.
The structural SPPM refactor report retains size, boundary, and clone findings
but explicitly retires its historical Radon scores; do not compare those scores
directly with Ruff's.

## Coding and Documentation Expectations

- Follow existing code style and naming conventions.
- Keep module boundaries intact (import-linter contracts are enforced).
- Update specs/docs when behavior changes.
- Prefer behavioral tests over coverage-only tests.

Documentation authority order is defined in `docs/policy/authoritative_artifacts.md`.

## Dependency Updates

[Dependabot](.github/dependabot.yml) checks uv-managed Python dependencies,
GitHub Actions, and npm dependencies weekly, with at most five open version-update
PRs per ecosystem. Python updates maintain `pyproject.toml` and `uv.lock`.
Routine Python patch/minor updates are grouped; Pint and the Pydantic family
remain individually reviewable. Major-version updates stay outside the group.
ELK updates remain separate npm PRs.

Dependabot alerts and security-update PRs are enabled in repository settings.
Security updates are not included in the routine version-update group.
Automerge is disabled; dependency PRs require green CI and human review,
especially when units, validation, or diagram geometry may change.

For ELK updates, install the updated npm lockfile dependencies and regenerate the
vendored runtime with `uv run python scripts/vendor_elkjs.py` before validation.
Review golden-artifact differences rather than automatically accepting new
baselines. Use the standard validation gates above for dependency changes.

## Distribution and Release Acceptance

Linux CI validates both the direct wheel and a wheel rebuilt from the sdist.
Each archive must match the declared package identity and contain a nonempty
vendored ELK bundle and license. Both wheel paths are installed in fresh
environments and exercised through the installed CLI journey.

To check archives locally after installing Node dependencies:

```bash
uv run python scripts/vendor_elkjs.py
uv build --out-dir dist --sdist
uv build --out-dir dist --wheel
uv run twine check --strict dist/*
uv run python scripts/check_release_artifacts.py dist/*.whl dist/*.tar.gz
uv build dist/*.tar.gz --wheel --out-dir .tmp/sdist-wheel
uv run python scripts/check_release_artifacts.py .tmp/sdist-wheel/*.whl
```

Use a clean output directory when testing a new candidate; archive globs must not
include stale releases. Publication additionally requires the release tag to
equal `project.version`, optionally prefixed with lowercase `v`. A mismatch
blocks the build before dependency installation. Publication is serialized and
never cancels an active run; ordinary CI cancels superseded runs.

## Pull Request Guidance

Please include:

- Problem statement and scope.
- Why the chosen approach is correct.
- Tests added or updated.
- Documentation updates, if applicable.
- Any compatibility or migration notes.

Keep PRs reviewable.
Large refactors should be split into logical slices.

## Commit Messages

Use clear, scoped commit messages.
Conventional-style prefixes are recommended, for example:

- `feat(...)`
- `fix(...)`
- `refactor(...)`
- `docs(...)`
- `test(...)`

## Security

Do not disclose vulnerabilities in public issues.
See `SECURITY.md` for reporting instructions.
