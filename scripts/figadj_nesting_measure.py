"""figadj_nesting_measure -- does scoping the rival set to R's OUTER CONTOUR
(the containment correction) stop ownership inverting, what does it cost, and
does it move the SIZE DISTRIBUTION?

Pre-registration: VISION_FIGADJ_NESTING_PREREG.md. Seeds 92000-92999.

Mechanical I/O + read-out ONLY. Every decision is the seed's
(`vision_border_ownership` v1.3.0): the flood, the labelling, the ownership
competition, the well-posedness hold-open, the containment scope and the mint
are ALL rules. This script builds fields, ticks to a fixpoint, and measures.

FOUR INSTRUMENT DISCIPLINES ARE LOAD-BEARING HERE:

1. M-E, THE VACUITY GATE, RUNS FIRST (s1 fifth clause / FM-0), and it runs on
   REAL-FRAME TILES, not speckle -- speckle has few holes-in-holes and is the
   wrong material for this conjunct. Declared in the prereg in advance.

2. NO FLOOR IS INHERITED. The incumbent, replacement AND wellposed arms are all
   re-measured in this tree on this engine. The predecessor's own words: "had I
   inherited the floor I'd have reported a 3x GAIN OVER A ZERO THAT WASN'T
   THERE."

3. ALL FOUR ARMS RUN THROUGH THE SUBSTRATE, and the read-out replicates the
   FOURTH predicate explicitly, reconciled against the rules' own minted output
   (`G_pass == n_protos`) SEPARATELY UNDER EACH ARM.

4. PROVENANCE IS PRINTED FROM INSIDE THIS PROCESS and the run aborts on
   divergence. A green gate in a DIFFERENT process is not provenance.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import time
from collections import Counter

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "domains"))

from domains import engine_provenance as ep                  # noqa: E402

ep.engine_preamble()

from substrate.boot_core import boot_core, load_seeds_into   # noqa: E402
from domains import border_ownership_world as bow            # noqa: E402

SEED_BLOCK = 92000

# G72 -- the resolution rung's configuration and both predecessors', verbatim,
# so the comparison is at the SAME GRAIN.
GRID = 72
REGION = 18
K_MAIN = 16
SAMPLED_FRAMES = (0, 25, 50, 75, 100, 125, 149)
N_DECODE = 160
MAX_STEPS = 200

# (bown_own, bown_wp, bown_nest) -- the four arms of PREREG s2.
ARMS = {"incumbent":   (0.0, 0.0, 0.0),
        "replacement": (1.0, 0.0, 0.0),
        "wellposed":   (1.0, 1.0, 0.0),
        "nested":      (1.0, 1.0, 1.0)}

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


def region_origins(shape=(GRID, GRID), region=REGION):
    h, w = shape
    return [(r0, c0)
            for r0 in range(0, h - h % region, region)
            for c0 in range(0, w - w % region, region)]


def tile(vals, r0, c0, region=REGION):
    return [row[c0:c0 + region] for row in vals[r0:r0 + region]]


def read_out(s, handle, arm):
    """Replicates the ARMED rule's gates IN THE ORDER the rule evaluates them,
    so the attribution reconciles against the rules' own minted output."""
    idx = handle["index"]
    H, W = handle["H"], handle["W"]
    rc = {idx[(r, c)]: (r, c) for r in range(H) for c in range(W)}
    at = {n: s.node(n)["attrs"] for n in rc}
    nb = {n: list(s.neighbours(n, "neighbour")) for n in rc}
    cells = list(rc)
    g = lambda n, k, d=0.0: float(at[n].get(k, d))          # noqa: E731

    n_frame = sum(1 for n in cells if g(n, "frame") >= 0.5)
    bgc = [n for n in cells if g(n, "bg") >= 0.5]
    enclosed = [n for n in cells if g(n, "bg") < 0.5]
    reach = len(bgc) - n_frame

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

    rim_computed = {
        lab: sum(1 for f in members
                 if any(g(m, "glabel") != lab for m in nb[f]))
        for lab, members in comp.items()}
    rim_mismatch = sum(
        1 for lab, members in comp.items() for f in members
        if int(round(g(f, "rim"))) != rim_computed[lab])

    # THE CONTAINMENT PREDICATE, replicated exactly as the rule states it:
    # component `q` is CONTAINED in `lab` iff no member of q has a neighbour
    # that is neither q nor lab.
    def contained_in(qlab, lab):
        return not any(
            any(g(p, "glabel") != qlab and g(p, "glabel") != lab
                for p in nb[c])
            for c in comp[qlab])

    tally = Counter()
    for lab, members in comp.items():
        if not settled:
            tally["G_settled"] += 1
            continue
        # rivals, per the ARM's own definition of a rival
        raw = {g(m, "glabel") for f in members for m in nb[f]
               if g(m, "bg") < 0.5 and g(m, "glabel") != lab}
        if arm == "nested":
            rivals = {q for q in raw if not contained_in(q, lab)}
        else:
            rivals = raw
        if arm == "incumbent":
            if rivals:
                tally["G_figadj"] += 1
                continue
        else:
            if any(not (rim_computed[lab] < rim_computed[q]) for q in rivals):
                tally["G_own_lost"] += 1
                continue
        if arm in ("wellposed", "nested"):
            ill = any(
                len({g(m, "glabel") for m in nb[f]
                     if g(m, "bg") < 0.5 and g(m, "glabel") != lab
                     and g(m, "glabel") in rivals}) > 1
                for f in members)
            if ill:
                tally["G_illposed"] += 1
                continue
        glabels = {g(gc, "glabel") for gc in cells
                   if g(gc, "bg") > 0.5
                   and any(g(f, "bg") < 0.5 and g(f, "glabel") == lab
                           for f in nb[gc])}
        if len(glabels) > 1:
            tally["G_gnd2"] += 1
            continue
        tally["G_pass"] += 1

    # M-F: the SIZE DISTRIBUTION -- the brief's actual target.
    nest_pairs = sum(1 for a in comp for b in comp
                     if a != b and contained_in(b, a)) if settled else 0

    protos = bow.protos(s)
    sizes = [p["members"] for p in protos]
    return {
        "n_cells": len(cells), "n_frame": n_frame, "reach": reach,
        "n_enclosed": len(enclosed), "n_components": len(comp),
        "settled": bool(settled), "rim_mismatch": rim_mismatch,
        "n_nested_pairs": nest_pairs,
        "G_settled": tally["G_settled"], "G_figadj": tally["G_figadj"],
        "G_own_lost": tally["G_own_lost"], "G_illposed": tally["G_illposed"],
        "G_gnd2": tally["G_gnd2"], "G_pass": tally["G_pass"],
        "n_protos": len(protos),
        "n_protos_multicell": sum(1 for x in sizes if x >= 2),
        "proto_sizes": sizes,
        "max_members": max(sizes, default=0),
        "max_members_frac": (max(sizes, default=0) / len(cells)
                             if cells else 0.0),
    }


def run_one(grid_vals, arm, *, clear_frame=False):
    own, wp, nest = ARMS[arm]
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_border_ownership"])
    handle = bow.add_field(s, grid_vals)
    if clear_frame:
        for n in handle["cell_ids"]:
            s.set_attr(n, "frame", 0.0)
    bow.set_flag(s, bown=1.0, bown_own=own, bown_wp=wp, bown_nest=nest)
    sweeps = bow.tick(s, max_steps=MAX_STEPS)
    return {"sweeps": sweeps, **read_out(s, handle, arm)}


def controls(log, real_tiles):
    """M-E FIRST (vacuity, on REAL tiles), then D1 / D2b / single-cell figure,
    then M-A (the registered speckle control) on all four arms."""
    out = {}
    g12 = [[0] * 12 for _ in range(12)]
    for r in range(3, 9):
        for c in range(4, 8):
            g12[r][c] = 1
    uni = [[3] * 12 for _ in range(12)]
    g1 = [[0] * 12 for _ in range(12)]           # a GENUINE 1-cell figure
    g1[6][6] = 1

    # ---- M-E: VACUITY GATE, on real-frame tiles, before a seed is burned ---
    dmax = 0
    for q in real_tiles[:20]:
        dmax = max(dmax, abs(run_one(q, "wellposed")["n_protos"]
                             - run_one(q, "nested")["n_protos"]))
    out["M_E_vacuity"] = {"D": dmax, "live": bool(dmax > 0),
                          "n_fields": len(real_tiles[:20]),
                          "material": "real-frame G72 tiles (declared in prereg)"}
    log(f"[M-E] vacuity D={dmax} live={dmax > 0}")
    if dmax == 0:
        raise SystemExit("M-E: CONJUNCT IS DECORATIVE (D==0) -- nothing claimed")

    for arm in ARMS:
        d1 = run_one(g12, arm)
        out[f"D1_{arm}"] = {
            **{k: d1[k] for k in ("n_protos", "max_members", "n_frame",
                                  "reach")},
            "expected": {"n_protos": 1, "members": 24},
            "reproduces": bool(d1["n_protos"] == 1 and d1["max_members"] == 24)}
        d2b = run_one(uni, arm, clear_frame=True)
        out[f"D2b_{arm}"] = {
            **{k: d2b[k] for k in ("n_protos", "max_members", "n_frame",
                                   "reach")},
            "fired": bool(d2b["n_frame"] == 0 and d2b["reach"] == 0
                          and d2b["n_protos"] > 0)}
        one = run_one(g1, arm)
        out[f"SINGLECELL_FIGURE_{arm}"] = {
            "n_protos": one["n_protos"], "max_members": one["max_members"],
            "mints": bool(one["n_protos"] == 1 and one["max_members"] == 1)}
        log(f"[control/{arm}] D1={out[f'D1_{arm}']['reproduces']} "
            f"D2b_fired={out[f'D2b_{arm}']['fired']} "
            f"1cell_figure_mints={out[f'SINGLECELL_FIGURE_{arm}']['mints']}")

    # ---- M-A: the registered speckle control, FRESH seeds, SAME fields -----
    nrng = np.random.RandomState(SEED_BLOCK + 900)
    hits = {a: 0 for a in ARMS}
    msize = {a: [] for a in ARMS}
    for _ in range(100):
        q = nrng.randint(0, K_MAIN, (REGION, REGION)).tolist()
        for arm in ARMS:
            r = run_one(q, arm)
            if r["n_protos"] > 0:
                hits[arm] += 1
                msize[arm].append(r["max_members"])
    for arm in ARMS:
        out[f"NOISE_{arm}"] = {
            "n_fields": 100, "fields_minting": hits[arm],
            "false_mint_rate": hits[arm] / 100.0,
            "max_false_proto_size": max(msize[arm], default=0),
            "CONTROL_PASSES": hits[arm] == 0, "seed": SEED_BLOCK + 900}
        log(f"[M-A/{arm}] speckle minting {hits[arm]}/100 "
            f"max_false_size={max(msize[arm], default=0)}")
    return out


def dist(sizes):
    if not sizes:
        return {"n": 0, "median": None, "mean": None, "p90": None, "max": None}
    a = np.asarray(sizes, float)
    return {"n": int(a.size), "median": float(np.median(a)),
            "mean": float(a.mean()), "p90": float(np.percentile(a, 90)),
            "max": float(a.max())}


def main():
    t0 = time.time()
    prov = ep.provenance_line()
    logf = open(os.path.join(ROOT, "results", "figadj_nesting.log"), "w")

    def log(m):
        print(m, flush=True)
        logf.write(m + "\n")
        logf.flush()

    log("== PROVENANCE (printed from INSIDE the measuring process) ==")
    log(prov)
    if "WRONG ENGINE" in prov or "DIVERGED" in prov:
        raise SystemExit("ENGINE PROVENANCE FAILED -- RUN VOID")

    # ---- decode first: M-E needs real tiles ------------------------------
    vp = _vp()
    origins = region_origins()
    decoded = {}
    for cid in ("C1", "C2"):
        spec = CORPORA[cid]
        frames, meta = vp.jellyfin_frames(
            N_DECODE, every=2, start_s=300, size=GRID,
            episode_index=spec["episode_index"])
        got = str(meta["episode_id"])
        if not got.startswith(spec["pin"]):
            raise SystemExit(f"PIN MISMATCH {cid}: expected {spec['pin']} "
                             f"got {got} -- RUN VOID")
        decoded[cid] = (frames, got)
        log(f"[{cid}] {spec['what']} decoded {len(frames)} @ {GRID}x{GRID} "
            f"pin {got[:8]} ok, {len(origins)} tiles of {REGION}x{REGION}")

    q0 = quantize(decoded["C1"][0][0], K_MAIN)
    q1 = quantize(decoded["C2"][0][0], K_MAIN)
    real_tiles = ([tile(q0, r0, c0) for r0, c0 in origins]
                  + [tile(q1, r0, c0) for r0, c0 in origins])[:20]

    ctrl = controls(log, real_tiles)
    for arm in ARMS:
        if not ctrl[f"D1_{arm}"]["reproduces"]:
            raise SystemExit(f"POSITIVE CONTROL DEAD ({arm}) -- nothing claimed")
    if not ctrl["D2b_nested"]["fired"]:
        raise SystemExit("DEAD-INSTRUMENT ARM DID NOT FIRE -- instrument blind")

    out = {"provenance": prov, "prereg": "VISION_FIGADJ_NESTING_PREREG.md",
           "seed_block": [SEED_BLOCK, SEED_BLOCK + 999],
           "config": {"GRID": GRID, "REGION": REGION,
                      "n_tiles": len(origins), "k_main": K_MAIN,
                      "sampled_frames": list(SAMPLED_FRAMES)},
           "controls": ctrl,
           "corpora": {cid: {"what": CORPORA[cid]["what"],
                             "episode_id": decoded[cid][1],
                             "n_decoded": len(decoded[cid][0])}
                       for cid in CORPORA},
           "m_c_rows": []}

    # ---- M-C (cost) + M-F (size distribution), all four arms -------------
    for cid in ("C1", "C2"):
        frames = decoded[cid][0]
        for arm in ARMS:
            for fi in SAMPLED_FRAMES:
                q = quantize(frames[fi], K_MAIN)
                agg = Counter()
                protos = multi = 0
                sizes = []
                for r0, c0 in origins:
                    r = run_one(tile(q, r0, c0), arm)
                    for key in ("G_settled", "G_figadj", "G_own_lost",
                                "G_illposed", "G_gnd2", "G_pass",
                                "n_components", "n_enclosed", "rim_mismatch",
                                "n_nested_pairs"):
                        agg[key] += r[key]
                    protos += r["n_protos"]
                    multi += r["n_protos_multicell"]
                    sizes.extend(r["proto_sizes"])
                out["m_c_rows"].append({
                    "corpus": cid, "arm": arm, "k": K_MAIN, "frame": fi,
                    "n_protos": protos, "n_protos_multicell": multi,
                    "proto_sizes": sizes,
                    **{key: agg[key] for key in
                       ("G_settled", "G_figadj", "G_own_lost", "G_illposed",
                        "G_gnd2", "G_pass", "n_components", "n_enclosed",
                        "rim_mismatch", "n_nested_pairs")}})
                log(f"  [M-C {cid}|{arm[:5]}|f{fi:3d}] protos={protos} "
                    f"multi={multi} comps={agg['n_components']} "
                    f"nest_pairs={agg['n_nested_pairs']} "
                    f"pass={agg['G_pass']} med="
                    f"{np.median(sizes) if sizes else 0}")

    summ = {}
    for cid in CORPORA:
        for arm in ARMS:
            rows = [r for r in out["m_c_rows"]
                    if r["corpus"] == cid and r["arm"] == arm]
            allsz = [x for r in rows for x in r["proto_sizes"]]
            multi_sz = [x for x in allsz if x >= 2]
            summ[f"{cid}|{arm}"] = {
                "mean_protos": float(np.mean([r["n_protos"] for r in rows])),
                "mean_multicell": float(
                    np.mean([r["n_protos_multicell"] for r in rows])),
                "reconciles": all(r["G_pass"] == r["n_protos"] for r in rows),
                "mean_components": float(
                    np.mean([r["n_components"] for r in rows])),
                "mean_nested_pairs": float(
                    np.mean([r["n_nested_pairs"] for r in rows])),
                "size_all": dist(allsz),
                "size_multicell": dist(multi_sz),
                "size_hist": {str(k): int(v)
                              for k, v in sorted(Counter(allsz).items())},
            }
    out["m_c_summary"] = summ
    out["elapsed_s"] = time.time() - t0

    path = os.path.join(ROOT, "results", "figadj_nesting.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1)
    log(f"[written] {path}")
    for k, v in summ.items():
        log(f"  {k}: protos={v['mean_protos']:.1f} "
            f"multi={v['mean_multicell']:.1f} "
            f"comps={v['mean_components']:.1f} "
            f"med_size={v['size_all']['median']} "
            f"p90={v['size_all']['p90']} max={v['size_all']['max']} "
            f"recon={v['reconciles']}")


if __name__ == "__main__":
    main()
