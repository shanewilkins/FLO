from flo.compiler.ir import enums


def test_enums_have_values():
    # exercise enum members to increase coverage
    assert enums.NodeKind.TASK.value == "task"
    assert enums.LaneType.SWIMLANE.value == "swimlane"
    assert enums.ValueClass.STRING.value == "string"
