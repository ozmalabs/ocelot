#!/usr/bin/env python3
"""AROUSAL / WINDOW-OF-TOLERANCE + CO-REGULATION runner (block 239000).

mint -> ingest -> run_rules -> read-off. Drives `worlds/coreg_dyad_world.py`
across N infants in three caregiver conditions (regulated present / absent /
dysregulated present) plus the plasticity arms (repeated co-regulation vs
repeated unsupported stress), reads off return-to-window times and the window
band / safety prior from the graph, and reduces them to CIs. The runner NEVER
branches on the infant's arousal to decide regulation -- that is the rule set in
`seeds/arousal_window_coreg.json`, riding the REAL `AffectiveState.arousal`.

Protocol frozen in AROUSAL_WOT_PREREG.md.
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

import substrate_rs as srs                            # noqa: E402
from worlds.coreg_dyad_world import CoregDyadWorld, RETURN_CAP  # noqa: E402

SEED_BASE = 239000
N = 60
N_EPISODES = 15


def _params(rng):
    return dict(half_width0=float(rng.uniform(20.0, 40.0)),
                stress_mag=float(rng.uniform(80.0, 140.0)))


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
    """A's CI lower bound strictly above B's CI upper bound."""
    return a["ci_lo"] > b["ci_hi"]


# ---------------------------------------------------------- G-co-regulation ----
def _one_return(seed, *, caregiver_present, regulated_caregiver):
    rng = np.random.default_rng(seed)
    w = CoregDyadWorld(caregiver_present=caregiver_present,
                       regulated_caregiver=regulated_caregiver, **_params(rng))
    ep = w.run_episode()
    return ep["return_ticks"], int(ep["censored"])


def coreg_arm(caregiver_present, regulated_caregiver):
    rows = [_one_return(SEED_BASE + i, caregiver_present=caregiver_present,
                        regulated_caregiver=regulated_caregiver) for i in range(N)]
    rt = [r[0] for r in rows]
    cens = [r[1] for r in rows]
    return dict(return_ticks=_ci95(rt), censored_frac=sum(cens) / len(cens))


# ------------------------------------------------------- plasticity arms ----
def _plasticity(seed, *, caregiver_present, regulated_caregiver):
    rng = np.random.default_rng(seed)
    w = CoregDyadWorld(caregiver_present=caregiver_present,
                       regulated_caregiver=regulated_caregiver, **_params(rng))
    hw0 = w.readout()["half_width"]
    sp0 = w.readout()["safety_prior"]
    for _ in range(N_EPISODES):
        w.run_episode()
        for _ in range(3):                    # settle back toward setpoint
            w.step(stress=False)
    r = w.readout()
    return dict(hw0=hw0, hw1=r["half_width"], sp0=sp0, sp1=r["safety_prior"],
                widen=r["widen_count"], narrow=r["narrow_count"])


def plasticity_arm(caregiver_present, regulated_caregiver):
    rows = [_plasticity(SEED_BASE + 1000 + i, caregiver_present=caregiver_present,
                        regulated_caregiver=regulated_caregiver) for i in range(N)]
    return dict(
        hw_initial=_ci95([r["hw0"] for r in rows]),
        hw_final=_ci95([r["hw1"] for r in rows]),
        safety_initial=_ci95([r["sp0"] for r in rows]),
        safety_final=_ci95([r["sp1"] for r in rows]),
        widen_count=_ci95([r["widen"] for r in rows]),
        narrow_count=_ci95([r["narrow"] for r in rows]))


# ---------------------------------------------------------------- G-glass-box ----
def glass_box_reconstruct(seed=SEED_BASE):
    """Reconstruct one co-regulation episode from graph_to_dict alone: the
    infant AffectiveState.arousal, the WindowOfTolerance band, the caregiver's
    arousal, and the attended_by coupling edge -- all readable graph state."""
    rng = np.random.default_rng(seed)
    w = CoregDyadWorld(caregiver_present=True, regulated_caregiver=True, **_params(rng))
    ep = w.run_episode()
    blob = w.checkpoint()
    nodes = {n["id"]: n for n in blob["nodes"]}
    aff = {nodes[i]["attrs"]["name"]: nodes[i]["attrs"]
           for i in nodes if nodes[i]["type"] == "AffectiveState"}
    wot = [nodes[i]["attrs"] for i in nodes if nodes[i]["type"] == "WindowOfTolerance"][0]
    coupling = [(e["src"], e["tgt"]) for e in blob["edges"] if e["type"] == "attended_by"]
    return dict(
        infant_arousal=aff["infant_affect"]["arousal"],
        infant_window=dict(lo=wot["lo"], hi=wot["hi"], half_width=wot["half_width"],
                           safety_prior=wot["safety_prior"]),
        caregiver_arousal=aff["caregiver_affect"]["arousal"],
        coupling_edges=len(coupling),
        returned_to_window=(ep["final"]["dysregulated"] == 0.0),
        widened=(wot["half_width"] > ep["final"]["half_width"] - 1e-9 and wot["widen_count"] >= 1.0),
        reconstructed_from="graph_to_dict")


# ------------------------------------------------------------ source audit ----
def source_audit():
    """No Python decides regulation. Forbidden: Python rule-engine calls, and any
    reward/punishment token (this rung models dysregulation as a STATE, never a
    badness -- Greene). The world adapter's conditionals are over WORLD state
    only (stress tick / caregiver present / caregiver regulated)."""
    path = os.path.join(_ROOT, "worlds", "coreg_dyad_world.py")
    src = open(path).read()
    code_toks = []
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type in (tokenize.COMMENT, tokenize.STRING):
            continue
        code_toks.append(tok.string)
    code = " ".join(code_toks)
    forbidden_engine = ["graph_rewrite", "make_rule", "_match", "_apply", "add_rule"]
    forbidden_reward = ["reward", "punish", "penalty", "penalis", "penaliz"]
    eng_hits = [f for f in forbidden_engine if f in code]
    rew_hits = [f for f in forbidden_reward if f in code.lower()]
    reads_arousal = "arousal" in code
    return dict(forbidden_engine_hits=eng_hits, forbidden_reward_hits=rew_hits,
                reads_arousal_off_graph=reads_arousal,
                clean=(not eng_hits and not rew_hits))


# --------------------------------------------------------------- G-discipline ----
CANON_SHARED_SO = ("/home/matt/ozma/internal/research/experiments/gamma-substrate/"
                   "runners/dsl/python/substrate_rs/_native.abi3.so")


def discipline():
    own_so = os.path.join(_ROOT, "runners", "dsl", "python", "substrate_rs",
                          "_native.abi3.so")
    own_md5 = hashlib.md5(open(own_so, "rb").read()).hexdigest() if os.path.exists(own_so) else None
    try:
        from domains.engine_provenance import engine_provenance
        p = engine_provenance()
        prov = p["source_match"]
    except Exception as e:                      # pragma: no cover
        prov = f"unavailable: {e}"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "arousal_window_coreg.json")))
    return dict(
        own_engine_so_md5=own_md5,
        provenance_source_match=prov,
        seed_self_load_only=bool(seed.get("self_load_only")),
        seed_depends_on=seed.get("depends_on"),
        rule_names=[r["name"] for r in seed["rules"]],
        no_rust="see runners/dsl diff (must be empty)")


def main():
    print("G-co-regulation (headline) ...")
    coreg = coreg_arm(caregiver_present=True, regulated_caregiver=True)
    alone = coreg_arm(caregiver_present=False, regulated_caregiver=True)
    dysreg_cg = coreg_arm(caregiver_present=True, regulated_caregiver=False)

    print("G-window-widens / G-trauma-narrows ...")
    healed = plasticity_arm(caregiver_present=True, regulated_caregiver=True)
    trauma = plasticity_arm(caregiver_present=False, regulated_caregiver=True)

    g_coreg = dict(
        return_coreg=coreg["return_ticks"], return_alone=alone["return_ticks"],
        return_dysreg_caregiver=dysreg_cg["return_ticks"],
        censored_coreg=coreg["censored_frac"], censored_alone=alone["censored_frac"],
        censored_dysreg_caregiver=dysreg_cg["censored_frac"],
        coreg_faster_than_alone_ci_separated=separated(alone["return_ticks"], coreg["return_ticks"]),
        alone_faster_than_dysreg_caregiver=(alone["return_ticks"]["mean"]
                                            < dysreg_cg["return_ticks"]["mean"]))
    g_widen = dict(
        hw_initial=healed["hw_initial"], hw_final=healed["hw_final"],
        widens_ci_separated=separated(healed["hw_final"], healed["hw_initial"]),
        control_hw_initial=trauma["hw_initial"], control_hw_final=trauma["hw_final"],
        control_does_not_widen=(trauma["hw_final"]["ci_hi"] < trauma["hw_initial"]["ci_lo"]))
    g_trauma = dict(
        trauma_hw_final=trauma["hw_final"], healed_hw_final=healed["hw_final"],
        hw_narrows_below_healed_ci_separated=separated(healed["hw_final"], trauma["hw_final"]),
        trauma_safety_final=trauma["safety_final"], healed_safety_final=healed["safety_final"],
        safety_lower_below_healed_ci_separated=separated(healed["safety_final"], trauma["safety_final"]))

    out = dict(
        block=239000, base_sha="9c5172d697d031ac613a36e5bc98b7edfb373723",
        seed_base=SEED_BASE, n=N, n_episodes=N_EPISODES, return_cap=RETURN_CAP,
        g_co_regulation=g_coreg, g_window_widens=g_widen, g_trauma_narrows=g_trauma,
        g_glass_box=glass_box_reconstruct(), source_audit=source_audit(),
        discipline=discipline(),
        synthetic_vs_clinical=(
            "SYNTHETIC model of the co-regulation / window-of-tolerance frameworks "
            "(grounded in the creator's in-vivo experience with 21 foster children). "
            "Mechanism-proven, NOT a clinical-outcome number."))
    os.makedirs(os.path.join(_ROOT, "results"), exist_ok=True)
    with open(os.path.join(_ROOT, "results", "arousal_wot.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    main()
