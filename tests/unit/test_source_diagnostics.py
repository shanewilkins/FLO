from flo.source.diagnostics import source_aware_message


def test_validation_message_points_to_node_field():
    content = """steps:
  - id: review
    kind: task
    metadata:
      wait_time: {value: 30, unit: min}
"""

    message = source_aware_message(
        "E1503: task node 'review' has wait_time metadata.",
        content=content,
        source_path="purchase.flo",
    )

    assert message.startswith("purchase.flo:5:7: E1503")
    assert "[steps.review.metadata.wait_time]" in message
    assert "5 |       wait_time:" in message


def test_global_validation_message_remains_unchanged():
    message = "E1003: IR must contain exactly one start node"

    assert (
        source_aware_message(message, content="steps: []\n", source_path="bad.flo")
        == message
    )
