"""Postgres search and semantic exposures rebuilt from warehouse tables."""

from __future__ import annotations

from contextlib import contextmanager, redirect_stderr, redirect_stdout
from dataclasses import dataclass
import io
import logging
import os
import sys
from typing import Any, Iterator
import warnings

import pandas as pd
import yaml

from alm_core import paths, warehouse
from alm_graph import age as graph_age

EMBEDDING_PROFILE = "fastembed_bge_small_en_v1_5"
EMBEDDING_DIMENSION = 384

TABLE_CLASSES: dict[str, str] = {
    "requirements": "Requirement",
    "architecture_elements": "ArchitectureElement",
    "test_cases": "TestCase",
    "defects": "Defect",
}


@dataclass(frozen=True)
class ExposureRecord:
    object_type: str
    object_id: str
    label: str
    text: str


def rebuild(*, semantic: bool = False, embedding_profile: str = EMBEDDING_PROFILE) -> dict[str, int]:
    """Rebuild Postgres FTS rows, and optionally pgvector embeddings, from the warehouse."""
    frames = warehouse.load_frames_from_db()
    records = records_from_frames(frames)
    con = graph_age.connect()
    try:
        _ensure_search_schema(con)
        con.execute("TRUNCATE alm_search_documents;")
        for record in records:
            con.execute(
                """
                INSERT INTO alm_search_documents
                (object_type, object_id, label, body)
                VALUES (%s, %s, %s, %s)
                """,
                (record.object_type, record.object_id, record.label, record.text),
            )
        if semantic:
            _rebuild_semantic(con, records, embedding_profile)
    finally:
        con.close()
    return {"documents": len(records), "embeddings": len(records) if semantic else 0}


def search(query: str, *, limit: int = 10) -> list[dict[str, Any]]:
    """Search indexed ALM documents through Postgres full-text search."""
    con = graph_age.connect()
    try:
        rows = con.execute(
            """
            WITH q AS (SELECT websearch_to_tsquery('english', %s) AS query)
            SELECT
                d.object_type,
                d.object_id,
                d.label,
                ts_rank_cd(d.search_vector, q.query) AS rank,
                ts_headline('english', d.body, q.query, 'MaxWords=18, MinWords=6') AS snippet
            FROM alm_search_documents d, q
            WHERE d.search_vector @@ q.query
            ORDER BY rank DESC, d.object_type, d.object_id
            LIMIT %s
            """,
            (query, int(limit)),
        ).fetchall()
    finally:
        con.close()
    return [
        {
            "object_type": row[0],
            "object_id": row[1],
            "label": row[2],
            "rank": float(row[3]),
            "snippet": row[4],
        }
        for row in rows
    ]


def similar(
    query: str,
    *,
    limit: int = 10,
    embedding_profile: str = EMBEDDING_PROFILE,
) -> list[dict[str, Any]]:
    """Find semantically similar indexed ALM documents through pgvector."""
    profile = _embedding_profile(embedding_profile)
    vector = _embed_query(profile, query)
    vector_literal = _vector_literal(vector)
    con = graph_age.connect()
    try:
        _ensure_vector_extension(con)
        rows = con.execute(
            """
            SELECT
                e.object_type,
                e.object_id,
                d.label,
                e.embedding <=> %s::vector AS distance
            FROM alm_semantic_embeddings e
            JOIN alm_search_documents d
              ON d.object_type = e.object_type AND d.object_id = e.object_id
            WHERE e.embedding_profile = %s
            ORDER BY e.embedding <=> %s::vector, e.object_type, e.object_id
            LIMIT %s
            """,
            (vector_literal, embedding_profile, vector_literal, int(limit)),
        ).fetchall()
    finally:
        con.close()
    return [
        {
            "object_type": row[0],
            "object_id": row[1],
            "label": row[2],
            "distance": float(row[3]),
        }
        for row in rows
    ]


def records_from_frames(frames: dict[str, pd.DataFrame]) -> list[ExposureRecord]:
    """Build one search/semantic document per node row from LinkML annotations."""
    model = _load_model()
    records: list[ExposureRecord] = []
    for table, class_name in TABLE_CLASSES.items():
        slots = _annotated_class_slots(model, class_name, "searchable")
        for row in frames[table].to_dict(orient="records"):
            object_id = str(row["id"])
            label = _label_for(row)
            parts = [str(row[slot]) for slot in slots if slot in row and _present(row[slot])]
            body = "\n".join(dict.fromkeys([label, *parts]))
            records.append(
                ExposureRecord(
                    object_type=class_name,
                    object_id=object_id,
                    label=label,
                    text=body,
                )
            )
    return records


def _ensure_search_schema(con) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS alm_search_documents (
            object_type text NOT NULL,
            object_id text NOT NULL,
            label text NOT NULL,
            body text NOT NULL,
            search_vector tsvector GENERATED ALWAYS AS (
                to_tsvector('english', coalesce(label, '') || ' ' || coalesce(body, ''))
            ) STORED,
            PRIMARY KEY (object_type, object_id)
        );
        """
    )
    con.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_alm_search_documents_vector
        ON alm_search_documents USING GIN (search_vector);
        """
    )


def _rebuild_semantic(
    con,
    records: list[ExposureRecord],
    embedding_profile: str,
) -> None:
    profile = _embedding_profile(embedding_profile)
    dimension = int(profile.get("dimension") or EMBEDDING_DIMENSION)
    _ensure_vector_extension(con)
    con.execute(
        f"""
        CREATE TABLE IF NOT EXISTS alm_semantic_embeddings (
            object_type text NOT NULL,
            object_id text NOT NULL,
            embedding_profile text NOT NULL,
            embedding_model text NOT NULL,
            embedding vector({dimension}) NOT NULL,
            source_text_sha text NOT NULL,
            PRIMARY KEY (object_type, object_id, embedding_profile)
        );
        """
    )
    con.execute("TRUNCATE alm_semantic_embeddings;")
    vectors = _embed_passages(profile, [record.text for record in records])
    for record, vector in zip(records, vectors):
        con.execute(
            """
            INSERT INTO alm_semantic_embeddings
            (object_type, object_id, embedding_profile, embedding_model, embedding, source_text_sha)
            VALUES (%s, %s, %s, %s, %s::vector, md5(%s))
            """,
            (
                record.object_type,
                record.object_id,
                embedding_profile,
                str(profile["model_name"]),
                _vector_literal(vector),
                record.text,
            ),
        )
    con.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_alm_semantic_embeddings_vector
        ON alm_semantic_embeddings USING hnsw (embedding vector_cosine_ops);
        """
    )


def _ensure_vector_extension(con) -> None:
    con.execute("CREATE EXTENSION IF NOT EXISTS vector;")


def _embedding_profile(name: str) -> dict[str, Any]:
    config_path = paths.EMBEDDINGS_FILE
    with config_path.open(encoding="utf-8") as fh:
        config = yaml.safe_load(fh) or {}
    for profile in config.get("profiles") or []:
        if profile.get("name") == name:
            if profile.get("provider") != "fastembed":
                raise ValueError(f"unsupported embedding provider: {profile.get('provider')}")
            return profile
    raise ValueError(f"unknown embedding profile: {name}")


def _load_model() -> dict[str, Any]:
    with paths.MODEL_FILE.open(encoding="utf-8") as fh:
        model = yaml.safe_load(fh) or {}
    return model


def _annotated_class_slots(model: dict[str, Any], class_name: str, annotation: str) -> list[str]:
    slots = model["slots"]
    class_slots = model["classes"][class_name].get("slots") or []
    return [
        slot
        for slot in class_slots
        if slot in slots and _annotation_bool(slots[slot].get("annotations") or {}, annotation)
    ]


def _annotation_bool(annotations: dict[str, Any], name: str) -> bool:
    value = annotations.get(name)
    if isinstance(value, dict):
        value = value.get("value")
    return str(value).lower() in {"true", "1", "yes"}


def _label_for(row: dict[str, object]) -> str:
    for key in ("title", "name", "id"):
        value = row.get(key)
        if _present(value):
            return str(value)
    return str(row["id"])


def _present(value: object) -> bool:
    return value is not None and not (isinstance(value, float) and pd.isna(value)) and str(value)


def _embed_passages(profile: dict[str, Any], texts: list[str]) -> list[list[float]]:
    model = _fastembed_model(profile)
    with _quiet_output():
        return [_vector_to_list(vector) for vector in model.passage_embed(texts)]


def _embed_query(profile: dict[str, Any], text: str) -> list[float]:
    model = _fastembed_model(profile)
    with _quiet_output():
        return _vector_to_list(next(iter(model.query_embed([text]))))


def _fastembed_model(profile: dict[str, Any]) -> Any:
    from fastembed import TextEmbedding  # type: ignore[import-not-found]

    cache_dir = paths.MODEL_CACHE_DIR / "fastembed"
    cache_dir.mkdir(parents=True, exist_ok=True)
    with _quiet_output():
        return TextEmbedding(
            model_name=str(profile["model_name"]),
            cache_dir=str(cache_dir),
            lazy_load=True,
        )


def _vector_to_list(vector: Any) -> list[float]:
    return [float(value) for value in list(vector)]


def _vector_literal(vector: list[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in vector) + "]"


@contextmanager
def _quiet_output() -> Iterator[None]:
    logger_names = ("fastembed", "huggingface_hub", "onnxruntime")
    previous_levels = {logger_name: logging.getLogger(logger_name).level for logger_name in logger_names}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for logger_name in logger_names:
            logging.getLogger(logger_name).setLevel(logging.ERROR)
        try:
            with _suppress_standard_fds():
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    yield
        finally:
            for logger_name, level in previous_levels.items():
                logging.getLogger(logger_name).setLevel(level)


@contextmanager
def _suppress_standard_fds() -> Iterator[None]:
    sys.stdout.flush()
    sys.stderr.flush()
    saved_stdout = os.dup(1)
    saved_stderr = os.dup(2)
    devnull = os.open(os.devnull, os.O_WRONLY)
    try:
        os.dup2(devnull, 1)
        os.dup2(devnull, 2)
        yield
    finally:
        sys.stdout.flush()
        sys.stderr.flush()
        os.dup2(saved_stdout, 1)
        os.dup2(saved_stderr, 2)
        os.close(saved_stdout)
        os.close(saved_stderr)
        os.close(devnull)
