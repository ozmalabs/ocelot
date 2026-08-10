#!/usr/bin/env python3
"""HARLOW D1 runner (block 233000) — mint -> ingest -> run_rules -> read-off.

Drives `worlds/harlow_world.py` across N infants in two conditions (contact
drive present / ablated), reads off the graph's proximity + flee decisions and
the regulator state, and writes `results/harlow_d1.json`. The runner NEVER
branches on the infant's graph state to decide the infant's action — that is the
Argmax rule in `seeds/harlow_attachment.json`. It only evaluates the frozen
protocol and reduces the read-offs to statistics.

Protocol frozen in HARLOW_D1_PREREG.md.
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import substrate_rs as srs                       # noqa: E402
from worlds.harlow_world import HarlowWorld       # noqa: E402

# ---- frozen confirmatory constants (HARLOW_D1_PREREG.md) --------------------
SEED_BASE = 233000
N = 200
T_BASE = 60
T_STRESS = 10


def _infant_params(rng):
    return dict(
        c_contact0=float(rng.uniform(10.0, 60.0)),
        c_hunger0=float(rng.uniform(20.0, 80.0)),
        contact_decay=float(rng.uniform(50.0, 70.0)),
        hunger_decay=float(rng.uniform(10.0, 20.0)))


def run_infant(seed, *, contact_drive):
    rng = np.random.default_rng(seed)
    p = _infant_params(rng)
    w = HarlowWorld(contact_drive=contact_drive, **p)
    w.run_baseline(T_BASE)
    prox = w.proximity()
    st = w.run_stress(T_STRESS)
    flee = st["flee"]
    flee_cloth = flee["cloth"] / T_STRESS
    return dict(cloth_frac=prox["cloth_frac"],
                cloth_ticks=prox["cloth_ticks"], wire_ticks=prox["wire_ticks"],
                cloth_bond=prox["cloth_bond"], wire_bond=prox["wire_bond"],
                flee_cloth=flee_cloth, flee=flee)


def _ci95(xs):
    xs = list(xs)
    n = len(xs)
    m = sum(xs) / n
    if n < 2:
        return m, 0.0, m, m
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    half = 1.96 * sd / math.sqrt(n)
    return m, sd, m - half, m + half


def run_condition(contact_drive):
    rows = [run_infant(SEED_BASE + i, contact_drive=contact_drive) for i in range(N)]
    cf = [r["cloth_frac"] for r in rows]
    fc = [r["flee_cloth"] for r in rows]
    cf_m, cf_sd, cf_lo, cf_hi = _ci95(cf)
    fc_m, fc_sd, fc_lo, fc_hi = _ci95(fc)
    return dict(
        n=N,
        cloth_frac=dict(mean=cf_m, sd=cf_sd, ci_lo=cf_lo, ci_hi=cf_hi),
        flee_cloth=dict(mean=fc_m, sd=fc_sd, ci_lo=fc_lo, ci_hi=fc_hi),
        n_infants_cloth_preferred=sum(1 for x in cf if x > 0.5),
        rows=rows)


def separated(a, b):
    """True iff condition A's CI lower bound is strictly above B's CI upper bound."""
    return a["ci_lo"] > b["ci_hi"]


# ------------------------------------------------------------- G-glass-box ----
def glass_box_reconstruct(seed=SEED_BASE):
    """Reconstruct one infant's bond from graph_to_dict alone: the approach_target
    edge, the mothers' proximity/bond_strength, and the regulator arousal on a
    comforted vs deprived tick. No hidden Python state — read from the graph."""
    w = HarlowWorld(contact_drive=True, **_infant_params(np.random.default_rng(seed)))
    dep = w.step(stress=False)              # first tick: contact deprived
    w.run_baseline(T_BASE)
    blob = w.checkpoint()
    nodes = {n["id"]: n for n in blob["nodes"]}
    mothers = {nodes[i]["attrs"]["name"]: nodes[i]["attrs"]
               for i in nodes if nodes[i]["type"] == "Mother"}
    # the approach_target edge, read from the serialised graph
    at = [e["tgt"] for e in blob["edges"] if e["type"] == "approach_target"]
    at_names = [nodes[t]["attrs"]["name"] for t in at]
    comforted = w.regulator_state()        # after living on cloth
    return dict(
        approach_target=at_names,
        cloth=dict(proximity=mothers["cloth"]["proximity"],
                   bond_strength=mothers["cloth"]["bond_strength"]),
        wire=dict(proximity=mothers["wire"]["proximity"],
                  bond_strength=mothers["wire"]["bond_strength"]),
        regulator_arousal_deprived_tick=dep["arousal"],
        regulator_arousal_comforted=comforted["arousal"],
        reconstructed_from="graph_to_dict")


# ---------------------------------------------------------------- G-ethics ----
def ethics_restore_demo(seed=SEED_BASE):
    """induce -> measure -> RESTORE, byte-identical. Checkpoint the neutral
    pre-stress mind; induce the stress phase; rebuild from the checkpoint and
    confirm graph_to_dict() is byte-identical; the restored regulator is
    non-oriented (identical to pre-stress)."""
    w = HarlowWorld(contact_drive=True, **_infant_params(np.random.default_rng(seed)))
    w.run_baseline(T_BASE)
    pre = w.checkpoint()                    # neutral, pre-stress
    pre_reg = w.regulator_state()
    st = w.run_stress(T_STRESS)             # induce distress
    stressed_reg = w.regulator_state()
    # RESTORE from the checkpoint into a fresh substrate
    s2 = srs.Substrate()
    s2.graph_from_dict(pre)
    restored = s2.graph_to_dict()
    byte_identical = (restored == pre)
    # regulator in the restored graph == pre-stress regulator (non-oriented).
    # Select the INFANT's projected AffectiveState (the affective_state_core seed
    # also installs a separate neutral agent-root AffectiveState).
    aff = [n["attrs"] for n in restored["nodes"]
           if n["type"] == "AffectiveState" and n["attrs"].get("name") == "infant_affect"][0]
    restored_reg = dict(valence=aff["valence"], arousal=aff["arousal"], securing=aff["securing"])
    return dict(byte_identical=byte_identical,
                pre_stress_regulator=pre_reg,
                stressed_regulator=stressed_reg,
                restored_regulator=restored_reg,
                stress_moved_arousal=(stressed_reg["arousal"] != pre_reg["arousal"]),
                restore_non_oriented=(restored_reg == pre_reg))


# ------------------------------------------------------------ source audit ----
def source_audit():
    """No Python decides attachment. Forbidden: Python rule-engine calls, and any
    if/else that reads a Mother/Drive/regulator attr to SELECT the infant's
    action. The selection is the Argmax rule; the adapter's conditionals are over
    WORLD provision flags only."""
    import io
    import tokenize
    path = os.path.join(_ROOT, "worlds", "harlow_world.py")
    src = open(path).read()
    # strip comments + string literals so the audit inspects CODE, not the
    # docstring that declares which patterns are forbidden.
    code_toks = []
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type in (tokenize.COMMENT, tokenize.STRING):
            continue
        code_toks.append(tok.string)
    code = " ".join(code_toks)
    forbidden = ["graph_rewrite", "make_rule", "_match", "_apply", "add_rule"]
    hits = [f for f in forbidden if f in code]
    # the approach decision must be read via the approach_target edge, not chosen
    reads_edge = "neighbours(self.infant, \"approach_target\")" in src
    return dict(forbidden_hits=hits, reads_approach_target_edge=reads_edge,
                clean=(not hits and reads_edge))


def main():
    A = run_condition(contact_drive=True)
    B = run_condition(contact_drive=False)
    out = dict(
        block=233000,
        base_sha="3c4666ceba0b0ceef1db4030d941a5cd66b5f949",
        seed_base=SEED_BASE, n=N, t_base=T_BASE, t_stress=T_STRESS,
        condition_A_contact_drive=A,
        condition_B_ablated=B,
        g_harlow=dict(
            cloth_frac_A=A["cloth_frac"], cloth_frac_B=B["cloth_frac"],
            proximity_ci_separated=separated(A["cloth_frac"], B["cloth_frac"]),
            proximity_above_half=A["cloth_frac"]["ci_lo"] > 0.5,
            flee_A=A["flee_cloth"], flee_B=B["flee_cloth"],
            flee_ci_separated=separated(A["flee_cloth"], B["flee_cloth"])),
        g_ablation=dict(
            cloth_frac_B_ci_hi=B["cloth_frac"]["ci_hi"],
            cloth_frac_A_ci_lo=A["cloth_frac"]["ci_lo"],
            preference_disappears_or_inverts=B["cloth_frac"]["ci_hi"] < A["cloth_frac"]["ci_lo"]),
        g_glass_box=glass_box_reconstruct(),
        g_ethics=ethics_restore_demo(),
        source_audit=source_audit(),
    )
    # drop the per-infant rows from the persisted file (keep it small); keep summaries
    for c in ("condition_A_contact_drive", "condition_B_ablated"):
        out[c] = {k: v for k, v in out[c].items() if k != "rows"}
    os.makedirs(os.path.join(_ROOT, "results"), exist_ok=True)
    with open(os.path.join(_ROOT, "results", "harlow_d1.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    main()
