"""peer_competition_measure -- PRICE THE PEER COMPETITION, WITH NO MECHANISM.

Pre-registration: VISION_PEER_COMPETITION_PREREG.md (committed 1a02db00).
Seeds 96000-96999. Declared draws: 96700 (speckle), 96701 (reserved).

The containment rung measured that 17/17 enclosing components are refused by
`G_own_lost` against a PEER, and named "price the peer competition" as the next
lever. This script prices it and BUILDS NOTHING: every arm is the standing
seed's own committed flags, and the two counterfactuals (P5) are ablations OF
THE READ-OUT ONLY -- no rule, no flag, no seed byte moves.

FOUR DISCIPLINES ARE LOAD-BEARING:

1. THE READ-OUT IS RECONCILED AGAINST THE RULES' OWN OUTPUT (`G_pass ==
   n_protos`) UNDER EVERY ARM before any classification is believed -- else the
   decomposition measures this Python, not the graph.

2. `rim` IS RECOMPUTED AND CHECKED AGAINST THE ATTRIBUTE THE RULE WROTE. The
   whole competition turns on `rim`; a diagnostic must not be computed by the
   component it checks.

3. THE ABLATIONS MUST BE LIVE. If NO-PEER does not change the pass count on
   real tiles, the instrument is decorative and the run stops (s1 fifth clause,
   FM-0) -- the containment rung's own stopping rule, kept.

4. PROVENANCE IS PRINTED FROM INSIDE THIS PROCESS and the run aborts on
   divergence.

THE CEILING ARGUMENT THIS SCRIPT EXISTS TO TEST: minting is a SELECTION over
enclosed components. No predicate over components can mint an object larger
than the largest component present. So the component-size distribution (P1) is
an UPPER BOUND on the proto-size distribution, and if it is already fragments,
no peer mechanism can deliver few-and-large.
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

# ---- declared seeds (PREREG s6); real tiles consume no RNG ---------------
SEED_SPECKLE = 96700

# G72 -- both predecessors' configuration, verbatim.
GRID = 72
REGION = 18
K_MAIN = 16
SAMPLED_FRAMES = (0, 25, 50, 75, 100, 125, 149)
N_DECODE = 160
MAX_STEPS = 200

# (bown_own, bown_wp, bown_nest) -- the seed's own committed flags.
ARMS = {"incumbent":   (0.0, 0.0, 0.0),
        "replacement": (1.0, 0.0, 0.0),
        "wellposed":   (1.0, 1.0, 0.0),
        "nested":      (1.0, 1.0, 1.0)}
PRIMARY = "wellposed"

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


def dist(xs):
    if not xs:
        return {"n": 0, "median": None, "mean": None, "p90": None, "max": None}
    a = np.asarray(xs, float)
    return {"n": int(a.size), "median": float(np.median(a)),
            "mean": float(a.mean()), "p90": float(np.percentile(a, 90)),
            "max": float(a.max())}


def read_out(s, handle, arm):
    """Replicates the ARMED rule's gates IN THE ORDER the rule evaluates them,
    and additionally classifies WHY each `G_own_lost` refusal happened and what
    two mechanism-free ablations of that one gate would pass (PREREG s2 P4/P5).
    """
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

    # DISCIPLINE 2: rim recomputed from the settled graph, checked against the
    # attribute the RULE wrote. The competition turns entirely on this number.
    rim_computed = {
        lab: sum(1 for f in members
                 if any(g(m, "glabel") != lab for m in nb[f]))
        for lab, members in comp.items()}
    rim_mismatch = sum(
        1 for lab, members in comp.items() for f in members
        if int(round(g(f, "rim"))) != rim_computed[lab])

    def contained_in(qlab, lab):
        return not any(
            any(g(p, "glabel") != qlab and g(p, "glabel") != lab
                for p in nb[c])
            for c in comp[qlab])

    def ground_ok(lab, members):
        glabels = {g(gc, "glabel") for gc in cells
                   if g(gc, "bg") > 0.5
                   and any(g(f, "bg") < 0.5 and g(f, "glabel") == lab
                           for f in nb[gc])}
        return len(glabels) <= 1

    def illposed(lab, members, rivals):
        return any(
            len({g(m, "glabel") for m in nb[f]
                 if g(m, "bg") < 0.5 and g(m, "glabel") != lab
                 and g(m, "glabel") in rivals}) > 1
            for f in members)

    def downstream(lab, members, rivals):
        """Every gate AFTER the ownership competition, unchanged."""
        if arm in ("wellposed", "nested") and illposed(lab, members, rivals):
            return None
        if not ground_ok(lab, members):
            return None
        return len(members)

    tally = Counter()
    # P1/P2/P3/P4/P5/P6 accumulators -------------------------------------
    comp_sizes = []
    peer_counts = []
    peer_counts_refused = []
    rims = []
    refuse_tie_only = 0
    refuse_strict = 0
    margins = []                 # min_rival rim(Q) - rim(R), <= 0 for blocks
    blocker_size_ratio = []      # size(R) / size(smallest-rim blocker)
    # ablation pass sets (sizes of what passes)
    pass_sizes = []
    pass_sizes_ties = []
    pass_sizes_nopeer = []
    n_pass_ties = 0
    n_pass_nopeer = 0
    # P6
    largest_lab = None
    largest_sz = -1

    for lab, members in comp.items():
        comp_sizes.append(len(members))
        if len(members) > largest_sz:
            largest_sz, largest_lab = len(members), lab

    for lab, members in comp.items():
        if not settled:
            tally["G_settled"] += 1
            continue
        raw = {g(m, "glabel") for f in members for m in nb[f]
               if g(m, "bg") < 0.5 and g(m, "glabel") != lab}
        if arm == "nested":
            rivals = {q for q in raw if not contained_in(q, lab)}
        else:
            rivals = raw
        peer_counts.append(len(rivals))
        rims.append(rim_computed[lab])

        # ---- the three readings of the ONE gate --------------------------
        blockers = [q for q in rivals
                    if not (rim_computed[lab] < rim_computed[q])]
        lost = bool(blockers)
        lost_ties_allowed = any(rim_computed[q] < rim_computed[lab]
                                for q in rivals)

        if arm == "incumbent":
            # the incumbent vetoes on CONTACT; the ablations are defined
            # against the ownership arms only, so it is measured but its
            # ablation columns are left at the incumbent's own verdict.
            if rivals:
                tally["G_figadj"] += 1
                continue
            sz = downstream(lab, members, rivals)
            if sz is None:
                tally["G_gnd2_or_ill"] += 1
                continue
            tally["G_pass"] += 1
            pass_sizes.append(sz)
            pass_sizes_ties.append(sz)
            pass_sizes_nopeer.append(sz)
            n_pass_ties += 1
            n_pass_nopeer += 1
            continue

        # --- ABLATION A: TIES-ALLOWED (refuse only on a strict loss) ------
        if not lost_ties_allowed:
            sz = downstream(lab, members, rivals)
            if sz is not None:
                n_pass_ties += 1
                pass_sizes_ties.append(sz)
        # --- ABLATION B: NO-PEER (the gate never refuses) -----------------
        sz = downstream(lab, members, rivals)
        if sz is not None:
            n_pass_nopeer += 1
            pass_sizes_nopeer.append(sz)

        # --- the ARMED rule, unchanged ------------------------------------
        if lost:
            tally["G_own_lost"] += 1
            peer_counts_refused.append(len(rivals))
            if all(rim_computed[q] == rim_computed[lab] for q in blockers):
                refuse_tie_only += 1
            else:
                refuse_strict += 1
            mn = min(rim_computed[q] for q in rivals) if rivals else None
            if mn is not None:
                margins.append(mn - rim_computed[lab])
                small = min(blockers, key=lambda q: rim_computed[q])
                blocker_size_ratio.append(len(members) / max(1, len(comp[small])))
            continue
        if arm in ("wellposed", "nested") and illposed(lab, members, rivals):
            tally["G_illposed"] += 1
            continue
        if not ground_ok(lab, members):
            tally["G_gnd2"] += 1
            continue
        tally["G_pass"] += 1
        pass_sizes.append(len(members))

    # ---- P6: the component that SHOULD win ------------------------------
    p6 = None
    if settled and largest_lab is not None:
        lab, members = largest_lab, comp[largest_lab]
        raw = {g(m, "glabel") for f in members for m in nb[f]
               if g(m, "bg") < 0.5 and g(m, "glabel") != lab}
        rivals = ({q for q in raw if not contained_in(q, lab)}
                  if arm == "nested" else raw)
        blockers = [q for q in rivals
                    if not (rim_computed[lab] < rim_computed[q])]
        if arm == "incumbent":
            gate = "G_figadj" if rivals else (
                "G_pass" if downstream(lab, members, rivals) is not None
                else "G_gnd2_or_ill")
        elif blockers:
            gate = "G_own_lost"
        elif arm in ("wellposed", "nested") and illposed(lab, members, rivals):
            gate = "G_illposed"
        elif not ground_ok(lab, members):
            gate = "G_gnd2"
        else:
            gate = "G_pass"
        p6 = {"size": len(members), "size_frac": len(members) / len(cells),
              "rim": rim_computed[lab], "n_rivals": len(rivals),
              "n_blockers": len(blockers), "gate": gate,
              "blocker_sizes": sorted(len(comp[q]) for q in blockers)[:8],
              "blocker_rims": sorted(rim_computed[q] for q in blockers)[:8]}

    protos = bow.protos(s)
    sizes = [p["members"] for p in protos]
    nest_pairs = sum(1 for a in comp for b in comp
                     if a != b and contained_in(b, a)) if settled else 0
    return {
        "n_cells": len(cells), "n_frame": n_frame, "reach": reach,
        "n_enclosed": len(enclosed), "n_components": len(comp),
        "settled": bool(settled), "rim_mismatch": rim_mismatch,
        "n_nested_pairs": nest_pairs,
        "G_settled": tally["G_settled"], "G_figadj": tally["G_figadj"],
        "G_own_lost": tally["G_own_lost"], "G_illposed": tally["G_illposed"],
        "G_gnd2": tally["G_gnd2"], "G_pass": tally["G_pass"],
        "G_gnd2_or_ill": tally["G_gnd2_or_ill"],
        "n_protos": len(protos), "proto_sizes": sizes,
        "n_protos_multicell": sum(1 for x in sizes if x >= 2),
        "max_members": max(sizes, default=0),
        # ---- the diagnostic payload ----
        "comp_sizes": comp_sizes,
        "peer_counts": peer_counts,
        "peer_counts_refused": peer_counts_refused,
        "rims": rims,
        "refuse_tie_only": refuse_tie_only,
        "refuse_strict": refuse_strict,
        "margins": margins,
        "blocker_size_ratio": blocker_size_ratio,
        "n_pass_ties": n_pass_ties, "n_pass_nopeer": n_pass_nopeer,
        "pass_sizes": pass_sizes, "pass_sizes_ties": pass_sizes_ties,
        "pass_sizes_nopeer": pass_sizes_nopeer,
        "p6": p6,
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


def floors(log):
    """PREREG s3.4 -- every floor re-earned IN THIS TREE, nothing inherited."""
    out = {}
    g12 = [[0] * 12 for _ in range(12)]
    for r in range(3, 9):
        for c in range(4, 8):
            g12[r][c] = 1
    uni = [[3] * 12 for _ in range(12)]
    g1 = [[0] * 12 for _ in range(12)]           # a GENUINE 1-cell figure
    g1[6][6] = 1

    for arm in ARMS:
        d1 = run_one(g12, arm)
        out[f"D1_{arm}"] = {
            "n_protos": d1["n_protos"], "max_members": d1["max_members"],
            "reproduces": bool(d1["n_protos"] == 1 and d1["max_members"] == 24)}
        d2b = run_one(uni, arm, clear_frame=True)
        out[f"D2b_{arm}"] = {
            "n_protos": d2b["n_protos"], "n_frame": d2b["n_frame"],
            "reach": d2b["reach"],
            "fired": bool(d2b["n_frame"] == 0 and d2b["reach"] == 0
                          and d2b["n_protos"] > 0)}
        one = run_one(g1, arm)
        out[f"SINGLECELL_FIGURE_{arm}"] = {
            "n_protos": one["n_protos"], "max_members": one["max_members"],
            "mints": bool(one["n_protos"] == 1 and one["max_members"] == 1)}
        log(f"[floor/{arm}] D1={out[f'D1_{arm}']['reproduces']} "
            f"D2b_fired={out[f'D2b_{arm}']['fired']} "
            f"1cell_figure_mints={out[f'SINGLECELL_FIGURE_{arm}']['mints']}")

    nrng = np.random.RandomState(SEED_SPECKLE)
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
            "CONTROL_PASSES": hits[arm] == 0, "seed": SEED_SPECKLE}
        log(f"[speckle/{arm}] minting {hits[arm]}/100 "
            f"max_false_size={max(msize[arm], default=0)}")
    return out


def main():
    t0 = time.time()
    prov = ep.provenance_line()
    logf = open(os.path.join(ROOT, "results", "peer_competition.log"), "w")

    def log(m):
        print(m, flush=True)
        logf.write(m + "\n")
        logf.flush()

    log("== PROVENANCE (printed from INSIDE the measuring process) ==")
    log(prov)
    if "WRONG ENGINE" in prov or "DIVERGED" in prov:
        raise SystemExit("ENGINE PROVENANCE FAILED -- RUN VOID")

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

    ctrl = floors(log)
    for arm in ARMS:
        if not ctrl[f"D1_{arm}"]["reproduces"]:
            raise SystemExit(f"POSITIVE CONTROL DEAD ({arm}) -- nothing claimed")
    if not ctrl["D2b_nested"]["fired"]:
        raise SystemExit("DEAD-INSTRUMENT ARM DID NOT FIRE -- instrument blind")

    out = {"provenance": prov, "prereg": "VISION_PEER_COMPETITION_PREREG.md",
           "seed_block": [96000, 96999],
           "config": {"GRID": GRID, "REGION": REGION, "k_main": K_MAIN,
                      "n_tiles_per_frame": len(origins),
                      "sampled_frames": list(SAMPLED_FRAMES),
                      "n_tiles_total": 2 * len(SAMPLED_FRAMES) * len(origins)},
           "floors": ctrl,
           "corpora": {cid: {"what": CORPORA[cid]["what"],
                             "episode_id": decoded[cid][1]}
                       for cid in CORPORA},
           "rows": []}

    for cid in ("C1", "C2"):
        frames = decoded[cid][0]
        for arm in ARMS:
            for fi in SAMPLED_FRAMES:
                q = quantize(frames[fi], K_MAIN)
                agg = Counter()
                acc = {k: [] for k in
                       ("comp_sizes", "peer_counts", "peer_counts_refused",
                        "rims", "margins", "blocker_size_ratio",
                        "proto_sizes", "pass_sizes", "pass_sizes_ties",
                        "pass_sizes_nopeer")}
                p6s = []
                for r0, c0 in origins:
                    r = run_one(tile(q, r0, c0), arm)
                    for key in ("G_settled", "G_figadj", "G_own_lost",
                                "G_illposed", "G_gnd2", "G_pass",
                                "G_gnd2_or_ill", "n_components", "n_enclosed",
                                "rim_mismatch", "n_nested_pairs",
                                "refuse_tie_only", "refuse_strict",
                                "n_pass_ties", "n_pass_nopeer", "n_protos",
                                "n_protos_multicell"):
                        agg[key] += r[key]
                    for key in acc:
                        acc[key].extend(r[key])
                    if r["p6"] is not None:
                        p6s.append(r["p6"])
                out["rows"].append({
                    "corpus": cid, "arm": arm, "frame": fi,
                    **{k: agg[k] for k in
                       ("G_settled", "G_figadj", "G_own_lost", "G_illposed",
                        "G_gnd2", "G_pass", "G_gnd2_or_ill", "n_components",
                        "n_enclosed", "rim_mismatch", "n_nested_pairs",
                        "refuse_tie_only", "refuse_strict", "n_pass_ties",
                        "n_pass_nopeer", "n_protos", "n_protos_multicell")},
                    **{k: acc[k] for k in acc},
                    "p6": p6s,
                })
                log(f"  [{cid}|{arm[:5]}|f{fi:3d}] protos={agg['n_protos']} "
                    f"comps={agg['n_components']} "
                    f"own_lost={agg['G_own_lost']} "
                    f"(tie={agg['refuse_tie_only']} "
                    f"strict={agg['refuse_strict']}) "
                    f"pass={agg['G_pass']} ties_abl={agg['n_pass_ties']} "
                    f"nopeer_abl={agg['n_pass_nopeer']} "
                    f"med_comp={np.median(acc['comp_sizes']) if acc['comp_sizes'] else 0} "
                    f"rimmis={agg['rim_mismatch']}")

    # ---- summary --------------------------------------------------------
    summ = {}
    for cid in CORPORA:
        for arm in ARMS:
            rows = [r for r in out["rows"]
                    if r["corpus"] == cid and r["arm"] == arm]
            cat = lambda k: [x for r in rows for x in r[k]]   # noqa: E731
            p6 = [x for r in rows for x in r["p6"]]
            n_own = sum(r["G_own_lost"] for r in rows)
            summ[f"{cid}|{arm}"] = {
                "mean_protos": float(np.mean([r["n_protos"] for r in rows])),
                "reconciles": all(r["G_pass"] == r["n_protos"] for r in rows),
                "rim_mismatch_total": sum(r["rim_mismatch"] for r in rows),
                "mean_components": float(
                    np.mean([r["n_components"] for r in rows])),
                # P1 -- THE CEILING
                "P1_component_sizes": dist(cat("comp_sizes")),
                "P1_max_comp_frac": (max(cat("comp_sizes"), default=0) / 324.0),
                # P2
                "P2_peer_counts": dist(cat("peer_counts")),
                "P2_peer_counts_refused": dist(cat("peer_counts_refused")),
                # P3
                "P3_rims": dist(cat("rims")),
                # P4
                "P4_n_own_lost": n_own,
                "P4_tie_only": sum(r["refuse_tie_only"] for r in rows),
                "P4_strict": sum(r["refuse_strict"] for r in rows),
                "P4_margins": dist(cat("margins")),
                "P4_margin_hist": {str(k): int(v) for k, v in
                                   sorted(Counter(cat("margins")).items())},
                "P4_blocker_size_ratio": dist(cat("blocker_size_ratio")),
                # P5 -- THE DECISION STATISTIC
                "P5_pass_armed": sum(r["G_pass"] for r in rows),
                "P5_pass_ties": sum(r["n_pass_ties"] for r in rows),
                "P5_pass_nopeer": sum(r["n_pass_nopeer"] for r in rows),
                "P5_sizes_armed": dist(cat("pass_sizes")),
                "P5_sizes_ties": dist(cat("pass_sizes_ties")),
                "P5_sizes_nopeer": dist(cat("pass_sizes_nopeer")),
                "P5_hist_nopeer": {str(k): int(v) for k, v in
                                   sorted(Counter(cat("pass_sizes_nopeer")).items())},
                "P5_LIVE": bool(sum(r["n_pass_nopeer"] for r in rows)
                                != sum(r["G_pass"] for r in rows)),
                # P6
                "P6_n_tiles": len(p6),
                "P6_largest_passes": sum(1 for x in p6 if x["gate"] == "G_pass"),
                "P6_gate_hist": {k: int(v) for k, v in
                                 Counter(x["gate"] for x in p6).items()},
                "P6_largest_size": dist([x["size"] for x in p6]),
                "P6_largest_frac": dist([x["size_frac"] for x in p6]),
                "P6_blocker_min_size": dist(
                    [min(x["blocker_sizes"]) for x in p6 if x["blocker_sizes"]]),
                # proto size distribution, reported beside every count
                "proto_sizes": dist(cat("proto_sizes")),
            }
    out["summary"] = summ
    out["elapsed_s"] = time.time() - t0

    path = os.path.join(ROOT, "results", "peer_competition.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1)
    log(f"[written] {path}")
    for k, v in summ.items():
        log(f"  {k}: protos={v['mean_protos']:.1f} recon={v['reconciles']} "
            f"rimmis={v['rim_mismatch_total']} "
            f"COMP med={v['P1_component_sizes']['median']} "
            f"p90={v['P1_component_sizes']['p90']} "
            f"max={v['P1_component_sizes']['max']} "
            f"(maxfrac={v['P1_max_comp_frac']:.3f}) | "
            f"peers med={v['P2_peer_counts']['median']} | "
            f"own_lost={v['P4_n_own_lost']} tie={v['P4_tie_only']} "
            f"strict={v['P4_strict']} | "
            f"PASS armed={v['P5_pass_armed']} ties={v['P5_pass_ties']} "
            f"nopeer={v['P5_pass_nopeer']} LIVE={v['P5_LIVE']} | "
            f"SIZE armed_med={v['P5_sizes_armed']['median']} "
            f"nopeer_med={v['P5_sizes_nopeer']['median']} "
            f"nopeer_max={v['P5_sizes_nopeer']['max']} | "
            f"P6 largest_passes={v['P6_largest_passes']}/{v['P6_n_tiles']}")


if __name__ == "__main__":
    main()
