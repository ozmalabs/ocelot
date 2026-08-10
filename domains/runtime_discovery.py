"""Graph-resident runtime discovery — Phase 1 of the self-loop runtime.

Per scripts/agent_designs_runtime.py, the substrate's path to full
self-loop is:

  1. Add SetAttr/AddNode/AddEdge as Term variants in Rust (Phase 2)
  2. Open FilterSpec/ActionSpec node productions (this commit)
  3. Build runtime discovery: walk FilterSpec nodes per step (this commit)
  4. Migrate detectors one at a time to FilterSpec form (this commit
     starts with one)

PHASE 1 (this module): the runtime walks FilterSpec nodes from the
graph + dispatches them. The action format is a small JSON dict DSL
interpreted in Python — sufficient for the substrate's existing
correction shapes (set_attr / add_node / add_edge). Once the 3 Rust
mutation Terms exist, action_spec becomes a Term-tree.

Action spec format (Phase 1 JSON DSL):

  {"op": "set_attr",  "target": "<var>", "key": "<str>", "value": <any>}
  {"op": "add_node",  "type": "<str>", "attrs": {...}}
  {"op": "add_edge",  "src": "<var>", "edge_type": "<str>", "tgt": "<var>"}

Variables resolved from the env passed to evaluate_action_spec:
  · "mt"      → the Mt being filtered
  · "concept" → the Concept being filtered (per_concept scope)
  · "<event field>" → values from the just-detected event dict

FilterSpec node schema:

  name              str
  scope             str — per_mt | cross_mt | per_concept
  quantity_attr     str — Mt or Concept attr to read
  threshold         float
  direction         str — above | below
  streak_required   int
  action_spec       JSON str — encodes the dict-DSL action
  event_type        str — node type for resulting events
  active            bool — toggle without removal
  agent_authored    bool — substrate-authored vs human-authored
"""
from __future__ import annotations

import json
from typing import Any


def evaluate_action_spec(substrate, spec: dict, env: dict) -> Any:
    """Interpret a Phase-1 action spec. Returns the result of the
    operation (e.g. new node handle for add_node)."""
    op = spec.get("op")
    if op == "set_attr":
        target = env[spec["target"]]
        substrate.set_attr(target, spec["key"], spec["value"])
        return None
    elif op == "add_node":
        attrs = dict(spec.get("attrs", {}))
        # Resolve any "$<var>" references in attrs against env.
        for k, v in list(attrs.items()):
            if isinstance(v, str) and v.startswith("$"):
                attrs[k] = env.get(v[1:])
        try:
            return substrate.add_node(spec["type"], attrs)
        except Exception:
            return None
    elif op == "add_edge":
        src = env[spec["src"]]
        tgt = env[spec["tgt"]]
        attrs = dict(spec.get("attrs", {}))
        try:
            substrate.add_edge(src, spec["edge_type"], tgt, attrs)
            return None
        except Exception:
            return None
    elif op == "noop":
        return None
    else:
        return None


def list_filter_specs(substrate) -> list[dict[str, Any]]:
    """Walk FilterSpec nodes; return summary dicts in graph order."""
    out: list[dict[str, Any]] = []
    for n in substrate.nodes("FilterSpec"):
        attrs = substrate.node(n)["attrs"]
        nid = n.value if hasattr(n, "value") else int(n)
        out.append({
            "node": n,
            "node_id": nid,
            "name": str(attrs.get("name", "")),
            "scope": str(attrs.get("scope", "per_mt")),
            "quantity_attr": str(attrs.get("quantity_attr", "")),
            "threshold": float(attrs.get("threshold", 0.0)),
            "direction": str(attrs.get("direction", "above")),
            "streak_required": int(attrs.get("streak_required", 1)),
            "action_spec": str(attrs.get("action_spec", "{}")),
            "event_type": str(attrs.get("event_type", "GenericEvent")),
            "active": bool(attrs.get("active", True)),
            "agent_authored": bool(attrs.get("agent_authored", True)),
            "policy_filter": str(attrs.get("policy_filter", "any")),
        })
    return out


def _mt_policy_matches(substrate, mt, policy_filter: str) -> bool:
    """Policy gate check. policy_filter ∈ {any, frozen, adaptive, hybrid}.
    'any' always passes. Others must match the Mt's update_policy."""
    if policy_filter == "any":
        return True
    actual = str(substrate.node(mt)["attrs"].get("update_policy", "frozen"))
    return actual == policy_filter


def _streak_attr_key(spec_name: str) -> str:
    return f"fs_streak_{spec_name}"


def _recorded_attr_key(spec_name: str) -> str:
    return f"fs_recorded_{spec_name}"


def run_filter_spec_on_mt(
    substrate, mt, spec: dict[str, Any],
) -> dict[str, Any] | None:
    """Phase-1 runtime: read the FilterSpec, check the quantity,
    update streak, fire action when streak crosses threshold.

    For per_mt scope, this is a simple above/below comparison + streak.
    Other scopes will follow in future commits."""
    if not spec["active"]:
        return None
    if spec["scope"] != "per_mt":
        # Phase-1: per_mt only. cross_mt + per_concept TBD.
        return None
    # Policy gate: skip if Mt's update_policy doesn't match.
    if not _mt_policy_matches(substrate, mt, spec.get("policy_filter", "any")):
        return None

    mt_attrs = substrate.node(mt)["attrs"]
    qattr = spec["quantity_attr"]
    if qattr not in mt_attrs:
        return None

    value = float(mt_attrs[qattr])
    threshold = spec["threshold"]
    direction = spec["direction"]

    if direction == "above":
        gate_passes = value > threshold
    elif direction == "below":
        gate_passes = value < threshold
    else:
        return None

    streak_key = _streak_attr_key(spec["name"])
    record_key = _recorded_attr_key(spec["name"])
    prev_streak = int(mt_attrs.get(streak_key, 0))
    already_recorded = bool(mt_attrs.get(record_key, False))

    if gate_passes:
        new_streak = prev_streak + 1
    else:
        new_streak = 0
        already_recorded = False

    substrate.set_attr(mt, streak_key, new_streak)
    substrate.set_attr(mt, record_key, already_recorded)

    if new_streak >= spec["streak_required"] and not already_recorded:
        substrate.set_attr(mt, record_key, True)
        # Build the env: mt + relevant event fields.
        mt_id = mt.value if hasattr(mt, "value") else int(mt)
        env: dict[str, Any] = {
            "mt": mt,
            "mt_id": mt_id,
            "mt_name": str(mt_attrs.get("name", "")),
            "value": value,
            "streak": new_streak,
            "threshold": threshold,
        }
        # Parse + execute action_spec.
        try:
            action = json.loads(spec["action_spec"])
        except (ValueError, TypeError):
            action = {}
        result = evaluate_action_spec(substrate, action, env)
        return {
            "filter_spec_name": spec["name"],
            "mt_id": mt_id,
            "value": value,
            "streak": new_streak,
            "action_result": result,
        }
    return None


def run_filter_spec_on_concept(
    substrate, mt, concept, spec: dict[str, Any],
) -> dict[str, Any] | None:
    """Per-Concept variant. Reads quantity_attr from the Concept's
    attrs; streak tracked on the Mt with a per-concept suffix so each
    (mt, concept) pair has its own streak."""
    if not spec["active"]:
        return None
    if spec["scope"] != "per_concept":
        return None

    concept_attrs = substrate.node(concept)["attrs"]
    qattr = spec["quantity_attr"]
    if qattr not in concept_attrs:
        return None

    value = float(concept_attrs[qattr])
    threshold = spec["threshold"]
    direction = spec["direction"]

    if direction == "above":
        gate_passes = value > threshold
    elif direction == "below":
        gate_passes = value < threshold
    else:
        return None

    cid = concept.value if hasattr(concept, "value") else int(concept)
    streak_key = f"{_streak_attr_key(spec['name'])}_concept_{cid}"
    record_key = f"{_recorded_attr_key(spec['name'])}_concept_{cid}"
    mt_attrs = substrate.node(mt)["attrs"]
    prev_streak = int(mt_attrs.get(streak_key, 0))
    already_recorded = bool(mt_attrs.get(record_key, False))

    if gate_passes:
        new_streak = prev_streak + 1
    else:
        new_streak = 0
        already_recorded = False

    substrate.set_attr(mt, streak_key, new_streak)
    substrate.set_attr(mt, record_key, already_recorded)

    if new_streak >= spec["streak_required"] and not already_recorded:
        substrate.set_attr(mt, record_key, True)
        mt_id = mt.value if hasattr(mt, "value") else int(mt)
        env: dict[str, Any] = {
            "mt": mt,
            "mt_id": mt_id,
            "concept": concept,
            "concept_id": cid,
            "concept_name": str(concept_attrs.get("name",
                                                   f"node_{cid}")),
            "value": value,
            "streak": new_streak,
            "threshold": threshold,
        }
        try:
            action = json.loads(spec["action_spec"])
        except (ValueError, TypeError):
            action = {}
        result = evaluate_action_spec(substrate, action, env)
        return {
            "filter_spec_name": spec["name"],
            "mt_id": mt_id,
            "concept_id": cid,
            "value": value,
            "streak": new_streak,
            "action_result": result,
        }
    return None


def run_filter_spec_on_pair(
    substrate, mt_a, mt_b, spec: dict[str, Any],
) -> dict[str, Any] | None:
    """Cross-Mt variant. Reads a pre-computed pair quantity attr from
    the canonical (lower-id) Mt: `<quantity_attr>_for_<other_id>`.
    Streak tracked similarly on the lower-id Mt with the other Mt's
    id in the key.

    The pair quantity must be pre-computed before this runs (e.g.,
    by stashing mt_pairwise_similarity output as a Mt-side attr).
    Phase-2 will eliminate the staging step by making the quantity
    itself a Term-tree."""
    if not spec["active"]:
        return None
    if spec["scope"] != "cross_mt":
        return None

    mt_a_id = mt_a.value if hasattr(mt_a, "value") else int(mt_a)
    mt_b_id = mt_b.value if hasattr(mt_b, "value") else int(mt_b)
    if mt_a_id > mt_b_id:
        mt_a, mt_b = mt_b, mt_a
        mt_a_id, mt_b_id = mt_b_id, mt_a_id

    qattr = f"{spec['quantity_attr']}_for_{mt_b_id}"
    mt_a_attrs = substrate.node(mt_a)["attrs"]
    if qattr not in mt_a_attrs:
        return None

    value = float(mt_a_attrs[qattr])
    threshold = spec["threshold"]
    direction = spec["direction"]

    if direction == "above":
        gate_passes = value > threshold
    elif direction == "below":
        gate_passes = value < threshold
    else:
        return None

    streak_key = f"{_streak_attr_key(spec['name'])}_pair_{mt_b_id}"
    record_key = f"{_recorded_attr_key(spec['name'])}_pair_{mt_b_id}"
    prev_streak = int(mt_a_attrs.get(streak_key, 0))
    already_recorded = bool(mt_a_attrs.get(record_key, False))

    if gate_passes:
        new_streak = prev_streak + 1
    else:
        new_streak = 0
        already_recorded = False

    substrate.set_attr(mt_a, streak_key, new_streak)
    substrate.set_attr(mt_a, record_key, already_recorded)

    if new_streak >= spec["streak_required"] and not already_recorded:
        substrate.set_attr(mt_a, record_key, True)
        env: dict[str, Any] = {
            "mt": mt_a,
            "mt_a": mt_a,
            "mt_b": mt_b,
            "mt_id": mt_a_id,
            "mt_a_id": mt_a_id,
            "mt_b_id": mt_b_id,
            "value": value,
            "streak": new_streak,
            "threshold": threshold,
        }
        try:
            action = json.loads(spec["action_spec"])
        except (ValueError, TypeError):
            action = {}
        result = evaluate_action_spec(substrate, action, env)
        return {
            "filter_spec_name": spec["name"],
            "mt_a_id": mt_a_id,
            "mt_b_id": mt_b_id,
            "value": value,
            "streak": new_streak,
            "action_result": result,
        }
    return None


def run_all_filter_specs(substrate) -> list[dict[str, Any]]:
    """Walk every active FilterSpec; apply to every relevant scope unit;
    collect fired events.

    Scope dispatch:
      per_mt      → iterate Mts; run_filter_spec_on_mt
      per_concept → iterate Mt × owned-Concepts; run_filter_spec_on_concept
      cross_mt    → iterate Mt pairs (canonical order);
                    run_filter_spec_on_pair (reads pre-computed pair attr)
    """
    specs = list_filter_specs(substrate)
    events: list[dict[str, Any]] = []
    for spec in specs:
        if not spec["active"]:
            continue
        if spec["scope"] == "per_mt":
            for mt in substrate.nodes("Microtheory"):
                event = run_filter_spec_on_mt(substrate, mt, spec)
                if event is not None:
                    events.append(event)
        elif spec["scope"] == "per_concept":
            for mt in substrate.nodes("Microtheory"):
                for concept in substrate.neighbours(mt, "has_concept"):
                    event = run_filter_spec_on_concept(
                        substrate, mt, concept, spec)
                    if event is not None:
                        events.append(event)
        elif spec["scope"] == "cross_mt":
            mts = list(substrate.nodes("Microtheory"))
            for i, mt_a in enumerate(mts):
                for mt_b in mts[i + 1:]:
                    event = run_filter_spec_on_pair(
                        substrate, mt_a, mt_b, spec)
                    if event is not None:
                        events.append(event)
    return events


def stash_delta_identity_per_concept(substrate) -> int:
    """Pre-compute Δh_id per Concept and stash as 'delta_identity'
    attr on the Concept itself. Enables per_concept FilterSpecs to
    detect identity formation as a streak above threshold.

    Reads previous_identity_<cid> from the Mt + current identity_field
    from the Concept; writes the difference back to the Concept's
    delta_identity attr.

    Returns count of concepts updated."""
    updated = 0
    for mt in substrate.nodes("Microtheory"):
        mt_attrs = substrate.node(mt)["attrs"]
        for c in substrate.neighbours(mt, "has_concept"):
            cid = c.value if hasattr(c, "value") else int(c)
            prev_key = f"previous_identity_{cid}"
            if prev_key not in mt_attrs:
                continue
            prev = float(mt_attrs[prev_key])
            current = float(substrate.node(c)["attrs"].get(
                "identity_field", 0.0))
            substrate.set_attr(c, "delta_identity", current - prev)
            updated += 1
    return updated


def stash_pair_quantities(substrate, min_shared: int = 1) -> int:
    """Pre-compute pair-level quantities + stash as Mt attrs so
    cross_mt FilterSpecs can read them.

    For each (mt_a, mt_b) pair with shared concepts:
      mt_pairwise_similarity(mt_a, mt_b) → stashed as
        pair_similarity_for_<higher_id> on lower-id Mt
      len(mt_conflicting_nodes(mt_a, mt_b)) → stashed as
        pair_conflict_count_for_<higher_id> on lower-id Mt
        (= number of shared Concepts where Mt_a and Mt_b's σ have
        opposite signs with substantial magnitudes)

    Returns count of pairs stashed."""
    mts = list(substrate.nodes("Microtheory"))
    stashed = 0
    for i, mt_a in enumerate(mts):
        a_id = mt_a.value if hasattr(mt_a, "value") else int(mt_a)
        a_concepts = {c.value for c in substrate.neighbours(
            mt_a, "has_concept")}
        for mt_b in mts[i + 1:]:
            b_id = mt_b.value if hasattr(mt_b, "value") else int(mt_b)
            b_concepts = {c.value for c in substrate.neighbours(
                mt_b, "has_concept")}
            shared = a_concepts & b_concepts
            if len(shared) < min_shared:
                continue
            # Canonical ordering — lower-id holds attrs.
            if a_id < b_id:
                lower, higher_id = mt_a, b_id
            else:
                lower, higher_id = mt_b, a_id
            sim_result = substrate.mt_pairwise_similarity(mt_a, mt_b)
            similarity = float(sim_result["similarity"])
            substrate.set_attr(lower,
                               f"pair_similarity_for_{higher_id}",
                               similarity)
            # Stash conflict count for the same pair.
            conflicts = substrate.mt_conflicting_nodes(mt_a, mt_b, 0.5)
            substrate.set_attr(lower,
                               f"pair_conflict_count_for_{higher_id}",
                               len(conflicts))
            stashed += 1
    return stashed


def install_filter_spec(
    substrate,
    name: str,
    scope: str,
    quantity_attr: str,
    threshold: float,
    direction: str,
    streak_required: int,
    action_spec: dict,
    event_type: str = "GenericEvent",
    agent_authored: bool = True,
    policy_filter: str = "any",
) -> Any:
    """Helper for installing a FilterSpec as graph data. Returns the
    new node handle. The agent's design output would call this directly
    instead of writing a Python module.

    policy_filter ∈ {any, frozen, adaptive, hybrid} — restricts to Mts
    matching that update_policy. 'any' = no restriction."""
    try:
        return substrate.add_node("FilterSpec", {
            "name": name,
            "scope": scope,
            "quantity_attr": quantity_attr,
            "threshold": float(threshold),
            "direction": direction,
            "streak_required": int(streak_required),
            "action_spec": json.dumps(action_spec),
            "event_type": event_type,
            "active": True,
            "agent_authored": agent_authored,
            "policy_filter": policy_filter,
        })
    except Exception:
        return None


__all__ = [
    "evaluate_action_spec",
    "list_filter_specs",
    "run_filter_spec_on_mt",
    "run_filter_spec_on_concept",
    "run_filter_spec_on_pair",
    "run_all_filter_specs",
    "stash_pair_quantities",
    "install_filter_spec",
]
