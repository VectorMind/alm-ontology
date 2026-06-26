"""Interactive Plotly figures, including a graph laid out with rustworkx.

Charts are Plotly only (interactive in the HTML report, even opened as a file). The
traceability graph is laid out with ``rustworkx`` and drawn as Plotly scatter traces.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import rustworkx as rx

from alm_core.queries import DAL_ORDER

TYPE_COLOR = {"requirement": "#3b6fb0", "element": "#3f9b6b", "defect": "#c0504d"}


def coverage_by_dal(summary: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_bar(name="covered", x=summary["dal"], y=summary["covered"], marker_color="#3f9b6b")
    fig.add_bar(name="uncovered", x=summary["dal"], y=summary["uncovered"], marker_color="#c0504d")
    fig.update_layout(
        title="Requirement coverage by DAL (passing test vs gap)",
        barmode="stack",
        xaxis_title="DAL",
        yaxis_title="requirements",
        legend_title="",
    )
    return fig


def outcome_distribution(df: pd.DataFrame) -> go.Figure:
    palette = {"passed": "#3f9b6b", "failed": "#c0504d", "not_run": "#d0a23b"}
    fig = go.Figure(
        go.Bar(
            x=df["outcome"],
            y=df["n"],
            marker_color=[palette.get(o, "#888") for o in df["outcome"]],
        )
    )
    fig.update_layout(title="Test outcomes", xaxis_title="outcome", yaxis_title="tests")
    return fig


def defects_per_element(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Bar(x=df["name"], y=df["n_defects"], marker_color="#c0504d"))
    fig.update_layout(
        title="Defects per affected element (direct)",
        xaxis_title="element",
        yaxis_title="defects",
    )
    return fig


def effective_dal_distribution(prop_df: pd.DataFrame) -> go.Figure:
    counts = (
        prop_df["effective_dal"]
        .fillna("none")
        .value_counts()
        .reindex([*DAL_ORDER, "none"])
        .dropna()
    )
    fig = go.Figure(go.Bar(x=counts.index.astype(str), y=counts.values, marker_color="#3b6fb0"))
    fig.update_layout(
        title="Architecture elements by effective (propagated) DAL",
        xaxis_title="effective DAL",
        yaxis_title="elements",
    )
    return fig


def impact_graph(result, labels: dict[str, str]) -> go.Figure:
    """Draw the impact subgraph (requirement -> elements -> defects) with a
    rustworkx spring layout."""
    g = rx.PyDiGraph()
    idx: dict[str, int] = {}

    def node(nid: str) -> int:
        if nid not in idx:
            idx[nid] = g.add_node(nid)
        return idx[nid]

    def kind(nid: str) -> str:
        if nid.startswith("REQ"):
            return "requirement"
        if nid.startswith("DEF"):
            return "defect"
        return "element"

    for src, dst, _rel in result.edges:
        g.add_edge(node(src), node(dst), None)
    # ensure isolated nodes (e.g. the requirement with no defects) still appear
    node(result.requirement)

    pos = rx.spring_layout(g, seed=42)

    edge_x: list[float] = []
    edge_y: list[float] = []
    for src, dst, _rel in result.edges:
        x0, y0 = pos[idx[src]]
        x1, y1 = pos[idx[dst]]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y, mode="lines",
        line=dict(width=1, color="#bbb"), hoverinfo="none", showlegend=False,
    )

    traces = [edge_trace]
    for k, color in TYPE_COLOR.items():
        xs, ys, texts = [], [], []
        for nid, i in idx.items():
            if kind(nid) != k:
                continue
            x, y = pos[i]
            xs.append(x)
            ys.append(y)
            texts.append(f"{nid}<br>{labels.get(nid, '')}")
        if xs:
            traces.append(
                go.Scatter(
                    x=xs, y=ys, mode="markers", name=k,
                    marker=dict(size=16, color=color, line=dict(width=1, color="#444")),
                    text=texts, hoverinfo="text",
                )
            )

    fig = go.Figure(traces)
    fig.update_layout(
        title=f"Impact trace from {result.requirement} (depth ≤ {result.max_depth})",
        showlegend=True,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        margin=dict(l=10, r=10, t=40, b=10),
    )
    return fig
