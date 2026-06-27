"""Reporting — write a Markdown report (tables/narrative) and a self-contained,
interactive HTML report (Plotly charts + rustworkx-laid-out graph).

Output convention (git-ignored):
    .cache/projects/<project>/report/<YYYY-MM-DD>/<topic>-<HHMMSS>.md
    .cache/projects/<project>/report/<YYYY-MM-DD>/<topic>-<HHMMSS>.html
The Markdown carries narrative + tables and links to the HTML; the HTML carries the
interactive charts. Plotly's JS is inlined once so the HTML is interactive as a file.
"""

from __future__ import annotations

import html as _html
from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go

from alm_core import paths, queries, warehouse
from alm_graph import rustworkx as graph_rustworkx
from alm_graph import sql as graph_sql
from alm_reports import charts

TOPICS = ["coverage", "propagate", "impact", "full"]


@dataclass
class Section:
    heading: str
    narrative: str
    table: pd.DataFrame | None = None
    figures: list[go.Figure] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# formatting helpers
# --------------------------------------------------------------------------- #
def _fmt(v: object) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "-"
    return str(v)


def _df_to_md(df: pd.DataFrame | None) -> str:
    if df is None or df.empty:
        return "_(none)_"
    cols = list(df.columns)
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join("---" for _ in cols) + " |",
    ]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(_fmt(row[c]).replace("|", "\\|") for c in cols) + " |")
    return "\n".join(lines)


def _df_to_html(df: pd.DataFrame | None) -> str:
    if df is None or df.empty:
        return "<p><em>(none)</em></p>"
    return df.fillna("-").to_html(index=False, border=0, classes="data", escape=True)


# --------------------------------------------------------------------------- #
# section builders
# --------------------------------------------------------------------------- #
def _coverage_sections() -> list[Section]:
    gaps = queries.coverage_gaps(min_dal="A")
    summary = queries.coverage_summary()
    outcomes = queries.outcome_distribution()
    n = len(gaps)
    narrative = (
        f"{n} DAL-A requirement(s) have no passing verifying test — a coverage gap and "
        "the literal shape of missing safety evidence. Coverage is computed as a "
        "relational anti-join (what is *missing*), not a graph match (what exists)."
    )
    return [
        Section(
            heading="Coverage gaps (DAL ≥ A)",
            narrative=narrative,
            table=gaps,
            figures=[charts.coverage_by_dal(summary), charts.outcome_distribution(outcomes)],
        )
    ]


def _propagate_sections() -> list[Section]:
    df = graph_rustworkx.propagate_table()
    inherited = int(df["inherited"].sum())
    narrative = (
        f"Effective DAL is propagated monotonically DOWN the composition. "
        f"{inherited} element(s) inherit a stronger DAL than their directly-allocated "
        "requirements imply. Propagation is auditable rustworkx code, not an opaque "
        "reasoner (conservative: ISO/ARP decomposition that could *lower* DAL is not modelled)."
    )
    show = df[["id", "name", "declared_dal", "effective_dal", "inherited"]]
    return [
        Section(
            heading="Effective DAL propagation",
            narrative=narrative,
            table=show,
            figures=[charts.effective_dal_distribution(df)],
        )
    ]


def _impact_sections(req: str) -> list[Section]:
    frames = warehouse.load_frames_from_db()
    g = graph_rustworkx.AlmGraph(frames)
    result = g.impact(req, max_depth=6)
    sql_defects, backend = graph_sql.impact(req, max_depth=6)
    agree = result.defects == sql_defects

    defects = frames["defects"]
    detail = defects[defects["id"].isin(result.defects)][
        ["id", "title", "severity", "status"]
    ].sort_values("id")

    labels = {
        **dict(zip(frames["requirements"]["id"], frames["requirements"]["title"])),
        **dict(zip(frames["architecture_elements"]["id"], frames["architecture_elements"]["name"])),
        **dict(zip(frames["defects"]["id"], frames["defects"]["title"])),
    }
    narrative = (
        f"From {req}, following allocation then composition (depth ≤ {result.max_depth}), "
        f"{len(result.elements)} architecture element(s) are reached and "
        f"{len(result.defects)} defect(s) are implicated. "
        f"Cross-engine check: rustworkx vs {backend} "
        f"{'AGREE' if agree else 'DISAGREE'} — the graph is a faithful regenerable view."
    )
    return [
        Section(
            heading=f"Impact trace from {req}",
            narrative=narrative,
            table=detail,
            figures=[charts.impact_graph(result, labels)],
        )
    ]


def _defects_section() -> list[Section]:
    df = queries.defects_per_element()
    return [
        Section(
            heading="Defect concentration",
            narrative="Defects per directly-affected architecture element.",
            table=df,
            figures=[charts.defects_per_element(df)],
        )
    ]


def build_sections(topic: str, req: str) -> list[Section]:
    if topic == "coverage":
        return _coverage_sections()
    if topic == "propagate":
        return _propagate_sections()
    if topic == "impact":
        return _impact_sections(req)
    if topic == "full":
        return [
            *_coverage_sections(),
            *_propagate_sections(),
            *_impact_sections(req),
            *_defects_section(),
        ]
    raise ValueError(f"unknown topic {topic!r}; choose from {TOPICS}")


# --------------------------------------------------------------------------- #
# rendering
# --------------------------------------------------------------------------- #
def _render_md(topic: str, when: datetime, sections: list[Section], html_name: str) -> str:
    out = [
        f"# ALM ontology report — {topic}",
        "",
        f"_Generated {when:%Y-%m-%d %H:%M:%S} from the current validated ALM dataset._",
        "",
        f"Interactive charts and the traceability graph are in the companion HTML: "
        f"[`{html_name}`]({html_name}).",
        "",
    ]
    for sec in sections:
        out += [f"## {sec.heading}", "", sec.narrative, ""]
        if sec.table is not None:
            out += [_df_to_md(sec.table), ""]
        if sec.figures:
            out += [f"_({len(sec.figures)} interactive chart(s) in the HTML report.)_", ""]
    return "\n".join(out)


def _render_html(topic: str, when: datetime, sections: list[Section]) -> str:
    body: list[str] = [
        f"<h1>ALM ontology report — {_html.escape(topic)}</h1>",
        f"<p class='meta'>Generated {when:%Y-%m-%d %H:%M:%S} "
        "from the current validated ALM dataset.</p>",
    ]
    first_fig = True
    for sec in sections:
        body.append(f"<h2>{_html.escape(sec.heading)}</h2>")
        body.append(f"<p>{_html.escape(sec.narrative)}</p>")
        if sec.table is not None:
            body.append(_df_to_html(sec.table))
        for fig in sec.figures:
            body.append(
                fig.to_html(
                    full_html=False,
                    include_plotlyjs=("inline" if first_fig else False),
                    default_height="460px",
                )
            )
            first_fig = False

    style = """
    body { font-family: system-ui, Arial, sans-serif; margin: 2rem auto; max-width: 980px;
           color: #222; line-height: 1.5; }
    .meta { color:#666; }
    h1 { border-bottom:2px solid #eee; padding-bottom:.3rem; }
    h2 { margin-top:2rem; color:#2a4d75; }
    table.data { border-collapse: collapse; margin:.5rem 0 1rem; font-size:.9rem; }
    table.data th, table.data td { border:1px solid #ddd; padding:.3rem .55rem; text-align:left; }
    table.data th { background:#f3f6fa; }
    """
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<title>ALM report — {_html.escape(topic)}</title><style>{style}</style></head>"
        f"<body>{''.join(body)}</body></html>"
    )


def generate(topic: str = "full", req: str = "REQ-0110") -> dict[str, str]:
    """Build a report; returns {'md': path, 'html': path}."""
    if topic not in TOPICS:
        raise ValueError(f"unknown topic {topic!r}; choose from {TOPICS}")
    sections = build_sections(topic, req)
    now = datetime.now()
    date_dir = paths.REPORT_DIR / now.strftime("%Y-%m-%d")
    date_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{topic}-{now:%H%M%S}"
    md_path = date_dir / f"{stem}.md"
    html_path = date_dir / f"{stem}.html"
    md_path.write_text(_render_md(topic, now, sections, html_path.name), encoding="utf-8")
    html_path.write_text(_render_html(topic, now, sections), encoding="utf-8")
    return {"md": str(md_path), "html": str(html_path)}
