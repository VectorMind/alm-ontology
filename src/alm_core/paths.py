"""Centralised filesystem paths for the repository."""

from __future__ import annotations

from pathlib import Path

# Repo root = three levels up from this file: src/alm_core/paths.py
REPO_ROOT = Path(__file__).resolve().parents[2]

PKG_ROOT = Path(__file__).resolve().parent
SRC_ROOT = REPO_ROOT / "src"
MODEL_ROOT = SRC_ROOT / "alm_model"
MODEL_FILE = MODEL_ROOT / "model" / "alm.yaml"
GENERATED_DIR = MODEL_ROOT / "generated"
GENERATED_TYPES = GENERATED_DIR / "alm_types.py"
GENERATED_DDL = GENERATED_DIR / "alm_ddl.sql"
GENERATED_DOCS = GENERATED_DIR / "docs"

DATA_DIR = REPO_ROOT / "data"
REQUIREMENTS_DIR = DATA_DIR / "requirements"
ARCHITECTURE_DIR = DATA_DIR / "architecture"
DEFECTS_DIR = DATA_DIR / "defects"

REPORT_DIR = REPO_ROOT / ".report"
