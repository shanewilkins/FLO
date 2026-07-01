# FLO Review Gate Findings (2026-07-01)

This note captures the ten prioritized findings from the senior-dev review gate, with concrete actions to move the codebase toward professional, maintainable quality.

## ~~1) Architecture Boundaries Are Not Reliably Enforced~~

~~Issue:~~
~~- Import-linter appears configured and run, but practical enforcement is weak and gives a false sense of architectural governance.~~
~~- A stale policy mapping exists and does not reflect the current package structure.~~

~~Action:~~
~~- Replace import-linter config with validated, active contracts.~~
~~- Add a CI/policy assertion that fails if contract count is zero.~~
~~- Remove or wire the stale layer-rules policy file so architecture policy is single-source and live.~~

## ~~2) Dead-Code Gate Is Soft and Can Hide Real Issues~~

~~Issue:~~
~~- Vulture invocation in hooks is permissive and currently structured to avoid failing quality gates, even when dead code exists.~~

~~Action:~~
~~- Fix vulture command ordering/options and stop swallowing failures.~~
~~- Triage findings into: delete, intentional public API, dynamic-use false positive.~~
~~- Keep whitelist narrow and audited.~~

## 3) Compiler Surface Still Reads as Prototype

Issue:
- Compiler entrypoint language and adapter fallbacks still communicate stub/prototype behavior.
- Permissive fallback parsing reduces trust in DSL correctness.

Action:
- Define and enforce a strict authoritative input model for spec_version/process/steps.
- Remove arbitrary text fallback behavior.
- Update compiler module docs to reflect actual v0.1 contract.

## 4) IR Serialization Contract Is Confusing

Issue:
- User-facing docs and internal IR methods imply different output shapes.
- Internal and schema-shaped representations are not clearly separated by API naming.

Action:
- Make one canonical public export path for schema-shaped output.
- Rename internal helpers to explicitly indicate internal shape.
- Align docs and code so contributors cannot misinterpret contract boundaries.

## 5) CLI/Render Option Plumbing Is Too Wide

Issue:
- Very large function signatures and repeated option threading reduce extensibility and increase regression risk.
- Click and argparse paths both require broad option handling.

Action:
- Introduce a typed command/options object as the single intermediate form.
- Keep parser adapters thin and table-driven.
- Reduce manual parameter plumbing to improve maintainability.

## ~~6) Silent Fail-Open Behavior Reduces Trust~~

~~Issue:~~
~~- Some postprocess steps swallow exceptions and continue with fallback output without explicit user signal.~~

~~Action:~~
~~- Define explicit fail-open policy per step.~~
~~- Emit telemetry and verbose diagnostics when fallback is used.~~
~~- Add tests proving intended degradation behavior.~~

## 7) Renderer Migration Debris Is Accumulating

Issue:
- Deprecated Graphviz compatibility path still contains substantial legacy/no-op shape and dead helper candidates.

Action:
- Split active compatibility behavior from retired migration code.
- Delete no-op hooks unless required by tested public compatibility surface.
- Document migration boundary in one authoritative location.

## 8) User Ergonomics Still Favor Deprecated Default Path

Issue:
- Default CLI path still emphasizes deprecated DOT compatibility output, while preferred modern flows require more flags.

Action:
- Make primary modern workflow shortest and most discoverable.
- If default cannot change yet, provide a concise first-class render command path and stronger guidance in docs/help.

## ~~9) Coverage Signal Is Diluted by Fill Tests~~

~~Issue:~~
~~- Some tests exist primarily to inflate coverage metrics rather than validate behavior.~~

~~Action:~~
~~- Replace fill-style tests with behavioral contract tests.~~
~~- Focus on schema/export validity, CLI error contract, capability matrix, and negative semantic cases.~~

## ~~10) Type Checking Strictness Lags Codebase Size~~

~~Issue:~~
~~- Type-check configuration is conservative for a large and evolving architecture with many Any-heavy seams.~~

~~Action:~~
~~- Increase strictness incrementally by module.~~
~~- Start with compiler IR, schema projection, and option construction paths.~~
~~- Treat typing debt as architecture debt with explicit milestones.~~

## Suggested First Three Work Items

1. Make architecture gates real (import-linter contracts + nonzero contract assertion + stale policy cleanup).
2. Align compiler/IR public contract (schema-shaped canonical export path + naming cleanup + docs alignment).
3. Harden quality signals (vulture fail policy + dead-code triage + replace coverage-fill tests with behavior tests).
