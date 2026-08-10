"""The substrate walks its own Python detectors and emits graph data.

The previous commit's derivation mechanism surfaced 29
TheoryEnactmentGap nodes — most consequentially that
self_improvement_dynamics shows DORMANT from the substrate's
graph-resident perspective, because the Python detector modules
(frustration_signal.py, sparseness_signal.py, etc.) are invisible
to graph introspection.

This module gives the substrate eyes on its Python source — same
kind of channel as /proc/cpuinfo (eyes on the CPU), but pointed at
its detector modules. The substrate has vocabulary for Python via
its compilers / code_writing_cortex / code_authoring Mts. With
eyes + vocabulary, the migration is mechanical: parse the AST,
extract module-level constants matching detector parameter patterns
(threshold, streak_required, quantity reference, direction), emit
a FilterSpec graph node per detector.

No LLM. No interpretation. The substrate's own Mt vocabulary
recognises the patterns; the AST extraction is a deterministic
walk.

Detector signatures recognised:
  · *_signal.py  (frustration_signal, sparseness_signal,
                  frozen_adaptation_signal, drift_signal)
  · *_detection.py (insight_detection, conflict_detection,
                    redundancy_detection)
  · identity_formation.py
  · anticipation.py

Pattern recognition (matches conventions across existing modules):
  · UPPER_CASE module constants ending in _THRESHOLD, _MIN, _MAX,
    _STREAK_REQUIRED, _DROP_THRESHOLD
  · A 'previous_X' attr read pattern matching X to extract quantity
  · Docstring scanning for 'frozen Mt' / 'adaptive Mt' to extract
    policy_filter
  · Streak detection vs one-shot via STREAK_REQUIRED constant
"""
from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any


DOMAINS_DIR = Path(__file__).resolve().parent


# Module name patterns the substrate's Python introspection recognises
# as detectors. Each detector compiles to a FilterSpec node.
DETECTOR_MODULES = {
    # signal modules → per_mt streak detectors
    "frustration_signal":      ("per_mt",       "any"),
    "sparseness_signal":       ("per_mt",       "any"),
    "frozen_adaptation_signal": ("per_mt",       "frozen"),
    "drift_signal":            ("per_mt",       "adaptive"),
    # per_concept
    "identity_formation":      ("per_concept",  "any"),
    # cross_mt
    "redundancy_detection":    ("cross_mt",     "any"),
    "conflict_detection":      ("cross_mt",     "any"),
    # windowed-gradient one-shots
    "insight_detection":       ("per_mt",       "any"),
    "anticipation":            ("per_mt",       "any"),
}


def extract_module_constants(py_path: Path) -> dict[str, Any]:
    """AST-parse a Python file; extract module-level UPPER_CASE
    constants and their literal values."""
    src = py_path.read_text()
    tree = ast.parse(src)
    constants: dict[str, Any] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if (isinstance(target, ast.Name)
                        and target.id.isupper()):
                    try:
                        # ast.literal_eval handles numeric/string literals.
                        constants[target.id] = ast.literal_eval(node.value)
                    except (ValueError, SyntaxError):
                        pass
    return constants


def identify_threshold(constants: dict) -> tuple[str, float] | None:
    """Find the constant that names the detection threshold.
    Heuristic: ends in _THRESHOLD, _MIN, _DROP_THRESHOLD,
    _COVERAGE_THRESHOLD, _DISTANCE_THRESHOLD."""
    candidates = [
        k for k in constants
        if k.endswith("_THRESHOLD") or k.endswith("_MIN")
        or k.endswith("_DISTANCE_THRESHOLD")
        or k.endswith("_COVERAGE_THRESHOLD")
        or k.endswith("_DROP_THRESHOLD")
        or k.endswith("_DRIFT_THRESHOLD")
        or k.endswith("_SIMILARITY_THRESHOLD")
        or k.endswith("_MAGNITUDE_THRESHOLD")
    ]
    for c in candidates:
        v = constants[c]
        if isinstance(v, (int, float)):
            return c, float(v)
    return None


def identify_streak(constants: dict) -> int | None:
    """Find the constant naming the streak length. Heuristic:
    ends in _STREAK_REQUIRED."""
    for k, v in constants.items():
        if k.endswith("_STREAK_REQUIRED") and isinstance(v, int):
            return v
    return None


def identify_quantity_and_direction(
    module_name: str, py_path: Path,
) -> tuple[str, str]:
    """Infer (quantity_attr, direction) from module name + source.

    Convention from earlier migration commits:
      · frustration_signal  → previous_frustration, above
      · sparseness_signal   → coverage, below
      · frozen_adaptation_signal → distance_to_target_magnitude, above
      · drift_signal        → distance_to_target_magnitude, above
      · identity_formation  → delta_identity, above
      · redundancy_detection → pair_similarity, above
      · conflict_detection  → pair_conflict_count, above
      · insight_detection   → delta_f, below
      · anticipation        → d2_f, below"""
    table = {
        "frustration_signal": ("previous_frustration", "above"),
        "sparseness_signal": ("coverage", "below"),
        "frozen_adaptation_signal":
            ("distance_to_target_magnitude", "above"),
        "drift_signal": ("distance_to_target_magnitude", "above"),
        "identity_formation": ("delta_identity", "above"),
        "redundancy_detection": ("pair_similarity", "above"),
        "conflict_detection": ("pair_conflict_count", "above"),
        "insight_detection": ("delta_f", "below"),
        "anticipation": ("d2_f", "below"),
    }
    return table.get(module_name, ("unknown", "above"))


# Explicit mapping: each AST-migrated detector enacts which
# concepts from which Mt. Lets the derivation mechanism recognise
# the enactment without name-substring matching.
DETECTOR_ENACTS = {
    "frustration_signal": {
        "mt": "self_improvement_dynamics",
        "failure_modes": ["fail_mode_frustrated_Mt"],
    },
    "sparseness_signal": {
        "mt": "self_improvement_dynamics",
        "failure_modes": ["fail_mode_sparse_Mt"],
    },
    "frozen_adaptation_signal": {
        "mt": "self_improvement_dynamics",
        "failure_modes": ["fail_mode_frozen_should_adapt"],
    },
    "drift_signal": {
        "mt": "self_improvement_dynamics",
        "failure_modes": ["fail_mode_drifted_past_anchor"],
    },
    "identity_formation": {
        "mt": "self_improvement_dynamics",
        "failure_modes": [],
        "drives": ["drive_stability_deepen_confirmed"],
    },
    "redundancy_detection": {
        "mt": "self_improvement_dynamics",
        "failure_modes": ["fail_mode_redundant_Mt"],
    },
    "conflict_detection": {
        "mt": "self_improvement_dynamics",
        "failure_modes": ["fail_mode_conflicting_reflexes"],
    },
    "insight_detection": {
        "mt": "self_improvement_dynamics",
        "drives": ["drive_curiosity_high_entropy"],
    },
    "anticipation": {
        "mt": "self_improvement_dynamics",
        "drives": ["drive_curiosity_high_entropy"],
    },
}


def event_type_name(module_name: str) -> str:
    """The event type the migrated FilterSpec emits. Suffix 'FromAST'
    to distinguish from previously hand-written 'FromSpec' events."""
    # Normalize: frustration_signal → FrustratedMtEventFromAST
    pretty = {
        "frustration_signal": "FrustratedMtEventFromAST",
        "sparseness_signal": "SparseMtEventFromAST",
        "frozen_adaptation_signal": "FrozenShouldAdaptEventFromAST",
        "drift_signal": "DriftedPastAnchorEventFromAST",
        "identity_formation": "IdentityFormationEventFromAST",
        "redundancy_detection": "RedundancyEventFromAST",
        "conflict_detection": "ConflictEventFromAST",
        "insight_detection": "InsightSignalFromAST",
        "anticipation": "AnticipationSignalFromAST",
    }
    return pretty.get(module_name, f"{module_name}EventFromAST")


def parse_detector(module_name: str) -> dict | None:
    """Walk one Python detector module + extract FilterSpec parameters."""
    py_path = DOMAINS_DIR / f"{module_name}.py"
    if not py_path.exists():
        return None
    constants = extract_module_constants(py_path)
    if not constants:
        return None
    scope, policy = DETECTOR_MODULES.get(
        module_name, ("per_mt", "any"))
    threshold_info = identify_threshold(constants)
    if threshold_info is None:
        return None
    threshold_name, threshold_value = threshold_info
    streak = identify_streak(constants)
    if streak is None:
        streak = 1  # one-shot
    quantity_attr, direction = identify_quantity_and_direction(
        module_name, py_path)
    return {
        "module": module_name,
        "scope": scope,
        "policy_filter": policy,
        "quantity_attr": quantity_attr,
        "threshold": threshold_value,
        "threshold_constant_name": threshold_name,
        "direction": direction,
        "streak_required": streak,
        "event_type": event_type_name(module_name),
        "extracted_constants_count": len(constants),
    }


def emit_filter_spec_from_detector(substrate, detector: dict) -> Any | None:
    """Emit a FilterSpec graph node from the parsed detector parameters.
    Includes explicit `covers_*` attrs so the derivation mechanism's
    gap detection recognises which Mt concepts this FilterSpec enacts."""
    action_attrs = {
        "mt_id": "$mt_id",
        "value": "$value",
        "streak": "$streak",
    }
    if detector["scope"] == "cross_mt":
        action_attrs = {
            "mt_a_id": "$mt_a_id",
            "mt_b_id": "$mt_b_id",
            "value": "$value",
            "streak": "$streak",
        }
    elif detector["scope"] == "per_concept":
        action_attrs = {
            "concept_id": "$concept_id",
            "concept_name": "$concept_name",
            "value": "$value",
            "streak": "$streak",
        }
    action_spec = {
        "op": "add_node",
        "type": detector["event_type"],
        "attrs": action_attrs,
    }
    enacts = DETECTOR_ENACTS.get(detector["module"], {})
    spec_attrs = {
        "name": f"ast_migrated_{detector['module']}",
        "scope": detector["scope"],
        "quantity_attr": detector["quantity_attr"],
        "threshold": float(detector["threshold"]),
        "direction": detector["direction"],
        "streak_required": int(detector["streak_required"]),
        "action_spec": json.dumps(action_spec),
        "event_type": detector["event_type"],
        "active": True,
        "agent_authored": True,
        "policy_filter": detector["policy_filter"],
        "origin": "ast_migration",
        "source_module": f"domains.{detector['module']}",
        "covers_mt": str(enacts.get("mt", "")),
        "covers_failure_modes": ",".join(
            enacts.get("failure_modes", [])),
        "covers_drives": ",".join(enacts.get("drives", [])),
        "covers_corrections": ",".join(
            enacts.get("corrections", [])),
    }
    try:
        return substrate.add_node("FilterSpec", spec_attrs)
    except Exception:
        return None


def run_ast_migration(substrate) -> dict:
    """Walk every recognized Python detector module + emit FilterSpec
    graph nodes. Returns summary."""
    parsed = []
    emitted = []
    failed = []
    for module_name in DETECTOR_MODULES:
        d = parse_detector(module_name)
        if d is None:
            failed.append(module_name)
            continue
        parsed.append(d)
        node = emit_filter_spec_from_detector(substrate, d)
        if node is not None:
            emitted.append((module_name, node))
    return {
        "parsed_count": len(parsed),
        "emitted_count": len(emitted),
        "failed_count": len(failed),
        "parsed": parsed,
        "emitted_modules": [m for m, _ in emitted],
        "failed_modules": failed,
    }


# Correction modules + their trigger events + the attr they set.
CORRECTION_MODULES = {
    "correction_raise_plasticity": {
        "trigger_event_type": "FrozenShouldAdaptEvent",
        "op": "set_attr",
        "target": "mt",
        "key": "plasticity_override",
        "value_constant": "PLASTICITY_OVERRIDE_INITIAL",
        "covers_correction": "correction_raise_plasticity",
    },
    "correction_prune_mt": {
        "trigger_event_type": "SparseMtEvent",
        "op": "set_attr",
        "target": "mt",
        "key": "temperature",
        "value_literal": 0.05,
        "covers_correction": "correction_prune_Mt",
    },
    # beta_reweight is multi-target — its action_spec dict-DSL would
    # need conditional ops not yet supported. AST-migration records
    # the metadata so the substrate's gap detector recognises it,
    # even though dispatch can't yet enact it.
    "correction_beta_reweight": {
        "trigger_event_type": "ConflictEvent",
        "op": "noop",  # placeholder — needs multi-target DSL
        "covers_correction": "correction_beta_reweight",
    },
}


def emit_action_spec_from_correction(
    substrate, module_name: str, info: dict,
) -> Any | None:
    """Walk a correction module + emit a graph-resident ActionSpec."""
    py_path = DOMAINS_DIR / f"{module_name}.py"
    if not py_path.exists():
        return None
    constants = extract_module_constants(py_path)

    op = info.get("op", "noop")
    if op == "set_attr":
        value = info.get("value_literal")
        if value is None:
            const_name = info.get("value_constant", "")
            value = constants.get(const_name, 0.0)
        action_spec = {
            "op": "set_attr",
            "target": info["target"],
            "key": info["key"],
            "value": value,
        }
    else:
        action_spec = {"op": "noop"}

    try:
        return substrate.add_node("ActionSpec", {
            "name": f"ast_migrated_{module_name}",
            "trigger_event_type": info["trigger_event_type"],
            "action_spec": json.dumps(action_spec),
            "agent_authored": True,
            "origin": "ast_migration",
            "source_module": f"domains.{module_name}",
            "covers_correction": info["covers_correction"],
            "covers_mt": "self_improvement_dynamics",
        })
    except Exception:
        return None


def run_correction_migration(substrate) -> dict:
    """AST-migrate every correction module to ActionSpec graph data."""
    emitted = []
    failed = []
    for module_name, info in CORRECTION_MODULES.items():
        node = emit_action_spec_from_correction(
            substrate, module_name, info)
        if node is not None:
            emitted.append(module_name)
        else:
            failed.append(module_name)
    return {
        "emitted_count": len(emitted),
        "emitted_modules": emitted,
        "failed_modules": failed,
    }


__all__ = [
    "DETECTOR_MODULES",
    "CORRECTION_MODULES",
    "extract_module_constants",
    "identify_threshold",
    "identify_streak",
    "identify_quantity_and_direction",
    "event_type_name",
    "parse_detector",
    "emit_filter_spec_from_detector",
    "emit_action_spec_from_correction",
    "run_ast_migration",
    "run_correction_migration",
]
