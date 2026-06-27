# Example Data - VM-E1 Sparrow

A fictional single-seat electric light aircraft, used to exercise the ALM ontology
POC. The data is **authored** (LLM-generated, hand-curated for traceability), not
randomly synthesized, and it is committed for reproducibility.

## Folders

- **`requirements/`** - the *binding specification* (the **what**).
  - `requirements.yaml` - requirements with a Design Assurance Level (DAL A-E),
    statement, acceptance criteria, and `refines` decomposition chains.
  - `tests.yaml` - test cases that `verify` a requirement, each carrying an
    outcome (`passed` / `failed` / `not_run`).
- **`architecture/`** - the *technical breakdown* (the **how**), authored **from**
  the requirements (it cannot be derived mechanically from them).
  - `architecture.yaml` - elements, their `composed_of` decomposition, and the
    `satisfies` allocation (which requirements each element is allocated).
  - `components.md` - component diagrams and descriptions (Mermaid).
  - `sequences.md` - interaction and sequence diagrams (Mermaid).
- **`defects/`** - problems that **violate** requirements and manifest in
  **affected** architecture components.
  - `defects.yaml` - defects with `affects` (components) and `violates` (requirements).

## Built Warehouse

Postgres warehouse tables are **regenerated** from these files by `uv run almon build`.
These authored YAML/Markdown files are the inputs of record. For how the warehouse is
projected into graphs, search, and answers, see
[`docs/architecture.md`](../../../docs/architecture.md).

## Deliberately Seeded Findings

So the analyses and report show something, the example intentionally contains:

- **REQ-0306** (DAL A, actuator fail-safe) - verified only by a **failed** test, so it
  is a coverage gap (a DAL-A requirement with no passing test).
- **REQ-0112** (DAL A, BMS over-voltage/over-current protection) - verified only by a
  **not_run** test, so it is a second coverage gap.
- **DEF-0001** - a critical defect on **ARC-CELL**, a depth-3 sub-element, so impact
  analysis from a battery requirement traverses the composition to reach it.
