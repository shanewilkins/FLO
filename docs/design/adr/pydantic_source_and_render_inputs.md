# ADR: Pydantic Source And Render Inputs

Status: accepted

## Context

The [quantity validation and units decision](quantity_validation_and_units.md)
completed configuration consolidation and left broader source models as a
follow-up. Source normalization still mixed handwritten shape checks, source
relationships, and conversion. Render mappings retained a large family of
per-option parsers separate from the application input model.

## Decision

Pydantic models in `flo.source.models` own strict authored shapes for process
identity/context, recursive steps and attrs, explicit transitions, named target
shorthand, and effective branch configuration. The compiler validates these
shapes before normalization. Normalization and IR assembly trust that boundary;
their superseded structural guards are removed.

Include composition uses a partial source model: validate shapes for fields
present in each fragment before merging, without requiring standalone process
identity or a complete flow. The composed document then passes the full source
model and domain validators. Both child spellings require a subprocess owner.
Known collection shapes are checked at all supported placements rather than
silently selecting around malformed legacy input.

Canonical and legacy collections compose additively across supported placements;
duplicate IDs remain errors, not an inheritance/override feature. Explicit
language versions must be supported and agree; fragments may omit them.
Unknown metadata retains its existing overlay behavior. Composition privately
tracks authored container origins so post-merge diagnostics can recover the
original file, indices, excerpts, and include chain without adding provenance
to canonical IR or exchange.

The validated models do not replace the authored mapping passed to assembly.
This preserves omitted keys, integer/string version identity, unknown metadata,
child spelling, boolean outcome names, and existing attrs-overlay precedence.
Effective branch and named-target shapes are validated after that overlay is
selected. Source-specific identity uniqueness and route ownership remain
explicit, as do canonical IR reference, graph, timing, and quantity semantics.

Model errors adapt to compiler-compatible failures carrying a typed location.
Diagnostics traverse YAML nodes to locate nested authored paths and retain
existing error codes and suggestions. Model-library validation dumps are not
exposed as the public error format. Existing enrichment remains available for
non-model producers; this does not implement common diagnostic delivery.

`flo.render.options.RenderInput` is the single model used by application input
validation and `RenderOptions.from_mapping`. It derives fields, types, and
defaults from the immutable dataclass, adds boundary parsers, and applies a
declarative alias table plus existing profile/projection/footer policy. A small
reflection step avoids maintaining a second field/default catalog. The model
stays in the render package so renderer consumers do not depend on application
code. Themes retain their dedicated semantic resolver.

Application validation retains only authored options and normalized positive
integers; model defaults do not become CLI overrides ahead of source render
intent resolution. Render mappings resolve profiles, dimensions, and derived
pixel bounds after the final input selection.

## Authority and compatibility

The core language and CLI specifications remain normative. Source models are
the implementation owner for structural checks; they are not a replacement
public source format or a new canonical schema. Published IR JSON Schemas and
schema projection are unchanged. Existing conformance/schema tests and the
release corpus guard agreement through source-to-IR-to-export/render paths.

Internal IR, geometry, and analysis dataclasses remain appropriate. This change
does not expand Pint beyond the accepted spatial trial, add inferred units,
reinterpret duration aliases, or move graph/domain rules into model callbacks.

## Validation

Regression coverage includes both child spellings, nested attrs locations,
process identity errors, annotation/omission/scalar preservation, effective
branch overlay, names resembling validation internals, and CLI/render alias and
invalid-value parity. Full-suite coverage, architecture/import checks, golden
artifact checks, and distribution import smoke checks remain the applicable
verification surfaces.
