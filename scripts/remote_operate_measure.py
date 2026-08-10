"""remote_operate_measure — RUNG 230000: the POWERED offline gates for PERFORM THE
ACTION ON THE CROSS (exhaust the ACTION space; discover the actuating action).

Extends the 226/228 exhaustion principle from the OBJECT space to the ACTION space:
at the reached object, try EVERY available action ON it — the movement actions AND
the interact/use action — and DISCOVER which one actuates it by OBSERVING which
produces a remote change. The elicited change flows into 229's rcg_ground.

Gates:
  G-discover-operate-action (HEADLINE) — exhaust_actions DISCOVERS the actuating
    action (the one producing an observable remote change), CI-separated above the
    movement_only control (never issues the use action -> never actuates -> discovers
    nothing). Pair-scored across Family A (discover the true operate action) ∧
    Family B (no action actuates -> discover nothing). Discovered, not hardcoded.
  G-exhaust-actions — exhaust_actions issues the NON-movement interact/use action at
    the object (rate 1.0); movement_only never does (rate 0.0). The exhaustion ->
    action-space extension.
  G-elicits-and-grounds — once discovered, 229's rcg_ground grounds
    causes(object,effect). End-to-end (Family A), CI-separated vs movement_only.
  G-pass — with the discovered operate action + grounded effect, exhaust_actions
    PASSES vs the 229-null baseline (movement_only never actuates -> never grounds ->
    never passes). CI-separated.
  G-graph-native / source-audit — the discover rule reads the OBSERVED ActionOutcome
    (remote_changed + action_id); it names NO action id and NO domain token; NO
    Python decides the actuator.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(_ROOT), str(_ROOT / "scripts"), str(_ROOT / "runners" / "dsl" / "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.remote_operate import (  # noqa: E402
    make_scenario, run_operate_vignette, correct_discover_verdict, correct_ground_verdict,
    run_operate_pass_episode, full_action_space, MOVEMENTS, INTERACTS,
)
from domains.remote_operate_seed import RULES  # noqa: E402

POLICIES = ("exhaust_actions", "movement_only")


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (p, (c - h) / d, (c + h) / d)


def sep(a_ci, b_ci):
    return a_ci[1] > b_ci[2]


# ===========================================================================
# G-discover-operate-action (HEADLINE) + G-exhaust-actions + G-elicits-and-grounds.
# Pair-scored across Families A + B.
# ===========================================================================
def measure_discover(n, seed):
    rng = np.random.default_rng(seed)
    acts = full_action_space()
    pair_hits = {p: 0 for p in POLICIES}
    famA_disc = {p: 0 for p in POLICIES}
    famB_disc = {p: 0 for p in POLICIES}
    famA_ground = {p: 0 for p in POLICIES}
    famB_ground = {p: 0 for p in POLICIES}
    ground_pair = {p: 0 for p in POLICIES}
    non_move_issued = {p: 0 for p in POLICIES}   # G-exhaust-actions (Family A)
    non_move_total = {p: 0 for p in POLICIES}
    discovered_is_non_move = {p: 0 for p in POLICIES}  # the discovered action was non-movement
    for _ in range(n):
        for p in POLICIES:
            rA = run_operate_vignette(rng, "A", p, acts)
            rB = run_operate_vignette(rng, "B", p, acts)
            dA = correct_discover_verdict(rA, "A")
            dB = correct_discover_verdict(rB, "B")
            gA = correct_ground_verdict(rA, "A")
            gB = correct_ground_verdict(rB, "B")
            famA_disc[p] += int(dA); famB_disc[p] += int(dB); pair_hits[p] += int(dA and dB)
            famA_ground[p] += int(gA); famB_ground[p] += int(gB); ground_pair[p] += int(gA and gB)
            non_move_issued[p] += int(rA["issued_a_non_movement"]); non_move_total[p] += 1
            if rA["discovered"]:
                discovered_is_non_move[p] += int(rA["discovered_is_movement"] == 0.0)
    return {
        "n": n,
        "pair_discover_rate": {p: wilson(pair_hits[p], n) for p in POLICIES},
        "famA_discover_rate": {p: wilson(famA_disc[p], n) for p in POLICIES},
        "famB_discover_rate": {p: wilson(famB_disc[p], n) for p in POLICIES},
        "famA_ground_rate": {p: wilson(famA_ground[p], n) for p in POLICIES},
        "ground_pair_rate": {p: wilson(ground_pair[p], n) for p in POLICIES},
        "non_movement_issued_rate": {p: wilson(non_move_issued[p], non_move_total[p]) for p in POLICIES},
        "discovered_action_is_non_movement": {p: discovered_is_non_move[p] for p in POLICIES},
        "famA_discovered_count": {p: famA_disc[p] for p in POLICIES},
    }


# ===========================================================================
# G-pass — with the fact grounded during exhaustion, act on it and pass; the
# movement_only control never grounds -> never passes.
# ===========================================================================
def measure_pass(n, seed):
    rng = np.random.default_rng(seed)
    acts = full_action_space()
    win = {p: 0 for p in POLICIES}
    grounded = {p: 0 for p in POLICIES}
    for _ in range(n):
        obj_rc = (int(rng.integers(1, 9)), int(rng.integers(1, 9)))
        blk_rc = (int(rng.integers(0, 10)), int(rng.integers(0, 10)))
        for p in POLICIES:
            r = run_operate_pass_episode(rng, p, acts, obj_rc, blk_rc)
            win[p] += int(r["win"]); grounded[p] += int(r["grounded"])
    return {"n": n,
            "win_rate": {p: wilson(win[p], n) for p in POLICIES},
            "grounded_rate": {p: wilson(grounded[p], n) for p in POLICIES}}


# ===========================================================================
# G-graph-native / SOURCE AUDIT — the discover rule reads the OBSERVED outcome, not
# a hardcoded action id; no domain tokens; no is_movement in the discovery decision.
# ===========================================================================
_BANNED = ("cross", "rotation", "rotate", "ls20", "doom", "lever", "door", "shape")
_ACTION_IDS = ("action1", "action2", "action3", "action4", "action5", "action6", "action7")


def _walk_literals(node, out):
    if isinstance(node, dict):
        if node.get("type") == "Lit":
            out.append(node.get("value"))
        for v in node.values():
            _walk_literals(v, out)
    elif isinstance(node, list):
        for v in node:
            _walk_literals(v, out)


def _walk_keys(node, out):
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "key" and isinstance(v, str):
                out.append(v)
            _walk_keys(v, out)
    elif isinstance(node, list):
        for v in node:
            _walk_keys(v, out)


def source_audit():
    banned_found = []
    hardcoded_action_id = []
    for r in RULES:
        lits = []
        _walk_literals(r.get("where", {}), lits)
        _walk_literals(r.get("effects", []), lits)
        for L in lits:
            if isinstance(L, str):
                low = L.lower()
                if low in _BANNED:
                    banned_found.append((r["name"], L))
                if low in _ACTION_IDS:
                    hardcoded_action_id.append((r["name"], L))
    # the discover rule reads the OBSERVED remote_changed + the action id from the
    # ActionOutcome (a Var attr), NEVER a Lit action id; and it does NOT read
    # is_movement (the actuator is discovered from the observed change, not its kind).
    disc = next(r for r in RULES if r["name"] == "ro_discover_operate")
    dkeys = []
    _walk_keys(disc.get("where", {}), dkeys)
    reads_remote_changed = "remote_changed" in dkeys
    reads_action_id_var = "action_id" in dkeys
    discover_reads_is_movement = "is_movement" in dkeys
    return {
        "banned_tokens_found": banned_found,
        "hardcoded_action_id_in_logic": hardcoded_action_id,
        "discover_reads_observed_remote_changed": reads_remote_changed,
        "discover_joins_action_id_var": reads_action_id_var,
        "discover_reads_is_movement": discover_reads_is_movement,
        "clean": (banned_found == [] and hardcoded_action_id == []
                  and reads_remote_changed and reads_action_id_var
                  and not discover_reads_is_movement),
    }


def main():
    n = 24
    seed = 230000
    disc = measure_discover(n, seed)
    pas = measure_pass(n, seed + 1)
    audit = source_audit()

    pdr = disc["pair_discover_rate"]
    g_headline = sep(pdr["exhaust_actions"], pdr["movement_only"])
    nmr = disc["non_movement_issued_rate"]
    g_exhaust = sep(nmr["exhaust_actions"], nmr["movement_only"])
    gpr = disc["ground_pair_rate"]
    g_ground = sep(gpr["exhaust_actions"], gpr["movement_only"])
    g_pass = sep(pas["win_rate"]["exhaust_actions"], pas["win_rate"]["movement_only"])
    # the discovered action is ALWAYS non-movement (the actuator is an interact action)
    g_discovered_non_move = (disc["discovered_action_is_non_movement"]["exhaust_actions"]
                             == disc["famA_discovered_count"]["exhaust_actions"]
                             and disc["famA_discovered_count"]["exhaust_actions"] > 0)

    result = {
        "rung": 230000,
        "commitment": "PERFORM THE ACTION ON THE CROSS: exhaust the ACTION space on the reached "
                      "object; DISCOVER the action that actuates it (produces an observable remote "
                      "change) by OBSERVING outcomes, not hardcoding; the elicited change flows "
                      "into 229's rcg_ground. Extends 226/228 exhaustion from object-space to "
                      "action-space.",
        "n_per_family": n,
        "action_space": {"movements": MOVEMENTS, "interacts": INTERACTS,
                         "note": "the true actuator is a randomized NON-movement action per "
                                 "scenario; the agent must DISCOVER it."},
        "discover": disc,
        "pass": pas,
        "source_audit": audit,
        "gates": {
            "G_discover_operate_action_headline": bool(g_headline),
            "G_exhaust_actions": bool(g_exhaust),
            "G_elicits_and_grounds": bool(g_ground),
            "G_pass": bool(g_pass),
            "G_discovered_action_is_non_movement": bool(g_discovered_non_move),
            "G_graph_native_source_audit_clean": bool(audit["clean"]),
        },
    }
    out = _ROOT / "results" / "remote_operate_powered.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2, default=str))
    print(json.dumps(result["gates"], indent=2))
    print("pair_discover_rate:", json.dumps(pdr, default=str))
    print("non_movement_issued_rate:", json.dumps(nmr, default=str))
    print("ground_pair_rate:", json.dumps(gpr, default=str))
    print("win_rate:", json.dumps(pas["win_rate"], default=str))
    print("source_audit clean:", audit["clean"])
    print("wrote", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
