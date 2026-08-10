"""Science probes on the LANDED engine seizure model (read-only w.r.t. the engine).

Extracts falsifiable, mechanistic predictions from `seizure_engine_lattice.py`
(the real (G,Gamma) settlement rule). NO engine changes. Every number is the
engine settling a CognitiveArea lattice via run_rules + fold_clock_edge.

Probes:
  A  onset-locus / geometry: give* at a CENTRAL vs EDGE vs CORNER focus (equal
     driven patch) -> does connectivity of the seeded tissue set the threshold?
  B  precursor: standing-phase net-balance (slope of total_R after drive removed,
     before travel) at give just-above vs just-below give* -> does an accumulation
     measure separate persist/die when onset morphology (rank1, peak) does not?
  C  intervention testbed: (C1) minimal aborting give (sweep desync_give) vs give*;
     (C2) point-of-no-return (sweep desync time).
  D  coupling: give* vs lateral coupling g.
"""
from __future__ import annotations
import json, os, sys, time
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from scripts.seizure_engine_lattice import Arch, EngineLattice, classify, persists  # noqa

ALPHA = 0.5
SEED = 5

def place_block(N, r0, c0, h=3, w=3):
    m = np.zeros((N, N), dtype=bool)
    m[r0:r0+h, c0:c0+w] = True
    return m

def run_focus(arch, give, focus_mask, D, seed=SEED, g=None, **run_kw):
    a = Arch(**{**arch.__dict__, **({} if g is None else {"g": g})})
    lat = EngineLattice(a, give=give, alpha=ALPHA, seed=seed)
    lat.focus = focus_mask
    return lat, lat.run(D, **run_kw)

def give_star(arch, focus_mask, D, grid, g=None, seed=SEED):
    """Largest give on `grid` (descending) that still PERSISTS = give* boundary."""
    last_persist = None
    rows = []
    for gv in grid:
        lat, res = run_focus(arch, gv, focus_mask, D, seed=seed, g=g)
        p = persists(res, arch)
        fa = float(res["n_active"][-60:].mean())
        rows.append({"give": gv, "persists": p, "final_active": fa})
        if p and last_persist is None:
            last_persist = gv
    return (last_persist if last_persist is not None else float("nan")), rows

def total_R_slope(res, arch):
    """Slope of total_R over the STANDING window: drive removed -> +40 substeps."""
    tR = res["total_R"]
    t0 = arch.t_onset
    t1 = min(len(tR), t0 + 40)
    y = tR[t0:t1]
    x = np.arange(len(y), dtype=float)
    if len(y) < 6:
        return float("nan")
    A = np.vstack([x, np.ones_like(x)]).T
    slope = np.linalg.lstsq(A, y, rcond=None)[0][0]
    return float(slope)

def main():
    arch = Arch()
    N = arch.N
    out = {"arch": arch.__dict__, "alpha": ALPHA, "seed": SEED}
    grid = [0.65, 0.6, 0.575, 0.55, 0.525, 0.5, 0.475, 0.45, 0.4]
    t_start = time.time()

    print("== Probe A: onset locus (equal 3x3 driven patch) ==")
    D_A = 6.0
    loci = {
        "center": place_block(N, N//2-1, N//2-1),
        "edge":   place_block(N, 1, N//2-1),
        "corner": place_block(N, 1, 1),
    }
    A = {}
    for name, mask in loci.items():
        gs, rows = give_star(arch, mask, D_A, grid)
        A[name] = {"give_star": gs, "rows": rows}
        print(f"  {name:7s} give* = {gs}")
    out["A_onset_locus"] = A

    print("== Probe B: precursor / standing-phase slope of total_R ==")
    focus_c = loci["center"]
    B = {}
    for label, gv in [("persist_0.50", 0.50), ("boundary_0.5375", 0.5375),
                      ("die_0.575", 0.575), ("die_0.65", 0.65)]:
        lat, res = run_focus(arch, gv, focus_c, D_A)
        cl = classify(res, arch)
        B[label] = {
            "give": gv, "persists": cl["persists"], "rank1_frac": cl["rank1_frac"],
            "peak_active": cl["peak_active"], "onset_prop_areas": cl["onset_prop_areas"],
            "standing_slope_totalR": total_R_slope(res, arch),
            "totalR_at_t0": float(res["total_R"][arch.t_onset]),
        }
        print(f"  give={gv:6.4f} persist={cl['persists']!s:5s} rank1={cl['rank1_frac']:.3f} "
              f"peak={cl['peak_active']:4d} standing_slope={B[label]['standing_slope_totalR']:+.3f}")
    out["B_precursor"] = B

    print("== Probe C1: minimal aborting give (running seizure give=0.30, desync@120) ==")
    C1 = {}
    for dg in [1.0, 0.7, 0.6, 0.575, 0.55, 0.5375, 0.525, 0.5]:
        lat, res = run_focus(arch, 0.30, focus_c, D_A, desync_at=120, desync_give=dg)
        aborted = not persists(res, arch)
        C1[str(dg)] = {"restore_give": dg, "aborted": aborted,
                       "active_before": float(np.mean(res["n_active"][110:120])),
                       "active_after": float(np.mean(res["n_active"][-40:]))}
        print(f"  restore give->{dg:6.4f}  aborted={aborted!s:5s}  "
              f"active {C1[str(dg)]['active_before']:7.1f} -> {C1[str(dg)]['active_after']:7.1f}")
    out["C1_min_abort_give"] = C1

    print("== Probe C2: point of no return (restore give=1.0 at time t) ==")
    C2 = {}
    for dt in [30, 60, 90, 120, 160, 200, 260]:
        lat, res = run_focus(arch, 0.30, focus_c, D_A, desync_at=dt, desync_give=1.0)
        aborted = not persists(res, arch)
        C2[str(dt)] = {"desync_at": dt, "aborted": aborted,
                       "final_active": float(res["n_active"][-40:].mean())}
        print(f"  desync@{dt:3d}  aborted={aborted!s:5s}  final_active={C2[str(dt)]['final_active']:.1f}")
    out["C2_point_of_no_return"] = C2

    print("== Probe D: give* vs lateral coupling g ==")
    Dd = {}
    for g in [0.4, 0.6, 0.8, 1.0]:
        gs, rows = give_star(arch, focus_c, D_A, grid, g=g)
        Dd[str(g)] = {"g": g, "give_star": gs, "rows": rows}
        print(f"  g={g:.2f}  give* = {gs}")
    out["D_give_star_vs_coupling"] = Dd

    out["runtime_s"] = time.time() - t_start
    dst = os.path.join(ROOT, "results", "seizure_science.json")
    json.dump(out, open(dst, "w"), indent=1)
    print(f"\nwrote {dst}  ({out['runtime_s']:.0f}s)")

if __name__ == "__main__":
    main()
