"""Postgres recursive-SQL graph renderers over the warehouse tables."""

from __future__ import annotations

from alm_core import queries, warehouse


def _fetchall(sql: str, params: tuple[object, ...] = ()) -> list[tuple]:
    con = warehouse.connect()
    try:
        return con.execute(sql, params).fetchall()
    finally:
        con.close()


def _impact_recursive(requirement: str, max_depth: int) -> list[str]:
    """Variable-length impact via a Postgres recursive CTE over ``composed_of``."""
    sql = """
    WITH RECURSIVE reach(elem, depth) AS (
        SELECT element, 0 FROM edge_satisfied_by WHERE req = %s
        UNION
        SELECT c.child, r.depth + 1
        FROM reach r
        JOIN edge_composed_of c ON c.parent = r.elem
        WHERE r.depth < %s
    )
    SELECT DISTINCT a.defect AS defect
    FROM edge_affects a
    JOIN reach r ON a.element = r.elem
    ORDER BY defect
    """
    rows = _fetchall(sql, (requirement, int(max_depth)))
    return [row[0] for row in rows]


def refines_closure(requirement: str, max_depth: int = 20) -> tuple[list[dict[str, int | str]], str]:
    """Requirement ancestors reached through transitive ``refines`` using recursive SQL."""
    sql = """
    WITH RECURSIVE closure(req, depth) AS (
        SELECT dst, 1 FROM edge_refines WHERE src = %s
        UNION
        SELECT e.dst, c.depth + 1
        FROM closure c
        JOIN edge_refines e ON e.src = c.req
        WHERE c.depth < %s
    )
    SELECT req AS id, MIN(depth) AS depth
    FROM closure
    GROUP BY req
    ORDER BY depth, id
    """
    rows = _fetchall(sql, (requirement, int(max_depth)))
    return [{"id": row[0], "depth": int(row[1])} for row in rows], "recursive-sql"


def propagate_dal() -> tuple[list[dict[str, str | None]], str]:
    """Effective DAL per architecture element using recursive SQL traversal."""
    sql = """
    WITH RECURSIVE reach(element, dal) AS (
        SELECT s.element, r.dal
        FROM edge_satisfied_by s
        JOIN requirements r ON r.id = s.req
        UNION
        SELECT c.child, reach.dal
        FROM reach
        JOIN edge_composed_of c ON c.parent = reach.element
    )
    SELECT a.id, reach.dal
    FROM architecture_elements a
    LEFT JOIN reach ON reach.element = a.id
    ORDER BY a.id
    """
    rows = _fetchall(sql)

    effective: dict[str, str | None] = {}
    for element, dal in rows:
        current = effective.get(element)
        if current is None or queries.dal_severity(dal) > queries.dal_severity(current):
            effective[element] = dal
        else:
            effective.setdefault(element, current)
    rows_out = [{"id": element, "effective_dal": effective[element]} for element in sorted(effective)]
    return rows_out, "recursive-sql"


def impact(requirement: str, max_depth: int = 6, engine: str = "recursive") -> tuple[list[str], str]:
    """Compute impacted defects using native Postgres recursive SQL."""
    if engine not in {"recursive", "auto"}:
        raise ValueError(f"unsupported SQL engine: {engine!r}; use 'recursive'")
    return _impact_recursive(requirement, max_depth), "recursive-sql"


def impact_recursive(requirement: str, max_depth: int = 6) -> tuple[list[str], str]:
    """GQC renderer entrypoint for the recursive SQL impact implementation."""
    return impact(requirement=requirement, max_depth=max_depth, engine="recursive")
