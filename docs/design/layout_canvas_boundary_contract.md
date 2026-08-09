# Layout To Canvas Boundary Contract (ELK/SVG)

Status: accepted

## Purpose

Define the stable handoff from layout output to SVG rendering so route and
shape policy has one owner.

## Ownership

- ELK plus direct SVG backend owns edge route shape policy for SPPM rework
  branch and return variants.
- Deprecated backend postprocessing must not be restored or allowed to own or
  duplicate rework route policy.
- Canvas consumers render what layout provides and may apply deterministic
  presentation transforms only when they do not redefine route policy.

## Required Handoff Fields

- Node geometry: id, x, y, width, height
- Edge endpoints: source id, target id
- Edge path points: ordered polyline points in canvas coordinates
- Edge semantic flags: is_rework and rework_variant when applicable

## Optional Handoff Fields

- Edge annotation content: label, callout_lines, callout_near_source
- Continuation metadata: outgoing_token, incoming_token
- Port hints and anchor ids for compatibility paths

## No-Leak Rules

- Layout layer does not encode renderer-specific SVG element concerns.
- Renderer layer does not rerun layout or introduce alternative route policy.
- Canvas presentation passes may normalize padding and background, but must not
  mutate ELK-owned rework path shapes.

## Validation Expectations

- Direct SVG backend tests assert orthogonal and deterministic rework branch
  and return polyline normalization.
- SVG presentation tests focus on deterministic transforms, not competing
  route-shape ownership logic.

## Migration Implication

This contract freezes Item 2 boundary expectations: route-shape semantics are
owned once in ELK/SVG and consumed downstream without policy duplication.
