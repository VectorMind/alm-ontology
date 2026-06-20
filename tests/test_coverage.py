"""Coverage anti-join tests on the VM-E1 example."""

from __future__ import annotations

from alm_ontology import queries


def test_dal_a_gaps_are_the_seeded_ones():
    gaps = queries.coverage_gaps(min_dal="A")
    ids = set(gaps["id"])
    # REQ-0306 (failed-only) and REQ-0112 (not_run) are the deliberate gaps.
    assert ids == {"REQ-0112", "REQ-0306"}


def test_passing_requirement_is_not_a_gap():
    gaps = queries.coverage_gaps(min_dal="A")
    assert "REQ-0111" not in set(gaps["id"])  # has a passing test


def test_lower_threshold_includes_more():
    a_gaps = set(queries.coverage_gaps(min_dal="A")["id"])
    c_gaps = set(queries.coverage_gaps(min_dal="C")["id"])
    assert a_gaps.issubset(c_gaps)
    # REQ-0307 (DAL C, failed-only) shows up once the threshold drops to C.
    assert "REQ-0307" in c_gaps


def test_coverage_summary_totals_match():
    summary = queries.coverage_summary()
    assert (summary["covered"] + summary["uncovered"] == summary["total"]).all()
