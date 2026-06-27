# Architecture

This page expands on the conceptual diagram in the [root README](../README.md). It
explains *what the layers are*, *how the ontology reaches every layer*, and *why the
graph can be thrown away and rebuilt at any time*.

## The spine: model → regenerable view → tooling

The whole system is one sentence: **the model is the schema, the tables are truth,
and everything else is a regenerable view.**

- The **model** (an ontology) fixes the vocabulary — what kinds of things exist and
  how they relate.
- The **facts** are instances of that vocabulary, validated and held in a single
  source of truth.
- Every **graph**, **search index**, and **answer** is rebuilt from that source of
  truth on demand. Nothing downstream is a store of record, so it can always be
  dropped and regenerated without losing information.

This discipline is what makes the analyses trustworthy: there is exactly one place
where facts live, and the model governs how they may be shaped and questioned.

## The concepts (the README diagram, in words)

| Concept | What it is |
|---|---|
| **Ontology** | The shared vocabulary: entity types, relationships, controlled terms. |
| **Authored knowledge** | The domain as written by hand — the inputs of record. |
| **Source of truth** | The validated facts, in a single canonical store. |
| **Graph** | The same facts viewed as a connected web, rebuilt from the store. |
| **Query contract** | The catalogue of questions the system agrees to answer. |
| **Answers & insight** | Traceability, impact, coverage, propagation, and search. |

The ontology is not just the top of the stack — it *governs* each layer below it: it
shapes and validates the facts, names the nodes and edges of the graph, and
constrains which questions the query contract may pose.

## How each concept is instantiated

| Concept | Realization in this repo |
|---|---|
| **Ontology** | LinkML schema [`alm.yaml`](../src/alm_model/model/alm.yaml) → generated Pydantic types, SQL DDL, and docs ([`modelgen.py`](../src/alm_model/modelgen.py)). |
| **Source of truth** | Committed [`data/*.yaml`](../data/), validated and loaded into Postgres warehouse node + edge tables ([`warehouse.py`](../src/alm_core/warehouse.py)). |
| **Graph** | Rebuilt from the tables on demand — *tables are truth, the graph is a regenerable view*. |
| **Query contract** | Graph Query Contract specs [`*.gqc.yaml`](../src/alm_graph/gqc_specs/), validated against the ontology's classes and slots ([`gqc.py`](../src/alm_graph/gqc.py)). |
| **Graph engines** | Apache AGE / openCypher ([`age.py`](../src/alm_graph/age.py)), recursive SQL ([`sql.py`](../src/alm_graph/sql.py)), and in-memory rustworkx ([`rustworkx.py`](../src/alm_graph/rustworkx.py)). |
| **Search exposures** | Postgres full-text search and pgvector semantic similarity ([`pg.py`](../src/alm_exposure/pg.py)). |
| **Answers** | impact · coverage · DAL propagation · refines closure · search. |

## The model is the single source of truth

`alm.yaml` is authored once; the Pydantic types, SQL DDL, and Markdown docs are
*generated* from it (`almon model gen`). Editing the model and regenerating changes
all downstream artifacts together, so they cannot drift apart.

The constraint split mirrors the cost of the check:

- **Structural** validation (required fields, the DAL vocabulary, cardinalities)
  runs cheaply against the generated Pydantic types when `data/` is loaded.
- **Cross-entity completeness** ("every DAL-A requirement has a passing verifying
  test") is a relational query over the warehouse tables.

## The Graph Query Contract (GQC)

GQC describes the supported graph questions as a small, closed set of **named,
finite capabilities** — not a general query language. Each capability (for example
[`impact.gqc.yaml`](../src/alm_graph/gqc_specs/impact.gqc.yaml)) is a YAML document
that records:

- the **shape** of the question (closure, fixed multi-hop path, anti-join, …);
- the **path** through the model's classes and slots;
- the **engines** that can answer it, each pointing to a renderer entrypoint;
- **fixtures** with expected results.

Crucially, every GQC capability is validated *against the ontology*: its start
class, each path step's source/target/slot, and its result class must all be real
LinkML classes and slots, with slot ranges that match. The contract therefore
cannot reference a noun the model does not define.

One contract, several backends: the same `impact` question is answered by AGE
(openCypher), by recursive SQL, and by rustworkx.

## Regenerable views and cross-engine agreement

Because the graph is rebuilt from the tables on every run, it must be a *faithful*
view. Two mechanisms keep it honest:

1. **Rebuild-on-demand.** The AGE graph is dropped and recreated from the warehouse
   frames; the rustworkx graph is ephemeral; the recursive-SQL engine reads the
   tables directly. None of them stores anything the tables do not.
2. **Cross-engine agreement.** Automated checks assert that the engines produce the
   same `impact` results. If they ever disagree, the graph is no longer a faithful
   projection of the tables — and the test fails.

The proof that the graph is *only* a view: delete the built warehouse, rebuild, and
the answers are identical. Nothing lives only inside a graph engine.

## Postgres: substrate and exposures

Postgres plays two roles. It is the **substrate** (the warehouse node and edge
tables, the source of truth), and it also hosts the regenerable **exposures**
layered over those tables:

- **Apache AGE** provides the openCypher property graph for traversal questions.
- **Full-text search** (`tsvector` / `tsquery`) indexes the human-readable text.
- **pgvector** stores embeddings for semantic similarity search.

Which text is indexed or embedded is itself driven by the ontology: slots annotated
`searchable` / `embeddable` in `alm.yaml` decide what flows into the search
documents.

## Domain note: DAL, not ASIL

The example domain is aerospace, so the controlled vocabulary is **DAL — Design
Assurance Level — A through E** (DO-178C / ARP4754A), where A is most critical
(catastrophic) and E is no-effect. The mechanism is the familiar criticality-level
pattern — it propagates down the architecture composition and requires a qualifying
passing test for critical items — only the vocabulary is domain-specific.

The bundled VM-E1 records are example data only; the dataset-specific notice lives
in the [data README](../data/README.md).

## Extending it

- **Replace the bundled data:** emit the normalized dataset shape in
  [data-contract.md](data-contract.md), then run validation before rebuilding the
  warehouse and graph views.
- **Add or change an entity or relationship:** edit [`alm.yaml`](../src/alm_model/model/alm.yaml),
  run `almon model gen`, and update `data/` to match.
- **Add a new graph question:** author a new `*.gqc.yaml` capability, implement its
  renderer(s), and add fixtures. The GQC validator will hold it to the model.
- **Add a new engine for an existing question:** point a new renderer entrypoint at
  the capability; the cross-engine check keeps it in agreement with the others.
