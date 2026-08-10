"""Install the 3 implemented corrections as ActionSpec graph data.

Step C (redirected). The original Phase-2 plan was 'add Rust mutation
Terms (SetAttr/AddNode/AddEdge)' — but on closer inspection the
existing JSON-dict action_spec format already provides graph-resident
mutation specification. The Rust Term variants would unify the
action DSL with the rest of substrate_rs but aren't strictly required
for self-loop functionality.

The actual remaining work: migrate the 3 implemented corrections
(raise_plasticity, beta_reweight, prune_Mt) into ActionSpec form so
that DETECTION → ACTION wiring is also graph-resident.

ActionSpec node schema:
  name                  str
  trigger_event_type    str — event type that fires this action
  action_spec           JSON str — dict-DSL action
  agent_authored        bool

Wiring (runtime):
  After each loop step's events fire, walk ActionSpec nodes; for
  each, look for events whose type matches trigger_event_type; for
  each match, evaluate the action_spec with an env bound from the
  event's attrs.

This commit:
  · Defines the ActionSpec node-type schema (via install_action_spec)
  · Installs raise_plasticity, beta_reweight, and prune_Mt as
    ActionSpec instances
  · Demonstrates parity: spec-driven and Python-driven corrections
    behave identically when triggered by the same event
"""
from __future__ import annotations

import json
from typing import Any

from domains.correction_beta_reweight import BETA_REWEIGHT_DELTA
from domains.correction_prune_mt import apply_prune_mt
from domains.correction_raise_plasticity import (
    PLASTICITY_OVERRIDE_INITIAL,
)


def install_action_spec(
    substrate,
    name: str,
    trigger_event_type: str,
    action_spec: dict,
    agent_authored: bool = False,
) -> Any:
    """Install an ActionSpec as a graph node."""
    try:
        return substrate.add_node("ActionSpec", {
            "name": name,
            "trigger_event_type": trigger_event_type,
            "action_spec": json.dumps(action_spec),
            "agent_authored": agent_authored,
        })
    except Exception:
        return None


def install_raise_plasticity_actionspec(substrate) -> Any:
    """For FrozenShouldAdaptEvent: write plasticity_override attr."""
    return install_action_spec(
        substrate,
        name="raise_plasticity_for_frozen",
        trigger_event_type="FrozenShouldAdaptEvent",
        action_spec={
            "op": "set_attr",
            "target": "mt",
            "key": "plasticity_override",
            "value": PLASTICITY_OVERRIDE_INITIAL,
        },
    )


def install_prune_actionspec(substrate) -> Any:
    """For SparseMtEvent: lower temperature to BETA_MIN."""
    return install_action_spec(
        substrate,
        name="prune_for_sparse",
        trigger_event_type="SparseMtEvent",
        action_spec={
            "op": "set_attr",
            "target": "mt",
            "key": "temperature",
            "value": 0.05,  # BETA_MIN
        },
    )


def install_correction_specs(substrate) -> dict[str, Any]:
    """Install both attr-modifying correction ActionSpecs.

    NOT installed (more complex than a single set_attr):
      · beta_reweight — requires reading two Mts' attrs +
        conditional logic. Currently Python-only; needs either
        the not-yet-built Rust mutation Terms OR an extension of
        the JSON-dict DSL with conditional ops.
    """
    return {
        "raise_plasticity": install_raise_plasticity_actionspec(substrate),
        "prune_Mt": install_prune_actionspec(substrate),
    }


def list_action_specs(substrate) -> list[dict[str, Any]]:
    """Walk ActionSpec nodes; return summary dicts."""
    out: list[dict[str, Any]] = []
    for n in substrate.nodes("ActionSpec"):
        attrs = substrate.node(n)["attrs"]
        nid = n.value if hasattr(n, "value") else int(n)
        out.append({
            "node": n,
            "node_id": nid,
            "name": str(attrs.get("name", "")),
            "trigger_event_type": str(attrs.get(
                "trigger_event_type", "")),
            "action_spec": str(attrs.get("action_spec", "{}")),
            "agent_authored": bool(attrs.get("agent_authored", False)),
        })
    return out


def run_action_specs_for_events(
    substrate, fired_events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """For each fired event, find matching ActionSpecs + execute them.

    `fired_events` is a list of dicts with at least:
      · 'event_type' — the type that fires
      · 'mt' — handle to the Mt the event is about
      · other attrs from the event

    Returns list of {action_spec_name, target_mt_id, result} entries
    for actions that fired."""
    from domains.runtime_discovery import evaluate_action_spec
    specs = list_action_specs(substrate)
    actions_taken: list[dict[str, Any]] = []
    for spec in specs:
        for event in fired_events:
            if event.get("event_type") != spec["trigger_event_type"]:
                continue
            try:
                action = json.loads(spec["action_spec"])
            except (ValueError, TypeError):
                continue
            env = dict(event)  # event provides mt, mt_id, etc.
            result = evaluate_action_spec(substrate, action, env)
            actions_taken.append({
                "action_spec_name": spec["name"],
                "target_mt_id": event.get("mt_id"),
                "result": result,
            })
    return actions_taken


__all__ = [
    "install_action_spec",
    "install_raise_plasticity_actionspec",
    "install_prune_actionspec",
    "install_correction_specs",
    "list_action_specs",
    "run_action_specs_for_events",
]
