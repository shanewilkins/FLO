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
uv sync --dev
npm ci --ignore-scripts --no-audit --no-fund
```

Python 3.14 or newer is required.

## Standard Validation

Run the same gates expected in CI:

```bash
uv run pre-commit run --all-files
```

Useful focused checks:

```bash
uv run pytest -q
uv run pytest --cov=src/flo --cov-report=term-missing --cov-fail-under=90
```

## Coding and Documentation Expectations

- Follow existing code style and naming conventions.
- Keep module boundaries intact (import-linter contracts are enforced).
- Update specs/docs when behavior changes.
- Prefer behavioral tests over coverage-only tests.

Documentation authority order is defined in `docs/policy/authoritative_artifacts.md`.

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
