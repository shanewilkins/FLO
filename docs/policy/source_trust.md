# FLO Source Trust and Resource Policy

Status: current

FLO `0.2.x` processes local source files. The supported boundary is a trusted local entry file plus included files contained beneath the entry file's parent directory. This is not an authorization boundary for a hosted upload service.

## Path boundary

- The entry file's parent directory is the source trust root.
- Relative and absolute include paths are accepted only when their resolved target remains inside that root.
- Resolution occurs before containment checking, so `..` traversal and symlink traversal cannot escape the root.
- When parsing content without a source path, the resolved current working directory is the trust root.

## Deterministic resource limits

- one entry or include file: at most 1,000,000 UTF-8 bytes;
- included files per composition: at most 256;
- include nesting beneath the entry file: at most 32 levels;
- entry plus loaded include bytes: at most 8,000,000 bytes.

Crossing a boundary fails parsing with a deterministic diagnostic. FLO does not fetch include files over a network. Hosted or untrusted-source processing requires a separately reviewed sandbox, tighter operational budgets, and adversarial parser testing; it is not a current release claim.
