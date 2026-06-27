# Plan — Apache AGE substrate + GQC (Graph Query Contract)

Migrate the ALM ontology graph layer onto one Postgres substrate with multiple task-specific
exposures (graph / search / semantic), governed by a per-capability **Graph Query Contract**.

> Successor to [../concept-handover/poc-proposal.md](../concept-handover/poc-proposal.md) (which named
> DuckPGQ + DuckDB/Parquet). Background: [../concept-handover/](../concept-handover/).

---

## Problem summary

The POC's portable graph contract relied on **DuckPGQ**, a DuckDB community extension with no build
for recent DuckDB/Windows; the SQL-side graph silently falls back to a recursive CTE. Embedded graph
libraries considered as replacements (Kùzu) carry abandonment risk. For a "corporate-serious" target
we need a graph layer that is operationally durable and that does not fragment the other access
patterns we want (keyword search, semantic recall) across separate engines.

## Resolution summary

Adopt **PostgreSQL as the single substrate** and expose the same connected dataset three ways —
**graph via Apache AGE (openCypher)**, **search via `tsvector`**, **semantic via `pgvector`** — plus
native relational SQL (incl. `WITH RECURSIVE`). Keep "tables are truth, the graph is a regenerable
view": every exposure is rebuilt from the tables. Govern the supported graph questions with **GQC**,
a closed registry of named, parameterized capabilities defined once in YAML, validated against the
LinkML schema, with per-engine renderers **authored by human/agent (not compiled)** and kept honest
by a generated **conformance/agreement** check.

## Goal and objectives

- **G.** One durable, low-ops substrate serving graph + search + semantic over one connected dataset.
- **O1.** AGE/openCypher as a first-class graph engine that agrees with the recursive-CTE and
  rustworkx engines (cross-engine agreement preserved).
- **O2.** GQC: a finite, LinkML-validated capability contract; renderers authored, conformance-gated.
- **O3.** LinkML drives all projections — relational DDL, graph labels, and search/vector columns —
  collapsing today's two-schema split.
- **O4.** Self-hosted, Docker-only deployment (no cloud).

## Design approach (durable)

- **Two source-of-truth layers.** LinkML (`alm.yaml`) = the **nouns** (classes→vertices, multivalued
  object-range slots→edges, types, directions). GQC (`*.gqc.yaml`) = the **verbs** (named traversals
  over those nouns), validated against LinkML. Mantra: *model (LinkML) + query contract (GQC) →
  regenerable multi-engine views → tooling.*
- **Three exposures, all rebuilt from tables.** Graph = AGE named graph `alm` (one connected graph);
  Search = `tsvector` + GIN over human-text slots; Semantic = `pgvector` embeddings table. Which
  slots are `searchable`/`embeddable` is declared via LinkML slot annotations.
- **GQC is a contract, not a query language.** Capabilities are *named instances* of a closed set of
  **five shapes**: closure over one edge; fixed multi-hop path; anti-join/negation; aggregation/count;
  property filter. "Common across engines" = the **intersection**. Anything not expressible as these
  five is a signal to push back, not to extend the DSL.
- **Renderers authored, conformance-gated.** No GQC→dialect compiler. A human/agent reads the GQC
  spec (+ LinkML) and authors the `recursive_sql` / `cypher_age` / `rustworkx` query; a generated test
  asserts every declared renderer agrees with the others and with golden fixtures. `engines:` is
  per-capability — anti-joins (e.g. `coverage_gaps`) may target `recursive_sql` only.
- **Engine roles.** `recursive_sql` (native PG `WITH RECURSIVE`) doubles as the in-DB cross-check;
  `cypher_age` is the AGE renderer; `rustworkx` is also the **infra-free oracle** that runs in CI
  without Docker/Postgres.
- **Source layout.** Runtime code is split into focused top-level packages under `src/`:
  `alm_core`, `alm_model`, `alm_graph`, `alm_exposure`, `alm_reports`, and `alm_cli`; tests live under
  `src/tests`. This replaces the former single `alm_ontology` package.

## Scope and non-goals

**In scope:** AGE graph exposure; GQC contract + conformance harness; LinkML-driven schema/labels/
exposure columns; FTS + pgvector exposures; the initial capability registry (`impact`,
`propagate_dal`, `refines_closure`, `coverage_gaps`, `defects_per_element`).

**Non-goals:** an automated GQC→dialect compiler (explicitly rejected); RBAC/clustering/HA ops of the
deployment (separate concern); MCP server surface (CLI verbs remain the contract); RDF/SPARQL port
(held in reserve); managed-cloud Postgres (deployment is self-hosted Docker).

## Open points

| ID | Topic | Status | Resolution / recommendation |
|---|---|---|---|
| **OP-001** | AGE deployment target | **Resolved** | Self-hosted, Docker-only (no cloud) → AGE installable. Managed PG (RDS/Cloud SQL/Azure) cannot install AGE; revisit only if hosting model changes. |
| **OP-002** | Embedding model (pgvector) | **Resolved** | Use local FastEmbed, aligned with `C:\dev\VectorMind\evidence-engine`: default profile `fastembed_bge_small_en_v1_5` / `BAAI/bge-small-en-v1.5` / 384 dims; keep profile configurable. |
| **OP-003** | FTS engine | **Resolved** | Use native Postgres `tsvector` + GIN first. Do not add ParadeDB unless ranking quality creates a concrete need. |
| **OP-004** | DuckDB/Parquet retention | **Resolved** | Remove DuckDB and Parquet from the runtime/build path for now; focus on Postgres warehouse tables as the relational substrate. |
| **OP-005** | GQC pattern formality | **Resolved** | Use structured YAML, LinkML-validated, with the closed shape set. `impact.gqc.yaml` is the first capability. |
| **OP-006** | Migration style | **Resolved (direction)** | Incremental implementation; AGE added alongside the old path first; rustworkx kept as infra-free oracle; DuckDB retired in Phase 5. |
| **OP-007** | Canonical edge naming | **Resolved** | LinkML owns ontologically relevant inverse relations. `satisfied_by` is now declared in LinkML as the inverse of `satisfies`; GQC consumes that model relation rather than defining the inverse itself. |
| **OP-008** | FTS/semantic plan home | **Resolved** | Folded into this packet (not a sibling plan). |

## Implementation phases

1. **AGE substrate, end-to-end, no GQC.** Docker Postgres+AGE; load the `alm` graph; hand-authored
   Cypher `impact`; `engine="age"` in the dispatch; three-way agreement test.
2. **Introduce GQC** with `impact` as the first capability (pattern + fixtures + renderer pointers);
   add conformance coverage; add GQC↔LinkML validation.
3. **Port the registry** — `propagate_dal`, `refines_closure`, `coverage_gaps`, `defects_per_element`.
4. **Search + semantic exposures** — `searchable`/`embeddable` annotations → `tsvector` + `pgvector`;
   `almon search` / `almon similar`.
5. **Parity + cleanup** — relational tables created in PG from LinkML; move `recursive_sql` onto PG;
   repoint reports; retire DuckDB and Parquet from the active runtime/build path.

## Dependencies and risks

- **AGE maturity.** Apache-incubating; openCypher **subset** (no `MERGE … ON CREATE/MATCH SET`, no
  `datetime()`, no `EXISTS{}`, weak `NOT (pattern)`/`count()` on empty, no APOC/GDS). Mitigated: our
  queries are bounded and JOIN-back-friendly (AGE's sweet spot); anti-joins stay in `recursive_sql`;
  fallback (`WITH RECURSIVE`) is native to the same engine.
- **Version/tag pinning.** The project now builds a custom image from a pinned `apache/age` digest
  and installs `postgresql-18-pgvector`. Verify ARM image support for the target hardware before
  relying on the digest outside this workstation.
- **Ergonomics, not ops.** Cost is the `cypher()` wrapper + single-`agtype`-map params + casting, not
  administration (AGE is "just Postgres": standard tooling, ~Postgres-sized image).
- **External dep:** a running Docker daemon for any AGE-backed path; tests skip when unreachable.

## Exit criteria

- `almon impact --engine all` shows AGE agreeing with `recursive-sql` and `rustworkx`.
- Each GQC capability's declared renderers agree with each other and with golden fixtures (generated
  conformance test green).
- LinkML drives relational DDL, AGE labels, and exposure columns; the two-schema split is gone.
- Search and semantic exposures answer `almon search` / `almon similar` from the rebuilt-from-tables
  indexes.
- Rebuilding the Postgres warehouse tables reproduces identical results on every engine
  (regenerable view).
