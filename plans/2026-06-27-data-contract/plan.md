# Data Contract And Dataset Notice Plan

## Problem Summary

The root README presented the entire repository as a fully AI-generated dummy
example, but only the bundled `data/` tree is dummy data. The repository itself is
intended as reusable ALM ontology infrastructure. There was also no explicit contract
for replacing the bundled example with another dataset.

## Resolution Summary

Keep the strong dummy-data notice in `data/`, remove repo-wide dummy wording from the
root README and model description, and add a durable data-contract document that
defines the normalized dataset shape adapters must emit.

## Goal And Objectives

- Scope the dummy-data warning to the bundled dataset.
- Document the production replacement contract for ALM data.
- Keep the LinkML model positioned as the reusable schema source of truth.

## Design Approach

The data contract is the normalized LinkML `Dataset` boundary, not a raw export
format. Upstream systems should be handled by adapters that emit the normalized YAML
collections before validation and warehouse loading.

## Scope And Non-Goals

In scope:

- Root README wording.
- Architecture/docs index links.
- New data-contract page.
- LinkML model description and regenerated model artifacts.

Out of scope:

- Making `data/` selectable by CLI option.
- Adding dataset metadata to reports.
- Writing source-system adapters.

## Open Points

| ID | Point | Status | Resolution |
|---|---|---|---|
| OP-001 | Should reports read dataset metadata instead of hardcoding VM-E1? | Open | Pending a later implementation packet. |
| OP-002 | Should the CLI accept `--data-dir` for alternate datasets? | Open | Pending a later implementation packet. |

## Implementation Phases

1. Update user-facing repository docs.
2. Add the data-contract page.
3. Update the LinkML model description and regenerate generated artifacts.
4. Run focused validation/proof.

## Dependencies And Risks

- Generated model artifacts must only change through `almon model gen`.
- Existing working-tree changes are present; edits must stay scoped.

## Exit Criteria

- Root README no longer describes the full repository as dummy data.
- `data/README.md` remains the authoritative dummy-data warning.
- Data replacement requirements are documented.
- Generated model docs/types no longer label the model itself as dummy data.
