#!/usr/bin/env python3
"""ABUSIVE-DYNAMICS R4 -- LEARNED HELPLESSNESS runner (block 292000).

mint -> ingest -> run_rules -> read-off. Drives
`worlds/abusive_r4_learned_helplessness_world.py` across two arms sharing
IDENTICAL machinery -- a CONTINGENT-ESCAPE arm (an attempt always succeeds)
vs a NON-CONTINGENT arm (an attempt is always blocked -- outcome
INDEPENDENT of the action, the classic escapable/inescapable-shock
yoked-pair operationalisation) -- and measures (1) the final
CONTINGENCY-BELIEF PRIOR (`EscapeDecision.contingency_prior`, read off
`r4_belief_update` in `seeds/abusive_r4_learned_helplessness.json`) and (2)
the ESCAPE-ATTEMPT RATE (fraction of ticks the graph's own `r4_choose`
Argmax chose to attempt). The runner NEVER branches on the victim's graph
state to decide whether to attempt escape -- that is the graph rule. It only
evaluates the frozen protocol (which arm's outcome-resolution function to
apply) and reduces the read-offs to statistics.

Protocol frozen in ABUSIVE_R4_LEARNED_HELPLESSNESS_PREREG.md, which locks
Part C of docs/research/bigville/ABUSIVE_RELATIONSHIPS_SCOPING.md verbatim.
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
from worlds.abusive_r4_learned_helplessness_world import (            # noqa: E402
    AbusiveR4LearnedHelplessnessWorld, ARM_NAMES,
    LR, ESCAPE_VALUE, ATTEMPT_COST, K_SELF, SETPOINT,
    RELIEF_MAG, BLOCK_MAG, P0_MEAN, P0_JITTER)

SEED_BASE = 292000
N = 200
T_TICKS = 60


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
    drawn from the SAME seed (default_rng(SEED_BASE+i)) for both arms at a
    given episode index i, so the two arms differ ONLY in the outcome
    resolution (contingent vs non-contingent), never in the starting belief
    -- a paired per-episode design, matching R1's own paired
    harm/relief-multiset construction (ABUSIVE_R1_TRAUMATIC_BOND_PREREG.md
    Sec. 2)."""
    p0 = float(rng.normal(mean, jitter))
    return min(0.95, max(0.05, p0))


# --------------------------------------------------------------- main measurement
def run_arm(arm, seed_base=SEED_BASE, n=N, ticks=T_TICKS):
    """N episodes of one arm. EVERY arm draws its initial contingency-prior
    from the SAME seed (default_rng(seed_base+i)) at episode index i as
    every other arm at that index -- a PAIRED per-episode design; the two
    arms differ ONLY in the outcome-resolution function (see
    worlds/abusive_r4_learned_helplessness_world.py's resolve_outcome)."""
    priors, rates, rows = [], [], []
    for i in range(n):
        rng = np.random.default_rng(seed_base + i)
        p0 = _sample_p0(rng)
        w = AbusiveR4LearnedHelplessnessWorld(arm, p0=p0)
        row = w.run_episode(ticks)
        priors.append(row["contingency_prior"])
        rates.append(row["attempt_rate"])
        rows.append(row)
    return dict(arm=arm, n=n, ticks=ticks,
                contingency_prior=_ci95(priors), attempt_rate=_ci95(rates))


def run_all_arms(seed_base=SEED_BASE, n=N, ticks=T_TICKS):
    return {arm: run_arm(arm, seed_base=seed_base, n=n, ticks=ticks) for arm in ARM_NAMES}


# ------------------------------------------------------------- G-glass-box ----
def glass_box_reconstruct(seed=SEED_BASE, ticks=T_TICKS):
    """Reconstruct one contingent-arm episode entirely from graph_to_dict:
    the has_escape_decision/has_affective_state edges,
    EscapeDecision.contingency_prior/chosen_action, and the harm-analog
    AffectiveState.arousal. No hidden Python state -- read from the graph."""
    rng = np.random.default_rng(seed)
    p0 = _sample_p0(rng)
    w = AbusiveR4LearnedHelplessnessWorld("contingent", p0=p0)
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
        victim_arousal=affect["arousal"],
        reconstructed_from="graph_to_dict")


# ------------------------------------------------------------------ G-ethics ----
def ethics_restore_demo(seed=SEED_BASE, ticks=20):
    """PART C.1 -- INDUCE -> MEASURE -> RESTORE, fully reversible. Checkpoint
    the neutral (pre-induction) mind; induce ONE non-contingent episode (the
    harm-analog: blocked escape attempts driving both the contingency prior
    down and the harm-analog arousal up, per Part C.3, the MINIMUM the gate
    needs); measure; then graph_from_dict the checkpoint into a FRESH
    substrate and assert graph_to_dict() is BYTE-IDENTICAL to the
    checkpoint, and that the restored mind is NON-ORIENTED (identical to the
    pre-induction neutral state)."""
    w = AbusiveR4LearnedHelplessnessWorld("noncontingent", p0=P0_MEAN)
    pre = w.checkpoint()                       # neutral, pre-induction
    pre_dec = w._attrs(w.dec)
    pre_state = dict(prior=pre_dec["contingency_prior"], arousal=w._attrs(w.affect)["arousal"])

    w.run_episode(ticks)                       # INDUCE the harm-analog + measure
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
    """PART C.2 -- NO REWARD / NO PUNISHMENT anywhere. Audits
    worlds/abusive_r4_learned_helplessness_world.py + the decision surface of
    seeds/abusive_r4_learned_helplessness.json for Python rule-engine calls
    and the literal banned shaping tokens named verbatim in Part C.2 of
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

    py_path = os.path.join(_ROOT, "worlds", "abusive_r4_learned_helplessness_world.py")
    code, src = _code_only(py_path)
    seed_path = os.path.join(_ROOT, "seeds", "abusive_r4_learned_helplessness.json")
    seed = json.load(open(seed_path))
    # Audit the graph's DECISION SURFACE (rule names + the attr "key"s a rule
    # actually reads/writes), never the free-text "description" / clinical
    # "microtheory" prose -- matching R1/R2's own audit scoping exactly
    # (their false-positive lesson: clinical prose legitimately discusses
    # "reinforcement"/"reward" while the mechanism itself carries no such
    # token).
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
    seed = json.load(open(os.path.join(_ROOT, "seeds", "abusive_r4_learned_helplessness.json")))
    return dict(
        own_engine_so_md5=own_md5,
        provenance_source_match=prov,
        seed_self_load_only=bool(seed.get("self_load_only")),
        seed_depends_on=seed.get("depends_on"),
        rule_names=[r["name"] for r in seed["rules"]],
        n_new_rules=len(seed["rules"]),
        no_rust="see runners/dsl diff (must be empty)")


def main():
    print("R4 -- LEARNED HELPLESSNESS: contingent-escape vs non-contingent arms ...")
    arms = run_all_arms()
    con = arms["contingent"]
    non = arms["noncontingent"]

    g_headline = dict(
        arms={k: dict(contingency_prior=v["contingency_prior"], attempt_rate=v["attempt_rate"])
              for k, v in arms.items()},
        contingent_prior_ci_separated_above_noncontingent=separated(
            con["contingency_prior"], non["contingency_prior"]),
        contingent_rate_ci_separated_above_noncontingent=separated(
            con["attempt_rate"], non["attempt_rate"]),
        headline_pass=(separated(con["contingency_prior"], non["contingency_prior"])
                       and separated(con["attempt_rate"], non["attempt_rate"])))

    out = dict(
        block=292000, seed_base=SEED_BASE, n=N, ticks=T_TICKS,
        lr=LR, escape_value=ESCAPE_VALUE, attempt_cost=ATTEMPT_COST,
        k_self=K_SELF, setpoint=SETPOINT, relief_mag=RELIEF_MAG, block_mag=BLOCK_MAG,
        p0_mean=P0_MEAN, p0_jitter=P0_JITTER,
        arms=arms,
        g_headline=g_headline,
        g_glass_box=glass_box_reconstruct(),
        g_ethics=ethics_restore_demo(),
        source_audit=source_audit(),
        discipline=discipline())
    os.makedirs(os.path.join(_ROOT, "results"), exist_ok=True)
    with open(os.path.join(_ROOT, "results", "abusive_r4_learned_helplessness.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    main()
