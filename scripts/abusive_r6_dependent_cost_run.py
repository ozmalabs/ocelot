#!/usr/bin/env python3
"""ABUSIVE-DYNAMICS R6 -- DEPENDENT/RESOURCE-COST DEVALUATION runner (block 361000).

mint -> ingest -> run_rules -> read-off. Drives
`worlds/abusive_r6_dependent_cost_world.py` across two arms sharing IDENTICAL
machinery AND identical (deterministic, always-succeeds) escape contingency
-- a ZERO-DEPENDENTS arm (`dependent_cost=0.0`, the harness-neutrality
replication of R4's own contingent arm) vs a HIGH-DEPENDENTS arm
(`dependent_cost=10.0`, large enough that escape_value - attempt_cost -
dependent_cost < 0 even at contingency_prior=1.0, ABUSIVE_R6_DEPENDENT_
COST_PREREG.md Sec. 3) -- and measures (1) the final CONTINGENCY-BELIEF
PRIOR (`EscapeDecision.contingency_prior`, read off R4's own unmodified
`r4_belief_update`) and (2) the ESCAPE-ATTEMPT RATE (fraction of ticks the
graph's own `r4_choose` Argmax chose to attempt). The runner NEVER branches
on the victim's graph state to decide whether to attempt escape -- that is
the graph rule. It only evaluates the frozen protocol (which `dependent_cost`
to set at construction) and reduces the read-offs to statistics.

Protocol frozen in ABUSIVE_R6_DEPENDENT_COST_PREREG.md, which locks Part D
of ABUSIVE_RELATIONSHIPS_BARRIERS_AND_RETURN_SCOPING.md verbatim.
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

import substrate_rs as srs                                            # noqa: E402
from worlds.abusive_r6_dependent_cost_world import (                  # noqa: E402
    AbusiveR6DependentCostWorld, ARM_NAMES, ARM_DEPENDENT_COST,
    ZERO_DEPENDENT_COST, HIGH_DEPENDENT_COST,
    LR, ESCAPE_VALUE, ATTEMPT_COST, K_SELF, SETPOINT,
    RELIEF_MAG, BLOCK_MAG, P0_MEAN, P0_JITTER)

SEED_BASE = 361000
N = 200
T_TICKS = 60

# R4's own landed contingent-arm numbers (results/abusive_r4_learned_helplessness.json,
# ABUSIVE_R4_LEARNED_HELPLESSNESS_RESULTS.md), reproduced here as literal
# comparison targets for the harness-neutrality check -- never re-derived,
# never re-measured, read once from R4's own committed results.
R4_CONTINGENT_PRIOR_MEAN = 0.99999999964
R4_CONTINGENT_RATE_MEAN = 1.000
R4_NONCONTINGENT_PRIOR_MEAN = 0.2560


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
    bound (A CI-separated BELOW B)."""
    return a["ci_hi"] < b["ci_lo"]


def _sample_p0(rng, mean=P0_MEAN, jitter=P0_JITTER):
    """MECHANICAL per-episode jitter of the initial contingency-prior --
    matches R4's own _sample_p0 exactly (same mean/jitter/clip), drawn from
    a seed unique to this rung's own block (SEED_BASE=361000, distinct from
    R4's 292000)."""
    p0 = float(rng.normal(mean, jitter))
    return min(0.95, max(0.05, p0))


# --------------------------------------------------------------- main measurement
def run_arm(arm, seed_base=SEED_BASE, n=N, ticks=T_TICKS):
    """N episodes of one arm. Each episode draws its initial
    contingency-prior from `default_rng(seed_base+i)` at episode index i;
    both R6 arms share the SAME deterministic, always-succeeds outcome
    resolution -- they differ ONLY in `dependent_cost` (see
    worlds/abusive_r6_dependent_cost_world.py)."""
    dependent_cost = ARM_DEPENDENT_COST[arm]
    priors, rates, rows = [], [], []
    for i in range(n):
        rng = np.random.default_rng(seed_base + i)
        p0 = _sample_p0(rng)
        w = AbusiveR6DependentCostWorld(dependent_cost, p0=p0)
        row = w.run_episode(ticks)
        priors.append(row["contingency_prior"])
        rates.append(row["attempt_rate"])
        rows.append(row)
    return dict(arm=arm, dependent_cost=dependent_cost, n=n, ticks=ticks,
                contingency_prior=_ci95(priors), attempt_rate=_ci95(rates))


def run_all_arms(seed_base=SEED_BASE, n=N, ticks=T_TICKS):
    return {arm: run_arm(arm, seed_base=seed_base, n=n, ticks=ticks) for arm in ARM_NAMES}


# ------------------------------------------------------------- G-glass-box ----
def glass_box_reconstruct(seed=SEED_BASE, ticks=T_TICKS):
    """Reconstruct one ZERO-DEPENDENTS episode entirely from graph_to_dict:
    the has_escape_decision/has_affective_state edges,
    EscapeDecision.contingency_prior/chosen_action/dependent_cost, and the
    harm-analog AffectiveState.arousal. No hidden Python state -- read from
    the graph."""
    rng = np.random.default_rng(seed)
    p0 = _sample_p0(rng)
    w = AbusiveR6DependentCostWorld(ZERO_DEPENDENT_COST, p0=p0)
    w.run_episode(ticks)
    blob = w.checkpoint()
    nodes = {nd["id"]: nd for nd in blob["nodes"]}
    dec = [nd["attrs"] for nd in nodes.values() if nd["type"] == "EscapeDecision"][0]
    affect = [nd["attrs"] for nd in nodes.values()
              if nd["type"] == "AffectiveState" and nd["attrs"].get("name") == "victim_affect"][0]
    dec_edges = [(e["src"], e["tgt"]) for e in blob["edges"] if e["type"] == "has_escape_decision"]
    return dict(
        has_escape_decision_edges=len(dec_edges),
        contingency_prior=dec["contingency_prior"],
        chosen_action=dec["chosen_action"],
        dependent_cost=dec["dependent_cost"],
        victim_arousal=affect["arousal"],
        reconstructed_from="graph_to_dict")


# ------------------------------------------------------------------ G-ethics ----
def ethics_restore_demo(seed=SEED_BASE, ticks=20):
    """PART D.1 -- INDUCE -> MEASURE -> RESTORE, fully reversible. Uses the
    ZERO-DEPENDENTS arm (`dependent_cost=0.0`, contingent) for the
    induction, NOT the HIGH-DEPENDENTS arm -- disclosed and reasoned in
    ABUSIVE_R6_DEPENDENT_COST_PREREG.md Sec. 4: HIGH-DEPENDENTS' entire
    predicted finding is that NOTHING moves (no attempt is ever made, so no
    outcome is ever delivered, so neither the belief nor the harm-analog
    arousal ever fires), which would make the restore gate itself vacuous
    (nothing to verify was reversed). ZERO-DEPENDENTS exercises R6's own
    seed composition (R4's unmodified rules PLUS r6_appraise_attempt_
    dependent, numerically a no-op at dependent_cost=0) and genuinely moves
    state: the belief climbs and the harm-analog arousal is repeatedly
    pushed by the relief magnitude on every delivered outcome. Checkpoint
    the neutral (pre-induction) mind; induce ONE minimal 20-tick episode;
    measure; then graph_from_dict the checkpoint into a FRESH substrate and
    assert graph_to_dict() is BYTE-IDENTICAL to the checkpoint, and that the
    restored mind is NON-ORIENTED (identical to the pre-induction neutral
    state)."""
    w = AbusiveR6DependentCostWorld(ZERO_DEPENDENT_COST, p0=P0_MEAN)
    pre = w.checkpoint()                       # neutral, pre-induction
    pre_dec = w._attrs(w.dec)
    pre_state = dict(prior=pre_dec["contingency_prior"], arousal=w._attrs(w.affect)["arousal"])

    w.run_episode(ticks)                       # INDUCE + measure
    induced_dec = w._attrs(w.dec)
    induced_state = dict(prior=induced_dec["contingency_prior"], arousal=w._attrs(w.affect)["arousal"])

    # RESTORE from the checkpoint into a FRESH substrate.
    s2 = srs.Substrate()
    s2.graph_from_dict(pre)
    restored = s2.graph_to_dict()
    byte_identical = (restored == pre)
    restored_dec = [nd["attrs"] for nd in restored["nodes"] if nd["type"] == "EscapeDecision"][0]
    restored_affect = [nd["attrs"] for nd in restored["nodes"]
                        if nd["type"] == "AffectiveState"
                        and nd["attrs"].get("name") == "victim_affect"][0]
    restored_state = dict(prior=restored_dec["contingency_prior"], arousal=restored_affect["arousal"])

    return dict(
        byte_identical=byte_identical,
        pre_induction_state=pre_state,
        induced_state=induced_state,
        restored_state=restored_state,
        induction_moved_prior=(induced_state["prior"] != pre_state["prior"]),
        induction_moved_arousal=(induced_state["arousal"] != pre_state["arousal"]),
        restore_non_oriented=(restored_state == pre_state))


# -------------------------------------------------------------- source audit ----
def source_audit():
    """PART D.2 -- NO REWARD / NO PUNISHMENT anywhere. Audits
    worlds/abusive_r6_dependent_cost_world.py + the decision surface of
    seeds/abusive_r6_dependent_cost.json for Python rule-engine calls and
    the literal banned shaping tokens named verbatim in Part D.2 of
    ABUSIVE_RELATIONSHIPS_BARRIERS_AND_RETURN_SCOPING.md: `reward_signal` /
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

    py_path = os.path.join(_ROOT, "worlds", "abusive_r6_dependent_cost_world.py")
    code, src = _code_only(py_path)
    seed_path = os.path.join(_ROOT, "seeds", "abusive_r6_dependent_cost.json")
    seed = json.load(open(seed_path))
    # Audit the graph's DECISION SURFACE (rule names + the attr "key"s a rule
    # actually reads/writes), never the free-text "description" / clinical
    # "microtheory" prose -- matching R1-R5's own audit scoping exactly.
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
    reads_prior_off_graph = 'self._attrs(self.dec)["contingency_prior"]' in src \
        or 'dec["contingency_prior"]' in src
    return dict(forbidden_engine_hits=eng_hits, forbidden_shaping_hits=shape_hits,
                reads_prior_off_graph=reads_prior_off_graph,
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
    seed = json.load(open(os.path.join(_ROOT, "seeds", "abusive_r6_dependent_cost.json")))
    return dict(
        own_engine_so_md5=own_md5,
        provenance_source_match=prov,
        seed_self_load_only=bool(seed.get("self_load_only")),
        seed_depends_on=seed.get("depends_on"),
        rule_names=[r["name"] for r in seed["rules"]],
        n_new_rules=len(seed["rules"]),
        no_rust="see runners/dsl diff (must be empty)")


def main():
    print("R6 -- DEPENDENT-COST DEVALUATION: zero-dependents vs high-dependents arms ...")
    arms = run_all_arms()
    zero = arms["zero_dependents"]
    high = arms["high_dependents"]

    g_harness_neutrality = dict(
        zero_dependents_attempt_rate_mean=zero["attempt_rate"]["mean"],
        zero_dependents_contingency_prior_mean=zero["contingency_prior"]["mean"],
        r4_contingent_attempt_rate_mean=R4_CONTINGENT_RATE_MEAN,
        r4_contingent_prior_mean=R4_CONTINGENT_PRIOR_MEAN,
        attempt_rate_matches=(zero["attempt_rate"]["mean"] == 1.0),
        prior_in_r4_range=(zero["contingency_prior"]["mean"] > 0.999),
        harness_neutral=(zero["attempt_rate"]["mean"] == 1.0
                          and zero["contingency_prior"]["mean"] > 0.999))

    g_headline = dict(
        arms={k: dict(contingency_prior=v["contingency_prior"], attempt_rate=v["attempt_rate"])
              for k, v in arms.items()},
        high_rate_ci_separated_below_zero=separated_below(
            high["attempt_rate"], zero["attempt_rate"]),
        headline_pass=separated_below(high["attempt_rate"], zero["attempt_rate"]),
        dissociation=dict(
            high_dependents_contingency_prior_mean=high["contingency_prior"]["mean"],
            high_dependents_attempt_rate_mean=high["attempt_rate"]["mean"],
            zero_dependents_contingency_prior_mean=zero["contingency_prior"]["mean"],
            r4_noncontingent_trap_prior_mean=R4_NONCONTINGENT_PRIOR_MEAN,
            prior_near_p0_undisturbed=(abs(high["contingency_prior"]["mean"] - P0_MEAN) < 3 * P0_JITTER)))

    out = dict(
        block=361000, seed_base=SEED_BASE, n=N, ticks=T_TICKS,
        lr=LR, escape_value=ESCAPE_VALUE, attempt_cost=ATTEMPT_COST,
        zero_dependent_cost=ZERO_DEPENDENT_COST, high_dependent_cost=HIGH_DEPENDENT_COST,
        k_self=K_SELF, setpoint=SETPOINT, relief_mag=RELIEF_MAG, block_mag=BLOCK_MAG,
        p0_mean=P0_MEAN, p0_jitter=P0_JITTER,
        arms=arms,
        g_harness_neutrality=g_harness_neutrality,
        g_headline=g_headline,
        g_glass_box=glass_box_reconstruct(),
        g_ethics=ethics_restore_demo(),
        source_audit=source_audit(),
        discipline=discipline())
    os.makedirs(os.path.join(_ROOT, "results"), exist_ok=True)
    with open(os.path.join(_ROOT, "results", "abusive_r6_dependent_cost.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    main()
