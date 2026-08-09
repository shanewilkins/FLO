import importlib.util
from pathlib import Path


_SCRIPT_PATH = Path("scripts/check_docs_governance.py")
_SPEC = importlib.util.spec_from_file_location("check_docs_governance", _SCRIPT_PATH)
assert _SPEC is not None
assert _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)


def test_roadmap_release_claims_accept_matching_requirement_row():
    warnings: list[str] = []

    _MODULE._warn_roadmap_release_claims(
        roadmap="- `UR-035` [0.2; Implemented]: Standalone publication is complete.\n",
        requirements={"UR-035": {"Target_Release": "0.2", "State": "Implemented"}},
        warnings=warnings,
    )

    assert warnings == []


def test_roadmap_release_claims_report_target_and_state_mismatches():
    warnings: list[str] = []

    _MODULE._warn_roadmap_release_claims(
        roadmap="- `UR-035` [0.6; Committed]: Standalone publication is complete.\n",
        requirements={"UR-035": {"Target_Release": "0.2", "State": "Implemented"}},
        warnings=warnings,
    )

    assert warnings == [
        "docs/ROADMAP.md: UR-035 claims 0.6, but register targets 0.2",
        "docs/ROADMAP.md: UR-035 claims Committed, but register state is Implemented",
    ]


def test_roadmap_release_claims_report_unknown_requirement():
    warnings: list[str] = []

    _MODULE._warn_roadmap_release_claims(
        roadmap="- `UR-999` [0.2; Implemented]: Unknown claim.\n",
        requirements={},
        warnings=warnings,
    )

    assert warnings == ["docs/ROADMAP.md: release claim references unknown UR-999"]
