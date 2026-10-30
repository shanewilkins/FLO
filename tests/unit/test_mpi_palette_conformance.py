"""The pinned shared tokens and FLO-owned role adapter stay in agreement."""

import json

import pytest

from flo.render.legacy_sppm_themes import SPPM_THEMES
from flo.render.themes import BUILTIN_THEMES
from scripts.check_mpi_palette import check_palette


@pytest.fixture
def producer(tmp_path):
    # Independent pinned producer subset; no dependency on a sibling checkout.
    tokens = {
        "--mpi-canvas": "#f6f7f5",
        "--mpi-surface": "#ffffff",
        "--mpi-ink": "#1f2933",
        "--mpi-muted": "#5b6870",
        "--mpi-border": "#cdd5d5",
        "--mpi-primary": "#0b5d5a",
        "--mpi-warning": "#8a5a00",
        "--mpi-danger": "#a43232",
        "--mpi-info": "#1d5d88",
        "--mpi-table-stripe": "#f1f4f3",
        "--mpi-font-heading": '"Source Sans 3", system-ui, sans-serif',
    }
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "mpi-theme"\nversion = "0.1.5"\n'
    )
    path = tmp_path / "mpi_theme/assets/tokens.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(tokens))
    return tmp_path


def test_pinned_producer_and_legacy_roles_conform(producer):
    check_palette(producer)
    theme = BUILTIN_THEMES["mpi-lms"]
    assert theme.canvas_background.upper() == "#F6F7F5"
    assert theme.font_family == ("Source Sans 3", "system-ui", "sans-serif")
    for name, color in (("va", "#0B5D5A"), ("rnva", "#8A5A00"), ("nva", "#A43232")):
        assert theme.role(name).fill == color
    for name in ("va", "rnva", "nva", "decision", "queue", "unknown", "start_end"):
        shared = theme.role(name)
        legacy = getattr(SPPM_THEMES["mpi-lms"], name)
        assert (legacy.fill, legacy.border, legacy.title_fill, legacy.info_fill) == (
            shared.fill,
            shared.border,
            shared.title_text,
            shared.detail_text,
        )


@pytest.mark.parametrize(
    "token,value",
    [
        ("--mpi-primary", "#123456"),
        ("--mpi-font-heading", '"Another Font", sans-serif'),
        ("--mpi-border", None),
    ],
)
def test_changed_or_missing_shared_tokens_fail_conformance(producer, token, value):
    path = producer / "mpi_theme/assets/tokens.json"
    tokens = json.loads(path.read_text())
    if value is None:
        del tokens[token]
    else:
        tokens[token] = value
    path.write_text(json.dumps(tokens))
    with pytest.raises(ValueError, match="MPI token drift"):
        check_palette(producer)


def test_new_producer_version_requires_deliberate_snapshot_review(producer):
    path = producer / "pyproject.toml"
    path.write_text(path.read_text().replace('"0.1.5"', '"0.2.0"'))
    with pytest.raises(ValueError, match=r"Expected mpi-theme 0\.1\.5"):
        check_palette(producer)
