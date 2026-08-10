"""figadj_wellposed_measure -- does the WELL-POSEDNESS conjunct close the
speckle false-mint control, and what does it cost on real frames?

Pre-registration: VISION_FIGADJ_WELLPOSED_PREREG.md, committed a62ee54c BEFORE
any confirmatory number. Seeds 89000-89999.

Mechanical I/O + read-out ONLY. Every decision is the seed's
(`vision_border_ownership` v1.2.0): the flood, the labelling, the ownership
competition, the well-posedness hold-open and the mint are ALL rules. This
script builds fields, ticks to a fixpoint, and measures.

THREE INSTRUMENT DISCIPLINES ARE LOAD-BEARING HERE:

1. M-E, THE VACUITY GATE, RUNS FIRST (§1 fifth clause / FM-0). A conjunct that
   moves nothing is decorative and its statistics mean nothing. `D == 0`
   aborts before a seed is burned.

2. THE BASELINE IS THE INCUMBENT AT THE SAME GRAIN (G72), never the retired
   whole-frame zero. Comparing to the whole-frame figure produced a phantom 3x
   in the predecessor and a phantom "few and large" reading in the rung after
   it. All three arms are re-measured here; nothing is inherited.

3. ALL THREE ARMS RUN THROUGH THE SUBSTRATE. A read-out calibrated to one
   predicate cannot score another -- the prior rung established this, and the
   well-posedness conjunct is a third predicate, so the read-out replicates it
   explicitly and is reconciled against the rules' own minted output
   (`G_pass == n_protos`) SEPARATELY UNDER EACH ARM.
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

SEED_BLOCK = 89000

# G72, the resolution rung's recommended proto-object configuration and the
# predecessor's, reused verbatim so the comparison is at the SAME GRAIN.
GRID = 72
REGION = 18
K_MAIN = 16
SAMPLED_FRAMES = (0, 25, 50, 75, 100, 125, 149)
N_DECODE = 160
MAX_STEPS = 200

# (bown_own, bown_wp) -- the three arms of §3.
ARMS = {"incumbent": (0.0, 0.0),
        "replacement": (1.0, 0.0),
        "wellposed": (1.0, 1.0)}

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

    tally = Counter()
    sizes = []
    for lab, members in comp.items():
        sizes.append(len(members))
        if not settled:
            tally["G_settled"] += 1
            continue
        abutting = {g(m, "glabel") for f in members for m in nb[f]
                    if g(m, "bg") < 0.5 and g(m, "glabel") != lab}
        if arm == "incumbent":
            if abutting:
                tally["G_figadj"] += 1
                continue
        else:
            if any(not (rim_computed[lab] < rim_computed[q]) for q in abutting):
                tally["G_own_lost"] += 1
                continue
        if arm == "wellposed":
            # THE NEW CONJUNCT: a member cell facing TWO DISTINCT enclosed
            # rivals claims one border in two competitions at once -- |B| does
            # not cancel, the competition is ill-posed, HELD OPEN.
            ill = any(
                len({g(m, "glabel") for m in nb[f]
                     if g(m, "bg") < 0.5 and g(m, "glabel") != lab}) > 1
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

    protos = bow.protos(s)
    return {
        "n_cells": len(cells), "n_frame": n_frame, "reach": reach,
        "n_enclosed": len(enclosed), "n_components": len(comp),
        "settled": bool(settled), "rim_mismatch": rim_mismatch,
        "G_settled": tally["G_settled"], "G_figadj": tally["G_figadj"],
        "G_own_lost": tally["G_own_lost"], "G_illposed": tally["G_illposed"],
        "G_gnd2": tally["G_gnd2"], "G_pass": tally["G_pass"],
        "n_protos": len(protos),
        "n_protos_multicell": sum(1 for p in protos if p["members"] >= 2),
        "max_members": max([p["members"] for p in protos], default=0),
        "max_members_frac": (max([p["members"] for p in protos], default=0)
                             / len(cells) if cells else 0.0),
    }


def run_one(grid_vals, arm, *, clear_frame=False):
    own, wp = ARMS[arm]
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_border_ownership"])
    handle = bow.add_field(s, grid_vals)
    if clear_frame:
        for n in handle["cell_ids"]:
            s.set_attr(n, "frame", 0.0)
    bow.set_flag(s, bown=1.0, bown_own=own, bown_wp=wp)
    sweeps = bow.tick(s, max_steps=MAX_STEPS)
    return {"sweeps": sweeps, **read_out(s, handle, arm)}


def controls(log):
    """M-E FIRST (vacuity), then D1 / D2b, then M-A (the speckle control)."""
    out = {}
    g12 = [[0] * 12 for _ in range(12)]
    for r in range(3, 9):
        for c in range(4, 8):
            g12[r][c] = 1
    uni = [[3] * 12 for _ in range(12)]
    # a GENUINE single-cell figure -- the case the discriminator must NOT break
    g1 = [[0] * 12 for _ in range(12)]
    g1[6][6] = 1

    # ---- M-E: VACUITY GATE, before a seed is burned ----------------------
    vrng = np.random.RandomState(SEED_BLOCK + 800)
    dmax = 0
    for _ in range(20):
        q = vrng.randint(0, K_MAIN, (REGION, REGION)).tolist()
        dmax = max(dmax, abs(run_one(q, "replacement")["n_protos"]
                             - run_one(q, "wellposed")["n_protos"]))
    out["M_E_vacuity"] = {"D": dmax, "live": bool(dmax > 0), "n_fields": 20,
                          "seed": SEED_BLOCK + 800}
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
        # THE CONSTRAINT THAT MAKES THIS NON-TRIVIAL: a single cell that is a
        # FIGURE must still mint, while a single cell that is NOISE must not.
        one = run_one(g1, arm)
        out[f"SINGLECELL_FIGURE_{arm}"] = {
            "n_protos": one["n_protos"], "max_members": one["max_members"],
            "mints": bool(one["n_protos"] == 1 and one["max_members"] == 1)}
        log(f"[control/{arm}] D1={out[f'D1_{arm}']['reproduces']} "
            f"D2b_fired={out[f'D2b_{arm}']['fired']} "
            f"1cell_figure_mints={out[f'SINGLECELL_FIGURE_{arm}']['mints']}")

    # ---- M-A: the speckle control, FRESH seeds, all arms on SAME fields ---
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


def main():
    prov = ep.provenance_line()
    print(f"[provenance] {prov}", flush=True)

    def log(m):
        print(m, flush=True)

    ctrl = controls(log)

    for arm in ARMS:
        if not ctrl[f"D1_{arm}"]["reproduces"]:
            raise SystemExit(f"POSITIVE CONTROL DEAD ({arm}) -- nothing claimed")
    if not ctrl["D2b_wellposed"]["fired"]:
        raise SystemExit("DEAD-INSTRUMENT ARM DID NOT FIRE -- instrument blind")

    out = {"provenance": prov, "prereg": "VISION_FIGADJ_WELLPOSED_PREREG.md",
           "prereg_commit": "a62ee54c", "seed_block": SEED_BLOCK,
           "config": {"GRID": GRID, "REGION": REGION,
                      "n_tiles": len(region_origins()), "k_main": K_MAIN,
                      "sampled_frames": list(SAMPLED_FRAMES)},
           "controls": ctrl, "corpora": {}, "m_c_rows": []}

    # ---- M-C: real-frame COST, at the SAME GRAIN, all three arms ---------
    vp = _vp()
    origins = region_origins()
    for _ci, cid in ((0, "C1"), (1, "C2")):
        spec = CORPORA[cid]
        frames, meta = vp.jellyfin_frames(
            N_DECODE, every=2, start_s=300, size=GRID,
            episode_index=spec["episode_index"])
        got = str(meta["episode_id"])
        if not got.startswith(spec["pin"]):
            raise SystemExit(f"PIN MISMATCH {cid}: expected {spec['pin']}… "
                             f"got {got} -- RUN VOID")
        out["corpora"][cid] = {"what": spec["what"], "episode_id": got,
                               "n_decoded": len(frames)}
        log(f"[{cid}] {spec['what']} decoded {len(frames)} @ {GRID}x{GRID} "
            f"pin ok, {len(origins)} tiles of {REGION}x{REGION}")

        for arm in ARMS:
            for fi in SAMPLED_FRAMES:
                q = quantize(frames[fi], K_MAIN)
                agg = Counter()
                protos = multi = 0
                for r0, c0 in origins:
                    r = run_one(tile(q, r0, c0), arm)
                    for key in ("G_settled", "G_figadj", "G_own_lost",
                                "G_illposed", "G_gnd2", "G_pass",
                                "n_components", "n_enclosed", "rim_mismatch"):
                        agg[key] += r[key]
                    protos += r["n_protos"]
                    multi += r["n_protos_multicell"]
                out["m_c_rows"].append({
                    "corpus": cid, "arm": arm, "k": K_MAIN, "frame": fi,
                    "n_protos": protos, "n_protos_multicell": multi,
                    **{key: agg[key] for key in
                       ("G_settled", "G_figadj", "G_own_lost", "G_illposed",
                        "G_gnd2", "G_pass", "n_components", "n_enclosed",
                        "rim_mismatch")}})
                log(f"  [M-C {cid}|{arm[:5]}|f{fi:3d}] protos={protos} "
                    f"multi={multi} comps={agg['n_components']} "
                    f"illposed={agg['G_illposed']} pass={agg['G_pass']}")

    # aggregate + the reconciliation check, per arm
    summ = {}
    for cid in CORPORA:
        for arm in ARMS:
            rows = [r for r in out["m_c_rows"]
                    if r["corpus"] == cid and r["arm"] == arm]
            summ[f"{cid}|{arm}"] = {
                "mean_protos": float(np.mean([r["n_protos"] for r in rows])),
                "mean_multicell": float(
                    np.mean([r["n_protos_multicell"] for r in rows])),
                "reconciles": all(r["G_pass"] == r["n_protos"] for r in rows),
                "mean_components": float(
                    np.mean([r["n_components"] for r in rows])),
            }
    out["m_c_summary"] = summ

    path = os.path.join(ROOT, "results", "figadj_wellposed.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1)
    log(f"[written] {path}")
    for k, v in summ.items():
        log(f"  {k}: protos={v['mean_protos']:.1f} "
            f"multi={v['mean_multicell']:.1f} "
            f"comps={v['mean_components']:.1f} recon={v['reconciles']}")


if __name__ == "__main__":
    main()
