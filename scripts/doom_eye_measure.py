#!/usr/bin/env python3
"""THE PHOTON EYE SEES DOOM — measure (seed block 181000-181999).

MECHANICAL MEASURE-ADAPTER. No agent decision, no Rust, no Term, no new seed. It
feeds REAL VizDoom E1M1 frames — as per-receptor Poisson PHOTON FLUX — into the
event-native 2-D photon eye (blocks 171-180: transduce -> onset events ->
held_surface EMA), ticks it under run_rules(), and reads out — purely mechanically
— the eye's OWN graph-native accumulation:

  * held reconstruction  = HeldSurfaceCell.value (the held_surface EMA rule)
  * stateless single-tick = HeldSurfaceCell.obs (raw caught_quanta, never integrated)
  * per-tick work C(t)    = # RetinalOnsetEvent nodes minted at epoch t

HEADLINE 1 (frames alone): on a held real Doom frame the reconstruction BUILDS
(error drops, beats stateless — denoising) and per-tick WORK drains; real turning
motion SPIKES the work, then it re-drains. A temporally-SCRAMBLED order kills the
build (control). HEADLINE 2 (GT depth, oracle only): the held reconstruction's
edges correlate with the true depth structure above a shuffle null.

The core (make_eye / run_accumulating / criteria / edge_corr) is importable and
gated on a COMMITTED frame fixture in tests/test_doom_eye_migrated.py — self
contained, VizDoom-free. Prereg: VISION_DOOM_EYE_PREREG.md. Deterministic; cost is
WORK UNITS (onset counts), no wall-clock claim.
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

from domains.photon_eye import GraphEye                       # noqa: E402
from domains import doom_photon_world as dpw                  # noqa: E402
from substrate.seed_loader import manifest_for                # noqa: E402

SEED = 181000
N_EL, N_AZ = 15, 20
ADAPT_RATE = 0.15
SURFACE_LR = 0.15
ONSET_DB = 6.0
T1 = 20          # STATIC-A: hold f0 (build)
M = 13           # MOTION: f1..fM real turning frames
T3 = 10          # STATIC-B: hold fM (re-drain)
RESULTS = os.path.join(ROOT, "results")
FRAMES_DIR = os.path.join(RESULTS, "doom_eye")


# =====================================================================
#  CORE — importable, VizDoom-free (the gate reuses this on the fixture)
# =====================================================================
def flat(c, r):
    return r * N_AZ + c


def make_eye(lr):
    """Build the 2-D photon eye and OPT IN to the persistent held surface
    (adapter I/O only: load the additive seed, add config + cell nodes, wire
    edges) — byte-identical to the block-180000 held_surface setup."""
    eye = GraphEye(n_az=N_AZ, n_el=N_EL, adapt_rate=ADAPT_RATE,
                   context={"retina_2d": True, "synchronous": True,
                            "worker_capacity": 1, "onset_threshold_db": ONSET_DB,
                            "onset_refractory_epochs": 0.0}).build()
    inner = eye.substrate._inner
    inner.load_seed_manifest(manifest_for("held_surface"), eye._agent)
    params = eye.substrate.add_node("HeldSurfaceParams",
                                    {"enabled": 1.0, "lr": float(lr)})
    inner.add_edge_unchecked(eye._retina, "has_held_surface_params", params)
    hs = {}
    for r in range(N_EL):
        for c in range(N_AZ):
            node = eye.substrate.add_node("HeldSurfaceCell", {
                "value": 0.0, "obs": 0.0, "row": r, "col": c,
                "cell_index": flat(c, r), "epoch": 0.0})
            inner.add_edge_unchecked(eye._cells[flat(c, r)],
                                     "has_held_surface_cell", node)
            hs[(c, r)] = node
    return eye, params, hs


def read_field(eye, hs, key):
    out = np.zeros((N_EL, N_AZ))
    for r in range(N_EL):
        for c in range(N_AZ):
            out[r, c] = float(eye.substrate.node(hs[(c, r)])["attrs"].get(key, 0.0))
    return out


def onset_count(eye, epoch):
    n = 0
    for nid in eye.substrate.nodes("RetinalOnsetEvent"):
        a = eye.substrate.node(nid)["attrs"]
        if "row_index" in a and int(round(float(a["epoch"]))) == int(epoch):
            n += 1
    return n


def tick(eye, luma, rng):
    eye.submit_photons_2d(dpw.photon_packets(luma, rng))
    eye.substrate._inner.run_cognitive_tasks(1)
    eye.substrate._inner.run_rules()


def true_field(luma):
    """The NOISELESS caught field for a frame (Poisson mean per cell), read off a
    fresh eye given the exact un-noised photon counts once."""
    eye, _p, hs = make_eye(SURFACE_LR)
    tick(eye, luma, rng=None)
    t = read_field(eye, hs, "obs")
    eye.stop()
    return t


def run_accumulating(luma_seq, seed=SEED):
    """One persistent eye over the full ordered sequence. Held state carries
    forward across ticks (the eye's own graph accumulation). Returns per-tick
    held (value), obs (raw caught), and C (onset-event count)."""
    eye, _params, hs = make_eye(SURFACE_LR)
    rng = np.random.default_rng(seed)
    held, obs, C = [], [], []
    for t, luma in enumerate(luma_seq, 1):
        tick(eye, luma, rng)
        held.append(read_field(eye, hs, "value"))
        obs.append(read_field(eye, hs, "obs"))
        C.append(onset_count(eye, t))
    eye.stop()
    return {"held": held, "obs": obs, "C": C}


def norm_error(est, truth):
    return float(np.mean(np.abs(est - truth)) / max(np.mean(truth), 1e-9))


def edge_map(field):
    """Gradient-magnitude (edge) map — mechanical structure extractor."""
    gy, gx = np.gradient(np.asarray(field, float))
    return np.hypot(gy, gx)


def pearson(a, b):
    a = np.asarray(a, float).ravel(); b = np.asarray(b, float).ravel()
    if np.std(a) < 1e-12 or np.std(b) < 1e-12:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def edge_corr(field_a, field_b):
    return pearson(edge_map(field_a), edge_map(field_b))


def compute_criteria(luma_seq, motion_lumas, depth_grid=None, seed=SEED):
    """Compute ALL prereg criteria over an ordered sequence + its motion frames.

    luma_seq    : [f0]*T1 + [f1..fM] + [fM]*T3  (the ordered stimulus)
    motion_lumas: [f1..fM] (distinct real motion frames, for the scramble arm)
    depth_grid  : downsampled true depth of f0 (oracle) or None (H2 skipped)

    Returns the full results dict (arrays + scalars + boolean criteria)."""
    n = len(luma_seq)
    t1, m, t3 = T1, len(motion_lumas), n - T1 - len(motion_lumas)
    f0 = luma_seq[0]

    acc = run_accumulating(luma_seq, seed)
    truth_A = true_field(f0)

    # ---- H1 build (STATIC-A) ----
    acc_EA = [norm_error(acc["held"][t], truth_A) for t in range(t1)]
    sl_EA = [norm_error(acc["obs"][t], truth_A) for t in range(t1)]
    asymptote = float(np.mean(acc_EA[-3:]))
    E_sl = float(np.mean(sl_EA))
    sl_cv = float(np.std(sl_EA) / max(E_sl, 1e-9))
    viol = sum(1 for i in range(len(acc_EA) - 1)
               if acc_EA[i + 1] > acc_EA[i] + 0.03)
    gap_ordered = E_sl - asymptote

    H1a = asymptote < 0.15 * max(acc_EA[0], 1e-9)
    H1b = asymptote < 0.12
    H1c = viol <= 3
    H1d = (sl_cv < 0.20) and (E_sl > 2.0 * asymptote)
    H1e = asymptote < 0.5 * E_sl

    # ---- H2 cost bend ----
    C = acc["C"]
    plateau = float(np.mean(C[t1 - 3:t1]))
    motion_C = C[t1:t1 + m]
    motion_mean = float(np.mean(motion_C)) if motion_C else 0.0
    motion_peak = float(np.max(motion_C)) if motion_C else 0.0
    plateau_B = float(np.mean(C[t1 + m + max(0, t3 - 3):t1 + m + t3])) if t3 >= 1 \
        else float("nan")
    ratio = motion_mean / max(plateau, 1.0)

    H2a = plateau <= 0.15 * max(C[0], 1e-9)
    H2b = (motion_peak >= 20) and (motion_mean >= 2.5 * max(plateau, 1.0))
    H2c = (plateau_B <= 0.5 * max(motion_peak, 1e-9)) if t3 >= 1 else True
    H2d = ratio >= 3.0

    # ---- CONTROL: temporally scrambled order kills the build ----
    order = [int(x) for x in np.random.default_rng(seed).permutation(m)]
    idx_seq = [order[i % m] for i in range(t1)]
    scr_seq = [motion_lumas[j] for j in idx_seq]
    scr = run_accumulating(scr_seq, seed)
    # target for each scrambled tick is that tick's OWN true field (moving target);
    # memoise over the m distinct motion frames (each true field is one eye build).
    true_motion = {j: true_field(motion_lumas[j]) for j in set(idx_seq)}
    scr_EA = [norm_error(scr["held"][t], true_motion[idx_seq[t]]) for t in range(t1)]
    scr_sl = [norm_error(scr["obs"][t], true_motion[idx_seq[t]]) for t in range(t1)]
    scr_asym = float(np.mean(scr_EA[-3:]))
    scr_start = float(scr_EA[0])
    scr_gap = float(np.mean(scr_sl)) - scr_asym
    scr_C_mean = float(np.mean(scr["C"]))

    C1 = (scr_asym >= 0.5 * scr_start) or (scr_asym > 2.0 * asymptote)
    C2 = scr_gap <= 0.5 * max(gap_ordered, 1e-9)
    C3 = scr_C_mean >= 3.0 * max(plateau, 1.0)

    # ---- H2 structure (oracle depth) ----
    held_endA = acc["held"][t1 - 1]
    structure = {}
    if depth_grid is not None:
        dg = np.asarray(depth_grid, float)
        corr = edge_corr(held_endA, dg)
        rng2 = np.random.default_rng(seed + 1)
        nulls = []
        for _ in range(20):
            sh = held_endA.ravel().copy()
            rng2.shuffle(sh)
            nulls.append(edge_corr(sh.reshape(held_endA.shape), dg))
        null_corr = float(np.mean(np.abs(nulls)))
        S1 = corr > 0.15
        S2 = (corr > 3.0 * null_corr) and (corr > float(np.mean(nulls)))
        structure = {"depth_edge_corr": corr, "null_corr_abs_mean": null_corr,
                     "null_corr_signed_mean": float(np.mean(nulls)),
                     "S1_depth_edge_corr": bool(S1), "S2_above_null": bool(S2)}

    results = {
        "block": SEED, "grid": [N_AZ, N_EL], "T1": t1, "M": m, "T3": t3,
        "adapt_rate": ADAPT_RATE, "surface_lr": SURFACE_LR, "onset_db": ONSET_DB,
        "acc_EA": acc_EA, "stateless_EA": sl_EA,
        "acc_EA_start": acc_EA[0], "asymptote": asymptote,
        "stateless_E_mean": E_sl, "stateless_E_cv": sl_cv,
        "accumulation_gap": gap_ordered, "monotone_violations": viol,
        "C": C, "cost_start": C[0], "plateau": plateau,
        "motion_C": motion_C, "motion_C_mean": motion_mean,
        "motion_C_peak": motion_peak, "plateau_B": plateau_B,
        "cost_static_vs_motion_ratio": ratio,
        "scramble_EA": scr_EA, "scramble_asymptote": scr_asym,
        "scramble_start": scr_start, "scramble_gap": scr_gap,
        "scramble_C_mean": scr_C_mean,
        "structure": structure,
        "criteria": {
            "H1a_build_drop": bool(H1a), "H1b_asymptote": bool(H1b),
            "H1c_monotone": bool(H1c), "H1d_stateless_flat": bool(H1d),
            "H1e_accumulation_gap": bool(H1e),
            "H2a_cost_drain": bool(H2a), "H2b_motion_spike": bool(H2b),
            "H2c_redrain": bool(H2c), "H2d_ratio": bool(H2d),
            "C1_no_build": bool(C1), "C2_gap_killed": bool(C2),
            "C3_cost_high": bool(C3),
            **({"S1_depth_edge_corr": structure["S1_depth_edge_corr"],
                "S2_above_null": structure["S2_above_null"]}
               if structure else {}),
        },
        "held_endA": held_endA.tolist(), "truth_A": truth_A.tolist(),
    }
    return results


# =====================================================================
#  RENDERING (mechanical EMIT) + carve IoU report
# =====================================================================
def render_curves(res, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    t1, m, t3 = res["T1"], res["M"], res["T3"]
    tb = list(range(1, t1 + 1))
    ts = list(range(1, t1 + m + t3 + 1))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    ax1.plot(tb, res["acc_EA"], "-o", ms=3, label="accumulating (held surface)",
             color="#2166ac")
    ax1.plot(tb, res["stateless_EA"], "--", label="stateless (single-tick)",
             color="#b2182b")
    ax1.plot(tb, res["scramble_EA"], ":", label="SCRAMBLED order (control)",
             color="#762a83")
    ax1.set_title("HEADLINE 1 — held reconstruction error on a real Doom frame")
    ax1.set_xlabel("tick"); ax1.set_ylabel("normalized error vs true luminance")
    ax1.legend(fontsize=7)
    ax2.plot(ts, res["C"], "-o", ms=3, color="#1a9850", label="ordered work C(t)")
    ax2.axvspan(0.5, t1 + 0.5, color="#cde", alpha=0.4, label="STATIC-A (build)")
    ax2.axvspan(t1 + 0.5, t1 + m + 0.5, color="#fcc", alpha=0.5, label="MOTION (turn)")
    ax2.axvspan(t1 + m + 0.5, t1 + m + t3 + 0.5, color="#cde", alpha=0.4,
                label="STATIC-B (re-drain)")
    ax2.set_title("COST-BEND — per-tick work [onset events]; compute ∝ surprise")
    ax2.set_xlabel("tick"); ax2.set_ylabel("work units (onset count)")
    ax2.legend(fontsize=7)
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)
    return path


def render_reconstruction(res, luma_seq, depth_grid, path):
    """gist->reconstruction: true held frame | held reconstruction (end static-A)
    | true depth (oracle structure overlay)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    held = np.asarray(res["held_endA"]); truth = np.asarray(res["truth_A"])
    fig, ax = plt.subplots(1, 3, figsize=(12, 3.2))
    ax[0].imshow(luma_seq[0], cmap="gray", interpolation="nearest")
    ax[0].set_title("real Doom f0 luminance (held)", fontsize=8)
    ax[1].imshow(held, cmap="magma", interpolation="nearest")
    ax[1].set_title("held reconstruction (photon eye EMA)", fontsize=8)
    if depth_grid is not None:
        ax[2].imshow(depth_grid, cmap="viridis", interpolation="nearest")
        ax[2].set_title("true DEPTH (oracle) — structure\n"
                        f"held-edge vs depth-edge corr="
                        f"{res['structure'].get('depth_edge_corr', float('nan')):.3f}",
                        fontsize=8)
    else:
        ax[2].axis("off")
    for a in ax:
        a.set_xticks([]); a.set_yticks([])
    fig.suptitle("THE PHOTON EYE SEES DOOM — gist → reconstruction on REAL frames",
                 fontsize=10)
    fig.tight_layout(); fig.savefig(path, dpi=120); plt.close(fig)
    return path


def render_contact_sheet(res, luma_seq, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    acc = run_accumulating(luma_seq, SEED)
    t1, m, t3 = res["T1"], res["M"], res["T3"]
    ticks = [1, 2, 4, 8, t1, t1 + 1, t1 + 3, t1 + m,
             t1 + m + 1, t1 + m + t3]
    ticks = [t for t in ticks if 1 <= t <= len(luma_seq)]
    peak = max(float(np.max(res["truth_A"])), 1e-9)
    cols = min(len(ticks), 5); rows = math.ceil(len(ticks) / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 2.2, rows * 2.3))
    axes = np.atleast_1d(axes).ravel()
    for i, t in enumerate(ticks):
        held = acc["held"][t - 1]
        axes[i].imshow(held / peak, cmap="magma", vmin=0, vmax=1,
                       interpolation="nearest")
        if t <= t1:
            phase = "static-A"
        elif t <= t1 + m:
            phase = "MOTION"
        else:
            phase = "static-B"
        axes[i].set_title(f"t={t} ({phase})\nC={acc['C'][t-1]}", fontsize=7)
        axes[i].set_xticks([]); axes[i].set_yticks([])
    for j in range(len(ticks), len(axes)):
        axes[j].axis("off")
    fig.suptitle("Held reconstruction over ticks — build, then real motion, then "
                 "re-drain", fontsize=9)
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)
    return path


def carve_iou_report(luma_seq, frames, seed=SEED):
    """REPORTED (not gated): 2-D common-fate carve over the motion phase vs the
    VizDoom labels grid. Compared to the documented ~0.24 RGB-native.segment
    sub-grid baseline WITH the provenance caveat (a DIFFERENT carve)."""
    from scripts.eye_on_doom_probe import downsample_labels
    eye, _p, hs = make_eye(SURFACE_LR)
    eye.context["visual_motion"] = True   # motion+carve read the onset stream
    rng = np.random.default_rng(seed)
    for t, luma in enumerate(luma_seq, 1):
        tick(eye, luma, rng)
    since = T1 + 1
    eye.settle_carve_2d(since_epoch=since)
    eye.substrate._inner.run_cognitive_tasks(1)
    eye.substrate._inner.run_rules()
    polys = eye.carve_polygons_2d()
    eye.stop()
    # score the carved az×el spans vs enemy/object label cells on the last motion frame
    best = 0.0
    if frames is not None and polys:
        lab = downsample_labels(frames[T1 + M - 1]["labels_buf"], N_EL, N_AZ)
        names = {l["value"]: l["name"] for l in frames[T1 + M - 1]["labels"]}
        obj_vals = {v for v, nm in names.items() if nm not in ("DoomPlayer",)}
        gt = {v: {(int(r), int(c)) for r, c in zip(*np.where(lab == v))}
              for v in obj_vals}
        for v, cells in gt.items():
            if not cells:
                continue
            for p in polys:
                span = {(r, c) for r in range(p["row_min"], p["row_max"] + 1)
                        for c in range(p["col_min"], p["col_max"] + 1)}
                u = len(cells | span)
                best = max(best, (len(cells & span) / u) if u else 0.0)
    return {"n_polygons": len(polys), "best_carve_vs_labels_iou": best,
            "baseline_context": "~0.24 (OLD RGB native.segment sub-grid; DIFFERENT "
            "carve path — provenance caveat, not a matched comparison)"}


# =====================================================================
def main():
    from domains.engine_provenance import provenance_stamp
    os.makedirs(FRAMES_DIR, exist_ok=True)

    if not dpw.vizdoom_available():
        print("VizDoom / DOOM.WAD unavailable — cannot capture. Aborting.")
        return 2
    prov = provenance_stamp(strict=False)

    # capture: f0 (paused) then M real turning frames
    actions = ["turn_right"] * (M + 1)
    frames = dpw.capture_e1m1(actions, skip=4, seed=SEED)
    assert len(frames) >= M + 1, f"only captured {len(frames)} frames"
    lumas = [dpw.luma_grid(f["rgb"], N_EL, N_AZ) for f in frames]
    f0, motion = lumas[0], lumas[1:M + 1]
    luma_seq = [f0] * T1 + motion + [motion[-1]] * T3
    depth_grid = dpw.scalar_grid(frames[0]["depth"], N_EL, N_AZ)

    res = compute_criteria(luma_seq, motion, depth_grid, seed=SEED)
    res["engine_source_match"] = prov.get("source_match")
    res["carve_report"] = carve_iou_report(luma_seq, frames, SEED)

    # save fixture for the self-contained gate (downsampled luma + depth only)
    fixdir = os.path.join(ROOT, "tests", "fixtures", "doom_eye")
    os.makedirs(fixdir, exist_ok=True)
    np.savez_compressed(
        os.path.join(fixdir, "frames.npz"),
        f0=f0.astype(np.float32),
        motion=np.stack(motion).astype(np.float32),
        depth=depth_grid.astype(np.float32),
        labels_last=dpw.scalar_grid(frames[T1 * 0 + M]["labels_buf"], N_EL, N_AZ)
        .astype(np.float32))

    with open(os.path.join(RESULTS, "doom_eye.json"), "w") as fh:
        json.dump({k: v for k, v in res.items()
                   if k not in ("held_endA", "truth_A")}, fh, indent=2)

    render_curves(res, os.path.join(FRAMES_DIR, "curves.png"))
    render_reconstruction(res, luma_seq, depth_grid,
                          os.path.join(FRAMES_DIR, "reconstruction.png"))
    render_contact_sheet(res, luma_seq,
                         os.path.join(FRAMES_DIR, "contact_sheet.png"))

    crit = res["criteria"]
    print(json.dumps(crit, indent=2))
    print(f"asymptote={res['asymptote']:.4f} start={res['acc_EA_start']:.3f} "
          f"E_sl={res['stateless_E_mean']:.4f} (cv={res['stateless_E_cv']:.3f}) "
          f"gap={res['accumulation_gap']:.4f}")
    print(f"plateau={res['plateau']:.1f} motion_mean={res['motion_C_mean']:.1f} "
          f"motion_peak={res['motion_C_peak']:.0f} plateau_B={res['plateau_B']:.1f} "
          f"ratio={res['cost_static_vs_motion_ratio']:.1f}")
    print(f"scramble: asym={res['scramble_asymptote']:.3f} start={res['scramble_start']:.3f} "
          f"gap={res['scramble_gap']:.4f} C_mean={res['scramble_C_mean']:.1f}")
    if res["structure"]:
        print(f"structure: depth_edge_corr={res['structure']['depth_edge_corr']:.3f} "
              f"null={res['structure']['null_corr_abs_mean']:.3f}")
    print("carve:", res["carve_report"])
    print("acc_EA:", [round(x, 3) for x in res["acc_EA"]])
    print("C:", res["C"])
    n_pass = sum(1 for v in crit.values() if v)
    print(f"\nCRITERIA {n_pass}/{len(crit)} pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
