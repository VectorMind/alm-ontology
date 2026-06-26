"""Postgres FTS and pgvector exposure tests."""

from __future__ import annotations

import pytest

from alm_ontology import graph_age, pg_exposure, warehouse


def _pg_available_or_skip() -> None:
    if not graph_age.available():
        pytest.skip("no Postgres+AGE instance reachable")


def test_records_are_derived_from_linkml_annotations():
    frames = warehouse.load_frames_from_db()
    records = pg_exposure.records_from_frames(frames)
    by_id = {(record.object_type, record.object_id): record for record in records}

    req = by_id[("Requirement", "REQ-0110")]
    assert "Battery energy for mission" in req.text
    assert "The battery pack shall store sufficient energy" in req.text

    element = by_id[("ArchitectureElement", "ARC-BMS")]
    assert "Battery Management System" in element.text


def test_postgres_full_text_search_returns_battery_hits():
    _pg_available_or_skip()
    counts = pg_exposure.rebuild(semantic=False)
    assert counts["documents"] > 0

    hits = pg_exposure.search("battery thermal", limit=5)
    assert hits
    assert any(hit["object_id"] in {"REQ-0110", "ARC-BMS", "ARC-BATT"} for hit in hits)


def test_pgvector_similarity_uses_rebuilt_embeddings(monkeypatch):
    _pg_available_or_skip()

    def fake_vector(text: str) -> list[float]:
        lower = text.lower()
        if "battery" in lower or "thermal" in lower:
            return [1.0, *([0.0] * 383)]
        return [0.0, 1.0, *([0.0] * 382)]

    monkeypatch.setattr(
        pg_exposure,
        "_embed_passages",
        lambda _profile, texts: [fake_vector(text) for text in texts],
    )
    monkeypatch.setattr(pg_exposure, "_embed_query", lambda _profile, text: fake_vector(text))

    counts = pg_exposure.rebuild(semantic=True)
    assert counts["embeddings"] == counts["documents"]

    hits = pg_exposure.similar("battery thermal containment", limit=5)
    assert hits
    assert hits[0]["distance"] == pytest.approx(0.0)
    assert any(hit["object_id"] in {"REQ-0110", "ARC-BMS", "ARC-BATT"} for hit in hits[:3])
