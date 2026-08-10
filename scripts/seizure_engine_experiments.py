"""Confirmatory sweep for the ENGINE seizure model (FRESH seeds 5-14).

Runs the prereg predictions P1-P8 on the frozen architecture, driving the REAL
engine (`run_rules` + `fold_clock_edge`). Writes results/seizure_engine.json and
results/seizure_engine_figure.png. NO architecture parameter is changed here.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.seizure_engine_lattice import (  # noqa: E402
    Arch, EngineLattice, classify, persists, standing_rank1_fraction,
    onset_propagation, traveling_speed_mm_s,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
CONFIRM_SEEDS = list(range(5, 15))          # FRESH, disjoint from pilot (0-4)
FOLD_GRID = [0.65, 0.625, 0.6, 0.575, 0.55, 0.525, 0.5]


def run(arch, give, alpha, D, seed, **kw):
    lat = EngineLattice(arch, give=give, alpha=alpha, theta=kw.pop("theta", 1.0), seed=seed)
    return lat.run(D, **kw)


def find_fold(arch, seed, alpha=0.5, D=3.0, grid=FOLD_GRID):
    last_die, first_persist = None, None
    for gv in grid:
        r = run(arch, gv, alpha, D, seed)
        if persists(r, arch):
            first_persist = gv       # grid descends, so keep the largest persisting give
        elif first_persist is None:
            last_die = gv
    if last_die is None or first_persist is None:
        return None
    return (last_die + first_persist) / 2.0


def main():
    os.makedirs(RESULTS, exist_ok=True)
    arch = Arch()
    out = {"arch": {k: getattr(arch, k) for k in vars(arch)},
           "confirm_seeds": CONFIRM_SEEDS, "fold_grid": FOLD_GRID}

    # --- P3: fold across FRESH seeds ---
    print("P3 folds (fresh seeds, alpha=0.5, D=3):")
    folds = []
    for seed in CONFIRM_SEEDS:
        f = find_fold(arch, seed)
        folds.append(f)
        print(f"  seed {seed}: fold={f}")
    fv = [f for f in folds if f is not None]
    out["P3_folds"] = {"per_seed": folds, "median": float(np.median(fv)),
                       "min": float(min(fv)), "max": float(max(fv)),
                       "prereg_interval": [0.50, 0.65]}
    print(f"  median fold = {np.median(fv):.4f}  (prereg [0.50,0.65])")

    # --- P1/P2/P4/P8: full classify sweep over give at alpha=0.5 (seed 5) ---
    print("P1/P2/P4/P8 give sweep (seed 5, alpha=0.5, D=3):")
    sweep = []
    for gv in [1.0, 0.7, 0.6, 0.575, 0.55, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0]:
        r = run(arch, gv, 0.5, 3.0, 5)
        c = classify(r, arch)
        sweep.append(c)
        print(f"  give={gv:4.2f}: rank1={c['rank1_frac']:.3f} onsetprop={c['onset_prop_areas']:.2f} "
              f"persists={c['persists']} final={c['final_active']:.0f} "
              f"speed={c['speed_mm_s']} r2={c['speed_r2']}")
    out["give_sweep_seed5"] = sweep

    # --- P7 good null: alpha=0 never seizes at any give; give=1 never seizes at any D ---
    print("P7 good null (alpha=0, seed 5, D=3):")
    null_alpha = []
    for gv in [1.0, 0.6, 0.5, 0.3, 0.0]:
        r = run(arch, gv, 0.0, 3.0, 5)
        null_alpha.append({"give": gv, "persists": persists(r, arch),
                           "peak_active": int(r["n_active"].max()),
                           "final_active": float(r["n_active"][-60:].mean())})
        print(f"  give={gv}: persists={persists(r, arch)} peak={r['n_active'].max()}")
    out["P7_null_alpha0"] = null_alpha
    print("P2 give=1 across drive D (alpha=0.5, seed 5):")
    p2 = []
    for D in [1, 3, 6, 12, 30, 60]:
        r = run(arch, 1.0, 0.5, float(D), 5)
        p2.append({"D": D, "persists": persists(r, arch),
                   "final_active": float(r["n_active"][-60:].mean())})
        print(f"  D={D}: persists={persists(r, arch)}")
    out["P2_give1_vs_D"] = p2

    # --- P6 anti-null: fold vs D across a few fresh seeds (vertical boundary) ---
    print("P6 fold vs D (fresh seeds 5-7):")
    p6 = {}
    for D in [2, 4, 8, 16]:
        row = [find_fold(arch, s, D=float(D)) for s in (5, 6, 7)]
        p6[D] = row
        print(f"  D={D}: folds={row}")
    out["P6_fold_vs_D"] = p6

    # --- P5 matched control: interictal vs seizure differ ONLY in give ---
    print("P5 matched control (seed 5, alpha=0.5, D=3; give 0.6 vs 0.5):")
    ri = run(arch, 0.6, 0.5, 3.0, 5)   # interictal (just above fold)
    rs = run(arch, 0.5, 0.5, 3.0, 5)   # seizure (just below fold)
    out["P5_matched"] = {
        "interictal_give0.60": classify(ri, arch),
        "seizure_give0.50": classify(rs, arch),
    }
    print(f"  interictal(0.60) persists={persists(ri, arch)} | seizure(0.50) persists={persists(rs, arch)}")

    # --- P7b desync rescue: restore give mid-seizure -> aborts ---
    print("P7b desync rescue (seed 5, give=0.3 -> restore give=1.0 at t=120):")
    lat = EngineLattice(arch, give=0.3, alpha=0.5, theta=1.0, seed=5)
    rres = lat.run(3.0, desync_at=120, desync_give=1.0)
    out["P7b_desync_rescue"] = {
        "active_before_120": float(rres["n_active"][100:120].mean()),
        "active_after_rescue": float(rres["n_active"][-40:].mean()),
        "persists": persists(rres, arch),
    }
    print(f"  active before={rres['n_active'][100:120].mean():.0f} after rescue={rres['n_active'][-40:].mean():.0f}")

    # --- figure timeseries (seed 5): die vs seize + a seizing snapshot triple ---
    fig_die = run(arch, 1.0, 0.5, 3.0, 5)
    fig_seize = run(arch, 0.5, 0.5, 3.0, 5)
    out["figure_series"] = {
        "die_total_R": fig_die["total_R"].tolist(),
        "die_active": fig_die["n_active"].tolist(),
        "seize_total_R": fig_seize["total_R"].tolist(),
        "seize_active": fig_seize["n_active"].tolist(),
        "seize_front": fig_seize["front_radius"].tolist(),
    }

    with open(os.path.join(RESULTS, "seizure_engine.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    print("wrote results/seizure_engine.json")

    _figure(arch, out, fig_die, fig_seize)


def _figure(arch, out, fig_die, fig_seize):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as e:
        print("no matplotlib, skipping figure:", e)
        return
    fig, ax = plt.subplots(2, 2, figsize=(12, 8))

    # A: persist vs die (matched, only give differs)
    ax[0, 0].plot(fig_die["n_active"], label="give=1.0 (interictal — DIES)", color="#2a9d8f")
    ax[0, 0].plot(fig_seize["n_active"], label="give=0.5 (seizure — PERSISTS)", color="#e76f51")
    ax[0, 0].axvline(arch.t_onset, ls=":", color="k", alpha=0.4, label="onset removed")
    ax[0, 0].set_title("A. Persist vs die — matched, only the give differs")
    ax[0, 0].set_xlabel("substep"); ax[0, 0].set_ylabel("recruited areas")
    ax[0, 0].legend(fontsize=8)

    # B: traveling front (linear) for the seizing run
    fr = np.array(fig_seize["front_radius"]); t0 = arch.t_onset
    ax[0, 1].plot(fr, color="#e76f51")
    sp, r2 = traveling_speed_mm_s(fig_seize, arch)
    ax[0, 1].axvline(t0, ls=":", color="k", alpha=0.4)
    ax[0, 1].set_title(f"B. Traveling recruitment front — {sp:.3f} mm/s (r²={r2:.3f}), paper 0.48")
    ax[0, 1].set_xlabel("substep"); ax[0, 1].set_ylabel("front radius (areas)")

    # C: the fold — final active vs give, alpha=0.5 vs alpha=0 (good null)
    gv = [c["give"] for c in out["give_sweep_seed5"]]
    fa = [c["final_active"] for c in out["give_sweep_seed5"]]
    ax[1, 0].plot(gv, fa, "o-", color="#e76f51", label="alpha=0.5 (positive feedback ON)")
    null_g = [d["give"] for d in out["P7_null_alpha0"]]
    null_f = [d["final_active"] for d in out["P7_null_alpha0"]]
    ax[1, 0].plot(null_g, null_f, "s--", color="#264653", label="alpha=0 (OFF — good null)")
    ax[1, 0].axvspan(0.50, 0.65, color="grey", alpha=0.15, label="prereg fold [0.50,0.65]")
    ax[1, 0].axvline(out["P3_folds"]["median"], ls="-", color="k", alpha=0.5,
                     label=f"measured fold {out['P3_folds']['median']:.3f}")
    ax[1, 0].set_title("C. The give-fold (bifurcation) + good null")
    ax[1, 0].set_xlabel("give"); ax[1, 0].set_ylabel("final recruited areas")
    ax[1, 0].invert_xaxis(); ax[1, 0].legend(fontsize=7)

    # D: P6 vertical boundary — fold vs D
    Ds = sorted(out["P6_fold_vs_D"], key=lambda x: int(x))
    med = [np.nanmedian([v for v in out["P6_fold_vs_D"][D] if v is not None]) for D in Ds]
    ax[1, 1].plot([int(D) for D in Ds], med, "o-", color="#264653")
    ax[1, 1].axhspan(0.50, 0.65, color="grey", alpha=0.15)
    ax[1, 1].set_title("D. Anti-null — fold independent of drive D (vertical boundary)")
    ax[1, 1].set_xlabel("onset drive D"); ax[1, 1].set_ylabel("give-fold")
    ax[1, 1].set_ylim(0.3, 0.8)

    fig.suptitle("Seizure in the REAL (G,Γ) engine: standing→persist/die→traveling from the give "
                 "(run_rules + fold_clock_edge over a CognitiveArea lattice)", fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    p = os.path.join(RESULTS, "seizure_engine_figure.png")
    fig.savefig(p, dpi=110)
    print("wrote", p)


if __name__ == "__main__":
    main()
