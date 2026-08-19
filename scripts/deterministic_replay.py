"""Portable episode specifications and differential replay utilities.

This module deliberately knows nothing about an aircraft, controller, or
world adapter.  A proving-ground harness supplies the profile/fault payload
and the trace; this module makes the experiment auditable and replayable.

The manifest is intentionally JSON rather than pickle.  A run can therefore
be reproduced by another process (or another implementation) using the same
initial state, event schedule, random-stream contract, and exogenous samples.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math
import platform
import subprocess
from pathlib import Path
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = "episode-spec-v1"


def _json_value(value: Any) -> Any:
    """Convert common runtime values to deterministic JSON values."""
    if isinstance(value, Mapping):
        return {
            str(key): _json_value(value[key])
            for key in sorted(value, key=lambda item: str(item))
        }
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            return str(value)
        # JSON's shortest round-trip representation is deterministic in the
        # supported Python versions and avoids locale-dependent formatting.
        return value
    if hasattr(value, "__dict__"):
        return _json_value(vars(value))
    return str(value)


def canonical_json(value: Any) -> str:
    """Return the canonical JSON encoding used for hashes and comparisons."""
    return json.dumps(
        _json_value(value),
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def file_sha256(path: str | Path) -> str | None:
    """Hash a source/seed file when it exists; absent files are explicit."""
    candidate = Path(path)
    if not candidate.is_file():
        return None
    digest = hashlib.sha256()
    with candidate.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_revision(cwd: str | Path | None = None) -> str | None:
    """Return the current revision without making git a runtime dependency."""
    try:
        result = subprocess.run(
            ("git", "rev-parse", "HEAD"),
            cwd=str(cwd) if cwd is not None else None,
            check=True,
            capture_output=True,
            text=True,
            timeout=2.0,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    revision = result.stdout.strip()
    return revision or None


@dataclass(frozen=True)
class EpisodeSpec:
    """All inputs that can affect one episode's observable outcome.

    The fields are deliberately domain-neutral.  ``profile`` and
    ``fault_specification`` are opaque payloads owned by the proving-ground
    adapter; a generic controller never needs to interpret them.
    """

    episode_id: str
    profile: Mapping[str, Any]
    initial_state: Mapping[str, Any]
    reference_schedule: Sequence[Mapping[str, Any]] = ()
    fault_specification: Mapping[str, Any] = field(default_factory=dict)
    event_timing: Mapping[str, Any] = field(default_factory=dict)
    exogenous: Mapping[str, Any] = field(default_factory=dict)
    rates: Mapping[str, Any] = field(default_factory=dict)
    controller: Mapping[str, Any] = field(default_factory=dict)
    seeds: Mapping[str, Any] = field(default_factory=dict)
    crash_predicates: Mapping[str, Any] = field(default_factory=dict)
    ambiguity_choices: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "schema_version": self.schema_version,
            "episode_id": self.episode_id,
            "profile": self.profile,
            "initial_state": self.initial_state,
            "reference_schedule": list(self.reference_schedule),
            "fault_specification": self.fault_specification,
            "event_timing": self.event_timing,
            "exogenous": self.exogenous,
            "rates": self.rates,
            "controller": self.controller,
            "seeds": self.seeds,
            "crash_predicates": self.crash_predicates,
            "ambiguity_choices": self.ambiguity_choices,
            "metadata": self.metadata,
        }
        payload["manifest_hash"] = sha256_json(payload)
        return _json_value(payload)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "EpisodeSpec":
        data = dict(payload)
        data.pop("manifest_hash", None)
        required = ("episode_id", "profile", "initial_state")
        missing = [key for key in required if key not in data]
        if missing:
            raise ValueError(f"episode manifest missing required fields: {missing}")
        if data.get("schema_version", SCHEMA_VERSION) != SCHEMA_VERSION:
            raise ValueError(
                f"unsupported episode manifest schema: {data.get('schema_version')}"
            )
        return cls(
            episode_id=str(data["episode_id"]),
            profile=data["profile"],
            initial_state=data["initial_state"],
            reference_schedule=tuple(data.get("reference_schedule", ())),
            fault_specification=data.get("fault_specification", {}),
            event_timing=data.get("event_timing", {}),
            exogenous=data.get("exogenous", {}),
            rates=data.get("rates", {}),
            controller=data.get("controller", {}),
            seeds=data.get("seeds", {}),
            crash_predicates=data.get("crash_predicates", {}),
            ambiguity_choices=data.get("ambiguity_choices", {}),
            metadata=data.get("metadata", {}),
            schema_version=data.get("schema_version", SCHEMA_VERSION),
        )

    def verify_hash(self, payload: Mapping[str, Any] | None = None) -> bool:
        data = dict(payload or self.to_dict())
        expected = data.pop("manifest_hash", None)
        return expected == sha256_json(data)


def save_episode_spec(spec: EpisodeSpec | Mapping[str, Any], path: str | Path) -> None:
    payload = spec.to_dict() if isinstance(spec, EpisodeSpec) else _json_value(spec)
    Path(path).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def load_episode_spec(path: str | Path) -> EpisodeSpec:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    spec = EpisodeSpec.from_dict(payload)
    if not spec.verify_hash(payload):
        raise ValueError(f"episode manifest hash mismatch: {path}")
    return spec


def runtime_fingerprint() -> dict[str, str]:
    """Small, non-domain-specific runtime identity for a manifest."""
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
    }


def _equal(left: Any, right: Any, tolerance: float) -> bool:
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return math.isclose(float(left), float(right), rel_tol=tolerance, abs_tol=tolerance)
    if isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)):
        return len(left) == len(right) and all(
            _equal(a, b, tolerance) for a, b in zip(left, right)
        )
    if isinstance(left, Mapping) and isinstance(right, Mapping):
        return set(left) == set(right) and all(
            _equal(left[key], right[key], tolerance) for key in left
        )
    return left == right


DEFAULT_DECISION_FIELDS = (
    "tokens",
    "groups",
    "program_mode",
    "target_body_rate_delta",
    "target_consequence_delta",
    "effector_position",
    "regime_ordinal",
    "flight_path_trim_active",
    "flight_path_orbit_active",
    "flight_path_speed_priority_active",
    "flight_path_roll_priority_active",
)


def first_divergence(
    baseline_trace: Sequence[Mapping[str, Any]],
    candidate_trace: Sequence[Mapping[str, Any]],
    *,
    fields: Sequence[str] = DEFAULT_DECISION_FIELDS,
    tolerance: float = 1.0e-9,
) -> dict[str, Any] | None:
    """Find the earliest observable decision/control divergence.

    The result points to the first action and field that differ, rather than
    attributing a later crash to the final metric.  Missing actions are also
    reported as divergence (the candidate may have failed earlier).
    """
    count = min(len(baseline_trace), len(candidate_trace))
    for index in range(count):
        baseline = baseline_trace[index]
        candidate = candidate_trace[index]
        action = baseline.get("request_seq", candidate.get("request_seq", index + 1))
        for field_name in fields:
            left = baseline.get(field_name)
            right = candidate.get(field_name)
            if not _equal(left, right, tolerance):
                return {
                    "action_index": index,
                    "request_seq": action,
                    "field": field_name,
                    "baseline": _json_value(left),
                    "candidate": _json_value(right),
                    "kind": "observable_decision_or_control",
                }
    if len(baseline_trace) != len(candidate_trace):
        index = count
        return {
            "action_index": index,
            "request_seq": index + 1,
            "field": "trace_length",
            "baseline": len(baseline_trace),
            "candidate": len(candidate_trace),
            "kind": "episode_termination",
        }
    return None


def differential_replay(
    baseline: Mapping[str, Any],
    candidate: Mapping[str, Any],
    *,
    fields: Sequence[str] = DEFAULT_DECISION_FIELDS,
    tolerance: float = 1.0e-9,
) -> dict[str, Any]:
    """Compare two results produced from one manifest."""
    baseline_spec = baseline.get("episode_spec", baseline.get("manifest"))
    candidate_spec = candidate.get("episode_spec", candidate.get("manifest"))
    manifest_match = None
    if baseline_spec is not None and candidate_spec is not None:
        manifest_match = (
            baseline_spec.get("manifest_hash") == candidate_spec.get("manifest_hash")
        )
    divergence = first_divergence(
        baseline.get("trace", ()), candidate.get("trace", ()),
        fields=fields, tolerance=tolerance,
    )
    return {
        "manifest_match": manifest_match,
        "first_divergence": divergence,
        "baseline_metrics": baseline.get("metrics"),
        "candidate_metrics": candidate.get("metrics"),
        "outcome_changed": baseline.get("metrics", {}).get("crash")
        != candidate.get("metrics", {}).get("crash"),
    }


__all__ = [
    "DEFAULT_DECISION_FIELDS",
    "EpisodeSpec",
    "SCHEMA_VERSION",
    "canonical_json",
    "differential_replay",
    "file_sha256",
    "first_divergence",
    "git_revision",
    "load_episode_spec",
    "runtime_fingerprint",
    "save_episode_spec",
    "sha256_json",
]
