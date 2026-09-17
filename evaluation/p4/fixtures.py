"""Locked public P4-R0 fixture validation and canonical materialization."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from evaluation.p0a.canonical import object_hash, parse_canonical, sha256
from .protocol import P4ProtocolError, SUPPORTED_ACTION_KINDS

_FORBIDDEN_LABELS = ("world", "domain", "fixture", "hidden", "mechanism", "evaluator")
_CANONICAL_ACTIONS = ["inspect", "reverse", "advance"]


def _valid_identifier(value: Any) -> bool:
    return isinstance(value, str) and bool(value) and len(value) <= 128 and all(
        char.isascii() and (char.isalnum() or char in "-_.:") for char in value
    )


def _validate_observation(observation: Any) -> None:
    if not isinstance(observation, dict) or not observation:
        raise P4ProtocolError("fixture observation")
    if any(any(word in key.lower() for word in _FORBIDDEN_LABELS) for key in observation):
        raise P4ProtocolError("fixture label leak")
    if set(observation) != {"signal"} or type(observation["signal"]) is not int:
        raise P4ProtocolError("fixture observation")


def load_bundle(path: Path) -> dict[str, Any]:
    try:
        raw = Path(path).read_bytes()
        value = parse_canonical(raw)
    except Exception as exc:
        raise P4ProtocolError("fixture bundle") from exc
    if (set(value) != {"schema", "fixtures"} or value["schema"] != "P4R0PublicBundleV1"
            or not isinstance(value["fixtures"], list) or len(value["fixtures"]) != 2):
        raise P4ProtocolError("exactly two fixtures")
    identifiers: set[str] = set()
    for fixture in value["fixtures"]:
        if (not isinstance(fixture, dict)
                or set(fixture) != {"id", "actions", "observations", "steps"}
                or not _valid_identifier(fixture.get("id"))
                or fixture["id"] in identifiers
                or type(fixture["steps"]) is not int or fixture["steps"] != 8
                or not isinstance(fixture["actions"], list)
                or not isinstance(fixture["observations"], list)
                or fixture["actions"] != _CANONICAL_ACTIONS
                or any(action not in SUPPORTED_ACTION_KINDS for action in fixture["actions"])):
            raise P4ProtocolError("fixture schema or transition mechanics")
        identifiers.add(fixture["id"])
        if len(fixture["observations"]) != 2:
            raise P4ProtocolError("fixture observations")
        for observation in fixture["observations"]:
            _validate_observation(observation)
    return value


def _record(fixture: dict[str, Any], bundle_digest: str) -> dict[str, Any]:
    return {
        "schema": "P4R0FixtureMaterializationV1",
        "bundle_digest": bundle_digest,
        "fixture_key": fixture["id"],
        "actions": list(fixture["actions"]),
        "observations": [dict(observation) for observation in fixture["observations"]],
        "steps": fixture["steps"],
    }


def materialize(path: Path, run_id: str, fixture_key: str | None = None) -> list[dict[str, Any]]:
    """Derive run-scoped opaque IDs while keeping the record digest stable."""
    bundle = load_bundle(path)
    bundle_digest = sha256(Path(path).read_bytes())
    selected = [f for f in bundle["fixtures"] if fixture_key is None or f["id"] == fixture_key]
    if fixture_key is not None and len(selected) != 1:
        raise P4ProtocolError("locked fixture selection")
    result = []
    for fixture in selected:
        canonical_record = _record(fixture, bundle_digest)
        result.append({
            **canonical_record,
            "fixture_id": "run-" + sha256((run_id + fixture["id"]).encode())[7:23],
            "fixture_digest": bundle_digest,
            "record_digest": object_hash(canonical_record),
            "selection_id": "sel-" + sha256(("p4-r0-selection:" + fixture["id"] + ":" + bundle_digest).encode())[7:23],
        })
    return result
