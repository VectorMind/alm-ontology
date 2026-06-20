"""Centralised filesystem paths for the POC."""

from __future__ import annotations

from pathlib import Path

# Repo root = three levels up from this file: src/alm_ontology/paths.py
REPO_ROOT = Path(__file__).resolve().parents[2]

PKG_ROOT = Path(__file__).resolve().parent
MODEL_FILE = PKG_ROOT / "model" / "alm.yaml"
GENERATED_DIR = PKG_ROOT / "generated"
GENERATED_TYPES = GENERATED_DIR / "alm_types.py"
GENERATED_DDL = GENERATED_DIR / "alm_ddl.sql"
GENERATED_DOCS = GENERATED_DIR / "docs"

DATA_DIR = REPO_ROOT / "data"
REQUIREMENTS_DIR = DATA_DIR / "requirements"
ARCHITECTURE_DIR = DATA_DIR / "architecture"
DEFECTS_DIR = DATA_DIR / "defects"

WAREHOUSE_DIR = DATA_DIR / "warehouse"
SQLITE_PATH = WAREHOUSE_DIR / "alm.sqlite"
PARQUET_DIR = WAREHOUSE_DIR / "parquet"

REPORT_DIR = REPO_ROOT / ".report"
