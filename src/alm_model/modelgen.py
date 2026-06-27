"""Layer 0 — generate Pydantic types, SQL DDL, and docs from the LinkML model.

`model once, generate many`: alm.yaml is the single source of truth. This wraps the
LinkML generator Python API (called in-process) and writes outputs into the active
project's generated cache.
"""

from __future__ import annotations

from alm_core import paths


def generate() -> dict[str, str]:
    """Regenerate all downstream artifacts from the LinkML model.

    Returns a mapping of artifact name -> path written.
    """
    from linkml.generators.docgen import DocGenerator
    from linkml.generators.pydanticgen import PydanticGenerator
    from linkml.generators.sqltablegen import SQLTableGenerator

    paths.GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    model = str(paths.MODEL_FILE)
    written: dict[str, str] = {}

    # 1) Pydantic types (used for structural validation at load time).
    pydantic_src = PydanticGenerator(model).serialize()
    paths.GENERATED_TYPES.write_text(pydantic_src, encoding="utf-8")
    written["pydantic"] = str(paths.GENERATED_TYPES)

    # 2) SQL DDL (committed artifact demonstrating the schema; the runtime warehouse
    #    builds its own predictable table layout, see warehouse.py).
    ddl = SQLTableGenerator(model).generate_ddl()
    paths.GENERATED_DDL.write_text(ddl, encoding="utf-8")
    written["ddl"] = str(paths.GENERATED_DDL)

    # 3) Markdown documentation.
    paths.GENERATED_DOCS.mkdir(parents=True, exist_ok=True)
    DocGenerator(model, directory=str(paths.GENERATED_DOCS), mergeimports=False).serialize()
    written["docs"] = str(paths.GENERATED_DOCS)

    return written
