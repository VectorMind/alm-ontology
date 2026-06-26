"""Global Typer CLI for alm-ontology. Entry point: `almon`."""

from __future__ import annotations

import typer

app = typer.Typer(
    name="almon",
    help="ALM ontology POC - model, build, query, and report over the VM-E1 example.",
    no_args_is_help=True,
    add_completion=False,
)

model_app = typer.Typer(help="Layer 0 - the LinkML model and its generated artifacts.")
app.add_typer(model_app, name="model")
graph_app = typer.Typer(help="AGE graph lifecycle and GQC-backed graph runs.")
app.add_typer(graph_app, name="graph")


@app.callback()
def _main() -> None:
    """ALM ontology POC CLI."""


@app.command()
def version() -> None:
    """Print the package version."""
    from alm_core import __version__

    typer.echo(__version__)


@model_app.command("gen")
def model_gen() -> None:
    """Regenerate Pydantic types, SQL DDL, and docs from alm.yaml."""
    from alm_model import modelgen

    typer.echo("Generating artifacts from the LinkML model...")
    written = modelgen.generate()
    for name, path in written.items():
        typer.echo(f"  {name:10s} -> {path}")
    typer.secho("Model artifacts regenerated.", fg=typer.colors.GREEN)


@graph_app.command("rebuild")
def graph_rebuild() -> None:
    """Rebuild and persist the AGE graph from the current warehouse tables."""
    from alm_graph import age as graph_age

    counts = graph_age.rebuild_from_warehouse()
    typer.secho("AGE graph rebuilt and persisted -> graph 'alm'", fg=typer.colors.GREEN)
    for name, n in counts.items():
        typer.echo(f"  {name:22s} {n:5d} rows")


@graph_app.command("run")
def graph_run(
    capability: str = typer.Argument("impact", help="GQC capability to run."),
    req: str = typer.Option(..., help="Requirement id for impact."),
    max_depth: int = typer.Option(6, help="Max composition depth to traverse."),
    rebuild: bool = typer.Option(
        True,
        "--rebuild/--no-rebuild",
        help="Rebuild the persisted AGE graph before running the capability.",
    ),
) -> None:
    """Run a GQC graph capability against the AGE graph."""
    from alm_graph import age as graph_age

    if capability != "impact":
        typer.secho(f"Unsupported GQC capability: {capability}", fg=typer.colors.RED)
        raise typer.Exit(code=2)
    defects, backend = graph_age.impact(req, max_depth=max_depth, rebuild_graph=rebuild)
    typer.echo(f"[{backend}] impacted defects ({len(defects)}): {', '.join(defects) or '(none)'}")


@graph_app.command("validate-gqc")
def graph_validate_gqc() -> None:
    """Validate checked-in GQC YAML against LinkML."""
    from alm_graph import gqc

    results = gqc.validate_all()
    errors = [error for result in results for error in result.errors]
    if errors:
        typer.secho("GQC validation FAILED:", fg=typer.colors.RED)
        for error in errors:
            typer.echo(f"  - {error}")
        raise typer.Exit(code=1)
    for result in results:
        typer.echo(f"  {result.capability}: ok")
    typer.secho("GQC validation passed.", fg=typer.colors.GREEN)


@app.command()
def build() -> None:
    """Load data/ and build the SQLite + Parquet warehouse."""
    from alm_core import warehouse

    typer.echo("Building warehouse from data/ ...")
    report = warehouse.build()
    if not report.ok:
        typer.secho("Build failed:", fg=typer.colors.RED)
        for err in report.errors:
            typer.echo(f"  - {err}")
        raise typer.Exit(code=1)
    for name, n in report.tables.items():
        typer.echo(f"  {name:22s} {n:5d} rows")
    typer.secho(f"Warehouse built -> {report.sqlite_path}", fg=typer.colors.GREEN)


@app.command()
def validate() -> None:
    """Validate the data: structural (Pydantic), referential, and completeness."""
    from alm_core import data_io, queries

    raw = data_io.load_raw()
    errors = data_io.validate_structural(raw) + data_io.validate_referential(raw)
    if errors:
        typer.secho("Validation FAILED:", fg=typer.colors.RED)
        for err in errors:
            typer.echo(f"  - {err}")
        raise typer.Exit(code=1)
    typer.secho("Structural + referential validation passed.", fg=typer.colors.GREEN)

    # Cross-entity completeness (the handover's anti-join): DAL-A requirements
    # without a passing verifying test.
    gaps = queries.coverage_gaps(min_dal="A")
    if gaps.empty:
        typer.secho("Completeness: no DAL-A coverage gaps.", fg=typer.colors.GREEN)
    else:
        typer.secho(
            f"Completeness: {len(gaps)} DAL-A requirement(s) without a passing test:",
            fg=typer.colors.YELLOW,
        )
        for _, row in gaps.iterrows():
            typer.echo(f"  - {row['id']} (DAL {row['dal']}) {row['title']}")


@app.command()
def coverage(min_dal: str = typer.Option("A", help="Minimum DAL criticality (A..E).")) -> None:
    """Show requirements at/above a DAL with no passing verifying test (anti-join)."""
    from alm_core import queries

    gaps = queries.coverage_gaps(min_dal=min_dal)
    if gaps.empty:
        typer.secho(f"No coverage gaps at DAL >= {min_dal}.", fg=typer.colors.GREEN)
        return
    typer.secho(f"Coverage gaps at DAL >= {min_dal}:", fg=typer.colors.YELLOW)
    for _, row in gaps.iterrows():
        outcomes = row["outcomes"] or "(no tests)"
        typer.echo(f"  {row['id']}  DAL {row['dal']}  {row['title']}  [{outcomes}]")


@app.command("rebuild-exposures")
def rebuild_exposures(
    semantic: bool = typer.Option(
        False,
        "--semantic/--no-semantic",
        help="Also build FastEmbed/pgvector semantic rows.",
    ),
) -> None:
    """Rebuild Postgres search and semantic exposures from warehouse tables."""
    from alm_exposure import pg as pg_exposure

    counts = pg_exposure.rebuild(semantic=semantic)
    typer.secho("Postgres exposures rebuilt.", fg=typer.colors.GREEN)
    typer.echo(f"  search documents {counts['documents']:5d} rows")
    typer.echo(f"  embeddings       {counts['embeddings']:5d} rows")


@app.command()
def search(
    query: str = typer.Argument(..., help="Full-text query."),
    limit: int = typer.Option(10, help="Maximum results."),
) -> None:
    """Search ALM entities through Postgres full-text search."""
    from alm_exposure import pg as pg_exposure

    hits = pg_exposure.search(query, limit=limit)
    if not hits:
        typer.secho("No search hits.", fg=typer.colors.YELLOW)
        return
    for hit in hits:
        typer.echo(
            f"{hit['object_type']:20s} {hit['object_id']:12s} "
            f"{hit['rank']:.4f}  {hit['label']}"
        )
        typer.echo(f"  {hit['snippet']}")


@app.command()
def similar(
    query: str = typer.Argument(..., help="Semantic query."),
    limit: int = typer.Option(10, help="Maximum results."),
) -> None:
    """Find semantically similar ALM entities through FastEmbed + pgvector."""
    from alm_exposure import pg as pg_exposure

    hits = pg_exposure.similar(query, limit=limit)
    if not hits:
        typer.secho("No semantic hits. Run `almon rebuild-exposures --semantic` first.", fg=typer.colors.YELLOW)
        return
    for hit in hits:
        typer.echo(
            f"{hit['object_type']:20s} {hit['object_id']:12s} "
            f"{hit['distance']:.4f}  {hit['label']}"
        )


@app.command()
def impact(
    req: str = typer.Option(..., help="Requirement id, e.g. REQ-0110."),
    max_depth: int = typer.Option(6, help="Max composition depth to traverse."),
    engine: str = typer.Option(
        "all",
        help="rustworkx | duckpgq | recursive | age | both | all (cross-engine check).",
    ),
) -> None:
    """Trace a requirement -> architecture -> defects (variable-length path)."""
    from alm_graph import age as graph_age
    from alm_graph import duckpgq as graph_duckpgq
    from alm_graph import rustworkx as graph_rustworkx

    multi = engine in ("both", "all")
    results: dict[str, list[str]] = {}

    if engine in ("rustworkx", "both", "all"):
        rx_res = graph_rustworkx.load().impact(req, max_depth=max_depth)
        results["rustworkx"] = rx_res.defects
        typer.echo(f"[rustworkx] elements reached: {len(rx_res.elements)}")
        typer.echo(f"[rustworkx] impacted defects ({len(rx_res.defects)}): {', '.join(rx_res.defects) or '(none)'}")

    if engine in ("duckpgq", "recursive", "both", "all"):
        sql_engine = "recursive" if engine == "recursive" else "auto"
        sql_defects, backend = graph_duckpgq.impact(req, max_depth=max_depth, engine=sql_engine)
        results[backend] = sql_defects
        typer.echo(f"[{backend}] impacted defects ({len(sql_defects)}): {', '.join(sql_defects) or '(none)'}")

    # AGE only when explicitly asked, or when reachable under a multi-engine run.
    if engine == "age" or (engine == "all" and graph_age.available()):
        age_defects, backend = graph_age.impact(req, max_depth=max_depth)
        results[backend] = age_defects
        typer.echo(f"[{backend}] impacted defects ({len(age_defects)}): {', '.join(age_defects) or '(none)'}")
    elif engine in ("age", "all"):
        typer.secho("[age] skipped (no Apache AGE instance reachable)", fg=typer.colors.YELLOW)

    if multi and len(results) > 1:
        baseline = next(iter(results.values()))
        if all(defects == baseline for defects in results.values()):
            typer.secho(
                f"Cross-engine agreement ({', '.join(results)}): MATCH (OK)", fg=typer.colors.GREEN
            )
        else:
            typer.secho("Cross-engine agreement: MISMATCH", fg=typer.colors.RED)
            for name, defects in results.items():
                typer.echo(f"  {name}: {', '.join(defects) or '(none)'}")
            raise typer.Exit(code=1)


@app.command()
def propagate() -> None:
    """Show effective (propagated) DAL per architecture element."""
    from alm_graph import rustworkx as graph_rustworkx

    import pandas as pd

    def fmt(v: object) -> str:
        return "-" if v is None or (isinstance(v, float) and pd.isna(v)) else str(v)

    df = graph_rustworkx.propagate_table()
    typer.echo(f"{'element':24s} {'declared':9s} {'effective':9s}  inherited")
    for _, row in df.iterrows():
        mark = "  <- inherited" if row["inherited"] else ""
        typer.echo(f"{row['id']:24s} {fmt(row['declared_dal']):9s} {fmt(row['effective_dal']):9s}{mark}")


@app.command()
def report(
    topic: str = typer.Option("full", help="coverage | propagate | impact | full."),
    req: str = typer.Option("REQ-0110", help="Requirement id for the impact trace."),
) -> None:
    """Generate a Markdown + interactive HTML report under .report/<date>/."""
    from alm_reports import report as report_mod

    out = report_mod.generate(topic=topic, req=req)
    typer.echo(f"  md   -> {out['md']}")
    typer.echo(f"  html -> {out['html']}")
    typer.secho("Report written. Open the HTML for interactive charts.", fg=typer.colors.GREEN)


@app.command()
def serve(port: int = typer.Option(8000, help="Port to serve .report/ on.")) -> None:
    """Serve generated reports from http://localhost:<port>/."""
    from alm_reports import serve as serve_mod

    serve_mod.serve(port=port)


if __name__ == "__main__":
    app()
