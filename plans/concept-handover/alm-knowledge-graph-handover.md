# Adding a Knowledge-Graph / Ontology Layer to the ALM Warehouse
### Design handover — rationale, options explored, and where it landed

> **How to read this.** This is a design-rationale document, not a spec. It captures *why* we ended up where we did, including the ideas we tried and discarded, so that anyone picking this up — the process-definition group in particular — can understand the reasoning rather than just inherit a conclusion. It is deliberately concept-only; no code. A separate runnable skeleton can follow once the direction is agreed.

---

## 1. What system this is about, and what is out of scope

The system is a **read-only analytics warehouse** over automotive software-lifecycle data — requirements, architecture, tests, defects — fetched out of Codebeamer and unified under a custom YAML-driven schema. The data is exposed over SQLite, Parquet, Typesense (semantic search over requirements and architecture), and LanceDB (disk vector store for defects), all wrapped behind an MCP server.

Three boundaries framed every decision:

- **Analytics only, not editing.** We fetch, transform, and analyse. We never write back into source tools. This is why a warehouse/ETL posture is the right shape and why we explicitly rejected OSLC (more on that below).
- **Codebeamer is not in scope.** It is upstream. Data leaves it and becomes our unified schema; nothing here tries to manage or re-integrate it.
- **The data is small and replicable.** Requirements and architecture fit comfortably on a single server, often in memory. Defects are larger and stay on disk. Copying data between representations (SQLite, Parquet, etc.) is acceptable and is treated as an *option*, not a constraint.

---

## 2. The conceptual distinction that started it: ontology vs knowledge graph

The opening question was deceptively simple: how does an ontology differ from a knowledge graph, and what does the ontology *technically* add?

The short version we settled on:

- A **knowledge graph is the data** — the instances and the links between them (this requirement is verified by that test; that test covers this component). In Semantic-Web terms, the assertions, the "A-Box."
- An **ontology is the formal model of meaning above the data** — the classes, the permitted relationships, the cardinalities, the hierarchies, and the logical rules. The "T-Box." Crucially, it carries *machine-interpretable logic* (inverses, transitivity, disjointness, classification rules), not just structure.

A database schema or a UML diagram is "a schema," but an ontology goes further: it is the thing a machine can *reason over*. The honest nuance we kept returning to is that **the real axis is not "graph vs ontology" but how much formal semantics you choose to layer on.** Many production "knowledge graphs" already embed an ontology; the question is dosage.

In our specific lifecycle context, the ontology earns its keep in four ways:

1. **Automated inference** — derive both directions of a relationship for free, trace requirement lineage across many hops, classify items by rule rather than by manual tagging.
2. **Consistency and compliance checking** — flag ASIL-critical requirements with no qualifying test, orphan requirements, defects pointing at non-existent components, tests that are simultaneously passed and failed. This is the literal shape of safety-case evidence.
3. **Semantic interoperability** — make "the same thing" mean the same thing across tools that each have their own data model.
4. **Semantically-typed impact analysis** — a raw graph tells you two things are *connected*; the ontology tells you *how* (satisfies vs. allocated-to vs. verifies) and lets rules propagate along the right edges.

---

## 3. The problem we are *actually* solving

Beneath the abstract question was a concrete pain that became the north star of the whole design:

**The process-definition group formalizes relations, constraints, and process on Confluence — in prose. Prose is not executable, so it drifts from the implementation the moment it is written.**

This reframed everything. The single highest-value outcome of introducing a "real" ontology here is not exotic reasoning — it is **collapsing the formal process model and the data-validation artifact into one thing**. The constraints the process group writes should *be* the constraints that validate the warehouse, under version control, reviewable, and regenerating their own documentation. Closing that prose-to-execution gap is the prize.

---

## 4. The critical reframe of the first instinct

The initial direction under consideration was a **self-referencing SQL table with recursive relation-fetching, plus a "layer on top."** That instinct is not wrong, but it quietly fuses two separable concerns, and that fusion is where these projects rot:

- **Storing and traversing edges** — a recursive table does this fine at our scale.
- **Modeling meaning, then validating and inferring over it** — this is the actual ontology, and SQL is a poor host for it.

Recursive queries give you **reachability, not semantics.** They can tell you what REQ-123 is connected to; they cannot natively express "ASIL propagates down a decomposition," "verifies is the inverse of is-verified-by," "refines is transitive," or "an ASIL-critical requirement with no passing test is non-conformant." Each of those becomes a bespoke, hand-maintained query, and you end up reimplementing a reasoner and a constraint engine, spread across query files.

The sharper realization: **the "layer on top" *is* the ontology.** The only real question is whether it is an ad-hoc pile of SQL and Python rules, or a declarative, versioned, executable model. So the guiding move became: **separate the model from the engine.** Keep recursive traversal as a possible mechanism if useful, but never let it *become* the model.

---

## 5. The hard lesson that redirected the engine choice

Early on, the attractive candidates for an embedded graph engine were Kuzu and Cozo — small, fast, local-first, no servers. Checking their current health turned up a decisive surprise:

- **Kuzu was archived and abandoned in October 2025.** Its sponsor moved on; the community was left to fork or migrate; and notably its on-disk format had never stabilized, forcing export/re-import on every release.
- **Cozo is effectively inactive** — no new releases for over a year, flagged as discontinued.

This was not a detour; it became a load-bearing lesson. **It is the empirical proof of "formats over engines."** Betting the critical path on a niche graph engine is exactly the risk that materialized here. The conclusion: keep the substrate boring and durable (SQLite as a universal format, a mainstream columnar engine for muscle), and make the graph/ontology a **swappable layer** so that the next engine that dies costs nothing.

This is also why the design treats the graph as a *view*, not a store. If the graph is always regenerable from the tables, no engine can hold your data hostage.

---

## 6. The design principles we converged on

These are the invariants the architecture is built to honor:

- **Formats over engines.** Durable, widely-readable standards (SQLite files, Parquet, LinkML YAML) outlive any particular runtime. Engines are replaceable; formats are the contract.
- **Model once, generate many.** A single declarative model is the source of truth, and everything downstream — table definitions, validators, documentation — is generated from it.
- **Tables are truth; the graph is a regenerable view; the model is the schema.** This sentence is the whole survival strategy in one line.
- **Separate recall from precision.** Fuzzy retrieval (vector search) and exact verification (ontology queries) are different jobs and should not be fused into one engine.
- **The LLM proposes; the ontology disposes.** Language models navigate and hypothesize; the deterministic query result is the evidence. The two never blur.
- **Fixed contract, swappable binding.** The query interface stays constant; only the storage it points at changes between the local case and the rare cloud case.
- **Read-only analytics posture.** Because we only analyse, we avoid the heavy machinery (and the auth/modal bloat) that bidirectional editing standards impose.

---

## 7. The option space we surveyed

We laid the realistic options on a single axis: **how much you move the data versus how much formal semantics you gain.**

- **Virtual knowledge graph / "query in place" (OBDA).** Map the existing relational tables to an ontology and let queries rewrite down to SQL on the fly; the database stays the source of truth, nothing is copied. Strong on "don't move the data," but the canonical engines are heavier (JVM) infrastructure than our embedded stack, and they naturally only cover the SQL-accessible side.
- **Materialized semantic store (full RDF + ontology + shape constraints).** Transform artifacts into triples and run a reasoner plus shape validation. Maximal semantics and standardized interchange, at the cost of a parallel store to keep in sync and a heavier mental model. Most justified when formal compliance evidence and standardized toolchain interop become first-class deliverables.
- **Embedded property graph beside the existing stack.** The most operationally aligned idea — until the two leading candidates turned out to be dead/dying (Section 5). The category is right; the specific products were a trap.
- **The orthogonal spine: a model-once schema language.** Independent of the above, a YAML-based schema/ontology language can act as the single source of truth that *generates* the artifacts each option needs. This turned out to be the connective tissue of the final design rather than a competing option.

Filtered through the constraints — prefer Python and Rust-backed-Python over Java behemoths, prefer in-memory with clean escape hatches, copying small data is fine, no editing, no OSLC — the center of gravity moved firmly toward **a durable columnar core plus a regenerable graph layer, with the model as the spine.**

---

## 8. Where it landed: a three-layer architecture

The design separates *what things mean* from *how they are queried* from *which tool runs the query*. Three layers, all over the same tables.

### Layer 0 — The model (the ontology/schema spine)

A single declarative, YAML-based model is the source of truth. It defines the entity types, the permitted relationships, the controlled vocabularies (for example, the ASIL levels), and the structural constraints. From this one artifact we generate the table definitions, runtime validators, and documentation.

This layer is what directly solves the Confluence-drift problem from Section 3: **the process group edits the model, and continuous integration regenerates both the human-readable documentation and the executable validators.** The formalized process and the thing checking the data become the same versioned artifact. It fits naturally because the warehouse is already YAML-driven.

### Layer 1 — The portable graph contract

A vendor-neutral, standards-based property-graph query layer is declared *as a view over the tables produced by Layer 0*. No second store; the graph reflects the tables and is always regenerable. This is where traceability and path questions are expressed in a portable way — "from this requirement, through its allocation, down any depth of architecture decomposition, to the defects that touch those elements." Because it is a standard contract, it survives whichever engine actually executes it.

### Layer 2 — Tooling instantiations

The portable contract is then realized by whichever tool fits the moment:

- **The analytical core** — a mainstream embedded columnar engine that reads the tables (and Parquet) directly, with predicate/projection pushdown, in memory by default and spilling to disk when needed. It is also the **cloud escape hatch**: the same graph definition and the same queries run unchanged whether the rows came from a local SQLite file, a Parquet file, or a cloud table store. The storage binding swaps; the contract does not.
- **The in-memory traversal/inference pass** — a fast, Rust-backed in-memory graph library used when traversal and rule-based inference want to be expressed as explicit, testable code. The graph here is *ephemeral*, rebuilt from the tables each run, which matches the "small enough to hold in memory" reality of requirements and architecture while defects stay on disk.
- **The standards port** — an embeddable RDF/SPARQL option, held in reserve for the specific slice (if any) that ever needs W3C-standard interchange. It is a port, not the core.

---

## 9. Design insights worth preserving

These are the non-obvious realizations that should not be lost in translation:

- **The constraint split.** Not all constraints belong in the same place. *Structural* rules — required fields, valid vocabulary values, cardinalities — are validated cheaply at ingest, in plain Python, with no RDF involved. *Cross-entity completeness* rules — "every ASIL-critical requirement has a passing verifying test" — belong in the query layer, expressed as anti-joins or closures. Trying to force everything into one mechanism is a mistake; the split is intentional and keeps the common path lightweight.

- **"An edge that carries a property" is a recurring shape, and it instantiates differently everywhere.** A verification relationship that carries an outcome (passed/failed) shows up as an association concept in the model, as an edge property in the property-graph layer, as an edge payload in the in-memory library, and — awkwardly — as a *reified intermediate node* in RDF, because RDF edges cannot natively carry properties. That RDF "reification tax" is a concrete reason the property-graph model fits this lifecycle domain more naturally than RDF, and a reason RDF stays a port rather than the core.

- **Completeness is an anti-join, not a graph pattern.** Graph pattern-matching tells you what *exists* (which requirements *are* covered). The interesting compliance question is what is *missing* (which are *not* covered), and absence is naturally a relational anti-join wrapped around the positive pattern. Knowing which half of the problem each tool is good at avoids a lot of wasted effort.

- **Inference-as-tested-code can beat an opaque reasoner for evidence.** The example that crystallized this was ASIL propagation — computing an effective ASIL by propagating the strongest level down the architecture composition. Implemented as an explicit, unit-tested function, every propagation step is auditable, which is more defensible in a safety review than a black-box classifier. (Caveat in Section 12.)

- **The Parquet champion is the columnar engine, not the graph engine.** A recurring worry was reading Parquet without either loading it fully into memory or scanning it slowly. The answer is that lazy scanning with predicate and projection pushdown is precisely what a columnar analytical engine does — whereas graph engines tend to *copy/ingest* Parquet into their own store. So the core that faces Parquet should be the columnar engine, and any graph sits as a view above it.

---

## 10. Cross-cutting decisions on the open questions

Several questions cut across all layers; here is where they settled.

- **Should the vector store mix with the ontology query engine? No — keep them separate, and pipeline them.** Vectors are about *recall* (fuzzy "find me candidates"); the ontology is about *precision* ("is this trace valid, is this compliant"). The right pattern is two-phase: vector search retrieves candidate identifiers, and the graph then validates and filters them. The graph references their IDs but never stores embeddings. This also means the existing Typesense (requirements/architecture) and LanceDB (defects) stores stay exactly where they are and keep doing what they are good at. Fusing imprecise recall with precise verification in one store muddies both — which, incidentally, is another reason the now-defunct "do everything in one engine" option was a poor fit even when it was alive.

- **How does a precise ontology mix with imprecise LLMs/agents? Through a strict evidence boundary.** The model proposes, navigates, and translates natural language into queries; it is never itself the evidence. The evidence is the deterministic query result. The MCP server is exactly that seam: an agent calls a tool, the tool runs a precise query, and the returned rows are what gets cited in an investigation or a safety case. The model narrates around them but cannot fabricate the trace. The two epistemologies coexist cleanly *because* of that boundary.

- **What MCP/CLI surface, and how does it scale? A fixed verb contract with a swappable binding.** The tools are verbs — validate, trace, impact, coverage. The contract never changes. Locally they bind to an in-memory engine over SQLite; for the rare cloud case the same verbs bind to the same engine reading cloud Parquet/table storage underneath. The escape hatch lives at the storage binding, not at the API — so the common single-server path stays lean and the corner case scales without touching the interface or the agent.

- **Why not OSLC? Because we only analyse.** OSLC's value is bidirectional linking and editing across live tools, and it brings auth and modal-integration weight with it. For a read-only analytics warehouse, that is cost without benefit. Fetching, transforming, and analysing into a unified schema is the better-shaped posture for what we actually do.

---

## 11. The concrete domain slice we worked through (conceptually)

To make the layers tangible, we worked a small but representative slice of the lifecycle.

**Entities:** requirements (each with an ASIL level), architecture elements, test cases, and defects.

**Relationships:**
- a requirement *refines* another requirement (decomposition — a transitive chain);
- a requirement is *allocated to* an architecture element;
- an architecture element is *composed of* sub-elements (also transitive);
- a test case *verifies* a requirement, and that relationship *carries an outcome* (passed/failed/not-run);
- a defect *affects* an architecture element.

**The canonical questions this slice answers:**
- **ASIL coverage gap** — which ASIL-A requirements have no passing verifying test. (Positive pattern from the graph; the gap itself from a relational anti-join.)
- **Traceability / impact** — from an ASIL-A requirement, through its allocation, down any depth of architecture composition, to the defects that touch those elements. (A variable-length path — the thing recursive queries make painful and the graph layer makes natural.)
- **ASIL propagation** — the inferred effective ASIL of each architecture element, obtained by propagating the strongest contributing level down the composition. (The "reasoner as auditable code" example.)

Each of these collapses into a single MCP verb whose contract is stable and whose engine behind it is interchangeable.

---

## 12. Open items, caveats, and possible next steps

- **The portable graph layer's leading implementation is a maturing community extension.** Treat the property graph strictly as a regenerable view, never as a store of record, and pin/verify the version — its surface for advanced path queries is still evolving. This is consistent with the "tables are truth" discipline regardless.
- **The ASIL-propagation rule is currently conservative.** It propagates the strongest level monotonically down composition. Real ISO 26262 ASIL *decomposition and tailoring* permits lowering ASIL across redundant elements. The current rule is a safe default, not a certifiable one, and must be refined with the functional-safety stakeholders before it is used as anything more than analysis.
- **Decide whether the RDF/SPARQL port is ever actually needed.** It is held in reserve for standardized interchange. If no such need materializes, it can stay unbuilt.
- **The in-memory graph is ephemeral by design.** That is the right choice for the small requirements/architecture core; defects remain on disk and are joined in only when a query reaches them. Revisit only if data volumes change character.
- **Natural next step:** a runnable skeleton — the model file, a loader that pulls the tables out of the warehouse, the verified in-memory inference functions, and tests that assert the coverage gap and the propagation result — so the three layers can be exercised end to end.

---

## 13. One-paragraph summary for someone in a hurry

We are adding a semantic layer to a read-only ALM analytics warehouse. The point is not exotic reasoning; it is making the process group's formalized constraints *executable* so they stop drifting from the data. We deliberately separate the model (a single YAML source of truth that generates tables, validators, and docs) from the query contract (a portable, standards-based property graph expressed as a regenerable *view* over those tables) from the tooling that runs it (a durable columnar engine as the core and cloud escape hatch, a fast in-memory library for auditable inference, and an RDF port held in reserve). The discipline that makes it durable — proven by two graph engines dying mid-evaluation — is one sentence: **tables are truth, the graph is a regenerable view, and the model is the schema.** Vector search and the ontology stay separate and pipelined; the LLM proposes while the ontology disposes; and the query interface keeps a fixed contract while its storage binding swaps between local and cloud.
