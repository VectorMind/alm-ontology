"""Shared fixtures — build the warehouse once per test session."""

from __future__ import annotations

import pytest

from alm_core import warehouse


@pytest.fixture(scope="session", autouse=True)
def built_warehouse():
    report = warehouse.build()
    assert report.ok, f"warehouse build failed: {report.errors}"
    yield report
