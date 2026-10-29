"""The required Pydantic runtime validates the compatibility input envelope."""

import pytest
from pydantic import ValidationError

from flo.source.models import SourceDocument


def test_adapter_envelope_rejects_invalid_text_with_a_field_path():
    with pytest.raises(ValidationError) as exc:
        SourceDocument.model_validate(
            {
                "spec_version": "0.1",
                "process": {"id": "p", "name": {"invalid": "name"}},
                "steps": [{"id": "start", "kind": "start"}],
            }
        )
    assert exc.value.errors()[0]["loc"] == ("process", "name")
