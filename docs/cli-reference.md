# CLI Reference

`almon` is the repository CLI. It is a Typer app exposed by `pyproject.toml` and currently runs
against the active project configured under `[tool.almon] active_project`.

## Command Surface

| CLI | What it does | What it generates or writes | Main dependencies | Docker needed? |
|---|---|---|---|---|
| `almon version` | Prints the package version. | Nothing. | Python package metadata. | No. |
| `almon model gen` | Reads the active project's LinkML model. | `.cache/projects/project-name/generated/alm_types.py`, `alm_ddl.sql`, and `docs/`. | `linkml`, filesystem. | No. |
| `almon validate` | Loads authored YAML, validates structure and references, then checks DAL-A coverage gaps. | Nothing durable. | Generated Pydantic types, `pyyaml`, Postgres for the coverage query. | Yes for the full command. |
| `almon build` | Loads `projects/project-name/data/` into warehouse tables. | Replaces Postgres node tables and `edge_*` tables. | Generated Pydantic types, `pandas`, `psycopg`, Postgres. | Yes. |
| `almon coverage` | Shows requirements at or above a DAL with no passing verifying test. | Nothing durable. | Postgres warehouse tables. | Yes. |
| `almon impact --engine rustworkx` | Builds an in-memory graph from warehouse tables and traces requirement impact. | Nothing durable. | Postgres warehouse, `rustworkx`. | Yes for the warehouse read. |
| `almon impact --engine recursive` | Runs recursive SQL over warehouse edge tables. | Nothing durable. | Postgres warehouse. | Yes. |
| `almon impact --engine age` | Runs Cypher over the Apache AGE graph, rebuilding by default. | AGE graph `alm` inside Postgres. | Postgres with Apache AGE. | Yes. |
| `almon impact --engine all` | Cross-checks rustworkx, recursive SQL, and AGE when AGE is reachable. | AGE graph may be rebuilt. | All graph backends. | Docker is required for AGE; AGE is skipped when unreachable. |
| `almon graph rebuild` | Explicitly rebuilds the persisted AGE graph from warehouse tables. | Drops and recreates AGE graph `alm`. | Postgres with Apache AGE. | Yes. |
| `almon graph run impact` | Runs the GQC-backed AGE impact capability. | AGE graph, unless `--no-rebuild` is used and the graph already exists. | Postgres with Apache AGE. | Yes. |
| `almon graph validate-gqc` | Validates checked-in GQC YAML against the LinkML model and renderer imports. | Nothing durable. | `pyyaml`, importable renderer modules. | No. |
| `almon rebuild-exposures` | Rebuilds the Postgres full-text search exposure from warehouse tables. | `alm_search_documents` table and GIN index. | Postgres full-text search. | Yes today. |
| `almon rebuild-exposures --semantic` | Adds semantic embedding rows for search documents. | `alm_semantic_embeddings`, pgvector index, local model cache under `.cache/models/fastembed/`. | `fastembed`, pgvector, Postgres. | Yes, plus the `embeddings` Python extra. |
| `almon search` | Runs full-text search over rebuilt search documents. | Nothing durable. | `alm_search_documents`. | Yes. |
| `almon similar` | Runs semantic similarity search over rebuilt embeddings. | Nothing durable. | `fastembed`, pgvector rows. | Yes. |
| `almon propagate` | Shows effective DAL propagation through the rustworkx graph view. | Nothing durable. | Postgres warehouse, `rustworkx`. | Yes. |
| `almon report` | Builds Markdown and interactive HTML reports. | `.cache/projects/project-name/report/<date>/*.{md,html}`. | Postgres warehouse, Plotly, rustworkx. | Yes. |
| `almon serve` | Serves generated reports from localhost. | Refreshes `.cache/projects/project-name/report/index.html`. | Python stdlib HTTP server. | No, assuming reports already exist. |

## Generation Rules

The authored inputs of record stay under `projects/project-name/`: the LinkML model, authored data,
GQC specs, and project configuration. Regenerable project outputs live under
`.cache/projects/project-name/` and can be rebuilt from those authored inputs.

Docker becomes necessary when a command needs the live Postgres substrate. The compose service is
intended to provide Postgres, Apache AGE, and pgvector for the warehouse, graph, search, and semantic
exposure commands.
