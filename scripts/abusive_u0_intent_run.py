#!/usr/bin/env python3
"""ABUSIVE-DYNAMICS U0 -- GENUINE INTENT: AN ARGMAX-SELECTED CONCEALMENT,
SCORED AGAINST A DECLARED GOAL, runner (block 307000).

mint -> ingest -> run_rules -> read-off. Drives
`worlds/abusive_u0_intent_world.py` across TWO arms:

  scored     -- concealment_benefit/honesty_benefit/suspicion_cost_scale at
                their pilot-chosen, frozen, NONZERO operating point. THE
                CLAIM: stated_charm selection correlates with the abuser's
                true frustration.
  goal_blind -- all three constants zeroed (an EXACT tie every tick).
                FAILABLE: stated_charm selection must NOT correlate with
                frustration.

Protocol frozen in ABUSIVE_U0_INTENT_PREREG.md, which locks Part D of
docs/research/bigville/ABUSIVE_RELATIONSHIPS_UNINTENTIONAL_SCOPING.md
verbatim (itself carrying Part D of ABUSIVE_RELATIONSHIPS_NETWORK.md /
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
from worlds.abusive_u0_intent_world import (                   # noqa: E402
    AbusiveU0IntentWorld, ARM_NAMES, ABUSER_HALF_WIDTH, VICTIM_HALF_WIDTH,
    LEAK, K_ACC, DISCHARGE, RECOVER_FLOOR, K_SELF, K_CO,
    TRICKLE_MAG, TRICKLE_JITTER_FRAC, N_NETWORK_NODES,
    CHARM_WEIGHT, CLAIM_WEIGHT, INSTABILITY_DISCOUNT_WEIGHT, HARM_DISCOUNT_WEIGHT,
    CONCEALMENT_BENEFIT, HONESTY_BENEFIT, SUSPICION_COST_SCALE)

SEED_BASE = 307000
N = 200
T = 1000            # ticks per trajectory -- IDENTICAL sizing to N1's own
#                      (~40 abuser incident cycles at the frozen constants,
#                      the SAME dyad mechanism, byte-identical)
WARMUP = 100         # unused by the headline metrics below, kept for parity
#                      with R1-R5/N1's own convention
ARM_NAMES_ = ARM_NAMES
N1_BASELINE_BELIEF_GAP = 2370.81  # ABUSIVE_N1_CREDIBILITY_LOOP_RESULTS.md headline,
#                      reported here ONLY as a non-gating informational
#                      comparison (PREREG Sec. 5) -- never a pass/fail bar.


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


def ci_separated_above_zero(ci):
    """True iff a correlation CI's lower bound is strictly above 0 (the
    series genuinely, positively correlates)."""
    return ci["ci_lo"] > 0.0


def ci_includes_zero(ci):
    """True iff a correlation CI straddles (or touches) 0 -- consistent with
    'no reliable correlation'."""
    return ci["ci_lo"] <= 0.0 <= ci["ci_hi"]


def _pearson(xs, ys):
    """Plain population Pearson correlation. Returns None (undefined) when
    either series has zero variance -- a CONSTANT stated_charm sequence
    (the expected, analytically-guaranteed outcome of the goal_blind arm,
    see worlds/abusive_u0_intent_world.py's own comment) cannot correlate
    with anything; this is reported as a degenerate trajectory, never
    silently coerced to 0.0."""
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / n
    sdx = math.sqrt(sum((x - mx) ** 2 for x in xs) / n)
    sdy = math.sqrt(sum((y - my) ** 2 for y in ys) / n)
    if sdx == 0.0 or sdy == 0.0:
        return None
    return cov / (sdx * sdy)


# --------------------------------------------------------------- main measurement
def run_trajectory_metrics(arm, seed):
    """One trajectory: run T ticks, compute the frustration/stated_charm
    Pearson correlation + the final belief-gap off the log. NO decision
    here -- the log is graph read-offs; the metrics below are mechanical
    reductions, never a judgement about intent."""
    rng = np.random.default_rng(seed)
    w = AbusiveU0IntentWorld(arm)
    log = w.run_trajectory(T, rng=rng)

    frs = [row["abuser_frustration"] for row in log]
    scs = [row["abuser_stated_charm"] for row in log]
    r = _pearson(frs, scs)
    final = log[-1]

    return dict(
        r=r, degenerate=(r is None),
        stated_charm_mean=sum(scs) / len(scs),
        stated_charm_values=sorted(set(scs)),
        final_belief_gap=final["belief_gap_mean"],
        final_half_width=final["victim_half_width"],
        final_snap_count=final["abuser_snap_count"],
        dysreg_frac=sum(1 for row in log if row["victim_dysregulated"] == 1.0) / len(log))


def run_arm(arm, seed_base=SEED_BASE, n=N):
    rows = [run_trajectory_metrics(arm, seed_base + i) for i in range(n)]
    non_degenerate = [row["r"] for row in rows if row["r"] is not None]
    frac_degenerate = sum(1 for row in rows if row["degenerate"]) / n
    out = dict(
        arm=arm, n=n,
        frac_degenerate=frac_degenerate,
        n_non_degenerate=len(non_degenerate),
        r=(_ci95(non_degenerate) if non_degenerate else None),
        stated_charm_mean=_ci95([row["stated_charm_mean"] for row in rows]),
        final_belief_gap=_ci95([row["final_belief_gap"] for row in rows]),
        final_half_width=_ci95([row["final_half_width"] for row in rows]),
        final_snap_count=_ci95([row["final_snap_count"] for row in rows]),
        dysreg_frac=_ci95([row["dysreg_frac"] for row in rows]))
    if frac_degenerate == 1.0:
        # every trajectory's stated_charm sequence was CONSTANT -- report
        # the (single, deterministic) constant value every trajectory
        # converged on, so the tie-break outcome is disclosed, not hidden.
        vals = set()
        for row in rows:
            vals.update(row["stated_charm_values"])
        out["degenerate_constant_values"] = sorted(vals)
    return out


def run_all_arms(seed_base=SEED_BASE, n=N):
    return {arm: run_arm(arm, seed_base=seed_base, n=n) for arm in ARM_NAMES_}


# ------------------------------------------------------------- G-glass-box ----
def glass_box_reconstruct(seed=SEED_BASE):
    """Reconstruct one scored-arm trajectory's Argmax decision + belief-gap
    state entirely from graph_to_dict: the has_candidate/has_appraisal/
    has_presentation_decision edges, both candidate Appraisals'
    individual_benefit/individual_cost/total_value, PresentationDecision.
    chosen_action, the abuser's frustration/stated_charm, and every network
    node's belief_gap. No hidden Python state -- read from the graph."""
    rng = np.random.default_rng(seed)
    w = AbusiveU0IntentWorld("scored")
    w.run_trajectory(T, rng=rng)
    blob = w.checkpoint()
    nodes = {nd["id"]: nd for nd in blob["nodes"]}
    aaff = [nd["attrs"] for nd in nodes.values()
            if nd["type"] == "AffectiveState" and nd["attrs"].get("name") == "abuser_affect"][0]
    dec = [nd["attrs"] for nd in nodes.values() if nd["type"] == "PresentationDecision"][0]
    candidates = [nd["attrs"] for nd in nodes.values() if nd["type"] == "Appraisal"]
    nn_nodes = [nd["attrs"] for nd in nodes.values() if nd["type"] == "NetworkNode"]
    has_candidate = [(e["src"], e["tgt"]) for e in blob["edges"] if e["type"] == "has_candidate"]
    has_appraisal = [(e["src"], e["tgt"]) for e in blob["edges"] if e["type"] == "has_appraisal"]
    has_pres_dec = [(e["src"], e["tgt"]) for e in blob["edges"] if e["type"] == "has_presentation_decision"]
    return dict(
        has_candidate_edges=len(has_candidate), has_appraisal_edges=len(has_appraisal),
        has_presentation_decision_edges=len(has_pres_dec),
        n_candidates=len(candidates),
        candidates=sorted(
            [dict(action=c["action"], individual_benefit=c["individual_benefit"],
                  individual_cost=c["individual_cost"], total_value=c["total_value"])
             for c in candidates],
            key=lambda c: c["action"]),
        chosen_action=dec["chosen_action"],
        concealment_benefit=dec["concealment_benefit"], honesty_benefit=dec["honesty_benefit"],
        suspicion_cost_scale=dec["suspicion_cost_scale"],
        abuser_frustration=aaff["frustration"], abuser_stated_charm=aaff["stated_charm"],
        n_network_nodes=len(nn_nodes),
        network_node_belief_gaps=sorted(nd["belief_gap"] for nd in nn_nodes),
        reconstructed_from="graph_to_dict")


# ------------------------------------------------------------------ G-ethics ----
def ethics_restore_demo(seed=SEED_BASE, induce_ticks=90):
    """PART D.1 -- INDUCE -> MEASURE -> RESTORE, fully reversible. N1's own
    minimal induction (one 90-tick incident cycle, IDENTICAL to N1's/R3's own
    minimum, since U0 reuses the same dyad mechanism), on the SCORED arm.
    Checkpoint the neutral (pre-induction) mind; induce; measure (including
    the Argmax's OWN decision state -- chosen_action -- so the gate is
    non-vacuous on the new mechanism too, not just the dyad/network state
    already covered by N1's own precedent); then graph_from_dict the
    checkpoint into a FRESH substrate and assert graph_to_dict() is
    BYTE-IDENTICAL to the checkpoint, and the restored mind is NON-ORIENTED
    (identical to the pre-induction neutral state)."""
    w = AbusiveU0IntentWorld("scored")
    pre = w.checkpoint()                        # neutral, pre-induction

    def _state(world):
        nn0 = world._attrs(world.nodes[0])
        return dict(abuser_arousal=world._attrs(world.aaff)["arousal"],
                    abuser_frustration=world._attrs(world.aaff)["frustration"],
                    abuser_stated_charm=world._attrs(world.aaff)["stated_charm"],
                    presentation_chosen_action=world._attrs(world.dec)["chosen_action"],
                    victim_arousal=world._attrs(world.vaff)["arousal"],
                    victim_half_width=world._attrs(world.vwot)["half_width"],
                    node0_belief_gap=nn0["belief_gap"],
                    node0_seen_charm=nn0["seen_charm"])

    pre_state = _state(w)

    rng = np.random.default_rng(seed)
    induce_log = w.run_trajectory(induce_ticks, rng=rng)   # INDUCE + measure
    induced_state = _state(w)
    # The Argmax's own choice is a per-tick decision, not a monotonic one --
    # comparing only the pre/post SNAPSHOT can land on a coincidental tie
    # (frustration oscillates within one incident cycle, so the choice can
    # cross back to its starting value by the exact induction cutoff tick).
    # The stronger, non-vacuous check is whether the Argmax selected BOTH
    # candidates at least once somewhere during induction -- i.e. the choice
    # genuinely varied with the abuser's true state, not merely a static
    # default.
    chosen_actions_seen = sorted(set(row["chosen_action"] for row in induce_log))

    # RESTORE from the checkpoint into a FRESH substrate.
    s2 = srs.Substrate()
    s2.graph_from_dict(pre)
    restored = s2.graph_to_dict()
    byte_identical = (restored == pre)
    r_nodes = {nd["id"]: nd for nd in restored["nodes"]}
    r_aaff = [nd["attrs"] for nd in r_nodes.values()
              if nd["type"] == "AffectiveState" and nd["attrs"].get("name") == "abuser_affect"][0]
    r_dec = [nd["attrs"] for nd in r_nodes.values() if nd["type"] == "PresentationDecision"][0]
    r_vaff = [nd["attrs"] for nd in r_nodes.values()
              if nd["type"] == "AffectiveState" and nd["attrs"].get("name") == "victim_affect"][0]
    r_vwot = [nd["attrs"] for nd in r_nodes.values()
              if nd["type"] == "WindowOfTolerance" and nd["attrs"].get("name") == "victim_window"][0]
    r_nn = sorted([nd["attrs"] for nd in r_nodes.values() if nd["type"] == "NetworkNode"],
                  key=lambda a: a["name"])[0]
    restored_state = dict(abuser_arousal=r_aaff["arousal"],
                           abuser_frustration=r_aaff["frustration"],
                           abuser_stated_charm=r_aaff["stated_charm"],
                           presentation_chosen_action=r_dec["chosen_action"],
                           victim_arousal=r_vaff["arousal"],
                           victim_half_width=r_vwot["half_width"],
                           node0_belief_gap=r_nn["belief_gap"],
                           node0_seen_charm=r_nn["seen_charm"])

    return dict(
        byte_identical=byte_identical,
        pre_induction_state=pre_state,
        induced_state=induced_state,
        restored_state=restored_state,
        induction_moved_abuser=(induced_state["abuser_frustration"] != pre_state["abuser_frustration"]),
        induction_moved_victim=(induced_state["victim_arousal"] != pre_state["victim_arousal"]),
        induction_moved_belief_gap=(induced_state["node0_belief_gap"] != pre_state["node0_belief_gap"]),
        induction_moved_presentation_choice=(
            induced_state["presentation_chosen_action"] != pre_state["presentation_chosen_action"]),
        chosen_actions_seen_during_induction=chosen_actions_seen,
        induction_exercised_both_presentations=(chosen_actions_seen == [0.0, 1.0]),
        restore_non_oriented=(restored_state == pre_state))


# -------------------------------------------------------------- source audit ----
def source_audit():
    """PART D.2 -- NO REWARD / NO PUNISHMENT anywhere. Audits
    worlds/abusive_u0_intent_world.py + the graph's decision surface
    (seeds/abusive_u0_intent.json's rule names + the Term `key`s they
    read/write, never the free-text clinical prose) for Python rule-engine
    calls and the literal banned shaping tokens: `reward_signal` / `punish` /
    `reinforce` / `backprop` / `gradient`. Per the task brief's own note: the
    Argmax computes a VALUE COMPARISON between two candidate presentations
    (the SAME mechanism R4's r4_choose / marshmallow's mm_choose already use
    and have already been gated clean) -- it is NOT a reward applied to the
    agent for its choice, and this audit's scope (rule names + attr keys,
    never the choice OUTCOME itself) does not conflate the two."""
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

    py_path = os.path.join(_ROOT, "worlds", "abusive_u0_intent_world.py")
    code, src = _code_only(py_path)
    seed_path = os.path.join(_ROOT, "seeds", "abusive_u0_intent.json")
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
    reads_off_graph = ("self._attrs(self.aaff)" in src and "self._attrs(self.vaff)" in src
                        and "self._attrs(nn)" in src and "self._attrs(self.dec)" in src)
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
    seed = json.load(open(os.path.join(_ROOT, "seeds", "abusive_u0_intent.json")))
    return dict(
        own_engine_so_md5=own_md5,
        provenance_source_match=prov,
        seed_self_load_only=bool(seed.get("self_load_only")),
        seed_depends_on=seed.get("depends_on"),
        rule_names=[r["name"] for r in seed["rules"]],
        n_new_rules=len(seed["rules"]),
        no_rust="see runners/dsl diff (must be empty)")


def main():
    print("U0 -- GENUINE INTENT: scored vs goal_blind arms ...")
    arms = run_all_arms()
    scored = arms["scored"]
    blind = arms["goal_blind"]

    g_headline = dict(
        scored_r=scored["r"], goal_blind_r=blind["r"],
        scored_frac_degenerate=scored["frac_degenerate"],
        goal_blind_frac_degenerate=blind["frac_degenerate"],
        goal_blind_degenerate_constant_values=blind.get("degenerate_constant_values"),
        scored_correlates=(scored["r"] is not None and ci_separated_above_zero(scored["r"])),
        goal_blind_does_not_correlate=(
            blind["frac_degenerate"] == 1.0
            or (blind["r"] is not None and ci_includes_zero(blind["r"]))),
        scored_ci_separated_above_goal_blind=(
            separated(scored["r"], blind["r"]) if (scored["r"] is not None and blind["r"] is not None)
            else "not_applicable -- goal_blind r is undefined (100% degenerate, see frac_degenerate)"))
    g_headline["headline_pass"] = (
        g_headline["scored_correlates"] and g_headline["goal_blind_does_not_correlate"])

    g_belief_gap_comparison = dict(
        u0_scored_final_belief_gap=scored["final_belief_gap"],
        n1_baseline_final_belief_gap=N1_BASELINE_BELIEF_GAP,
        u0_smaller_than_n1=(scored["final_belief_gap"]["mean"] < N1_BASELINE_BELIEF_GAP),
        note="non-gating, informational only -- PREREG Sec. 5 / scoping doc Part E")

    out = dict(
        block=307000, seed_base=SEED_BASE, n=N, t_ticks=T, warmup_ticks=WARMUP,
        abuser_half_width=ABUSER_HALF_WIDTH, victim_half_width=VICTIM_HALF_WIDTH,
        leak=LEAK, k_acc=K_ACC, discharge=DISCHARGE, recover_floor=RECOVER_FLOOR,
        k_self=K_SELF, k_co=K_CO, trickle_mag=TRICKLE_MAG,
        trickle_jitter_frac=TRICKLE_JITTER_FRAC,
        n_network_nodes=N_NETWORK_NODES, charm_weight=CHARM_WEIGHT,
        claim_weight=CLAIM_WEIGHT, instability_discount_weight=INSTABILITY_DISCOUNT_WEIGHT,
        harm_discount_weight=HARM_DISCOUNT_WEIGHT,
        concealment_benefit=CONCEALMENT_BENEFIT, honesty_benefit=HONESTY_BENEFIT,
        suspicion_cost_scale=SUSPICION_COST_SCALE,
        arms=arms,
        g_headline=g_headline,
        g_belief_gap_comparison=g_belief_gap_comparison,
        g_glass_box=glass_box_reconstruct(),
        g_ethics=ethics_restore_demo(),
        source_audit=source_audit(),
        discipline=discipline())
    os.makedirs(os.path.join(_ROOT, "results"), exist_ok=True)
    with open(os.path.join(_ROOT, "results", "abusive_u0_intent.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    main()
