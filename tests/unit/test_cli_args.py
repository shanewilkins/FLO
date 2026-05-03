from flo.services import get_services
from flo.core.cli_args import parse_args
import pytest


@pytest.fixture
def services():
    return get_services(verbose=False)


def test_parse_args_none_returns_defaults(services):
    path, command, options, services_out, logger = parse_args(None, services)
    assert path is None
    assert command == "run"
    assert isinstance(options, dict)
    assert services_out is services


@pytest.mark.parametrize(
    "args, expected_command, expected_output",
    [
        (["/tmp/input.flo", "-v", "-o", "out.txt", "--validate"], "validate", "out.txt"),
        (["file.flo"], "run", None),
    ],
)
def test_parse_args_with_flags(services, args, expected_command, expected_output):
    path, command, options, services_out, logger = parse_args(args, services)
    assert path == (args[0] if args else None)
    assert command == expected_command
    if expected_output:
        assert options["output"] == expected_output


@pytest.mark.parametrize(
    "extra_args, expected_export",
    [
        ([], "dot"),
        (["--export", "json"], "json"),
        (["--export", "ingredients"], "ingredients"),
        (["--export", "movement"], "movement"),
    ],
)
def test_parse_args_export_flag(services, extra_args: list[str], expected_export: str):
    path, command, options, _, _ = parse_args(["file.flo"] + extra_args, services)
    assert path == "file.flo"
    assert command == "run"
    assert options["export"] == expected_export


def test_parse_args_render_options(services):
    path, command, options, _, _ = parse_args(
        [
            "file.flo",
            "--diagram",
            "swimlane",
            "--profile",
            "analysis",
            "--detail",
            "verbose",
            "--orientation",
            "tb",
            "--show-notes",
            "--subprocess-view",
            "parent-only",
            "--spaghetti-channel",
            "people",
            "--spaghetti-people-mode",
            "worker",
        ],
        services,
    )
    assert path == "file.flo"
    assert command == "run"
    assert options["diagram"] == "swimlane"
    assert options["profile"] == "analysis"
    assert options["detail"] == "verbose"
    assert options["orientation"] == "tb"
    assert options["show_notes"] is True
    assert options["subprocess_view"] == "parent-only"
    assert options["spaghetti_channel"] == "people"
    assert options["spaghetti_people_mode"] == "worker"


def test_parse_args_spaghetti_diagram_option(services):
    path, command, options, _, _ = parse_args(["file.flo", "--diagram", "spaghetti"], services)
    assert path == "file.flo"
    assert command == "run"
    assert options["diagram"] == "spaghetti"


def test_parse_args_spaghetti_channel_option(services):
    path, command, options, _, _ = parse_args(["file.flo", "--spaghetti-channel", "material"], services)
    assert path == "file.flo"
    assert command == "run"
    assert options["spaghetti_channel"] == "material"


def test_parse_args_spaghetti_people_mode_option(services):
    path, command, options, _, _ = parse_args(["file.flo", "--spaghetti-people-mode", "aggregate"], services)
    assert path == "file.flo"
    assert command == "run"
    assert options["spaghetti_people_mode"] == "aggregate"


def test_parse_args_sppm_extended_options(services):
    path, command, options, _, _ = parse_args(_extended_sppm_args(), services)
    assert path == "file.flo"
    assert command == "run"
    _assert_expected_options(
        options,
        {
            "diagram": "sppm",
            "sppm_theme": "print",
            "layout_wrap": "auto",
            "layout_fit": "fit-strict",
            "layout_spacing": "compact",
            "sppm_step_numbering": "node",
            "sppm_label_density": "compact",
            "sppm_wrap_strategy": "balanced",
            "sppm_truncation_policy": "clip",
            "layout_max_width_px": 1200,
            "layout_target_columns": 7,
            "sppm_max_label_step_name": 48,
            "sppm_max_label_workers": 24,
            "sppm_max_label_ctwt": 18,
            "sppm_output_profile": "book",
        },
    )


def _assert_expected_options(options: dict[str, object], expected: dict[str, object]) -> None:
    for key, value in expected.items():
        assert options[key] == value


def _extended_sppm_args() -> list[str]:
    return [
        "file.flo",
        "--diagram",
        "sppm",
        "--sppm-theme",
        "print",
        "--layout-wrap",
        "auto",
        "--layout-fit",
        "fit-strict",
        "--layout-spacing",
        "compact",
        "--sppm-step-numbering",
        "node",
        "--sppm-label-density",
        "compact",
        "--sppm-wrap-strategy",
        "balanced",
        "--sppm-truncation-policy",
        "clip",
        "--layout-max-width-px",
        "1200",
        "--layout-target-columns",
        "7",
        "--sppm-max-label-step-name",
        "48",
        "--sppm-max-label-workers",
        "24",
        "--sppm-max-label-ctwt",
        "18",
        "--sppm-output-profile",
        "book",
    ]


def test_parse_args_rejects_removed_sppm_wrap_rows_alias(services):
    with pytest.raises(SystemExit):
        parse_args(
            ["file.flo", "--diagram", "sppm", "--sppm-wrap-rows", "auto"],
            services,
        )
