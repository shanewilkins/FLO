from flo.compiler.ir import enums


def test_enums_have_values():
    # exercise enum members to increase coverage
    assert enums.NodeKind.TASK.value == "task"
    assert enums.NodeKind.WAIT.value == "wait"
    assert enums.NodeKind.PROCESS.value == "process"
    assert enums.NodeKind.DECISION.value == "decision"
    assert enums.LaneType.SWIMLANE.value == "swimlane"
    assert enums.LaneType.GROUP.value == "group"
    assert enums.ValueClass.STRING.value == "string"
    assert enums.ValueClass.NUMBER.value == "number"
    assert enums.ProcessValueClass.VA.value == "VA"
    assert enums.ProcessValueClass.RNVA.value == "RNVA"
    assert enums.ProcessValueClass.NVA.value == "NVA"
    assert enums.ProcessValueClass.UNKNOWN.value == "unknown"
