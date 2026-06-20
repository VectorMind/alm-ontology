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


@app.callback()
def _main() -> None:
    """ALM ontology POC CLI."""


@app.command()
def version() -> None:
    """Print the package version."""
    from alm_ontology import __version__

    typer.echo(__version__)


@model_app.command("gen")
def model_gen() -> None:
    """Regenerate Pydantic types, SQL DDL, and docs from alm.yaml."""
    from alm_ontology import modelgen

    typer.echo("Generating artifacts from the LinkML model...")
    written = modelgen.generate()
    for name, path in written.items():
        typer.echo(f"  {name:10s} -> {path}")
    typer.secho("Model artifacts regenerated.", fg=typer.colors.GREEN)


@app.command()
def build() -> None:
    """Load data/ and build the SQLite + Parquet warehouse."""
    from alm_ontology import warehouse

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
    from alm_ontology import data_io, queries

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
    from alm_ontology import queries

    gaps = queries.coverage_gaps(min_dal=min_dal)
    if gaps.empty:
        typer.secho(f"No coverage gaps at DAL >= {min_dal}.", fg=typer.colors.GREEN)
        return
    typer.secho(f"Coverage gaps at DAL >= {min_dal}:", fg=typer.colors.YELLOW)
    for _, row in gaps.iterrows():
        outcomes = row["outcomes"] or "(no tests)"
        typer.echo(f"  {row['id']}  DAL {row['dal']}  {row['title']}  [{outcomes}]")


@app.command()
def impact(
    req: str = typer.Option(..., help="Requirement id, e.g. REQ-0110."),
    max_depth: int = typer.Option(6, help="Max composition depth to traverse."),
    engine: str = typer.Option(
        "both", help="rustworkx | duckpgq | recursive | both (cross-engine check)."
    ),
) -> None:
    """Trace a requirement -> architecture -> defects (variable-length path)."""
    from alm_ontology import graph_duckpgq, graph_rustworkx

    if engine in ("rustworkx", "both"):
        g = graph_rustworkx.load()
        rx_res = g.impact(req, max_depth=max_depth)
        typer.echo(f"[rustworkx] elements reached: {len(rx_res.elements)}")
        typer.echo(f"[rustworkx] impacted defects ({len(rx_res.defects)}): {', '.join(rx_res.defects) or '(none)'}")

    if engine in ("duckpgq", "recursive", "both"):
        sql_engine = "auto" if engine in ("duckpgq", "both") else "recursive"
        sql_defects, backend = graph_duckpgq.impact(req, max_depth=max_depth, engine=sql_engine)
        typer.echo(f"[{backend}] impacted defects ({len(sql_defects)}): {', '.join(sql_defects) or '(none)'}")

    if engine == "both":
        agree = rx_res.defects == sql_defects
        if agree:
            typer.secho("Cross-engine agreement: MATCH (OK)", fg=typer.colors.GREEN)
        else:
            typer.secho("Cross-engine agreement: MISMATCH", fg=typer.colors.RED)
            typer.echo(f"  rustworkx only: {set(rx_res.defects) - set(sql_defects)}")
            typer.echo(f"  sql only:       {set(sql_defects) - set(rx_res.defects)}")
            raise typer.Exit(code=1)


@app.command()
def propagate() -> None:
    """Show effective (propagated) DAL per architecture element."""
    from alm_ontology import graph_rustworkx

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
    from alm_ontology import report as report_mod

    out = report_mod.generate(topic=topic, req=req)
    typer.echo(f"  md   -> {out['md']}")
    typer.echo(f"  html -> {out['html']}")
    typer.secho("Report written. Open the HTML for interactive charts.", fg=typer.colors.GREEN)


@app.command()
def serve(port: int = typer.Option(8000, help="Port to serve .report/ on.")) -> None:
    """Serve generated reports from http://localhost:<port>/."""
    from alm_ontology import serve as serve_mod

    serve_mod.serve(port=port)


if __name__ == "__main__":
    app()
