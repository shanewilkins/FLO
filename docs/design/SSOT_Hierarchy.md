# FLO Source of Truth Hierarchy (v0.1)

Purpose: define where truth lives for FLO structure, semantics, and user-facing behavior.

## Hierarchy

1. Schema contract (structural SSOT)
   - File: `schema/flo_ir.json`
   - Defines machine-readable structural contract for exported IR.
   - Any structural breaking change must update this schema first.

2. Language semantics (semantic SSOT)
   - File: `docs/design/IR.md`
   - Defines graph rules, node/edge expectations, and validation semantics.
   - Validator behavior in code must match this document.

3. Implementation behavior (executable SSOT)
   - Files:
     - `src/flo/compiler/ir/validate.py`
     - `src/flo/compiler/compile.py`
   - Implements current semantics and compilation assumptions.
   - Test suite enforces conformance for this behavior.

4. User-facing summary
   - File: `README.md`
   - Concise, practical summary of the current language and CLI behavior.
   - Must not conflict with semantic SSOT; if in conflict, `docs/design/IR.md` wins.

## Rule for changes

For any behavior change:

1. Update semantic SSOT (`docs/design/IR.md`) and schema (if structural).
2. Update implementation.
3. Update tests (unit + conformance/integration as applicable).
4. Update user-facing docs (`README.md`) if user-visible behavior changed.

## Current semantic baseline (v0.1)

- Exactly one `start` node.
- At least one `end` node.
- All edge endpoints must resolve.
- `decision` nodes require at least two outgoing edges.
- Every node except `start` must have at least one predecessor.
- Every node except `end` must have at least one successor.
- Every node must be reachable from `start`.
- Every node must be able to reach at least one `end` node.
