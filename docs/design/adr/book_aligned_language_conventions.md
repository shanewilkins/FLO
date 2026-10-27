# ADR: Book-Aligned Language Conventions

Status: accepted

## Context

The modern process-improvement book is an immediate user of the FLO language,
analysis, and rendering system. Its readers should be able to move from the
book's concepts and worksheets into FLO without first learning
implementation-specific synonyms, compatibility aliases, or metadata
placement rules.

FLO has accumulated terminology and field shapes that do not always match the
book. Examples include multiple names for setup or changeover time, a separate
canonical name for task-level waiting evidence, and accepted fields whose
process-improvement meaning is incomplete or unused. Those differences make
the language harder to teach and allow structurally valid documents to imply
semantics that FLO cannot interpret consistently.

FLO is still pre-1.0 and currently has one direct user. Preserving accidental
language history is less valuable than establishing a small, coherent domain
language before external compatibility commitments exist.

## Decision

FLO language design follows the domain concepts and practitioner terminology
established in the modern process-improvement book.

This decision applies to:

- authored field names and nesting;
- process, step, relation, and measurement concepts;
- definitions shown in user documentation and diagnostics;
- analysis and renderer labels;
- maintained examples and conformance fixtures; and
- the order in which belt-specific language capabilities are introduced.

The book is the domain-convention authority, while FLO specifications remain
the normative machine contract. Book terminology must be translated into an
explicit FLO specification, schema, validation rule, and acceptance example
before it becomes implemented language behavior. A book revision does not
silently mutate a released FLO contract.

When an existing FLO term differs from the book:

1. use the book term unless a documented semantic distinction requires a
   separate FLO concept;
2. record that distinction in a normative specification;
3. avoid compatibility aliases whose only purpose is to preserve pre-1.0 FLO
   terminology; and
4. update source, canonical exchange, analysis, rendering, examples, and
   documentation as one coordinated semantic change.

Core book concepts that participate in validation, analysis, rendering, or
public exchange are first-class typed language fields rather than unstructured
metadata. FLO may retain an explicit extension boundary for non-language data,
but extension fields do not acquire process meaning implicitly.

The maintained repository extraction in `notes/notes-from-book.md` and the
book reference process in `examples/reference/book_washnfold.flo` provide the
current implementation evidence for book alignment. Normative definitions
belong in `docs/specs/`, and belt acceptance follows the governance and release
requirements.

## Consequences

Positive consequences:

- book readers encounter familiar language in source files, diagnostics, and
  diagrams;
- teaching material, examples, validation, and analysis share one vocabulary;
- pre-1.0 aliases and unused fields can be removed instead of becoming
  permanent compatibility obligations;
- semantic differences must be deliberate and documented rather than emerging
  from implementation details; and
- belt-specific language work remains tied to accepted instructional needs.

Costs and constraints:

- aligning existing syntax is intentionally breaking;
- repository examples, schemas, tests, renderers, and documentation must move
  together when terminology changes;
- the book extraction must be maintained as the instructional source evolves;
  and
- FLO still needs formal definitions where practitioner terminology alone is
  insufficient for deterministic validation or analysis.

## Rejected Alternatives

### Preserve existing FLO names through compatibility aliases

Rejected because there are no external compatibility commitments that justify
carrying multiple names for one concept. Aliases increase validation,
documentation, and diagnostic complexity and make the preferred language less
obvious.

### Let implementation terminology define the language

Rejected because storage layout, renderer needs, and historical helper names
are not practitioner-facing domain concepts.

### Treat the book as the executable specification

Rejected because instructional prose does not define every machine constraint,
error state, reference rule, or analysis limitation. FLO specifications remain
the normative executable contract and make the book's concepts deterministic.

## Related Decisions

- `measurement_profiles_and_evidence.md`
- `pydantic_source_and_render_inputs.md`
- `canonical_ir_metadata_and_subprocess_hierarchy.md`

