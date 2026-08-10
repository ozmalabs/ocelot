"""SETTLE-8 STEP 1 — THE SPECTRUM OF THE WIRED SHEET.

**Pre-registered in `VISION_SETTLE8_PREREG.md` §1, committed at `536c0a31`
BEFORE this ran.** Deterministic linear algebra: **no RNG, no arm, no seed
burned** — the same move that made the wave-isotropy rung decisive (it computed
`E[xxᵀ]`'s eigenspectrum directly and answered the question without a cortex, a
rule, or a probe).

THE OPERATOR IS READ OFF THE GRAPH'S OWN EDGES, NEVER RE-DERIVED
------------------------------------------------------------------
`A` is built by walking the `sunit_neighbour` edges that
`settle_world.wire_sheet` ACTUALLY wired, on the centres
`settle_lib.lattice_centres` ACTUALLY placed. **This is not fastidiousness: the
settling rung's `linspace(3,12,3).round() = [3,8,12]` wired 12 directed edges
where 24 were due, with no error and no warning** (`VISION_SETTLE_RESULTS.md`
§6.5). An idealised adjacency would have hidden exactly that class of bug, and
the bug it would hide is the one that already happened.

`M = D⁻¹A − (1/N)J` is the linear part of `st_settle`'s sweep
`act_next ← max(aff + mean_nb(act) − mean_sheet(act), 0)`:
`mean_nb = D⁻¹A` (the seed's `Div(Fold(Neighbours ...), Max(Count,1))`) and
`mean_sheet = (1/N)J`.

**§13 — the row-sum check is a REQUIREMENT, not a diagnostic.** A sum over a
degree-`d` adjacency IS a gain of `d` (the settling rung measured `act → 2.5e224`
on the summed version). `D⁻¹A`'s rows must sum to exactly 1 at BOTH
connectivities or the "mean" is not a mean. Asserted, not assumed.
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains.engine_provenance import engine_preamble, provenance_line  # noqa: E402

engine_preamble()

from domains.settle_world import wire_sheet  # noqa: E402
from scripts.settle_lib import lattice_centres  # noqa: E402


class _MinimalSheet:
    """The SUnits + their `cy`/`cx`, and nothing else.

    `wire_sheet` reads exactly two attrs (`cy`, `cx`) and calls `add_edge`. The
    retina, the bipolars and the learning rule are IRRELEVANT to
    `sunit_neighbour` — they cannot change which units are lattice-adjacent. So
    the adjacency this wires is byte-identical to `build_sheet`'s, and
    `_verify_against_full_boot` PROVES that rather than asserting it.

    **The SEEDS ARE STILL LOADED, and that is the point, not a formality.** A
    bare `boot_core` raises `InadmissibleEdge: Γ rejects: type 'SUnit' not in
    vocabulary` — the `SUnit` type and the `SUnit -sunit_neighbour-> SUnit`
    production are graph data in `vision_onoff` / `vision_settle`. **Γ refuses to
    let this script wire an edge the agent's own grammar does not admit**, so the
    adjacency measured here is one the substrate would actually hold. The seed
    load order is `build_sheet`'s (settle BEFORE onoff — the settling rung's
    rule-priority finding), so nothing about the anatomy diverges.
    """

    def __init__(self, substrate):
        self.s = substrate


def wired_adjacency(n_side: int, connectivity: int):
    """Return (A, units, n_edges) with `A` read off the REAL `sunit_neighbour`
    edges. Mechanical."""
    from substrate.boot_core import boot_core, load_seeds_into

    s, ag = boot_core()
    # THE ORDER IS build_sheet's: vision_settle BEFORE vision_onoff.
    load_seeds_into(s, ag, ["vision_waves", "vision_settle", "vision_onoff"])
    centres = lattice_centres(n_side)
    units = [s.add_node("SUnit", {"cy": float(cy), "cx": float(cx)})
             for cy, cx in centres]
    w = _MinimalSheet(s)
    n_edges = wire_sheet(w, units, connectivity=connectivity)

    idx = {u: i for i, u in enumerate(units)}
    n = len(units)
    A = np.zeros((n, n), dtype=float)
    for u in units:
        for v in s.neighbours(u, "sunit_neighbour"):
            if v in idx:
                A[idx[u], idx[v]] = 1.0
    return A, units, n_edges


def is_bipartite(A):
    """2-colour the graph by BFS. Returns (bipartite?, n_triangles)."""
    n = A.shape[0]
    colour = {}
    for start in range(n):
        if start in colour:
            continue
        colour[start] = 0
        stack = [start]
        while stack:
            u = stack.pop()
            for v in np.nonzero(A[u])[0]:
                v = int(v)
                if v not in colour:
                    colour[v] = 1 - colour[u]
                    stack.append(v)
                elif colour[v] == colour[u]:
                    return False, _triangles(A)
    return True, _triangles(A)


def _triangles(A):
    """Number of triangles = trace(A^3)/6 for a simple undirected graph."""
    return int(round(np.trace(A @ A @ A) / 6.0))


def operator(A):
    """M = D^-1 A - (1/N) J, the linear part of st_settle's sweep."""
    n = A.shape[0]
    d = A.sum(axis=1)
    if np.any(d == 0):
        raise RuntimeError(f"isolated unit(s): degrees {sorted(set(d.tolist()))}")
    P = A / d[:, None]                      # D^-1 A
    # §13: the row-sum check is a REQUIREMENT. A "mean" whose rows do not sum to
    # 1 is a GAIN, and a gain of `degree` is what detonated the first cut.
    assert np.allclose(P.sum(axis=1), 1.0, atol=1e-12), \
        f"D^-1 A rows do not sum to 1: {P.sum(axis=1)}"
    J = np.ones((n, n))
    return P - J / n, P, d


def spectrum(n_side, connectivity):
    A, units, n_edges = wired_adjacency(n_side, connectivity)
    n = A.shape[0]
    sym = np.allclose(A, A.T)
    bip, tri = is_bipartite(A)
    M, P, d = operator(A)

    ev_M = np.linalg.eigvals(M)
    ev_P = np.linalg.eigvals(P)
    # The DC mode: M @ 1 must be 0 exactly-ish (J kills what D^-1 A preserves).
    dc = float(np.max(np.abs(M @ np.ones(n))))
    return {
        "n_side": n_side, "c": connectivity, "N": n, "edges": n_edges,
        "symmetric": sym, "bipartite": bip, "triangles": tri,
        "deg_hist": {int(k): int(v) for k, v in
                     zip(*np.unique(d, return_counts=True))},
        "lam_min_M": float(np.min(ev_M.real)),
        "rho_M": float(np.max(np.abs(ev_M))),
        "lam_min_P": float(np.min(ev_P.real)),
        "lam_max_P": float(np.max(ev_P.real)),
        "lam2_P": float(np.sort(ev_P.real)[-2]),
        "max_imag_M": float(np.max(np.abs(ev_M.imag))),
        "dc_residual": dc,
    }


def _verify_against_full_boot(n_side=3):
    """PROVE the minimal sheet's adjacency == the FULL `build_sheet`'s.

    §12's rule in spirit: do not assert that the cheap path equals the real one
    — measure it. If these ever differ, every number in this file is void.
    """
    from scripts.settle_lib import build_sheet
    out = {}
    for c in (4, 8):
        w, us, n_edges = build_sheet(seed=0, n_side=n_side, connectivity=c)
        idx = {u: i for i, u in enumerate(us)}
        A_full = np.zeros((len(us), len(us)))
        for u in us:
            for v in w.s.neighbours(u, "sunit_neighbour"):
                if v in idx:
                    A_full[idx[u], idx[v]] = 1.0
        A_min, _, n_min = wired_adjacency(n_side, c)
        same = np.array_equal(A_full, A_min)
        out[c] = (same, n_edges, n_min)
    return out


def main():
    print(provenance_line())
    print()
    print("STEP 1 — THE SPECTRUM OF THE WIRED SHEET (deterministic; no seed burned)")
    print("=" * 78)

    hdr = (f"{'c':>2} {'n':>2} {'N':>3} {'edges':>5} {'bip':>5} {'tri':>4} "
           f"{'lam_min(M)':>12} {'rho(M)':>10} {'lam_min(P)':>11} "
           f"{'lam2(P)':>9} {'dc':>9}")
    print(hdr)
    print("-" * 78)
    rows = []
    for c in (4, 8):
        for n_side in (3, 4, 5, 6):
            r = spectrum(n_side, c)
            rows.append(r)
            print(f"{r['c']:>2} {r['n_side']:>2} {r['N']:>3} {r['edges']:>5} "
                  f"{str(r['bipartite']):>5} {r['triangles']:>4} "
                  f"{r['lam_min_M']:>12.6f} {r['rho_M']:>10.6f} "
                  f"{r['lam_min_P']:>11.6f} {r['lam2_P']:>9.6f} "
                  f"{r['dc_residual']:>9.2e}")
        print("-" * 78)

    print()
    print("DEGREE HISTOGRAMS (the sheet is NOT regular at an open boundary —")
    print("which is exactly why spec(M) != {0} u spec(D^-1 A)\\{1}; see prereg §1.2c)")
    for r in rows:
        print(f"  c={r['c']} n_side={r['n_side']}: {r['deg_hist']}  "
              f"max|Im lam(M)| = {r['max_imag_M']:.2e}")

    print()
    print("CROSS-CHECK — minimal sheet vs the FULL build_sheet boot (n_side=3):")
    for c, (same, n_full, n_min) in _verify_against_full_boot(3).items():
        print(f"  c={c}: adjacency identical = {same}   "
              f"edges full={n_full} minimal={n_min}")

    print()
    print("DECISION (pre-registered, §1.3):")
    for r in rows:
        if r["c"] != 8:
            continue
        lam, rho = r["lam_min_M"], r["rho_M"]
        if lam <= -1 + 1e-9:
            v = "STOP — lambda_min <= -1; the 2-colouring survived"
        elif rho >= 1.0 - 1e-12:
            v = "STOP — rho >= 1; non-bipartite was NECESSARY, NOT SUFFICIENT"
        else:
            v = "PROCEED to STEP 2"
        print(f"  c=8 n_side={r['n_side']}: lam_min={lam:.6f} rho={rho:.6f} -> {v}")


if __name__ == "__main__":
    main()
