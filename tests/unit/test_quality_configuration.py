"""The configured Ruff gates enforce complexity and correctness policies."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]


def _check_source(source: str, filename: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603 - Trusted interpreter and fixed Ruff invocation.
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "--output-format",
            "json",
            "--stdin-filename",
            filename,
            "-",
        ],
        input=source,
        text=True,
        capture_output=True,
        cwd=_ROOT,
        check=False,
    )


@pytest.mark.parametrize("complexity", [15, 16])
@pytest.mark.parametrize(
    "filename",
    [
        "src/flo/render/themes.py",
        "src/flo/process/analysis/timing.py",
        "src/flo/process/ir/validate.py",
        "src/flo/source/_adapter_normalization.py",
        "src/flo/source/diagnostics.py",
        "tests/unit/test_render_themes.py",
        "scripts/check_sppm_geometry.py",
    ],
)
def test_complexity_limit_applies_without_historical_file_exclusions(
    complexity, filename
):
    branches = "".join(
        f"    if value == {index}:\n        value += 1\n"
        for index in range(complexity - 1)
    )
    source = (
        '"""Candidate lint source."""\n\n'
        'def candidate(value):\n    """Return the candidate value."""\n'
        f"{branches}    return value\n"
    )
    result = _check_source(source, filename)
    assert result.returncode == (0 if complexity == 15 else 1), result.stderr
    records = json.loads(result.stdout)
    assert [item["code"] for item in records] == ([] if complexity == 15 else ["C901"])
    if records:
        assert "(16 > 15)" in records[0]["message"]


@pytest.mark.parametrize(
    ("code", "source"),
    [
        ("PLE0101", "class Candidate:\n    def __init__(self):\n        return 1\n"),
        ("DTZ005", "import datetime\nvalue = datetime.datetime.now()\n"),
        ("LOG015", "import logging\nlogging.error('failed')\n"),
        (
            "G004",
            (
                "import logging\nvalue = 42\n"
                "logging.getLogger(__name__).error(f'value={value}')\n"
            ),
        ),
        ("PGH003", "value = 1  # type: ignore\n"),
        ("ISC004", "values = ['first' 'second']\n"),
        ("PLW1510", "import subprocess\nsubprocess.run(['node'])\n"),
        ("PT011", "import pytest\nwith pytest.raises(ValueError):\n    int('bad')\n"),
        (
            "PT012",
            (
                "import pytest\nwith pytest.raises(ValueError, match='invalid'):\n"
                "    int('bad')\n    int('also bad')\n"
            ),
        ),
        (
            "PT017",
            (
                "try:\n    int('bad')\nexcept ValueError as exc:\n"
                "    assert str(exc) == 'invalid'\n"
            ),
        ),
        ("S102", "exec('value = 1')\n"),
        (
            "S110",
            "try:\n    int('bad')\nexcept Exception:\n    pass\n",
        ),
        (
            "S112",
            (
                "for value in ['bad']:\n    try:\n        int(value)\n"
                "    except Exception:\n        continue\n"
            ),
        ),
        ("S324", "import hashlib\nhashlib.sha1(b'palette')\n"),
        (
            "S603",
            "import subprocess\ncommand = input()\nsubprocess.run([command], check=True)\n",
        ),
    ],
)
def test_correctness_rules_are_enforced(code, source):
    result = _check_source(source, "tests/unit/test_candidate.py")

    assert result.returncode == 1, result.stderr
    assert code in {item["code"] for item in json.loads(result.stdout)}


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("src/flo/candidate.py", {"D100", "D103"}),
        ("scripts/candidate.py", {"D100", "D103"}),
        ("tests/conftest.py", {"D100", "D103"}),
        ("tests/unit/test_candidate.py", set()),
    ],
)
def test_docstring_rules_preserve_the_previous_filename_scope(filename, expected):
    result = _check_source("def candidate():\n    return 1\n", filename)

    assert result.returncode == (1 if expected else 0), result.stderr
    assert {item["code"] for item in json.loads(result.stdout)} == expected


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("src/flo/candidate.py", {"S101"}),
        ("scripts/candidate.py", {"S101"}),
        ("tests/conftest.py", set()),
        ("tests/unit/test_candidate.py", set()),
    ],
)
def test_security_assertion_exception_is_limited_to_tests(filename, expected):
    result = _check_source('"""Candidate lint source."""\nassert True\n', filename)

    assert result.returncode == (1 if expected else 0), result.stderr
    assert {item["code"] for item in json.loads(result.stdout)} == expected
