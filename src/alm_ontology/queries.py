"""Layer 2 (analytical core) — DuckDB queries, including the completeness anti-join.

`completeness is an anti-join, not a graph pattern`: graph matching tells you what
*is* covered; the compliance question is what is *missing*, which is an anti-join.
"""

from __future__ import annotations

import pandas as pd

from . import warehouse

# DAL severity: A is most critical. Higher number = more critical.
DAL_SEVERITY: dict[str, int] = {"A": 4, "B": 3, "C": 2, "D": 1, "E": 0}
DAL_ORDER = ["A", "B", "C", "D", "E"]


def dal_severity(dal: str | None) -> int:
    return DAL_SEVERITY.get(dal or "", -1)


def coverage_gaps(min_dal: str = "A") -> pd.DataFrame:
    """Requirements at/above ``min_dal`` criticality with no passing verifying test.

    Returns columns: id, title, dal, n_tests, outcomes.
    """
    threshold = DAL_SEVERITY[min_dal]
    critical = [d for d, sev in DAL_SEVERITY.items() if sev >= threshold]
    in_list = ", ".join(f"'{d}'" for d in critical)

    con = warehouse.connect("parquet")
    try:
        sql = f"""
        SELECT
            r.id,
            r.title,
            r.dal,
            COUNT(t.id) AS n_tests,
            COALESCE(STRING_AGG(t.outcome, ', '), '') AS outcomes
        FROM requirements r
        LEFT JOIN test_cases t ON t.verifies = r.id
        WHERE r.dal IN ({in_list})
          AND NOT EXISTS (
              SELECT 1 FROM test_cases tp
              WHERE tp.verifies = r.id AND tp.outcome = 'passed'
          )
        GROUP BY r.id, r.title, r.dal
        ORDER BY r.dal, r.id
        """
        return con.execute(sql).fetch_df()
    finally:
        con.close()


def coverage_gap_ids(min_dal: str = "A") -> tuple[list[str], str]:
    """Renderer-friendly list of coverage-gap requirement ids."""
    return coverage_gaps(min_dal=min_dal)["id"].tolist(), "recursive-sql"


def coverage_summary() -> pd.DataFrame:
    """Per-DAL coverage: total requirements vs those with a passing test."""
    con = warehouse.connect("parquet")
    try:
        sql = """
        SELECT
            r.dal,
            COUNT(*) AS total,
            COUNT(*) FILTER (
                WHERE EXISTS (
                    SELECT 1 FROM test_cases tp
                    WHERE tp.verifies = r.id AND tp.outcome = 'passed'
                )
            ) AS covered
        FROM requirements r
        GROUP BY r.dal
        ORDER BY r.dal
        """
        df = con.execute(sql).fetch_df()
        df["uncovered"] = df["total"] - df["covered"]
        return df
    finally:
        con.close()


def outcome_distribution() -> pd.DataFrame:
    """Test-outcome counts."""
    con = warehouse.connect("parquet")
    try:
        return con.execute(
            "SELECT outcome, COUNT(*) AS n FROM test_cases GROUP BY outcome ORDER BY outcome"
        ).fetch_df()
    finally:
        con.close()


def defects_per_element(top: int | None = None) -> pd.DataFrame:
    """Defect counts per directly-affected architecture element."""
    con = warehouse.connect("parquet")
    try:
        sql = """
        SELECT a.name, a.id, COUNT(e.defect) AS n_defects
        FROM architecture_elements a
        LEFT JOIN edge_affects e ON e.element = a.id
        GROUP BY a.id, a.name
        HAVING COUNT(e.defect) > 0
        ORDER BY n_defects DESC, a.id
        """
        df = con.execute(sql).fetch_df()
        if top:
            df = df.head(top)
        return df
    finally:
        con.close()


def defect_counts_by_element(top: int | None = None) -> tuple[list[dict[str, int | str]], str]:
    """Renderer-friendly defect counts per directly affected architecture element."""
    df = defects_per_element(top=top)
    rows = [
        {"id": row["id"], "name": row["name"], "n_defects": int(row["n_defects"])}
        for _, row in df.iterrows()
    ]
    return rows, "recursive-sql"
