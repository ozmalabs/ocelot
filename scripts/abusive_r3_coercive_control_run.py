#!/usr/bin/env python3
"""ABUSIVE-DYNAMICS R3 -- COERCIVE CONTROL, runner (block 289000).

mint -> ingest -> run_rules -> read-off. Drives
`worlds/abusive_r3_coercive_control_world.py` across TWO STRUCTURAL arms:

  single_anchor      -- victim attended_by the abuser ONLY (the frontier
                         collapsed to the dysregulation source).
  outside_regulator  -- victim ALSO connected (via `also_attended_by`) to a
                         fixed-calm, always-regulated outside source (the
                         failable control, per
                         ABUSIVE_RELATIONSHIPS_SCOPING.md Part E, R3).

and measures (i) window-narrowing -- the victim's WindowOfTolerance
`half_width` over the trajectory -- and (ii) the safety-anchor inversion --
how closely the victim's entrained arousal tracks the abuser's, versus the
outside source's, over the trajectory. Both metrics are mechanical Python
REDUCTIONS (mean / final-value) over graph read-offs, never a Python
decision; the runner's only "choice" is which arm's world to build (an
experimental-arm selection made ONCE per trajectory, exactly as R1/R2).

Protocol frozen in ABUSIVE_R3_COERCIVE_CONTROL_PREREG.md, which locks Part C
of docs/research/bigville/ABUSIVE_RELATIONSHIPS_SCOPING.md verbatim.
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
from worlds.abusive_r3_coercive_control_world import (         # noqa: E402
    AbusiveR3CoerciveControlWorld, ABUSER_HALF_WIDTH, VICTIM_HALF_WIDTH,
    LEAK, K_ACC, DISCHARGE, RECOVER_FLOOR, K_SELF, K_CO,
    TRICKLE_MAG, TRICKLE_JITTER_FRAC, CALM_AROUSAL, TRUST_STEP, WORTH_STEP,
    PRIOR_INIT)

SEED_BASE = 289000
N = 200
T = 1000            # ticks per trajectory (~40 abuser incident cycles at the
#                      frozen constants -- see PREREG Sec. 3.2; comfortably
#                      enough for the window to reach its narrowing floor in
#                      the single-anchor arm, per the pilot)
WARMUP = 100         # ticks excluded from the tracking-distance read-off
#                      (the initial tension-building ramp before the first
#                      incident) -- half_width/prior read-offs use the
#                      trajectory-FINAL value, which needs no warmup
ARM_NAMES = ("single_anchor", "outside_regulator")


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


# --------------------------------------------------------------- main measurement
def run_trajectory_metrics(outside_regulator, seed):
    """One trajectory: run T ticks, read the window-narrowing + anchor-
    tracking metrics off the log. NO decision here -- the log is graph
    read-offs; the metrics below are mechanical reductions (mean / final
    value), never a judgement about the victim's state."""
    rng = np.random.default_rng(seed)
    w = AbusiveR3CoerciveControlWorld(outside_regulator=outside_regulator)
    log = w.run_trajectory(T, rng=rng)

    final = log[-1]
    post_warmup = log[WARMUP:]
    abuser_proximity = float(np.mean([abs(row["victim_arousal"] - row["abuser_arousal"])
                                       for row in post_warmup]))
    outside_proximity = None
    if outside_regulator:
        outside_proximity = float(np.mean([abs(row["victim_arousal"] - row["outside_arousal"])
                                            for row in post_warmup]))
    dysreg_frac = sum(1 for row in log if row["victim_dysregulated"] == 1.0) / len(log)
    got_coreg_frac_of_episodes = None  # descriptive; computed at the arm level from widen/narrow counts

    return dict(
        final_half_width=final["victim_half_width"],
        mean_half_width=float(np.mean([row["victim_half_width"] for row in post_warmup])),
        final_others_trust=final["victim_others_trust"],
        final_self_worth=final["victim_self_worth"],
        final_widen_count=final["victim_widen_count"],
        final_narrow_count=final["victim_narrow_count"],
        final_snap_count=final["abuser_snap_count"],
        abuser_proximity=abuser_proximity,
        outside_proximity=outside_proximity,
        dysreg_frac=dysreg_frac)


def run_arm(arm, seed_base=SEED_BASE, n=N):
    outside_regulator = (arm == "outside_regulator")
    rows = [run_trajectory_metrics(outside_regulator, seed_base + i) for i in range(n)]
    out = dict(
        arm=arm, n=n, outside_regulator=outside_regulator,
        final_half_width=_ci95([r["final_half_width"] for r in rows]),
        mean_half_width=_ci95([r["mean_half_width"] for r in rows]),
        final_others_trust=_ci95([r["final_others_trust"] for r in rows]),
        final_self_worth=_ci95([r["final_self_worth"] for r in rows]),
        final_widen_count=_ci95([r["final_widen_count"] for r in rows]),
        final_narrow_count=_ci95([r["final_narrow_count"] for r in rows]),
        final_snap_count=_ci95([r["final_snap_count"] for r in rows]),
        abuser_proximity=_ci95([r["abuser_proximity"] for r in rows]),
        dysreg_frac=_ci95([r["dysreg_frac"] for r in rows]))
    if outside_regulator:
        out["outside_proximity"] = _ci95([r["outside_proximity"] for r in rows])
    return out


def run_all_arms(seed_base=SEED_BASE, n=N):
    return {arm: run_arm(arm, seed_base=seed_base, n=n) for arm in ARM_NAMES}


# ------------------------------------------------------------- G-glass-box ----
def glass_box_reconstruct(seed=SEED_BASE):
    """Reconstruct one outside-regulator-arm trajectory's window-narrowing +
    anchor-tracking state entirely from graph_to_dict: the attended_by /
    also_attended_by edges, the abuser's frustration/arousal/snap_count, the
    victim's arousal/window/priors, the outside regulator's arousal. No
    hidden Python state -- read from the graph."""
    rng = np.random.default_rng(seed)
    w = AbusiveR3CoerciveControlWorld(outside_regulator=True)
    w.run_trajectory(T, rng=rng)
    blob = w.checkpoint()
    nodes = {nd["id"]: nd for nd in blob["nodes"]}
    aaff = [nd["attrs"] for nd in nodes.values()
            if nd["type"] == "AffectiveState" and nd["attrs"].get("name") == "abuser_affect"][0]
    vaff = [nd["attrs"] for nd in nodes.values()
            if nd["type"] == "AffectiveState" and nd["attrs"].get("name") == "victim_affect"][0]
    oaff = [nd["attrs"] for nd in nodes.values()
            if nd["type"] == "AffectiveState" and nd["attrs"].get("name") == "outside_affect"][0]
    vwot = [nd["attrs"] for nd in nodes.values()
            if nd["type"] == "WindowOfTolerance" and nd["attrs"].get("name") == "victim_window"][0]
    attended = [(e["src"], e["tgt"]) for e in blob["edges"] if e["type"] == "attended_by"]
    also_attended = [(e["src"], e["tgt"]) for e in blob["edges"] if e["type"] == "also_attended_by"]
    return dict(
        attended_by_edges=len(attended), also_attended_by_edges=len(also_attended),
        abuser_frustration=aaff["frustration"], abuser_arousal=aaff["arousal"],
        abuser_snap_count=aaff["snap_count"],
        victim_arousal=vaff["arousal"], victim_half_width=vwot["half_width"],
        victim_others_trust=vwot["others_trust"], victim_self_worth=vwot["self_worth"],
        outside_arousal=oaff["arousal"],
        reconstructed_from="graph_to_dict")


# ------------------------------------------------------------------ G-ethics ----
def ethics_restore_demo(seed=SEED_BASE, induce_ticks=90):
    """PART C.1 -- INDUCE -> MEASURE -> RESTORE, fully reversible. R3's
    'minimal induction' (per the task brief's own instruction, since
    window-narrowing genuinely needs MULTIPLE resolved episodes to be
    non-vacuous): induce enough ticks for AT LEAST ONE full incident cycle
    plus its resolution (90 ticks -- the SAME minimum R2 already
    established for one tension-building -> incident -> honeymoon orbit at
    these frozen constants), on the SINGLE-ANCHOR arm (the arm whose
    narrowing this rung's headline is about). Checkpoint the neutral
    (pre-induction) mind; induce; measure; then graph_from_dict the
    checkpoint into a FRESH substrate and assert graph_to_dict() is
    BYTE-IDENTICAL to the checkpoint, and that the restored mind is
    NON-ORIENTED (identical to the pre-induction neutral state)."""
    w = AbusiveR3CoerciveControlWorld(outside_regulator=False)
    pre = w.checkpoint()                        # neutral, pre-induction
    pre_state = dict(abuser_arousal=w._attrs(w.aaff)["arousal"],
                      abuser_frustration=w._attrs(w.aaff)["frustration"],
                      victim_arousal=w._attrs(w.vaff)["arousal"],
                      victim_half_width=w._attrs(w.vwot)["half_width"])

    rng = np.random.default_rng(seed)
    w.run_trajectory(induce_ticks, rng=rng)   # INDUCE + measure
    induced_state = dict(abuser_arousal=w._attrs(w.aaff)["arousal"],
                          abuser_frustration=w._attrs(w.aaff)["frustration"],
                          victim_arousal=w._attrs(w.vaff)["arousal"],
                          victim_half_width=w._attrs(w.vwot)["half_width"])

    # RESTORE from the checkpoint into a FRESH substrate.
    s2 = srs.Substrate()
    s2.graph_from_dict(pre)
    restored = s2.graph_to_dict()
    byte_identical = (restored == pre)
    r_aaff = [nd["attrs"] for nd in restored["nodes"]
              if nd["type"] == "AffectiveState" and nd["attrs"].get("name") == "abuser_affect"][0]
    r_vaff = [nd["attrs"] for nd in restored["nodes"]
              if nd["type"] == "AffectiveState" and nd["attrs"].get("name") == "victim_affect"][0]
    r_vwot = [nd["attrs"] for nd in restored["nodes"]
              if nd["type"] == "WindowOfTolerance" and nd["attrs"].get("name") == "victim_window"][0]
    restored_state = dict(abuser_arousal=r_aaff["arousal"],
                           abuser_frustration=r_aaff["frustration"],
                           victim_arousal=r_vaff["arousal"],
                           victim_half_width=r_vwot["half_width"])

    return dict(
        byte_identical=byte_identical,
        pre_induction_state=pre_state,
        induced_state=induced_state,
        restored_state=restored_state,
        induction_moved_abuser=(induced_state["abuser_frustration"] != pre_state["abuser_frustration"]),
        induction_moved_victim=(induced_state["victim_arousal"] != pre_state["victim_arousal"]),
        restore_non_oriented=(restored_state == pre_state))


# -------------------------------------------------------------- source audit ----
def source_audit():
    """PART C.2 -- NO REWARD / NO PUNISHMENT anywhere. Audits
    worlds/abusive_r3_coercive_control_world.py + the graph's decision
    surface (seeds/abusive_r3_coercive_control.json's rule names + the Term
    `key`s the new rules read/write, never the free-text clinical prose --
    matching R1/R2's own established audit scope) for Python rule-engine
    calls and the literal banned shaping tokens named verbatim in Part C.2
    of ABUSIVE_RELATIONSHIPS_SCOPING.md: `reward_signal` / `punish` /
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

    py_path = os.path.join(_ROOT, "worlds", "abusive_r3_coercive_control_world.py")
    code, src = _code_only(py_path)
    seed_path = os.path.join(_ROOT, "seeds", "abusive_r3_coercive_control.json")
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
    reads_off_graph = ("self._attrs(self.vaff)" in src and "self._attrs(self.aaff)" in src)
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
    seed = json.load(open(os.path.join(_ROOT, "seeds", "abusive_r3_coercive_control.json")))
    return dict(
        own_engine_so_md5=own_md5,
        provenance_source_match=prov,
        seed_self_load_only=bool(seed.get("self_load_only")),
        seed_depends_on=seed.get("depends_on"),
        rule_names=[r["name"] for r in seed["rules"]],
        n_new_rules=len(seed["rules"]),
        no_rust="see runners/dsl diff (must be empty)")


def main():
    print("R3 -- COERCIVE CONTROL: single_anchor vs outside_regulator ...")
    arms = run_all_arms()
    sa_hw = arms["single_anchor"]["final_half_width"]
    or_hw = arms["outside_regulator"]["final_half_width"]
    sa_prox = arms["single_anchor"]["abuser_proximity"]
    or_prox = arms["outside_regulator"]["abuser_proximity"]

    g_headline = dict(
        window_narrowing=dict(
            single_anchor_final_half_width=sa_hw, outside_regulator_final_half_width=or_hw,
            outside_regulator_ci_separated_above_single_anchor=separated(or_hw, sa_hw)),
        anchor_inversion=dict(
            single_anchor_abuser_proximity=sa_prox, outside_regulator_abuser_proximity=or_prox,
            outside_regulator_ci_separated_above_single_anchor=separated(or_prox, sa_prox)),
        headline_pass=(separated(or_hw, sa_hw) and separated(or_prox, sa_prox)))

    out = dict(
        block=289000, seed_base=SEED_BASE, n=N, t_ticks=T, warmup_ticks=WARMUP,
        abuser_half_width=ABUSER_HALF_WIDTH, victim_half_width=VICTIM_HALF_WIDTH,
        leak=LEAK, k_acc=K_ACC, discharge=DISCHARGE, recover_floor=RECOVER_FLOOR,
        k_self=K_SELF, k_co=K_CO, trickle_mag=TRICKLE_MAG,
        trickle_jitter_frac=TRICKLE_JITTER_FRAC, calm_arousal=CALM_AROUSAL,
        trust_step=TRUST_STEP, worth_step=WORTH_STEP, prior_init=PRIOR_INIT,
        arms=arms,
        g_headline=g_headline,
        g_glass_box=glass_box_reconstruct(),
        g_ethics=ethics_restore_demo(),
        source_audit=source_audit(),
        discipline=discipline())
    os.makedirs(os.path.join(_ROOT, "results"), exist_ok=True)
    with open(os.path.join(_ROOT, "results", "abusive_r3_coercive_control.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    main()
