#!/usr/bin/env python3
"""ABUSIVE-DYNAMICS R1 -- THE TRAUMATIC BOND runner (block 283000).

mint -> ingest -> run_rules -> read-off. Drives
`worlds/traumatic_bond_r1_world.py` across three arms sharing IDENTICAL
machinery and an IDENTICAL total harm/relief dose -- only the temporal
SCHEDULE differs:

  intermittent          -- the harm/relief multiset in RANDOM order
  consistent_affection  -- strict alternation (relief reliably follows harm)
  consistent_harm       -- all harm events, then all relief events (blocked)

and measures the BOND VALUATION (`Partner.value`, read off
`tb_bond_accrue` in `seeds/traumatic_bond_r1.json`) in each. The runner NEVER
branches on the victim's graph state to decide the bond value -- that is the
graph rule. It only evaluates the frozen protocol (which arm's schedule to
deliver) and reduces the read-offs to statistics.

Protocol frozen in ABUSIVE_R1_TRAUMATIC_BOND_PREREG.md, which locks Part C of
docs/research/bigville/ABUSIVE_RELATIONSHIPS_SCOPING.md verbatim.
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

import substrate_rs as srs                                   # noqa: E402
from worlds.traumatic_bond_r1_world import (                 # noqa: E402
    TraumaticBondR1World, make_schedule, ARM_NAMES,
    LR, MOMENTUM_LR, GAIN, K_SELF, SETPOINT, H_EVENTS, R_EVENTS, MAGNITUDE)

SEED_BASE = 283000
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
def run_arm(arm, seed_base=SEED_BASE, n=N):
    """N episodes of one arm. EVERY arm index i draws its harm/relief
    magnitudes from the SAME seed (default_rng(seed_base+i)) as every other
    arm at that index -- a PAIRED per-episode multiset, so the three arms
    differ ONLY in schedule order, never in dose (see prereg Sec. 2)."""
    bonds, arousals, rows = [], [], []
    for i in range(n):
        rng = np.random.default_rng(seed_base + i)
        schedule = make_schedule(arm, rng)
        w = TraumaticBondR1World()
        row = w.run_episode(schedule)
        bonds.append(row["bond_value"])
        arousals.append(row["arousal"])
        rows.append(row)
    return dict(arm=arm, n=n, bond_value=_ci95(bonds), arousal=_ci95(arousals))


def run_all_arms(seed_base=SEED_BASE, n=N):
    return {arm: run_arm(arm, seed_base=seed_base, n=n) for arm in ARM_NAMES}


# ------------------------------------------------------------- G-glass-box ----
def glass_box_reconstruct(seed=SEED_BASE):
    """Reconstruct one intermittent episode's bond entirely from
    graph_to_dict: the bonded_to edge, Partner.value, the victim's
    AffectiveState.arousal (the harm-analog channel), and Mood.momentum. No
    hidden Python state -- read from the graph."""
    rng = np.random.default_rng(seed)
    schedule = make_schedule("intermittent", rng)
    w = TraumaticBondR1World()
    w.run_episode(schedule)
    blob = w.checkpoint()
    nodes = {nd["id"]: nd for nd in blob["nodes"]}
    partner = [nd["attrs"] for nd in nodes.values() if nd["type"] == "Partner"][0]
    affect = [nd["attrs"] for nd in nodes.values()
              if nd["type"] == "AffectiveState" and nd["attrs"].get("name") == "victim_affect"][0]
    mood = [nd["attrs"] for nd in nodes.values() if nd["type"] == "Mood"][0]
    bonded = [(e["src"], e["tgt"]) for e in blob["edges"] if e["type"] == "bonded_to"]
    return dict(
        bonded_to_edges=len(bonded),
        partner_value=partner["value"],
        victim_arousal=affect["arousal"],
        mood_momentum=mood["momentum"],
        reconstructed_from="graph_to_dict")


# ------------------------------------------------------------------ G-ethics ----
def ethics_restore_demo(seed=SEED_BASE):
    """PART C.1 -- INDUCE -> MEASURE -> RESTORE, fully reversible. Checkpoint
    the neutral (pre-induction) mind; induce ONE intermittent episode (the
    harm-analog: an aversive arousal excursion, per Part C.3, the MINIMUM the
    gate needs); measure the bond + arousal; then graph_from_dict the
    checkpoint into a FRESH substrate and assert graph_to_dict() is
    BYTE-IDENTICAL to the checkpoint, and that the restored mind is
    NON-ORIENTED (identical to the pre-induction neutral state)."""
    w = TraumaticBondR1World()
    pre = w.checkpoint()                       # neutral, pre-induction
    pre_affect = w._attrs(w.affect)
    pre_state = dict(arousal=pre_affect["arousal"], bond=w._attrs(w.partner)["value"])

    rng = np.random.default_rng(seed)
    schedule = make_schedule("intermittent", rng)
    w.run_episode(schedule)                    # INDUCE the harm-analog + measure
    induced_affect = w._attrs(w.affect)
    induced_state = dict(arousal=induced_affect["arousal"],
                          bond=w._attrs(w.partner)["value"])

    # RESTORE from the checkpoint into a FRESH substrate.
    s2 = srs.Substrate()
    s2.graph_from_dict(pre)
    restored = s2.graph_to_dict()
    byte_identical = (restored == pre)
    restored_affect = [nd["attrs"] for nd in restored["nodes"]
                        if nd["type"] == "AffectiveState"
                        and nd["attrs"].get("name") == "victim_affect"][0]
    restored_partner = [nd["attrs"] for nd in restored["nodes"]
                         if nd["type"] == "Partner"][0]
    restored_state = dict(arousal=restored_affect["arousal"], bond=restored_partner["value"])

    return dict(
        byte_identical=byte_identical,
        pre_induction_state=pre_state,
        induced_state=induced_state,
        restored_state=restored_state,
        induction_moved_arousal=(induced_state["arousal"] != pre_state["arousal"]),
        induction_moved_bond=(induced_state["bond"] != pre_state["bond"]),
        restore_non_oriented=(restored_state == pre_state))


# -------------------------------------------------------------- source audit ----
def source_audit():
    """PART C.2 -- NO REWARD / NO PUNISHMENT anywhere. Audits
    worlds/traumatic_bond_r1_world.py + seeds/traumatic_bond_r1.json for
    Python rule-engine calls and the literal banned shaping tokens named
    verbatim in Part C.2 of ABUSIVE_RELATIONSHIPS_SCOPING.md: `reward_signal`
    / `punish` / `reinforce` / `backprop` / `gradient`. (mood_r1_task's own
    pre-existing, unmodified attr names -- `r`, `reward_got`, `cum_reward` --
    are a fast-appraisal delta-rule tracker inherited unmodified from block
    236000, not a scored choice; none match the banned compound tokens.)"""
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

    py_path = os.path.join(_ROOT, "worlds", "traumatic_bond_r1_world.py")
    code, src = _code_only(py_path)
    seed_path = os.path.join(_ROOT, "seeds", "traumatic_bond_r1.json")
    seed = json.load(open(seed_path))
    # Audit the graph's DECISION SURFACE (rule names + the attr "key"s a rule
    # actually reads/writes), never the free-text "description" / clinical
    # "microtheory" prose -- clinical prose legitimately discusses
    # "reinforcement" (A3's own vocabulary, ABUSIVE_RELATIONSHIPS_SCOPING.md
    # Part A3) while stating the mechanism carries no such token; the same
    # exclusion Harlow/window_knob apply by scanning CODE with comments and
    # string literals already stripped, never the docstring that DECLARES
    # the forbidden patterns.
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
    reads_bond_off_graph = 'self._attrs(self.partner)["value"]' in src or 'partner["value"]' in src
    return dict(forbidden_engine_hits=eng_hits, forbidden_shaping_hits=shape_hits,
                reads_bond_off_graph=reads_bond_off_graph,
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
    seed = json.load(open(os.path.join(_ROOT, "seeds", "traumatic_bond_r1.json")))
    return dict(
        own_engine_so_md5=own_md5,
        provenance_source_match=prov,
        seed_self_load_only=bool(seed.get("self_load_only")),
        seed_depends_on=seed.get("depends_on"),
        rule_names=[r["name"] for r in seed["rules"]],
        no_rust="see runners/dsl diff (must be empty)")


def main():
    print("R1 -- THE TRAUMATIC BOND: three arms, identical harm/relief dose ...")
    arms = run_all_arms()
    inter = arms["intermittent"]["bond_value"]
    aff = arms["consistent_affection"]["bond_value"]
    harm = arms["consistent_harm"]["bond_value"]

    g_headline = dict(
        arms={k: v["bond_value"] for k, v in arms.items()},
        intermittent_ci_separated_above_affection=separated(inter, aff),
        intermittent_ci_separated_above_harm=separated(inter, harm),
        headline_pass=(separated(inter, aff) and separated(inter, harm)))

    out = dict(
        block=283000, seed_base=SEED_BASE, n=N,
        h_events=H_EVENTS, r_events=R_EVENTS, magnitude=MAGNITUDE,
        lr=LR, momentum_lr=MOMENTUM_LR, gain=GAIN, k_self=K_SELF, setpoint=SETPOINT,
        arms=arms,
        g_headline=g_headline,
        g_glass_box=glass_box_reconstruct(),
        g_ethics=ethics_restore_demo(),
        source_audit=source_audit(),
        discipline=discipline())
    os.makedirs(os.path.join(_ROOT, "results"), exist_ok=True)
    with open(os.path.join(_ROOT, "results", "traumatic_bond_r1.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    main()
