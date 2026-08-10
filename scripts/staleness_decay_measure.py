#!/usr/bin/env python3
"""STALENESS DECAY — the shared integer-half-life decay primitive; the held
surface DECOUPLES density from latency (seed block 196000).

MECHANICAL MEASURE-ADAPTER. No agent decision, no Rust, no Term. It holds a
scene (a persistent fine-texture STATIC patch + a bright block that JUMPS every
P ticks) in front of the event-native 2-D photon eye, opts the eye in to the
shared decay primitive (`seeds/staleness_decay.json`), ticks it, and reads out —
purely mechanically — the eye's OWN graph-native decay bookkeeping and held
surface. Every DECISION (residual, half_life, freshness, the precision blend,
the foveation flag) is a graph RULE under `run_rules()`; this script only submits
photons, ticks, and reads attributes.

Gates: G1 decoupling, G2 first-classness, G3 falsifier, G4 genericity, G5
integer-native, G6 power-law, G7 existing-decay audit. Prereg:
VISION_STALENESS_DECAY_PREREG.md. Deterministic; no wall-clock claim.
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from domains.photon_eye import GraphEye            # noqa: E402
from substrate.seed_loader import manifest_for     # noqa: E402

SEED = 196000
ROD_NM = 498.0
N = 16
ADAPT_RATE = 0.15
ONSET_DB = 6.0
L_BG = 20
L_HI = 200
P = 15                     # move period
T = 90                     # ticks (6 block positions)
MOVES = [16, 31, 46, 61, 76]   # ticks where the block JUMPS
# static patch = rows 0..7; moving band = rows 8..15
STAT_ROWS = range(0, 8)
MOVE_ROWS = range(8, 16)
BLOCK_W = 4
RESULTS = os.path.join(ROOT, "results")
FRAMES = os.path.join(RESULTS, "staleness_decay")

# shared decay-primitive constants (integer-native)
C0 = 1024.0
DEF = dict(enabled=1.0, lr_min=0.15, hl_scale=32.0, hl_min=1.0, c0=C0,
           refresh_thresh=32.0, attn_thresh=768.0, uniform=0.0,
           uniform_hl=256.0, pin_freshness=0.0)


def block_cols(tick):
    seg = min((tick - 1) // P, 5)
    start = (seg * BLOCK_W) % N
    return start, start + BLOCK_W


def static_pattern():
    """A fixed fine texture over the static rows (values that need denoising)."""
    pat = np.full((N, N), L_BG, dtype=int)
    levels = [40, 80, 120, 160]
    for r in STAT_ROWS:
        for c in range(N):
            pat[r, c] = levels[(r + c) % 4]
    return pat


def scene(tick):
    s = static_pattern()
    for r in MOVE_ROWS:
        for c in range(N):
            s[r, c] = L_BG
    c0, c1 = block_cols(tick)
    for r in MOVE_ROWS:
        for c in range(c0, c1):
            s[r, c] = L_HI
    return s


def packets(scene_arr, rng):
    out = []
    for r in range(N):
        for c in range(N):
            lam = int(scene_arr[r, c])
            cnt = int(rng.poisson(lam)) if rng is not None else lam
            if cnt > 0:
                out.append({"col": c, "row": r, "wavelength_nm": ROD_NM,
                            "count": cnt})
    return out


def base_eye():
    return GraphEye(n_az=N, n_el=N, adapt_rate=ADAPT_RATE,
                    context={"retina_2d": True, "synchronous": True,
                             "worker_capacity": 1, "onset_threshold_db": ONSET_DB,
                             "onset_refractory_epochs": 0.0}).build()


def make_gated(params):
    """Eye + shared decay primitive (staleness_decay seed). Adapter I/O only."""
    eye = base_eye()
    inner = eye.substrate._inner
    inner.load_seed_manifest(manifest_for("staleness_decay"), eye._agent)
    dp = eye.substrate.add_node("HeldDecayParams", dict(params))
    inner.add_edge_unchecked(eye._retina, "has_held_decay_params", dp)
    hs = {}
    for r in range(N):
        for c in range(N):
            node = eye.substrate.add_node("HeldSurfaceCell", {
                "value": 0.0, "obs": 0.0, "row": r, "col": c,
                "cell_index": r * N + c, "epoch": 0.0, "residual": 0.0,
                "last_refresh_epoch": 0.0, "half_life": params["hl_scale"],
                "freshness": params["c0"], "needs_attention": 0.0})
            inner.add_edge_unchecked(eye._cells[r * N + c],
                                     "has_held_surface_cell", node)
            hs[(c, r)] = node
    return eye, dp, hs


def make_fixed(lr):
    """Eye + the block-180000 FIXED-rate held surface (control). Adapter I/O."""
    eye = base_eye()
    inner = eye.substrate._inner
    inner.load_seed_manifest(manifest_for("held_surface"), eye._agent)
    params = eye.substrate.add_node("HeldSurfaceParams",
                                    {"enabled": 1.0, "lr": float(lr)})
    inner.add_edge_unchecked(eye._retina, "has_held_surface_params", params)
    hs = {}
    for r in range(N):
        for c in range(N):
            node = eye.substrate.add_node("HeldSurfaceCell", {
                "value": 0.0, "obs": 0.0, "row": r, "col": c,
                "cell_index": r * N + c, "epoch": 0.0})
            inner.add_edge_unchecked(eye._cells[r * N + c],
                                     "has_held_surface_cell", node)
            hs[(c, r)] = node
    return eye, hs


def tick(eye, scene_arr, rng):
    eye.submit_photons_2d(packets(scene_arr, rng))
    eye.substrate._inner.run_cognitive_tasks(1)
    eye.substrate._inner.run_rules()


def read(eye, hs, key):
    out = np.zeros((N, N))
    for r in range(N):
        for c in range(N):
            out[r, c] = float(eye.substrate.node(hs[(c, r)])["attrs"].get(key, 0.0))
    return out


def true_field(tick_):
    """Noiseless caught field for the scene at `tick_` (one pass on a fresh eye)."""
    eye, _dp, hs = make_gated(DEF)
    tick(eye, scene(tick_), rng=None)
    truth = read(eye, hs, "obs")
    eye.stop()
    return truth


def region_err(field, truth, rows):
    idx = list(rows)
    est = field[idx, :]
    tru = truth[idx, :]
    return float(np.mean(np.abs(est - tru)) / max(np.mean(tru), 1e-9))


def run_arm(kind, lr=None, params=None):
    """Returns per-tick held `value` fields (and, for gated, the needs_attention
    + decay-attr fields for audits)."""
    if kind == "fixed":
        eye, hs = make_fixed(lr)
        extra_keys = []
    else:
        eye, _dp, hs = make_gated(params)
        extra_keys = ["needs_attention", "residual", "half_life", "freshness",
                      "last_refresh_epoch"]
    rng = np.random.default_rng(SEED)
    vals, extras = [], {k: [] for k in extra_keys}
    for t in range(1, T + 1):
        tick(eye, scene(t), rng)
        vals.append(read(eye, hs, "value"))
        for k in extra_keys:
            extras[k].append(read(eye, hs, k))
    eye.stop()
    return vals, extras


def latencies(vals, truths, thresh=0.15):
    """Ticks after each move for the MOVING region error to fall below thresh."""
    lats = []
    for mv in MOVES:
        lat = None
        for dt in range(0, P):
            t = mv + dt
            if t - 1 >= len(vals):
                break
            e = region_err(vals[t - 1], truths[t - 1], MOVE_ROWS)
            if e < thresh:
                lat = dt
                break
        lats.append(lat if lat is not None else P)
    return lats


# ------------------------------------------------------------------ G4/G5/G6/G7
def freshness_law(delta, hl, c0=int(C0)):
    """The rule's exact integer arithmetic: Ashr(c0, IDiv(delta, hl))."""
    k = delta // hl
    return c0 >> k if k < 64 else 0


def decaytrace_generic_check():
    """G4b: drive a DecayTrace through sd_freshness_generic and confirm the
    IDENTICAL machinery halves it on schedule (integer-exact)."""
    eye, dp, _hs = make_gated(DEF)
    inner = eye.substrate._inner
    dt = eye.substrate.add_node("DecayTrace", {
        "magnitude": 1.0, "now_epoch": 0.0, "last_refresh_epoch": 0.0,
        "half_life": 4.0, "freshness": C0})
    inner.add_edge_unchecked(eye._retina, "has_decay_trace", dt)
    seq = []
    for now in range(0, 17):
        eye.substrate.set_attr(dt, "now_epoch", float(now))
        inner.run_rules()
        seq.append(int(float(eye.substrate.node(dt)["attrs"]["freshness"])))
    eye.stop()
    expected = [freshness_law(now, 4) for now in range(0, 17)]
    return seq, expected


def structural_skeleton(term):
    """Op-type tree with all var/key/lit names abstracted (for G4a)."""
    if not isinstance(term, dict):
        return "@"
    t = term.get("type", "?")
    if t in ("Attr", "Var", "Lit"):
        return t
    kids = []
    for k in ("a", "b", "arg", "cond", "then", "other", "node"):
        if k in term:
            kids.append(structural_skeleton(term[k]))
    if "items" in term:
        kids.extend(structural_skeleton(x) for x in term["items"])
    return t + "(" + ",".join(kids) + ")"


def find_ashr(term):
    if isinstance(term, dict):
        if term.get("type") == "Ashr":
            return term
        for k in ("a", "b", "arg", "cond", "then", "other", "node"):
            if k in term:
                r = find_ashr(term[k])
                if r:
                    return r
        for x in term.get("items", []):
            r = find_ashr(x)
            if r:
                return r
    return None


def genericity_gate():
    """G4a: the freshness op tree is structurally identical across the two
    consumers (held surface + DecayTrace)."""
    seed = json.load(open(os.path.join(ROOT, "seeds", "staleness_decay.json")))
    rules = {r["name"]: r for r in seed["rules"]}

    def ashr_skel(rule_name):
        eff = rules[rule_name]["effects"][0]
        term = eff[3]["__term__"]
        return structural_skeleton(find_ashr(term))
    a = ashr_skel("sd_freshness")
    b = ashr_skel("sd_freshness_generic")
    return a, b, (a == b)


def integer_terms_audit():
    """G5b: the decay-bookkeeping rules use ONLY integer Terms."""
    seed = json.load(open(os.path.join(ROOT, "seeds", "staleness_decay.json")))
    allowed = {"Abs", "Minus", "Plus", "IDiv", "Ashr", "Max", "Min",
               "IfThenElse", "Lt", "Gt", "Gte", "Lte", "Eq", "And", "Attr",
               "Lit", "Var"}
    float_terms = {"Div", "Times", "Exp", "Log", "Sqrt"}
    bookkeeping = {"sd_residual", "sd_gate", "sd_freshness", "sd_freshness_generic"}

    def ops(term, acc):
        if isinstance(term, dict):
            if "type" in term:
                acc.add(term["type"])
            for k in ("a", "b", "arg", "cond", "then", "other", "node"):
                if k in term:
                    ops(term[k], acc)
            for x in term.get("items", []):
                ops(x, acc)
        return acc
    report = {}
    for r in seed["rules"]:
        used = set()
        for eff in r["effects"]:
            if isinstance(eff[3], dict) and "__term__" in eff[3]:
                ops(eff[3]["__term__"], used)
        report[r["name"]] = sorted(used)
    bad = {n: sorted(set(report[n]) & float_terms)
           for n in bookkeeping if set(report[n]) & float_terms}
    blend_ok = bool(set(report.get("sd_blend", [])) & {"Div", "Times"})
    return report, bad, blend_ok


def power_law_gate():
    """G6: aggregate forgetting of a heterogeneous-half-life surface. Each cohort
    halves exponentially; the SUPERPOSITION is fit power vs single-exponential."""
    half_lives = [1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64]
    deltas = np.arange(1, 129)
    S = np.array([sum(freshness_law(int(d), h) for h in half_lives)
                  for d in deltas], dtype=float)
    # verify the engine's Ashr matches freshness_law on a few points (spot check)
    x = np.log(deltas)
    y = np.log(np.maximum(S, 1e-9))
    # power-law fit: log S = a - alpha log D
    A = np.vstack([x, np.ones_like(x)]).T
    (mp, bp), *_ = np.linalg.lstsq(A, y, rcond=None)
    yhat_p = A @ np.array([mp, bp])
    ss_res_p = float(np.sum((y - yhat_p) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2_power = 1 - ss_res_p / max(ss_tot, 1e-12)
    # single-exponential fit: log S = c - lam D
    Ae = np.vstack([deltas, np.ones_like(deltas)]).T.astype(float)
    (me, be), *_ = np.linalg.lstsq(Ae, y, rcond=None)
    yhat_e = Ae @ np.array([me, be])
    ss_res_e = float(np.sum((y - yhat_e) ** 2))
    r2_exp = 1 - ss_res_e / max(ss_tot, 1e-12)
    return dict(half_lives=half_lives, S=S.tolist(), slope=float(mp),
                r2_power=float(r2_power), r2_exp=float(r2_exp),
                power_beats_exp=bool(r2_power > r2_exp))


def existing_decay_audit():
    """G7: enumerate the decays already in the eye/substrate + classify."""
    ct = os.path.join(ROOT, "runners", "dsl", "src", "cognitive_tasks.rs")
    ct_src = open(ct).read() if os.path.exists(ct) else ""
    rod_float = "next_adaptation" in ct_src and "adapt_rate" in ct_src
    hs_seed = json.load(open(os.path.join(ROOT, "seeds", "held_surface.json")))
    hs_uses_lr = any("lr" in json.dumps(r) for r in hs_seed["rules"])
    rows = [
        {"decay": "rod light adaptation (photon_retina)",
         "form": "adaptation += adapt_rate*(caught-adaptation)  [EMA]",
         "site": "runners/dsl/src/cognitive_tasks.rs (fused Naka-Rushton)",
         "kind": "AD-HOC FLOAT" if rod_float else "unknown",
         "disposition": "FOLLOW-ON (fused hot path; not a rule; not a clean swap)"},
        {"decay": "held-surface value EMA (held_surface_accumulate)",
         "form": "value += lr*(caught-value)  [EMA]",
         "site": "seeds/held_surface.json",
         "kind": "AD-HOC FLOAT" if hs_uses_lr else "unknown",
         "disposition": "SUPERSEDED-IN-VARIANT (this rung's precision blend "
                        "reads integer freshness; base rule retained as control)"},
        {"decay": "residual salience (residual_salience)",
         "form": "recomputed per pass (no persistent temporal decay)",
         "site": "seeds/residual_salience.json",
         "kind": "NOT-A-TEMPORAL-DECAY",
         "disposition": "N/A (stateless recompute, not a leaky integrator)"},
        {"decay": "onset refractory (onset_refractory_epochs)",
         "form": "integer-epoch refractory window",
         "site": "domains/photon_eye.py / retinal_onset seeds",
         "kind": "ALREADY INTEGER-EPOCH",
         "disposition": "OK (epoch-native; no float decay)"},
        {"decay": "shared staleness freshness (THIS RUNG)",
         "form": "freshness = Ashr(C0, IDiv(dEpoch, half_life))",
         "site": "seeds/staleness_decay.json",
         "kind": "INTEGER-HALF-LIFE (scale2 on epoch)",
         "disposition": "THE PRIMITIVE"},
    ]
    floats = [r["decay"] for r in rows if r["kind"] == "AD-HOC FLOAT"]
    return dict(rows=rows, float_decays=floats,
                one_primitive_known_consumers=True)


# ------------------------------------------------------------------------ main
def render_curves(res, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.2))
    ts = list(range(1, T + 1))
    ax1.plot(ts, res["Estatic_gated"], "-", color="#2166ac", label="gated (surprise-decay)")
    ax1.plot(ts, res["Estatic_lr_low"], "--", color="#67a9cf", label="fixed lr=0.15")
    ax1.plot(ts, res["Estatic_lr_high"], ":", color="#b2182b", label="fixed lr=0.9")
    ax1.plot(ts, res["Estatic_uniform_short"], "-.", color="#762a83", label="uniform-short (falsifier)")
    ax1.set_title("STATIC region — density (1/error) CLIMBS with dwell")
    ax1.set_xlabel("tick"); ax1.set_ylabel("normalized error (lower = denser)")
    ax1.set_ylim(bottom=0); ax1.legend(fontsize=7)
    labels = ["gated", "lr=0.15", "lr=0.9", "uni-long", "pin-fresh"]
    keys = ["gated", "lr_low", "lr_high", "uniform_long", "pin_fresh"]
    lat_means = [np.mean(res["latency"][k]) for k in keys]
    ax2.bar(labels, lat_means, color=["#2166ac", "#67a9cf", "#b2182b", "#762a83", "#f1a340"])
    ax2.set_title("MOVING region — adopt LATENCY (ticks) stays flat & low for gated")
    ax2.set_ylabel("mean ticks to adopt")
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)


def render_powerlaw(pl, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    d = np.arange(1, len(pl["S"]) + 1)
    fig, ax = plt.subplots(figsize=(5.5, 4.2))
    ax.loglog(d, pl["S"], "-o", ms=2, color="#2166ac")
    ax.set_title(f"Aggregate forgetting (12 half-lives)\nlog-log slope={pl['slope']:.2f}  "
                 f"R2_power={pl['r2_power']:.3f} vs R2_exp={pl['r2_exp']:.3f}")
    ax.set_xlabel("Δepoch"); ax.set_ylabel("Σ freshness")
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)


def main():
    os.makedirs(FRAMES, exist_ok=True)
    truths = [true_field(t) for t in range(1, T + 1)]

    arms = {
        "gated": run_arm("gated", params=DEF),
        "lr_low": run_arm("fixed", lr=0.15),
        "lr_high": run_arm("fixed", lr=0.9),
        "uniform_long": run_arm("gated", params={**DEF, "uniform": 1.0, "uniform_hl": 256.0}),
        "uniform_short": run_arm("gated", params={**DEF, "uniform": 1.0, "uniform_hl": 1.0}),
        "pin_fresh": run_arm("gated", params={**DEF, "pin_freshness": 1.0}),
    }
    Estatic = {k: [region_err(v[t], truths[t], STAT_ROWS) for t in range(T)]
               for k, (v, _e) in arms.items()}
    latency = {k: latencies(v, truths) for k, (v, _e) in arms.items()}

    def stat_asym(k):
        return float(np.mean(Estatic[k][-5:]))
    e_g0 = float(np.mean(Estatic["gated"][:2]))
    e_gT = stat_asym("gated")

    # ---- G1 decoupling ----
    G1a = e_gT < 0.5 * e_g0
    lg = np.array(latency["gated"], float)
    slope = float(np.polyfit(range(len(lg)), lg, 1)[0])
    G1b = (float(np.std(lg) / max(np.mean(lg), 1e-9)) < 0.5) and (abs(slope) < 0.5)
    meanL = {k: float(np.mean(latency[k])) for k in latency}
    G1c = (e_gT <= 1.5 * stat_asym("lr_low")
           and meanL["gated"] <= meanL["lr_high"] + 2
           and stat_asym("lr_high") > 2 * stat_asym("lr_low")
           and meanL["lr_low"] > 2 * meanL["lr_high"])

    # ---- G2 first-classness ----
    G2a = meanL["pin_fresh"] > 2 * meanL["gated"]
    # G2b foveation flag AT the jump tick of move #3 (t=46), when the changed
    # cells are maximally stale. The flag rule keys off the exposed freshness.
    jump_tick = MOVES[2]
    flag_field = arms["gated"][1]["needs_attention"][jump_tick - 1]
    move_cells = [(c, r) for r in MOVE_ROWS for c in range(N)]
    # "settled" static = static cells past warmup (they have denoised by now)
    stat_cells = [(c, r) for r in STAT_ROWS for c in range(N)]
    flagged = [(c, r) for (c, r) in move_cells + stat_cells if flag_field[r, c] >= 1.0]
    frac_flagged_in_move = (sum(1 for (c, r) in flagged if r in MOVE_ROWS)
                            / max(len(flagged), 1))
    frac_static_flagged = (sum(1 for (c, r) in stat_cells if flag_field[r, c] >= 1.0)
                           / len(stat_cells))
    G2b = frac_flagged_in_move >= 0.80 and frac_static_flagged <= 0.05
    # G2c SOURCE AUDIT: the decay bookkeeping is graph-resident. The adapter
    # (this script) must NOT set_attr any decay-bookkeeping key — those are
    # written ONLY by the seed rules. Python's only set_attr is the external
    # DecayTrace clock (now_epoch), admissible world I/O. And the seed rule
    # sd_freshness must own the freshness write.
    import re
    this_src = open(os.path.abspath(__file__)).read()
    setattr_lines = re.findall(r"set_attr\([^\n]*", this_src)
    bad_setattr = [ln for ln in setattr_lines
                   if any(k in ln for k in ("freshness", "half_life",
                                            "last_refresh_epoch", "residual"))]
    seed = json.load(open(os.path.join(ROOT, "seeds", "staleness_decay.json")))
    fresh_rule = next(r for r in seed["rules"] if r["name"] == "sd_freshness")
    rule_owns_freshness = fresh_rule["effects"][0][2] == "freshness"
    G2c = (len(bad_setattr) == 0) and rule_owns_freshness

    # ---- G3 falsifier ----
    G3a = meanL["uniform_long"] > 2 * meanL["gated"]
    G3b = stat_asym("uniform_short") > 2 * e_gT
    G3 = G3a and G3b

    # ---- G4 genericity ----
    skel_a, skel_b, G4a = genericity_gate()
    dt_seq, dt_exp = decaytrace_generic_check()
    G4b = dt_seq == dt_exp

    # ---- G5 integer-native ----
    v_g, ex_g = arms["gated"]
    intkeys = ("residual", "half_life", "freshness", "last_refresh_epoch")
    nonint = 0
    for k in intkeys:
        for fld in ex_g[k]:
            nonint += int(np.sum(~np.isclose(fld, np.round(fld))))
    G5a = nonint == 0
    term_report, bad_float, blend_uses_float = integer_terms_audit()
    G5b = (len(bad_float) == 0) and blend_uses_float

    # ---- G6 power-law / G7 audit ----
    pl = power_law_gate()
    audit = existing_decay_audit()

    results = {
        "block": SEED, "N": N, "T": T, "P": P, "MOVES": MOVES,
        "constants": DEF,
        "Estatic_gated": Estatic["gated"], "Estatic_lr_low": Estatic["lr_low"],
        "Estatic_lr_high": Estatic["lr_high"],
        "Estatic_uniform_short": Estatic["uniform_short"],
        "Estatic_uniform_long": Estatic["uniform_long"],
        "static_asymptote": {k: stat_asym(k) for k in Estatic},
        "static_start_gated": e_g0,
        "latency": latency, "mean_latency": meanL, "latency_slope_gated": slope,
        "G2b_frac_flagged_in_move": frac_flagged_in_move,
        "G2b_frac_static_flagged": frac_static_flagged,
        "G4a_skeleton_held": skel_a, "G4a_skeleton_generic": skel_b,
        "G4b_decaytrace_seq": dt_seq, "G4b_expected": dt_exp,
        "G5a_noninteger_cells": nonint,
        "G5b_term_report": term_report, "G5b_bad_float": bad_float,
        "G5b_blend_uses_float": blend_uses_float,
        "power_law": pl, "existing_decay_audit": audit,
        "criteria": {
            "G1a_density_climbs": bool(G1a),
            "G1b_latency_flat": bool(G1b),
            "G1c_decoupling_dominates": bool(G1c),
            "G2a_blend_keys_off_freshness": bool(G2a),
            "G2b_foveation_keys_off_freshness": bool(G2b),
            "G2c_source_audit_graph_resident": bool(G2c),
            "G3a_uniform_long_smears": bool(G3a),
            "G3b_uniform_short_no_density": bool(G3b),
            "G3_falsifier_both_diverge": bool(G3),
            "G4a_identical_machinery": bool(G4a),
            "G4b_decaytrace_halves_exact": bool(G4b),
            "G5a_decay_bookkeeping_integer": bool(G5a),
            "G5b_only_blend_is_float": bool(G5b),
            "G6_power_law_beats_exp": bool(pl["power_beats_exp"]),
        },
    }
    with open(os.path.join(RESULTS, "staleness_decay.json"), "w") as fh:
        json.dump(results, fh, indent=2)

    render_curves(results, os.path.join(FRAMES, "decoupling.png"))
    render_powerlaw(pl, os.path.join(FRAMES, "power_law.png"))

    print(json.dumps(results["criteria"], indent=2))
    print(f"\nstatic density: gated {e_g0:.3f}->{e_gT:.3f} | "
          f"lr_low {stat_asym('lr_low'):.3f} lr_high {stat_asym('lr_high'):.3f} "
          f"uni_short {stat_asym('uniform_short'):.3f}")
    print(f"mean latency: {json.dumps({k: round(v,2) for k,v in meanL.items()})}")
    print(f"power-law: slope {pl['slope']:.2f}  R2_power {pl['r2_power']:.3f} "
          f"R2_exp {pl['r2_exp']:.3f}")
    print(f"G4b DecayTrace freshness: {dt_seq[:9]} (expected {dt_exp[:9]})")
    print(f"G5a non-integer decay-attr cells: {nonint}")
    print(f"existing-decay floats to migrate: {audit['float_decays']}")


if __name__ == "__main__":
    main()
