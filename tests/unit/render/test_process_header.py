from flo.compiler.ir.models import IR, Node
from flo.render._process_header import build_process_header_rows, extract_process_header_context


def test_extract_process_header_context_from_dict_process_model():
    process = {
        "process": {
            "id": "wash_n_fold",
            "name": "Wash n' Fold",
            "metadata": {"owner": "Laundry Ops", "revision": "R2"},
        }
    }

    context = extract_process_header_context(process)
    assert context.title == "Wash n' Fold"
    assert context.metadata["process_id"] == "wash_n_fold"
    assert context.metadata["process_name"] == "Wash n' Fold"
    assert context.metadata["owner"] == "Laundry Ops"


def test_extract_process_header_context_from_ir_process_metadata():
    ir = IR(
        name="fallback-id",
        nodes=[Node(id="start", type="start")],
        process_metadata={"process_id": "wash_n_fold", "process_name": "Wash n' Fold", "revision": "R2"},
    )

    context = extract_process_header_context(ir)
    assert context.title == "Wash n' Fold"
    assert context.metadata["process_id"] == "wash_n_fold"


def test_build_process_header_rows_merges_default_fields_and_extra_rows():
    process = {
        "process": {
            "id": "wash_n_fold",
            "name": "Wash n' Fold",
            "metadata": {"owner": "Laundry Ops", "revision": "R2"},
        }
    }

    context = extract_process_header_context(process)
    rows = build_process_header_rows(context=context, extra_rows=[("Profile", "print"), ("Nodes", "12")])
    assert ("Process", "wash_n_fold") in rows
    assert ("Owner", "Laundry Ops") in rows
    assert ("Revision", "R2") in rows
    assert ("Profile", "print") in rows
    assert ("Nodes", "12") in rows