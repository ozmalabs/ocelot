#!/usr/bin/env python3
"""WINDOW-AS-A-KNOB runner (block 241000).

mint -> ingest -> run_rules -> read-off. Drives `worlds/window_knob_dyad_world.py`
to measure:

  G-knob (HEADLINE): the stressor MAGNITUDE at which the infant dysregulates as a
    MONOTONIC function of window WIDTH (>=3 widths), CI-separated -- the formal,
    settable window of tolerance the clinical models never had; plus a FAILABLE
    placebo axis (sweep k_self at fixed width -> the onset threshold must stay
    FLAT, proving the knob is the WIDTH, not just any parameter).

  G-bidirectional: the infant's arousal PULLS the caregiver's (mutual
    entrainment), and the caregiver's OWN window WIDTH predicts co-regulation
    capacity -- a WIDE-window caregiver stays regulated and co-regulates, a
    NARROW-window one is pulled into CO-DYSREGULATION and fails. The SAME width
    knob governs single-agent tolerance AND two-agent co-regulation capacity.

The runner NEVER branches on arousal to decide regulation/coupling -- that is the
rule set in `seeds/window_knob_coreg.json`, riding the REAL AffectiveState.arousal
and 239000's WindowOfTolerance. Protocol frozen in WINDOW_KNOB_PREREG.md.
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

from worlds.window_knob_dyad_world import (            # noqa: E402
    WindowKnobDyadWorld, RETURN_CAP)

SEED_BASE = 241000
N = 60

# G-knob: infant half-width levels (the WIDTH knob) and the placebo k_self axis.
WIDTH_LEVELS = [15.0, 30.0, 45.0]
WIDTH_JITTER = 2.0
PLACEBO_KSELF = [0.05, 0.15, 0.30]
PLACEBO_WIDTH = 30.0
BISECT_LO, BISECT_HI, BISECT_ITERS = 0.0, 200.0, 12

# G-bidirectional: caregiver half-width arms (the SAME knob, two-agent scale).
CAREGIVER_ARMS = {"narrow": 10.0, "mid": 30.0, "wide": 90.0}
INFANT_HW_MEAN, INFANT_HW_SD = 30.0, 3.0
STRESS_MEAN, STRESS_SD = 100.0, 8.0


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


def overlap(a, b):
    """The two CIs OVERLAP (neither strictly above the other) -- a FLAT result."""
    return not (a["ci_lo"] > b["ci_hi"] or b["ci_lo"] > a["ci_hi"])


# ------------------------------------------------- G-knob: onset threshold ----
def onset_threshold(half_width, *, k_self=0.15):
    """Bisect the stressor MAGNITUDE to find the onset threshold -- the GRAPH
    decides onset (in_episode latches at wk_infant_dysreg_onset_*). No caregiver:
    this is the SINGLE-agent tolerance. Threshold == the window's hi."""
    lo, hi = BISECT_LO, BISECT_HI
    for _ in range(BISECT_ITERS):
        mid = 0.5 * (lo + hi)
        w = WindowKnobDyadWorld(infant_half_width=half_width, stress_mag=mid,
                                caregiver_present=False, k_self=k_self)
        fired = w.step(stress=True)["in_episode"] == 1.0
        if fired:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


def width_arm(level_mu, seed0, n=N):
    rng = np.random.default_rng(seed0)
    thr = [onset_threshold(float(rng.normal(level_mu, WIDTH_JITTER)))
           for _ in range(n)]
    return _ci95(thr)


def placebo_arm(k_self, seed0, n=N):
    """FAILABLE CONTROL: sweep k_self at FIXED width -- onset threshold must be
    FLAT (the knob is the WIDTH, not the self-reg gain)."""
    rng = np.random.default_rng(seed0)
    thr = [onset_threshold(float(rng.normal(PLACEBO_WIDTH, WIDTH_JITTER)),
                           k_self=k_self) for _ in range(n)]
    return _ci95(thr)


# ----------------------------------------- G-bidirectional: caregiver width ----
def _one_dyad(seed, caregiver_half_width):
    rng = np.random.default_rng(seed)
    w = WindowKnobDyadWorld(
        infant_half_width=float(rng.normal(INFANT_HW_MEAN, INFANT_HW_SD)),
        stress_mag=float(rng.normal(STRESS_MEAN, STRESS_SD)),
        caregiver_present=True, caregiver_half_width=caregiver_half_width)
    ep = w.run_episode()
    return dict(return_ticks=ep["return_ticks"], censored=int(ep["censored"]),
                cg_dysreg=int(bool(ep["caregiver_dysregulated"])),
                cg_peak=ep["caregiver_peak_arousal"])


def caregiver_arm(caregiver_half_width, seed0, n=N):
    rows = [_one_dyad(seed0 + i, caregiver_half_width) for i in range(n)]
    return dict(
        return_ticks=_ci95([r["return_ticks"] for r in rows]),
        censored_frac=sum(r["censored"] for r in rows) / len(rows),
        cg_dysreg_frac=_ci95([r["cg_dysreg"] for r in rows]),
        cg_peak_arousal=_ci95([r["cg_peak"] for r in rows]))


# ---------------------------------------------------------------- G-glass-box ----
def glass_box_reconstruct(seed=SEED_BASE):
    """Reconstruct one bidirectional episode from graph_to_dict alone: both
    arousals, both window bands [lo,hi] (WIDTHs), the caregiver's regulated /
    dysregulated flags, and the attended_by coupling edge -- all readable."""
    w = WindowKnobDyadWorld(infant_half_width=30.0, stress_mag=100.0,
                            caregiver_present=True, caregiver_half_width=10.0)
    ep = w.run_episode()
    blob = w.checkpoint()
    nodes = {n["id"]: n for n in blob["nodes"]}
    aff = {nodes[i]["attrs"]["name"]: nodes[i]["attrs"]
           for i in nodes if nodes[i]["type"] == "AffectiveState"}
    wins = {nodes[i]["attrs"]["name"]: nodes[i]["attrs"]
            for i in nodes if nodes[i]["type"] == "WindowOfTolerance"}
    coupling = [(e["src"], e["tgt"]) for e in blob["edges"]
                if e["type"] == "attended_by"]
    caff = aff["caregiver_affect"]
    return dict(
        infant_arousal=aff["infant_affect"]["arousal"],
        infant_window=dict(lo=wins["infant_window"]["lo"],
                           hi=wins["infant_window"]["hi"],
                           width=wins["infant_window"]["hi"] - wins["infant_window"]["lo"]),
        caregiver_arousal=caff["arousal"],
        caregiver_regulated=caff["regulated"],
        caregiver_dysregulated=caff["dysregulated"],
        caregiver_window=dict(lo=wins["caregiver_window"]["lo"],
                              hi=wins["caregiver_window"]["hi"],
                              width=wins["caregiver_window"]["hi"] - wins["caregiver_window"]["lo"]),
        coupling_edges=len(coupling),
        caregiver_pulled_in=(caff["regulated"] == 0.0 or caff["dysregulated"] == 1.0),
        reconstructed_from="graph_to_dict")


# ------------------------------------------------------------ source audit ----
def source_audit():
    """No Python decides regulation/coupling. Forbidden: Python rule-engine
    calls, and any reward/punishment token (dysregulation is a STATE, never a
    badness -- Greene). The adapter's conditionals are over WORLD state only."""
    path = os.path.join(_ROOT, "worlds", "window_knob_dyad_world.py")
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
    return dict(forbidden_engine_hits=eng_hits, forbidden_reward_hits=rew_hits,
                reads_arousal_off_graph=("arousal" in code),
                clean=(not eng_hits and not rew_hits))


# --------------------------------------------------------------- G-discipline ----
def discipline():
    own_so = os.path.join(_ROOT, "runners", "dsl", "python", "substrate_rs",
                          "_native.abi3.so")
    own_md5 = hashlib.md5(open(own_so, "rb").read()).hexdigest() if os.path.exists(own_so) else None
    try:
        from domains.engine_provenance import engine_provenance
        prov = engine_provenance()["source_match"]
    except Exception as e:                      # pragma: no cover
        prov = f"unavailable: {e}"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "window_knob_coreg.json")))
    return dict(
        own_engine_so_md5=own_md5,
        provenance_source_match=prov,
        seed_self_load_only=bool(seed.get("self_load_only")),
        seed_depends_on=seed.get("depends_on"),
        rule_names=[r["name"] for r in seed["rules"]],
        no_rust="see runners/dsl diff (must be empty)")


def main():
    print("G-knob (headline): onset threshold vs window WIDTH ...")
    widths = {int(mu): width_arm(mu, SEED_BASE + 100 * i)
              for i, mu in enumerate(WIDTH_LEVELS)}
    placebo = {f"k_self={k}": placebo_arm(k, SEED_BASE + 400 + 100 * i)
               for i, k in enumerate(PLACEBO_KSELF)}

    print("G-bidirectional: caregiver-width -> co-regulation capacity ...")
    arms = {name: caregiver_arm(hw, SEED_BASE + 1000 + 100 * i)
            for i, (name, hw) in enumerate(CAREGIVER_ARMS.items())}

    lvls = sorted(widths.keys())
    placebo_vals = list(placebo.values())
    g_knob = dict(
        widths={str(k): widths[k] for k in lvls},
        monotone_ci_separated=all(
            separated(widths[lvls[j + 1]], widths[lvls[j]])
            for j in range(len(lvls) - 1)),
        placebo=placebo,
        placebo_flat=all(
            overlap(placebo_vals[i], placebo_vals[i + 1])
            for i in range(len(placebo_vals) - 1)))

    wide, mid, narrow = arms["wide"], arms["mid"], arms["narrow"]
    g_bidir = dict(
        arms=arms,
        mutual_entrainment_both_arms=(wide["cg_peak_arousal"]["ci_lo"] > 8.0
                                      and narrow["cg_peak_arousal"]["ci_lo"] > 8.0),
        narrow_slower_than_wide_ci_separated=separated(
            narrow["return_ticks"], wide["return_ticks"]),
        narrow_pulled_in=(narrow["cg_dysreg_frac"]["mean"] >= 0.9),
        wide_not_pulled_in=(wide["cg_dysreg_frac"]["mean"] <= 0.1),
        codysreg_frac_separated=separated(
            narrow["cg_dysreg_frac"], wide["cg_dysreg_frac"]))

    out = dict(
        block=241000, base_sha="ecdcd8dbad143c12586ed3b0d886f76cfcb35d53",
        seed_base=SEED_BASE, n=N, return_cap=RETURN_CAP,
        width_levels=WIDTH_LEVELS, caregiver_arms=CAREGIVER_ARMS,
        g_knob=g_knob, g_bidirectional=g_bidir,
        g_glass_box=glass_box_reconstruct(), source_audit=source_audit(),
        discipline=discipline(),
        unification=("The SAME half_width knob sets the single-agent onset "
                     "threshold (G-knob) AND the two-agent co-regulation capacity "
                     "(G-bidirectional) -- one parameter, both scales."),
        synthetic_vs_clinical=(
            "SYNTHETIC model of the window-of-tolerance / co-regulation "
            "frameworks. Concedes co-regulation-the-mechanism as prior art "
            "(coupled-oscillator dyads; active-inference CPC; arousal-caregiver "
            "robot); claims ONLY the settable window-width knob + the "
            "single<->two-agent unification. Mechanism-proven, NOT a "
            "clinical-outcome number."))
    os.makedirs(os.path.join(_ROOT, "results"), exist_ok=True)
    with open(os.path.join(_ROOT, "results", "window_knob.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    main()
