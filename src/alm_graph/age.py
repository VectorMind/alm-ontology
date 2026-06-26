"""Layer 1 (portable graph contract) — the Apache AGE / openCypher backend.

Phase 1 of the AGE migration (see plans/2026-06-26-age-gqc/): a third, independent graph engine
alongside the recursive CTE and rustworkx, computing ``impact`` via Cypher over a property graph
rebuilt from the warehouse tables on every call.

`tables are truth, the graph is a regenerable view`: the ``alm`` AGE graph is dropped and
recreated from the Parquet warehouse frames each run — nothing is stored here. The Cypher result
is asserted equal to the recursive-SQL and rustworkx engines (cross-engine agreement).

AGE ergonomics handled here (see the plan's risks and implementation log): every Cypher query is wrapped in
``cypher('alm', $$ … $$)`` with an explicit ``AS (col agtype)`` column list, and agtype scalars come
back JSON-quoted.
"""

from __future__ import annotations

import json
import os

import pandas as pd

from alm_core import data_io, warehouse

GRAPH_NAME = "alm"

# Node table -> AGE vertex label (the model's class names).
NODE_LABELS: dict[str, str] = {
    "requirements": "Requirement",
    "architecture_elements": "ArchitectureElement",
    "test_cases": "TestCase",
    "defects": "Defect",
}

# Edge table -> (source label, destination label, edge label).
# The two EDGE_COLUMNS are (source_id, destination_id) in that order.
EDGE_SPECS: dict[str, tuple[str, str, str]] = {
    "edge_refines": ("Requirement", "Requirement", "refines"),
    "edge_composed_of": ("ArchitectureElement", "ArchitectureElement", "composed_of"),
    "edge_satisfied_by": ("Requirement", "ArchitectureElement", "satisfied_by"),
    "edge_affects": ("Defect", "ArchitectureElement", "affects"),
    "edge_violates": ("Defect", "Requirement", "violates"),
}

# Long free-text slots are skipped as vertex properties for increment 1: they are not needed for
# traversal and keep the loader robust against quoting. Richer properties land in a later increment.
SKIP_PROPS: frozenset[str] = frozenset({"statement", "acceptance", "rationale", "description"})


# --- connection ----------------------------------------------------------
def _conn_params() -> dict[str, object]:
    """Postgres connection params (env-overridable; defaults match docker-compose.yml)."""
    return {
        "host": os.environ.get("ALM_PG_HOST", "localhost"),
        "port": int(os.environ.get("ALM_PG_PORT", "5432")),
        "user": os.environ.get("ALM_PG_USER", "postgres"),
        "password": os.environ.get("ALM_PG_PASSWORD", "postgres"),
        "dbname": os.environ.get("ALM_PG_DB", "alm"),
    }


def connect():
    """Open an AGE-ready psycopg connection (autocommit; extension loaded, search_path set)."""
    import psycopg

    con = psycopg.connect(**_conn_params(), autocommit=True, connect_timeout=5)
    con.execute("CREATE EXTENSION IF NOT EXISTS age;")
    con.execute("LOAD 'age';")
    con.execute('SET search_path = ag_catalog, "$user", public;')
    return con


def available() -> bool:
    """True iff a Postgres+AGE instance is reachable. Callers skip/fall back when False."""
    try:
        con = connect()
        con.close()
        return True
    except Exception:
        return False


def rebuild_on_query_default() -> bool:
    """Whether query helpers rebuild the AGE graph before each query.

    Defaults to true to preserve Phase 1 behavior. Set ``ALM_AGE_REBUILD_ON_QUERY=0`` once a caller
    wants to manage graph persistence explicitly via ``almon graph rebuild``.
    """
    value = os.environ.get("ALM_AGE_REBUILD_ON_QUERY", "1").strip().lower()
    return value not in {"0", "false", "no", "off"}


# --- Cypher helpers ------------------------------------------------------
def _lit(value: object) -> str:
    """Render a scalar as a Cypher literal (JSON-quoted strings handle escaping)."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    return json.dumps(str(value))


def _cypher_map(row: dict[str, object]) -> str:
    """A Cypher property map ``{k: v, …}`` from a row dict, skipping nulls/long text."""
    parts = [
        f"{key}: {_lit(val)}"
        for key, val in row.items()
        if key not in SKIP_PROPS and not (val is None or (isinstance(val, float) and pd.isna(val)))
    ]
    return "{" + ", ".join(parts) + "}"


def _run(con, cypher: str, columns: str = "v agtype"):
    """Execute a Cypher query through AGE's ``cypher()`` wrapper; return the cursor."""
    return con.execute(f"SELECT * FROM cypher('{GRAPH_NAME}', $cy${cypher}$cy$) AS ({columns});")


def _parse_agtype(value: object) -> object:
    """Unwrap an agtype scalar (returned JSON-quoted, e.g. '\"DEF-0002\"')."""
    if value is None:
        return None
    text = value if isinstance(value, str) else str(value)
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return text.strip('"')


# --- build ---------------------------------------------------------------
def rebuild(con, frames: dict[str, pd.DataFrame]) -> None:
    """Drop and recreate the ``alm`` graph from the warehouse frames (the regenerable view)."""
    try:
        con.execute(f"SELECT drop_graph('{GRAPH_NAME}', true);")
    except Exception:
        pass  # graph did not exist yet
    con.execute(f"SELECT create_graph('{GRAPH_NAME}');")

    for label in NODE_LABELS.values():
        con.execute(f"SELECT create_vlabel('{GRAPH_NAME}', '{label}');")
    for _src, _dst, label in EDGE_SPECS.values():
        con.execute(f"SELECT create_elabel('{GRAPH_NAME}', '{label}');")

    # Vertices.
    for table, label in NODE_LABELS.items():
        for row in frames[table].to_dict(orient="records"):
            _run(con, f"CREATE (:{label} {_cypher_map(row)})")

    # Edges (match endpoints by id, then create the typed relationship).
    for table, (src_label, dst_label, edge_label) in EDGE_SPECS.items():
        src_col, dst_col = data_io.EDGE_COLUMNS[table]
        for row in frames[table].to_dict(orient="records"):
            src, dst = row[src_col], row[dst_col]
            _run(
                con,
                f"MATCH (a:{src_label} {{id: {_lit(src)}}}), (b:{dst_label} {{id: {_lit(dst)}}}) "
                f"CREATE (a)-[:{edge_label}]->(b)",
            )


def rebuild_from_warehouse() -> dict[str, int]:
    """Rebuild and persist the ``alm`` AGE graph from the current warehouse tables."""
    frames = warehouse.load_frames_from_db()
    con = connect()
    try:
        rebuild(con, frames)
    finally:
        con.close()
    return {name: len(df) for name, df in frames.items()}


def graph_exists(con) -> bool:
    """True when the named AGE graph exists in Postgres."""
    row = con.execute("SELECT EXISTS (SELECT 1 FROM ag_graph WHERE name = %s);", (GRAPH_NAME,)).fetchone()
    return bool(row and row[0])


# --- query ---------------------------------------------------------------
def _query_impact(con, requirement: str, max_depth: int) -> list[str]:
    """Impacted defects via Cypher: requirement -satisfied_by-> e0 -composed_of*0..max-> e
    <-affects- defect."""
    cypher = (
        f"MATCH (r:Requirement {{id: {_lit(requirement)}}})"
        f"-[:satisfied_by]->(e0:ArchitectureElement) "
        f"MATCH (e0)-[:composed_of*0..{int(max_depth)}]->(e:ArchitectureElement) "
        f"MATCH (d:Defect)-[:affects]->(e) "
        f"RETURN DISTINCT d.id"
    )
    cur = _run(con, cypher, columns="defect agtype")
    return sorted({_parse_agtype(r[0]) for r in cur.fetchall()})


def impact(
    requirement: str,
    max_depth: int = 6,
    *,
    rebuild_graph: bool | None = None,
) -> tuple[list[str], str]:
    """Compute impacted defects on the AGE/Cypher side. Returns (sorted defect ids, backend name).

    By default, rebuilds the ``alm`` graph from the current warehouse on each call (small data; keeps
    the graph a faithful regenerable view). Callers can pass ``rebuild_graph=False`` or set
    ``ALM_AGE_REBUILD_ON_QUERY=0`` after explicitly running ``almon graph rebuild``.
    """
    con = connect()
    try:
        should_rebuild = rebuild_on_query_default() if rebuild_graph is None else rebuild_graph
        if should_rebuild or not graph_exists(con):
            rebuild(con, warehouse.load_frames_from_db())
        return _query_impact(con, requirement, max_depth), "age"
    finally:
        con.close()
