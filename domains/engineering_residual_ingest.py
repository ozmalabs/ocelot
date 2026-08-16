"""engineering_residual_ingest — mechanical I/O for Proposal 3
(DESIGN_REVIEW_CAPABILITY_EXPANSION_PREREG.md §4,
docs/research/engine_substrate/MEASURED_RESIDUAL_FILING_PREREG.md).

A diagnostic script (scripts/ceiling3_diag_sweep.py,
scripts/mbpp_endgame_battery.py) already computes a structured residual
population dict -- the SAME shape mbpp_endgame_battery.taxonomy() returns:

    {outcome: {"n": count, "task_ids": [task_id, ...]}, ...}

This module writes each named population as a typed `EngineeringResidual`
fact node -- mechanical I/O only, NO interpretation of the numbers (the ONE
exception, "pass" is not a residual, is a rule-side decision in
seeds/engineering_residual_gap.json, not here). Which populations constitute
a standing SelfConcern, and when a re-measurement retires one, is entirely
the seed's rules' call -- this module never mints a SelfConcern itself.

Two independent things live here:

  1. `ingest_taxonomy` -- the pure graph mutation (find-or-update an
     EngineeringResidual node per population, tick()). Works against ANY
     substrate + agent node the caller already has open (a fresh test
     substrate, an existing WorldAdapter, ...).
  2. `load_or_boot_residual_substrate` / `save_residual_substrate` -- a
     SMALL, DEDICATED persisted substrate (results/engineering_gaps_
     substrate.json, graph_to_dict/graph_from_dict -- the CLAUDE.md-
     sanctioned save/load pair, already used this way by
     scripts/corpus_self_learn.py) so a re-measurement across separate
     script invocations can retire a population whose count fell to zero.
     This is NOT the real jabberwock daemon's own checkpoint -- wiring the
     daemon to read it is a named residual, not built here.
"""
from __future__ import annotations

import json
import os
import time
from typing import Any, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CHECKPOINT = os.path.join(ROOT, "results", "engineering_gaps_substrate.json")


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def ingest_taxonomy(substrate, agent, *, source_script: str,
                    taxonomy: dict[str, dict[str, Any]],
                    measured_at: Optional[str] = None) -> dict[str, Any]:
    """Mechanical I/O: upsert one `EngineeringResidual` node per population
    in `taxonomy` (the {outcome: {"n": count, "task_ids": [...]}} shape
    mbpp_endgame_battery.taxonomy() already produces), keyed by
    (source_script, outcome). A population held from a PRIOR ingest under
    this source_script but ABSENT from this run's taxonomy is treated as
    count=0 (absence is zero -- never left stale). Calls substrate.tick()
    once at the end so seeds/engineering_residual_gap.json's rules see the
    update immediately. Returns a plain readback dict (upserted/zeroed
    counts) -- no decision is made here about which populations are gaps.
    """
    measured_at = measured_at or _now()
    existing: dict[str, Any] = {}
    for nid in substrate.nodes("EngineeringResidual"):
        at = substrate.node(nid)["attrs"]
        if at.get("source_script") == source_script:
            existing[str(at.get("outcome"))] = nid

    seen = set()
    upserted = []
    for outcome, entry in taxonomy.items():
        seen.add(outcome)
        count = int(entry.get("n", 0))
        task_ids = list(entry.get("task_ids", []))
        pop_key = f"{source_script}:{outcome}"
        if outcome in existing:
            nid = existing[outcome]
            substrate.set_attr(nid, "count", count)
            substrate.set_attr(nid, "task_ids", task_ids)
            substrate.set_attr(nid, "measured_at", measured_at)
        else:
            nid = substrate.add_node("EngineeringResidual", {
                "source_script": source_script,
                "outcome": str(outcome),
                "population_key": pop_key,
                "count": count,
                "task_ids": task_ids,
                "measured_at": measured_at,
            })
            # has_engineering_residual has no Γ production (this is a
            # mechanical fact edge, the same "unchecked" precedent
            # jabberwock_daemon.promote_self_concern uses for
            # promoted_to/about_message -- graph data with no admissibility
            # grammar declared for it yet).
            substrate.add_edge_unchecked(agent, "has_engineering_residual", nid)
        upserted.append({"outcome": outcome, "count": count,
                         "population_key": pop_key})

    zeroed = []
    for outcome, nid in existing.items():
        if outcome not in seen:
            substrate.set_attr(nid, "count", 0)
            substrate.set_attr(nid, "task_ids", [])
            substrate.set_attr(nid, "measured_at", measured_at)
            zeroed.append(outcome)

    substrate.tick()
    return {"source_script": source_script, "upserted": upserted,
            "zeroed_absent": zeroed, "measured_at": measured_at}


def load_or_boot_residual_substrate(checkpoint_path: str = DEFAULT_CHECKPOINT):
    """Returns (substrate, agent_node): ALWAYS a freshly seed-loaded
    WorldAdapter (`WorldAdapter(seeds=()) + load_all_seeds` -- the
    tests/test_gap_awareness_migrated.py fixture's own pattern), so
    seeds/engineering_residual_gap.json's RULES are always current.

    Measured (this rung): `Substrate.graph_to_dict()` carries only
    `{nodes, edges, next_id}` -- NO `rules` key -- so a raw
    `graph_from_dict` reload silently drops every Rule node, exactly the
    checkpoint-resume rule-loss residual CLAUDE.md already names for the
    real jabberwock daemon (`_reconcile_seed_rules`). A prior version of
    this function used graph_from_dict directly and the retire rule
    measurably never fired again after one save/reload cycle -- caught by
    this rung's own live-verify, not assumed away.

    The fix here is RECONCILE, not reload: boot fresh (rules current), then
    re-materialise only the persisted `EngineeringResidual` facts and
    `engineering_residual`-kind `SelfConcern`s from the checkpoint (if any)
    BY CONTENT, via `_reconcile_residual_state` below -- the
    `_reconcile_seed_typed_nodes` find-or-create-by-content precedent,
    scoped to the two node types and three edge types this seed's own
    rules read."""
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    s, agent = a.s, a.agent
    if os.path.exists(checkpoint_path):
        with open(checkpoint_path) as f:
            d = json.load(f)
        _reconcile_residual_state(s, agent, d)
    return s, agent


def _reconcile_residual_state(substrate, agent, checkpoint_dict: dict) -> None:
    """Re-materialise persisted EngineeringResidual / engineering_residual
    SelfConcern nodes (+ their has_engineering_residual / has_self_concern /
    about_residual edges) from a graph_to_dict()-shaped dict onto a
    freshly-booted substrate, mapping old node ids to newly-allocated ones.
    Mechanical re-add, no decision -- the seed's own rules re-derive
    everything else (dedup/mint/retire) on the next tick()."""
    old_nodes = {n["id"]: n for n in checkpoint_dict.get("nodes", [])}
    id_map: dict[int, Any] = {}
    for old_id, n in old_nodes.items():
        if n.get("type") == "EngineeringResidual":
            nid = substrate.add_node("EngineeringResidual", dict(n.get("attrs", {})))
            id_map[old_id] = nid
            substrate.add_edge_unchecked(agent, "has_engineering_residual", nid)
    for old_id, n in old_nodes.items():
        if n.get("type") == "SelfConcern" and n.get("attrs", {}).get("kind") == "engineering_residual":
            at = dict(n.get("attrs", {}))
            nid = substrate.add_node("SelfConcern", at)
            id_map[old_id] = nid
            if at.get("status") != "retired":
                substrate.add_edge_unchecked(agent, "has_self_concern", nid)
    for e in checkpoint_dict.get("edges", []):
        if e.get("type") == "about_residual" and e.get("src") in id_map and e.get("tgt") in id_map:
            substrate.add_edge_unchecked(id_map[e["src"]], "about_residual", id_map[e["tgt"]])


def save_residual_substrate(substrate, agent, checkpoint_path: str = DEFAULT_CHECKPOINT) -> None:
    """Mechanical I/O: write the SMALL, filtered subset `_reconcile_residual_
    state` above knows how to read back -- EngineeringResidual nodes,
    engineering_residual-kind SelfConcern nodes, and their
    has_engineering_residual / has_self_concern / about_residual edges --
    not a full `graph_to_dict()` of the whole seed-booted graph (every
    caller re-derives the rest via a fresh `load_all_seeds` boot in
    `load_or_boot_residual_substrate`, so persisting it twice would only
    bloat the file with data no reader of this checkpoint needs)."""
    os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
    agent_id = agent.value if hasattr(agent, "value") else agent
    full = substrate.graph_to_dict()
    keep_types = {"EngineeringResidual"}
    nodes = []
    keep_ids = set()
    for n in full.get("nodes", []):
        if n.get("type") in keep_types or (
            n.get("type") == "SelfConcern"
            and n.get("attrs", {}).get("kind") == "engineering_residual"
        ):
            nodes.append(n)
            keep_ids.add(n["id"])
    edges = [e for e in full.get("edges", [])
             if e.get("type") in ("has_engineering_residual", "has_self_concern",
                                  "about_residual")
             and e.get("tgt") in keep_ids
             and (e.get("src") in keep_ids or e.get("src") == agent_id)]
    d = {"nodes": nodes, "edges": edges}
    with open(checkpoint_path, "w") as f:
        json.dump(d, f, default=str)
