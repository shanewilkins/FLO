"""Structural baseline reporting remains useful without historical Radon scores."""

from dataclasses import asdict

from flo.app._sppm_refactor_baseline import (
    collect_sppm_refactor_baseline,
    format_sppm_refactor_baseline_report,
    main,
)


def test_structural_baseline_explicitly_retires_radon_scores(tmp_path):
    source = tmp_path / "sample.py"
    source.write_text("def first():\n    return 1\n\ndef second():\n    return 2\n")
    report = collect_sppm_refactor_baseline([source])
    stats = report.files[0]
    assert stats.line_count == 5
    assert stats.function_count == 2
    assert stats.longest_function.name == "first"
    assert stats.longest_function.span_lines == 2
    assert "complexity_findings" not in asdict(stats)
    assert "complexity" not in asdict(stats.longest_function)
    rendered = format_sppm_refactor_baseline_report(report)
    assert "first:2" in rendered
    assert "| Complexity |" not in rendered
    assert "Historical Radon complexity scores are retired." in rendered
    assert "Ruff C901" in rendered
    assert "## Layer Violations" in rendered
    assert "## DRY Violations" in rendered


def test_baseline_entrypoint_preserves_structural_and_clone_findings(tmp_path, capsys):
    source = tmp_path / "sample.py"
    source.write_text("def work():\n    return 1\n")
    assert main([str(source)]) == 0
    rendered = capsys.readouterr().out
    assert "work:2" in rendered
    assert "Ruff C901" in rendered
    assert "No normalized cross-file clone groups detected" in rendered
