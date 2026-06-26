"""Load the authored ``data/`` YAML, validate it, and shape it into tables.

The committed YAML under ``data/{requirements,architecture,defects}/`` is the input
of record. This module merges the files, validates them structurally against the
LinkML-generated Pydantic types, checks referential integrity, and flattens the
embedded relationships into predictable node/edge tables for the warehouse.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd
import yaml

from . import paths

# Node tables: column order is fixed and predictable (the graph layers depend on it).
NODE_COLUMNS: dict[str, list[str]] = {
    "requirements": ["id", "title", "statement", "acceptance", "rationale", "dal"],
    "architecture_elements": ["id", "name", "kind", "description"],
    "test_cases": ["id", "title", "description", "verifies", "outcome"],
    "defects": ["id", "title", "description", "severity", "status"],
}

EDGE_COLUMNS: dict[str, list[str]] = {
    "edge_refines": ["src", "dst"],          # requirement refines requirement
    "edge_composed_of": ["parent", "child"],  # element composed_of element
    "edge_satisfied_by": ["req", "element"],  # requirement satisfied_by element
    "edge_affects": ["defect", "element"],    # defect affects element
    "edge_violates": ["defect", "req"],       # defect violates requirement
}


@dataclass
class LoadResult:
    raw: dict[str, list[dict]]
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def _read_yaml(path) -> dict:
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def load_raw() -> dict[str, list[dict]]:
    """Merge the authored YAML files into one record-set keyed by collection."""
    merged: dict[str, list[dict]] = {
        "requirements": [],
        "architecture_elements": [],
        "test_cases": [],
        "defects": [],
    }
    sources = [
        paths.REQUIREMENTS_DIR / "requirements.yaml",
        paths.REQUIREMENTS_DIR / "tests.yaml",
        paths.ARCHITECTURE_DIR / "architecture.yaml",
        paths.DEFECTS_DIR / "defects.yaml",
    ]
    for src in sources:
        doc = _read_yaml(src)
        for key in merged:
            if key in doc and doc[key]:
                merged[key].extend(doc[key])
    return merged


def validate_structural(raw: dict[str, list[dict]]) -> list[str]:
    """Validate records against the generated Pydantic types. Returns error strings."""
    from .generated.alm_types import Dataset

    errors: list[str] = []
    try:
        Dataset(**raw)
    except Exception as exc:  # pydantic.ValidationError, surfaced verbatim
        errors.append(f"structural validation failed:\n{exc}")
    return errors


def validate_referential(raw: dict[str, list[dict]]) -> list[str]:
    """Check that every referenced id exists."""
    errors: list[str] = []
    req_ids = {r["id"] for r in raw["requirements"]}
    elem_ids = {e["id"] for e in raw["architecture_elements"]}

    def check(ref: str, universe: set[str], where: str) -> None:
        if ref not in universe:
            errors.append(f"{where}: unknown reference '{ref}'")

    for r in raw["requirements"]:
        for parent in r.get("refines", []) or []:
            check(parent, req_ids, f"Requirement {r['id']} refines")
    for e in raw["architecture_elements"]:
        for child in e.get("composed_of", []) or []:
            check(child, elem_ids, f"Element {e['id']} composed_of")
        for req in e.get("satisfies", []) or []:
            check(req, req_ids, f"Element {e['id']} satisfies")
    for t in raw["test_cases"]:
        if t.get("verifies"):
            check(t["verifies"], req_ids, f"TestCase {t['id']} verifies")
    for d in raw["defects"]:
        for el in d.get("affects", []) or []:
            check(el, elem_ids, f"Defect {d['id']} affects")
        for req in d.get("violates", []) or []:
            check(req, req_ids, f"Defect {d['id']} violates")
    return errors


def to_frames(raw: dict[str, list[dict]]) -> dict[str, pd.DataFrame]:
    """Flatten records + embedded relationships into node and edge DataFrames."""
    frames: dict[str, pd.DataFrame] = {}

    # Node tables (scalar columns only).
    for table, cols in NODE_COLUMNS.items():
        rows = [{c: rec.get(c) for c in cols} for rec in raw[table]]
        frames[table] = pd.DataFrame(rows, columns=cols)

    # Edge tables (derived from embedded multivalued slots).
    refines = [(r["id"], p) for r in raw["requirements"] for p in (r.get("refines") or [])]
    composed = [
        (e["id"], c) for e in raw["architecture_elements"] for c in (e.get("composed_of") or [])
    ]
    satisfied_by = [
        (req, e["id"]) for e in raw["architecture_elements"] for req in (e.get("satisfies") or [])
    ]
    affects = [(d["id"], el) for d in raw["defects"] for el in (d.get("affects") or [])]
    violates = [(d["id"], req) for d in raw["defects"] for req in (d.get("violates") or [])]

    frames["edge_refines"] = pd.DataFrame(refines, columns=EDGE_COLUMNS["edge_refines"])
    frames["edge_composed_of"] = pd.DataFrame(composed, columns=EDGE_COLUMNS["edge_composed_of"])
    frames["edge_satisfied_by"] = pd.DataFrame(
        satisfied_by, columns=EDGE_COLUMNS["edge_satisfied_by"]
    )
    frames["edge_affects"] = pd.DataFrame(affects, columns=EDGE_COLUMNS["edge_affects"])
    frames["edge_violates"] = pd.DataFrame(violates, columns=EDGE_COLUMNS["edge_violates"])
    return frames
