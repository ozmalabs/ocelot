#!/usr/bin/env python3
"""THE HELD-PREDICTION / DECAY / DEMOTION LOOP ON THE REAL DOOM EYE (block 200000).

MECHANICAL MEASURE-ADAPTER. No agent decision, no Rust, no Term, NO new seed. It
opts the REAL Doom eye (`domains/photon_eye.py` GraphEye over real VizDoom E1M1
frames, `domains/doom_photon_world.py`, the 181000 path) into the EXISTING
held-prediction loop — `seeds/staleness_decay.json` (196000) + optionally
`seeds/demotion_hierarchy.json` (198000), over `seeds/held_surface.json`
(180000) — feeds real Doom photon flux, ticks under run_rules(), and reads out —
purely mechanically — the eye's OWN graph-native decay bookkeeping and held
surface. Every DECISION (residual, half_life, freshness, precision blend, tier,
demote) is a graph RULE; this script submits photons, sets external epochs,
ticks, and reads attributes.

The held surface that has not decayed IS the accumulated prediction; the new
Doom frame is the ORDER-0 residual against it; decay ∝ surprise manages the
field. STATIC level geometry keeps a long half-life and DENOISES (density climbs
with dwell); MOVING content collapses freshness and ADOPTS the new frame at flat
integer-tick latency — the two curves DECOUPLE on real Doom.

Gates: G1 decoupling (static density climbs; moving latency flat & low as an
INTEGER tick-count), G2 scene recovery preserved (onset/carve byte-observable),
G3 compute ∝ surprise (work-count drains), G4 demote-not-delete, G5
integer-native + default-OFF byte-identity. Prereg:
VISION_DOOM_HELD_PREDICTION_PREREG.md. Deterministic; cost is INTEGER counts, no
wall-clock claim. Core is importable + VizDoom-free (gated on a committed
fixture); main() re-captures + refreshes the fixture when VizDoom is present.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
# Only ROOT (for domains/ + substrate/). substrate_rs resolves via the
# site-packages .pth to the CANONICAL tree's built engine — inserting this
# worktree's runners/dsl/python would shadow it with an unbuilt package.
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from domains.photon_eye import GraphEye                       # noqa: E402
from domains import doom_photon_world as dpw                  # noqa: E402
from substrate.seed_loader import manifest_for                # noqa: E402

SEED = 200000
N_EL, N_AZ = 15, 20
N = N_EL * N_AZ
ADAPT_RATE = 0.15
ONSET_DB = 6.0
GAIN = 1.0       # photon gain: the eye's NATIVE scale (luma = per-receptor
                 # photon-count mean; no invented scale). The lower-count regime
                 # is reported separately in the RESULTS doc as a robustness leg.
T1 = 16          # STATIC hold of f0 (density climb on static geometry)
M = 10           # real PAN steps (turn_right frames)
SKIP = 8         # sim tics per pan step (a substantial ~31-luma view change)
H = 5            # ticks each pan frame is HELD (a STEP the moving region adopts)
T3 = 8           # STATIC re-hold of fM (re-drain)
ADOPT_TOL = 0.15
K_SEEDS = 5      # photon-seed ensemble for the G1 verdicts (POWER THE GATE —
                 # deltas within the per-episode step are not results, lesson set)
RESULTS = os.path.join(ROOT, "results")
FRAMES_DIR = os.path.join(RESULTS, "doom_held_prediction")
FIXTURE = os.path.join(ROOT, "tests", "fixtures", "doom_held_prediction",
                       "frames.npz")

# shared decay-primitive params, tuned to the real Doom luminance scale
# (luma ~12..99; static shot-noise residual ~6, a pan step ~20..80).
C0 = 1024.0
DEF = dict(enabled=1.0, lr_min=0.15, hl_scale=32.0, hl_min=1.0, c0=C0,
           refresh_thresh=15.0, attn_thresh=768.0, uniform=0.0,
           uniform_hl=256.0, pin_freshness=0.0)
# demotion-hierarchy tier params (supporting observable; block 198000)
TIER = dict(enabled=1.0, c0=C0, t_fresh=512.0, t_gist=64.0, k_gist=2.0,
            bits_full=8.0, bits_gist=4.0, bits_latent=1.0,
            delete_enabled=0.0, evict_age=64.0)


# =====================================================================
#  CORE — importable, VizDoom-free (the gate reuses this on the fixture)
# =====================================================================
def flat(c, r):
    return r * N_AZ + c


def base_eye():
    return GraphEye(n_az=N_AZ, n_el=N_EL, adapt_rate=ADAPT_RATE,
                    context={"retina_2d": True, "synchronous": True,
                             "worker_capacity": 1, "onset_threshold_db": ONSET_DB,
                             "onset_refractory_epochs": 0.0}).build()


def _add_cells(eye):
    inner = eye.substrate._inner
    hs = {}
    for r in range(N_EL):
        for c in range(N_AZ):
            node = eye.substrate.add_node("HeldSurfaceCell", {
                "value": 0.0, "obs": 0.0, "row": r, "col": c,
                "cell_index": flat(c, r), "epoch": 0.0, "residual": 0.0,
                "last_refresh_epoch": 0.0, "half_life": DEF["hl_scale"],
                "freshness": DEF["c0"], "needs_attention": 0.0})
            inner.add_edge_unchecked(eye._cells[flat(c, r)],
                                     "has_held_surface_cell", node)
            hs[(c, r)] = node
    return hs


def make_decay_eye(params=DEF):
    """Real Doom eye opted in to the staleness_decay loop (adapter I/O only)."""
    eye = base_eye()
    inner = eye.substrate._inner
    inner.load_seed_manifest(manifest_for("staleness_decay"), eye._agent)
    dp = eye.substrate.add_node("HeldDecayParams", dict(params))
    inner.add_edge_unchecked(eye._retina, "has_held_decay_params", dp)
    hs = _add_cells(eye)
    return eye, dp, hs


def make_fixed_eye(lr):
    """The CURRENT Doom eye: fixed-lr held_surface (control)."""
    eye = base_eye()
    inner = eye.substrate._inner
    inner.load_seed_manifest(manifest_for("held_surface"), eye._agent)
    params = eye.substrate.add_node("HeldSurfaceParams",
                                    {"enabled": 1.0, "lr": float(lr)})
    inner.add_edge_unchecked(eye._retina, "has_held_surface_params", params)
    hs = _add_cells(eye)
    return eye, params, hs


def tick(eye, luma, rng):
    eye.submit_photons_2d(dpw.photon_packets(luma, rng, gain=GAIN))
    eye.substrate._inner.run_cognitive_tasks(1)
    eye.substrate._inner.run_rules()


def read_field(eye, hs, key):
    out = np.zeros((N_EL, N_AZ))
    for r in range(N_EL):
        for c in range(N_AZ):
            out[r, c] = float(eye.substrate.node(hs[(c, r)])["attrs"].get(key, 0.0))
    return out


def onset_cells(eye, epoch):
    """Set of (row, col) cells that minted a RetinalOnsetEvent this epoch."""
    cells = set()
    for nid in eye.substrate.nodes("RetinalOnsetEvent"):
        a = eye.substrate.node(nid)["attrs"]
        if "row_index" in a and int(round(float(a.get("epoch", -1)))) == int(epoch):
            cells.add((int(a["row_index"]), int(a["column_index"])))
    return cells


def true_field(luma):
    """Noiseless caught field for one frame (Poisson mean), off a fresh eye."""
    eye, _dp, hs = make_decay_eye(DEF)
    tick(eye, luma, rng=None)
    t = read_field(eye, hs, "obs")
    eye.stop()
    return t


def build_sequence(f0, motion):
    """[f0]*T1 (static hold) + stepped pan ([fk]*H) + [fM]*T3 (re-hold)."""
    seq = [f0] * T1
    step_starts = []                    # tick index (0-based) where each step begins
    for fk in motion:
        step_starts.append(len(seq))
        seq.extend([fk] * H)
    seq.extend([motion[-1]] * T3)
    return seq, step_starts


def classify_regions(true_seq):
    """STATIC vs MOVING cells by per-cell temporal variance of the true field
    across the WHOLE sequence (empirical, from the stimulus itself)."""
    arr = np.stack(true_seq)                       # (T, N_EL, N_AZ)
    var = arr.var(axis=0)
    thresh = float(np.median(var))
    static = [(r, c) for r in range(N_EL) for c in range(N_AZ)
              if var[r, c] <= thresh]
    moving = [(r, c) for r in range(N_EL) for c in range(N_AZ)
              if var[r, c] > thresh]
    return static, moving, var


def region_err(field, truth, cells):
    idx = np.array(cells)
    est = field[idx[:, 0], idx[:, 1]]
    tru = truth[idx[:, 0], idx[:, 1]]
    return float(np.mean(np.abs(est - tru)) / max(np.mean(np.abs(tru)), 1e-9))


def run_arm(kind, lr=None, params=DEF, seed=SEED, seq=None):
    """One persistent eye over `seq`. Returns per-tick held value fields, the
    onset-cell sets, and (decay arm) the integer decay attrs."""
    if kind == "fixed":
        eye, _p, hs = make_fixed_eye(lr)
        extra = []
    else:
        eye, _dp, hs = make_decay_eye(params)
        extra = ["residual", "half_life", "freshness", "last_refresh_epoch",
                 "needs_attention"]
    rng = np.random.default_rng(seed)
    vals, onsets, ex = [], [], {k: [] for k in extra}
    for t, luma in enumerate(seq, 1):
        tick(eye, luma, rng)
        vals.append(read_field(eye, hs, "value"))
        onsets.append(onset_cells(eye, t))
        for k in extra:
            ex[k].append(read_field(eye, hs, k))
    eye.stop()
    return {"vals": vals, "onsets": onsets, "extra": ex}


def adopt_latencies(vals, true_seq, step_starts, moving, tol=ADOPT_TOL):
    """INTEGER ticks-to-adopt for the MOVING region after each pan STEP:
    ticks (0..H-1) for the moving-cell held error vs the step's true field to
    fall below `tol`. Censored at H if never reached."""
    lats = []
    for s in step_starts:
        truth = true_seq[s]                        # the (new) true field at the step
        lat = H
        for dt in range(H):
            t = s + dt
            if t >= len(vals):
                break
            if region_err(vals[t], truth, moving) < tol:
                lat = dt
                break
        lats.append(lat)
    return lats


def static_density_curve(vals, truth_static, static):
    """Normalized held error on STATIC cells across the static-hold ticks
    (density = 1/error climbs as shot noise averages out)."""
    return [region_err(vals[t], truth_static, static) for t in range(T1)]


# =====================================================================
#  G2 — scene recovery (onset + carve) preserved, byte-observable
# =====================================================================
def carve_polys(kind, seq, lr=None, params=DEF, seed=SEED):
    """Run the 2-D common-fate carve over the motion phase and read the polygon
    set — with the loop ON (decay) or the current fixed eye."""
    if kind == "fixed":
        eye, _p, _hs = make_fixed_eye(lr)
    else:
        eye, _dp, _hs = make_decay_eye(params)
    eye.context["visual_motion"] = True
    rng = np.random.default_rng(seed)
    for luma in seq:
        tick(eye, luma, rng)
    eye.settle_carve_2d(since_epoch=T1 + 1)
    eye.substrate._inner.run_cognitive_tasks(1)
    eye.substrate._inner.run_rules()
    polys = eye.carve_polygons_2d()
    eye.stop()
    return [(p["row_min"], p["row_max"], p["col_min"], p["col_max"]) for p in polys]


# =====================================================================
#  G4 — demotion (demote, never delete) on real Doom content (supporting)
# =====================================================================
def demotion_observable(true_static, static, seed=SEED):
    """Attach HierTraces seeded with REAL Doom static-cell detail, advance the
    innovation clock WITHOUT refresh (the remembered appearance is no longer
    re-confirmed under the pan) and confirm they DEMOTE FRESH->GIST->LATENT while
    the node count stays CONSTANT (never deleted); a re-observation PROMOTES back
    and RECOVERS full detail. All decisions are dh_* rules; the adapter only sets
    now_epoch / obs_epoch / obs_detail (mechanical, exactly as the 198000 gate)."""
    eye = base_eye()
    inner = eye.substrate._inner
    inner.load_seed_manifest(manifest_for("staleness_decay"), eye._agent)
    inner.load_seed_manifest(manifest_for("demotion_hierarchy"), eye._agent)
    tp = eye.substrate.add_node("HeldTierParams", dict(TIER))
    inner.add_edge_unchecked(eye._retina, "has_hier_tier_params", tp)
    # seed one HierTrace per (sampled) static cell with that cell's REAL detail
    sample = static[:: max(1, len(static) // 8)][:8]
    traces = {}
    for (r, c) in sample:
        detail = int(round(float(true_static[r, c])))
        tr = eye.substrate.add_node("HierTrace", {
            "detail": float(detail), "now_epoch": 0.0, "last_refresh_epoch": 0.0,
            "half_life": 2.0, "freshness": C0, "tier": 2.0,
            "stored": float(detail), "recon": float(detail), "bits": TIER["bits_full"],
            "present": 1.0, "obs_epoch": 0.0, "obs_detail": 0.0})
        inner.add_edge_unchecked(eye._retina, "has_hier_trace", tr)
        traces[(r, c)] = (tr, detail)
    n0 = len(eye.substrate.nodes("HierTrace"))
    # advance the clock WITHOUT refresh -> freshness decays -> demote
    tiers = {}
    for now in range(0, 13):
        for (tr, _d) in traces.values():
            eye.substrate.set_attr(tr, "now_epoch", float(now))
        inner.run_rules()
        tiers[now] = [int(float(eye.substrate.node(tr)["attrs"]["tier"]))
                      for (tr, _d) in traces.values()]
    n_mid = len(eye.substrate.nodes("HierTrace"))
    demoted = min(min(v) for v in tiers.values())          # reached GIST or LATENT
    # re-observe -> promote back to FRESH, recover detail
    for (r, c), (tr, detail) in traces.items():
        eye.substrate.set_attr(tr, "now_epoch", 14.0)
        eye.substrate.set_attr(tr, "obs_epoch", 14.0)
        eye.substrate.set_attr(tr, "obs_detail", float(detail))
    inner.run_rules()                                       # dh_promote
    inner.run_rules()                                       # dh_freshness/tier/demote
    recovered = all(
        int(float(eye.substrate.node(tr)["attrs"]["detail"])) == detail
        and int(float(eye.substrate.node(tr)["attrs"]["tier"])) == 2
        for (tr, detail) in traces.values())
    n_end = len(eye.substrate.nodes("HierTrace"))
    eye.stop()
    return {"n_seeded": n0, "n_mid": n_mid, "n_end": n_end,
            "min_tier_reached": demoted, "node_count_constant": n0 == n_mid == n_end,
            "demoted": demoted <= 1, "promoted_recovered": bool(recovered),
            "tiers_by_epoch": tiers}


# =====================================================================
#  G5b — default-OFF byte-identity (no params node -> loop inert)
# =====================================================================
def default_off_check(seq, seed=SEED):
    """With the decay seed loaded but NO HeldDecayParams node, the loop is inert:
    the held value field is byte-identical to a plain fixed-lr eye run, and no
    decay bookkeeping fires."""
    # eye A: fixed-lr held surface (current eye)
    a = run_arm("fixed", lr=DEF["lr_min"], seed=seed, seq=seq)
    # eye B: decay seed LOADED but params disabled (enabled=0) -> no rule fires;
    # fall back to a fixed-lr held_surface too, so value must match A byte-for-byte
    eye = base_eye()
    inner = eye.substrate._inner
    inner.load_seed_manifest(manifest_for("staleness_decay"), eye._agent)
    inner.load_seed_manifest(manifest_for("held_surface"), eye._agent)
    params = eye.substrate.add_node("HeldSurfaceParams",
                                    {"enabled": 1.0, "lr": float(DEF["lr_min"])})
    inner.add_edge_unchecked(eye._retina, "has_held_surface_params", params)
    hs = _add_cells(eye)
    rng = np.random.default_rng(seed)
    vals_b = []
    for luma in seq:
        tick(eye, luma, rng)
        vals_b.append(read_field(eye, hs, "value"))
    n_decayparams = len(eye.substrate.nodes("HeldDecayParams"))
    eye.stop()
    identical = all(np.array_equal(x, y) for x, y in zip(a["vals"], vals_b))
    return {"byte_identical": bool(identical), "n_decayparams_when_off": n_decayparams}


# =====================================================================
#  G5a — integer-native audit of the decay bookkeeping
# =====================================================================
def integer_audit(arm):
    ex = arm["extra"]
    nonint = 0
    for k in ("residual", "half_life", "freshness", "last_refresh_epoch"):
        for fld in ex[k]:
            nonint += int(np.sum(~np.isclose(fld, np.round(fld))))
    return {"noninteger_cells": nonint, "integer_native": nonint == 0}


# =====================================================================
def compute_criteria(f0, motion, depth=None, labels_last=None, seed=SEED):
    seq, step_starts = build_sequence(f0, motion)
    # memoize the noiseless true field per UNIQUE frame (seq repeats frames)
    _tcache = {}
    def truth(luma):
        key = id(luma)
        if key not in _tcache:
            _tcache[key] = true_field(luma)
        return _tcache[key]
    true_seq = [truth(l) for l in seq]
    truth_f0 = true_seq[0]
    static, moving, var = classify_regions(true_seq)

    def asym(curve):
        return float(np.mean(curve[-3:]))

    # ---- ENSEMBLE the 3 arms over K photon seeds (power the G1 verdicts) ----
    seeds = [seed + i for i in range(K_SEEDS)]
    dens_ens = {k: [] for k in ("gated", "lr_low", "lr_high")}
    lat_ens = {k: [] for k in ("gated", "lr_low", "lr_high")}
    arms_primary = {}
    for s in seeds:
        runs = {"gated": run_arm("decay", params=DEF, seed=s, seq=seq),
                "lr_low": run_arm("fixed", lr=0.15, seed=s, seq=seq),
                "lr_high": run_arm("fixed", lr=0.9, seed=s, seq=seq)}
        if s == seed:
            arms_primary = runs
        for k, r in runs.items():
            dens_ens[k].append(static_density_curve(r["vals"], truth_f0, static))
            lat_ens[k].append(adopt_latencies(r["vals"], true_seq, step_starts, moving))
    # ensemble-mean density curves + latency vectors
    dens = {k: np.mean(np.array(v), axis=0).tolist() for k, v in dens_ens.items()}
    lat = {k: np.mean(np.array(v), axis=0).tolist() for k, v in lat_ens.items()}
    gated, lr_low, lr_high = (arms_primary["gated"], arms_primary["lr_low"],
                              arms_primary["lr_high"])

    # ---- G1a static density climbs (on STATIC cells during the hold) ----
    g_start = float(np.mean(dens["gated"][:2]))
    g_asym = asym(dens["gated"])
    viol = sum(1 for i in range(len(dens["gated"]) - 1)
               if dens["gated"][i + 1] > dens["gated"][i] + 0.03)
    G1a = (g_asym < 0.5 * g_start) and (viol <= 3)

    # ---- G1b moving latency flat & low, INTEGER ticks ----
    # integer-ness is a per-run property (each run's ticks-to-adopt is an int);
    # the ensemble MEAN is reported, flatness/slope gated on it.
    lg = np.array(lat["gated"], float)
    lat_slope = float(np.polyfit(range(len(lg)), lg, 1)[0]) if len(lg) > 1 else 0.0
    lat_cv = float(np.std(lg) / max(np.mean(lg), 1e-9))
    lat_max = float(np.max(lg))
    all_integer_lat = all(float(x).is_integer()
                          for run in lat_ens["gated"] for x in run)
    G1b = ((float(np.mean(lg)) <= 3.0) and (lat_max <= 3.0)
           and (abs(lat_slope) < 0.5) and all_integer_lat)

    # ---- G1c decoupling dominates the fixed-rate trade (prereg clauses) ----
    meanL = {k: float(np.mean(v)) for k, v in lat.items()}
    c1 = g_asym <= 1.5 * asym(dens["lr_low"])            # gated denoises ~ lr_low
    c2 = meanL["gated"] <= meanL["lr_high"] + 2          # gated adopts ~ lr_high
    c3 = meanL["lr_low"] > 2 * max(meanL["gated"], 1e-9)  # lr_low too slow
    c4 = asym(dens["lr_high"]) > 2 * g_asym              # lr_high too noisy (vs loop)
    lr_high_over_gated = asym(dens["lr_high"]) / max(g_asym, 1e-9)
    G1c = c1 and c2 and c3 and c4
    # the DECOUPLING HEADLINE, robust to the arbitrary 2x on the noisy axis:
    # gated Pareto-dominates BOTH fixed controls, and the controls SPLIT axes.
    pareto = (g_asym <= min(asym(dens["lr_low"]), asym(dens["lr_high"])) + 1e-9
              and meanL["gated"] <= min(meanL["lr_low"], meanL["lr_high"]) + 1.0
              and meanL["lr_low"] > meanL["lr_high"]            # lr_low = the slow one
              and asym(dens["lr_high"]) > asym(dens["lr_low"]))  # lr_high = the noisy one

    # ---- G2 scene recovery preserved ----
    onset_gated = [sorted(s) for s in gated["onsets"]]
    onset_fixed = [sorted(s) for s in lr_low["onsets"]]
    G2a = onset_gated == onset_fixed
    carve_gated = carve_polys("decay", seq, params=DEF, seed=seed)
    carve_fixed = carve_polys("fixed", lr=0.15, seq=seq, seed=seed)
    G2b = carve_gated == carve_fixed

    # ---- G3 compute ∝ surprise (work-count) ----
    W = [len(s) for s in gated["onsets"]]
    w_start = float(np.mean(W[:2]))
    plateau = float(np.mean(W[T1 - 3:T1]))
    motion_W = W[T1:T1 + M * H]
    motion_mean = float(np.mean(motion_W)) if motion_W else 0.0
    motion_peak = float(np.max(motion_W)) if motion_W else 0.0
    plateau_B = float(np.mean(W[-3:]))
    G3a = (plateau <= 0.15 * max(w_start, 1e-9)
           and motion_peak >= 20 and motion_mean >= 2.5 * max(plateau, 1.0)
           and plateau_B <= 0.5 * max(motion_peak, 1e-9))
    G3b = (plateau <= 0.25 * N) and (motion_mean / max(plateau, 1.0) >= 3.0)

    # ---- G4 demote-not-delete ----
    demo = demotion_observable(truth_f0, static, seed=seed)
    G4 = (demo["demoted"] and demo["node_count_constant"]
          and demo["promoted_recovered"])

    # ---- G5 integer-native + default-off ----
    ia = integer_audit(gated)
    G5a = ia["integer_native"] and all_integer_lat
    doff = default_off_check(seq, seed=seed)
    G5b = doff["byte_identical"] and doff["n_decayparams_when_off"] == 0

    results = {
        "block": SEED, "grid": [N_AZ, N_EL], "N": N,
        "T1": T1, "M": M, "H": H, "T3": T3, "params": DEF,
        "n_static": len(static), "n_moving": len(moving),
        "density_static": dens, "density_start_gated": g_start,
        "density_asymptote": {k: asym(v) for k, v in dens.items()},
        "latency_moving": lat, "mean_latency": meanL,
        "latency_slope_gated": lat_slope, "latency_cv_gated": lat_cv,
        "latency_max_gated": lat_max, "all_integer_latency": bool(all_integer_lat),
        "K_seeds": K_SEEDS,
        "g1c_clauses": {"c1_gated_denoises": bool(c1), "c2_gated_fast": bool(c2),
                        "c3_lr_low_slow": bool(c3), "c4_lr_high_noisy_2x": bool(c4)},
        "lr_high_over_gated_density": float(lr_high_over_gated),
        "pareto_dominates": bool(pareto),
        "work_count": W, "work_start": w_start, "work_plateau": plateau,
        "work_motion_mean": motion_mean, "work_motion_peak": motion_peak,
        "work_plateau_B": plateau_B,
        "onset_identical": bool(G2a), "n_onset_events_total": sum(len(s) for s in gated["onsets"]),
        "carve_gated": carve_gated, "carve_fixed": carve_fixed,
        "demotion": demo, "integer_audit": ia, "default_off": doff,
        "criteria": {
            "G1a_static_density_climbs": bool(G1a),
            "G1b_moving_latency_flat_low_integer": bool(G1b and all_integer_lat),
            "G1c_decoupling_dominates": bool(G1c),
            "G1c_pareto_dominates": bool(pareto),
            "G2a_onset_preserved": bool(G2a),
            "G2b_carve_preserved": bool(G2b),
            "G3a_work_drains_spikes_redrains": bool(G3a),
            "G3b_fewer_cells_than_every_frame": bool(G3b),
            "G4_demote_not_delete": bool(G4),
            "G5a_integer_native": bool(G5a),
            "G5b_default_off_byte_identical": bool(G5b),
        },
    }
    return results


# =====================================================================
#  RENDER (mechanical emit)
# =====================================================================
def render(res, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(16, 4.3))
    tb = list(range(1, T1 + 1))
    ax[0].plot(tb, res["density_static"]["gated"], "-o", ms=3, color="#2166ac",
               label="gated (surprise-decay)")
    ax[0].plot(tb, res["density_static"]["lr_low"], "--", color="#67a9cf",
               label="fixed lr=0.15")
    ax[0].plot(tb, res["density_static"]["lr_high"], ":", color="#b2182b",
               label="fixed lr=0.9")
    ax[0].set_title("G1a — STATIC region density (1/error) CLIMBS with dwell\n"
                    "(real Doom geometry)")
    ax[0].set_xlabel("static-hold tick"); ax[0].set_ylabel("normalized error")
    ax[0].set_ylim(bottom=0); ax[0].legend(fontsize=7)
    steps = list(range(1, M + 1))
    ax[1].plot(steps, res["latency_moving"]["gated"], "-o", ms=3, color="#2166ac",
               label="gated")
    ax[1].plot(steps, res["latency_moving"]["lr_low"], "--", color="#67a9cf",
               label="fixed lr=0.15")
    ax[1].plot(steps, res["latency_moving"]["lr_high"], ":", color="#b2182b",
               label="fixed lr=0.9")
    ax[1].set_title("G1b — MOVING region adopt-LATENCY (INTEGER ticks) flat & low")
    ax[1].set_xlabel("pan step (dwell)"); ax[1].set_ylabel("ticks-to-adopt")
    ax[1].set_ylim(bottom=0); ax[1].legend(fontsize=7)
    ts = list(range(1, len(res["work_count"]) + 1))
    ax[2].plot(ts, res["work_count"], "-o", ms=2, color="#1a9850")
    ax[2].axhline(res["N"], color="#999", ls="--", lw=0.8, label=f"every-frame = N={res['N']}")
    ax[2].axvspan(0.5, T1 + 0.5, color="#cde", alpha=0.4, label="STATIC (drain)")
    ax[2].axvspan(T1 + 0.5, T1 + M * H + 0.5, color="#fcc", alpha=0.5, label="PAN (spike)")
    ax[2].axvspan(T1 + M * H + 0.5, len(ts) + 0.5, color="#cde", alpha=0.4)
    ax[2].set_title("G3 — work-count (surprising cells); compute ∝ surprise")
    ax[2].set_xlabel("tick"); ax[2].set_ylabel("cells re-processed")
    ax[2].legend(fontsize=7)
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)


# =====================================================================
def load_fixture():
    d = np.load(FIXTURE)
    return (d["f0"].astype(float), [m.astype(float) for m in d["motion"]],
            d["depth"].astype(float), d["labels_last"].astype(float))


def main(refresh_fixture=True):
    os.makedirs(FRAMES_DIR, exist_ok=True)
    if refresh_fixture and dpw.vizdoom_available():
        frames = dpw.capture_e1m1(["turn_right"] * (M + 1), skip=SKIP, seed=SEED)
        assert len(frames) >= M + 1, f"only captured {len(frames)} frames"
        lumas = [dpw.luma_grid(f["rgb"], N_EL, N_AZ) for f in frames]
        f0, motion = lumas[0], lumas[1:M + 1]
        depth = dpw.scalar_grid(frames[0]["depth"], N_EL, N_AZ)
        labels_last = dpw.scalar_grid(frames[M]["labels_buf"], N_EL, N_AZ)
        os.makedirs(os.path.dirname(FIXTURE), exist_ok=True)
        np.savez_compressed(FIXTURE, f0=f0.astype(np.float32),
                            motion=np.stack(motion).astype(np.float32),
                            depth=depth.astype(np.float32),
                            labels_last=labels_last.astype(np.float32))
    f0, motion, depth, labels_last = load_fixture()

    from domains.engine_provenance import provenance_stamp
    prov = provenance_stamp(strict=False)
    res = compute_criteria(f0, motion, depth, labels_last, seed=SEED)
    res["engine_source_match"] = prov.get("source_match")
    res["engine_sha"] = prov.get("short")

    with open(os.path.join(RESULTS, "doom_held_prediction.json"), "w") as fh:
        json.dump(res, fh, indent=2)
    render(res, os.path.join(FRAMES_DIR, "decoupling.png"))

    crit = res["criteria"]
    print(json.dumps(crit, indent=2))
    print(f"\nstatic density gated {res['density_start_gated']:.3f}->"
          f"{res['density_asymptote']['gated']:.3f} | "
          f"lr_low {res['density_asymptote']['lr_low']:.3f} "
          f"lr_high {res['density_asymptote']['lr_high']:.3f}")
    print(f"moving latency (int ticks): {res['mean_latency']}  "
          f"gated raw {res['latency_moving']['gated']}")
    print(f"work-count: start {res['work_start']:.1f} plateau {res['work_plateau']:.1f} "
          f"motion_mean {res['work_motion_mean']:.1f} peak {res['work_motion_peak']:.0f} "
          f"(N={res['N']})")
    print(f"onset preserved={res['onset_identical']} carve gated={len(res['carve_gated'])} "
          f"fixed={len(res['carve_fixed'])}")
    print(f"demotion: {res['demotion']['min_tier_reached']} min-tier, "
          f"nodes {res['demotion']['n_seeded']}->{res['demotion']['n_end']} "
          f"recovered={res['demotion']['promoted_recovered']}")
    print(f"engine {res['engine_sha']} [{res['engine_source_match']}]")
    n_pass = sum(1 for v in crit.values() if v)
    print(f"\nCRITERIA {n_pass}/{len(crit)} pass")
    return res


if __name__ == "__main__":
    main()
