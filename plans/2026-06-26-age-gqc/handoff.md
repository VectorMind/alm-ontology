# Handoff — Apache AGE substrate + GQC

Operational and in-flight details not captured in `plan.md`. Read this before continuing the work.

## Working state

- **Branch:** `feat/age-substrate` (off `main`). Phases 1–2 landed in the working tree,
  **not committed** (maintainer owns git per the workflow). New/modified areas include AGE graph
  backend, graph CLI lifecycle, formal GQC files, LinkML inverse relation + generated artifacts,
  custom Docker image, and FastEmbed profile config.
- **Container:** `alm-age` (from `docker-compose.yml`) is up and healthy on `localhost:5432`. Tear
  down with `docker compose down` (add `-v` to drop the data volume). It was recreated with
  `alm-ontology-age:pg18-age-pgvector`; `CREATE EXTENSION vector` works and reports pgvector `0.8.3`.

## Running it locally

```
docker compose up -d --build          # start custom Postgres+AGE+pgvector; wait for healthy
uv run almon build                    # (re)build the Parquet warehouse = truth
uv run almon graph rebuild            # persist the AGE graph explicitly
uv run almon graph run impact --req REQ-0110 --no-rebuild
uv run almon impact --req REQ-0110 --engine all
uv run almon graph validate-gqc
uv run pytest -q                      # AGE tests skip automatically if the container is down
```

- **Connection defaults** (env-overridable, see `graph_age._conn_params()`):
  `ALM_PG_HOST=localhost`, `ALM_PG_PORT=5432`, `ALM_PG_USER=postgres`, `ALM_PG_PASSWORD=postgres`,
  `ALM_PG_DB=alm`. These match the compose file.
- Every session must `CREATE EXTENSION IF NOT EXISTS age; LOAD 'age'; SET search_path = ag_catalog,
  "$user", public;` — `graph_age.connect()` does this for you.

## Gotchas already hit (don't re-discover these)

- **PG18 mount convention.** `apache/age:latest` is PG18; it refuses to start if the volume is mounted
  at `/var/lib/postgresql/data`. Mount at `/var/lib/postgresql`. If you change the tag to an older PG,
  this may flip back — check container logs on first boot (`docker logs alm-age`).
- **Custom image.** Compose now builds `alm-ontology-age:pg18-age-pgvector` from a pinned
  `apache/age` digest and installs `postgresql-18-pgvector`. No web UI is exposed by this image.
  Verify ARM support before relying on the pinned digest on non-amd64 machines.
- **agtype results are JSON-quoted.** A returned `d.id` arrives as the string `"DEF-0002"`;
  `graph_age._parse_agtype()` `json.loads`-es it. Don't compare raw.
- **Cypher must be wrapped.** `SELECT * FROM cypher('alm', $cy$ … $cy$) AS (col agtype);` — the column
  list is mandatory even for writes (we use a throwaway `v agtype`). We dollar-quote with `$cy$` (not
  `$$`) so query text is safe.
- **Params are inlined, not bound.** AGE passes params as one `agtype` map, which is awkward; for this
  tiny trusted dataset we inline values via `_lit()` (JSON-escaped). If this ever takes untrusted
  input, switch to AGE's parameter mechanism — do not interpolate raw strings.

## Nuances the plan glosses

- **`recursive_sql` is still DuckDB, not Postgres.** Phase 1 only put the *graph* in PG. The
  agreement check is rustworkx (in-mem) + recursive-CTE (DuckDB/Parquet) + Cypher (AGE/PG) — three
  independent engines, but the "rCTE inside the same Postgres" story is Phase 5. Until then, two
  different stores are involved.
- **Two-schema split still exists.** `src/alm_ontology/generated/alm_ddl.sql` (LinkML
  `SQLTableGenerator`, a demo artifact) and the runtime layout in `data_io.py` are still separate.
  Collapsing them (LinkML drives the PG relational schema) is Phase 5 / objective O3.
- **`satisfies` vs `satisfied_by`.** LinkML now declares `satisfied_by` as the inverse of
  `satisfies`, and generated artifacts were regenerated. Runtime edge derivation still comes from
  authored `ArchitectureElement.satisfies` data.
- **Graph rebuild policy.** `graph_age.impact()` still rebuilds by default. Set
  `ALM_AGE_REBUILD_ON_QUERY=0` or pass `rebuild_graph=False` after running `almon graph rebuild`.
  `almon graph run ... --no-rebuild` exercises the persisted graph path.

## Next action

Phase 4 is next: add LinkML `searchable`/`embeddable` annotations, native Postgres `tsvector` search,
FastEmbed-backed `pgvector` rows, and `almon search` / `almon similar`. Keep the Phase 5 DuckDB
retirement boundary separate unless you are ready to move relational tables into Postgres.

## Plans-management note

This packet was migrated from the former `plans/concept-handover/age-gqc-plan.md` into the dated
folder structure per `C:\dev\VectorMind\evidence-engine\WORKFLOW.md`. The `concept-handover/` research
docs (handover, POC proposal, research reports) were left in place as durable reference. A `test.md`
proof file was not split out separately — Phase 1 proof lives in `implementation.md`; create `test.md`
per the workflow if/when richer test evidence is wanted. The older `poc-proposal.md` could be
retro-filed as a closed packet if full conformance to the workflow is desired.
