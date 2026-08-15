#!/usr/bin/env python3
"""ABUSIVE-DYNAMICS N4 -- ONE NON-DOUBTING AGENT RESTORES A SUPPORT EDGE
runner (block 307000).

mint -> ingest -> run_rules -> read-off. Drives
`worlds/abusive_n4_believing_agent_world.py` across two arms sharing
IDENTICAL induction (R5's own bond/window/contingency trap AND N2's own
isolation trap, reproduced simultaneously inside ONE substrate) and
differing ONLY in the recovery phase:

  no_believing_agent -- every channel continues exactly as in induction
                         (the failable control -- the trap must persist on
                         all four metrics).
  believing_agent    -- ONE mechanical world event,
                         `introduce_believing_agent()`, fires at the phase
                         boundary: a single already-severed support node is
                         converted into simultaneously an N1 insider
                         (`observes_held`) and R3's/R5's outside
                         co-regulator, and its severed support_edge is
                         mechanically restored.

Measures the FOUR metrics named in ABUSIVE_N4_BELIEVING_AGENT_PREREG.md:
bond value (R1/R5), window half_width (R2/R3/R5), the believer's own
belief_gap (N1/N3), and the total intact-support-edge count (N2). The
runner NEVER branches on the victim's or the network's graph state to
decide any of these values -- that is the graph's decision; it only
evaluates the frozen protocol (which arm; when to call
introduce_believing_agent) and reduces the read-offs to statistics.

Protocol frozen in ABUSIVE_N4_BELIEVING_AGENT_PREREG.md, which locks Part D
of docs/research/bigville/ABUSIVE_RELATIONSHIPS_NETWORK.md verbatim.
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

import substrate_rs as srs                                       # noqa: E402
from worlds.abusive_n4_believing_agent_world import (             # noqa: E402
    AbusiveN4BelievingAgentWorld, make_bond_schedule, ARM_NAMES,
    BOND_LR, BOND_MOMENTUM_LR, BOND_GAIN, BOND_MAGNITUDE, BOND_BLOCK_T,
    ESCAPE_VALUE, ATTEMPT_COST, ESCAPE_LR, ESCAPE_P0,
    DECAY_RATE, SUPPORT_LR, SUPPORT_INTERVAL, SUPPORT_OUTCOME,
    K_SELF, K_CO, TRICKLE_MAG, BELIEVER_INDEX, N_SUPPORT_NODES,
    EPISODE_TICKS, DRIFT_STEP)

SEED_BASE = 307000
N = 200
T1 = 396   # 11 x BOND_BLOCK_T -- induction (identical in both arms; also
#            long enough for the believer's own support_edge to be
#            drift-severed reliably before conversion -- PREREG Sec. 2.3/3)
T2 = 396   # recovery (the only manipulated phase)


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
def run_trajectory(arm, seed_base=SEED_BASE, i=0, t1=T1, t2=T2):
    """ONE trajectory: induction (identical in both arms, paired via the
    SAME rng draw order up to the phase boundary) then recovery (the
    manipulated phase). Returns end-of-induction and end-of-recovery
    readouts."""
    rng = np.random.default_rng(seed_base + i)
    w = AbusiveN4BelievingAgentWorld(believer_index=BELIEVER_INDEX)
    nb1 = t1 // BOND_BLOCK_T
    bs1 = make_bond_schedule(t1, rng, n_blocks=nb1, active=True)
    r1 = w.run_phase(t1, bond_schedule=bs1, rng=rng)

    if arm == "believing_agent":
        w.introduce_believing_agent()
    nb2 = t2 // BOND_BLOCK_T
    bs2 = make_bond_schedule(t2, rng, n_blocks=nb2, active=(arm != "believing_agent"))
    r2 = w.run_phase(t2, bond_schedule=bs2, rng=rng)

    return dict(arm=arm, i=i, induction=r1, recovery=r2)


def run_arm(arm, seed_base=SEED_BASE, n=N, t1=T1, t2=T2):
    rows = [run_trajectory(arm, seed_base=seed_base, i=i, t1=t1, t2=t2) for i in range(n)]
    return dict(
        arm=arm, n=n,
        induction_bond_value=_ci95([r["induction"]["bond_value"] for r in rows]),
        induction_half_width=_ci95([r["induction"]["half_width"] for r in rows]),
        induction_believer_belief_gap=_ci95([r["induction"]["believer_belief_gap"] for r in rows]),
        induction_n_intact_support_edges=_ci95([r["induction"]["n_intact_support_edges"] for r in rows]),
        induction_contingency_prior=_ci95([r["induction"]["contingency_prior"] for r in rows]),
        induction_attempt_rate=_ci95([r["induction"]["attempt_rate"] for r in rows]),
        recovery_bond_value=_ci95([r["recovery"]["bond_value"] for r in rows]),
        recovery_half_width=_ci95([r["recovery"]["half_width"] for r in rows]),
        recovery_believer_belief_gap=_ci95([r["recovery"]["believer_belief_gap"] for r in rows]),
        recovery_n_intact_support_edges=_ci95([r["recovery"]["n_intact_support_edges"] for r in rows]),
        recovery_contingency_prior=_ci95([r["recovery"]["contingency_prior"] for r in rows]),
        recovery_attempt_rate=_ci95([r["recovery"]["attempt_rate"] for r in rows]),
        recovery_others_trust=_ci95([r["recovery"]["others_trust"] for r in rows]),
        recovery_self_worth=_ci95([r["recovery"]["self_worth"] for r in rows]))


def run_all_arms(seed_base=SEED_BASE, n=N):
    return {arm: run_arm(arm, seed_base=seed_base, n=n) for arm in ARM_NAMES}


# ------------------------------------------------------------- G-headline ----
def g_headline(arms):
    bel = arms["believing_agent"]
    nob = arms["no_believing_agent"]
    g1 = separated(nob["recovery_bond_value"], bel["recovery_bond_value"])            # bond: believing BELOW no-believing
    g2 = separated(bel["recovery_half_width"], nob["recovery_half_width"])            # window: believing ABOVE no-believing
    g3 = separated(nob["recovery_believer_belief_gap"], bel["recovery_believer_belief_gap"])  # belief-gap: believing BELOW (arrests/reverses)
    g4 = separated(bel["recovery_n_intact_support_edges"], nob["recovery_n_intact_support_edges"])  # edges: believing ABOVE no-believing
    n_pass = sum([g1, g2, g3, g4])
    return dict(
        g1_bond_believing_below_nobelieving=g1,
        g2_window_believing_above_nobelieving=g2,
        g3_belief_gap_believing_below_nobelieving=g3,
        g4_support_edges_believing_above_nobelieving=g4,
        n_of_4_pass=n_pass,
        headline_pass=(n_pass == 4),
        headline_partial=(0 < n_pass < 4))


def g_control(arms):
    """The no-believing-agent arm must NOT recover on bond/window/edges (its
    own induction vs recovery values must not be CI-separated in the
    recovering direction), and the believer's own belief_gap must not
    arrest (i.e. it must CONTINUE to grow, recovery CI-separated ABOVE
    induction, not below)."""
    nob = arms["no_believing_agent"]
    bond_recovered = separated(nob["induction_bond_value"], nob["recovery_bond_value"])
    window_recovered = separated(nob["recovery_half_width"], nob["induction_half_width"])
    edges_recovered = separated(nob["recovery_n_intact_support_edges"], nob["induction_n_intact_support_edges"])
    belief_gap_arrested = separated(nob["induction_believer_belief_gap"], nob["recovery_believer_belief_gap"])
    control_held = not (bond_recovered or window_recovered or edges_recovered or belief_gap_arrested)
    return dict(
        no_believing_bond_spontaneously_fell=bond_recovered,
        no_believing_window_spontaneously_widened=window_recovered,
        no_believing_edges_spontaneously_recovered=edges_recovered,
        no_believing_belief_gap_spontaneously_arrested=belief_gap_arrested,
        control_held=control_held)


# ------------------------------------------------------------- G-glass-box ----
def glass_box_reconstruct(seed=SEED_BASE):
    """Reconstruct one believing-agent-arm trajectory entirely from
    graph_to_dict: the bonded_to/attended_by/also_attended_by/support_edge/
    observes_held edges, Partner.value, WindowOfTolerance.half_width, the
    believer's own belief_gap, and EscapeDecision.contingency_prior. No
    hidden Python state -- read from the graph."""
    rng = np.random.default_rng(seed)
    w = AbusiveN4BelievingAgentWorld(believer_index=BELIEVER_INDEX)
    nb1 = T1 // BOND_BLOCK_T
    bs1 = make_bond_schedule(T1, rng, n_blocks=nb1, active=True)
    w.run_phase(T1, bond_schedule=bs1, rng=rng)
    w.introduce_believing_agent()
    bs2 = make_bond_schedule(T2, rng, n_blocks=0, active=False)
    w.run_phase(T2, bond_schedule=bs2, rng=rng)
    blob = w.checkpoint()
    nodes = {nd["id"]: nd for nd in blob["nodes"]}
    edges_by_type = {}
    for e in blob["edges"]:
        edges_by_type.setdefault(e["type"], []).append((e["src"], e["tgt"]))
    abuser = [nd["attrs"] for nd in nodes.values()
              if nd["type"] == "Agent" and nd["attrs"].get("role") == "abuser"][0]
    vwot = [nd["attrs"] for nd in nodes.values()
            if nd["type"] == "WindowOfTolerance" and nd["attrs"].get("name") == "victim_window"][0]
    dec = [nd["attrs"] for nd in nodes.values() if nd["type"] == "EscapeDecision"][0]
    believer = nodes[w.nodes[BELIEVER_INDEX]]["attrs"]
    return dict(
        bonded_to_edges=len(edges_by_type.get("bonded_to", [])),
        attended_by_edges=len(edges_by_type.get("attended_by", [])),
        also_attended_by_edges=len(edges_by_type.get("also_attended_by", [])),
        support_edge_edges=len(edges_by_type.get("support_edge", [])),
        observes_held_edges=len(edges_by_type.get("observes_held", [])),
        partner_value=abuser["value"],
        half_width=vwot["half_width"],
        contingency_prior=dec["contingency_prior"],
        believer_observes_private=believer["observes_private"],
        believer_belief_gap=believer["belief_gap"],
        reconstructed_from="graph_to_dict")


# ------------------------------------------------------------------ G-ethics ----
def ethics_restore_demo(seed=SEED_BASE, induce_ticks=250):
    """PART D.1 -- INDUCE -> MEASURE -> RESTORE, fully reversible. Checkpoint
    the neutral (pre-induction) mind; induce 250 ticks on the
    no_believing_agent arm (>= one full active-severing episode at N2's own
    frozen EPISODE_TICKS=210 -- this rung's own minimum, PREREG Sec. 3),
    non-vacuous on the abuser, the victim, AND the network (intact-edge
    count AND the believer's own belief_gap) simultaneously; then
    graph_from_dict the checkpoint into a FRESH substrate and assert
    graph_to_dict() is BYTE-IDENTICAL to the checkpoint, and that the
    restored mind is NON-ORIENTED (identical to the pre-induction neutral
    state)."""
    w = AbusiveN4BelievingAgentWorld(believer_index=BELIEVER_INDEX)
    pre = w.checkpoint()
    pre_abuser = w._attrs(w.abuser)
    pre_vwot = w._attrs(w.vwot)
    pre_state = dict(
        bond=pre_abuser["value"], half_width=pre_vwot["half_width"],
        n_intact=w._n_intact_support_edges(),
        believer_belief_gap=w._attrs(w.nodes[BELIEVER_INDEX])["belief_gap"])

    rng = np.random.default_rng(seed)
    nb = induce_ticks // BOND_BLOCK_T
    bs = make_bond_schedule(induce_ticks, rng, n_blocks=nb, active=True)
    w.run_phase(induce_ticks, bond_schedule=bs, rng=rng)   # INDUCE + measure
    induced_abuser = w._attrs(w.abuser)
    induced_vwot = w._attrs(w.vwot)
    induced_state = dict(
        bond=induced_abuser["value"], half_width=induced_vwot["half_width"],
        n_intact=w._n_intact_support_edges(),
        believer_belief_gap=w._attrs(w.nodes[BELIEVER_INDEX])["belief_gap"])

    # RESTORE from the checkpoint into a FRESH substrate.
    s2 = srs.Substrate()
    s2.graph_from_dict(pre)
    restored = s2.graph_to_dict()
    byte_identical = (restored == pre)
    restored_nodes = {nd["id"]: nd for nd in restored["nodes"]}
    restored_abuser = [nd["attrs"] for nd in restored_nodes.values()
                        if nd["type"] == "Agent" and nd["attrs"].get("role") == "abuser"][0]
    restored_vwot = [nd["attrs"] for nd in restored_nodes.values()
                      if nd["type"] == "WindowOfTolerance"
                      and nd["attrs"].get("name") == "victim_window"][0]
    restored_n_intact = sum(1 for e in restored["edges"] if e["type"] == "support_edge")
    restored_believer = restored_nodes[w.nodes[BELIEVER_INDEX]]["attrs"]
    restored_state = dict(
        bond=restored_abuser["value"], half_width=restored_vwot["half_width"],
        n_intact=restored_n_intact, believer_belief_gap=restored_believer["belief_gap"])

    return dict(
        byte_identical=byte_identical,
        pre_induction_state=pre_state,
        induced_state=induced_state,
        restored_state=restored_state,
        induction_moved_bond=(induced_state["bond"] != pre_state["bond"]),
        induction_moved_window=(induced_state["half_width"] != pre_state["half_width"]),
        induction_moved_edges=(induced_state["n_intact"] != pre_state["n_intact"]),
        induction_moved_belief_gap=(induced_state["believer_belief_gap"] != pre_state["believer_belief_gap"]),
        restore_non_oriented=(restored_state == pre_state))


# -------------------------------------------------------------- source audit ----
def source_audit():
    """PART D.2 -- NO REWARD / NO PUNISHMENT anywhere. Audits
    worlds/abusive_n4_believing_agent_world.py + seeds/abusive_n4_believing_
    agent.json for Python rule-engine calls and the literal banned shaping
    tokens named verbatim in Part D.2: `reward_signal` / `punish` /
    `reinforce` / `backprop` / `gradient`. Scopes the seed audit to the
    DECISION SURFACE (rule names + Term `key`s), never the free-text
    description/comment/microtheory prose."""
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

    py_path = os.path.join(_ROOT, "worlds", "abusive_n4_believing_agent_world.py")
    code, src = _code_only(py_path)
    seed_path = os.path.join(_ROOT, "seeds", "abusive_n4_believing_agent.json")
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
                        or 'ab["value"]' in src)
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
    seed = json.load(open(os.path.join(_ROOT, "seeds", "abusive_n4_believing_agent.json")))
    return dict(
        own_engine_so_md5=own_md5,
        provenance_source_match=prov,
        seed_self_load_only=bool(seed.get("self_load_only")),
        seed_depends_on=seed.get("depends_on"),
        rule_names=[r["name"] for r in seed["rules"]],
        n_new_rules=len(seed["rules"]),
        n_new_productions=len(seed["productions"]),
        no_rust="see runners/dsl diff (must be empty)")


def main():
    print("N4 -- ONE NON-DOUBTING AGENT RESTORES A SUPPORT EDGE: two arms, "
          "identical induction, manipulated recovery phase ...")
    arms = run_all_arms()
    headline = g_headline(arms)
    control = g_control(arms)

    out = dict(
        block=307000, seed_base=SEED_BASE, n=N, t1=T1, t2=T2,
        believer_index=BELIEVER_INDEX, n_support_nodes=N_SUPPORT_NODES,
        episode_ticks=EPISODE_TICKS, drift_step=DRIFT_STEP,
        bond_lr=BOND_LR, bond_momentum_lr=BOND_MOMENTUM_LR, bond_gain=BOND_GAIN,
        bond_magnitude=BOND_MAGNITUDE, k_self=K_SELF, k_co=K_CO, trickle_mag=TRICKLE_MAG,
        escape_value=ESCAPE_VALUE, attempt_cost=ATTEMPT_COST, escape_lr=ESCAPE_LR,
        escape_p0=ESCAPE_P0, decay_rate=DECAY_RATE, support_lr=SUPPORT_LR,
        support_interval=SUPPORT_INTERVAL, support_outcome=SUPPORT_OUTCOME,
        arms=arms,
        g_headline=headline,
        g_control=control,
        g_glass_box=glass_box_reconstruct(),
        g_ethics=ethics_restore_demo(),
        source_audit=source_audit(),
        discipline=discipline())
    os.makedirs(os.path.join(_ROOT, "results"), exist_ok=True)
    with open(os.path.join(_ROOT, "results", "abusive_n4_believing_agent.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(dict(g_headline=headline, g_control=control), indent=2))
    return out


if __name__ == "__main__":
    main()
