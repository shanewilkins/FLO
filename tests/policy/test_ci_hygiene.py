"""Keep CI reproducible, bounded, and consistent with local quality gates."""

import os
import re
import shlex
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parents[2]


def _load(path):
    return yaml.safe_load((_ROOT / path).read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "path",
    [
        ".github/workflows/ci.yml",
        ".github/workflows/publish.yml",
        ".github/actions/setup/action.yml",
    ],
)
def test_external_actions_are_pinned_to_commits(path):
    document = _load(path)
    steps = (
        document["runs"]["steps"]
        if "runs" in document
        else [step for job in document["jobs"].values() for step in job["steps"]]
    )
    for step in steps:
        reference = step.get("uses")
        if reference is not None and not reference.startswith("./"):
            assert re.fullmatch(r"[^@]+@[0-9a-f]{40}", reference), reference


@pytest.mark.parametrize(
    "path", [".github/workflows/ci.yml", ".github/workflows/publish.yml"]
)
def test_workflows_enforce_locks_read_only_permissions_and_timeouts(path):
    document = _load(path)
    assert document["permissions"] == {"contents": "read"}
    assert document["env"]["UV_LOCKED"] == "true"
    for job in document["jobs"].values():
        assert 0 < job["timeout-minutes"] <= 30
        for step in job["steps"]:
            command = step.get("run", "")
            assert "pip install uv" not in command
            assert "uv sync\n" not in command + "\n"


def test_ci_cancels_superseded_runs_but_publication_is_not_interrupted():
    ci = _load(".github/workflows/ci.yml")
    publish = _load(".github/workflows/publish.yml")

    assert ci["concurrency"]["cancel-in-progress"] is True
    assert "${{ github.ref }}" in ci["concurrency"]["group"]
    assert publish["concurrency"]["cancel-in-progress"] is False


@pytest.mark.parametrize(
    "path", [".github/workflows/ci.yml", ".github/workflows/publish.yml"]
)
def test_ci_runs_the_full_suite_once_with_coverage_instead_of_plain_pytest(path):
    workflow = _load(path)
    commands = [
        step.get("run", "")
        for job in workflow["jobs"].values()
        for step in job["steps"]
    ]
    hooks = _load(".pre-commit-config.yaml")["repos"][-1]["hooks"]
    pytest_hook = next(hook for hook in hooks if hook["id"] == "pytest-check")
    quality_steps = [
        step
        for job in workflow["jobs"].values()
        for step in job["steps"]
        if "pre-commit run --all-files" in step.get("run", "")
    ]
    pytest_commands = [command for command in commands if " pytest" in command]

    assert len(quality_steps) == 1
    assert quality_steps[0]["env"]["SKIP"] == "pytest-check"
    assert len(pytest_commands) == 1
    assert shlex.split(pytest_commands[0]) == [
        *shlex.split(pytest_hook["entry"]),
        "--cov=src/flo",
        "--cov-report=term-missing",
        "--cov-fail-under=90",
    ]
    assert "sppm-determinism" not in workflow["jobs"]


def test_local_hooks_use_locked_tools_and_plain_pytest_without_obsolete_hooks():
    hooks = _load(".pre-commit-config.yaml")["repos"][-1]["hooks"]
    by_id = {hook["id"]: hook for hook in hooks}

    assert "vulture-check" not in by_id
    assert "ruff-ann401-advisory" not in by_id
    assert shlex.split(by_id["pytest-check"]["entry"]) == [
        "uv",
        "run",
        "--locked",
        "pytest",
    ]
    for hook in hooks:
        assert shlex.split(hook["entry"])[:3] == ["uv", "run", "--locked"]
    for hook_id in ("ruff-check", "ruff-format"):
        assert shlex.split(by_id[hook_id]["entry"])[-3:] == ["src", "tests", "scripts"]


def test_locked_ci_environment_rejects_manifest_drift_without_changing_lock(tmp_path):
    uv = shutil.which("uv")
    assert uv is not None
    manifest = tmp_path / "pyproject.toml"
    original = '[project]\nname = "lock-policy-probe"\nversion = "0.0.1"\nrequires-python = ">=3.14"\n'
    manifest.write_text(original, encoding="utf-8")
    environment = {
        **os.environ,
        "UV_LOCKED": "false",
        "UV_FROZEN": "false",
        "UV_CACHE_DIR": str(tmp_path / "uv-cache"),
    }
    result = subprocess.run(  # noqa: S603 - Trusted uv executable; isolated offline fixture.
        [uv, "lock", "--offline", "--project", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
        env=environment,
    )
    assert result.returncode == 0, result.stderr
    lock = tmp_path / "uv.lock"
    locked_content = lock.read_bytes()
    manifest.write_text(original.replace("0.0.1", "0.0.2"), encoding="utf-8")
    result = subprocess.run(  # noqa: S603 - Trusted uv executable; isolated offline fixture.
        [uv, "sync", "--dry-run", "--offline", "--project", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
        env={**environment, "UV_LOCKED": "true"},
    )

    assert result.returncode != 0
    assert "lockfile" in result.stderr.lower()
    assert lock.read_bytes() == locked_content


@pytest.mark.parametrize(
    "hook_id",
    [
        "ruff-format",
        "ruff-check",
        "ty-check",
        "pytest-check",
    ],
)
@pytest.mark.parametrize(
    "filename", ["pyproject.toml", "uv.lock", ".pre-commit-config.yaml"]
)
def test_python_quality_hooks_accept_configuration_only_changes(hook_id, filename):
    config = _load(".pre-commit-config.yaml")
    hook = next(
        hook
        for repo in config["repos"]
        for hook in repo["hooks"]
        if hook["id"] == hook_id
    )

    assert hook["types"] == ["file"]
    assert re.search(hook["files"], filename)


def test_publish_checks_tag_and_sdist_before_upload():
    steps = _load(".github/workflows/publish.yml")["jobs"]["build"]["steps"]
    tag_index = next(
        index for index, step in enumerate(steps) if "--tag" in step.get("run", "")
    )
    build_index = next(
        index
        for index, step in enumerate(steps)
        if "uv build --out-dir dist" in step.get("run", "")
    )
    smoke_index = next(
        index
        for index, step in enumerate(steps)
        if step.get("name") == "Smoke-test sdist-built wheel"
    )
    upload_index = next(
        index
        for index, step in enumerate(steps)
        if step.get("uses", "").startswith("actions/upload-artifact@")
    )

    assert tag_index < build_index < smoke_index < upload_index
    assert (
        steps[tag_index]["env"]["RELEASE_TAG"] == "${{ github.event.release.tag_name }}"
    )
    assert '--tag "$RELEASE_TAG"' in steps[tag_index]["run"]
    assert "uv build dist/*.tar.gz --wheel" in steps[build_index]["run"]
    assert "twine check --strict" in steps[build_index]["run"]
    assert "scripts/check_release_artifacts.py" in steps[build_index]["run"]
    assert "scripts/check_yb_journey.py" in steps[smoke_index]["run"]
