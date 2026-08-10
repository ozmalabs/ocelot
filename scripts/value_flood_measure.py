"""value_flood_measure -- MEASURE the value-flood halting conditions.

Pre-registration: VISION_VALUE_FLOOD_PREREG.md (committed 8a0a3980 before any
number). Seeds 81000-81999.

Mechanical I/O + read-out ONLY. The seed `vision_border_ownership` is UNCHANGED
and does every decision; this script builds fields, ticks to a fixpoint, and
measures. The gate attribution (M2) is computed here in the read-out, never by
the rules under test, and is RECONCILED against the rules' own minted output --
a diagnostic that does not reconcile is not claimed (PROTOCOL: a diagnostic must
not be computed by the component it checks).
"""
from __future__ import annotations
import importlib.util
import json
import os
import sys
import time
from collections import Counter, deque

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "domains"))

from domains import engine_provenance as ep                   # noqa: E402

# PROTOCOL §10 rule 3 / 1b -- PIN, do not merely REPORT.
#
# THIS FILE IS THE COUNTEREXAMPLE TO "EACH IS A ONE-LINE FIX". It inserts
# `domains` rather than `runners/dsl/python`, so it resolved the engine purely
# through the CANONICAL tree's `.pth`; and `substrate.boot_core` -- which LOADS
# the engine -- was imported ABOVE this line. MEASURED: with the pin left where
# the import sat, `substrate_rs` is already bound to the canonical binary and
# the preamble CANNOT rebind it (an extension module is bound at first import);
# it does not even refuse, because the Rust source is byte-identical, so the
# verdict is a legitimate `shared`. The prescribed one-liner would have changed
# only the line that gets PRINTED. The import is hoisted so the pin is real.
ep.engine_preamble()                                          # noqa: E402

from substrate.boot_core import boot_core, load_seeds_into    # noqa: E402
from domains import border_ownership_world as bow             # noqa: E402

SEED_BLOCK = 81000
FRAME_INDICES = (0, 25, 50, 75, 100, 125, 149)
N_DECODE = 150
K_LEVELS = (2, 4, 8, 16)
LATTICES = (16, 24, 32)
MAX_STEPS = 200_000

CORPORA = {
    "C1": {"what": "cartoon", "episode_index": 0, "pin": "08630d4b"},
    "C2": {"what": "live-action", "episode_index": 3, "pin": "119eca43"},
}


def _vp():
    spec = importlib.util.spec_from_file_location(
        "vp", os.path.join(ROOT, "scripts", "video_probe_measure.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def quantize(frame, k):
    """The incumbent quantizer, reproduced exactly (per-frame min/max)."""
    f = np.asarray(frame, float)
    lo, hi = float(f.min()), float(f.max())
    if hi <= lo:
        return [[0 for _ in row] for row in f]
    q = np.clip(((f - lo) / (hi - lo) * k).astype(int), 0, k - 1)
    return [[int(v) for v in row] for row in q]


# --- M1 / M2: read-out over the settled graph --------------------------------
def _neigh_map(s, handle):
    idx = handle["index"]
    H, W = handle["H"], handle["W"]
    rc = {idx[(r, c)]: (r, c) for r in range(H) for c in range(W)}
    at = {n: s.node(n)["attrs"] for n in rc}
    nb = {n: list(s.neighbours(n, "neighbour")) for n in rc}
    return rc, at, nb


def flood_and_gates(s, handle):
    """M1 (where the flood stops) + M2 (which gate refuses each component).

    Replicates bo_mint_enclosed's gates in the SAME ORDER the rule evaluates
    them (settled -> G_figadj -> G_gnd2 -> pass) so the attribution is
    reconcilable against the rules' minted output."""
    rc, at, nb = _neigh_map(s, handle)
    cells = list(rc)
    g = lambda n, k, d=0.0: float(at[n].get(k, d))  # noqa: E731

    n_frame = sum(1 for n in cells if g(n, "frame") >= 0.5)
    bgc = [n for n in cells if g(n, "bg") >= 0.5]
    enclosed = [n for n in cells if g(n, "bg") < 0.5]
    bg_frac = len(bgc) / len(cells) if cells else 0.0
    reach = len(bgc) - n_frame

    # frontier value gaps: adjacent pairs across the bg=1 / bg=0 boundary
    gaps = Counter()
    for n in bgc:
        for m in nb[n]:
            if g(m, "bg") < 0.5:
                gaps[int(round(abs(g(n, "val") - g(m, "val"))))] += 1

    # settled? (gate 4, global)
    can_flood = any(
        g(z, "bg") < 0.5 and (
            g(z, "frame") > 0.5 or
            any(g(m, "val") == g(z, "val") and g(m, "bg") > 0.5 for m in nb[z]))
        for z in cells)
    can_label = any(
        any(g(m, "val") == g(z, "val") and g(m, "glabel") < g(z, "glabel")
            for m in nb[z])
        for z in cells)
    settled = not (can_flood or can_label)

    comp: dict[float, list] = {}
    for n in enclosed:
        comp.setdefault(g(n, "glabel"), []).append(n)

    tally = Counter()
    sizes = []
    for lab, members in comp.items():
        sizes.append(len(members))
        if not settled:
            tally["G_settled"] += 1
            continue
        # G_figadj: any figure cell adjacent to a DIFFERENT enclosed component
        figadj = any(
            g(m, "glabel") != lab and g(m, "bg") < 0.5
            for f in members for m in nb[f])
        if figadj:
            tally["G_figadj"] += 1
            continue
        # G_gnd2: two ground neighbours of the figure with different glabel
        glabels = {g(gc, "glabel") for gc in cells
                   if g(gc, "bg") > 0.5
                   and any(g(f, "bg") < 0.5 and g(f, "glabel") == lab
                           for f in nb[gc])}
        if len(glabels) > 1:
            tally["G_gnd2"] += 1
            continue
        tally["G_pass"] += 1

    return {
        "n_cells": len(cells), "n_frame": n_frame,
        "bg_frac": bg_frac, "reach": reach,
        "n_enclosed": len(enclosed), "n_components": len(comp),
        "max_component": max(sizes) if sizes else 0,
        "mean_component": (sum(sizes) / len(sizes)) if sizes else 0.0,
        "settled": bool(settled),
        "frontier_gaps": dict(sorted(gaps.items())),
        "G_settled": tally["G_settled"], "G_figadj": tally["G_figadj"],
        "G_gnd2": tally["G_gnd2"], "G_pass": tally["G_pass"],
    }


def run_one(grid_vals, *, clear_frame=False):
    """One field through the UNCHANGED seed to its fixpoint."""
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_border_ownership"])
    handle = bow.add_field(s, grid_vals)
    if clear_frame:
        # DEAD-INSTRUMENT ARM: strip every seed so the flood cannot start.
        for n in handle["cell_ids"]:
            s.set_attr(n, "frame", 0.0)
    bow.set_flag(s, bown=1.0)
    t0 = time.time()
    sweeps = bow.tick(s, max_steps=MAX_STEPS)
    ms = (time.time() - t0) * 1e3
    protos = bow.protos(s)
    d = flood_and_gates(s, handle)
    return {"n_protos": len(protos),
            "n_protos_multicell": sum(1 for p in protos if p["members"] >= 2),
            "max_members": max([p["members"] for p in protos], default=0),
            "sweeps": sweeps, "ms": ms, **d}


# --- M3: value distributions, offline, no seed involved ----------------------
def _components(vals, ok):
    """Connected components of the 4-lattice under edge predicate ok(a, b)."""
    a = np.asarray(vals, int)
    H, W = a.shape
    seen = np.zeros((H, W), bool)
    sizes = []
    for r0 in range(H):
        for c0 in range(W):
            if seen[r0, c0]:
                continue
            seen[r0, c0] = True
            q, n = deque([(r0, c0)]), 0
            while q:
                r, c = q.popleft()
                n += 1
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < H and 0 <= cc < W and not seen[rr, cc] \
                            and ok(int(a[r, c]), int(a[rr, cc])):
                        seen[rr, cc] = True
                        q.append((rr, cc))
            sizes.append(n)
    return sizes


def value_stats(vals):
    a = np.asarray(vals, int)
    d = []
    d += list(np.abs(np.diff(a, axis=0)).ravel())
    d += list(np.abs(np.diff(a, axis=1)).ravel())
    d = np.asarray(d, int)
    eq = _components(vals, lambda x, y: x == y)
    gr = _components(vals, lambda x, y: abs(x - y) <= 1)
    return {
        "delta_hist": {int(k): int(v) for k, v in
                       sorted(Counter(d.tolist()).items())},
        "frac_delta0": float((d == 0).mean()) if d.size else 0.0,
        "frac_delta_le1": float((d <= 1).mean()) if d.size else 0.0,
        "eq_n": len(eq), "eq_max": max(eq), "eq_mean": float(np.mean(eq)),
        "grad_n": len(gr), "grad_max": max(gr), "grad_mean": float(np.mean(gr)),
    }


# --- controls ----------------------------------------------------------------
def synthetic(L):
    """A figure scaled to lattice L (the L=12 case is the committed control)."""
    g = [[0] * L for _ in range(L)]
    r0, r1 = int(L * 0.25), int(L * 0.75)
    c0, c1 = int(L * 0.33), int(L * 0.67)
    for r in range(r0, r1):
        for c in range(c0, c1):
            g[r][c] = 1
    return g, (r1 - r0) * (c1 - c0)


def controls():
    """D1 positive (must reproduce) + D2 dead-instrument (must FIRE)."""
    out = {}
    g12 = [[0] * 12 for _ in range(12)]
    for r in range(3, 9):
        for c in range(4, 8):
            g12[r][c] = 1
    d1 = run_one(g12)
    out["D1_committed_12x12"] = {
        **{k: d1[k] for k in ("n_protos", "max_members", "sweeps",
                              "n_frame", "bg_frac", "reach")},
        "expected": {"n_protos": 1, "members": 24},
        "reproduces": bool(d1["n_protos"] == 1 and d1["max_members"] == 24)}
    # D2a -- the REGISTERED dead-instrument field. It does NOT produce a vacuous
    # mint: with no seed every cell reads enclosed, so the 0-region and the
    # 1-region are two mutually-adjacent enclosed components and G_figadj
    # refuses BOTH. Recorded because the prereg predicted a vacuous mint here
    # and was wrong -- and because it is the first evidence for P2.
    d2a = run_one(g12, clear_frame=True)
    out["D2a_registered_field"] = {
        **{k: d2a[k] for k in ("n_protos", "max_members", "sweeps", "n_frame",
                               "bg_frac", "reach", "G_figadj", "G_pass")},
        "registered_expectation": "vacuous mint (n_protos > 0)",
        "fired": bool(d2a["n_protos"] > 0),
        "separated_from_live": bool(d2a["n_frame"] != d1["n_frame"]
                                    and d2a["bg_frac"] != d1["bg_frac"])}
    # D2b -- the trap REPRODUCED. A uniform field with no seed is ONE enclosed
    # component with nothing to touch, so the mint fires vacuously on a field
    # containing no figure at all: 1 proto, every cell a "member". This is the
    # blob rung's failure, demonstrated ACTUALLY FAILING, and M1 catches it by
    # n_frame = 0 / reach = 0 while n_protos > 0.
    uni = [[3] * 12 for _ in range(12)]
    d2b = run_one(uni, clear_frame=True)
    out["D2b_vacuous_mint"] = {
        **{k: d2b[k] for k in ("n_protos", "max_members", "sweeps", "n_frame",
                               "bg_frac", "reach")},
        "fired": bool(d2b["n_frame"] == 0 and d2b["reach"] == 0
                      and d2b["n_protos"] > 0),
        "separated_from_live": bool(d2b["n_frame"] != d1["n_frame"]
                                    and d2b["bg_frac"] != d1["bg_frac"])}
    # A uniform field WITH its seed intact: the same field, correctly flooded,
    # yields NO proto. The pair (D2b, D2c) is the whole point -- identical
    # pixels, opposite verdicts, decided entirely by whether the flood seeded.
    d2c = run_one(uni)
    out["D2c_uniform_seeded"] = {
        **{k: d2c[k] for k in ("n_protos", "max_members", "n_frame",
                               "bg_frac", "reach")}}
    out["D1_per_lattice"] = {}
    for L in LATTICES:
        g, exp = synthetic(L)
        r = run_one(g)
        out["D1_per_lattice"][str(L)] = {
            "n_protos": r["n_protos"], "max_members": r["max_members"],
            "expected_members": exp, "sweeps": r["sweeps"],
            "reproduces": bool(r["n_protos"] == 1 and r["max_members"] == exp)}
    return out


def main():
    prov = ep.provenance_line()
    print(f"[provenance] {prov}", flush=True)
    ctrl = controls()
    print(f"[D1 committed] {ctrl['D1_committed_12x12']}", flush=True)
    print(f"[D2a registered] {ctrl['D2a_registered_field']}", flush=True)
    print(f"[D2b vacuous mint] {ctrl['D2b_vacuous_mint']}", flush=True)
    print(f"[D2c uniform seeded] {ctrl['D2c_uniform_seeded']}", flush=True)
    print(f"[D1 per lattice] {ctrl['D1_per_lattice']}", flush=True)

    if not ctrl["D1_committed_12x12"]["reproduces"]:
        raise SystemExit("POSITIVE CONTROL DEAD -- no real-frame number claimed")
    if not (ctrl["D2b_vacuous_mint"]["fired"]
            and ctrl["D2b_vacuous_mint"]["separated_from_live"]):
        raise SystemExit("DEAD-INSTRUMENT ARM DID NOT FIRE -- instrument blind")

    out = {"provenance": prov, "prereg": "VISION_VALUE_FLOOD_PREREG.md",
           "prereg_commit": "8a0a3980", "seed_block": SEED_BLOCK,
           "lattices": list(LATTICES), "k_levels": list(K_LEVELS),
           "frame_indices": list(FRAME_INDICES),
           "controls": ctrl, "corpora": {}, "rows": []}

    vp = _vp()
    for cid, spec in CORPORA.items():
        for L in LATTICES:
            frames, meta = vp.jellyfin_frames(
                N_DECODE, every=2, start_s=300, size=L,
                episode_index=spec["episode_index"])
            got = str(meta["episode_id"])
            if not got.startswith(spec["pin"]):
                raise SystemExit(
                    f"PIN MISMATCH {cid}: expected {spec['pin']}… got {got} "
                    f"-- RUN VOID")
            out["corpora"][f"{cid}_L{L}"] = {"what": spec["what"],
                                             "episode_id": got,
                                             "n_decoded": len(frames)}
            print(f"[{cid}|L={L}] {spec['what']} decoded {len(frames)} pin ok",
                  flush=True)
            for k in K_LEVELS:
                for fi in FRAME_INDICES:
                    q = quantize(frames[fi], k)
                    r = run_one(q)
                    v = value_stats(q)
                    out["rows"].append({"corpus": cid, "L": L, "k": k,
                                        "frame": fi, **r, **v})
                    print(f"  [{cid}|L{L}|k{k:2d}|f{fi:3d}] "
                          f"protos={r['n_protos']} multi={r['n_protos_multicell']} "
                          f"bg={r['bg_frac']:.3f} reach={r['reach']} "
                          f"comp={r['n_components']} max={r['max_component']} "
                          f"figadj={r['G_figadj']} gnd2={r['G_gnd2']} "
                          f"pass={r['G_pass']} | eqmax={v['eq_max']} "
                          f"grmax={v['grad_max']} d0={v['frac_delta0']:.3f} "
                          f"({r['ms']:.0f}ms)", flush=True)

    rp = os.path.join(ROOT, "results", "value_flood.json")
    with open(rp, "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"[written] {rp}", flush=True)

    # RECONCILIATION: the attribution must agree with the rules' own output.
    bad = [r for r in out["rows"] if r["G_pass"] != r["n_protos"]]
    print(f"\n[reconciliation] rows={len(out['rows'])} mismatched={len(bad)}",
          flush=True)
    if bad:
        for r in bad[:5]:
            print(f"  MISMATCH {r['corpus']} L{r['L']} k{r['k']} f{r['frame']}"
                  f" G_pass={r['G_pass']} n_protos={r['n_protos']}", flush=True)


if __name__ == "__main__":
    main()
