# Plan — Apache AGE substrate + GQC (Graph Query Contract)

### Migrating the ALM ontology onto one Postgres substrate with multiple exposures, governed by a per-capability query contract

> **Status:** draft for review. Successor/evolution to [poc-proposal.md](poc-proposal.md). That
> proposal named **DuckPGQ** as the portable graph contract (with RDF "in reserve") and used
> **DuckDB + Parquet/SQLite** as the substrate. This plan supersedes both choices: DuckPGQ is
> dropped (community extension, newest DuckDB/Windows unsupported — the same fragility that
> motivated this rethink), and the substrate moves to **PostgreSQL**, chosen because it can host
> *all three exposures we want from one connected dataset*.

---

## 1. Why this change

The POC proved the spine (**model → regenerable view → tooling**) but leaned on two engines that
turned out to be operationally fragile for a "corporate-serious" target: DuckPGQ has no build for
recent DuckDB/Windows, and embedded graph libraries we considered (Kùzu) carry abandonment risk.

The reframing that resolves it: we don't want *a graph database*, we want **one connected dataset
with several task-specific exposures** over it — a graph exposure, a full-text search exposure, and
a semantic (vector) exposure — for a traceability engine where "the whole graph knows itself."

**PostgreSQL is the only substrate that delivers all three in one engine, one database, one
transaction:**

| Exposure | Postgres realization |
|---|---|
| **Graph** (traversal, impact, propagation) | **Apache AGE** — openCypher over the same tables |
| **Search** (keyword / lexical) | native `tsvector`/`tsquery` (optionally ParadeDB `pg_search` for BM25) |
| **Semantic** (similarity / recall) | **pgvector** |
| **Relational/analytical** (anti-joins, coverage) | plain SQL incl. native `WITH RECURSIVE` |

A standalone graph DB (Neo4j/Memgraph) would give a strong graph exposure but fragment search and
semantic into separate engines — breaking the "one connected dataset" property. Postgres keeps them
unified while staying the safest long-horizon bet in any enterprise.

**Risk acknowledged honestly.** AGE is an Apache-*incubating* extension whose Cypher is a *subset*
and which pins to specific Postgres majors — the same *class* of risk that DuckPGQ had. Two things
make it materially safer here: (a) Apache governance means it won't die with one vendor, and (b) the
fallback (`WITH RECURSIVE`) is native to the *same* engine over the *same* tables, so an AGE gap
never blocks us — worst case a capability is expressed in SQL instead of Cypher. If AGE ever stalls,
the data is still plain Postgres tables: zero lock-in.

---

## 2. Target architecture

```
                        data/  (authored YAML — input of record, committed)
                          │  build
                          ▼
        ┌─────────────────────────────────────────────────────────┐
        │                    PostgreSQL (one DB)                    │
        │                                                           │
        │  relational tables  ──┐                                   │
        │  (nodes + edge tables)│                                   │
        │                       ├─► GRAPH exposure   (Apache AGE)   │
        │                       ├─► SEARCH exposure  (tsvector)     │
        │                       └─► SEMANTIC exposure (pgvector)    │
        └─────────────────────────────────────────────────────────┘
              ▲                         ▲
              │ schema (nouns)          │ capabilities (verbs)
        ┌───────────┐             ┌───────────────────────────────┐
        │  LinkML   │  validates  │  GQC — Graph Query Contract    │
        │  alm.yaml │ ◄───────────│  *.gqc.yaml (per capability)   │
        └───────────┘             └───────────────────────────────┘
                                          │ authored by human/agent, conformance-gated
                                          ▼
                          renderers: recursive_sql · cypher_age · rustworkx
```

Two source-of-truth layers, both YAML, both generating/governing downstream artifacts:

- **LinkML (`alm.yaml`) = the nouns.** Classes → node tables / graph vertex labels; multivalued
  object-range slots → edge tables / graph edge labels; types and directions. Already exists.
- **GQC (`*.gqc.yaml`) = the verbs.** A *closed registry of named capabilities* (traversals,
  anti-joins, aggregations) over the LinkML vocabulary. New in this plan.

The mantra grows one box: *model (LinkML) + query contract (GQC) → regenerable multi-engine views →
tooling.* "Tables are truth" is unchanged — every exposure is rebuilt from the tables; nothing is a
store of record except the authored `data/`.

---

## 3. GQC — Graph Query Contract

### 3.1 What GQC is (and is deliberately not)

- **Is:** a finite, named set of parameterized *capabilities*, each declared once in YAML, validated
  against LinkML, carrying golden conformance fixtures.
- **Is not:** a graph query language. You cannot author arbitrary patterns in it. New capabilities
  are added as named instances of a closed set of **five shapes**; anything that isn't one of these
  is a signal to push back, not to extend the DSL.

| Shape | recursive_sql | cypher_age | rustworkx |
|---|---|---|---|
| bounded/unbounded **closure** over one edge | `WITH RECURSIVE` | `-[:rel*0..n]->` | BFS |
| fixed **multi-hop path** | joins | `MATCH (a)-[]->(b)-[]->(c)` | walk |
| **anti-join / negation** | `NOT EXISTS` | `OPTIONAL MATCH … IS NULL` ⚠️ | set diff |
| **aggregation / count** | `GROUP BY` | `count()` | dict tally |
| property **filter** | `WHERE` | `WHERE` | predicate |

"Common across all engines" means the **intersection** of what every targeted engine can do — not the
union. The anti-join shape graphs poorly (Cypher), so it is allowed to target only `recursive_sql`
(see §3.4).

### 3.2 Renderers are authored, not generated — conformance is the gate

Per the agreed decision: we target a small number of capabilities and **do not** build an automated
GQC→dialect compiler. Instead, for each capability a human or an agent reads the GQC spec (+ the
LinkML schema) and **authors** the concrete query in each target language — including the imperative
rustworkx code. Those renderers are committed and reviewed.

What keeps hand/agent-authored renderers honest is the **conformance test**, generated from GQC:
for every capability, run each declared renderer over the golden fixtures and assert (a) every
renderer agrees with every other, and (b) all agree with the expected rows. This is the generalized,
per-capability successor to today's hand-written [test_cross_engine.py](../../tests/test_cross_engine.py)
— "the graph is a faithful regenerable view" enforced for every capability by construction.

### 3.3 A capability, concretely

```yaml
# gqc/impact.gqc.yaml
capability: impact
title: Defects impacted by a requirement, via allocation then composition depth.
params:
  requirement: { type: node_ref, class: Requirement }   # class checked vs LinkML
  max_depth:   { type: int, default: 6 }
returns:
  - { name: defect, class: Defect }

# Declarative intent in ontology vocabulary. Structured enough to (1) validate
# against LinkML and (2) feed an agent a precise spec — but NOT compiled.
pattern:
  start: { class: Requirement, bind: r, where: { id: $requirement } }
  steps:
    - traverse: { edge: allocated_to, from: r, bind: e0 }   # = inverse(satisfies); see §5
    - closure:  { edge: composed_of, from: e0, min: 0, max: $max_depth, bind: e }
    - traverse: { edge: affects, to: e, direction: in, bind: d }
  select: { distinct: "d.id as defect", order_by: defect }

engines: [recursive_sql, cypher_age, rustworkx]   # renderers that must exist AND agree

renderers:                       # pointers to the authored, reviewed query code
  recursive_sql: queries/impact.sql
  cypher_age:    queries/impact.cypher
  rustworkx:     graph_rustworkx.py::AlmGraph.impact

conformance:                     # golden oracle — every renderer must reproduce these
  - params: { requirement: REQ-0110, max_depth: 6 }
    expect: [DEF-0002, DEF-0005]
  - params: { requirement: REQ-0400, max_depth: 6 }
    expect: []
```

### 3.4 Per-capability engine targeting (the escape hatch)

`engines:` is per capability. Capabilities that don't fit the graph cleanly simply omit the
graph renderers. The completeness check is the canonical case — [queries.py](../../src/alm_ontology/queries.py)
states *"completeness is an anti-join, not a graph pattern."* So:

```yaml
capability: coverage_gaps
engines: [recursive_sql]          # relational only; no Cypher renderer, no agreement check for it
```

The conformance/agreement check only fires where a capability declares ≥2 engines. This keeps the
contract honest rather than forcing anti-joins through Cypher.

### 3.5 Initial capability set (the closed registry, v1)

| Capability | Shape(s) | engines |
|---|---|---|
| `impact` | traverse → closure → traverse | recursive_sql, cypher_age, rustworkx |
| `propagate_dal` | closure + filter (strongest-DAL down composition) | recursive_sql, rustworkx |
| `refines_closure` | closure over `refines` | recursive_sql, cypher_age, rustworkx |
| `coverage_gaps` | anti-join | recursive_sql only |
| `defects_per_element` | aggregation | recursive_sql (+ cypher_age optional) |

---

## 4. The three exposures, built from the tables

All exposures are regenerated by `build`; none is a store of record.

- **Graph (AGE).** `build` runs `create_graph('alm')`, derives `create_vlabel` per LinkML class and
  `create_elabel` per relationship slot, then loads vertices from the node tables and edges from the
  relationship/edge tables. One named graph `alm` = one connected graph (satisfies "the whole graph
  knows itself"). Cypher renderers run via `cypher('alm', $$ … $$)`.
- **Search (FTS).** Generate a `tsvector` column (or a separate FTS table) over the human-text slots
  (`title`, `statement`, `description`, `rationale`, `acceptance`) with a GIN index. Which slots are
  searchable is declared via a LinkML slot annotation so it stays model-driven (see §5).
- **Semantic (pgvector).** An `embeddings` table keyed by node id with a `vector` column; populated
  by embedding the same text slots. Which slots are embeddable is likewise a LinkML annotation.
  (Embedding model + dimension is an open point — §9.)

---

## 5. Connecting LinkML — the model drives everything

The LinkML model already declares the full node/edge typing; the SQL generator proves it by
materializing relationship slots as M2M join tables. This plan stops discarding that:

1. **Relational schema from LinkML.** Point `SQLTableGenerator` at Postgres. This collapses today's
   *two-schema split* — the committed generated DDL (LinkML, currently a demo artifact) vs the
   hand-rolled runtime layout in [data_io.py](../../src/alm_ontology/data_io.py) — into one
   model-driven schema.
2. **Graph labels from LinkML.** Add a `gen_age` step in [modelgen.py](../../src/alm_ontology/modelgen.py)
   that walks the `SchemaView`: classes → VLABELs, multivalued object-range slots → ELABELs. ~30
   lines, fits the existing "model once, generate many" pattern. No official LinkML→AGE generator
   exists; this is a small custom walker.
3. **Inverse/alias edges live in GQC.** LinkML slots are single-named and directional; the model
   calls allocation `satisfies` (element→requirement) while traversal wants `allocated_to`
   (requirement→element). GQC declares `allocated_to: inverse(satisfies)` — resolving the one place
   model and runtime disagree, in the layer whose job is convenient traversal vocabulary.
4. **Exposure annotations on slots.** LinkML slot annotations (`searchable: true`, `embeddable: true`)
   drive which text columns get `tsvector` / `pgvector` treatment — so all three exposures derive
   from the single spine.
5. **Validation stays Pydantic** (LinkML-generated) at load time — unchanged.
6. **GQC validated against LinkML.** GQC `pattern` references (classes, edges, directions) are
   checked against the LinkML schema at lint/test time: a capability cannot reference an edge the
   ontology doesn't have, and renaming a slot flags every capability that used it.

---

## 6. Engine strategy & testing

- **recursive_sql** — native Postgres `WITH RECURSIVE` over the edge tables. The current
  [_impact_recursive](../../src/alm_ontology/graph_duckpgq.py) query ports essentially unchanged; it
  is both a first-class renderer and the in-DB cross-check against Cypher.
- **cypher_age** — authored Cypher via `cypher('alm', …)`.
- **rustworkx** — authored imperative code; also the **infra-free oracle** that runs in CI *without*
  Docker/Postgres, so correctness checks aren't hostage to a live server.
- **Conformance/agreement test** — generated from GQC: per capability, all declared renderers agree
  with each other and with golden fixtures.

---

## 7. Operability & ergonomics (AGE) — what the investigation found

Deployment is fixed: **self-hosted, Docker-only, no cloud** (resolves open point #1 in AGE's favour —
self-hosted Postgres *can* install AGE; managed services generally cannot).

**Ops burden — low by design.** AGE is "just Postgres." The official `apache/age` image is a stock
Postgres image (**~174 MB**, on par with base `postgres`) with the extension preloaded; it's actively
published (~52k pulls/week, rebuilt within days). Standard PG tooling — `psql`, pgAdmin, `pg_dump`,
connection pooling, replication — all work unchanged. There is **no second engine, backup strategy,
or monitoring stack** to run, so the incremental admin cost over "running a Postgres container" is
near-zero. This is the decisive answer to the "needs 10 admins" worry: it folds into existing PG ops
rather than adding a specialist system.

**Install gotchas (minor, all known):**
- Requires `shared_preload_libraries = 'age'` in `postgresql.conf`, then
  `CREATE EXTENSION age; LOAD 'age'; SET search_path = ag_catalog, "$user", public;`. The official
  image handles the preload; a from-source build does not — **use the official image**.
- **ARM**: multi-arch support has been a historical pain point — verify the chosen tag runs on our
  hardware (Apple Silicon / ARM servers) before committing.
- Run `CREATE EXTENSION age` *before* granting `CREATE` on the DB to other roles, so `ag_catalog` is
  owned correctly.

**Version lag — modest and invisible to us.** AGE now covers PG 11–18 (v1.7.0 / PG18, Jan 2026) but
historically trails a new Postgres major by ~one quarter. Because we pin a Docker image to a fixed PG
major, that lag never reaches us.

**The real cost is Cypher ergonomics, not ops:**
- Every Cypher query is wrapped — `SELECT * FROM cypher('alm', $$ … $$) AS (col agtype);` with explicit
  result columns + casting — the single most common "why won't this run?" cause.
- Parameters pass as **one `agtype` map**, not individual bind params — this shapes how we author the
  `cypher_age` GQC renderers.
- openCypher is a **subset**: no `MERGE … ON CREATE/ON MATCH SET`, no `datetime()`, no
  `EXISTS { subquery }`, no `NOT (pattern)` in `WHERE`, weak `count()` on empty matches, limited
  list/string functions, no APOC/GDS algorithm libraries.

**Why most of that misses us.** Our queries are bounded, well-indexed, and JOIN back to relational data
(AGE's sweet spot, not the deep-traversal-at-scale case where it loses); we rebuild the graph from
tables each run, so no `MERGE` upserts; and `coverage_gaps` already stays in `recursive_sql`, sidestepping
AGE's weak negation. The plan's per-capability engine targeting (§3.4) is the right hedge. Net residual
cost to us: the `cypher()` wrapper + agtype-map params when authoring `cypher_age` renderers.

> Sources: [Docker Hub apache/age](https://hub.docker.com/r/apache/age),
> [apache/age (GitHub)](https://github.com/apache/age),
> [gdotv — Apache AGE Explained](https://gdotv.com/blog/apache-age-explained/),
> [openCypher compliance issue #2323](https://github.com/apache/age/issues/2323),
> [PuppyGraph — Apache Graph Database](https://www.puppygraph.com/blog/apache-graph-database).

---

## 8. Build phases (increments)

1. **AGE substrate, end-to-end, no GQC yet.** Docker `compose` with Postgres + AGE (+ pgvector).
   `build` loads relational tables + the `alm` graph from LinkML-derived labels. Author one Cypher
   `impact` by hand, wire `engine="age"` into the existing `impact()` dispatch, and add it to the
   cross-engine test (Cypher vs native-PG recursive CTE vs rustworkx). *Proves the second real
   backend before we abstract over it.*
2. **Introduce GQC with `impact` as the first capability.** Define `impact.gqc.yaml` (pattern +
   fixtures + renderer pointers); move the three authored renderers under it; generate the
   conformance test from the contract. Add GQC↔LinkML validation.
3. **Port the rest of the registry.** `propagate_dal`, `refines_closure`, `coverage_gaps`,
   `defects_per_element` — each as a GQC capability with its authored renderers.
4. **Search + semantic exposures.** `searchable`/`embeddable` LinkML annotations → `tsvector` (GIN)
   and `pgvector` (embeddings table) built by `build`; add `almon search` / `almon similar` verbs.
5. **Reporting/CLI parity + cleanup.** Repoint reports at PG; retire DuckDB-as-substrate; keep a
   Parquet/SQLite *export* only if we decide to (§9).

Phases 1–3 are the meaningful core; 4–5 build out the multi-exposure story.

---

## 9. Open points (need decisions)

1. ~~**Deployment target for AGE.**~~ **RESOLVED** — self-hosted, Docker-only, no cloud. Self-hosted
   Postgres can install AGE, so the choice stands; operability findings are in §7. *Retained caveat
   only:* if hosting ever moves to a managed service (RDS / Cloud SQL / Azure Flexible), AGE — and
   ParadeDB `pg_search` (#3) — would not be installable and the graph layer would need revisiting.
2. **Embedding model for pgvector.** Local (sentence-transformers, offline, no API key, ~384/768-dim)
   vs hosted API. Affects dimension, determinism, and whether `build` needs network. *Recommend:*
   local sentence-transformers for the POC (offline, reproducible); make the field/dimension config.
   Is semantic search in scope for v1 or a stub?
3. **FTS engine.** Native `tsvector` (zero deps, ships with PG) vs ParadeDB `pg_search` for true BM25
   (another extension to install — compounds the managed-PG question in #1). *Recommend:* native
   `tsvector` for v1; revisit BM25 only if ranking quality demands it.
4. **DuckDB / Parquet retention.** Drop DuckDB entirely once PG is the substrate, or keep a Parquet
   (and/or SQLite) *export* as the handover's "cloud escape hatch"? *Recommend:* PG is the runtime
   substrate; keep a cheap Parquet **export** for portability, drop DuckDB as a query engine.
5. **GQC pattern formality.** Structured + LinkML-validated (my recommendation — enables refactor
   safety and precise agent prompts) vs lightweight prose/pseudocode. Even without a compiler, the
   structured form earns its keep.
6. **Migration style.** Hard-cut a branch to PG, or keep the DuckDB/SQLite path working in parallel
   during migration? *Recommend:* branch + hard-cut, but preserve the rustworkx in-memory path so
   tests run without Docker.
7. **Canonical edge naming.** Confirm GQC (not LinkML annotations) is where inverse/alias edges like
   `allocated_to = inverse(satisfies)` are declared.
8. **Plan home / search+semantic split.** This plan now folds in FTS + pgvector (per decision). Keep
   them in this one plan, or split the multi-exposure work into a sibling plan once graph+GQC lands?

---

## 10. Out of scope (for now)

- An automated GQC→dialect **compiler** (explicitly rejected — renderers are human/agent-authored,
  conformance-gated).
- RBAC/multi-tenant/clustering concerns of the eventual deployment (separate ops plan).
- MCP server surface (the CLI verbs remain the contract; wrapping is mechanical, later).
- RDF/SPARQL standards port (still held in reserve, as in the original proposal).
