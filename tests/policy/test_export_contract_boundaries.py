"""Policy assertions for schema export contract boundaries."""

from __future__ import annotations

import flo.compiler.ir as compiler_ir
import flo.export as export_api


def test_compiler_ir_package_does_not_expose_schema_export_projection() -> None:
    assert "ir_to_schema_dict" not in compiler_ir.__all__
    assert "ir_to_internal_dict" not in compiler_ir.__all__
    assert "ir_from_internal_dict" not in compiler_ir.__all__
    assert "ir_to_internal_json" not in compiler_ir.__all__
    assert not hasattr(compiler_ir, "ir_to_internal_dict")
    assert not hasattr(compiler_ir, "ir_from_internal_dict")
    assert not hasattr(compiler_ir, "ir_to_internal_json")


def test_public_export_surface_is_registry_only() -> None:
    assert "export_ir" in export_api.__all__
    assert "ir_to_schema_dict" not in export_api.__all__
    assert "ir_to_schema_json" not in export_api.__all__
    assert "ir_to_internal_dict" not in export_api.__all__
    assert "ir_from_internal_dict" not in export_api.__all__
    assert "ir_to_internal_json" not in export_api.__all__
    assert not hasattr(export_api, "ir_to_internal_dict")
    assert not hasattr(export_api, "ir_from_internal_dict")
    assert not hasattr(export_api, "ir_to_internal_json")
