"""M-G -- THE NEW ARM. Does a screen/mirror composite mint as ONE object under
the containment scope, instead of shattering into its content?

Pre-registration: VISION_FIGADJ_NESTING_PREREG.md. Seeds 92000-92999.

THE STIMULI ARE REUSED VERBATIM from `scripts/surface_assignment_measure.py`
(seeds 87000-87999) -- same tile ordinal, same sides, same content arms, same
start_s, same compositing functions, imported rather than reimplemented -- so
the comparison against the predecessor is EXACT. Only the RNG ordinals move
into this rung's block (87000 is burned).

THE HONEST BOUND, DECLARED IN THE PREREG BEFORE THE RUN: there is no `Surface`
type, no calibration attribute and no containment edge in `seeds/`, and a
FEATURED screen is not a single component -- it shatters, so there is nothing
for a SURFACE proto to be minted FROM. `n_surface == 0` is therefore NOT
evidence of failed identification. This rung is not asked to identify a
surface, only to stop an enclosing region losing to its contents; the
measurable consequence inside R is the SIZE of what mints there.
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

SEED_BLOCK = 92000

GRID = 72
REGION = 18
K_MAIN = 16
TILE_ORDINAL = 5            # the predecessor's, unchanged
SIDES = (8, 14)
N_FRAMES = 100
START_S = 900               # the predecessor's material, unchanged
EVERY = 2

# the four arms; `wellposed` is the STANDING predicate and the baseline here.
ARMS = ("incumbent", "replacement", "wellposed", "nested")
CONTENT_ARMS = ("plain", "flat", "screen", "mirror", "scramble")

CORPORA = {
    "C1": {"what": "cartoon", "episode_index": 0, "pin": "08630d4b"},
    "C2": {"what": "live-action", "episode_index": 3, "pin": "119eca43"},
}


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    t0 = time.time()
    logf = open(os.path.join(ROOT, "results", "nesting_surface.log"), "w")

    def log(m):
        print(m, flush=True)
        logf.write(m + "\n")
        logf.flush()

    prov = ep.provenance_line()
    log("== PROVENANCE (printed from INSIDE the measuring process) ==")
    log(prov)
    if "WRONG ENGINE" in prov or "DIVERGED" in prov:
        raise SystemExit("ENGINE PROVENANCE FAILED -- RUN VOID")

    # the predecessor's stimulus generator and discriminator, IMPORTED
    sa = _load("sa", os.path.join(ROOT, "scripts",
                                  "surface_assignment_measure.py"))
    # this rung's four-arm driver
    fn = _load("fn", os.path.join(ROOT, "scripts",
                                  "figadj_nesting_measure.py"))
    vp = _load("vp", os.path.join(ROOT, "scripts", "video_probe_measure.py"))

    origins = fn.region_origins()
    r0, c0 = origins[TILE_ORDINAL]
    log(f"== G72: tile ordinal {TILE_ORDINAL} at ({r0},{c0}); sides {SIDES}; "
        f"n={N_FRAMES}/corpus; stimuli imported from surface_assignment_measure")

    # ---- §3.3 instrument positive control: a synthetic square must read
    #      S == R exactly, in EVERY arm. A discriminator that cannot report
    #      SURFACE would make "no SURFACE" a §1.1 dead-arm floor.
    ctrl = {}
    ok = True
    for side in SIDES:
        off = (REGION - side) // 2
        g = [[3] * REGION for _ in range(REGION)]
        for r in range(off, off + side):
            for c in range(off, off + side):
                g[r][c] = 9
        R = sa.rect_cells(off, side)
        for arm in ARMS:
            res = fn.run_one(g, arm)
            cl = sa.classify(bow_support(res, arm, g, fn), R)
            fired = cl["n_surface_exact"] == 1 and cl["n_inside"] == 0
            ok = ok and fired
            ctrl[f"s{side}|{arm}"] = {"fired_exact_S_eq_R": bool(fired), **cl}
            log(f"  [CTRL s={side:2d} {arm:11s}] S==R exactly: {fired}")
    ctrl["ALL_FIRED"] = bool(ok)
    if not ok:
        raise SystemExit("INSTRUMENT CONTROL DID NOT FIRE -- RUN VOID")

    decoded = {}
    for cid in ("C1", "C2"):
        spec = CORPORA[cid]
        frames, meta = vp.jellyfin_frames(
            N_FRAMES, every=EVERY, start_s=START_S, size=GRID,
            episode_index=spec["episode_index"])
        got = str(meta["episode_id"])
        if not got.startswith(spec["pin"]):
            raise SystemExit(f"PIN MISMATCH {cid}: got {got} -- RUN VOID")
        decoded[cid] = frames
        log(f"[{cid}] {spec['what']} decoded {len(frames)} pin {got[:8]} ok")

    n = min(len(decoded["C1"]), len(decoded["C2"]))
    out = {"provenance": prov, "prereg": "VISION_FIGADJ_NESTING_PREREG.md",
           "seed_block": [SEED_BLOCK, SEED_BLOCK + 999],
           "stimuli_from": "scripts/surface_assignment_measure.py (imported)",
           "config": {"grid": GRID, "region": REGION, "k": K_MAIN,
                      "tile_ordinal": TILE_ORDINAL, "tile_origin": [r0, c0],
                      "sides": list(SIDES), "n_frames": n,
                      "start_s": START_S, "every": EVERY},
           "instrument_control": ctrl, "rows": []}

    for ci, cid in ((0, "C1"), (1, "C2")):
        other = "C2" if cid == "C1" else "C1"
        for si, side in ((0, 8), (1, 14)):
            off = (REGION - side) // 2
            R = sa.rect_cells(off, side)
            for coi, content in ((0, "plain"), (1, "flat"), (2, "screen"),
                                 (3, "mirror"), (4, "scramble")):
                rng = np.random.RandomState(
                    SEED_BLOCK + 100 * ci + 10 * si + coi)
                per_arm = {a: [] for a in ARMS}
                for fi in range(n):
                    f, _ = sa.build_stimulus(
                        decoded[cid][fi], decoded[other][fi],
                        r0, c0, off, side, content, rng)
                    q = fn.quantize(f, K_MAIN)
                    t = fn.tile(q, r0, c0)
                    for arm in ARMS:
                        res = fn.run_one(t, arm)
                        sup = bow_support(res, arm, t, fn)
                        cl = sa.classify(sup, R)
                        inR = [len(v) for k, v in sup.items()
                               if {tuple(x) for x in v} <= R]
                        per_arm[arm].append({
                            "n_protos": res["n_protos"],
                            "settled": res["settled"],
                            "sizes_in_R": inR, **cl,
                            "verdict": sa.verdict(cl)})
                for arm in ARMS:
                    rows = per_arm[arm]
                    vs = [r_["verdict"] for r_ in rows]
                    inR = [x for r_ in rows for x in r_["sizes_in_R"]]
                    out["rows"].append({
                        "corpus": cid, "side": side, "content": content,
                        "arm": arm, "n": len(rows),
                        "verdicts": {v: vs.count(v) for v in
                                     ("REFUSE", "SURFACE",
                                      "CONTENT_IN_SCENE", "SPILL_ONLY")},
                        "mean_n_inside": float(np.mean(
                            [r_["n_inside"] for r_ in rows])),
                        "mean_n_surface": float(np.mean(
                            [r_["n_surface"] for r_ in rows])),
                        "n_surface_exact": int(sum(
                            r_["n_surface_exact"] for r_ in rows)),
                        "mean_n_protos": float(np.mean(
                            [r_["n_protos"] for r_ in rows])),
                        "all_settled": bool(all(r_["settled"] for r_ in rows)),
                        # M-F inside R: the size of what mints there
                        "size_in_R": fn.dist(inR),
                        "hist_in_R": {str(k): int(v) for k, v in
                                      sorted(Counter(inR).items())},
                        "per_frame_n_inside": [r_["n_inside"] for r_ in rows],
                    })
                    log(f"  [{cid} s{side} {content:8s} {arm:11s}] "
                        f"SURF={vs.count('SURFACE')} "
                        f"inside={np.mean([r_['n_inside'] for r_ in rows]):.2f} "
                        f"med_size_in_R={fn.dist(inR)['median']}")

    out["elapsed_s"] = time.time() - t0
    path = os.path.join(ROOT, "results", "nesting_surface.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1)
    log(f"[written] {path}")


def bow_support(res, arm, grid, fn):
    """Re-run and read the proto SUPPORT (root -> member coords). The driver
    returns aggregates; the surface discriminator needs the member sets, so
    this asks the graph for them. Mechanical query, no decision."""
    from domains import border_ownership_world as bow_
    from substrate.boot_core import boot_core, load_seeds_into
    own, wp, nest = fn.ARMS[arm]
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_border_ownership"])
    h = bow_.add_field(s, grid)
    bow_.set_flag(s, bown=1.0, bown_own=own, bown_wp=wp, bown_nest=nest)
    bow_.tick(s, max_steps=fn.MAX_STEPS)
    idx = h["index"]
    rc = {idx[(r, c)]: (r, c) for r in range(h["H"]) for c in range(h["W"])}
    sup = {}
    for n in rc:
        a = s.node(n)["attrs"]
        if float(a.get("bg", 0.0)) < 0.5:
            sup.setdefault(float(a.get("glabel", -1)), []).append(rc[n])
    minted = {float(p.get("root_glabel", p.get("root", -1)))
              for p in bow_.protos(s)}
    return {k: v for k, v in sup.items() if k in minted} if minted else {}


if __name__ == "__main__":
    main()
