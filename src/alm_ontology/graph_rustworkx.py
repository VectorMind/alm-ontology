"""Layer 2 (in-memory inference) — the regenerable rustworkx graph view.

`inference-as-tested-code can beat an opaque reasoner for evidence`: DAL propagation
and impact traversal are explicit, auditable functions over an ephemeral graph rebuilt
from the tables on every run. Nothing is stored here; the tables are truth.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

import pandas as pd
import rustworkx as rx

from . import queries, warehouse


def _stronger(a: str | None, b: str | None) -> str | None:
    """Return the more critical of two DAL values (A is most critical)."""
    sa, sb = queries.dal_severity(a), queries.dal_severity(b)
    if sa < 0:
        return b
    if sb < 0:
        return a
    return a if sa >= sb else b


@dataclass
class ImpactResult:
    requirement: str
    max_depth: int
    elements: list[str] = field(default_factory=list)  # reachable architecture elements
    defects: list[str] = field(default_factory=list)    # impacted defect ids (sorted)
    edges: list[tuple[str, str, str]] = field(default_factory=list)  # (src, dst, kind)


class AlmGraph:
    """An ephemeral property graph over the warehouse tables."""

    def __init__(self, frames: dict[str, pd.DataFrame]):
        self.frames = frames
        self.req_dal: dict[str, str] = dict(
            zip(frames["requirements"]["id"], frames["requirements"]["dal"])
        )
        self.element_ids: list[str] = frames["architecture_elements"]["id"].tolist()

        # composed_of digraph (parent -> child) for traversal/propagation.
        self._g = rx.PyDiGraph()
        self._idx: dict[str, int] = {e: self._g.add_node(e) for e in self.element_ids}
        for _, row in frames["edge_composed_of"].iterrows():
            self._g.add_edge(self._idx[row["parent"]], self._idx[row["child"]], "composed_of")

        # adjacency lookups
        self._children: dict[str, list[str]] = {e: [] for e in self.element_ids}
        for _, row in frames["edge_composed_of"].iterrows():
            self._children[row["parent"]].append(row["child"])

        self._alloc_req_to_elems: dict[str, list[str]] = {}
        self._alloc_elem_to_reqs: dict[str, list[str]] = {}
        for _, row in frames["edge_allocated_to"].iterrows():
            self._alloc_req_to_elems.setdefault(row["req"], []).append(row["element"])
            self._alloc_elem_to_reqs.setdefault(row["element"], []).append(row["req"])

        self._affects: dict[str, list[str]] = {}
        for _, row in frames["edge_affects"].iterrows():
            self._affects.setdefault(row["element"], []).append(row["defect"])

    # --- traversal -------------------------------------------------------
    def descendants(self, element: str, max_depth: int | None = None) -> dict[str, int]:
        """BFS over composed_of from ``element``. Returns {element_id: depth}."""
        seen: dict[str, int] = {element: 0}
        q: deque[str] = deque([element])
        while q:
            cur = q.popleft()
            d = seen[cur]
            if max_depth is not None and d >= max_depth:
                continue
            for child in self._children.get(cur, []):
                if child not in seen:
                    seen[child] = d + 1
                    q.append(child)
        return seen

    # --- inference -------------------------------------------------------
    def propagate_dal(self) -> dict[str, str | None]:
        """Effective DAL per element: strongest DAL allocated to it or any ancestor.

        Conservative/monotonic propagation DOWN the composition (ISO/ARP tailoring
        that could lower DAL across redundancy is intentionally NOT modelled).
        """
        effective: dict[str, str | None] = {e: None for e in self.element_ids}
        for req, elems in self._alloc_req_to_elems.items():
            dal = self.req_dal.get(req)
            for elem in elems:
                for target in self.descendants(elem):  # elem + all descendants
                    effective[target] = _stronger(effective[target], dal)
        return effective

    def impact(self, requirement: str, max_depth: int = 6) -> ImpactResult:
        """From a requirement -> allocated elements -> composition descendants ->
        defects affecting any of those elements."""
        result = ImpactResult(requirement=requirement, max_depth=max_depth)
        reachable: dict[str, int] = {}
        for elem in self._alloc_req_to_elems.get(requirement, []):
            result.edges.append((requirement, elem, "allocated_to"))
            for e, depth in self.descendants(elem, max_depth).items():
                reachable[e] = min(depth, reachable.get(e, depth))

        # record composed_of edges within the reachable set
        for parent in reachable:
            for child in self._children.get(parent, []):
                if child in reachable:
                    result.edges.append((parent, child, "composed_of"))

        defects: set[str] = set()
        for elem in reachable:
            for d in self._affects.get(elem, []):
                defects.add(d)
                result.edges.append((d, elem, "affects"))

        result.elements = sorted(reachable)
        result.defects = sorted(defects)
        return result


def load() -> AlmGraph:
    """Build the graph from the current warehouse."""
    return AlmGraph(warehouse.load_frames_from_db())


def propagate_table() -> pd.DataFrame:
    """Effective-vs-declared DAL per element as a DataFrame (for reports/CLI)."""
    g = load()
    effective = g.propagate_dal()
    rows = []
    elems = g.frames["architecture_elements"]
    for _, row in elems.iterrows():
        eid = row["id"]
        allocated = sorted(g._alloc_elem_to_reqs.get(eid, []))
        declared = None
        for req in allocated:
            declared = _stronger(declared, g.req_dal.get(req))
        rows.append(
            {
                "id": eid,
                "name": row["name"],
                "declared_dal": declared,        # from directly-allocated requirements
                "effective_dal": effective[eid],  # after downward propagation
                # effective is strictly more critical than declared -> inherited from above
                "inherited": queries.dal_severity(effective[eid]) > queries.dal_severity(declared),
            }
        )
    df = pd.DataFrame(rows)
    df["_sev"] = df["effective_dal"].map(lambda d: queries.dal_severity(d))
    return df.sort_values(["_sev", "id"], ascending=[False, True]).drop(columns="_sev")
