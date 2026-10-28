"""Generate authored and canonical JSON Schemas from Pydantic contracts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from flo.process.contracts import CanonicalIRContract
from flo.source.models import SourceDocument

ROOT = Path(__file__).resolve().parents[1]


def generated_schemas() -> dict[Path, str]:
    """Return deterministic source and exchange schemas without touching disk."""
    source_schema = SourceDocument.model_json_schema(
        ref_template="#/$defs/{model}",
        mode="validation",
    )
    canonical_schema = CanonicalIRContract.model_json_schema(
        ref_template="#/$defs/{model}",
        mode="validation",
    )
    return {
        ROOT / path: json.dumps(schema, indent=2) + "\n"
        for path, schema in (
            ("schema/flo_source.json", source_schema),
            ("schema/flo_ir.json", canonical_schema),
            ("src/flo/process/schema/flo_ir.json", canonical_schema),
        )
    }


def main() -> None:
    """Write schemas, or fail read-only when generated artifacts have drifted."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail on schema drift")
    args = parser.parse_args()
    stale = []
    for path, expected in generated_schemas().items():
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != expected:
                stale.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(expected, encoding="utf-8")
    if stale:
        parser.exit(
            1,
            "Schema drift: "
            + ", ".join(stale)
            + "\nRun python scripts/generate_contract_schemas.py\n",
        )


if __name__ == "__main__":
    main()
