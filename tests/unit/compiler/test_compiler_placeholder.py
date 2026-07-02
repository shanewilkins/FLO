import pytest

from flo.compiler import compile_adapter


def test_compile_adapter_rejects_missing_steps() -> None:
    with pytest.raises(ValueError, match="steps"):
        compile_adapter(
            {
                "spec_version": "0.1",
                "process": {"id": "p", "name": "Process"},
            }
        )
