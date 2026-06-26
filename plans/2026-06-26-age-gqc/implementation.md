# Implementation — Apache AGE substrate + GQC

## Progress

`▰▰▰▰▱ Phase 4/5` — Phase 4 (search and semantic exposures) done and proven; next is Phase 5
(Postgres relational parity and DuckDB retirement).

---

## Done (Phase 1 — AGE substrate, no GQC)

A third, independent graph engine (Apache AGE / openCypher) computes `impact` over a property graph
rebuilt from the warehouse on each call, and agrees with the recursive-CTE and rustworkx engines.

### Files changed

- **`docker-compose.yml`** (new) — `apache/age:latest` container `alm-age`, healthcheck, named volume,
  conn defaults matching `graph_age._conn_params()`.
- **`src/alm_ontology/graph_age.py`** (new) — AGE backend: env-overridable connection (`connect`,
  `available`), `rebuild()` drops+recreates the `alm` graph from frames, `impact()` runs Cypher and
  returns `(sorted defect ids, "age")`. Cypher helpers handle the `cypher()` wrapper (`$cy$`
  dollar-quoting), property maps, and agtype JSON unwrapping.
- **`src/alm_ontology/cli.py`** — `almon impact` gains `--engine age|all`; results collected into a
  dict and checked for agreement; AGE auto-skipped when unreachable under `all`.
- **`tests/test_cross_engine.py`** — 5 parametrized AGE-vs-rustworkx agreement tests (skip if AGE
  down) + `test_age_reports_availability`.
- **`pyproject.toml` / `uv.lock`** — added `psycopg[binary]>=3.1` (installed `psycopg==3.3.4`).

### Implementation facts

- Vertex labels mapped from node-table names (`NODE_LABELS`) and edge labels/endpoints from
  edge-table names (`EDGE_SPECS`), using `data_io.EDGE_COLUMNS` for (source, dest) order.
- Impact Cypher path: `(:Requirement{id})-[:satisfied_by]->(e0)-[:composed_of*0..N]->(e)<-[:affects]-(:Defect)`.
- Graph is rebuilt from `warehouse.load_frames_from_db()` (Parquet) on **every** `impact()` call —
  fine at this scale (~39 reqs / 28 elems / 20 defects / ~145 edges).

### Decisions made during development

- **Vertex properties limited** to `id` + short/enum fields; long free-text slots skipped
  (`SKIP_PROPS`) to keep the loader robust against quoting. Not needed for traversal.
- **Labels not yet LinkML-`SchemaView`-driven** — the `gen_age` generator is deferred to Phase 2/5;
  the table-name mapping is model-faithful enough for Phase 1.
- Kept `engine="recursive"`/`duckpgq`/`both` working; added `all` (default) which now includes AGE.

### Deviations from the plan

- **Relational tables are NOT yet in Postgres.** `graph_age` loads only the AGE graph into PG, from
  the Parquet frames. So the `recursive_sql` engine in the agreement check **still runs on DuckDB**
  (`graph_duckpgq`), not on Postgres. The plan's "rCTE native in the same Postgres" is Phase 5 work;
  Phase 1 still yields three *independent* engines agreeing, which is the point.
- **`apache/age:latest` is PG18**, which changed the data-dir convention → the named volume had to
  mount at `/var/lib/postgresql` (not `/var/lib/postgresql/data`) or the container exits on boot.
  Corrected and commented in the compose file. (Surfaces OP / risk: pin the tag.)

### Follow-up risks

- Image tag unpinned (`:latest` = PG18 today); pin `PG18_<x.y.z>` before this leaves the POC.
- pgvector is **not** in the `apache/age` image — Phase 4 must add it (or a combined image).
- Per-call graph rebuild won't scale; revisit when data grows or for a persistent-graph mode.

### Commands / proof (Phase 1)

```
docker compose up -d                       # apache/age, mount at /var/lib/postgresql
uv run almon build                         # Parquet warehouse (truth)
uv run almon impact --req REQ-0110 --engine all
#   [rustworkx]     DEF-0001, DEF-0004, DEF-0016
#   [recursive-sql] DEF-0001, DEF-0004, DEF-0016
#   [age]           DEF-0001, DEF-0004, DEF-0016
#   Cross-engine agreement (rustworkx, recursive-sql, age): MATCH (OK)
uv run pytest -q                           # 26 passed (incl. 5 AGE agreement cases, empty-result REQ-0400)
uv run ruff check .                        # clean
```

`composed_of*0..6` (zero-length path) works in AGE without a workaround — semantics match the other
engines, including the empty-result case.

## Done (Phase 2 — structured GQC for `impact`)

`impact` now has a formal YAML contract and LinkML-backed validation. The contract records the closed
shape (`fixed_multi_hop_path`), parameters, path, result, renderer entrypoints, and golden fixtures.

### Files changed

- **`src/alm_ontology/gqc/impact.gqc.yaml`** (new) — first formal GQC capability.
- **`src/alm_ontology/gqc.py`** (new) — loads GQC YAML, validates the closed shape set, validates
  classes/slots/ranges/path continuity against LinkML, and checks renderer entrypoints import.
- **`tests/test_gqc.py`** (new) — validates all GQC documents, asserts LinkML owns the
  `satisfied_by`/`satisfies` inverse, and checks `impact` fixtures across renderers.
- **`src/alm_ontology/model/alm.yaml`** — added `satisfied_by` as the LinkML inverse of `satisfies`;
  regenerated `src/alm_ontology/generated/`.
- **`src/alm_ontology/graph_rustworkx.py`** — added a module-level `impact()` renderer entrypoint.
- **`src/alm_ontology/cli.py`** — added `almon graph rebuild`, `almon graph run`, and
  `almon graph validate-gqc`.
- **`src/alm_ontology/graph_age.py`** — added persisted graph lifecycle helpers and
  `ALM_AGE_REBUILD_ON_QUERY` control; default remains rebuild-on-query.
- **`docker/age/Dockerfile` / `docker-compose.yml`** — compose now builds a project-owned image from
  the pinned AGE digest and installs `postgresql-18-pgvector`.
- **`config/embeddings.yaml` / `pyproject.toml` / `uv.lock`** — declared the FastEmbed profile and
  optional `embeddings` dependency.

### Decisions accepted during Phase 2

- **OP-002:** FastEmbed is the semantic default, using `fastembed_bge_small_en_v1_5`.
- **OP-003:** FTS will use native Postgres `tsvector`.
- **OP-004:** DuckDB is to be retired as runtime/query substrate in Phase 5; Postgres is the focus.
- **OP-005:** GQC is structured YAML plus LinkML validation, not prose.
- **OP-007:** Inverse relations belong in LinkML; GQC consumes `satisfied_by`, it does not define it.
- **Image strategy:** one custom project image for AGE + pgvector under the existing compose file.

### Commands / proof (Phase 2)

```
uv run almon model gen
uv lock
uv run almon graph validate-gqc
uv run pytest -q
# 30 passed
uv run ruff check .
# All checks passed!
uv run almon graph rebuild
uv run almon graph run impact --req REQ-0110 --no-rebuild
# [age] impacted defects (3): DEF-0001, DEF-0004, DEF-0016
docker compose build age
docker run --rm alm-ontology-age:pg18-age-pgvector bash -lc "test -f /usr/share/postgresql/18/extension/vector.control && echo vector-extension-present"
# vector-extension-present
docker compose up -d --build
docker exec alm-age psql -U postgres -d alm -tAc "CREATE EXTENSION IF NOT EXISTS vector"
docker exec alm-age psql -U postgres -d alm -tAc "SELECT extversion FROM pg_extension WHERE extname='vector'"
# 0.8.3
uv run almon impact --req REQ-0110 --engine all
# Cross-engine agreement (rustworkx, recursive-sql, age): MATCH (OK)
```

## Done (Phase 3 — remaining GQC capability registry)

The initial GQC registry now covers all planned Phase 3 capabilities:

- **`propagate_dal.gqc.yaml`** — closure from requirements through `satisfied_by` and `composed_of`;
  renderers: rustworkx + recursive SQL.
- **`refines_closure.gqc.yaml`** — transitive requirement parent closure over `refines`; renderers:
  rustworkx + recursive SQL.
- **`coverage_gaps.gqc.yaml`** — anti-join over requirements and test cases; renderer:
  recursive SQL.
- **`defects_per_element.gqc.yaml`** — count aggregation over defects affecting architecture
  elements; renderer: recursive SQL.

Implementation facts:

- Renamed the ontology inverse from `allocated_to` to `satisfied_by` after maintainer feedback.
  Runtime derived edge table is now `edge_satisfied_by`.
- `tests/test_gqc.py` now validates every GQC document and runs every declared renderer against
  fixtures. It compares renderer outputs when multiple renderers are declared.
- `AlmGraph` now has a `refines_closure()` method plus module-level renderer entrypoints for
  `impact`, `propagate_dal`, and `refines_closure`.
- `graph_duckpgq.py` now exposes recursive SQL renderer entrypoints for `impact`, `propagate_dal`,
  and `refines_closure`.
- `queries.py` now exposes renderer-friendly `coverage_gap_ids()` and
  `defect_counts_by_element()`.

Commands / proof:

```
uv run almon model gen
uv run almon build
uv run almon graph validate-gqc
# coverage_gaps: ok; defects_per_element: ok; impact: ok; propagate_dal: ok; refines_closure: ok
uv run almon graph rebuild
uv run pytest -q
# 33 passed
uv run ruff check .
# All checks passed!
uv run almon graph run impact --req REQ-0110 --no-rebuild
# [age] impacted defects (3): DEF-0001, DEF-0004, DEF-0016
```

## Done (Phase 4 — search and semantic exposures)

Postgres now exposes the rebuilt warehouse through native full-text search and FastEmbed-backed
pgvector semantic search.

Files changed:

- **`src/alm_ontology/model/alm.yaml`** — added `searchable` and `embeddable` annotations to
  human-text slots (`title`, `name`, `statement`, `acceptance`, `description`, `rationale`);
  regenerated `src/alm_ontology/generated/`.
- **`src/alm_ontology/pg_exposure.py`** (new) — rebuilds `alm_search_documents` from warehouse
  frames using LinkML annotations, creates a generated `tsvector` column + GIN index, optionally
  creates `alm_semantic_embeddings` with `vector(384)` rows, and runs FTS/semantic queries.
- **`src/alm_ontology/cli.py`** — added `almon rebuild-exposures`, `almon search`, and
  `almon similar`.
- **`.gitignore`** — ignores `.cache/`, where FastEmbed model files are cached.
- **`tests/test_pg_exposure.py`** (new) — covers annotation-derived records, Postgres FTS, and
  pgvector similarity with a fake embedder so tests do not download model weights.

Implementation facts:

- Search rows are one document per node row (`Requirement`, `ArchitectureElement`, `TestCase`,
  `Defect`), currently 126 rows in the VM-E1 dataset.
- `almon rebuild-exposures` rebuilds FTS rows only; `almon rebuild-exposures --semantic` also builds
  FastEmbed vectors in pgvector.
- FastEmbed uses the existing `fastembed_bge_small_en_v1_5` profile
  (`BAAI/bge-small-en-v1.5`, 384 dims). Runtime model files cache under `.cache/alm-ontology/`.
- Search/semantic exposures are still rebuilt from the warehouse frames; they do not make Postgres
  the relational source of truth yet. That remains Phase 5.

Commands / proof:

```
uv run almon model gen
uv run almon rebuild-exposures
# search documents   126 rows
uv run almon search "battery thermal" --limit 5
# returns REQ-0115, REQ-0111, ARC-BATT ...
uv run --extra embeddings almon rebuild-exposures --semantic
# search documents   126 rows; embeddings 126 rows
uv run --extra embeddings almon similar "battery thermal containment" --limit 5
# returns ARC-BATT, REQ-0115, REQ-0111, ARC-BMS, ARC-ELEC
uv run pytest -q
# 36 passed
uv run ruff check .
# All checks passed!
uv run almon graph validate-gqc
# all five capabilities ok
```

## Remaining (Phase 5)

- **Phase 5** — create relational tables in PG from LinkML; move `recursive_sql` onto PG; collapse the
  two-schema split; repoint reports; retire DuckDB-as-substrate (keep Parquet only as export/interchange
  if useful).
