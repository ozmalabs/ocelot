"""H1 (cost) + H2 (recognition) -- blob-native vs a RE-EARNED square baseline.

`VISION_BLOB_NATIVE_PREREG.md` (df0156a4, corrected 58e43007). Seeds 80000-80999.

MATCHED FIELD SIZE and MATCHED TASK: both arms identify one of the SAME N region
footprints over the SAME frames with the SAME quantizer and the SAME seed. Only
the sampling differs -- a complete pixel partition (N x region^2 samples) vs a
foveated blob field (M << pixels samples), with each footprint described by the
blobs whose centres fall inside it.

Verdict is `hamming` (set-overlap), for the two reasons fixed in the corrected
prereg: it admits the VARIABLE-LENGTH signatures foveation necessarily produces,
and read-back is only 0.5-1.8% of graph there, so a graph-cost claim is not
confounded by the reference instrument.

NOTHING TRANSFERS BY ASSUMPTION (H2). The noise floors are RE-MEASURED under
each representation: G2c (uniform-random cell values) and A3 (arrangement
shuffle, value multiset preserved exactly). Floors move with codebook size and
with representation, so a floor measured on the square arm is not a floor for
the blob arm.

Read-back is reported SPLIT into the graph-answer parse and the outside
reference, per prereg 0.2 -- which already established that the raster was not
the read-back cost.
"""
from __future__ import annotations

import importlib.util
import json
import math
import os
import random
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from domains import blob_sampler as bs                 # noqa: E402
from domains import engine_provenance as ep            # noqa: E402

# PROTOCOL §10 rule 3 / 1b -- PIN, do not merely REPORT. This script called
# `ep.provenance_line()` and never pinned, resolving through the
# `sys.path.insert(runners/dsl/python)` convention §10.2 measured as broken in
# a worktree (it pins a HEADLESS package there). The call must precede the
# first import that LOADS the engine, or it is a no-op on resolution and only
# changes the line that gets printed.
ep.engine_preamble()                                   # noqa: E402
from domains import invariant_comparator_world as iw   # noqa: E402

SEED_BLOCK = 80000
GRID = 24
REGION = 6
K = 4
N_FRAMES = 6
FRAME_STRIDE = 25
KAPPAS = (2.0, 4.0, 6.75)

CORPORA = {
    "C1": {"episode_index": 0, "pin": "08630d4b7b215c469df19b9c42d7b617",
           "what": "cartoon"},
    "C2": {"episode_index": 3, "pin": "119eca433329b36b19e5d69fef84966e",
           "what": "live-action"},
}


def _vp():
    spec = importlib.util.spec_from_file_location(
        "vp", os.path.join(ROOT, "scripts", "video_probe_measure.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def square_sigs(qframe):
    """The incumbent representation: N region footprints, each its complete
    region-local relation system. Byte-identical in construction to
    `invariant_comparator_world.sig_of` over `regions_of`."""
    return [iw.sig_of(t) for t in iw.regions_of(qframe, REGION)]


def blob_assign(layout, grid=GRID, region=REGION):
    """Assign each blob to the region footprint its CENTRE falls in.

    The footprints are the SAME N tiles the square arm identifies, so the task
    is matched exactly; only the description of each footprint changes. Group
    sizes VARY -- that is foveation, and it is why the verdict must be a set
    overlap rather than a fixed-length dot."""
    cy = cx = (grid - 1) / 2.0
    ncol = grid // region
    groups: dict[int, list[int]] = {}
    for i, (dy, dx, _r) in enumerate(layout):
        r = int(math.floor((cy + dy) / region))
        c = int(math.floor((cx + dx) / region))
        r = min(max(r, 0), ncol - 1)
        c = min(max(c, 0), ncol - 1)
        groups.setdefault(r * ncol + c, []).append(i)
    return groups


def blob_sigs(frame, layout, groups, n_groups):
    """Each footprint as the relation system of ITS blobs, indexed by INTEGER
    blob index -- no name string, so no fixed-width field to overflow."""
    vals = bs.sample_blobs(np.asarray(frame, float), layout, k=K)
    return [[["blob", int(i), f"v{int(vals[i])}"] for i in groups.get(g, [])]
            for g in range(n_groups)]


def run_arm(codebook_sigs, probe_sets, *, tag):
    """One substrate, one codebook, every probe. Returns timings and rows.

    The graph does the identification; this function times it and reads the
    answer back. The answer is read as an INTEGER INDEX attribute."""
    from substrate.boot_core import boot_core
    from substrate.seed_loader import manifest_for
    from domains import reflective_faculty as rf

    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    native.load_seed_manifest(manifest_for("vision_invariant_comparator"), ag)
    for p in s.nodes("InvComparatorParams"):
        s.set_attr(p, "invcomp", 1.0)

    order = list(range(len(codebook_sigs)))
    random.Random(SEED_BLOCK).shuffle(order)
    width = max(2, len(str(max(len(codebook_sigs) - 1, 0))))
    for i in order:
        s.add_node("XfSignature", {
            "name": f"r{i:0{width}d}", "region_index": float(i),
            "signature": json.dumps(codebook_sigs[i]),
            "kind": "faculty", "faculty": f"r{i:0{width}d}",
            "dim_types": iw.DIM_TYPES})

    groups = []
    for truth, sig in probe_sets:
        grp = s.add_node("ObsGroup", {"key": [f"{tag}|{truth}"],
                                      "status": "icg_pending"})
        s.add_edge(ag, "has_group", grp)
        node = s.add_node("Observation", {
            "signature": sig, "key": [f"{tag}|{truth}#0"],
            "status": "ic_pending", "dim_types": iw.DIM_TYPES})
        s.add_edge(ag, "observed", node)
        s.add_edge(grp, "has_member", node)
        groups.append((grp, truth, sig))

    t0 = time.perf_counter()
    native.run_rules()
    graph_s = time.perf_counter() - t0

    # READ-BACK, SPLIT. (a) the graph answer.
    t0 = time.perf_counter()
    said = []
    for grp, truth, _sig in groups:
        at = s.node(grp)["attrs"]
        nm = at.get("identified_as")
        idx = None
        if isinstance(nm, str) and nm.startswith("r") and nm[1:].isdigit():
            idx = int(nm[1:])          # FULL remaining field -- no fixed width
        said.append((truth, idx))
    parse_s = time.perf_counter() - t0

    # (b) the outside reference.
    t0 = time.perf_counter()
    csets = [{tuple(r) for r in cs} for cs in codebook_sigs]
    ref = []
    for _grp, truth, sig in groups:
        scores = [sum(1 for r in sig if tuple(r) in cs) for cs in csets]
        best = max(scores) if scores else 0
        ref.append((truth, scores.index(best) if scores else None,
                    sum(1 for x in scores if x == best)))
    ref_s = time.perf_counter() - t0

    acc = float(np.mean([1.0 if a == t else 0.0 for t, a in said])) if said else 0.0
    ref_acc = float(np.mean([1.0 if a == t else 0.0 for t, a, _n in ref])) if ref else 0.0
    n_none = sum(1 for _t, a in said if a is None)
    return {"graph_s": graph_s, "parse_s": parse_s, "ref_s": ref_s,
            "read_s": parse_s + ref_s, "acc": acc, "ref_acc": ref_acc,
            "n_probes": len(said), "n_answer_none": n_none,
            "n_tuples": sum(len(c) for c in codebook_sigs)}


def main():
    prov = ep.provenance_line()
    out = {"provenance": prov, "prereg": "VISION_BLOB_NATIVE_PREREG.md",
           "prereg_commit": "df0156a45717d785b56816eff42b782fb145a19e",
           "seed_block": SEED_BLOCK, "grid": GRID, "region": REGION, "k": K,
           "verdict": "hamming", "kappas": list(KAPPAS),
           "corpora": {}, "rows": []}
    print(f"[provenance] {prov}", flush=True)

    vp = _vp()
    R = (GRID - 1) / 2.0
    n_groups = (GRID // REGION) ** 2
    layouts = {}
    for kap in KAPPAS:
        lay = bs.blob_layout(R, bs.layout_count(kap, R))
        layouts[kap] = (lay, blob_assign(lay))
        occ = sum(1 for g in range(n_groups) if layouts[kap][1].get(g))
        print(f"[layout] kappa={kap} n_blobs={len(lay)} "
              f"footprints_occupied={occ}/{n_groups}", flush=True)
    out["layouts"] = {str(k): {"n_blobs": len(v[0]),
                               "occupied": sum(1 for g in range(n_groups)
                                               if v[1].get(g)),
                               **bs.eccentricity_profile(v[0])}
                      for k, v in layouts.items()}

    for cid, spec in CORPORA.items():
        frames, meta = vp.jellyfin_frames(N_FRAMES * FRAME_STRIDE + 1, every=2,
                                          start_s=300, size=GRID,
                                          episode_index=spec["episode_index"])
        if meta.get("episode_id") != spec["pin"]:
            raise SystemExit(f"EPISODE PIN MISMATCH {cid} -- run is VOID")
        out["corpora"][cid] = {"what": spec["what"], "meta": meta}
        print(f"[{cid}] {spec['what']}  pin ok", flush=True)

        for fi in range(0, N_FRAMES * FRAME_STRIDE, FRAME_STRIDE):
            if fi >= len(frames):
                continue
            f = np.asarray(frames[fi], float)[:GRID, :GRID]
            q = iw.quantize(f, K)
            rng = random.Random(SEED_BLOCK + 500 + fi)

            # ---- square arm: ARM + its OWN re-measured floors ----
            cb = square_sigs(q)
            probes = [(i, cb[i]) for i in range(len(cb))]
            r = run_arm(cb, probes, tag="sq")
            out["rows"].append({"corpus": cid, "frame": fi, "arm": "square",
                                "kappa": None, "cond": "arm",
                                "n_samples": GRID * GRID, **r})
            # A3 floor: arrangement destroyed, value multiset preserved.
            tiles = iw.regions_of(q, REGION)
            a3 = [(i, iw.sig_of(iw.shuffle_arrangement(tiles[i], rng)))
                  for i in range(len(tiles))]
            r3 = run_arm(cb, a3, tag="sq_a3")
            out["rows"].append({"corpus": cid, "frame": fi, "arm": "square",
                                "kappa": None, "cond": "A3_floor",
                                "n_samples": GRID * GRID, **r3})
            # G2c floor: uniform-random values, no image behind them.
            g2 = [(i, iw.sig_of(iw.uniform_noise_tile(rng, K, REGION)))
                  for i in range(len(tiles))]
            r2 = run_arm(cb, g2, tag="sq_g2")
            out["rows"].append({"corpus": cid, "frame": fi, "arm": "square",
                                "kappa": None, "cond": "G2c_floor",
                                "n_samples": GRID * GRID, **r2})
            print(f"  [{cid}|f{fi:3d}] square  n=576 graph={r['graph_s']*1000:7.1f}ms "
                  f"read={r['read_s']*1000:6.1f}ms acc={r['acc']:.3f} "
                  f"A3={r3['acc']:.3f} G2c={r2['acc']:.3f}", flush=True)

            # ---- blob arms: ARM + their OWN re-measured floors ----
            for kap in KAPPAS:
                lay, grp = layouts[kap]
                cbb = blob_sigs(f, lay, grp, n_groups)
                pb = [(i, cbb[i]) for i in range(n_groups)]
                rb = run_arm(cbb, pb, tag=f"bl{kap}")
                out["rows"].append({"corpus": cid, "frame": fi, "arm": "blob",
                                    "kappa": kap, "cond": "arm",
                                    "n_samples": len(lay), **rb})
                # A3 for blobs: permute VALUES over blob INDICES within a
                # footprint -- the multiset is preserved, the arrangement is
                # destroyed. The blob-native analogue, re-measured, not carried
                # over from the square arm.
                a3b = []
                for i in range(n_groups):
                    sig = list(cbb[i])
                    vals = [t[2] for t in sig]
                    rng.shuffle(vals)
                    a3b.append((i, [["blob", sig[j][1], vals[j]]
                                    for j in range(len(sig))]))
                rb3 = run_arm(cbb, a3b, tag=f"bl{kap}_a3")
                out["rows"].append({"corpus": cid, "frame": fi, "arm": "blob",
                                    "kappa": kap, "cond": "A3_floor",
                                    "n_samples": len(lay), **rb3})
                g2b = [(i, [["blob", int(j), f"v{rng.randrange(K)}"]
                            for j in grp.get(i, [])]) for i in range(n_groups)]
                rb2 = run_arm(cbb, g2b, tag=f"bl{kap}_g2")
                out["rows"].append({"corpus": cid, "frame": fi, "arm": "blob",
                                    "kappa": kap, "cond": "G2c_floor",
                                    "n_samples": len(lay), **rb2})
                print(f"  [{cid}|f{fi:3d}] blob k={kap:<5} n={len(lay):3d} "
                      f"graph={rb['graph_s']*1000:7.1f}ms "
                      f"read={rb['read_s']*1000:6.1f}ms acc={rb['acc']:.3f} "
                      f"A3={rb3['acc']:.3f} G2c={rb2['acc']:.3f}", flush=True)

    rp = os.path.join(ROOT, "results", "blob_cost.json")
    with open(rp, "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"[written] {rp}", flush=True)

    print("\n=== H1/H2 (per corpus, never pooled) ===", flush=True)
    for cid in CORPORA:
        for kap in (None,) + KAPPAS:
            arm = "square" if kap is None else "blob"
            sel = lambda cond: [r for r in out["rows"]
                                if r["corpus"] == cid and r["arm"] == arm
                                and r["kappa"] == kap and r["cond"] == cond]
            a, f3, f2 = sel("arm"), sel("A3_floor"), sel("G2c_floor")
            if not a:
                continue
            print(f"[{cid}] {arm} kappa={kap} n_samples={a[0]['n_samples']} "
                  f"graph={np.mean([r['graph_s'] for r in a])*1000:8.1f}ms "
                  f"parse={np.mean([r['parse_s'] for r in a])*1000:6.2f}ms "
                  f"ref={np.mean([r['ref_s'] for r in a])*1000:7.2f}ms "
                  f"acc={np.mean([r['acc'] for r in a]):.3f} "
                  f"A3={np.mean([r['acc'] for r in f3]):.3f} "
                  f"G2c={np.mean([r['acc'] for r in f2]):.3f} "
                  f"none={sum(r['n_answer_none'] for r in a)}", flush=True)


if __name__ == "__main__":
    main()
