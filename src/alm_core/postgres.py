"""Shared Postgres connection helpers."""

from __future__ import annotations

import os


def conn_params() -> dict[str, object]:
    """Postgres connection params (env-overridable; defaults match docker-compose.yml)."""
    return {
        "host": os.environ.get("ALM_PG_HOST", "127.0.0.1"),
        "port": int(os.environ.get("ALM_PG_PORT", "5432")),
        "user": os.environ.get("ALM_PG_USER", "postgres"),
        "password": os.environ.get("ALM_PG_PASSWORD", "postgres"),
        "dbname": os.environ.get("ALM_PG_DB", "alm"),
    }


def label() -> str:
    """Human-readable connection label without credentials."""
    params = conn_params()
    return f"{params['user']}@{params['host']}:{params['port']}/{params['dbname']}"


def connect(*, autocommit: bool = True, connect_timeout: int = 5):
    """Open a psycopg connection to the ALM Postgres substrate."""
    import psycopg

    return psycopg.connect(
        **conn_params(),
        autocommit=autocommit,
        connect_timeout=connect_timeout,
    )
