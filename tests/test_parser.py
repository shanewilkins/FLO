from flo import parser


def test_parse_basic():
    src = """
    # sample
    process MyProc
    task A
    task B
    """
    res = parser.parse(src)
    assert res["process"] is not None
    assert res["process"].name == "MyProc"
    assert [t.name for t in res["tasks"]] == ["A", "B"]
