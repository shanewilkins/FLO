"""The required Pydantic runtime validates the compatibility input envelope."""

import pytest
from pydantic import ValidationError

from flo.source.models import AdapterModel


def test_adapter_envelope_rejects_invalid_text_with_a_field_path():
    with pytest.raises(ValidationError) as exc:
        AdapterModel.model_validate({"name": {"invalid": "name"}, "content": "text"})
    assert exc.value.errors()[0]["loc"] == ("name",)
