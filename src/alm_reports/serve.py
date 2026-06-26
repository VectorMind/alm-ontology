"""Serve generated reports from localhost with a small stdlib HTTP server.

Plotly HTML is interactive opened directly as a file; this is a convenience for
browsing all reports with a generated index.
"""

from __future__ import annotations

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from alm_core import paths


def build_index() -> str:
    """Write ``.report/index.html`` listing every report grouped by date."""
    paths.REPORT_DIR.mkdir(parents=True, exist_ok=True)
    items: list[str] = []
    for date_dir in sorted(paths.REPORT_DIR.glob("*"), reverse=True):
        if not date_dir.is_dir():
            continue
        htmls = sorted(date_dir.glob("*.html"), reverse=True)
        if not htmls:
            continue
        items.append(f"<h2>{date_dir.name}</h2><ul>")
        for h in htmls:
            rel = f"{date_dir.name}/{h.name}"
            md = h.with_suffix(".md").name
            md_link = (
                f" &nbsp;<a href='{date_dir.name}/{md}'>(md)</a>"
                if (date_dir / md).exists()
                else ""
            )
            items.append(f"<li><a href='{rel}'>{h.stem}</a>{md_link}</li>")
        items.append("</ul>")
    body = "".join(items) or "<p>No reports yet. Run <code>almon report</code>.</p>"
    html = (
        "<!doctype html><html><head><meta charset='utf-8'><title>ALM reports</title>"
        "<style>body{font-family:system-ui,Arial,sans-serif;max-width:820px;margin:2rem auto;}"
        "a{text-decoration:none;color:#2a4d75;} h2{color:#444;border-bottom:1px solid #eee;}</style>"
        "</head><body><h1>ALM ontology reports</h1>"
        f"{body}</body></html>"
    )
    index_path = paths.REPORT_DIR / "index.html"
    index_path.write_text(html, encoding="utf-8")
    return str(index_path)


def serve(port: int = 8000) -> None:
    build_index()
    handler = partial(SimpleHTTPRequestHandler, directory=str(paths.REPORT_DIR))
    httpd = ThreadingHTTPServer(("127.0.0.1", port), handler)
    print(f"Serving reports at http://127.0.0.1:{port}/  (Ctrl+C to stop)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        httpd.server_close()
