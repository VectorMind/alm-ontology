# Workflow

This repository is spec-driven. The **LinkML model is the schema of record**, and time-bounded
implementation work is organized as **dated planning packets** under `plans/`.

## Core discipline

*Tables are truth, the graph is a regenerable view, the model is the schema.* Every engine
(rustworkx, recursive SQL, Apache AGE) and every exposure is rebuilt from the tables on each run;
nothing is a store of record except the authored inputs. Hold this line when adding capabilities.

## Schema of record

The durable contract lives in the model, not in prose:

- `src/alm_ontology/model/alm.yaml` — the LinkML spine. Entity types, controlled vocabularies, and
  permitted relationships. Edit here first when the domain changes, then regenerate.
- `src/alm_ontology/generated/` — Pydantic types, SQL DDL, docs **generated** from the model
  (`almon model gen`). Committed for reviewability but regenerable; never hand-edit.
- `plans/concept-handover/` — the original handover, POC proposal, and research reports. Durable
  reference for *why* the architecture is shaped as it is. Read-only history; do not rewrite.

## Regenerable artifacts (do not commit)

The built warehouse (`data/warehouse/`), reports (`.report/`), and caches are regenerable from the
authored `data/` and are gitignored. Do not commit built data; commit the authored inputs and the
code that rebuilds them.

## Plans

Use `plans/` for dated planning packets tied to active work.

```text
plans/YYYY-MM-DD-<slug>/
  survey.md            # only when the maintainer explicitly requests one
  plan.md
  implementation.md    # created only after implementation work has happened
  handoff.md           # uncaptured operational/in-flight detail for the next person/agent
  test.md              # proof of behavior (may be folded into implementation.md for small packets)
```

Use the ISO date of the day the packet **starts**, followed by a short lowercase slug. Create
`survey.md` only on explicit request — fold light discovery notes into `plan.md` otherwise.

Two index files at the top of `plans/` track packet status: `open.md` lists packets with work still
outstanding, `closed.md` lists completed packets with their proof. Update them whenever a packet is
started or finished, so the state of all plans is visible at a glance.

## Plan shape

`plan.md` stays focused on the work package and contains:

- problem summary;
- resolution summary;
- goal and objectives;
- design approach (the durable design — this repo has no `specifications/`, so durable design for a
  packet lives here);
- scope and non-goals;
- open points with resolution status;
- implementation phases;
- dependencies and risks;
- exit criteria.

Track open points with stable IDs (`OP-001`, …), keep the current status visible, and record a
resolution only when the answer is accepted. `plan.md` does not need a rewrite for every
implementation deviation — once implementation starts, facts about what actually landed belong in
`implementation.md`.

## Implementation log

Create `implementation.md` only once implementation work has actually happened; it logs facts really
implemented, never planned intent. A packet still in planning has no `implementation.md`.

It opens with a **Progress** section — the first section after the title, kept to two lines at most:

- one line with a bar of filled/empty blocks plus the current phase, e.g. `` `▰▰▰▱▱▱ Phase 3/6` ``,
  using the plan's own phase names; when fully done and proven, `` `▰▰▰▰▰▰ Done` ``;
- one short clause naming the phase in progress and what comes next.

Keep the bar current on every change. The rest of the file is the running trace: files changed,
implementation facts, decisions made during development, deviations from the plan, follow-up risks,
and important commands/migrations. Describe what happened; do not restate the whole plan.

## Handoff

`handoff.md` captures the operational and in-flight detail that `plan.md` glosses and that the next
person/agent would otherwise rediscover: working state (branch, running containers), how to run it
locally (env vars, commands), gotchas already hit, nuances the plan leaves implicit, and the concrete
next action. Create it when a packet is handed over or paused mid-flight.

## Test proof

`test.md` is proof of behavior: commands run, fixtures used, expected vs actual results, known gaps,
and environment/dependency notes affecting reproducibility. For small packets the proof may live in
`implementation.md` instead; for planning-only changes it may record document review and consistency
checks rather than runtime proof.

## Git ownership

The maintainer owns commits. Assistants may create a feature branch for isolation but must not
`git commit`, `git push`, or merge without an explicit request, and must never skip hooks or bypass
signing. Leave finished work in the working tree for the maintainer to review, stage, and commit.
