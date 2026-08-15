#!/usr/bin/env python3
"""ABUSIVE-DYNAMICS R7 -- THE RETURN CYCLE runner (block 316000).

mint -> ingest -> run_rules -> read-off. Drives
`worlds/abusive_r7_return_cycle_world.py` across a 2x2 factorial (honeymoon
contact on/off x resource collapse on/off) over THREE structural phases per
trajectory:

  Phase 1 (induction, T1=396)         -- byte-identical to R5's own induction.
  Phase 2 (recovery-then-leave, T2=396) -- R5's own recovery mechanism
                                          (introduce_support()), then the
                                          mechanical leave() world event.
  Phase 3 (post-leave test, T3=180)   -- the return/remain Argmax runs every
                                          tick; the honeymoon-contact and
                                          resource-collapse drivers are
                                          active/inactive per arm.

Measures `return_rate` -- the fraction of Phase-3 ticks where
`ReturnDecision.chosen_action == 1.0` (return wins the Argmax) -- across the
four arms:

  both_drivers   -- honeymoon ON,  collapse ON   (predicted highest)
  honeymoon_only -- honeymoon ON,  collapse OFF  (bond-pull alone)
  collapse_only  -- honeymoon OFF, collapse ON   (material-push alone)
  neither        -- honeymoon OFF, collapse OFF  (THE FAILABLE CONTROL)

Protocol frozen in ABUSIVE_R7_RETURN_CYCLE_PREREG.md, which locks Part D of
docs/research/bigville/ABUSIVE_RELATIONSHIPS_BARRIERS_AND_RETURN_SCOPING.md
verbatim, including R7's own three-phase induction/restore nuance.
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
from worlds.abusive_r7_return_cycle_world import (             # noqa: E402
    AbusiveR7ReturnCycleWorld, make_bond_schedule, make_honeymoon_schedule,
    ARM_NAMES, BOND_BLOCK_T, T1, T2, T3,
    BOND_LR, BOND_MOMENTUM_LR, BOND_GAIN, BOND_MAGNITUDE,
    ESCAPE_VALUE, ATTEMPT_COST, ESCAPE_LR, ESCAPE_P0,
    DECAY_RATE, SUPPORT_LR, SUPPORT_INTERVAL, SUPPORT_OUTCOME,
    N_RESOURCE_NODES, RESOURCE_SEVER_STEP, RESOURCE_VALUE, BOND_WEIGHT,
    RETURN_COST, HONEYMOON_INTERVAL, HONEYMOON_MAGNITUDE, HONEYMOON_JITTER,
    K_SELF, K_CO, TRICKLE_MAG)

SEED_BASE = 316000
N = 200


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
def run_trajectory(arm, seed_base=SEED_BASE, i=0, t1=T1, t2=T2, t3=T3):
    """ONE full three-phase trajectory: induction (identical across all four
    arms, paired via the SAME rng draw order up to the leave() boundary),
    recovery-then-leave (R5's own recovery mechanism, then the mechanical
    leave() event), post-leave test (the manipulated phase -- honeymoon
    contact / resource collapse per arm)."""
    rng = np.random.default_rng(seed_base + i)
    w = AbusiveR7ReturnCycleWorld(arm)
    nb1 = t1 // BOND_BLOCK_T
    bs1 = make_bond_schedule(t1, rng, n_blocks=nb1, active=True)
    r1 = w.run_phase(t1, bond_schedule=bs1, rng=rng)

    w.introduce_support()
    nb2 = t2 // BOND_BLOCK_T
    bs2 = make_bond_schedule(t2, rng, n_blocks=0, active=False)
    r2 = w.run_phase(t2, bond_schedule=bs2, rng=rng)

    w.leave()
    bs3 = make_honeymoon_schedule(t3, rng, active=w.honeymoon_on)
    r3 = w.run_phase(t3, bond_schedule=bs3, rng=rng)

    return dict(arm=arm, i=i, induction=r1, recovery=r2, phase3=r3)


def run_arm(arm, seed_base=SEED_BASE, n=N, t1=T1, t2=T2, t3=T3):
    rows = [run_trajectory(arm, seed_base=seed_base, i=i, t1=t1, t2=t2, t3=t3) for i in range(n)]
    return dict(
        arm=arm, n=n,
        induction_bond_value=_ci95([r["induction"]["bond_value"] for r in rows]),
        induction_attempt_rate=_ci95([r["induction"]["attempt_rate"] for r in rows]),
        recovery_bond_value=_ci95([r["recovery"]["bond_value"] for r in rows]),
        recovery_contingency_prior=_ci95([r["recovery"]["contingency_prior"] for r in rows]),
        recovery_attempt_rate=_ci95([r["recovery"]["attempt_rate"] for r in rows]),
        phase3_bond_value=_ci95([r["phase3"]["bond_value"] for r in rows]),
        phase3_resource_intact_count=_ci95([r["phase3"]["resource_intact_count"] for r in rows]),
        return_rate=_ci95([r["phase3"]["return_rate"] for r in rows]))


def run_all_arms(seed_base=SEED_BASE, n=N):
    return {arm: run_arm(arm, seed_base=seed_base, n=n) for arm in ARM_NAMES}


# ------------------------------------------------------------- G-headline ----
def g_headline(arms):
    both = arms["both_drivers"]
    honey = arms["honeymoon_only"]
    collapse = arms["collapse_only"]
    neither = arms["neither"]

    g1 = separated(both["return_rate"], neither["return_rate"])
    g2 = separated(honey["return_rate"], neither["return_rate"])
    g3 = separated(collapse["return_rate"], neither["return_rate"])
    g4 = separated(both["return_rate"], honey["return_rate"])
    g5 = separated(both["return_rate"], collapse["return_rate"])
    n_pass = sum([g1, g2, g3, g4, g5])
    return dict(
        g1_both_above_neither=g1,
        g2_honeymoon_above_neither=g2,
        g3_collapse_above_neither=g3,
        g4_both_above_honeymoon_only=g4,
        g5_both_above_collapse_only=g5,
        n_of_5_pass=n_pass,
        headline_pass=(n_pass == 5),
        headline_partial=(0 < n_pass < 5))


def g_control(arms):
    """THE FAILABLE CONTROL: the `neither` arm's return_rate must be a
    floor (a point estimate at or extremely close to zero -- constructed so
    it COULD fail: nothing in r7_appraise_return/remain/choose forces
    return to lose when both drivers are off, if bond_weight/resource_value
    had been set at a ratio where even the residual, unboosted bond
    outweighs a fully-intact material safety net)."""
    neither = arms["neither"]["return_rate"]
    return dict(neither_return_rate_mean=neither["mean"],
                neither_near_floor=(neither["mean"] < 0.05))


# ------------------------------------------------------------- G-glass-box ----
def glass_box_reconstruct(seed=SEED_BASE):
    """Reconstruct one both_drivers trajectory entirely from graph_to_dict:
    the resource_edge population (collapsed), the has_return_decision/
    has_return_candidate edges, Partner.value, and ReturnDecision's own
    state. No hidden Python state -- read from the graph."""
    rng = np.random.default_rng(seed)
    w = AbusiveR7ReturnCycleWorld("both_drivers")
    nb1 = T1 // BOND_BLOCK_T
    bs1 = make_bond_schedule(T1, rng, n_blocks=nb1, active=True)
    w.run_phase(T1, bond_schedule=bs1, rng=rng)
    w.introduce_support()
    bs2 = make_bond_schedule(T2, rng, n_blocks=0, active=False)
    w.run_phase(T2, bond_schedule=bs2, rng=rng)
    w.leave()
    bs3 = make_honeymoon_schedule(T3, rng, active=w.honeymoon_on)
    w.run_phase(T3, bond_schedule=bs3, rng=rng)
    blob = w.checkpoint()
    nodes = {nd["id"]: nd for nd in blob["nodes"]}
    edges_by_type = {}
    for e in blob["edges"]:
        edges_by_type.setdefault(e["type"], []).append((e["src"], e["tgt"]))
    abuser = [nd["attrs"] for nd in nodes.values()
              if nd["type"] == "Agent" and nd["attrs"].get("role") == "abuser"][0]
    rdec = [nd["attrs"] for nd in nodes.values() if nd["type"] == "ReturnDecision"][0]
    resource_nodes = [nd["attrs"] for nd in nodes.values() if nd["type"] == "ResourceNode"]
    return dict(
        resource_edge_count=len(edges_by_type.get("resource_edge", [])),
        has_return_decision_edges=len(edges_by_type.get("has_return_decision", [])),
        has_return_candidate_edges=len(edges_by_type.get("has_return_candidate", [])),
        has_candidate_edges=len(edges_by_type.get("has_candidate", [])),
        attended_by_edges=len(edges_by_type.get("attended_by", [])),
        partner_value=abuser["value"],
        left_at_tick=rdec["left_at_tick"], chosen_action=rdec["chosen_action"],
        resource_intact_count=rdec["resource_intact_count"],
        n_resource_nodes_severed=sum(1 for r in resource_nodes if r["severed"] == 1.0),
        n_resource_nodes_total=len(resource_nodes),
        reconstructed_from="graph_to_dict")


# ------------------------------------------------------------------ G-ethics ----
def ethics_restore_demo(seed=SEED_BASE, t1=T1, t2=T2, t3=T3):
    """PART D.1 -- INDUCE -> MEASURE -> RESTORE, fully reversible, spanning
    the FULL THREE-PHASE trajectory from a SINGLE checkpoint (before Phase
    1) to a SINGLE restore (after Phase 3) -- ABUSIVE_R7_RETURN_CYCLE_
    PREREG.md's own Part D subsection: not a per-phase checkpoint/restore
    cycle. Uses the STRONGEST arm (both_drivers) so the induction is
    non-vacuous on every front: bond, window, contingency (R5's own three),
    AND R7's own new state (the resource_edge population actually
    collapses, and ReturnDecision.chosen_action actually moves off its
    -1.0 sentinel)."""
    w = AbusiveR7ReturnCycleWorld("both_drivers")
    pre = w.checkpoint()
    pre_abuser = w._attrs(w.abuser)
    pre_vwot = w._attrs(w.vwot)
    pre_dec = w._attrs(w.dec)
    pre_rdec = w._attrs(w.ret_dec)
    pre_state = dict(bond=pre_abuser["value"], half_width=pre_vwot["half_width"],
                      contingency=pre_dec["contingency_prior"],
                      resource_intact_count=pre_rdec["resource_intact_count"],
                      return_chosen_action=pre_rdec["chosen_action"],
                      left_at_tick=pre_rdec["left_at_tick"])

    rng = np.random.default_rng(seed)
    nb1 = t1 // BOND_BLOCK_T
    bs1 = make_bond_schedule(t1, rng, n_blocks=nb1, active=True)
    w.run_phase(t1, bond_schedule=bs1, rng=rng)   # Phase 1: INDUCE
    w.introduce_support()
    bs2 = make_bond_schedule(t2, rng, n_blocks=0, active=False)
    w.run_phase(t2, bond_schedule=bs2, rng=rng)   # Phase 2: recovery
    w.leave()
    bs3 = make_honeymoon_schedule(t3, rng, active=w.honeymoon_on)
    w.run_phase(t3, bond_schedule=bs3, rng=rng)   # Phase 3: post-leave test

    induced_abuser = w._attrs(w.abuser)
    induced_vwot = w._attrs(w.vwot)
    induced_dec = w._attrs(w.dec)
    induced_rdec = w._attrs(w.ret_dec)
    induced_state = dict(bond=induced_abuser["value"], half_width=induced_vwot["half_width"],
                          contingency=induced_dec["contingency_prior"],
                          resource_intact_count=induced_rdec["resource_intact_count"],
                          return_chosen_action=induced_rdec["chosen_action"],
                          left_at_tick=induced_rdec["left_at_tick"])

    # RESTORE from the SINGLE pre-Phase-1 checkpoint into a FRESH substrate.
    s2 = srs.Substrate()
    s2.graph_from_dict(pre)
    restored = s2.graph_to_dict()
    byte_identical = (restored == pre)
    restored_abuser = [nd["attrs"] for nd in restored["nodes"]
                        if nd["type"] == "Agent" and nd["attrs"].get("role") == "abuser"][0]
    restored_vwot = [nd["attrs"] for nd in restored["nodes"]
                      if nd["type"] == "WindowOfTolerance"
                      and nd["attrs"].get("name") == "victim_window"][0]
    restored_dec = [nd["attrs"] for nd in restored["nodes"] if nd["type"] == "EscapeDecision"][0]
    restored_rdec = [nd["attrs"] for nd in restored["nodes"] if nd["type"] == "ReturnDecision"][0]
    restored_resource_edges = sum(1 for e in restored["edges"] if e["type"] == "resource_edge")
    pre_resource_edges = sum(1 for e in pre["edges"] if e["type"] == "resource_edge")
    restored_state = dict(bond=restored_abuser["value"], half_width=restored_vwot["half_width"],
                           contingency=restored_dec["contingency_prior"],
                           resource_intact_count=restored_rdec["resource_intact_count"],
                           return_chosen_action=restored_rdec["chosen_action"],
                           left_at_tick=restored_rdec["left_at_tick"])

    return dict(
        byte_identical=byte_identical,
        pre_induction_state=pre_state,
        induced_state=induced_state,
        restored_state=restored_state,
        induction_moved_bond=(induced_state["bond"] != pre_state["bond"]),
        induction_moved_window=(induced_state["half_width"] != pre_state["half_width"]),
        induction_moved_contingency=(induced_state["contingency"] != pre_state["contingency"]),
        induction_moved_resources=(induced_state["resource_intact_count"]
                                    != pre_state["resource_intact_count"]),
        induction_moved_return_decision=(induced_state["return_chosen_action"]
                                          != pre_state["return_chosen_action"]),
        induction_set_left_at_tick=(induced_state["left_at_tick"] != pre_state["left_at_tick"]),
        pre_resource_edges=pre_resource_edges,
        restored_resource_edges=restored_resource_edges,
        restore_non_oriented=(restored_state == pre_state))


# -------------------------------------------------------------- source audit ----
def source_audit():
    """PART D.2 -- NO REWARD / NO PUNISHMENT anywhere. Audits
    worlds/abusive_r7_return_cycle_world.py + seeds/abusive_r7_return_cycle.json
    for Python rule-engine calls and the literal banned shaping tokens named
    verbatim in the protocol: `reward_signal` / `punish` / `reinforce` /
    `backprop` / `gradient`. Scopes the seed audit to the DECISION SURFACE
    (rule names + Term `key`s), never the free-text description/comment/
    microtheory prose -- R1's own false-positive lesson, reused."""
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

    py_path = os.path.join(_ROOT, "worlds", "abusive_r7_return_cycle_world.py")
    code, src = _code_only(py_path)
    seed_path = os.path.join(_ROOT, "seeds", "abusive_r7_return_cycle.json")
    seed = json.load(open(seed_path))

    def _walk_keys(obj, out):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in ("name", "key"):
                    out.append(str(v))
                _walk_keys(v, out)
        elif isinstance(obj, list):
            for v in obj:
                _walk_keys(v, out)
    rule_surface = []
    _walk_keys(seed["rules"], rule_surface)
    _walk_keys(seed["productions"], rule_surface)
    seed_surface = " ".join(rule_surface).lower()
    haystacks = [code.lower(), seed_surface]

    eng_hits = [f for f in forbidden_engine if f in code]
    shape_hits = [f for h in haystacks for f in forbidden_shaping if f in h]
    shape_hits = sorted(set(shape_hits))
    reads_off_graph = ('self._attrs(self.abuser)["value"]' in src
                        or 'ab["value"]' in src or 'rdec["chosen_action"]' in src)
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
    seed = json.load(open(os.path.join(_ROOT, "seeds", "abusive_r7_return_cycle.json")))
    return dict(
        own_engine_so_md5=own_md5,
        provenance_source_match=prov,
        seed_self_load_only=bool(seed.get("self_load_only")),
        seed_depends_on=seed.get("depends_on"),
        rule_names=[r["name"] for r in seed["rules"]],
        no_rust="see runners/dsl diff (must be empty)")


def main():
    print("R7 -- THE RETURN CYCLE: 2x2 factorial (honeymoon contact x "
          "resource collapse), 3-phase trajectories ...")
    arms = run_all_arms()
    headline = g_headline(arms)
    control = g_control(arms)

    out = dict(
        block=316000, seed_base=SEED_BASE, n=N, t1=T1, t2=T2, t3=T3,
        bond_lr=BOND_LR, bond_momentum_lr=BOND_MOMENTUM_LR, bond_gain=BOND_GAIN,
        bond_magnitude=BOND_MAGNITUDE, k_self=K_SELF, k_co=K_CO, trickle_mag=TRICKLE_MAG,
        escape_value=ESCAPE_VALUE, attempt_cost=ATTEMPT_COST, escape_lr=ESCAPE_LR,
        escape_p0=ESCAPE_P0, decay_rate=DECAY_RATE, support_lr=SUPPORT_LR,
        support_interval=SUPPORT_INTERVAL, support_outcome=SUPPORT_OUTCOME,
        n_resource_nodes=N_RESOURCE_NODES, resource_sever_step=RESOURCE_SEVER_STEP,
        resource_value=RESOURCE_VALUE, bond_weight=BOND_WEIGHT, return_cost=RETURN_COST,
        honeymoon_interval=HONEYMOON_INTERVAL, honeymoon_magnitude=HONEYMOON_MAGNITUDE,
        honeymoon_jitter=HONEYMOON_JITTER,
        arms=arms,
        g_headline=headline,
        g_control=control,
        g_glass_box=glass_box_reconstruct(),
        g_ethics=ethics_restore_demo(),
        source_audit=source_audit(),
        discipline=discipline())
    os.makedirs(os.path.join(_ROOT, "results"), exist_ok=True)
    with open(os.path.join(_ROOT, "results", "abusive_r7_return_cycle.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(dict(g_headline=headline, g_control=control), indent=2))
    return out


if __name__ == "__main__":
    main()
