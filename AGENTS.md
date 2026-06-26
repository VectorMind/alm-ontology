# Agent Guidance

Read [WORKFLOW.md](WORKFLOW.md) before doing planning or implementation work in this repository. It
is the authority on how plans, implementation logs, operational notes, and proofs are organized; this
file is the short version.

## Core discipline

*Tables are truth, the graph is a regenerable view, the model is the schema.* Every engine and
exposure is rebuilt from the tables on each run. Change the domain in the LinkML model
(`src/alm_model/model/alm.yaml`) first, then regenerate (`almon model gen`) — never hand-edit
`src/alm_model/generated/`. Do not commit built artifacts (`data/warehouse/`, `.report/`); they are
regenerable and gitignored.

## Spec and planning workflow

- The **LinkML model is the schema of record**. Durable architectural reference lives in
  `plans/concept-handover/` (read-only history).
- Store time-bounded work under `plans/YYYY-MM-DD-<slug>/`, ISO date of the day the packet starts.
- Each dated packet uses `plan.md`; add `implementation.md` only after real implementation has
  happened (open it with a current **Progress** bar) and keep operational notes/proof there. Add
  `test.md` for proof only when it is large enough to split out. Add `survey.md` only on explicit
  request. Do not create or maintain `handoff.md`.
- Keep `plans/open.md` and `plans/closed.md` current as packets start and finish.
- Track open points with stable IDs (`OP-001`, …); record a resolution only when accepted.
- Keep `plan.md` focused on approved scope; once implementation starts, what actually landed goes in
  `implementation.md`, not back into `plan.md`.

## Git

The maintainer owns commits. You may branch for isolation, but do not commit, push, or merge without
an explicit request. Leave finished work in the working tree for review.
