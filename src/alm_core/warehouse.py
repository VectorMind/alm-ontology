"""Postgres warehouse built from the authored ``data/`` YAML.

`tables are truth`: the relational tables are the single source every graph/search/
semantic exposure rebuilds from. The AGE graph, recursive SQL, rustworkx graph, FTS,
and pgvector rows are all regenerable views over these tables.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from alm_core import data_io, postgres


@dataclass
class BuildReport:
    tables: dict[str, int]
    postgres_dsn: str
    errors: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors


def build() -> BuildReport:
    """Load + validate ``data/``, then replace the Postgres warehouse tables."""
    raw = data_io.load_raw()
    errors = data_io.validate_structural(raw) + data_io.validate_referential(raw)
    if errors:
        return BuildReport(tables={}, postgres_dsn="", errors=errors)

    frames = data_io.to_frames(raw)
    con = connect()
    try:
        _replace_tables(con, frames)
    finally:
        con.close()
    return BuildReport(
        tables={name: len(df) for name, df in frames.items()},
        postgres_dsn=postgres.label(),
        errors=[],
    )


def connect():
    """Open a Postgres connection to the warehouse substrate."""
    return postgres.connect()


def load_frames_from_db() -> dict[str, pd.DataFrame]:
    """Read all warehouse tables back as DataFrames (used by graph/exposure builders)."""
    con = connect()
    try:
        return {
            name: _read_table(con, name, columns)
            for name, columns in (*data_io.NODE_COLUMNS.items(), *data_io.EDGE_COLUMNS.items())
        }
    finally:
        con.close()


def _replace_tables(con, frames: dict[str, pd.DataFrame]) -> None:
    all_tables = [*data_io.EDGE_COLUMNS, *data_io.NODE_COLUMNS]
    for table in all_tables:
        con.execute(f"DROP TABLE IF EXISTS {table};")

    for table, columns in data_io.NODE_COLUMNS.items():
        col_defs = ", ".join(f"{column} text" for column in columns)
        pk = "PRIMARY KEY (id)" if "id" in columns else ""
        con.execute(f"CREATE TABLE {table} ({col_defs}, {pk});")

    for table, columns in data_io.EDGE_COLUMNS.items():
        col_defs = ", ".join(f"{column} text NOT NULL" for column in columns)
        con.execute(f"CREATE TABLE {table} ({col_defs});")

    for table, df in frames.items():
        _insert_frame(con, table, df)

    _create_indexes(con)


def _insert_frame(con, table: str, df: pd.DataFrame) -> None:
    if df.empty:
        return
    columns = list(df.columns)
    quoted_columns = ", ".join(columns)
    placeholders = ", ".join(["%s"] * len(columns))
    sql = f"INSERT INTO {table} ({quoted_columns}) VALUES ({placeholders});"
    for row in df.itertuples(index=False, name=None):
        con.execute(sql, tuple(_clean_scalar(value) for value in row))


def _read_table(con, table: str, columns: list[str]) -> pd.DataFrame:
    order = ", ".join(columns)
    select = ", ".join(columns)
    rows = con.execute(f"SELECT {select} FROM {table} ORDER BY {order};").fetchall()
    return pd.DataFrame(rows, columns=columns)


def _clean_scalar(value: Any) -> object:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return str(value)


def _create_indexes(con) -> None:
    con.execute("CREATE INDEX idx_test_cases_verifies ON test_cases (verifies);")
    con.execute("CREATE INDEX idx_edge_refines_src ON edge_refines (src);")
    con.execute("CREATE INDEX idx_edge_composed_of_parent ON edge_composed_of (parent);")
    con.execute("CREATE INDEX idx_edge_satisfied_by_req ON edge_satisfied_by (req);")
    con.execute("CREATE INDEX idx_edge_affects_element ON edge_affects (element);")
    con.execute("CREATE INDEX idx_edge_violates_req ON edge_violates (req);")
