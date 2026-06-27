# Graph Queries

This folder exposes the current lower-layer query forms for the VM-E1 Sparrow project.

It is intentionally separate from `../gqc/`:

- `gqc/` is the supported capability contract: names, parameters, shapes, engine renderers, and
  fixtures.
- `graph-queries/` is human-readable query evidence for the renderers that exist today.

These files do not claim ISO GQL support and they are not a GQC compiler target. They document the
actual runtime families currently used by the project:

| Folder | Runtime / language | Notes |
|---|---|---|
| `apache-age-open-cypher/` | Apache AGE openCypher subset | Query bodies are executed by Postgres through AGE's `cypher()` wrapper. |
| `postgres-sql/` | Postgres SQL | Includes recursive CTE traversal queries plus relational anti-join/aggregation renderers. |

The executable source of record still lives in the Python renderer modules listed in each file
header. If a renderer changes, update the matching reference file in the same packet.

## Current Capability Coverage

| Capability | GQC file | Query evidence |
|---|---|---|
| `impact` | `../gqc/impact.gqc.yaml` | `apache-age-open-cypher/impact.cypher`, `postgres-sql/impact_recursive.sql` |
| `refines_closure` | `../gqc/refines_closure.gqc.yaml` | `postgres-sql/refines_closure.sql` |
| `propagate_dal` | `../gqc/propagate_dal.gqc.yaml` | `postgres-sql/propagate_dal.sql` |
| `coverage_gaps` | `../gqc/coverage_gaps.gqc.yaml` | `postgres-sql/coverage_gaps.sql` |
| `defects_per_element` | `../gqc/defects_per_element.gqc.yaml` | `postgres-sql/defects_per_element.sql` |

