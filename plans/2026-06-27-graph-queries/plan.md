# Plan - Graph Query Files

## Problem Summary

The project now has GQC capability files under `projects/vm-e1-sparrow/gqc/`, but the lower-layer
queries are still embedded in Python renderers. That makes the supported questions visible as
contracts, while the actual AGE/openCypher and SQL forms are harder to inspect directly.

## Resolution Summary

Expose the current lower-layer query forms as project-authored reference files under
`projects/vm-e1-sparrow/graph-queries/`. These files document what exists today: Apache AGE
openCypher for the AGE-backed `impact` renderer, and Postgres SQL for the recursive/relational
renderers. They are mirrors/reference evidence, not a new query compiler or replacement runtime.

## Goal and Objectives

- **G.** Make the current graph-query layer inspectable without pretending it is ISO GQL or another
  standard layer.
- **O1.** Add a clear folder name that separates lower-layer query evidence from GQC contracts.
- **O2.** Mirror each current GQC-backed lower-layer query with explicit engine/language comments.
- **O3.** Call out runtime facts such as AGE's `cypher()` wrapper, Python-inlined parameters, and
  Python post-processing where present.

## Design Approach

- `gqc/` remains the supported capability contract.
- `graph-queries/` becomes the human-readable lower-layer query evidence.
- Query files are grouped by actual runtime/language:
  - `apache-age-open-cypher/` for AGE/openCypher query bodies.
  - `postgres-sql/` for recursive and relational Postgres SQL renderers.
- Files use comments for capability, engine, language, renderer, parameter binding, and limitations.

## Scope and Non-Goals

**In scope:** documentation/reference files for the existing `impact`, `refines_closure`,
`propagate_dal`, `coverage_gaps`, and `defects_per_element` lower-layer queries; project README and
manifest updates.

**Non-goals:** changing runtime dispatch, compiling GQC to SQL/Cypher, claiming ISO GQL support,
adding a new graph engine, or moving renderer strings out of Python in this packet.

## Open Points

| ID | Topic | Status | Resolution / recommendation |
|---|---|---|---|
| **OP-001** | Folder name | **Resolved** | Use `graph-queries/`; it is descriptive and avoids implying a standard. |
| **OP-002** | AGE subfolder name | **Resolved** | Use `apache-age-open-cypher/`; it identifies both the runtime and the Cypher-family language. |

## Implementation Phases

1. Add plan packet.
2. Add `graph-queries/` reference files for current lower-layer renderers.
3. Update project-level docs so readers know where the query evidence lives.
4. Validate GQC and run focused tests where feasible.

## Dependencies and Risks

- These files can drift if renderer code changes without updating the reference files.
- Some files are honest templates rather than standalone runnable SQL, because the current renderers
  inline parameters or perform Python post-processing.

## Exit Criteria

- `projects/vm-e1-sparrow/graph-queries/` exists and covers current GQC-backed lower-layer queries.
- Documentation distinguishes GQC contracts from lower-layer query evidence.
- Validation or focused tests confirm the existing GQC registry remains intact.
