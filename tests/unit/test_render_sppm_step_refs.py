from flo.render import render_dot


def test_sppm_nodes_show_stable_visible_reference_tokens():
    ir_like = {
        "nodes": [
            {
                "id": "review_request",
                "kind": "task",
                "name": "Review Request",
                "metadata": {},
            },
            {"id": "approve_request", "kind": "decision", "name": "Approved?"},
            {
                "id": "dispatch_queue",
                "kind": "queue",
                "name": "Dispatch Queue",
                "metadata": {"wait_time": {"value": 5, "unit": "min"}},
            },
        ],
        "edges": [
            {"source": "review_request", "target": "approve_request"},
            {"source": "approve_request", "target": "dispatch_queue"},
        ],
    }
    out = render_dot(ir_like, options={"diagram": "sppm"})
    assert "Review Request" in out
    assert "Approved?" in out
    assert "Dispatch Queue" in out
    assert "[review_request]" not in out
    assert '"approve_request" [label="Approved?", shape=diamond' in out
    assert '"dispatch_queue" [label=<<TABLE' in out
    assert "shape=triangle" in out
    assert "[approve_request]" not in out
    assert "[dispatch_queue]" not in out
