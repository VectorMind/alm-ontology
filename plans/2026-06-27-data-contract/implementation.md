# Data Contract And Dataset Notice Implementation

## Progress

`■■■■ Done`
Dataset notice scoped and data contract documented.

## Changes

- Removed the repo-wide dummy-data disclaimer from the root README.
- Added a root README data-contract section pointing to `docs/data-contract.md` and
  scoped the fictional warning to the bundled `data/` tree.
- Added `docs/data-contract.md` with the normalized dataset layout, record fields,
  relationship edges, identifier rules, validation gates, and adapter boundary.
- Linked the data contract from `docs/README.md` and `docs/architecture.md`.
- Updated `src/alm_model/model/alm.yaml` so the LinkML model describes reusable ALM
  ontology infrastructure rather than a dummy VM-E1 model.
- Regenerated LinkML-derived Pydantic, SQL DDL, and Markdown docs with
  `uv run almon model gen`.
- Removed hardcoded VM-E1 dummy warning text from report rendering; reports now refer
  to the current validated ALM dataset.

## Proof

- `uv run almon model gen` regenerated `src/alm_model/generated/`.
- `rg -n "FULLY AI-GENERATED DUMMY|NOT FOR REAL-WORLD USE" README.md docs pyproject.toml src data -S`
  now returns matches only under `data/`.
- `uv run ruff check README.md docs src\alm_cli src\alm_core src\alm_reports`
  passed.
- `uv run python -m pytest src\tests\test_gqc.py` passed: 7 tests.

## Follow-Up Notes

- Alternate dataset roots should be implemented as a separate CLI/config change.
- Reports are now generic, but a future dataset metadata file would let reports show
  the active dataset name, source, and assurance status without hardcoding the
  bundled VM-E1 example.
