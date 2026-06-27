# Project Readme

## Problem Summary

The active VM-E1 Sparrow project does not have a top-level README. Its only local overview is inside
`data/README.md`, where the dummy-data warning is repeated at the data-folder level. The project
needs a friendly overview that explains how the fictional aircraft example and the ALM ontology fit
together.

## Resolution Summary

Add `projects/vm-e1-sparrow/README.md` as the single project entrypoint and move the dummy-data
warning there. Keep `data/README.md` focused on the authored dataset layout.

## Goal And Objectives

- Make the warning visible once at the project top level.
- Explain the link between project content and ontology mechanics.
- Include a few useful diagrams that show the interaction between domain facts, the model, generated
  validation, warehouse tables, graph views, and answers.
- Avoid changing authored data or runtime behavior.

## Scope And Non-Goals

In scope: project README, data README cleanup, plan indices, and proof.

Out of scope: model changes, generated artifacts, CLI changes, and root documentation restructuring.

## Open Points

- OP-001: Should the warning remain in `data/README.md`?
  - Resolution: No. The warning moves to `projects/vm-e1-sparrow/README.md`; one mention is enough.

## Implementation Phases

1. Add the project README.
2. Remove the duplicate warning from the data README.
3. Run documentation consistency checks.

## Dependencies And Risks

The new README uses Mermaid diagrams, consistent with existing repository docs. Rendering depends on
the Markdown viewer, but the text remains useful without rendered diagrams.

## Exit Criteria

- `projects/vm-e1-sparrow/README.md` exists and contains the warning.
- `projects/vm-e1-sparrow/data/README.md` no longer contains the warning.
- A text scan confirms the warning phrase appears only once in the project docs.
