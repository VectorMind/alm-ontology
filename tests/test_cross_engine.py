"""Cross-engine agreement: the SQL-side graph must match the rustworkx view.

This is what makes "the graph is a regenerable view" an enforced property rather
than a slogan: two independent engines computing impact over the same tables agree.
"""

from __future__ import annotations

import pytest

from alm_ontology import graph_duckpgq, graph_rustworkx

REQUIREMENTS = ["REQ-0110", "REQ-0300", "REQ-0100", "REQ-0400", "REQ-0200"]


@pytest.mark.parametrize("req", REQUIREMENTS)
def test_rustworkx_matches_recursive_sql(req):
    g = graph_rustworkx.load()
    rx_defects = g.impact(req, max_depth=6).defects
    sql_defects, backend = graph_duckpgq.impact(req, max_depth=6, engine="recursive")
    assert backend == "recursive-sql"
    assert rx_defects == sql_defects


@pytest.mark.parametrize("req", REQUIREMENTS)
def test_rustworkx_matches_auto_backend(req):
    """Whatever SQL backend `auto` selects (DuckPGQ if present, else recursive)."""
    g = graph_rustworkx.load()
    rx_defects = g.impact(req, max_depth=6).defects
    sql_defects, _backend = graph_duckpgq.impact(req, max_depth=6, engine="auto")
    assert rx_defects == sql_defects


def test_duckpgq_reports_availability():
    # Just exercise the detection path; it returns a bool either way.
    assert isinstance(graph_duckpgq.duckpgq_available(), bool)
