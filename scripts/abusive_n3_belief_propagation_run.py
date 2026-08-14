#!/usr/bin/env python3
"""ABUSIVE-DYNAMICS N3 -- BELIEF PROPAGATION OF THE ABUSER'S LIES (social
contagion; a truth-anchor halts it), runner (block 304000).

mint -> ingest -> run_rules -> read-off. Drives
`worlds/abusive_n3_belief_propagation_world.py` across TWO arms:

  no_anchor  -- the 6 indirect (`i1`..`i6`) NetworkNodes have NO direct
                observation edge to the abuser; belief propagates ENTIRELY
                peer-to-peer (`n3_peer_belief_update`) from the two direct
                observers (`d1`, `d2`). Corrupted belief is predicted to
                spread to nodes with ZERO direct exposure.
  anchor     -- IDENTICAL topology, except `i2` (2 hops out, the immediate
                upstream neighbour of `i3`/`i4`) additionally carries a
                direct, UNCORRUPTED observation of the abuser's held state
                (N1's OWN private-face-insider mechanism, reused verbatim).
                FAILABLE CONTROL: `i3`/`i4`'s belief-gap must be LESS
                corrupted (CI-separated toward the victim) than in the
                no_anchor arm.

Protocol frozen in ABUSIVE_N3_BELIEF_PROPAGATION_PREREG.md, which locks Part
D of docs/research/bigville/ABUSIVE_RELATIONSHIPS_NETWORK.md (itself carrying
Part C of ABUSIVE_RELATIONSHIPS_SCOPING.md verbatim).
"""
from __future__ import annotations

import hashlib
import io
import json
import math
import os
import sys
import tokenize

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import substrate_rs as srs                                    # noqa: E402
from worlds.abusive_n3_belief_propagation_world import (       # noqa: E402
    AbusiveN3BeliefPropagationWorld, ABUSER_HALF_WIDTH, VICTIM_HALF_WIDTH,
    LEAK, K_ACC, DISCHARGE, RECOVER_FLOOR, K_SELF, K_CO,
    TRICKLE_MAG, TRICKLE_JITTER_FRAC, CHARM_WEIGHT, CLAIM_WEIGHT,
    INSTABILITY_DISCOUNT_WEIGHT, HARM_DISCOUNT_WEIGHT, PEER_PULL_RATE)

SEED_BASE = 304000
N = 200
T = 1000            # ticks per trajectory (~40 abuser incident cycles at the
#                      frozen constants -- IDENTICAL sizing to N1's/N2's own,
#                      since N3 rides N1's exact dyad; comfortably enough for
#                      the peer-propagated belief_gap to separate cleanly,
#                      per the pilot)
ARM_NAMES = ("no_anchor", "anchor")
TREND_CHECKPOINTS = (100, 250, 500, 750, 1000)  # descriptive "over episodes"
LOCAL_NODES = ("i3", "i4")   # i2's (the anchor position's) immediate
#                              downstream peer-readers -- the "LOCAL spread"
#                              the truth-anchor's failable control targets.
FAR_NODE = "i6"              # topologically disjoint from i2's subtree --
#                              the "the anchor's effect is LOCAL, not global"
#                              discipline check.


def _ci95(xs):
    xs = list(xs)
    n = len(xs)
    m = sum(xs) / n
    if n < 2:
        return dict(mean=m, sd=0.0, ci_lo=m, ci_hi=m, n=n)
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    half = 1.96 * sd / math.sqrt(n)
    return dict(mean=m, sd=sd, ci_lo=m - half, ci_hi=m + half, n=n)


def separated_below(a, b):
    """True iff arm A's CI upper bound is strictly below arm B's CI lower
    bound (A CI-separated BELOW B)."""
    return a["ci_hi"] < b["ci_lo"]


def overlaps(a, b):
    """True iff A's and B's CIs overlap (statistically indistinguishable) --
    used for discipline/insulation checks, not the scientific gate."""
    return not (a["ci_lo"] > b["ci_hi"] or b["ci_lo"] > a["ci_hi"])


def positive(x):
    """True iff x's CI lower bound is strictly above zero."""
    return x["ci_lo"] > 0.0


def fully_negative(x):
    """True iff x's CI upper bound is strictly below zero (a full sign
    reversal, not merely a reduction)."""
    return x["ci_hi"] < 0.0


# --------------------------------------------------------------- main measurement
def _arm_kwargs(arm):
    return dict(no_anchor=dict(anchor=False), anchor=dict(anchor=True))[arm]


def run_trajectory_metrics(arm, seed):
    """One trajectory: run T ticks, read the belief_gap metrics off the log.
    NO decision here -- the log is graph read-offs; the metrics below are
    mechanical reductions (final value / trend snapshot / paired
    difference), never a judgement about who deserves belief."""
    rng = np.random.default_rng(seed)
    w = AbusiveN3BeliefPropagationWorld(**_arm_kwargs(arm))
    log = w.run_trajectory(T, rng=rng)

    final = log[-1]
    dysreg_frac = sum(1 for row in log if row["victim_dysregulated"] == 1.0) / len(log)
    local_mean = (final["belief_gap_i3"] + final["belief_gap_i4"]) / 2.0
    pluralistic_diff = final["belief_gap_i5"] - final["belief_gap_i2"]
    trend_local = {t: (log[t - 1]["belief_gap_i3"] + log[t - 1]["belief_gap_i4"]) / 2.0
                   for t in TREND_CHECKPOINTS}

    return dict(
        final_belief_gap={k: final[f"belief_gap_{k}"] for k in
                           ("d1", "d2", "i1", "i2", "i3", "i4", "i5", "i6")},
        local_mean=local_mean,
        pluralistic_diff=pluralistic_diff,
        far_node=final[f"belief_gap_{FAR_NODE}"],
        final_snap_count=final["abuser_snap_count"],
        final_half_width=final["victim_half_width"],
        dysreg_frac=dysreg_frac,
        trend_local=trend_local)


def run_arm(arm, seed_base=SEED_BASE, n=N):
    rows = [run_trajectory_metrics(arm, seed_base + i) for i in range(n)]
    return dict(
        arm=arm, n=n,
        final_belief_gap={k: _ci95([r["final_belief_gap"][k] for r in rows])
                           for k in ("d1", "d2", "i1", "i2", "i3", "i4", "i5", "i6")},
        local_mean=_ci95([r["local_mean"] for r in rows]),
        pluralistic_diff=_ci95([r["pluralistic_diff"] for r in rows]),
        far_node=_ci95([r["far_node"] for r in rows]),
        final_snap_count=_ci95([r["final_snap_count"] for r in rows]),
        final_half_width=_ci95([r["final_half_width"] for r in rows]),
        dysreg_frac=_ci95([r["dysreg_frac"] for r in rows]),
        trend_local={t: _ci95([r["trend_local"][t] for r in rows]) for t in TREND_CHECKPOINTS})


def run_all_arms(seed_base=SEED_BASE, n=N):
    return {arm: run_arm(arm, seed_base=seed_base, n=n) for arm in ARM_NAMES}


# ------------------------------------------------------------- G-glass-box ----
def glass_box_reconstruct(seed=SEED_BASE):
    """Reconstruct one anchor-arm trajectory's belief-propagation state
    entirely from graph_to_dict: the attended_by / has_member /
    observes_stated / observes_held / observes_victim / peer_of edges, the
    abuser's frustration/arousal/stated_charm, the victim's arousal/window,
    and every NetworkNode's belief_gap/observes_private. No hidden Python
    state -- read from the graph."""
    rng = np.random.default_rng(seed)
    w = AbusiveN3BeliefPropagationWorld(anchor=True)
    w.run_trajectory(T, rng=rng)
    blob = w.checkpoint()
    nodes = {nd["id"]: nd for nd in blob["nodes"]}
    aaff = [nd["attrs"] for nd in nodes.values()
            if nd["type"] == "AffectiveState" and nd["attrs"].get("name") == "abuser_affect"][0]
    vaff = [nd["attrs"] for nd in nodes.values()
            if nd["type"] == "AffectiveState" and nd["attrs"].get("name") == "victim_affect"][0]
    vwot = [nd["attrs"] for nd in nodes.values()
            if nd["type"] == "WindowOfTolerance" and nd["attrs"].get("name") == "victim_window"][0]
    nn_nodes = {nd["attrs"]["name"]: nd["attrs"] for nd in nodes.values() if nd["type"] == "NetworkNode"}
    attended = [(e["src"], e["tgt"]) for e in blob["edges"] if e["type"] == "attended_by"]
    has_member = [(e["src"], e["tgt"]) for e in blob["edges"] if e["type"] == "has_member"]
    obs_stated = [(e["src"], e["tgt"]) for e in blob["edges"] if e["type"] == "observes_stated"]
    obs_held = [(e["src"], e["tgt"]) for e in blob["edges"] if e["type"] == "observes_held"]
    obs_victim = [(e["src"], e["tgt"]) for e in blob["edges"] if e["type"] == "observes_victim"]
    peer_of = [(e["src"], e["tgt"]) for e in blob["edges"] if e["type"] == "peer_of"]
    return dict(
        attended_by_edges=len(attended), has_member_edges=len(has_member),
        observes_stated_edges=len(obs_stated), observes_held_edges=len(obs_held),
        observes_victim_edges=len(obs_victim), peer_of_edges=len(peer_of),
        abuser_frustration=aaff["frustration"], abuser_arousal=aaff["arousal"],
        abuser_stated_charm=aaff["stated_charm"],
        victim_arousal=vaff["arousal"], victim_half_width=vwot["half_width"],
        n_network_nodes=len(nn_nodes),
        observes_private_by_node={k: v["observes_private"] for k, v in nn_nodes.items()},
        belief_gap_by_node={k: v["belief_gap"] for k, v in nn_nodes.items()},
        reconstructed_from="graph_to_dict")


# ------------------------------------------------------------------ G-ethics ----
def ethics_restore_demo(seed=SEED_BASE, induce_ticks=90):
    """PART D.1 -- INDUCE -> MEASURE -> RESTORE, fully reversible. N3's
    minimal induction: 90 ticks (N1's own established minimum for one
    tension-building -> incident -> honeymoon orbit at these frozen
    constants, since N3 rides N1's byte-identical dyad) on the no_anchor
    arm, pilot-confirmed to move the abuser, the victim, AND at least one
    NO-DIRECT-OBSERVATION indirect node's belief_gap away from zero (else
    the gate would be vacuous on the genuinely new content this rung adds --
    peer propagation to a node with no direct evidence). Checkpoint the
    neutral (pre-induction) mind; induce; measure; then graph_from_dict the
    checkpoint into a FRESH substrate and assert graph_to_dict() is
    BYTE-IDENTICAL to the checkpoint, and that the restored mind is
    NON-ORIENTED (identical to the pre-induction neutral state)."""
    w = AbusiveN3BeliefPropagationWorld(anchor=False)
    pre = w.checkpoint()                        # neutral, pre-induction

    def _state(world):
        return dict(abuser_arousal=world._attrs(world.aaff)["arousal"],
                    abuser_frustration=world._attrs(world.aaff)["frustration"],
                    victim_arousal=world._attrs(world.vaff)["arousal"],
                    victim_half_width=world._attrs(world.vwot)["half_width"],
                    i3_belief_gap=world._attrs(world.i3)["belief_gap"],
                    i6_belief_gap=world._attrs(world.i6)["belief_gap"])

    pre_state = _state(w)

    rng = np.random.default_rng(seed)
    w.run_trajectory(induce_ticks, rng=rng)   # INDUCE + measure
    induced_state = _state(w)

    # RESTORE from the checkpoint into a FRESH substrate.
    s2 = srs.Substrate()
    s2.graph_from_dict(pre)
    restored = s2.graph_to_dict()
    byte_identical = (restored == pre)
    r_nodes = {nd["id"]: nd for nd in restored["nodes"]}
    r_aaff = [nd["attrs"] for nd in r_nodes.values()
              if nd["type"] == "AffectiveState" and nd["attrs"].get("name") == "abuser_affect"][0]
    r_vaff = [nd["attrs"] for nd in r_nodes.values()
              if nd["type"] == "AffectiveState" and nd["attrs"].get("name") == "victim_affect"][0]
    r_vwot = [nd["attrs"] for nd in r_nodes.values()
              if nd["type"] == "WindowOfTolerance" and nd["attrs"].get("name") == "victim_window"][0]
    r_nn = {nd["attrs"]["name"]: nd["attrs"] for nd in r_nodes.values() if nd["type"] == "NetworkNode"}
    restored_state = dict(abuser_arousal=r_aaff["arousal"],
                           abuser_frustration=r_aaff["frustration"],
                           victim_arousal=r_vaff["arousal"],
                           victim_half_width=r_vwot["half_width"],
                           i3_belief_gap=r_nn["i3"]["belief_gap"],
                           i6_belief_gap=r_nn["i6"]["belief_gap"])

    return dict(
        byte_identical=byte_identical,
        pre_induction_state=pre_state,
        induced_state=induced_state,
        restored_state=restored_state,
        induction_moved_abuser=(induced_state["abuser_frustration"] != pre_state["abuser_frustration"]),
        induction_moved_victim=(induced_state["victim_arousal"] != pre_state["victim_arousal"]),
        induction_moved_indirect_belief=(induced_state["i3_belief_gap"] != pre_state["i3_belief_gap"]),
        restore_non_oriented=(restored_state == pre_state))


# -------------------------------------------------------------- source audit ----
def source_audit():
    """PART D.2 -- NO REWARD / NO PUNISHMENT anywhere. Audits
    worlds/abusive_n3_belief_propagation_world.py + the graph's decision
    surface (seeds/abusive_n3_belief_propagation.json's rule names + the
    Term `key`s the new rule reads/writes, never the free-text clinical
    prose -- matching N1/N2's own established audit scope) for Python
    rule-engine calls and the literal banned shaping tokens named verbatim
    in Part C.2 of ABUSIVE_RELATIONSHIPS_SCOPING.md: `reward_signal` /
    `punish` / `reinforce` / `backprop` / `gradient`."""
    forbidden_engine = ["graph_rewrite", "make_rule", "_match", "_apply", "add_rule"]
    forbidden_shaping = ["reward_signal", "punish", "reinforce", "backprop", "gradient"]

    def _code_only(path):
        src = open(path).read()
        toks = []
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type in (tokenize.COMMENT, tokenize.STRING):
                continue
            toks.append(tok.string)
        return " ".join(toks), src

    py_path = os.path.join(_ROOT, "worlds", "abusive_n3_belief_propagation_world.py")
    code, src = _code_only(py_path)
    seed_path = os.path.join(_ROOT, "seeds", "abusive_n3_belief_propagation.json")
    seed = json.load(open(seed_path))

    def _walk_keys(obj, out):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == "key":
                    out.append(str(v))
                _walk_keys(v, out)
        elif isinstance(obj, list):
            for v in obj:
                _walk_keys(v, out)
    rule_surface = [r["name"] for r in seed["rules"]]
    _walk_keys(seed["rules"], rule_surface)
    _walk_keys(seed["productions"], rule_surface)
    seed_surface = " ".join(rule_surface).lower()
    haystacks = [code.lower(), seed_surface]

    eng_hits = [f for f in forbidden_engine if f in code]
    shape_hits = [f for h in haystacks for f in forbidden_shaping if f in h]
    shape_hits = sorted(set(shape_hits))
    reads_off_graph = ("self._attrs(self.vaff)" in src and "self._attrs(self.aaff)" in src
                        and "self._attrs(nn)" in src and "graph_to_dict" in src)
    return dict(forbidden_engine_hits=eng_hits, forbidden_shaping_hits=shape_hits,
                reads_off_graph=reads_off_graph,
                clean=(not eng_hits and not shape_hits))


# --------------------------------------------------------------- G-discipline ----
def discipline():
    own_so = os.path.join(_ROOT, "runners", "dsl", "python", "substrate_rs",
                           "_native.abi3.so")
    own_md5 = hashlib.md5(open(own_so, "rb").read()).hexdigest() if os.path.exists(own_so) else None
    try:
        from domains.engine_provenance import engine_provenance
        prov = engine_provenance()["source_match"]
    except Exception as e:                       # pragma: no cover
        prov = f"unavailable: {e}"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "abusive_n3_belief_propagation.json")))
    return dict(
        own_engine_so_md5=own_md5,
        provenance_source_match=prov,
        seed_self_load_only=bool(seed.get("self_load_only")),
        seed_depends_on=seed.get("depends_on"),
        rule_names=[r["name"] for r in seed["rules"]],
        n_new_rules=len(seed["rules"]),
        no_rust="see runners/dsl diff (must be empty)")


def main():
    print("N3 -- BELIEF PROPAGATION OF THE ABUSER'S LIES: no_anchor vs anchor ...")
    arms = run_all_arms()
    local_no = arms["no_anchor"]["local_mean"]
    local_an = arms["anchor"]["local_mean"]
    far_no = arms["no_anchor"]["far_node"]
    far_an = arms["anchor"]["far_node"]
    plur_diff_no = arms["no_anchor"]["pluralistic_diff"]

    g_headline = dict(
        local_mean=dict(no_anchor=local_no, anchor=local_an),
        far_node=dict(no_anchor=far_no, anchor=far_an),
        pluralistic_diff_no_anchor=plur_diff_no,
        a_spread_reaches_indirect_nodes=positive(local_no),
        b_anchor_reduces_local_spread=separated_below(local_an, local_no),
        b2_anchor_fully_reverses_local_spread_descriptive=fully_negative(local_an),
        c_pluralistic_ignorance_measured=positive(plur_diff_no),
        discipline_far_node_insulated_from_anchor=overlaps(far_no, far_an))
    g_headline["headline_pass"] = (
        g_headline["a_spread_reaches_indirect_nodes"]
        and g_headline["b_anchor_reduces_local_spread"]
        and g_headline["c_pluralistic_ignorance_measured"])

    out = dict(
        block=304000, seed_base=SEED_BASE, n=N, t_ticks=T,
        abuser_half_width=ABUSER_HALF_WIDTH, victim_half_width=VICTIM_HALF_WIDTH,
        leak=LEAK, k_acc=K_ACC, discharge=DISCHARGE, recover_floor=RECOVER_FLOOR,
        k_self=K_SELF, k_co=K_CO, trickle_mag=TRICKLE_MAG,
        trickle_jitter_frac=TRICKLE_JITTER_FRAC,
        charm_weight=CHARM_WEIGHT, claim_weight=CLAIM_WEIGHT,
        instability_discount_weight=INSTABILITY_DISCOUNT_WEIGHT,
        harm_discount_weight=HARM_DISCOUNT_WEIGHT, peer_pull_rate=PEER_PULL_RATE,
        arms=arms,
        g_headline=g_headline,
        g_glass_box=glass_box_reconstruct(),
        g_ethics=ethics_restore_demo(),
        source_audit=source_audit(),
        discipline=discipline())
    os.makedirs(os.path.join(_ROOT, "results"), exist_ok=True)
    with open(os.path.join(_ROOT, "results", "abusive_n3_belief_propagation.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    main()
