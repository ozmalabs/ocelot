#!/usr/bin/env python3
"""SPLAT OVER TIME — does the eye BUILD a fixed scene? (seed block 179000-179999)

MECHANICAL MEASURE-ADAPTER. No agent decision, no Rust, no Term. Holds ONE fixed
scene in front of the event-native 2-D photon eye, ticks it, and reads out —
purely mechanically — the eye's OWN graph-native accumulation:

  * held reconstruction   = per-receptor adapting floor `adaptation` (EMA→caught)
  * ground-truth target   = per-receptor `caught_quanta` (fixed scene ⇒ constant)
  * per-tick compute C(t)  = # RetinalOnsetEvent nodes minted at epoch t

The accumulation is the eye's own `photon_retina` EMA rule + `retinal_onset_2d`
rule under `run_rules()`. This script only submits a fixed stimulus, ticks,
reads attributes, counts nodes, computes error/compute curves, and renders the
held field as a Gaussian splat (holes where the floor has not grounded).

Prereg: VISION_SPLAT_OVER_TIME_PREREG.md. Deterministic; no wall-clock claim.
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

from domains.photon_eye import GraphEye  # noqa: E402

SEED = 179000
ROD_NM = 498.0
N_AZ = N_EL = 16
ADAPT_RATE = 0.15
ONSET_DB = 6.0
T1 = 20          # build phase ticks 1..T1
T2 = 40          # perturb phase ticks T1+1..T2
L_BG = 20        # dim background photon count
L_HI = 200       # bright block / perturb photon count
# fixed regions (row, col ranges, half-open)
BLOCK = (4, 12, 2, 8)          # rows 4..11, cols 2..7  — the bright block in A
PATCH = (2, 6, 11, 15)         # rows 2..5, cols 11..14 — dim in A, brightened in B
RESULTS = os.path.join(ROOT, "results")
FRAMES_DIR = os.path.join(RESULTS, "splat_over_time")


def flat(col, row):
    return row * N_AZ + col


def scene_A():
    s = np.full((N_EL, N_AZ), L_BG, dtype=int)
    r0, r1, c0, c1 = BLOCK
    s[r0:r1, c0:c1] = L_HI
    return s


def scene_B():
    s = scene_A()
    r0, r1, c0, c1 = PATCH
    s[r0:r1, c0:c1] = L_HI     # BRIGHTEN a previously-dim patch (onset re-fires)
    return s


def patch_cells():
    r0, r1, c0, c1 = PATCH
    return {(c, r) for r in range(r0, r1) for c in range(c0, c1)}


def packets_for(scene):
    out = []
    for r in range(N_EL):
        for c in range(N_AZ):
            cnt = int(scene[r, c])
            if cnt > 0:
                out.append({"col": c, "row": r,
                            "wavelength_nm": ROD_NM, "count": cnt})
    return out


def read_fields(eye):
    """Mechanical read-out: per-cell adaptation floor and caught_quanta."""
    adapt = np.zeros((N_EL, N_AZ))
    caught = np.zeros((N_EL, N_AZ))
    for r in range(N_EL):
        for c in range(N_AZ):
            rod = eye._receptors[(flat(c, r), "rod")]
            a = eye.substrate.node(rod)["attrs"]
            adapt[r, c] = float(a.get("adaptation", 0.0))
            caught[r, c] = float(a.get("caught_quanta", 0.0))
    return adapt, caught


def onset_cells_at(eye, epoch):
    """Mechanical read-out: (col,row) of every onset event minted at `epoch`."""
    cells = []
    for nid in eye.substrate.nodes("RetinalOnsetEvent"):
        a = eye.substrate.node(nid)["attrs"]
        if "row_index" not in a:
            continue
        if int(round(float(a["epoch"]))) == int(epoch):
            cells.append((int(a["column_index"]), int(a["row_index"])))
    return cells


def make_eye(adapt_rate):
    return GraphEye(n_az=N_AZ, n_el=N_EL, adapt_rate=adapt_rate,
                    context={"retina_2d": True, "synchronous": True,
                             "worker_capacity": 1, "onset_threshold_db": ONSET_DB,
                             "onset_refractory_epochs": 0.0}).build()


def tick(eye, scene):
    eye.submit_photons_2d(packets_for(scene))
    eye.substrate._inner.run_cognitive_tasks(1)
    eye.substrate._inner.run_rules()


def run_accumulating():
    """One persistent eye: build phase on A, then perturb to B. Held state
    carries forward across ticks (the eye's own graph accumulation)."""
    eye = make_eye(ADAPT_RATE)
    rec = {"adapt": [], "caught": [], "C": [], "onset_cells": []}
    for t in range(1, T2 + 1):
        scene = scene_A() if t <= T1 else scene_B()
        tick(eye, scene)
        adapt, caught = read_fields(eye)
        cells = onset_cells_at(eye, t)
        rec["adapt"].append(adapt)
        rec["caught"].append(caught)
        rec["C"].append(len(cells))
        rec["onset_cells"].append(cells)
    eye.stop()
    return rec


def run_stateless(scene, n):
    """FRESH eye each tick, shown the scene ONCE — held state never persists
    between ticks. Control: expected FLAT."""
    E, C = [], []
    for t in range(1, n + 1):
        eye = make_eye(ADAPT_RATE)
        tick(eye, scene)
        adapt, caught = read_fields(eye)
        gt = caught  # caught after one frame = the target
        E.append(float(np.mean(np.abs(adapt - gt)) / max(np.mean(gt), 1e-9)))
        C.append(len(onset_cells_at(eye, 1)))
        eye.stop()
    return E, C


def run_frozen(scene, n):
    """Persistent eye with adapt_rate=0 — accumulation coefficient OFF.
    Secondary control: expected FLAT."""
    eye = make_eye(0.0)
    E, C = [], []
    for t in range(1, n + 1):
        tick(eye, scene)
        adapt, caught = read_fields(eye)
        E.append(float(np.mean(np.abs(adapt - caught)) / max(np.mean(caught), 1e-9)))
        C.append(len(onset_cells_at(eye, t)))
    eye.stop()
    return E, C


def norm_error(adapt, caught):
    return float(np.mean(np.abs(adapt - caught)) / max(np.mean(caught), 1e-9))


def pearson(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    if np.std(a) < 1e-12 or np.std(b) < 1e-12:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def spearman(a, b):
    ra = np.argsort(np.argsort(a)); rb = np.argsort(np.argsort(b))
    return pearson(ra, rb)


def iou(s1, s2):
    s1, s2 = set(s1), set(s2)
    if not s1 and not s2:
        return 1.0
    return len(s1 & s2) / max(len(s1 | s2), 1)


# ---------------------------------------------------------------- rendering ----
def render_splat(adapt, caught, path, title, hole_thresh=0.15, S=16):
    """Mechanical EMIT: render the held adaptation field as a Gaussian splat.

    Each grounded cell = one isotropic Gaussian; brightness = adaptation
    (normalised by the scene's peak caught), opacity = confidence
    (adaptation/caught). A cell below `hole_thresh` confidence renders as a HOLE
    (the dark canvas shows through) — honest absence where the floor has not yet
    grounded."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    H, W = N_EL * S, N_AZ * S
    # FIXED scale across ALL frames (never per-frame renormalized) so the build
    # is visible: brightness = adaptation / scene-peak; alpha = confidence. Cells
    # are disjoint S×S blocks, each a soft Gaussian blob → the splat look with
    # honest HOLES (dark canvas) where the floor has not grounded (conf<thresh).
    peak = float(L_HI)
    yy, xx = np.mgrid[0:S, 0:S]
    sig = S * 0.42
    g = np.exp(-((xx - (S - 1) / 2) ** 2 + (yy - (S - 1) / 2) ** 2)
               / (2 * sig ** 2))
    intensity = np.zeros((H, W))
    alpha = np.zeros((H, W))
    for r in range(N_EL):
        for c in range(N_AZ):
            conf = float(np.clip(adapt[r, c] / max(caught[r, c], 1e-9), 0.0, 1.0))
            if conf < hole_thresh:
                continue
            bright = float(np.clip(adapt[r, c] / peak, 0.0, 1.0))
            y0, x0 = r * S, c * S
            intensity[y0:y0 + S, x0:x0 + S] = g * bright
            alpha[y0:y0 + S, x0:x0 + S] = g * conf
    rgb = plt.cm.magma(np.clip(intensity, 0, 1))[..., :3] * np.clip(alpha, 0, 1)[..., None]
    plt.imsave(path, np.clip(rgb, 0, 1))
    return path


def render_contact_sheet(rec, ticks, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    n = len(ticks)
    cols = min(n, 6)
    rows = math.ceil(n / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 2.2, rows * 2.4))
    axes = np.atleast_1d(axes).ravel()
    peak = max(float(np.max(rec["caught"][-1])), 1e-9)
    for i, t in enumerate(ticks):
        adapt = rec["adapt"][t - 1]; caught = rec["caught"][t - 1]
        conf = np.clip(adapt / np.maximum(caught, 1e-9), 0, 1)
        disp = np.where(conf < 0.15, np.nan, adapt / peak)
        ax = axes[i]
        ax.imshow(disp, cmap="magma", vmin=0, vmax=1, interpolation="nearest")
        phase = "build" if t <= T1 else "perturb"
        ax.set_title(f"t={t} ({phase})\nE={norm_error(adapt, caught):.3f} "
                     f"C={rec['C'][t-1]}", fontsize=7)
        ax.set_xticks([]); ax.set_yticks([])
    for j in range(len(ticks), len(axes)):
        axes[j].axis("off")
    fig.suptitle("Held reconstruction (adapting floor) over ticks — "
                 "gist → reconstruction; grey = HOLE (ungrounded)", fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


def render_curves(acc_E, acc_C, sl_E, sl_C, fr_E, fr_C, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ts = list(range(1, T2 + 1))
    tb = list(range(1, T1 + 1))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
    ax1.plot(ts, acc_E, "-o", ms=3, label="accumulating", color="#2166ac")
    ax1.plot(tb, sl_E, "--", label="stateless (fresh eye/tick)", color="#b2182b")
    ax1.plot(tb, fr_E, ":", label="frozen (adapt_rate=0)", color="#762a83")
    ax1.axvline(T1 + 0.5, color="grey", ls=":", lw=1)
    ax1.set_title("HEADLINE 1 — reconstruction error E(t)")
    ax1.set_xlabel("tick"); ax1.set_ylabel("normalized error"); ax1.legend(fontsize=7)
    ax2.plot(ts, acc_C, "-o", ms=3, label="accumulating", color="#2166ac")
    ax2.plot(tb, sl_C, "--", label="stateless", color="#b2182b")
    ax2.plot(tb, fr_C, ":", label="frozen", color="#762a83")
    ax2.axvline(T1 + 0.5, color="grey", ls=":", lw=1)
    ax2.set_title("HEADLINE 2 — per-tick compute C(t) [onset events]")
    ax2.set_xlabel("tick"); ax2.set_ylabel("work units"); ax2.legend(fontsize=7)
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)
    return path


def main():
    os.makedirs(FRAMES_DIR, exist_ok=True)
    np.random.seed(SEED)

    acc = run_accumulating()
    acc_E = [norm_error(acc["adapt"][t], acc["caught"][t]) for t in range(T2)]
    acc_C = acc["C"]
    # GT caught is constant; capture N_lit / N_perturbed from the scene.
    N_lit = int(np.sum(scene_A() > 0))
    N_perturbed = len(patch_cells())

    sl_E, sl_C = run_stateless(scene_A(), T1)
    fr_E, fr_C = run_frozen(scene_A(), T1)

    # ---- HEADLINE 1: build ----
    build_E = acc_E[:T1]
    viol = sum(1 for i in range(len(build_E) - 1)
               if build_E[i + 1] > build_E[i] + 0.02)
    H1a = viol == 0
    H1b = build_E[-1] < 0.12
    H1c = build_E[-1] / max(build_E[0], 1e-9) < 0.25
    H1d = (float(np.std(sl_E)) < 0.02) and (float(np.mean(sl_E)) > 0.5)
    H1e = build_E[-1] < 0.3 * float(np.mean(sl_E))

    # ---- HEADLINE 2: cost bend ----
    build_C = acc_C[:T1]
    H2a = build_C[-1] <= 0.10 * max(build_C[0], 1e-9)
    H2b = (float(np.mean(sl_C)) >= 0.5 * N_lit) and \
          (float(np.std(sl_C)) < 0.10 * max(float(np.mean(sl_C)), 1e-9))
    plateau = float(np.mean(build_C[-3:]))
    C_perturb = acc_C[T1]      # tick T1+1 (0-indexed T1)
    H2c = (C_perturb >= 3 * plateau) and (C_perturb >= 0.5 * N_perturbed) \
        if plateau > 0 else (C_perturb >= 0.5 * N_perturbed)
    pear = pearson(build_E, build_C)
    spear = spearman(build_E, build_C)
    H2d = pear > 0.6

    # ---- HEADLINE 3: fovea (post-perturb window [T1+1, T1+4]) ----
    win = range(T1, min(T1 + 4, T2))   # 0-indexed ticks T1+1..T1+4
    explicit = set()
    for t in win:
        explicit |= set(acc["onset_cells"][t])
    # implicit: cells with largest |Δ adaptation| across the window
    base = acc["adapt"][T1 - 1]        # last build tick
    end = acc["adapt"][min(T1 + 3, T2 - 1)]
    dmap = np.abs(end - base)
    idx = np.dstack(np.unravel_index(
        np.argsort(dmap.ravel())[::-1], dmap.shape))[0][:N_perturbed]
    implicit = {(int(c), int(r)) for r, c in idx}
    patch = patch_cells()
    H3a = iou(explicit, patch) >= 0.5
    H3b = iou(explicit, implicit) >= 0.5

    results = {
        "block": SEED, "adapt_rate": ADAPT_RATE, "T1": T1, "T2": T2,
        "N_lit": N_lit, "N_perturbed": N_perturbed,
        "acc_E": acc_E, "acc_C": acc_C,
        "stateless_E": sl_E, "stateless_C": sl_C,
        "frozen_E": fr_E, "frozen_C": fr_C,
        "build_E_start": build_E[0], "build_E_end": build_E[-1],
        "build_C_start": build_C[0], "build_C_end": build_C[-1],
        "stateless_E_mean": float(np.mean(sl_E)), "stateless_E_std": float(np.std(sl_E)),
        "stateless_C_mean": float(np.mean(sl_C)), "stateless_C_std": float(np.std(sl_C)),
        "frozen_E_mean": float(np.mean(fr_E)), "frozen_C_mean": float(np.mean(fr_C)),
        "plateau_C": plateau, "C_perturb": C_perturb,
        "pearson_E_C": pear, "spearman_E_C": spear,
        "fovea_explicit_cells": sorted(explicit),
        "fovea_implicit_cells": sorted(implicit),
        "fovea_iou_explicit_patch": iou(explicit, patch),
        "fovea_iou_explicit_implicit": iou(explicit, implicit),
        "criteria": {
            "H1a_monotone": bool(H1a), "H1b_asymptote": bool(H1b),
            "H1c_build_drop": bool(H1c), "H1d_stateless_flat": bool(H1d),
            "H1e_accumulation_gap": bool(H1e),
            "H2a_cost_drop": bool(H2a), "H2b_stateless_cost_flat": bool(H2b),
            "H2c_perturb_reraise": bool(H2c), "H2d_correlation": bool(H2d),
            "H3a_localization": bool(H3a), "H3b_implicit_explicit": bool(H3b),
        },
        "monotone_violations": viol,
    }
    with open(os.path.join(RESULTS, "splat_over_time.json"), "w") as fh:
        json.dump(results, fh, indent=2)

    # renders
    frame_ticks = [1, 2, 3, 5, 8, 12, 20, 21, 23, 26, 33, 40]
    for t in frame_ticks:
        render_splat(acc["adapt"][t - 1], acc["caught"][t - 1],
                     os.path.join(FRAMES_DIR, f"frame_t{t:02d}.png"),
                     f"t={t}")
    render_contact_sheet(acc, frame_ticks,
                         os.path.join(FRAMES_DIR, "contact_sheet.png"))
    render_curves(acc_E, acc_C, sl_E, sl_C, fr_E, fr_C,
                  os.path.join(FRAMES_DIR, "curves.png"))

    print(json.dumps({k: results[k] for k in (
        "criteria", "build_E_start", "build_E_end", "build_C_start",
        "build_C_end", "stateless_E_mean", "stateless_E_std", "stateless_C_mean",
        "frozen_E_mean", "frozen_C_mean", "plateau_C", "C_perturb",
        "pearson_E_C", "spearman_E_C", "fovea_iou_explicit_patch",
        "fovea_iou_explicit_implicit", "N_lit", "N_perturbed",
        "monotone_violations")}, indent=2))
    print("acc_E:", [round(x, 3) for x in acc_E])
    print("acc_C:", acc_C)


if __name__ == "__main__":
    main()
