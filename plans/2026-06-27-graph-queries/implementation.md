# Implementation - Graph Query Files

## Progress

`###### Done`
Query evidence added; validation proof recorded below.

## Implemented

- Added `projects/vm-e1-sparrow/graph-queries/` as the lower-layer query evidence folder.
- Added `apache-age-open-cypher/impact.cypher` for the current Apache AGE/openCypher `impact`
  renderer.
- Added Postgres SQL reference files for current GQC-backed SQL renderers:
  - `impact_recursive.sql`
  - `refines_closure.sql`
  - `propagate_dal.sql`
  - `coverage_gaps.sql`
  - `defects_per_element.sql`
- Added comments in each query file naming the capability, GQC file, engine, runtime language, and
  renderer module.
- Called out runtime facts that make some files templates rather than standalone executable SQL:
  AGE's `cypher()` wrapper, Python-inlined parameters, DAL-list construction, optional `top`
  handling, and Python reduction for strongest effective DAL.
- Updated project and architecture docs to distinguish:
  - `gqc/` as the supported capability contract;
  - `graph-queries/` as human-readable lower-layer query evidence.

## Proof

- `uv run almon graph validate-gqc` was attempted first, but failed before project execution because
  uv could not access the user-level cache at `C:\Users\wassi\AppData\Local\uv\cache`.
- `.venv\Scripts\almon.exe graph validate-gqc` passed:
  `coverage_gaps`, `defects_per_element`, `impact`, `propagate_dal`, and `refines_closure` all
  validated as `ok`.
- `.venv\Scripts\python.exe -m pytest src\tests\test_gqc.py` passed: 7 tests.
- Pytest emitted one cache warning because it could not write `.pytest_cache`, but no test failed.
