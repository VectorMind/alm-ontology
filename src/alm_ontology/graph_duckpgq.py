"""Layer 1 (portable graph contract) — the SQL-side graph over the same tables.

This realizes the handover's "graph as a regenerable view" on the SQL side, with two
backends:

* **recursive CTE** (always available) — a genuine, independent traversal engine used
  for the cross-engine agreement check against rustworkx.
* **DuckPGQ `MATCH`** (SQL/PGQ) — the standards-based property-graph contract, wired
  and auto-activated *iff* the community extension loads. DuckPGQ has no build for
  several DuckDB/platform combinations (notably Windows on recent DuckDB), so the
  code degrades to the recursive CTE and reports which backend ran.
"""

from __future__ import annotations

from . import warehouse

PROPERTY_GRAPH_DDL = """
CREATE PROPERTY GRAPH alm
VERTEX TABLES (
    requirements          KEY (id),
    architecture_elements KEY (id),
    defects               KEY (id)
)
EDGE TABLES (
    edge_allocated_to KEY (req, element)
        SOURCE KEY (req) REFERENCES requirements (id)
        DESTINATION KEY (element) REFERENCES architecture_elements (id)
        LABEL allocated_to,
    edge_composed_of KEY (parent, child)
        SOURCE KEY (parent) REFERENCES architecture_elements (id)
        DESTINATION KEY (child) REFERENCES architecture_elements (id)
        LABEL composed_of,
    edge_affects KEY (defect, element)
        SOURCE KEY (defect) REFERENCES defects (id)
        DESTINATION KEY (element) REFERENCES architecture_elements (id)
        LABEL affects
);
"""


def _impact_recursive(con, requirement: str, max_depth: int) -> list[str]:
    """Variable-length impact via a recursive CTE over composed_of."""
    sql = """
    WITH RECURSIVE reach(elem, depth) AS (
        SELECT element, 0 FROM edge_allocated_to WHERE req = ?
        UNION
        SELECT c.child, r.depth + 1
        FROM reach r
        JOIN edge_composed_of c ON c.parent = r.elem
        WHERE r.depth < ?
    )
    SELECT DISTINCT a.defect AS defect
    FROM edge_affects a
    JOIN reach r ON a.element = r.elem
    ORDER BY defect
    """
    rows = con.execute(sql, [requirement, max_depth]).fetchall()
    return [row[0] for row in rows]


def _impact_duckpgq(con, requirement: str, max_depth: int) -> list[str]:
    """Variable-length impact via SQL/PGQ MATCH (DuckPGQ).

    Only called when the extension has loaded. Path: requirement -allocated_to-> e0
    -composed_of*{0,max}-> e <-affects- defect.
    """
    con.execute(PROPERTY_GRAPH_DDL)
    sql = f"""
    SELECT DISTINCT defect FROM GRAPH_TABLE (alm
        MATCH
            (r:requirements WHERE r.id = ?)-[:allocated_to]->(e0:architecture_elements)
            -[:composed_of]->{{0,{int(max_depth)}}}(e:architecture_elements)
            <-[:affects]-(d:defects)
        COLUMNS (d.id AS defect)
    )
    ORDER BY defect
    """
    rows = con.execute(sql, [requirement]).fetchall()
    return [row[0] for row in rows]


def duckpgq_available() -> bool:
    con = warehouse.connect("parquet")
    try:
        return warehouse.try_load_duckpgq(con)
    finally:
        con.close()


def impact(requirement: str, max_depth: int = 6, engine: str = "auto") -> tuple[list[str], str]:
    """Compute impacted defects on the SQL side.

    ``engine``: ``auto`` prefers DuckPGQ then falls back; ``duckpgq`` forces SQL/PGQ
    (raises if unavailable); ``recursive`` forces the recursive CTE. Returns
    (sorted defect ids, backend name).
    """
    con = warehouse.connect("parquet")
    try:
        if engine in ("auto", "duckpgq"):
            if warehouse.try_load_duckpgq(con):
                try:
                    return _impact_duckpgq(con, requirement, max_depth), "duckpgq"
                except Exception as exc:
                    if engine == "duckpgq":
                        raise
                    # fall through to recursive on auto
                    _ = exc
            elif engine == "duckpgq":
                raise RuntimeError(
                    "DuckPGQ extension is not available for this DuckDB/platform. "
                    "Use --engine recursive (or rustworkx)."
                )
        return _impact_recursive(con, requirement, max_depth), "recursive-sql"
    finally:
        con.close()
