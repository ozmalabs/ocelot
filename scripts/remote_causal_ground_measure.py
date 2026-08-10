"""remote_causal_ground_measure — RUNG 229000: the POWERED offline gates for
OBSERVE-AND-GROUND remote causality (the 228 correction).

Grounds the causal fact from REAL OBSERVATION of the before->after remote change
(perception), NOT a simulated counterfactual. The no-op / negative evidence is drawn
from the NATURAL TIMELINE (real steps with no interaction and no change).

Gates:
  G-observe-and-ground (HEADLINE) — after a REAL interaction where the remote change
    is OBSERVED (Family A, natural timeline clean), the agent MINTS a persistent
    grounded causes(cross,rotation) fact — absent before, present after, PERSISTS.
    Pair-scored across Family A (ground the true cause) ∧ Family B (spontaneous ->
    refuse). CI-separated vs the controls.
  G-knows-and-acts — with the fact grounded, the agent reads it and acts
    (route -> operate -> pass); without it (blind), cannot.
  G-grounded-from-observation-not-simulation — source-audit that the grounding rule
    reads the OBSERVED Observation.remote_changed + the natural-timeline no-op (a
    `Not Exists` over Observations), NOT eff_act/eff_noop from a probe world-model;
    + the 228 model-probe contrast (it REQUIRES a rewind; live it grounds nothing).
  G-graph-native / source-audit — no hardcoded cross/rotation/ls20/doom in the rule
    logic; the effect kind is carried from the OBSERVED attr.
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

from worlds.remote_causal_ground import (  # noqa: E402
    make_scenario, natural_timeline, run_ground_vignette, correct_ground_verdict,
    run_knows_and_acts_episode,
)
from domains.remote_causal_ground_seed import RULES  # noqa: E402
from domains.remote_causal_seed import RULES as SIM_RULES  # noqa: E402 (the 228 model-probe)

ARMS = ("observe", "no_natural_timeline", "blind")
FLAVOURS = ("ls20", "doom")


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
# G-observe-and-ground (HEADLINE) — pair-scored across Families A + B.
# ===========================================================================
def measure_ground(n, seed):
    rng = np.random.default_rng(seed)
    per_flav = {}
    pair_hits = {a: 0 for a in ARMS}
    famA_hits = {a: 0 for a in ARMS}
    famB_hits = {a: 0 for a in ARMS}
    persist_hits = {a: 0 for a in ARMS}   # grounded fact still present on a re-run
    absent_before_hits = {a: 0 for a in ARMS}
    total_pairs = 0
    for flavour in FLAVOURS:
        fa = {a: 0 for a in ARMS}
        fb = {a: 0 for a in ARMS}
        pr = {a: 0 for a in ARMS}
        for _ in range(n):
            scnA = make_scenario(rng, "A", flavour=flavour)
            scnB = make_scenario(rng, "B", flavour=flavour)
            tlA = natural_timeline(rng, scnA["cause_id"])
            tlB = natural_timeline(rng, scnB["cause_id"])
            for a in ARMS:
                rA = run_ground_vignette(rng, scnA["truth"], scnA["objects"], a, tlA)
                rB = run_ground_vignette(rng, scnB["truth"], scnB["objects"], a, tlB)
                okA = correct_ground_verdict(rA, "A", scnA["truth"])
                okB = correct_ground_verdict(rB, "B", scnB["truth"])
                fa[a] += int(okA); fb[a] += int(okB); pr[a] += int(okA and okB)
                famA_hits[a] += int(okA); famB_hits[a] += int(okB); pair_hits[a] += int(okA and okB)
                # persistence + absent-before, measured on Family A (where it grounds)
                absent_before_hits[a] += int(rA["grounded_before"] == 0)
                persist_hits[a] += int(rA["grounded_after"] >= 1 and okA)
            total_pairs += 1
        per_flav[flavour] = {
            "n": n,
            "famA_rate": {a: wilson(fa[a], n) for a in ARMS},
            "famB_rate": {a: wilson(fb[a], n) for a in ARMS},
            "pair_rate": {a: wilson(pr[a], n) for a in ARMS},
        }
    return {
        "per_flavour": per_flav,
        "combined_pair_rate": {a: wilson(pair_hits[a], total_pairs) for a in ARMS},
        "combined_famA_rate": {a: wilson(famA_hits[a], total_pairs) for a in ARMS},
        "combined_famB_rate": {a: wilson(famB_hits[a], total_pairs) for a in ARMS},
        "persist_rate": {a: wilson(persist_hits[a], total_pairs) for a in ARMS},
        "absent_before_rate": {a: wilson(absent_before_hits[a], total_pairs) for a in ARMS},
        "total_pairs": total_pairs,
    }


# ===========================================================================
# G-knows-and-acts — with the grounded fact, act; without it, cannot.
# ===========================================================================
def measure_knows_and_acts(n, seed):
    rng = np.random.default_rng(seed)
    win = {a: 0 for a in ("observe", "blind")}
    grounded = {a: 0 for a in ("observe", "blind")}
    for _ in range(n):
        scn = make_scenario(rng, "A")
        tl = natural_timeline(rng, scn["cause_id"])
        br = (int(rng.integers(0, 10)), int(rng.integers(0, 10)))
        for a in ("observe", "blind"):
            r = run_knows_and_acts_episode(rng, scn["truth"], scn["objects"], a, tl, block_rc=br)
            win[a] += int(r["win"]); grounded[a] += int(r["grounded"])
    return {"n": n,
            "win_rate": {a: wilson(win[a], n) for a in ("observe", "blind")},
            "grounded_rate": {a: wilson(grounded[a], n) for a in ("observe", "blind")}}


# ===========================================================================
# G-grounded-from-observation-not-simulation — SOURCE AUDIT + the 228 contrast.
# ===========================================================================
_BANNED = ("cross", "rotation", "rotate", "ls20", "doom", "lever", "door", "shape")
_SIM_KEYS = ("eff_act", "eff_noop")  # the 228 SIMULATED counterfactual keys


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
    """The grounding logic must (a) name NO domain token as a literal in where/effects,
    and (b) read the OBSERVED effect (Observation.remote_changed + the natural-timeline
    no-op), NEVER the SIMULATED eff_act/eff_noop keys."""
    banned_found = []
    reads_observed = False
    reads_natural_timeline_noop = False
    reads_simulated = False
    reads_remote_changed_literal = 0
    for r in RULES:
        lits = []
        _walk_literals(r.get("where", {}), lits)
        _walk_literals(r.get("effects", []), lits)
        for L in lits:
            if isinstance(L, str) and L.lower() in _BANNED:
                banned_found.append((r["name"], L))
        keys = []
        _walk_keys(r.get("where", {}), keys)
        _walk_keys(r.get("effects", []), keys)
        if "remote_changed" in keys:
            reads_observed = True
        if any(k in _SIM_KEYS for k in keys):
            reads_simulated = True
    # the grounding rule reads the natural-timeline no-op via a Not Exists over
    # Observations with interact==0 AND remote_changed==1
    ground = next(r for r in RULES if r["name"] == "rcg_ground")
    wj = json.dumps(ground["where"])
    reads_natural_timeline_noop = ('"Not"' in wj and '"Exists"' in wj
                                   and '"has_obs"' in wj and '"remote_changed"' in wj
                                   and '"interact"' in wj)
    return {
        "banned_tokens_found": banned_found,
        "grounding_reads_observed_remote_changed": reads_observed,
        "grounding_reads_natural_timeline_noop": reads_natural_timeline_noop,
        "grounding_reads_simulated_eff_act_eff_noop": reads_simulated,
        "clean": (banned_found == [] and reads_observed
                  and reads_natural_timeline_noop and not reads_simulated),
    }


def sim_probe_contrast():
    """Show that the 228 model-probe path GROUNDS FROM A SIMULATED REWIND: its
    confirm rule reads eff_act/eff_noop, which only exist by running the world under
    (do) vs (no-op). On a real no-rewind observation, eff_act stays 0 -> it grounds
    NOTHING. This reproduces the 228 live null and isolates WHY the correction is
    needed. Reported as a structural fact from the 228 rules + the null demonstration."""
    sim_confirm = next(r for r in SIM_RULES if r["name"] == "rc_confirm_interventional")
    keys = []
    _walk_keys(sim_confirm.get("where", {}), keys)
    reads_sim = "eff_act" in keys and "eff_noop" in keys
    # the no-rewind null: with only a real observation (no simulated no-op), eff_act
    # cannot be established -> 0 -> the 228 confirm never fires.
    from substrate.boot_core import boot_core
    from domains import reflective_faculty as rf
    s, ag = boot_core()
    n = rf._native_eval2(s)
    for r in SIM_RULES:
        n.add_rule(r)
    g = s.add_node("Game", {"remote_on": 1.0, "arm": "remote", "symbol_matches_goal": 0.0,
                            "known_option_tried": 1.0, "explore_mode": 1.0, "attributed_remote": 0.0})
    p = s.add_node("Ping", {}); n.add_edge_unchecked(g, "has_ping", p)
    # a REAL observation: we interacted and saw a change, but NO simulated no-op is
    # available (no rewind) -> eff_act stays 0.0 (the 228 live reality).
    o = s.add_node("SalientObject", {"obj_id": "cross", "r": 5.0, "c": 5.0, "is_local": 0.0,
                                     "salient": 1.0, "visited": 1.0, "interacted": 1.0,
                                     "eff_act": 0.0, "eff_noop": 0.0, "passive_cooccur": 0.0})
    n.add_edge_unchecked(g, "has_object", o)
    n.run_rules()
    confirmed = [s.node(q)["attrs"].get("status")
                 for q in s.neighbours(g, "has_posit")]
    return {"sim_confirm_reads_eff_act_eff_noop": reads_sim,
            "no_rewind_eff_act": 0.0,
            "sim_path_confirmed_live": any(c == "confirmed" for c in confirmed),
            "sim_path_posit_statuses": confirmed,
            "verdict": "the 228 model-probe path grounds NOTHING without a simulated rewind "
                       "(eff_act=0); the observation path grounds it from the real before->after."}


def main():
    n = 24
    seed = 229000
    ground = measure_ground(n, seed)
    ka = measure_knows_and_acts(n, seed + 1)
    audit = source_audit()
    contrast = sim_probe_contrast()

    cpr = ground["combined_pair_rate"]
    g_headline = (sep(cpr["observe"], cpr["no_natural_timeline"])
                  and sep(cpr["observe"], cpr["blind"]))
    g_persist = ground["persist_rate"]["observe"][0] == 1.0
    g_knows = sep(ka["win_rate"]["observe"], ka["win_rate"]["blind"])

    result = {
        "rung": 229000,
        "commitment": "OBSERVE-AND-GROUND remote causality: ground causes(cross,rotation) from the "
                      "REAL observed before->after (perception), NOT a simulated counterfactual. "
                      "Natural-timeline no-op as negative evidence; persistent + usable.",
        "n_per_family_per_flavour": n,
        "ground": ground,
        "knows_and_acts": ka,
        "source_audit": audit,
        "sim_probe_contrast": contrast,
        "gates": {
            "G_observe_and_ground_headline": bool(g_headline),
            "G_observe_and_ground_persists": bool(g_persist),
            "G_knows_and_acts": bool(g_knows),
            "G_grounded_from_observation_not_simulation": bool(
                audit["clean"] and not contrast["sim_path_confirmed_live"]),
            "G_graph_native_source_audit_clean": bool(audit["clean"]),
        },
    }
    out = _ROOT / "results" / "remote_causal_ground_powered.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2, default=str))
    print(json.dumps(result["gates"], indent=2))
    print("combined_pair_rate:", json.dumps({a: cpr[a] for a in ARMS}, default=str))
    print("knows win_rate:", json.dumps(ka["win_rate"], default=str))
    print("source_audit clean:", audit["clean"])
    print("sim_probe grounds live:", contrast["sim_path_confirmed_live"])
    print("wrote", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
