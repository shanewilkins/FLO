from flo.schema.render_metadata import (
    PROCESS_HEADER_METADATA_FIELDS,
    PROCESS_METADATA_PROCESS_ID_KEY,
    PROCESS_METADATA_PROCESS_NAME_KEY,
    SPPM_CONTINUATION_INCOMING_METADATA_KEYS,
    SPPM_CONTINUATION_OUTGOING_METADATA_KEYS,
    SPPM_FOOTER_METRIC_METADATA_KEYS,
    SPPM_FOOTER_NOTES_METADATA_KEYS,
    SUBPROCESS_DETAIL_MAP_REFERENCE_KEYS,
    first_present_metadata_value,
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


def test_sppm_footer_metric_alias_contract_is_stable():
    assert SPPM_FOOTER_METRIC_METADATA_KEYS == (
        "publication_legend_items",
        "legend_items",
        "legend",
        "publication_footer_metrics",
        "footer_metrics",
        "analytics_footer_metrics",
        "analytics_metrics",
    )


def test_sppm_footer_note_alias_contract_is_stable():
    assert SPPM_FOOTER_NOTES_METADATA_KEYS == (
        "publication_caption",
        "caption",
        "publication_footer_notes",
        "footer_notes",
        "publication_footer",
        "footer_note",
    )


def test_sppm_continuation_token_alias_contracts_are_stable():
    assert SPPM_CONTINUATION_OUTGOING_METADATA_KEYS == (
        "continuation_to",
        "continuation_out",
        "continuation_token_out",
    )
    assert SPPM_CONTINUATION_INCOMING_METADATA_KEYS == (
        "continuation_from",
        "continuation_in",
        "continuation_token_in",
    )


def test_subprocess_reference_alias_contract_is_exposed_from_shared_metadata_module():
    assert SUBPROCESS_DETAIL_MAP_REFERENCE_KEYS == (
        "detail_map_ref",
        "detail_map_id",
        "detail_map",
        "detail_map_label",
    )


def test_first_present_metadata_value_uses_alias_order():
    metadata = {
        "footer_metrics": {"Lead Time": "24 min"},
        "legend_items": {"Queue": "7 min"},
    }
    value = first_present_metadata_value(metadata, SPPM_FOOTER_METRIC_METADATA_KEYS)
    assert value == {"Queue": "7 min"}


def test_first_present_metadata_value_returns_none_when_no_alias_value_present():
    metadata = {"footer_metrics": {}, "legend_items": []}
    value = first_present_metadata_value(metadata, SPPM_FOOTER_METRIC_METADATA_KEYS)
    assert value is None
