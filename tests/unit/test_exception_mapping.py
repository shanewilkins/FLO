from flo.services import errors


def test_map_domain_exception_to_rc():
    exc = errors.ParseError("bad syntax")
    rc, msg, internal, stage = errors.map_exception_to_rc(exc)
    assert rc == errors.EXIT_PARSE_ERROR
    assert "bad syntax" in msg
    assert internal is False
    assert stage == "parse"


def test_map_unexpected_exception_to_internal():
    exc = ValueError("something went wrong")
    rc, msg, internal, stage = errors.map_exception_to_rc(exc)
    assert rc == errors.EXIT_INTERNAL_ERROR
    assert "something went wrong" in msg
    assert internal is True
    assert stage is None
