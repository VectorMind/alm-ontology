# Cache Generated Artifacts

## Problem Summary

The project layout was restructured under `projects/<name>/`, but generated artifacts still live
inside the authored project tree. Reports also use a dotted `.report` name inside the project, and
the FastEmbed cache includes an unnecessary `alm-ontology` path segment.

## Resolution Summary

Move regenerable project outputs under `.cache/projects/<project>/` and keep cache child names plain:
`generated/` for LinkML outputs and `report/` for generated reports. Move the shared model cache to
`.cache/models/fastembed/`. Add a durable CLI reference in `docs/`.

## Goal And Objectives

- Document the current CLI surface and Docker requirements.
- Resolve generated model artifacts from `.cache/projects/<project>/generated/`.
- Resolve reports from `.cache/projects/<project>/report/`.
- Resolve FastEmbed models from `.cache/models/fastembed/`.
- Remove the old checked-in `projects/<project>/generated/` output tree.

## Design Approach

Keep authored project inputs in `projects/<project>/`: `model/`, `data/`, `gqc/`, `config/`, and
`project.yaml`. Put all project-scoped generated outputs under `.cache/projects/<project>/` so they
remain clearly regenerable and gitignored. Runtime code should use central path constants rather
than reconstructing cache paths locally.

## Scope And Non-Goals

In scope: path constants, docs, packaging metadata, generated output location, report output
location, and old generated artifact removal.

Out of scope: changing the Postgres warehouse schema, changing CLI command names, adding a project
selection flag, or changing authored domain data.

## Open Points

- OP-001: Should generated LinkML artifacts remain committed?
  - Resolution: No for this increment. They move under `.cache/projects/<project>/generated/`, which
    is gitignored and regenerable.

## Implementation Phases

1. Add CLI reference and planning packet.
2. Update path constants and runtime users.
3. Update docs and packaging metadata.
4. Regenerate artifacts under `.cache`.
5. Remove old generated tree and verify.

## Dependencies And Risks

- Commands that validate, build, query, or report still need a running Postgres/AGE/pgvector
  container.
- A fresh checkout must run `almon model gen` before structural validation can load generated
  Pydantic types.

## Exit Criteria

- `almon model gen` writes to `.cache/projects/<project>/generated/`.
- `projects/<project>/generated/` is absent.
- Docs describe the new generated and report locations.
- Focused validation commands pass or any Docker-dependent gaps are recorded.
