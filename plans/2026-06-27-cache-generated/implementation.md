# Cache Generated Artifacts Implementation

## Progress

`[#####] Done`
Generated artifacts now live under `.cache`; docs and tests are complete.

## Implementation Log

- Added `docs/cli-reference.md` with the current CLI surface, outputs, dependencies, and Docker
  requirements.
- Added this dated packet and marked it open in `plans/open.md`.
- Updated central path resolution so generated LinkML outputs now resolve under
  `.cache/projects/<project>/generated/`.
- Updated report output resolution to `.cache/projects/<project>/report/`.
- Updated the FastEmbed model cache to `.cache/models/fastembed/`, dropping the old
  `.cache/alm-ontology/` segment.
- Updated repository guidance, README, data contract docs, project manifest comments, CLI help, and
  package metadata to remove the old committed `projects/<project>/generated/` assumption.
- Regenerated LinkML artifacts with `uv run almon model gen`; output now lands under
  `.cache/projects/vm-e1-sparrow/generated/`.
- Removed the old tracked `projects/vm-e1-sparrow/generated/` tree after confirming the resolved
  path.

## Proof

- `uv run almon model gen` passed and wrote:
  - `.cache/projects/vm-e1-sparrow/generated/alm_types.py`
  - `.cache/projects/vm-e1-sparrow/generated/alm_ddl.sql`
  - `.cache/projects/vm-e1-sparrow/generated/docs/`
- `uv run almon graph validate-gqc` passed for all five capabilities.
- `uv run ruff check .` passed.
- `uv run almon validate` passed structural and referential validation; it reported the expected
  two DAL-A coverage gaps.
- `uv run almon report --topic coverage` passed and wrote Markdown/HTML under
  `.cache/projects/vm-e1-sparrow/report/2026-06-27/`.
- `uv run pytest` passed: 35 tests.
