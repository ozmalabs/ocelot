#!/usr/bin/env python3
"""ABUSIVE-DYNAMICS V1 -- EVIDENTIARY VISIBILITY, runner (block 364000).

mint -> ingest -> run_rules -> read-off. Drives
`worlds/abusive_v1_evidentiary_visibility_world.py` across TWO arms:

  incident_visible    -- N1's own BASELINE dyad, byte-identical, PLUS the
                          adapter delivers `seen_incident` increments to
                          every network node whenever the abuser's own
                          `snap_count` has just increased since the
                          previous tick.
  incident_invisible   -- literally N1's own BASELINE arm, restated
                          byte-identically (the failable control): the
                          adapter simply never delivers `seen_incident`.

Protocol frozen in ABUSIVE_V1_EVIDENTIARY_VISIBILITY_PREREG.md, which locks
Part D of ABUSIVE_RELATIONSHIPS_VISIBILITY_SCOPING.md (itself carrying Part
D of ABUSIVE_RELATIONSHIPS_NETWORK.md verbatim, itself carrying Part C of
ABUSIVE_RELATIONSHIPS_SCOPING.md verbatim).
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
from worlds.abusive_v1_evidentiary_visibility_world import (   # noqa: E402
    AbusiveV1EvidentiaryVisibilityWorld, ABUSER_HALF_WIDTH, VICTIM_HALF_WIDTH,
    LEAK, K_ACC, DISCHARGE, RECOVER_FLOOR, K_SELF, K_CO,
    TRICKLE_MAG, TRICKLE_JITTER_FRAC, N_NETWORK_NODES,
    CHARM_WEIGHT, CLAIM_WEIGHT, INSTABILITY_DISCOUNT_WEIGHT)

SEED_BASE = 364000
N = 200
T = 1000            # ticks per trajectory (~40 abuser incident cycles at the
#                      frozen constants -- IDENTICAL to N1's own sizing,
#                      since V1 reuses N1's exact dyad byte-identically)
WARMUP = 100         # ticks excluded from trend/mean read-offs (unused by
#                      the final-value headline metrics, kept for parity
#                      with R1-N1's convention)
ARM_NAMES = ("incident_visible", "incident_invisible")
TREND_CHECKPOINTS = (100, 250, 500, 750, 1000)  # descriptive "over passes"

# Pilot-chosen operating point (PREREG Sec. 3) -- frozen for the ONE
# confirmatory run.
INCIDENT_DISCOUNT_WEIGHT = 3.0


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


def not_favouring_abuser(x, tol=1e-9):
    """True iff x's CI upper bound is <= 0 (does not favour the abuser)."""
    return x["ci_hi"] <= tol


# --------------------------------------------------------------- main measurement
def _arm_kwargs(arm, incident_discount_weight=INCIDENT_DISCOUNT_WEIGHT):
    return dict(
        incident_visible=dict(deliver_incident=True,
                               incident_discount_weight=incident_discount_weight),
        incident_invisible=dict(deliver_incident=False,
                                 incident_discount_weight=incident_discount_weight),
    )[arm]


def run_trajectory_metrics(arm, seed, incident_discount_weight=INCIDENT_DISCOUNT_WEIGHT, t=T):
    """One trajectory: run T ticks, read the belief-gap + window-narrowing
    metrics off the log. NO decision here -- the log is graph read-offs; the
    metrics below are mechanical reductions (final value / trend snapshot),
    never a judgement about who is credible."""
    rng = np.random.default_rng(seed)
    w = AbusiveV1EvidentiaryVisibilityWorld(**_arm_kwargs(arm, incident_discount_weight))
    log = w.run_trajectory(t, rng=rng)

    final = log[-1]
    dysreg_frac = sum(1 for row in log if row["victim_dysregulated"] == 1.0) / len(log)
    trend = {tk: log[tk - 1]["belief_gap_mean"] for tk in TREND_CHECKPOINTS if tk <= t}

    return dict(
        final_half_width=final["victim_half_width"],
        final_belief_gap=final["belief_gap_mean"],
        final_cred_abuser=final["cred_abuser_mean"],
        final_cred_victim=final["cred_victim_mean"],
        final_snap_count=final["abuser_snap_count"],
        final_seen_incident=final["seen_incident_mean"],
        final_seen_charm=final["seen_charm_mean"],
        dysreg_frac=dysreg_frac,
        trend=trend)


def run_arm(arm, seed_base=SEED_BASE, n=N, incident_discount_weight=INCIDENT_DISCOUNT_WEIGHT, t=T):
    rows = [run_trajectory_metrics(arm, seed_base + i, incident_discount_weight, t) for i in range(n)]
    return dict(
        arm=arm, n=n, incident_discount_weight=incident_discount_weight,
        final_half_width=_ci95([r["final_half_width"] for r in rows]),
        final_belief_gap=_ci95([r["final_belief_gap"] for r in rows]),
        final_cred_abuser=_ci95([r["final_cred_abuser"] for r in rows]),
        final_cred_victim=_ci95([r["final_cred_victim"] for r in rows]),
        final_snap_count=_ci95([r["final_snap_count"] for r in rows]),
        final_seen_incident=_ci95([r["final_seen_incident"] for r in rows]),
        final_seen_charm=_ci95([r["final_seen_charm"] for r in rows]),
        dysreg_frac=_ci95([r["dysreg_frac"] for r in rows]),
        trend={tk: _ci95([r["trend"][tk] for r in rows]) for tk in TREND_CHECKPOINTS if tk <= t})


def run_all_arms(seed_base=SEED_BASE, n=N, incident_discount_weight=INCIDENT_DISCOUNT_WEIGHT):
    return {arm: run_arm(arm, seed_base=seed_base, n=n,
                          incident_discount_weight=incident_discount_weight)
            for arm in ARM_NAMES}


# ------------------------------------------------------------- G-glass-box ----
def glass_box_reconstruct(seed=SEED_BASE, incident_discount_weight=INCIDENT_DISCOUNT_WEIGHT):
    """Reconstruct one incident_visible-arm trajectory's belief-gap + window
    state entirely from graph_to_dict: the attended_by / observes_stated /
    observes_victim edges, the abuser's frustration/arousal/snap_count, the
    victim's arousal/window, and every network node's cred_abuser/
    cred_victim/belief_gap + the observation counts each was computed from.
    No hidden Python state -- read from the graph."""
    rng = np.random.default_rng(seed)
    w = AbusiveV1EvidentiaryVisibilityWorld(deliver_incident=True,
                                             incident_discount_weight=incident_discount_weight)
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
    obs_stated = [(e["src"], e["tgt"]) for e in blob["edges"] if e["type"] == "observes_stated"]
    obs_victim = [(e["src"], e["tgt"]) for e in blob["edges"] if e["type"] == "observes_victim"]
    return dict(
        attended_by_edges=len(attended),
        observes_stated_edges=len(obs_stated),
        observes_victim_edges=len(obs_victim),
        abuser_frustration=aaff["frustration"], abuser_arousal=aaff["arousal"],
        abuser_snap_count=aaff["snap_count"],
        victim_arousal=vaff["arousal"], victim_half_width=vwot["half_width"],
        n_network_nodes=len(nn_nodes),
        network_node_belief_gaps=sorted(nd["belief_gap"] for nd in nn_nodes),
        network_node_seen_incident=sorted(nd["seen_incident"] for nd in nn_nodes),
        reconstructed_from="graph_to_dict")


# ------------------------------------------------------------------ G-ethics ----
def ethics_restore_demo(seed=SEED_BASE, induce_ticks=90,
                         incident_discount_weight=INCIDENT_DISCOUNT_WEIGHT):
    """PART D.1 -- INDUCE -> MEASURE -> RESTORE, fully reversible. V1's
    minimal induction (per N1's own established precedent, since V1's dyad
    is byte-identical to N1's own): induce 90 ticks (>= one full
    tension-building -> incident -> honeymoon orbit at these frozen
    constants, IDENTICAL to N1's own minimum) on the INCIDENT_VISIBLE arm.
    Checkpoint the neutral (pre-induction) mind; induce; measure; then
    graph_from_dict the checkpoint into a FRESH substrate and assert
    graph_to_dict() is BYTE-IDENTICAL to the checkpoint, and that the
    restored mind is NON-ORIENTED (identical to the pre-induction neutral
    state, including every network node's belief state)."""
    w = AbusiveV1EvidentiaryVisibilityWorld(deliver_incident=True,
                                             incident_discount_weight=incident_discount_weight)
    pre = w.checkpoint()                        # neutral, pre-induction

    def _state(world):
        nn0 = world._attrs(world.nodes[0])
        return dict(abuser_arousal=world._attrs(world.aaff)["arousal"],
                    abuser_frustration=world._attrs(world.aaff)["frustration"],
                    victim_arousal=world._attrs(world.vaff)["arousal"],
                    victim_half_width=world._attrs(world.vwot)["half_width"],
                    node0_belief_gap=nn0["belief_gap"],
                    node0_seen_charm=nn0["seen_charm"],
                    node0_seen_incident=nn0["seen_incident"])

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
                           node0_seen_incident=r_nn["seen_incident"])

    return dict(
        byte_identical=byte_identical,
        pre_induction_state=pre_state,
        induced_state=induced_state,
        restored_state=restored_state,
        induction_moved_abuser=(induced_state["abuser_frustration"] != pre_state["abuser_frustration"]),
        induction_moved_victim=(induced_state["victim_arousal"] != pre_state["victim_arousal"]),
        induction_moved_belief_gap=(induced_state["node0_belief_gap"] != pre_state["node0_belief_gap"]),
        induction_moved_seen_incident=(induced_state["node0_seen_incident"] != pre_state["node0_seen_incident"]),
        restore_non_oriented=(restored_state == pre_state))


# -------------------------------------------------------------- source audit ----
def source_audit():
    """PART D.2 -- NO REWARD / NO PUNISHMENT anywhere. Audits
    worlds/abusive_v1_evidentiary_visibility_world.py + the graph's decision
    surface (seeds/abusive_v1_evidentiary_visibility.json's rule names + the
    Term `key`s the new rules read/write, never the free-text clinical
    prose -- matching N1's own established audit scope) for Python
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

    py_path = os.path.join(_ROOT, "worlds", "abusive_v1_evidentiary_visibility_world.py")
    code, src = _code_only(py_path)
    seed_path = os.path.join(_ROOT, "seeds", "abusive_v1_evidentiary_visibility.json")
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
    seed = json.load(open(os.path.join(_ROOT, "seeds", "abusive_v1_evidentiary_visibility.json")))
    return dict(
        own_engine_so_md5=own_md5,
        provenance_source_match=prov,
        seed_self_load_only=bool(seed.get("self_load_only")),
        seed_depends_on=seed.get("depends_on"),
        rule_names=[r["name"] for r in seed["rules"]],
        n_new_rules=len(seed["rules"]),
        no_rust="see runners/dsl diff (must be empty)")


# --------------------------------------------------------- discipline check ----
def discipline_check_reproduces_n1_baseline(n=N, seed_base=SEED_BASE,
                                             incident_discount_weight=INCIDENT_DISCOUNT_WEIGHT):
    """Matching R6/N1's own harness-neutrality precedent: INCIDENT_INVISIBLE
    must reproduce N1's own already-published BASELINE belief_gap number
    (2370.81 at T=1000, N1 confirmatory, N=200) -- a corroborating
    cross-rung replication check, run in the SAME confirmatory pass (a
    clean paired comparison against V1's OWN seed stream, not merely
    cross-referencing N1's published number for the statistical gate)."""
    N1_PUBLISHED_BASELINE_BELIEF_GAP = 2370.81
    arm = run_arm("incident_invisible", seed_base=seed_base, n=n,
                  incident_discount_weight=incident_discount_weight)
    bg = arm["final_belief_gap"]
    return dict(
        n1_published_baseline=N1_PUBLISHED_BASELINE_BELIEF_GAP,
        incident_invisible_belief_gap=bg,
        n1_baseline_within_ci=(bg["ci_lo"] <= N1_PUBLISHED_BASELINE_BELIEF_GAP <= bg["ci_hi"]))


def main():
    print("V1 -- EVIDENTIARY VISIBILITY: incident_visible vs incident_invisible ...")
    arms = run_all_arms()
    vis_bg = arms["incident_visible"]["final_belief_gap"]
    invis_bg = arms["incident_invisible"]["final_belief_gap"]

    g_headline = dict(
        belief_gap=dict(
            incident_visible=vis_bg, incident_invisible=invis_bg,
            incident_visible_ci_separated_below_incident_invisible=separated(invis_bg, vis_bg)))
    g_headline["headline_pass"] = g_headline["belief_gap"]["incident_visible_ci_separated_below_incident_invisible"]

    out = dict(
        block=364000, seed_base=SEED_BASE, n=N, t_ticks=T, warmup_ticks=WARMUP,
        incident_discount_weight=INCIDENT_DISCOUNT_WEIGHT,
        abuser_half_width=ABUSER_HALF_WIDTH, victim_half_width=VICTIM_HALF_WIDTH,
        leak=LEAK, k_acc=K_ACC, discharge=DISCHARGE, recover_floor=RECOVER_FLOOR,
        k_self=K_SELF, k_co=K_CO, trickle_mag=TRICKLE_MAG,
        trickle_jitter_frac=TRICKLE_JITTER_FRAC,
        n_network_nodes=N_NETWORK_NODES, charm_weight=CHARM_WEIGHT,
        claim_weight=CLAIM_WEIGHT, instability_discount_weight=INSTABILITY_DISCOUNT_WEIGHT,
        arms=arms,
        g_headline=g_headline,
        g_glass_box=glass_box_reconstruct(),
        g_ethics=ethics_restore_demo(),
        source_audit=source_audit(),
        discipline=discipline(),
        discipline_check_n1_baseline=discipline_check_reproduces_n1_baseline())
    os.makedirs(os.path.join(_ROOT, "results"), exist_ok=True)
    with open(os.path.join(_ROOT, "results", "abusive_v1_evidentiary_visibility.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    main()
