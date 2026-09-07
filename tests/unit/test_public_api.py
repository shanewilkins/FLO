from flo import compile, export, inspect, parse, validate

_VALID_SOURCE = """spec_version: "0.1"

process:
  id: purchase_request
  name: Purchase Request

steps:
  - id: start
    kind: start
  - id: finish
    kind: end

transitions:
  - source: start
    target: finish
"""


def test_public_api_runs_the_supported_source_workflow():
    parsed = parse(_VALID_SOURCE, source_path="purchase-request.flo")
    compiled = compile(_VALID_SOURCE, source_path="purchase-request.flo")
    validated = validate(_VALID_SOURCE, source_path="purchase-request.flo")
    report = inspect(_VALID_SOURCE, source_path="purchase-request.flo")
    exported = export(_VALID_SOURCE, source_path="purchase-request.flo")

    assert parsed.ok
    assert compiled.ok
    assert validated.ok
    assert report.ok
    assert exported.ok
    assert validated.value is not None
    assert validated.value.process_metadata is not None
    assert validated.value.process_metadata["process_id"] == "purchase_request"
    assert report.value is not None
    assert report.value.process_id == "purchase_request"
    assert exported.value is not None
    assert '"id": "purchase_request"' in exported.value


def test_public_api_returns_typed_diagnostics_instead_of_raising():
    result = validate(
        """spec_version: "0.1"

process:
  id: invalid
  name: Invalid

steps:
  - id: start
    kind: start
  - id: review
    kind: task
    metadata:
      wait_time: {value: 30, unit: min}
  - id: finish
    kind: end

transitions:
  - source: start
    target: review
  - source: review
    target: finish
""",
        source_path="invalid.flo",
    )

    assert not result.ok
    assert result.value is None
    assert result.diagnostics[0].code == "E1503"
    assert result.diagnostics[0].source == "invalid.flo"
