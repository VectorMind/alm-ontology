"""Cross-engine agreement: the SQL-side graph must match the rustworkx view.

This is what makes "the graph is a regenerable view" an enforced property rather
than a slogan: two independent engines computing impact over the same tables agree.
"""

from __future__ import annotations

import pytest

from alm_graph import age as graph_age
from alm_graph import rustworkx as graph_rustworkx
from alm_graph import sql as graph_sql

REQUIREMENTS = ["REQ-0110", "REQ-0300", "REQ-0100", "REQ-0400", "REQ-0200"]


@pytest.fixture(scope="module")
def persisted_age_graph():
    if not graph_age.available():
        pytest.skip("no Apache AGE instance reachable (start docker-compose.yml)")
    graph_age.rebuild_from_warehouse()
    return True


@pytest.mark.parametrize("req", REQUIREMENTS)
def test_rustworkx_matches_recursive_sql(req):
    g = graph_rustworkx.load()
    rx_defects = g.impact(req, max_depth=6).defects
    sql_defects, backend = graph_sql.impact(req, max_depth=6)
    assert backend == "recursive-sql"
    assert rx_defects == sql_defects


@pytest.mark.parametrize("req", REQUIREMENTS)
def test_rustworkx_matches_auto_sql_alias(req):
    """The SQL auto alias remains recursive SQL while there is only one PG SQL backend."""
    g = graph_rustworkx.load()
    rx_defects = g.impact(req, max_depth=6).defects
    sql_defects, _backend = graph_sql.impact(req, max_depth=6, engine="auto")
    assert rx_defects == sql_defects


@pytest.mark.parametrize("req", REQUIREMENTS)
def test_rustworkx_matches_age(req, persisted_age_graph):
    """The AGE/Cypher engine must agree with rustworkx (skipped if no AGE instance is up)."""
    g = graph_rustworkx.load()
    rx_defects = g.impact(req, max_depth=6).defects
    age_defects, backend = graph_age.impact(req, max_depth=6, rebuild_graph=False)
    assert backend == "age"
    assert rx_defects == age_defects


def test_age_reports_availability():
    # Detection path returns a bool whether or not AGE is running.
    assert isinstance(graph_age.available(), bool)
