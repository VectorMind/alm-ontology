"""GQC contract validation and first capability conformance."""

from __future__ import annotations

from importlib import import_module

import pytest

from alm_ontology import gqc, graph_age


def test_gqc_documents_validate_against_linkml():
    results = gqc.validate_all()
    assert results
    errors = [error for result in results for error in result.errors]
    assert errors == []


def test_linkml_owns_allocation_inverse_relation():
    impact = gqc.load_capability("impact")
    allocation_step = impact["path"][0]
    assert allocation_step["slot"] == "satisfied_by"

    model = gqc._load_model()
    satisfies = model["slots"]["satisfies"]
    satisfied_by = model["slots"]["satisfied_by"]
    assert satisfies["inverse"] == "satisfied_by"
    assert satisfied_by["inverse"] == "satisfies"
    assert "satisfied_by" in model["classes"]["Requirement"]["slots"]


def _call_renderer(entrypoint: str, params: dict):
    module_name, attr_path = entrypoint.split(":", 1)
    value = import_module(module_name)
    for attr in attr_path.split("."):
        value = getattr(value, attr)
    return value(**params)


def _expected_payload(expected: dict):
    if "defects" in expected:
        return expected["defects"]
    if "ids" in expected:
        return expected["ids"]
    return expected["rows"]


def _assert_matches_expected(actual, expected: dict):
    expected_payload = _expected_payload(expected)
    if "rows" not in expected or len(actual) == len(expected_payload):
        assert actual == expected_payload
        return
    for row in expected_payload:
        assert row in actual


@pytest.mark.parametrize("capability", gqc.list_capabilities())
def test_gqc_declared_renderers_match_fixtures(capability):
    doc = gqc.load_capability(capability)
    for fixture in doc.get("fixtures", []):
        params = fixture.get("parameters") or {}
        expected = fixture["expected"]
        baseline = None
        for engine, spec in (doc.get("engines") or {}).items():
            if engine == "cypher_age" and not graph_age.available():
                continue
            actual, _backend = _call_renderer(spec["renderer"], params)
            _assert_matches_expected(actual, expected)
            if baseline is None:
                baseline = actual
            elif len(actual) == len(baseline):
                assert actual == baseline
