# Implementation â€” Apache AGE substrate + GQC

## Progress

`Done` - Phase 5 (Postgres relational parity and DuckDB/Parquet retirement) is implemented and
proven.

---

## Done (Phase 1 â€” AGE substrate, no GQC)

A third, independent graph engine (Apache AGE / openCypher) computes `impact` over a property graph
rebuilt from the warehouse on each call, and agrees with the recursive-CTE and rustworkx engines.

### Files changed

- **`docker-compose.yml`** (new) â€” `apache/age:latest` container `alm-age`, healthcheck, named volume,
  conn defaults matching `graph_age._conn_params()`.
- **`src/alm_graph/age.py`** (new) â€” AGE backend: env-overridable connection (`connect`,
  `available`), `rebuild()` drops+recreates the `alm` graph from frames, `impact()` runs Cypher and
  returns `(sorted defect ids, "age")`. Cypher helpers handle the `cypher()` wrapper (`$cy$`
  dollar-quoting), property maps, and agtype JSON unwrapping.
- **`src/alm_cli/cli.py`** â€” `almon impact` gains `--engine age|all`; results collected into a
  dict and checked for agreement; AGE auto-skipped when unreachable under `all`.
- **`tests/test_cross_engine.py`** â€” 5 parametrized AGE-vs-rustworkx agreement tests (skip if AGE
  down) + `test_age_reports_availability`.
- **`pyproject.toml` / `uv.lock`** â€” added `psycopg[binary]>=3.1` (installed `psycopg==3.3.4`).

### Implementation facts

- Vertex labels mapped from node-table names (`NODE_LABELS`) and edge labels/endpoints from
  edge-table names (`EDGE_SPECS`), using `data_io.EDGE_COLUMNS` for (source, dest) order.
- Impact Cypher path: `(:Requirement{id})-[:satisfied_by]->(e0)-[:composed_of*0..N]->(e)<-[:affects]-(:Defect)`.
- Graph is rebuilt from `warehouse.load_frames_from_db()` (Parquet) on **every** `impact()` call â€”
  fine at this scale (~39 reqs / 28 elems / 20 defects / ~145 edges).

### Decisions made during development

- **Vertex properties limited** to `id` + short/enum fields; long free-text slots skipped
  (`SKIP_PROPS`) to keep the loader robust against quoting. Not needed for traversal.
- **Labels not yet LinkML-`SchemaView`-driven** â€” the `gen_age` generator is deferred to Phase 2/5;
  the table-name mapping is model-faithful enough for Phase 1.
- Kept `engine="recursive"`/`duckpgq`/`both` working; added `all` (default) which now includes AGE.

### Deviations from the plan

- **Relational tables are NOT yet in Postgres.** `graph_age` loads only the AGE graph into PG, from
  the Parquet frames. So the `recursive_sql` engine in the agreement check **still runs on DuckDB**
  (`graph_duckpgq`), not on Postgres. The plan's "rCTE native in the same Postgres" is Phase 5 work;
  Phase 1 still yields three *independent* engines agreeing, which is the point.
- **`apache/age:latest` is PG18**, which changed the data-dir convention â†’ the named volume had to
  mount at `/var/lib/postgresql` (not `/var/lib/postgresql/data`) or the container exits on boot.
  Corrected and commented in the compose file. (Surfaces OP / risk: pin the tag.)

### Follow-up risks

- Image tag unpinned (`:latest` = PG18 today); pin `PG18_<x.y.z>` before this leaves the POC.
- pgvector is **not** in the `apache/age` image â€” Phase 4 must add it (or a combined image).
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

`composed_of*0..6` (zero-length path) works in AGE without a workaround â€” semantics match the other
engines, including the empty-result case.

## Done (Phase 2 â€” structured GQC for `impact`)

`impact` now has a formal YAML contract and LinkML-backed validation. The contract records the closed
shape (`fixed_multi_hop_path`), parameters, path, result, renderer entrypoints, and golden fixtures.

### Files changed

- **`src/alm_graph/gqc_specs/impact.gqc.yaml`** (new) â€” first formal GQC capability.
- **`src/alm_graph/gqc.py`** (new) â€” loads GQC YAML, validates the closed shape set, validates
  classes/slots/ranges/path continuity against LinkML, and checks renderer entrypoints import.
- **`tests/test_gqc.py`** (new) â€” validates all GQC documents, asserts LinkML owns the
  `satisfied_by`/`satisfies` inverse, and checks `impact` fixtures across renderers.
- **`src/alm_model/model/alm.yaml`** â€” added `satisfied_by` as the LinkML inverse of `satisfies`;
  regenerated `src/alm_model/generated/`.
- **`src/alm_graph/rustworkx.py`** â€” added a module-level `impact()` renderer entrypoint.
- **`src/alm_cli/cli.py`** â€” added `almon graph rebuild`, `almon graph run`, and
  `almon graph validate-gqc`.
- **`src/alm_graph/age.py`** â€” added persisted graph lifecycle helpers and
  `ALM_AGE_REBUILD_ON_QUERY` control; default remains rebuild-on-query.
- **`docker/age/Dockerfile` / `docker-compose.yml`** â€” compose now builds a project-owned image from
  the pinned AGE digest and installs `postgresql-18-pgvector`.
- **`config/embeddings.yaml` / `pyproject.toml` / `uv.lock`** â€” declared the FastEmbed profile and
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

## Done (Phase 3 â€” remaining GQC capability registry)

The initial GQC registry now covers all planned Phase 3 capabilities:

- **`propagate_dal.gqc.yaml`** â€” closure from requirements through `satisfied_by` and `composed_of`;
  renderers: rustworkx + recursive SQL.
- **`refines_closure.gqc.yaml`** â€” transitive requirement parent closure over `refines`; renderers:
  rustworkx + recursive SQL.
- **`coverage_gaps.gqc.yaml`** â€” anti-join over requirements and test cases; renderer:
  recursive SQL.
- **`defects_per_element.gqc.yaml`** â€” count aggregation over defects affecting architecture
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

## Done (Phase 4 â€” search and semantic exposures)

Postgres now exposes the rebuilt warehouse through native full-text search and FastEmbed-backed
pgvector semantic search.

Files changed:

- **`src/alm_model/model/alm.yaml`** â€” added `searchable` and `embeddable` annotations to
  human-text slots (`title`, `name`, `statement`, `acceptance`, `description`, `rationale`);
  regenerated `src/alm_model/generated/`.
- **`src/alm_exposure/pg.py`** (new) â€” rebuilds `alm_search_documents` from warehouse
  frames using LinkML annotations, creates a generated `tsvector` column + GIN index, optionally
  creates `alm_semantic_embeddings` with `vector(384)` rows, and runs FTS/semantic queries.
- **`src/alm_cli/cli.py`** â€” added `almon rebuild-exposures`, `almon search`, and
  `almon similar`.
- **`.gitignore`** â€” ignores `.cache/`, where FastEmbed model files are cached.
- **`src/tests/test_pg_exposure.py`** (new) â€” covers annotation-derived records, Postgres FTS, and
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

## Source Layout Restructure

After Phase 4, the former single `src/alm_ontology/` package was split into focused top-level
packages:

- **`src/alm_core/`** — shared paths, data loading, warehouse build/readback, and analytical SQL
  query helpers.
- **`src/alm_model/`** — LinkML model, model generation, and generated artifacts.
- **`src/alm_graph/`** — AGE, recursive SQL, rustworkx, GQC validator, and GQC
  YAML specs.
- **`src/alm_exposure/`** — Postgres FTS/pgvector exposure rebuild and query code.
- **`src/alm_reports/`** — report, chart, and local report serving code.
- **`src/alm_cli/`** — Typer CLI entry point.
- **`src/tests/`** — test suite, now colocated under `src`.

`pyproject.toml` now points `almon` at `alm_cli.cli:app`, packages each top-level source package
explicitly, excludes `src/alm_model/generated` from Ruff, and sets pytest `testpaths = ["src/tests"]`.
`handoff.md` was deleted by maintainer request; ongoing operational notes now live in this
implementation log.

## Done (Phase 5 - Postgres relational parity and DuckDB/Parquet retirement)

The active runtime/build path now uses Postgres warehouse tables only. DuckDB and Parquet were
removed from the code path and dependency graph.

Files changed:

- **`src/alm_core/postgres.py`** (new) - shared env-overridable Postgres connection helper. The
  default host is `127.0.0.1` to avoid the 5s IPv6 fallback delay observed with `localhost`.
- **`src/alm_core/warehouse.py`** - `almon build` now validates authored YAML and replaces native
  Postgres tables (`requirements`, `architecture_elements`, `test_cases`, `defects`, and edge
  tables). It no longer writes SQLite or Parquet artifacts.
- **`src/alm_graph/sql.py`** (new) - native Postgres recursive-SQL renderers for `impact`,
  `propagate_dal`, and `refines_closure`.
- **`src/alm_graph/duckpgq.py`** - removed.
- **`src/alm_core/queries.py`**, **`src/alm_reports/report.py`**, **`src/alm_cli/cli.py`**, and GQC
  YAML renderer pointers - repointed from DuckDB/DuckPGQ to Postgres recursive SQL.
- **`pyproject.toml` / `uv.lock`** - removed `duckdb` and `pyarrow`.
- **`src/tests/test_cross_engine.py`** - AGE agreement tests now rebuild the persisted AGE graph once
  and query it with `rebuild_graph=False`; product defaults still rebuild on query.

Implementation facts:

- `almon build` now reports `Warehouse built -> postgres@127.0.0.1:5432/alm`.
- Recursive SQL, AGE, rustworkx, FTS, and pgvector all rebuild/read from the same Postgres warehouse
  tables.
- The active source and top-level docs have no remaining `duckdb`, `duckpgq`, `parquet`, `pyarrow`,
  or SQLite runtime references.
- AGE graph rebuilds mutate the shared graph name `alm`; do not run two AGE graph rebuild/query
  smoke tests concurrently against the same local database.

Commands / proof:

```
uv lock
# Removed duckdb v1.5.4
# Removed pyarrow v24.0.0

uv run almon build
# requirements 39; architecture_elements 28; test_cases 39; defects 20
# edge_refines 37; edge_composed_of 27; edge_satisfied_by 35; edge_affects 23; edge_violates 23
# Warehouse built -> postgres@127.0.0.1:5432/alm

uv run pytest -q
# 35 passed in 4.44s

uv run ruff check .
# All checks passed!

uv run almon graph validate-gqc
# coverage_gaps: ok; defects_per_element: ok; impact: ok; propagate_dal: ok; refines_closure: ok
# GQC validation passed.

uv run almon impact --req REQ-0110 --engine all
# rustworkx, recursive-sql, and age all return DEF-0001, DEF-0004, DEF-0016
# Cross-engine agreement: MATCH (OK)

uv run --extra embeddings almon rebuild-exposures --semantic
# search documents 126 rows; embeddings 126 rows

uv run almon search "battery thermal" --limit 2
# returns REQ-0115 and REQ-0111

uv run --extra embeddings almon similar "battery thermal containment" --limit 3
# returns ARC-BATT, REQ-0115, and REQ-0111
```
