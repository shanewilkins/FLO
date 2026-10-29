from flo.process.schema.render_metadata import (
    CONTINUATION_EXTENSION_KEY,
    PROCESS_HEADER_METADATA_FIELDS,
    PROCESS_METADATA_PROCESS_ID_KEY,
    PROCESS_METADATA_PROCESS_NAME_KEY,
    PUBLICATION_EXTENSION_KEY,
)
from flo.process.schema.subprocess_refs import SUBPROCESS_DETAIL_MAP_REFERENCE_KEYS
from flo.render._process_header import extract_process_header_context
from flo.render.sppm.continuation_tokens import (
    resolve_explicit_sppm_continuation_tokens,
)


def test_process_header_contract_includes_expected_default_fields():
    assert PROCESS_HEADER_METADATA_FIELDS == (
        ("process_id", "Process"),
        ("owner", "Owner"),
        ("revision", "Revision"),
        ("publication_date", "Date"),
    )


def test_process_identity_keys_are_stable():
    assert PROCESS_METADATA_PROCESS_ID_KEY == "process_id"
    assert PROCESS_METADATA_PROCESS_NAME_KEY == "process_name"


def test_publication_annotations_have_one_extension_namespace():
    assert PUBLICATION_EXTENSION_KEY == "flo:publication"


def test_continuations_have_one_extension_namespace():
    assert CONTINUATION_EXTENSION_KEY == "flo:continuation"


def test_continuation_tokens_preserve_both_directions():
    assert resolve_explicit_sppm_continuation_tokens(
        {"extensions": {"flo:continuation": {"outgoing": "A", "incoming": "B"}}}
    ) == ("A", "B")


def test_subprocess_reference_has_one_spelling():
    assert SUBPROCESS_DETAIL_MAP_REFERENCE_KEYS == ("detail_map_ref",)


def test_headers_ignore_retired_process_metadata():
    context = extract_process_header_context(
        {
            "process": {
                "id": "p",
                "name": "Process",
                "metadata": {"footer_metrics": {"Lead Time": "24 min"}},
            }
        }
    )
    assert "footer_metrics" not in context.metadata


def test_continuations_ignore_retired_edge_metadata():
    assert resolve_explicit_sppm_continuation_tokens(
        {"metadata": {"continuation_to": "A"}}
    ) == (None, None)
