"""Graph Query Contract (GQC) loading and LinkML validation.

GQC describes the supported graph questions as named, finite capabilities. It is
not a general query language and it is not compiled into dialect SQL/Cypher. The
YAML contract records the shared shape and renderer entrypoints; tests keep the
hand-authored renderers in agreement.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Any

import yaml

from alm_core import paths

GQC_DIR = paths.SRC_ROOT / "alm_graph" / "gqc_specs"
ALLOWED_SHAPES = {
    "closure",
    "fixed_multi_hop_path",
    "anti_join",
    "aggregation_count",
    "property_filter",
}
ALLOWED_DIRECTIONS = {"forward", "reverse"}


@dataclass(frozen=True)
class ValidationResult:
    capability: str
    errors: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors


def load_capability(name: str) -> dict[str, Any]:
    """Load a named GQC capability YAML document."""
    path = GQC_DIR / f"{name}.gqc.yaml"
    if not path.exists():
        raise FileNotFoundError(f"unknown GQC capability: {name}")
    with path.open(encoding="utf-8") as fh:
        doc = yaml.safe_load(fh) or {}
    if not isinstance(doc, dict):
        raise ValueError(f"GQC capability {name!r} did not parse as a mapping")
    return doc


def list_capabilities() -> list[str]:
    """Return available GQC capability names."""
    if not GQC_DIR.exists():
        return []
    return sorted(path.name.removesuffix(".gqc.yaml") for path in GQC_DIR.glob("*.gqc.yaml"))


def validate_capability(doc: dict[str, Any]) -> ValidationResult:
    """Validate one GQC document against the closed GQC shape set and LinkML nouns."""
    name = str(doc.get("name") or "<unnamed>")
    errors: list[str] = []
    model = _load_model()

    shape = doc.get("shape")
    if shape not in ALLOWED_SHAPES:
        errors.append(f"{name}: unsupported shape {shape!r}")

    classes = model.get("classes", {})
    slots = model.get("slots", {})
    start = doc.get("start") or {}
    start_class = start.get("class")
    if start_class is None:
        current_class = None
    elif start_class not in classes:
        errors.append(f"{name}: start class {start_class!r} is not a LinkML class")
        current_class = None
    else:
        current_class = start_class

    path_steps = doc.get("path") or []
    if not isinstance(path_steps, list):
        errors.append(f"{name}: path must be a list when present")
        path_steps = []
    if shape in {"closure", "fixed_multi_hop_path"} and not path_steps:
        errors.append(f"{name}: {shape} capabilities must contain at least one path step")

    for idx, step in enumerate(path_steps, start=1):
        if not isinstance(step, dict):
            errors.append(f"{name}: path step {idx} is not a mapping")
            continue
        slot = step.get("slot")
        source = step.get("source")
        target = step.get("target")
        direction = step.get("direction")

        if direction not in ALLOWED_DIRECTIONS:
            errors.append(f"{name}: path step {idx} has invalid direction {direction!r}")
            continue
        if source not in classes:
            errors.append(f"{name}: path step {idx} source {source!r} is not a LinkML class")
        if target not in classes:
            errors.append(f"{name}: path step {idx} target {target!r} is not a LinkML class")
        if slot not in slots:
            errors.append(f"{name}: path step {idx} slot {slot!r} is not a LinkML slot")
            continue

        if source in classes and slot not in _class_slots(model, str(source)):
            errors.append(f"{name}: slot {slot!r} is not declared on class {source!r}")
        slot_range = slots[slot].get("range")
        if target in classes and slot_range != target:
            errors.append(
                f"{name}: slot {slot!r} range is {slot_range!r}, expected target {target!r}"
            )

        if current_class:
            expected_current = source if direction == "forward" else target
            if current_class != expected_current:
                errors.append(
                    f"{name}: path step {idx} starts from {expected_current!r}, "
                    f"but previous step ended at {current_class!r}"
                )
            current_class = target if direction == "forward" else source

    uses = doc.get("uses") or {}
    for cls_name in uses.get("classes") or []:
        if cls_name not in classes:
            errors.append(f"{name}: uses class {cls_name!r} is not a LinkML class")
    for slot_name in uses.get("slots") or []:
        if slot_name not in slots:
            errors.append(f"{name}: uses slot {slot_name!r} is not a LinkML slot")

    result = doc.get("result") or {}
    group_by = result.get("group_by") or {}
    result_class = result.get("class") or group_by.get("class")
    if result_class not in classes:
        errors.append(f"{name}: result class {result_class!r} is not a LinkML class")
    elif current_class and result.get("class") and result_class != current_class:
        errors.append(
            f"{name}: result class {result_class!r} does not match path end {current_class!r}"
        )
    for field in group_by.get("fields") or []:
        if result_class in classes and field not in _class_slots(model, str(result_class)):
            errors.append(f"{name}: group_by field {field!r} is not on {result_class!r}")

    for engine, spec in (doc.get("engines") or {}).items():
        renderer = (spec or {}).get("renderer")
        if not renderer or not _renderer_exists(str(renderer)):
            errors.append(f"{name}: renderer for engine {engine!r} is not importable: {renderer!r}")

    return ValidationResult(capability=name, errors=errors)


def validate_all() -> list[ValidationResult]:
    """Validate every checked-in GQC capability."""
    return [validate_capability(load_capability(name)) for name in list_capabilities()]


def _load_model() -> dict[str, Any]:
    with paths.MODEL_FILE.open(encoding="utf-8") as fh:
        model = yaml.safe_load(fh) or {}
    if not isinstance(model, dict):
        raise ValueError("LinkML model did not parse as a mapping")
    return model


def _class_slots(model: dict[str, Any], class_name: str) -> set[str]:
    cls = model.get("classes", {}).get(class_name, {})
    slots = set(cls.get("slots") or [])
    slots.update((cls.get("attributes") or {}).keys())
    return slots


def _renderer_exists(entrypoint: str) -> bool:
    if ":" not in entrypoint:
        return False
    module_name, attr_path = entrypoint.split(":", 1)
    try:
        value: Any = import_module(module_name)
        for attr in attr_path.split("."):
            value = getattr(value, attr)
    except Exception:
        return False
    return callable(value)
