"""Validate and publish the Riverside teaching example using FLO's Python API."""

from __future__ import annotations

import argparse
import base64
import html
import json
from pathlib import Path

import flo
from flo.render import render_artifact

ROOT = Path(__file__).resolve().parent
STATES = ("current", "proposed")
FIELDS = ("cycle_time", "wait_time", "changeover_time")
LIMITATION = (
    "End-to-end time: unavailable. Both checks run in parallel; clarification "
    "can repeat review. Branch frequencies and repeat counts are not supplied. "
    "Activity means cannot be added into an empirical process mean or percentile. "
    "Unknown waiting and setup remain unknown. No savings percentage is claimed."
)


def evidence_rows(payload: dict) -> list[list[str]]:
    """Project all work timing evidence, explicitly preserving missingness and zero."""
    rows = []
    for node in payload["nodes"]:
        if node["kind"] != "task":
            continue
        for field in FIELDS:
            profile = node.get(field)
            if profile is None:
                rows.append([node["id"], field, "Unknown", "—", "Unknown", "—"])
                continue
            result = profile["results"][profile["primary"]]
            count = profile.get("observation_count")
            sample = (
                f"{count} {profile['observation_unit']}"
                if count is not None
                else "Unknown (estimate)"
            )
            rows.append(
                [
                    node["id"],
                    field,
                    f"{result['method']}: {result['value']} {result['unit']}",
                    profile["basis"],
                    sample,
                    profile["evidence_ref"],
                ]
            )
    return rows


def table(rows: list[list[str]]) -> str:
    """Create an escaped, accessible evidence table shared by notebook and print."""
    headings = ("Step", "Measurement", "Result", "Basis", "Observations", "Source")
    return (
        "<table><thead><tr>"
        + "".join(f'<th scope="col">{html.escape(h)}</th>' for h in headings)
        + "</tr></thead><tbody>"
        + "".join(
            "<tr>" + "".join(f"<td>{html.escape(v)}</td>" for v in row) + "</tr>"
            for row in rows
        )
        + "</tbody></table>"
    )


def build(output: Path) -> Path:
    """Write self-contained HTML, SVG, canonical JSON and inspection evidence."""
    prepared = []
    for state in STATES:
        path = ROOT / f"{state}.flo"
        source = path.read_text(encoding="utf-8")
        validated = flo.validate(source, source_path=str(path))
        if not validated.ok:
            raise ValueError(json.dumps(validated.report.as_dict(), indent=2))
        exported = flo.export(source, source_path=str(path))
        inspected = flo.inspect(source, source_path=str(path))
        if not exported.ok or not inspected.ok:
            raise ValueError("Export or inspection failed; see FLO diagnostics.")
        artifact = render_artifact(
            validated.value,
            {
                "diagram": "swimlane",
                "orientation": "tb",
                "theme": "print",
                "no_footer": True,
            },
        )
        if artifact.diagnostic_report.error_count:
            raise ValueError(json.dumps(artifact.diagnostic_report.as_dict()))
        prepared.append((state, exported, inspected, artifact))

    output.mkdir(parents=True, exist_ok=True)
    sections = []
    for state, exported, inspected, artifact in prepared:
        (output / f"{state}.svg").write_text(artifact.content, encoding="utf-8")
        (output / f"{state}.json").write_text(exported.value, encoding="utf-8")
        (output / f"{state}-inspection.json").write_text(
            json.dumps(inspected.value.as_dict(), indent=2) + "\n", encoding="utf-8"
        )
        (output / f"{state}-diagnostics.json").write_text(
            json.dumps(inspected.report.as_dict(), indent=2) + "\n", encoding="utf-8"
        )
        encoded = base64.b64encode(artifact.content.encode()).decode("ascii")
        diagnostics = "".join(
            f"<li>{html.escape(d.code or 'diagnostic')}: {html.escape(d.message)}</li>"
            for d in inspected.diagnostics
        )
        sections.append(
            f"<section><h2>{state.title()} state</h2>"
            f"<p>{html.escape(LIMITATION)}</p>"
            f'<img alt="Riverside {state} process map" src="data:image/svg+xml;base64,{encoded}">'
            "<p>P/T = processing; W/T = waiting; S/T = setup. Tables show mean minutes. "
            "Explicit handoff transfers responsibility. Rework returns to review; "
            "split/join requires both checks.</p></section>"
            f"<section><h2>{state.title()} evidence</h2>"
            + table(evidence_rows(json.loads(exported.value)))
            + f"<h3>Validation and analysis findings</h3><ul>{diagnostics}</ul></section>"
        )
    document = """<!doctype html><html lang="en"><meta charset="utf-8">
<title>Riverside current and proposed states</title>
<style>
body {font: 16px/1.45 system-ui, sans-serif; color: #111; margin: 2rem auto; max-width: 1100px; padding: 0 1rem}
img {display: block; margin: auto; width: auto; max-width: 100%; height: auto; max-height: 950px; object-fit: contain} table {border-collapse: collapse; width: 100%; font-size: 12px}
th,td {border: 1px solid #777; padding: 6px; text-align: left; overflow-wrap: anywhere}
thead {display: table-header-group} tr {break-inside: avoid} h2,h3 {break-after: avoid}
@page {size: A3 portrait; margin: 12mm}
@media print {body {margin: 0; padding: 0; max-width: none} section {break-before: page} img {max-height: 245mm} a {color: inherit}}
</style><h1>Riverside request review</h1>
<p>Fictional teaching case. Current = synthetic summaries (FLO basis: simulated).
Proposed = estimates: halve known waits using a shared intake checklist and review alerts.
Processing assumptions and flow stay the same. Estimates are hypotheses, not measured improvements.</p>
<p>Compare the same step IDs, mean statistic and minute units. Zero means an explicitly
supplied zero; Unknown means no measurement. Counts refer to activity executions,
not unique requests. The clarification cohort differs from the mainline cohort.</p>
"""
    report = output / "comparison.html"
    report.write_text(document + "".join(sections) + "</html>\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("renders/riverside"))
    print(build(parser.parse_args().output).resolve())
