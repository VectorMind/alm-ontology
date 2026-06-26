"""Substrate — build SQLite + Parquet from ``data/`` and open DuckDB sessions.

`tables are truth`: the warehouse is a regenerable build artifact. The node/edge
tables here are the single source the graph engines (rustworkx, recursive SQL,
DuckPGQ) all rebuild from on every run.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

import duckdb
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from alm_core import data_io, paths


@dataclass
class BuildReport:
    tables: dict[str, int]          # table -> row count
    sqlite_path: str
    parquet_dir: str
    errors: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors


def build() -> BuildReport:
    """Load + validate ``data/``, then write SQLite and Parquet."""
    raw = data_io.load_raw()
    errors = data_io.validate_structural(raw) + data_io.validate_referential(raw)
    if errors:
        return BuildReport(tables={}, sqlite_path="", parquet_dir="", errors=errors)

    frames = data_io.to_frames(raw)

    paths.WAREHOUSE_DIR.mkdir(parents=True, exist_ok=True)
    paths.PARQUET_DIR.mkdir(parents=True, exist_ok=True)

    # SQLite (durable, universal interchange).
    if paths.SQLITE_PATH.exists():
        paths.SQLITE_PATH.unlink()
    con = sqlite3.connect(paths.SQLITE_PATH)
    try:
        for name, df in frames.items():
            df.to_sql(name, con, if_exists="replace", index=False)
        con.commit()
    finally:
        con.close()

    # Parquet (analytical, cloud escape hatch).
    counts: dict[str, int] = {}
    for name, df in frames.items():
        table = pa.Table.from_pandas(df, preserve_index=False)
        pq.write_table(table, paths.PARQUET_DIR / f"{name}.parquet")
        counts[name] = len(df)

    return BuildReport(
        tables=counts,
        sqlite_path=str(paths.SQLITE_PATH),
        parquet_dir=str(paths.PARQUET_DIR),
        errors=[],
    )


def connect(source: str = "parquet") -> duckdb.DuckDBPyConnection:
    """Open a DuckDB session with the warehouse tables registered as views.

    ``source`` selects the storage binding (the handover's 'swappable binding'):
    ``parquet`` reads the Parquet files; ``sqlite`` attaches the SQLite file.
    Either way the table names are identical, so queries are storage-agnostic.
    """
    con = duckdb.connect()
    if source == "parquet":
        if not paths.PARQUET_DIR.exists() or not any(paths.PARQUET_DIR.glob("*.parquet")):
            raise FileNotFoundError("No Parquet warehouse found. Run `almon build` first.")
        for pqfile in paths.PARQUET_DIR.glob("*.parquet"):
            con.execute(
                f"CREATE VIEW {pqfile.stem} AS SELECT * FROM read_parquet('{pqfile.as_posix()}')"
            )
    elif source == "sqlite":
        if not paths.SQLITE_PATH.exists():
            raise FileNotFoundError("No SQLite warehouse found. Run `almon build` first.")
        con.execute("INSTALL sqlite; LOAD sqlite;")
        con.execute(f"ATTACH '{paths.SQLITE_PATH.as_posix()}' AS w (TYPE sqlite);")
        for name in (*data_io.NODE_COLUMNS, *data_io.EDGE_COLUMNS):
            con.execute(f"CREATE VIEW {name} AS SELECT * FROM w.{name}")
    else:
        raise ValueError(f"unknown source: {source!r}")
    return con


def load_frames_from_db() -> dict[str, pd.DataFrame]:
    """Read all warehouse tables back as DataFrames (used by the graph builders)."""
    con = connect("parquet")
    try:
        return {
            name: con.execute(f"SELECT * FROM {name}").fetch_df()
            for name in (*data_io.NODE_COLUMNS, *data_io.EDGE_COLUMNS)
        }
    finally:
        con.close()


def try_load_duckpgq(con: duckdb.DuckDBPyConnection) -> bool:
    """Attempt to load the DuckPGQ community extension. Returns True on success.

    DuckPGQ has no build for several DuckDB/platform combinations (notably Windows
    on recent DuckDB), so this is best-effort; callers fall back to recursive SQL.
    """
    try:
        con.execute("INSTALL duckpgq FROM community;")
        con.execute("LOAD duckpgq;")
        return True
    except Exception:
        return False
