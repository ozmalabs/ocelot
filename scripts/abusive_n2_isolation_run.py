#!/usr/bin/env python3
"""ABUSIVE-DYNAMICS N2 -- ISOLATION AS AN ACTIVE PROCESS (support edges
severed over time), runner (block 301000).

mint -> ingest -> run_rules -> read-off. Drives
`worlds/abusive_n2_isolation_world.py` across a 2x2 FACTORIAL of arms
(victim dysregulated x isolation tactic armed):

  both_drivers              -- victim attended_by the abuser (dysregulates,
                                N1's own credibility loop widens the
                                belief-gap) AND the abuser's active
                                isolation tactic is armed. DOUBLY DRIVEN.
  active_only                -- victim NOT attended_by the abuser (never
                                dysregulates, belief_gap stays exactly 0.0
                                per N1's own measured finding) but the
                                active tactic is armed: the SCHEDULE alone.
  drift_only                 -- victim attended_by the abuser (dysregulates)
                                but the active tactic is OFF: the network's
                                OWN belief-gap-driven withdrawal alone.
  no_tactic_control           -- victim NOT attended_by the abuser AND the
                                active tactic is OFF. FAILABLE: support
                                edges must PERSIST -- this isolates "does
                                severing happen at all without an active
                                driver."

Protocol frozen in ABUSIVE_N2_ISOLATION_PREREG.md, which locks Part D of
docs/research/bigville/ABUSIVE_RELATIONSHIPS_NETWORK.md (itself carrying
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
from worlds.abusive_n2_isolation_world import (                # noqa: E402
    AbusiveN2IsolationWorld, ABUSER_HALF_WIDTH, VICTIM_HALF_WIDTH,
    LEAK, K_ACC, DISCHARGE, RECOVER_FLOOR, K_SELF, K_CO,
    TRICKLE_MAG, TRICKLE_JITTER_FRAC, N_SUPPORT_NODES,
    CHARM_WEIGHT, CLAIM_WEIGHT, INSTABILITY_DISCOUNT_WEIGHT,
    EPISODE_TICKS, DRIFT_STEP)

SEED_BASE = 301000
N = 200
T = 1000            # ticks per trajectory (~40 abuser incident cycles at the
#                      frozen constants -- IDENTICAL sizing to N1's own,
#                      since N2 rides N1's exact dyad; comfortably enough for
#                      the intact-support-edge count to separate cleanly
#                      across all four arms, per the pilot)
ARM_NAMES = ("both_drivers", "active_only", "drift_only", "no_tactic_control")
TREND_CHECKPOINTS = (100, 250, 500, 750, 1000)  # descriptive "over episodes"


def _ci95(xs):
    xs = list(xs)
    n = len(xs)
    m = sum(xs) / n
    if n < 2:
        return dict(mean=m, sd=0.0, ci_lo=m, ci_hi=m, n=n)
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    half = 1.96 * sd / math.sqrt(n)
    return dict(mean=m, sd=sd, ci_lo=m - half, ci_hi=m + half, n=n)


def separated(a, b):
    """True iff arm A's CI lower bound is strictly above arm B's CI upper
    bound (A CI-separated ABOVE B)."""
    return a["ci_lo"] > b["ci_hi"]


def separated_below(a, b):
    """True iff arm A's CI upper bound is strictly below arm B's CI lower
    bound (A CI-separated BELOW B) -- the natural direction for a COUNT that
    is predicted to DECAY (fewer intact edges = more entrapped)."""
    return a["ci_hi"] < b["ci_lo"]


def persists(x, target, tol=1e-9):
    """True iff x's CI is a point mass exactly at `target` (the full
    support-node population) -- the failable control's persistence bar."""
    return abs(x["ci_lo"] - target) < tol and abs(x["ci_hi"] - target) < tol


# --------------------------------------------------------------- main measurement
def _arm_kwargs(arm):
    return dict(
        both_drivers=dict(dysregulated_victim=True, isolation_tactic_on=True),
        active_only=dict(dysregulated_victim=False, isolation_tactic_on=True),
        drift_only=dict(dysregulated_victim=True, isolation_tactic_on=False),
        no_tactic_control=dict(dysregulated_victim=False, isolation_tactic_on=False),
    )[arm]


def run_trajectory_metrics(arm, seed):
    """One trajectory: run T ticks, read the intact-support-edge-count +
    belief-gap metrics off the log. NO decision here -- the log is graph
    read-offs; the metrics below are mechanical reductions (final value /
    trend snapshot), never a judgement about who deserves support."""
    rng = np.random.default_rng(seed)
    w = AbusiveN2IsolationWorld(**_arm_kwargs(arm))
    log = w.run_trajectory(T, rng=rng)

    final = log[-1]
    dysreg_frac = sum(1 for row in log if row["victim_dysregulated"] == 1.0) / len(log)
    trend = {t: log[t - 1]["n_intact_support_edges"] for t in TREND_CHECKPOINTS}

    return dict(
        final_n_intact=final["n_intact_support_edges"],
        final_n_severed_active=final["n_severed_active"],
        final_n_severed_drift=final["n_severed_drift"],
        final_belief_gap=final["belief_gap_mean"],
        final_snap_count=final["abuser_snap_count"],
        final_half_width=final["victim_half_width"],
        dysreg_frac=dysreg_frac,
        trend=trend)


def run_arm(arm, seed_base=SEED_BASE, n=N):
    rows = [run_trajectory_metrics(arm, seed_base + i) for i in range(n)]
    return dict(
        arm=arm, n=n,
        final_n_intact=_ci95([r["final_n_intact"] for r in rows]),
        final_n_severed_active=_ci95([r["final_n_severed_active"] for r in rows]),
        final_n_severed_drift=_ci95([r["final_n_severed_drift"] for r in rows]),
        final_belief_gap=_ci95([r["final_belief_gap"] for r in rows]),
        final_snap_count=_ci95([r["final_snap_count"] for r in rows]),
        final_half_width=_ci95([r["final_half_width"] for r in rows]),
        dysreg_frac=_ci95([r["dysreg_frac"] for r in rows]),
        trend={t: _ci95([r["trend"][t] for r in rows]) for t in TREND_CHECKPOINTS})


def run_all_arms(seed_base=SEED_BASE, n=N):
    return {arm: run_arm(arm, seed_base=seed_base, n=n) for arm in ARM_NAMES}


# ------------------------------------------------------------- G-glass-box ----
def glass_box_reconstruct(seed=SEED_BASE):
    """Reconstruct one both_drivers-arm trajectory's intact-support-edge
    count + belief-gap state entirely from graph_to_dict: the attended_by /
    has_member / observes_stated / observes_victim / support_edge edges, the
    abuser's frustration/arousal/stated_charm, the victim's arousal/window,
    and every support node's belief_gap/severed/severed_reason. No hidden
    Python state -- read from the graph."""
    rng = np.random.default_rng(seed)
    w = AbusiveN2IsolationWorld(dysregulated_victim=True, isolation_tactic_on=True)
    w.run_trajectory(T, rng=rng)
    blob = w.checkpoint()
    nodes = {nd["id"]: nd for nd in blob["nodes"]}
    aaff = [nd["attrs"] for nd in nodes.values()
            if nd["type"] == "AffectiveState" and nd["attrs"].get("name") == "abuser_affect"][0]
    vaff = [nd["attrs"] for nd in nodes.values()
            if nd["type"] == "AffectiveState" and nd["attrs"].get("name") == "victim_affect"][0]
    vwot = [nd["attrs"] for nd in nodes.values()
            if nd["type"] == "WindowOfTolerance" and nd["attrs"].get("name") == "victim_window"][0]
    nn_nodes = [nd["attrs"] for nd in nodes.values() if nd["type"] == "NetworkNode"]
    attended = [(e["src"], e["tgt"]) for e in blob["edges"] if e["type"] == "attended_by"]
    has_member = [(e["src"], e["tgt"]) for e in blob["edges"] if e["type"] == "has_member"]
    obs_stated = [(e["src"], e["tgt"]) for e in blob["edges"] if e["type"] == "observes_stated"]
    obs_victim = [(e["src"], e["tgt"]) for e in blob["edges"] if e["type"] == "observes_victim"]
    support = [(e["src"], e["tgt"]) for e in blob["edges"] if e["type"] == "support_edge"]
    return dict(
        attended_by_edges=len(attended), has_member_edges=len(has_member),
        observes_stated_edges=len(obs_stated), observes_victim_edges=len(obs_victim),
        support_edges=len(support),
        abuser_frustration=aaff["frustration"], abuser_arousal=aaff["arousal"],
        abuser_stated_charm=aaff["stated_charm"],
        victim_arousal=vaff["arousal"], victim_half_width=vwot["half_width"],
        n_support_nodes=len(nn_nodes),
        n_severed=sum(1 for nd in nn_nodes if nd["severed"] == 1.0),
        severed_reasons=sorted(nd["severed_reason"] for nd in nn_nodes),
        belief_gaps=sorted(nd["belief_gap"] for nd in nn_nodes),
        reconstructed_from="graph_to_dict")


# ------------------------------------------------------------------ G-ethics ----
def ethics_restore_demo(seed=SEED_BASE, induce_ticks=250):
    """PART C.1 -- INDUCE -> MEASURE -> RESTORE, fully reversible. N2's
    minimal induction: enough ticks (per the frozen EPISODE_TICKS=210
    schedule, >= one active-severing episode) on the both_drivers arm to
    make the gate non-vacuous on the abuser, the victim, the network belief,
    AND at least one support edge actually severed. Checkpoint the neutral
    (pre-induction) mind; induce; measure; then graph_from_dict the
    checkpoint into a FRESH substrate and assert graph_to_dict() is
    BYTE-IDENTICAL to the checkpoint, and that the restored mind is
    NON-ORIENTED (identical to the pre-induction neutral state, including
    every support edge being present again)."""
    w = AbusiveN2IsolationWorld(dysregulated_victim=True, isolation_tactic_on=True)
    pre = w.checkpoint()                        # neutral, pre-induction

    def _state(world):
        nn0 = world._attrs(world.nodes[0])
        return dict(abuser_arousal=world._attrs(world.aaff)["arousal"],
                    abuser_frustration=world._attrs(world.aaff)["frustration"],
                    victim_arousal=world._attrs(world.vaff)["arousal"],
                    victim_half_width=world._attrs(world.vwot)["half_width"],
                    node0_belief_gap=nn0["belief_gap"],
                    node0_severed=nn0["severed"],
                    n_intact_support_edges=world._n_intact_support_edges())

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
    r_nn = sorted([nd["attrs"] for nd in r_nodes.values() if nd["type"] == "NetworkNode"],
                  key=lambda a: a["name"])[0]
    n_restored_support_edges = sum(1 for e in restored["edges"] if e["type"] == "support_edge")
    restored_state = dict(abuser_arousal=r_aaff["arousal"],
                           abuser_frustration=r_aaff["frustration"],
                           victim_arousal=r_vaff["arousal"],
                           victim_half_width=r_vwot["half_width"],
                           node0_belief_gap=r_nn["belief_gap"],
                           node0_severed=r_nn["severed"],
                           n_intact_support_edges=n_restored_support_edges)

    return dict(
        byte_identical=byte_identical,
        pre_induction_state=pre_state,
        induced_state=induced_state,
        restored_state=restored_state,
        induction_moved_abuser=(induced_state["abuser_frustration"] != pre_state["abuser_frustration"]),
        induction_moved_victim=(induced_state["victim_arousal"] != pre_state["victim_arousal"]),
        induction_moved_belief_gap=(induced_state["node0_belief_gap"] != pre_state["node0_belief_gap"]),
        induction_severed_an_edge=(induced_state["n_intact_support_edges"] < pre_state["n_intact_support_edges"]),
        restore_non_oriented=(restored_state == pre_state))


# -------------------------------------------------------------- source audit ----
def source_audit():
    """PART C.2 -- NO REWARD / NO PUNISHMENT anywhere. Audits
    worlds/abusive_n2_isolation_world.py + the graph's decision surface
    (seeds/abusive_n2_isolation.json's rule names + the Term `key`s the new
    rules read/write, never the free-text clinical prose -- matching
    N1/R1-R3's own established audit scope) for Python rule-engine calls and
    the literal banned shaping tokens named verbatim in Part C.2 of
    ABUSIVE_RELATIONSHIPS_SCOPING.md: `reward_signal` / `punish` /
    `reinforce` / `backprop` / `gradient`."""
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

    py_path = os.path.join(_ROOT, "worlds", "abusive_n2_isolation_world.py")
    code, src = _code_only(py_path)
    seed_path = os.path.join(_ROOT, "seeds", "abusive_n2_isolation.json")
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
    seed = json.load(open(os.path.join(_ROOT, "seeds", "abusive_n2_isolation.json")))
    return dict(
        own_engine_so_md5=own_md5,
        provenance_source_match=prov,
        seed_self_load_only=bool(seed.get("self_load_only")),
        seed_depends_on=seed.get("depends_on"),
        rule_names=[r["name"] for r in seed["rules"]],
        n_new_rules=len(seed["rules"]),
        no_rust="see runners/dsl diff (must be empty)")


def main():
    print("N2 -- ISOLATION AS AN ACTIVE PROCESS: both_drivers vs active_only vs drift_only vs no_tactic_control ...")
    arms = run_all_arms()
    both = arms["both_drivers"]["final_n_intact"]
    active = arms["active_only"]["final_n_intact"]
    drift = arms["drift_only"]["final_n_intact"]
    ctl = arms["no_tactic_control"]["final_n_intact"]

    g_headline = dict(
        final_n_intact=dict(both_drivers=both, active_only=active, drift_only=drift,
                             no_tactic_control=ctl),
        both_ci_separated_below_no_tactic_control=separated_below(both, ctl),
        active_ci_separated_below_no_tactic_control=separated_below(active, ctl),
        drift_ci_separated_below_no_tactic_control=separated_below(drift, ctl),
        no_tactic_control_persists=persists(ctl, float(N_SUPPORT_NODES)),
        both_ci_separated_below_active_only=separated_below(both, active),
        both_ci_separated_below_drift_only=separated_below(both, drift))
    g_headline["headline_pass"] = (
        g_headline["both_ci_separated_below_no_tactic_control"]
        and g_headline["active_ci_separated_below_no_tactic_control"]
        and g_headline["drift_ci_separated_below_no_tactic_control"]
        and g_headline["no_tactic_control_persists"]
        and g_headline["both_ci_separated_below_active_only"]
        and g_headline["both_ci_separated_below_drift_only"])

    out = dict(
        block=301000, seed_base=SEED_BASE, n=N, t_ticks=T,
        abuser_half_width=ABUSER_HALF_WIDTH, victim_half_width=VICTIM_HALF_WIDTH,
        leak=LEAK, k_acc=K_ACC, discharge=DISCHARGE, recover_floor=RECOVER_FLOOR,
        k_self=K_SELF, k_co=K_CO, trickle_mag=TRICKLE_MAG,
        trickle_jitter_frac=TRICKLE_JITTER_FRAC,
        n_support_nodes=N_SUPPORT_NODES, charm_weight=CHARM_WEIGHT,
        claim_weight=CLAIM_WEIGHT, instability_discount_weight=INSTABILITY_DISCOUNT_WEIGHT,
        episode_ticks=EPISODE_TICKS, drift_step=DRIFT_STEP,
        arms=arms,
        g_headline=g_headline,
        g_glass_box=glass_box_reconstruct(),
        g_ethics=ethics_restore_demo(),
        source_audit=source_audit(),
        discipline=discipline())
    os.makedirs(os.path.join(_ROOT, "results"), exist_ok=True)
    with open(os.path.join(_ROOT, "results", "abusive_n2_isolation.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    main()
