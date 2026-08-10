#!/usr/bin/env python3
"""HELD SURFACE — does the SURFACE-level reconstruction BUILD, graph-natively?
(seed block 180000-180999)

MECHANICAL MEASURE-ADAPTER. No agent decision, no Rust, no Term. It holds a
fixed scene in front of the event-native 2-D photon eye, opts the eye in to a
persistent HELD SURFACE (a `HeldSurfaceCell` per retina cell + a
`HeldSurfaceParams` config node + the `held_surface` seed), ticks it, and reads
out — purely mechanically — the eye's OWN graph-native SURFACE accumulation:

  * held surface value = the `held_surface_accumulate` rule's EMA of the noisy
    per-tick observation (`value ← value + lr·(caught_quanta − value)`)
  * stateless surface  = the raw per-tick observation `caught_quanta` (the
    un-accumulated single-tick carve — re-derived each call, never integrated)
  * ground truth       = the NOISELESS caught field (Poisson mean per cell)

The accumulation is a graph RULE under `run_rules()`. This script only submits a
(shot-noisy) fixed stimulus, ticks, reads attributes, computes error curves, and
renders the held surface as a Gaussian splat (honest holes where the surface has
not grounded).

Prereg: VISION_HELD_SURFACE_PREREG.md. Deterministic; no wall-clock claim.
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

from domains.photon_eye import GraphEye              # noqa: E402
from substrate.seed_loader import manifest_for       # noqa: E402

SEED = 180000
ROD_NM = 498.0
N_AZ = N_EL = 16
ADAPT_RATE = 0.15
SURFACE_LR = 0.15
ONSET_DB = 6.0
T1 = 30          # build phase ticks 1..T1 (scene A)
T2 = 60          # perturb phase ticks T1+1..T2 (scene B — block MOVED)
L_BG = 20        # dim background photon mean
L_HI = 200       # bright block photon mean
BLOCK_A = (4, 12, 2, 8)     # rows 4..11, cols 2..7  — the bright block in A
BLOCK_B = (4, 12, 9, 15)    # rows 4..11, cols 9..14 — the block MOVED in B
RESULTS = os.path.join(ROOT, "results")
FRAMES_DIR = os.path.join(RESULTS, "held_surface")


def flat(col, row):
    return row * N_AZ + col


def scene(block):
    s = np.full((N_EL, N_AZ), L_BG, dtype=int)
    r0, r1, c0, c1 = block
    s[r0:r1, c0:c1] = L_HI
    return s


def block_cells(block):
    r0, r1, c0, c1 = block
    return {(c, r) for r in range(r0, r1) for c in range(c0, c1)}


def packets_for(scene_arr, rng=None):
    """Per-cell photon packets; with `rng` the count carries Poisson SHOT NOISE."""
    out = []
    for r in range(N_EL):
        for c in range(N_AZ):
            lam = int(scene_arr[r, c])
            cnt = int(rng.poisson(lam)) if rng is not None else lam
            if cnt > 0:
                out.append({"col": c, "row": r,
                            "wavelength_nm": ROD_NM, "count": cnt})
    return out


def make_eye_with_surface(lr):
    """Build the 2-D eye and OPT IN to the persistent held surface (adapter I/O
    only: load the additive seed, add the config + cell nodes, wire edges)."""
    eye = GraphEye(n_az=N_AZ, n_el=N_EL, adapt_rate=ADAPT_RATE,
                   context={"retina_2d": True, "synchronous": True,
                            "worker_capacity": 1, "onset_threshold_db": ONSET_DB,
                            "onset_refractory_epochs": 0.0}).build()
    inner = eye.substrate._inner
    inner.load_seed_manifest(manifest_for("held_surface"), eye._agent)
    params = eye.substrate.add_node("HeldSurfaceParams",
                                    {"enabled": 1.0, "lr": float(lr)})
    inner.add_edge_unchecked(eye._retina, "has_held_surface_params", params)
    hs_nodes = {}
    for r in range(N_EL):
        for c in range(N_AZ):
            cell = eye._cells[flat(c, r)]
            hs = eye.substrate.add_node("HeldSurfaceCell", {
                "value": 0.0, "obs": 0.0, "row": r, "col": c,
                "cell_index": flat(c, r), "epoch": 0.0})
            inner.add_edge_unchecked(cell, "has_held_surface_cell", hs)
            hs_nodes[(c, r)] = hs
    return eye, params, hs_nodes


def tick(eye, scene_arr, rng):
    eye.submit_photons_2d(packets_for(scene_arr, rng))
    eye.substrate._inner.run_cognitive_tasks(1)
    eye.substrate._inner.run_rules()


def read_field(eye, hs_nodes, key):
    out = np.zeros((N_EL, N_AZ))
    for r in range(N_EL):
        for c in range(N_AZ):
            out[r, c] = float(eye.substrate.node(hs_nodes[(c, r)])["attrs"].get(key, 0.0))
    return out


def true_surface(block):
    """The NOISELESS caught field for a scene (the Poisson mean per cell), read
    off a fresh eye given the exact (un-noised) photon counts once."""
    eye, _params, hs_nodes = make_eye_with_surface(SURFACE_LR)
    tick(eye, scene(block), rng=None)          # noiseless: count == lambda
    truth = read_field(eye, hs_nodes, "obs")   # obs = this-tick caught (noiseless)
    eye.stop()
    return truth


def norm_error(est, truth):
    return float(np.mean(np.abs(est - truth)) / max(np.mean(truth), 1e-9))


def run_arm(freeze_at_perturb):
    """One persistent eye: build on A (ticks 1..T1), then perturb to B
    (T1+1..T2). If `freeze_at_perturb`, the accumulation coefficient lr is set to
    0 at perturb onset (mechanical ablation) — the FROZEN control. Returns the
    held-surface field and the raw observation field at every tick."""
    eye, params, hs_nodes = make_eye_with_surface(SURFACE_LR)
    rng = np.random.default_rng(SEED)
    held, obs = [], []
    for t in range(1, T2 + 1):
        if t == T1 + 1 and freeze_at_perturb:
            eye.substrate.set_attr(params, "lr", 0.0)   # ablate accumulation
        sc = scene(BLOCK_A) if t <= T1 else scene(BLOCK_B)
        tick(eye, sc, rng)
        held.append(read_field(eye, hs_nodes, "value"))
        obs.append(read_field(eye, hs_nodes, "obs"))
    eye.stop()
    return held, obs


# ---------------------------------------------------------------- rendering ----
def render_splat(held, truth, path, hole_thresh=0.15, S=16):
    """Render the held SURFACE as a Gaussian splat. Brightness = value / peak;
    alpha = confidence = value/truth; a cell below `hole_thresh` confidence is a
    HOLE (dark canvas shows through) — honest absence where the surface has not
    grounded. FIXED scale across frames so the build is visible."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    H, W = N_EL * S, N_AZ * S
    peak = float(L_HI)
    yy, xx = np.mgrid[0:S, 0:S]
    sig = S * 0.42
    g = np.exp(-((xx - (S - 1) / 2) ** 2 + (yy - (S - 1) / 2) ** 2) / (2 * sig ** 2))
    intensity = np.zeros((H, W))
    alpha = np.zeros((H, W))
    for r in range(N_EL):
        for c in range(N_AZ):
            conf = float(np.clip(held[r, c] / max(truth[r, c], 1e-9), 0.0, 1.0))
            if conf < hole_thresh:
                continue
            bright = float(np.clip(held[r, c] / peak, 0.0, 1.0))
            y0, x0 = r * S, c * S
            intensity[y0:y0 + S, x0:x0 + S] = g * bright
            alpha[y0:y0 + S, x0:x0 + S] = g * conf
    rgb = plt.cm.magma(np.clip(intensity, 0, 1))[..., :3] * np.clip(alpha, 0, 1)[..., None]
    plt.imsave(path, np.clip(rgb, 0, 1))
    return path


def render_contact_sheet(held_seq, err_seq, ticks, truth_for, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    n = len(ticks)
    cols = min(n, 6)
    rows = math.ceil(n / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 2.2, rows * 2.4))
    axes = np.atleast_1d(axes).ravel()
    for i, t in enumerate(ticks):
        held = held_seq[t - 1]
        truth = truth_for(t)
        conf = np.clip(held / np.maximum(truth, 1e-9), 0, 1)
        disp = np.where(conf < 0.15, np.nan, held / float(L_HI))
        ax = axes[i]
        ax.imshow(disp, cmap="magma", vmin=0, vmax=1, interpolation="nearest")
        phase = "build A" if t <= T1 else "perturb B"
        ax.set_title(f"t={t} ({phase})\nE={err_seq[t-1]:.3f}", fontsize=7)
        ax.set_xticks([]); ax.set_yticks([])
    for j in range(len(ticks), len(axes)):
        axes[j].axis("off")
    fig.suptitle("HELD SURFACE over ticks — gist → reconstruction, then the block "
                 "MOVES (fade old / adopt new); grey = HOLE (ungrounded)", fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


def render_curves(acc_EA, sl_EA, acc_EB, fr_EB, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    tb = list(range(1, T1 + 1))
    tp = list(range(T1 + 1, T2 + 1))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
    ax1.plot(tb, acc_EA, "-o", ms=3, label="accumulating (held surface)", color="#2166ac")
    ax1.plot(tb, sl_EA, "--", label="stateless (single-tick carve)", color="#b2182b")
    ax1.set_title("HEADLINE 1 — SURFACE build error vs true_A")
    ax1.set_xlabel("tick"); ax1.set_ylabel("normalized error"); ax1.legend(fontsize=7)
    ax2.plot(tp, acc_EB, "-o", ms=3, label="accumulating (follows)", color="#2166ac")
    ax2.plot(tp, fr_EB, ":", label="frozen (lr=0 at perturb)", color="#762a83")
    ax2.axvline(T1 + 0.5, color="grey", ls=":", lw=1)
    ax2.set_title("HEADLINE 2 — DECAY: error vs true_B after the block MOVES")
    ax2.set_xlabel("tick"); ax2.set_ylabel("normalized error"); ax2.legend(fontsize=7)
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)
    return path


def main():
    os.makedirs(FRAMES_DIR, exist_ok=True)

    true_A = true_surface(BLOCK_A)
    true_B = true_surface(BLOCK_B)

    acc_held, acc_obs = run_arm(freeze_at_perturb=False)
    fr_held, _fr_obs = run_arm(freeze_at_perturb=True)

    # ---- build phase (A) ----
    acc_EA = [norm_error(acc_held[t], true_A) for t in range(T1)]
    sl_EA = [norm_error(acc_obs[t], true_A) for t in range(T1)]     # stateless single-tick
    # ---- perturb phase (B) ----
    acc_EB = [norm_error(acc_held[t], true_B) for t in range(T1, T2)]
    fr_EB = [norm_error(fr_held[t], true_B) for t in range(T1, T2)]

    asymptote = float(np.mean(acc_EA[-3:]))
    E_sl = float(np.mean(sl_EA))
    sl_cv = float(np.std(sl_EA) / max(E_sl, 1e-9))
    tail_acc_B = float(np.mean(acc_EB[-3:]))
    tail_fr_B = float(np.mean(fr_EB[-3:]))
    first_B = float(acc_EB[0])

    # ---- HEADLINE 1: the surface builds ----
    H1a = asymptote < 0.15 * max(acc_EA[0], 1e-9)
    H1b = asymptote < 0.06
    viol = sum(1 for i in range(len(acc_EA) - 1) if acc_EA[i + 1] > acc_EA[i] + 0.03)
    H1c = viol <= 3
    H1d = (sl_cv < 0.15) and (E_sl > 2.0 * asymptote)
    H1e = asymptote < 0.5 * E_sl

    # ---- HEADLINE 2: decay is real ----
    H2a = tail_acc_B < 0.10
    H2b = tail_acc_B < 0.4 * max(first_B, 1e-9)
    H2c = tail_fr_B > 0.5
    H2d = tail_acc_B < 0.2 * max(tail_fr_B, 1e-9)

    results = {
        "block": SEED, "surface_lr": SURFACE_LR, "T1": T1, "T2": T2,
        "L_bg": L_BG, "L_hi": L_HI, "block_A": BLOCK_A, "block_B": BLOCK_B,
        "acc_EA": acc_EA, "stateless_EA": sl_EA,
        "acc_EB": acc_EB, "frozen_EB": fr_EB,
        "acc_EA_start": acc_EA[0], "asymptote": asymptote,
        "stateless_E_mean": E_sl, "stateless_E_cv": sl_cv,
        "acc_EB_first": first_B, "tail_acc_B": tail_acc_B, "tail_frozen_B": tail_fr_B,
        "monotone_violations": viol,
        "criteria": {
            "H1a_build_drop": bool(H1a), "H1b_asymptote": bool(H1b),
            "H1c_monotone": bool(H1c), "H1d_stateless_flat": bool(H1d),
            "H1e_accumulation_gap": bool(H1e),
            "H2a_acc_follows": bool(H2a), "H2b_acc_decreases": bool(H2b),
            "H2c_frozen_stuck": bool(H2c), "H2d_decay_gap": bool(H2d),
        },
    }
    with open(os.path.join(RESULTS, "held_surface.json"), "w") as fh:
        json.dump(results, fh, indent=2)

    # renders (accumulating held surface across build + perturb)
    def truth_for(t):
        return true_A if t <= T1 else true_B
    err_full = [norm_error(acc_held[t], truth_for(t + 1)) for t in range(T2)]
    frame_ticks = [1, 2, 4, 8, 15, 30, 31, 33, 38, 45, 60]
    for t in frame_ticks:
        render_splat(acc_held[t - 1], truth_for(t),
                     os.path.join(FRAMES_DIR, f"frame_t{t:02d}.png"))
    render_contact_sheet(acc_held, err_full, frame_ticks, truth_for,
                         os.path.join(FRAMES_DIR, "contact_sheet.png"))
    render_curves(acc_EA, sl_EA, acc_EB, fr_EB,
                  os.path.join(FRAMES_DIR, "curves.png"))

    print(json.dumps(results["criteria"], indent=2))
    print(f"acc_EA_start={acc_EA[0]:.3f} asymptote={asymptote:.4f} "
          f"E_sl={E_sl:.4f} (cv={sl_cv:.3f}) gap={asymptote/max(E_sl,1e-9):.3f}")
    print(f"acc_EB_first={first_B:.3f} tail_acc_B={tail_acc_B:.4f} "
          f"tail_frozen_B={tail_fr_B:.4f} decay_gap={tail_acc_B/max(tail_fr_B,1e-9):.3f}")
    print("monotone_violations:", viol)
    print("acc_EA:", [round(x, 3) for x in acc_EA])
    print("acc_EB:", [round(x, 3) for x in acc_EB])
    print("frozen_EB:", [round(x, 3) for x in fr_EB])


if __name__ == "__main__":
    main()
