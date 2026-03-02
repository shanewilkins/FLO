import json

from flo.compiler.ir.models import IR, Node
from flo.export import export_ir


def test_export_ir_defaults_to_json_projection():
    ir = IR(name="p", nodes=[Node(id="start", type="start", attrs={})], edges=[])
    out = export_ir(ir)
    payload = json.loads(out)
    assert payload["process"]["id"] == "p"
    assert payload["nodes"][0]["id"] == "start"


def test_export_ir_honors_json_indent_option():
    ir = IR(name="p", nodes=[Node(id="start", type="start", attrs={})], edges=[])
    out = export_ir(ir, options={"export": "json", "json_indent": 0})
    assert "\n" not in out
