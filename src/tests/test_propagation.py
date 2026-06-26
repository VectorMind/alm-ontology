"""Golden-fixture tests for DAL propagation (auditable inference)."""

from __future__ import annotations

import pandas as pd

from alm_graph.rustworkx import AlmGraph


def _mini_frames() -> dict[str, pd.DataFrame]:
    """A tiny composition: E1 -composed_of-> E2 -composed_of-> E3.

    R1(DAL A) is satisfied by E1; R3(DAL C) is satisfied by E3; D1 affects E3.
    """
    return {
        "requirements": pd.DataFrame(
            [{"id": "R1", "dal": "A"}, {"id": "R3", "dal": "C"}]
        ),
        "architecture_elements": pd.DataFrame(
            [{"id": "E1", "name": "E1"}, {"id": "E2", "name": "E2"}, {"id": "E3", "name": "E3"}]
        ),
        "edge_composed_of": pd.DataFrame(
            [{"parent": "E1", "child": "E2"}, {"parent": "E2", "child": "E3"}]
        ),
        "edge_satisfied_by": pd.DataFrame(
            [{"req": "R1", "element": "E1"}, {"req": "R3", "element": "E3"}]
        ),
        "edge_affects": pd.DataFrame([{"defect": "D1", "element": "E3"}]),
    }


def test_propagation_flows_strongest_dal_downward():
    g = AlmGraph(_mini_frames())
    eff = g.propagate_dal()
    # A allocated at the top propagates monotonically down to every descendant,
    # overriding E3's own (weaker) declared C.
    assert eff == {"E1": "A", "E2": "A", "E3": "A"}


def test_propagation_does_not_flow_upward():
    frames = _mini_frames()
    # Allocate a strong DAL only to the LEAF; it must not raise the parents.
    frames["edge_satisfied_by"] = pd.DataFrame([{"req": "R1", "element": "E3"}])
    g = AlmGraph(frames)
    eff = g.propagate_dal()
    assert eff["E3"] == "A"
    assert eff["E1"] is None
    assert eff["E2"] is None


def test_impact_traverses_composition_to_defects():
    g = AlmGraph(_mini_frames())
    res = g.impact("R1", max_depth=6)
    assert res.elements == ["E1", "E2", "E3"]
    assert res.defects == ["D1"]


def test_impact_respects_max_depth():
    g = AlmGraph(_mini_frames())
    # From E1, depth 1 reaches only E2; E3 (depth 2) and its defect are excluded.
    res = g.impact("R1", max_depth=1)
    assert "E3" not in res.elements
    assert res.defects == []


def test_real_warehouse_airframe_inherits_b():
    """On the VM-E1 example, airframe leaves inherit B (over declared C/D)."""
    from alm_graph import rustworkx as graph_rustworkx

    df = graph_rustworkx.propagate_table().set_index("id")
    assert df.loc["ARC-FUSE", "effective_dal"] == "B"   # declared D
    assert df.loc["ARC-WING", "effective_dal"] == "B"   # declared C
    assert df.loc["ARC-DISP", "effective_dal"] == "C"   # not flooded
