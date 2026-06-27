"""Centralised filesystem paths, resolved against the active project.

Project-authored inputs (the LinkML model, dataset, GQC specs, and config) live under
``projects/<name>/``. Project-generated outputs live under
``.cache/projects/<name>/``. The active project is hardcoded in ``pyproject.toml``
under ``[tool.almon] active_project``; if that is absent and exactly one project
exists, it is used by default.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

# Repo root = three levels up from this file: src/alm_core/paths.py
REPO_ROOT = Path(__file__).resolve().parents[2]

PKG_ROOT = Path(__file__).resolve().parent
SRC_ROOT = REPO_ROOT / "src"
PROJECTS_ROOT = REPO_ROOT / "projects"
CACHE_ROOT = REPO_ROOT / ".cache"
CACHE_PROJECTS_ROOT = CACHE_ROOT / "projects"
MODEL_CACHE_DIR = CACHE_ROOT / "models"


def _active_project_name() -> str:
    """Resolve the active project name from the manifest, or the sole project."""
    pyproject = REPO_ROOT / "pyproject.toml"
    if pyproject.exists():
        with pyproject.open("rb") as fh:
            manifest = tomllib.load(fh)
        name = manifest.get("tool", {}).get("almon", {}).get("active_project")
        if name:
            return str(name)
    candidates = (
        sorted(p.name for p in PROJECTS_ROOT.iterdir() if p.is_dir())
        if PROJECTS_ROOT.exists()
        else []
    )
    if len(candidates) == 1:
        return candidates[0]
    raise RuntimeError(
        "No active project configured. Set [tool.almon] active_project in pyproject.toml "
        f"to one of: {candidates}"
    )


ACTIVE_PROJECT = _active_project_name()
PROJECT_ROOT = PROJECTS_ROOT / ACTIVE_PROJECT
CACHE_PROJECT_ROOT = CACHE_PROJECTS_ROOT / ACTIVE_PROJECT

# Model (the ontology, Layer 0) and its generated artifacts.
MODEL_ROOT = PROJECT_ROOT / "model"
MODEL_FILE = MODEL_ROOT / "alm.yaml"
GENERATED_DIR = CACHE_PROJECT_ROOT / "generated"
GENERATED_TYPES = GENERATED_DIR / "alm_types.py"
GENERATED_DDL = GENERATED_DIR / "alm_ddl.sql"
GENERATED_DOCS = GENERATED_DIR / "docs"

# Graph Query Contract capabilities (model-specific).
GQC_DIR = PROJECT_ROOT / "gqc"

# Authored dataset (the substrate inputs of record).
DATA_DIR = PROJECT_ROOT / "data"
REQUIREMENTS_DIR = DATA_DIR / "requirements"
ARCHITECTURE_DIR = DATA_DIR / "architecture"
DEFECTS_DIR = DATA_DIR / "defects"

# Project configuration.
CONFIG_DIR = PROJECT_ROOT / "config"
EMBEDDINGS_FILE = CONFIG_DIR / "embeddings.yaml"

# Generated reports (gitignored, regenerable).
REPORT_DIR = CACHE_PROJECT_ROOT / "report"
