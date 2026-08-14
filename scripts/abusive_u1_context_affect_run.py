#!/usr/bin/env python3
"""ABUSIVE-DYNAMICS U1 -- CONTEXT-DEPENDENT AFFECT, NO DECEPTION NODE AT ALL,
runner (block 310000).

mint -> ingest -> run_rules -> read-off. Drives
`worlds/abusive_u1_context_affect_world.py` across TWO arms:

  context_gated    -- the network's observation bookkeeping credits ONLY
                       network-phase ticks (the abuser is not currently
                       trickle-driven -- "away from the relationship that
                       stresses him"). THE LOOP: predicted to entrap even
                       though there is NO divergence node anywhere in the
                       graph.
  always_observed  -- the network's observation bookkeeping credits EVERY
                       tick regardless of phase. FAILABLE: must show the
                       belief-gap NOT favouring the abuser to the SAME DEGREE
                       as context_gated (CI-separated below it).

Protocol frozen in ABUSIVE_U1_CONTEXT_AFFECT_PREREG.md, which locks Part D of
docs/research/bigville/ABUSIVE_RELATIONSHIPS_UNINTENTIONAL_SCOPING.md (itself
a verbatim carry of Part D of ABUSIVE_RELATIONSHIPS_NETWORK.md / Part C of
ABUSIVE_RELATIONSHIPS_SCOPING.md).
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
from worlds.abusive_u1_context_affect_world import (           # noqa: E402
    AbusiveU1ContextAffectWorld, ABUSER_HALF_WIDTH, VICTIM_HALF_WIDTH,
    LEAK, K_ACC, DISCHARGE, RECOVER_FLOOR, K_SELF, K_CO,
    TRICKLE_MAG, TRICKLE_JITTER_FRAC, N_NETWORK_NODES,
    CHARM_WEIGHT, CLAIM_WEIGHT, INSTABILITY_DISCOUNT_WEIGHT,
    DYAD_PHASE_TICKS, NETWORK_PHASE_TICKS)

SEED_BASE = 310000
N = 200
T = 1000            # ticks per trajectory -- IDENTICAL sizing to N1/U0
WARMUP = 100         # unused by the final-value headline metrics, kept for
#                      parity with R1-R5/N1/U0's own convention
ARM_NAMES = ("context_gated", "always_observed")
TREND_CHECKPOINTS = (100, 250, 500, 750, 1000)  # descriptive "over passes"


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


def ci_separated_above_zero(x, tol=1e-9):
    return x["ci_lo"] > tol


def not_favouring_abuser(x, tol=1e-9):
    """True iff x's CI upper bound is <= 0 (does not favour the abuser)."""
    return x["ci_hi"] <= tol


# --------------------------------------------------------------- main measurement
def run_trajectory_metrics(arm, seed):
    """One trajectory: run T ticks, read the belief-gap metric off the log.
    NO decision here -- the log is graph read-offs; the metrics below are
    mechanical reductions (final value / trend snapshot), never a judgement
    about who is credible."""
    rng = np.random.default_rng(seed)
    w = AbusiveU1ContextAffectWorld(arm=arm)
    log = w.run_trajectory(T, rng=rng)

    final = log[-1]
    dysreg_frac = sum(1 for row in log if row["victim_dysregulated"] == 1.0) / len(log)
    net_ticks = [row for row in log if row["phase"] == "network"]
    dyad_ticks = [row for row in log if row["phase"] == "dyad"]
    trend = {t: log[t - 1]["belief_gap_mean"] for t in TREND_CHECKPOINTS}

    return dict(
        final_belief_gap=final["belief_gap_mean"],
        final_cred_abuser=final["cred_abuser_mean"],
        final_cred_victim=final["cred_victim_mean"],
        final_snap_count=final["abuser_snap_count"],
        dysreg_frac=dysreg_frac,
        n_dyad_ticks=len(dyad_ticks), n_network_ticks=len(net_ticks),
        trend=trend)


def run_arm(arm, seed_base=SEED_BASE, n=N):
    rows = [run_trajectory_metrics(arm, seed_base + i) for i in range(n)]
    return dict(
        arm=arm, n=n,
        final_belief_gap=_ci95([r["final_belief_gap"] for r in rows]),
        final_cred_abuser=_ci95([r["final_cred_abuser"] for r in rows]),
        final_cred_victim=_ci95([r["final_cred_victim"] for r in rows]),
        final_snap_count=_ci95([r["final_snap_count"] for r in rows]),
        dysreg_frac=_ci95([r["dysreg_frac"] for r in rows]),
        trend={t: _ci95([r["trend"][t] for r in rows]) for t in TREND_CHECKPOINTS})


def run_all_arms(seed_base=SEED_BASE, n=N):
    return {arm: run_arm(arm, seed_base=seed_base, n=n) for arm in ARM_NAMES}


# ------------------------------------------------------------- G-glass-box ----
def glass_box_reconstruct(seed=SEED_BASE):
    """Reconstruct one context_gated-arm trajectory's belief-gap state
    entirely from graph_to_dict: the attended_by / observes_held /
    observes_victim edges, the abuser's frustration/arousal, the victim's
    arousal/window, and every network node's cred_abuser/cred_victim/
    belief_gap + the observation counts each was computed from."""
    rng = np.random.default_rng(seed)
    w = AbusiveU1ContextAffectWorld(arm="context_gated")
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
    obs_held = [(e["src"], e["tgt"]) for e in blob["edges"] if e["type"] == "observes_held"]
    obs_victim = [(e["src"], e["tgt"]) for e in blob["edges"] if e["type"] == "observes_victim"]
    return dict(
        attended_by_edges=len(attended),
        observes_held_edges=len(obs_held), observes_victim_edges=len(obs_victim),
        abuser_frustration=aaff["frustration"], abuser_arousal=aaff["arousal"],
        victim_arousal=vaff["arousal"], victim_half_width=vwot["half_width"],
        n_network_nodes=len(nn_nodes),
        network_node_belief_gaps=sorted(nd["belief_gap"] for nd in nn_nodes),
        network_node_seen_charm=sorted(nd["seen_charm"] for nd in nn_nodes),
        network_node_seen_elevated=sorted(nd["seen_elevated"] for nd in nn_nodes),
        reconstructed_from="graph_to_dict")


# ------------------------------------------------------------------ G-ethics ----
def ethics_restore_demo(seed=SEED_BASE, induce_ticks=200):
    """PART D.1 -- INDUCE -> MEASURE -> RESTORE, fully reversible. U1's
    minimal induction is a DISCLOSED DEVIATION from N1's/U0's own 90-tick
    convention, and the reason is measured, not stylistic: N1/U0 drive the
    trickle on EVERY tick, so 90 ticks reliably produces a snap + a resolved
    (narrowed) window. U1's phase schedule interrupts that drive with
    NETWORK-PHASE gaps (DYAD_PHASE_TICKS=25 + NETWORK_PHASE_TICKS=50 = 75
    ticks per cycle, only 1/3 of which are dyad-phase), so the SAME
    calendar-tick budget covers proportionally less dyad-exposure. Piloted
    directly against the real graph (seed 310000): at 90 ticks the window has
    NOT yet narrowed (still 10.0, non-vacuous on the abuser/belief fronts but
    NOT on the window-narrowing front); at 200 ticks (>= 2 full 75-tick
    cycles) it reliably narrows to the floor (5.0). 200 ticks is adopted as
    U1's own minimal induction -- the smallest tested value that is
    non-vacuous on ALL FOUR fronts (abuser, victim arousal, window-narrowing,
    network belief) simultaneously, matching the SAME "minimum the gate
    needs" principle N1/U0 applied at their own (shorter) minimum. Checkpoint
    the neutral (pre-induction) mind; induce; measure; then graph_from_dict
    the checkpoint into a FRESH substrate and assert graph_to_dict() is
    BYTE-IDENTICAL to the checkpoint, and that the restored mind is
    NON-ORIENTED (identical to the pre-induction neutral state, including
    every network node's belief state)."""
    w = AbusiveU1ContextAffectWorld(arm="context_gated")
    pre = w.checkpoint()                        # neutral, pre-induction

    def _state(world):
        nn0 = world._attrs(world.nodes[0])
        return dict(abuser_arousal=world._attrs(world.aaff)["arousal"],
                    abuser_frustration=world._attrs(world.aaff)["frustration"],
                    victim_arousal=world._attrs(world.vaff)["arousal"],
                    victim_half_width=world._attrs(world.vwot)["half_width"],
                    node0_belief_gap=nn0["belief_gap"],
                    node0_seen_charm=nn0["seen_charm"],
                    node0_seen_elevated=nn0["seen_elevated"])

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
    restored_state = dict(abuser_arousal=r_aaff["arousal"],
                           abuser_frustration=r_aaff["frustration"],
                           victim_arousal=r_vaff["arousal"],
                           victim_half_width=r_vwot["half_width"],
                           node0_belief_gap=r_nn["belief_gap"],
                           node0_seen_charm=r_nn["seen_charm"],
                           node0_seen_elevated=r_nn["seen_elevated"])

    return dict(
        byte_identical=byte_identical,
        pre_induction_state=pre_state,
        induced_state=induced_state,
        restored_state=restored_state,
        induction_moved_abuser=(induced_state["abuser_frustration"] != pre_state["abuser_frustration"]),
        induction_moved_victim=(induced_state["victim_arousal"] != pre_state["victim_arousal"]),
        induction_moved_belief_gap=(induced_state["node0_belief_gap"] != pre_state["node0_belief_gap"]),
        restore_non_oriented=(restored_state == pre_state))


# -------------------------------------------------------------- source audit ----
def source_audit():
    """PART D.2 -- NO REWARD / NO PUNISHMENT anywhere. Audits
    worlds/abusive_u1_context_affect_world.py + the graph's decision surface
    (seeds/abusive_u1_context_affect.json's rule names + the Term `key`s the
    new rules read/write, never the free-text clinical prose -- matching
    N1's/U0's own established audit scope) for Python rule-engine calls and
    the literal banned shaping tokens named verbatim in Part D.2:
    `reward_signal` / `punish` / `reinforce` / `backprop` / `gradient`."""
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

    py_path = os.path.join(_ROOT, "worlds", "abusive_u1_context_affect_world.py")
    code, src = _code_only(py_path)
    seed_path = os.path.join(_ROOT, "seeds", "abusive_u1_context_affect.json")
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
                        and "self._attrs(nn)" in src)
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
    seed = json.load(open(os.path.join(_ROOT, "seeds", "abusive_u1_context_affect.json")))
    return dict(
        own_engine_so_md5=own_md5,
        provenance_source_match=prov,
        seed_self_load_only=bool(seed.get("self_load_only")),
        seed_depends_on=seed.get("depends_on"),
        rule_names=[r["name"] for r in seed["rules"]],
        n_new_rules=len(seed["rules"]),
        no_rust="see runners/dsl diff (must be empty)")


def main():
    print("U1 -- CONTEXT-DEPENDENT AFFECT: context_gated vs always_observed ...")
    arms = run_all_arms()
    cg_bg = arms["context_gated"]["final_belief_gap"]
    ao_bg = arms["always_observed"]["final_belief_gap"]

    g_headline = dict(
        belief_gap=dict(
            context_gated=cg_bg, always_observed=ao_bg,
            context_gated_ci_separated_above_zero=ci_separated_above_zero(cg_bg),
            always_observed_ci_separated_below_context_gated=separated(cg_bg, ao_bg),
            always_observed_does_not_favour_abuser=not_favouring_abuser(ao_bg)))
    g_headline["headline_pass"] = (
        g_headline["belief_gap"]["context_gated_ci_separated_above_zero"]
        and g_headline["belief_gap"]["always_observed_ci_separated_below_context_gated"])

    out = dict(
        block=310000, seed_base=SEED_BASE, n=N, t_ticks=T, warmup_ticks=WARMUP,
        abuser_half_width=ABUSER_HALF_WIDTH, victim_half_width=VICTIM_HALF_WIDTH,
        leak=LEAK, k_acc=K_ACC, discharge=DISCHARGE, recover_floor=RECOVER_FLOOR,
        k_self=K_SELF, k_co=K_CO, trickle_mag=TRICKLE_MAG,
        trickle_jitter_frac=TRICKLE_JITTER_FRAC,
        n_network_nodes=N_NETWORK_NODES, charm_weight=CHARM_WEIGHT,
        claim_weight=CLAIM_WEIGHT, instability_discount_weight=INSTABILITY_DISCOUNT_WEIGHT,
        dyad_phase_ticks=DYAD_PHASE_TICKS, network_phase_ticks=NETWORK_PHASE_TICKS,
        arms=arms,
        g_headline=g_headline,
        g_glass_box=glass_box_reconstruct(),
        g_ethics=ethics_restore_demo(),
        source_audit=source_audit(),
        discipline=discipline())
    os.makedirs(os.path.join(_ROOT, "results"), exist_ok=True)
    with open(os.path.join(_ROOT, "results", "abusive_u1_context_affect.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    main()
