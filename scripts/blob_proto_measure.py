"""H3 -- THE SHARPEST TEST: does a blob decomposition make PROTO-OBJECTS work
where the square grid did not?

`VISION_BLOB_NATIVE_PREREG.md` (committed df0156a4, corrected 58e43007), §H3.
Seeds 80000-80999.

Proto-objects have produced 0 protos on 7/7 real frames, byte-identically across
two probes. The registered prediction is that a blob field does NOT change this,
because §0.3 established that the proto stage never sees the region grid at all
-- it consumes a raw quantized luminance lattice in its own substrate, and the
gates that must pass are VALUE-FLOOD conditions, not tile-boundary conditions.

The prediction is registered so a null cannot be retrofitted as expected. And
the mechanism is MEASURED, not inferred: §0.3's attribution to gates 2 and 5
came from reading rule comments, and this script converts it to a measurement by
counting, per frame, how many cells are enclosed at all (bg=0) and how many
figure components the single-ground gate refuses.

ARM (blob) vs BASELINE (square): the SAME frames, the SAME quantizer, the SAME
seed, the SAME rules. Only the FIELD GRAPH differs -- pixel lattice with
4-neighbour edges vs blob field with overlap adjacency. Nothing else moves.
"""
from __future__ import annotations

import importlib.util
import json
import math
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from domains import blob_sampler as bs               # noqa: E402
from domains import border_ownership_world as bow    # noqa: E402
from domains import engine_provenance as ep          # noqa: E402

# PROTOCOL §10 rule 3 / 1b -- PIN, do not merely REPORT. Must precede the
# `substrate.boot_core` import below, which LOADS the engine: a preamble that
# runs after the first engine import is a no-op on resolution.
ep.engine_preamble()                                 # noqa: E402

from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402

SEED_BLOCK = 80000

#: Inherited UNCHANGED from the video probe, so the baseline reproduces its
#: byte-identical 0-on-7/7 rather than being re-specified here.
CORPORA = {
    "C1": {"episode_index": 0, "pin": "08630d4b7b215c469df19b9c42d7b617",
           "what": "cartoon"},
    "C2": {"episode_index": 3, "pin": "119eca433329b36b19e5d69fef84966e",
           "what": "live-action"},
}
#: MATCHED TO THE INCUMBENT EXACTLY (VISION_VIDEO_PROBE_RERUN_RESULTS.md S3):
#: grid 16, the k sweep, and frames SPREAD across the clip (0,25,...,149) -- not
#: 7 consecutive ones. A first run of this script used grid=24 and consecutive
#: frames and did NOT reproduce the committed 0-on-7/7; that was the harness
#: differing from the incumbent, not the instrument being broken, and it is
#: recorded because a baseline that does not reproduce invalidates every
#: comparison drawn against it.
GRID = 16
FRAME_INDICES = (0, 25, 50, 75, 100, 125, 149)
N_DECODE = 150
K_LEVELS = (2, 4, 8, 16)
KAPPAS = (1.0, 2.0, 3.0, 4.0)
S3_MAX_STEPS = 200_000


def _vp():
    spec = importlib.util.spec_from_file_location(
        "vp", os.path.join(ROOT, "scripts", "video_probe_measure.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def quantize(frame, k):
    """The video probe's own quantizer, reproduced exactly (per-frame min/max)
    so the baseline arm is the incumbent's input, not a new one."""
    f = np.asarray(frame, float)
    lo, hi = float(f.min()), float(f.max())
    if hi <= lo:
        return [[0 for _ in row] for row in f]
    q = np.clip(((f - lo) / (hi - lo) * k).astype(int), 0, k - 1)
    return [[int(v) for v in row] for row in q]


def blob_field(s, vals, layout, R):
    """Build the proto stage's Field from BLOBS instead of pixels.

    Mechanical translation, exactly the class `add_field` is: one `Cell` per
    blob, `neighbour` edges wherever two blob supports OVERLAP (centre distance
    <= r_i + r_j -- the adjacency the representation itself implies, not a
    4-neighbour lattice imposed on it), and `frame=1` for any blob whose support
    reaches the field boundary (the blob analogue of a border pixel, since the
    bg flood must have somewhere to start).

    Returns the same handle shape `add_field` returns, so every downstream
    readout is unchanged."""
    n = len(layout)
    field = s.add_node("Field", {"H": float(n), "W": 1.0})
    ids, index = [], {}
    # THE BORDER IS STRUCTURAL, NOT A THRESHOLD. A first version flagged a blob
    # as frame when `hypot(dy,dx) + r >= R`, and at kappa in {1,2,3} that matched
    # NOTHING (the geometric ring ladder terminates before the field edge). With
    # no frame cell the bg flood has no seed, every blob keeps its initial bg=0,
    # every component reads as "enclosed", and the mint rule fires VACUOUSLY --
    # producing exactly 1 proto on every frame of both corpora at every k, which
    # is what a layout artifact looks like when it is mistaken for a percept.
    # An absence off a threshold is evidence of a LOOKUP, not a measurement
    # (PROTOCOL 1.1). So the border is now the OUTERMOST RING by construction,
    # and it is ASSERTED below rather than hoped for.
    ecc = [math.hypot(dy, dx) for dy, dx, _r in layout]
    outer = max(ecc) if ecc else 0.0
    for i, ((dy, dx, r), v) in enumerate(zip(layout, vals)):
        on_edge = abs(math.hypot(dy, dx) - outer) < 1e-9 and outer > 0.0
        node = s.add_node("Cell", {
            "crow": float(i), "ccol": 0.0,
            "val": float(v),
            "frame": 1.0 if on_edge else 0.0,
            "cid": float(i),
            "bg": 0.0, "glabel": float(i), "owns": 0.0})
        s.add_edge_unchecked(field, "has_cell", node)
        ids.append(node)
        index[(i, 0)] = node
    adj = 0
    for i, (yi, xi, ri) in enumerate(layout):
        for j, (yj, xj, rj) in enumerate(layout):
            if i == j:
                continue
            if math.hypot(yi - yj, xi - xj) <= (ri + rj):
                s.add_edge_unchecked(ids[i], "neighbour", ids[j])
                adj += 1
    n_frame = sum(1 for c in ids
                  if float(s.node(c)["attrs"].get("frame", 0.0)) >= 0.5)
    if n_frame == 0:
        raise ValueError(
            f"BLOB FIELD HAS NO BORDER: {n} blobs, none flagged frame=1. The bg "
            f"flood would have no seed, every cell would read as enclosed, and "
            f"the mint rule would fire vacuously on every frame. This is the "
            f"silent-absence failure the structural border exists to kill.")
    return {"field": field, "cell_ids": ids, "index": index,
            "H": n, "W": 1, "n_adj": adj, "n_frame": n_frame}


def gate_diagnostics(s, handle):
    """MEASURE the two gates §0.3 could only infer.

    gate 2 (`bg < 0.5`)  -- how many cells are ENCLOSED at all. If this is ~0,
                            nothing is even a figure candidate and no change to
                            the sampling geometry can produce a proto.
    gate 5 (single-ground) -- for each enclosed component, how many DISTINCT
                            glabels sit on its ground side. A component is
                            refused unless that count is 1.

    Pure query over graph state after the fixpoint. Computed here, in the
    read-out, never by the rules under test."""
    cells = list(s.nodes("Cell"))
    at = {c: s.node(c)["attrs"] for c in cells}
    enclosed = [c for c in cells if float(at[c].get("bg", 0.0)) < 0.5]
    comp: dict[float, list] = {}
    for c in enclosed:
        comp.setdefault(float(at[c].get("glabel", -1.0)), []).append(c)
    refused = singly = vacuous = 0
    sizes = []
    for lab, members in comp.items():
        mset = set(members)
        ground_labels = set()
        for m in members:
            for nb in s.neighbours(m, "neighbour"):
                if nb in mset:
                    continue
                a = s.node(nb)["attrs"]
                if float(a.get("bg", 0.0)) >= 0.5:
                    ground_labels.add(float(a.get("glabel", -1.0)))
        sizes.append(len(members))
        # ZERO ground neighbours is VACUOUSLY single-ground: the rule's gate is
        # `Not Exists two ground cells with different glabel`, which is TRUE
        # when there are none. An earlier version of this diagnostic counted
        # that case as REFUSED and so reported 43 refusals beside 43 minted
        # protos -- a diagnostic contradicting the rule it claims to measure.
        if len(ground_labels) <= 1:
            singly += 1
            if not ground_labels:
                vacuous += 1
        else:
            refused += 1
    return {"n_cells": len(cells),
            "n_enclosed": len(enclosed),
            "frac_enclosed": len(enclosed) / len(cells) if cells else 0.0,
            "n_enclosed_components": len(comp),
            "n_singly_surrounded": singly,
            "n_vacuously_single": vacuous,
            "n_refused_by_ground_gate": refused,
            "max_component": max(sizes) if sizes else 0}


def positive_control():
    """The instrument's own liveness check, reproduced from
    `video_probe_measure._s3_positive_control`: a 12x12 synthetic figure that
    MUST yield exactly 1 proto with 24 members.

    If this does not reproduce, NO real-frame number is claimed -- a gate that
    has never been able to fail has not been tested, and a null from a dead
    instrument is not a null."""
    H = W = 12
    g = [[0] * W for _ in range(H)]
    for r in range(3, 9):
        for c in range(4, 8):
            g[r][c] = 1
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_border_ownership"])
    bow.add_field(s, g)
    bow.set_flag(s, bown=1.0)
    sweeps = bow.tick(s, max_steps=S3_MAX_STEPS)
    protos = bow.protos(s)
    ok = (len(protos) == 1 and protos[0]["members"] == 24)
    return {"n_protos": len(protos),
            "members": protos[0]["members"] if protos else None,
            "sweeps": sweeps, "expected": {"n_protos": 1, "members": 24},
            "reproduces_committed_answer": bool(ok)}


def run_one(grid_vals, *, blob=False, layout=None, R=None):
    """One field through the UNCHANGED seed to its fixpoint."""
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_border_ownership"])
    if blob:
        handle = blob_field(s, grid_vals, layout, R)
    else:
        handle = bow.add_field(s, grid_vals)
    bow.set_flag(s, bown=1.0)
    sweeps = bow.tick(s)
    return {"n_protos": bow.n_protos(s), "protos": bow.protos(s),
            "sweeps": sweeps, **gate_diagnostics(s, handle),
            "n_adj": handle.get("n_adj"), "n_frame": handle.get("n_frame")}


def main():
    prov = ep.provenance_line()
    ctrl = positive_control()
    out = {"provenance": prov, "prereg": "VISION_BLOB_NATIVE_PREREG.md",
           "prereg_commit": "df0156a45717d785b56816eff42b782fb145a19e",
           "correction_commit": "58e43007",
           "seed_block": SEED_BLOCK, "grid": GRID,
           "frame_indices": list(FRAME_INDICES),
           "k_levels": list(K_LEVELS), "kappas": list(KAPPAS),
           "registered_prediction": "NULL (protos stay 0 at k=16 under blobs)",
           "positive_control": ctrl,
           "corpora": {}, "rows": []}
    print(f"[provenance] {prov}", flush=True)
    print(f"[positive control] {ctrl}", flush=True)
    if not ctrl["reproduces_committed_answer"]:
        out["verdict"] = "UNINTERPRETABLE -- positive control failed"
        with open(os.path.join(ROOT, "results", "blob_proto.json"), "w") as fh:
            json.dump(out, fh, indent=1)
        raise SystemExit("POSITIVE CONTROL FAILED -- no real-frame number claimed")

    vp = _vp()
    R = (GRID - 1) / 2.0
    layouts = {}
    for kap in KAPPAS:
        lay = bs.blob_layout(R, bs.layout_count(kap, R))
        layouts[kap] = lay
        print(f"[layout] kappa={kap} n_blobs={len(lay)} "
              f"{bs.eccentricity_profile(lay)}", flush=True)
    out["layouts"] = {str(k): {"n": len(v), **bs.eccentricity_profile(v)}
                      for k, v in layouts.items()}

    for cid, spec in CORPORA.items():
        frames, meta = vp.jellyfin_frames(N_DECODE, every=2, start_s=300,
                                          size=GRID,
                                          episode_index=spec["episode_index"])
        if meta.get("episode_id") != spec["pin"]:
            raise SystemExit(f"EPISODE PIN MISMATCH {cid}: "
                             f"{meta.get('episode_id')} != {spec['pin']}"
                             f" -- run is VOID")
        out["corpora"][cid] = {"what": spec["what"], "meta": meta,
                               "n_decoded": len(frames)}
        print(f"[{cid}] {spec['what']} decoded {len(frames)}  pin ok", flush=True)

        for fi in FRAME_INDICES:
            if fi >= len(frames):
                continue
            f = np.asarray(frames[fi], float)[:GRID, :GRID]
            for k in K_LEVELS:
                g = quantize(f, k)
                base = run_one(g, blob=False)
                out["rows"].append({"corpus": cid, "k": k, "frame": fi,
                                    "arm": "square", "kappa": None,
                                    "n_samples": GRID * GRID, **base})
                print(f"  [{cid}|k{k:2d}|f{fi:3d}] square n=256 "
                      f"protos={base['n_protos']} "
                      f"encl={base['n_enclosed']} comp={base['n_enclosed_components']} "
                      f"refused={base['n_refused_by_ground_gate']}", flush=True)
                for kap in KAPPAS:
                    lay = layouts[kap]
                    vals = bs.sample_blobs(f, lay, k=k)
                    arm = run_one(vals, blob=True, layout=lay, R=R)
                    out["rows"].append({"corpus": cid, "k": k, "frame": fi,
                                        "arm": "blob", "kappa": kap,
                                        "n_samples": len(lay), **arm})
                    print(f"  [{cid}|k{k:2d}|f{fi:3d}] blob  kap={kap} n={len(lay):3d} "
                          f"protos={arm['n_protos']} "
                          f"encl={arm['n_enclosed']} comp={arm['n_enclosed_components']} "
                          f"refused={arm['n_refused_by_ground_gate']} "
                          f"vac={arm['n_vacuously_single']}", flush=True)

    rp = os.path.join(ROOT, "results", "blob_proto.json")
    with open(rp, "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"[written] {rp}", flush=True)

    # PER CORPUS, NEVER POOLED.
    print("\n=== H3 VERDICT (per corpus, per k) ===", flush=True)
    for cid in CORPORA:
        for k in K_LEVELS:
            sq = [r for r in out["rows"] if r["corpus"] == cid
                  and r["arm"] == "square" and r["k"] == k]
            if sq:
                print(f"[{cid}|k={k:2d}] square  n_frames={len(sq)} "
                      f"protos={[r['n_protos'] for r in sq]} "
                      f"mean={np.mean([r['n_protos'] for r in sq]):.2f}", flush=True)
            for kap in KAPPAS:
                bl = [r for r in out["rows"] if r["corpus"] == cid
                      and r["arm"] == "blob" and r["k"] == k and r["kappa"] == kap]
                if bl:
                    print(f"[{cid}|k={k:2d}] blob kap={kap} n_blobs={bl[0]['n_samples']} "
                          f"protos={[r['n_protos'] for r in bl]} "
                          f"mean={np.mean([r['n_protos'] for r in bl]):.2f}", flush=True)


if __name__ == "__main__":
    main()
