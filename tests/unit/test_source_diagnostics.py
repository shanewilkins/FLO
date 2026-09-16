from flo.source.diagnostics import source_aware_message, source_diagnostic


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

    diagnostic = source_diagnostic(
        "E1503: task node 'review' has wait_time metadata.",
        content=content,
        source_path="purchase.flo",
    )

    assert diagnostic is not None
    assert diagnostic.code == "E1503"
    assert diagnostic.severity == "error"
    assert diagnostic.field_path == "steps.review.metadata.wait_time"
    assert diagnostic.suggestion == (
        "Use wait_before on work nodes; wait_time is canonical only on queues."
    )
    assert diagnostic.include_chain == ()


def test_global_validation_message_remains_unchanged():
    message = "E1003: IR must contain exactly one start node"

    assert (
        source_aware_message(message, content="steps: []\n", source_path="bad.flo")
        == message
    )


def test_transition_diagnostic_points_to_missing_outcome_and_suggests_fix():
    content = """transitions:
  - source: gate
    target: finish
"""

    diagnostic = source_diagnostic(
        "E1020: decision 'gate' has outgoing edge 'gate' -> 'finish' without an outcome.",
        content=content,
        source_path="review.flo",
    )

    assert diagnostic.code == "E1020"
    assert diagnostic.line == 3
    assert diagnostic.field_path == "transitions.gate->finish.outcome"
    assert diagnostic.suggestion == (
        "Add a unique outcome to every transition leaving the decision."
    )


def test_compile_diagnostic_points_to_transition_field_and_suggests_fix():
    content = """transitions:
  - source: review
    target: fix
    rework: yes
"""

    diagnostic = source_diagnostic(
        "E0209: transitions[0].rework must be true or false when provided",
        content=content,
        source_path="review.flo",
    )

    assert diagnostic.code == "E0209"
    assert diagnostic.line == 4
    assert diagnostic.field_path == "transitions[0].rework"
    assert diagnostic.suggestion == "Use the YAML boolean true or false without quotes."


def test_branch_mode_diagnostic_points_to_authored_mode_and_suggests_fix():
    content = """steps:
  - id: assign
    kind: branch
    branch:
      mode: least_loaded
"""

    diagnostic = source_diagnostic(
        "E0216: steps[0].branch.mode must be one of: dispatch, external, probabilistic, unspecified",
        content=content,
        source_path="leveling.flo",
    )

    assert diagnostic.line == 5
    assert diagnostic.field_path == "steps[0].branch.mode"
    assert diagnostic.suggestion == (
        "Use dispatch, probabilistic, external, or unspecified as the branch mode."
    )


def test_ambiguous_fan_out_diagnostic_identifies_step_and_branch_point_fix():
    content = """steps:
  - id: assign
    kind: task
"""

    diagnostic = source_diagnostic(
        "E1025: node 'assign' has 2 outgoing edges but kind 'task' is not a branch point.",
        content=content,
        source_path="leveling.flo",
    )

    assert diagnostic.line == 3
    assert diagnostic.field_path == "steps.assign.kind"
    assert diagnostic.suggestion == (
        "Use decision, branch, or parallel_split to state how outgoing paths are selected."
    )


def test_invalid_route_diagnostic_points_to_transition_route():
    content = """transitions:
  - source: work
    target: finish
    route: fast
"""

    diagnostic = source_diagnostic(
        "E1027: edge 'work' -> 'finish' declares route 'fast', but source 'work' is not a branch.",
        content=content,
        source_path="routing.flo",
    )

    assert diagnostic.line == 4
    assert diagnostic.field_path == "transitions.work->finish.route"
    assert diagnostic.suggestion == (
        "Remove the route or make the transition source a branch."
    )
