#!/usr/bin/env python3
"""COLOUR IDENTITY'S REFUSAL BOUND — the PACKING RADIUS of the minted codebook
(confirmatory run).

Pre-registration: VISION_COLOUR_BOUND_PREREG.md (committed BEFORE this run, §3).

L1b (VISION_UNIQUENESS_RESULTS.md) found `ci_assign` to be the worst case in its
audit table: an `Argmin` over `ColourCategory` with ZERO `Lte` — no admission bound
at all, so a probe at opponent distance 269.52 is confidently assigned and the
equidistant probe is decided by a margin of exactly 0.0000. This rung adds a refusal
bound derived as the codebook's PACKING RADIUS (half the minimum inter-prototype
distance — the radius at which the codebook's own quanta do not overlap), flag-gated
OFF by default, and MEASURES the delta to the two landed rungs that depend on colour
identity.

The bound is decided ENTIRELY by the seed rules (`ci_assign`'s added disjunct and the
new `ci_refuse`). This runner only CONSTRUCTS stimuli, READS attributes back, and
TALLIES over them (mechanical I/O, §0). The packing-radius predicate recomputed here
in `_packing_admits` is an INDEPENDENT re-derivation used to MEASURE the graph's
decision pointwise (arm E) — it is never fed back into the graph.

Run from the gamma-substrate dir:
    python scripts/colour_bound_measure.py
"""
from __future__ import annotations
import json
import math
import os
import random
import time

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

import domains.seed_registry  # noqa: E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains import colour_bound_world as cbw  # noqa: E402

# The landed rung's own stimuli, imported so the scenes are byte-for-byte identical.
# Package-qualified so it resolves BOTH under pytest (root on sys.path) and as a
# direct script run with PYTHONPATH=.
from scripts import colour_identity_measure as cim  # noqa: E402

A, B, C = cim.A, cim.B, cim.C          # A(10,0)  B(-10,0)  C(0,12)

# L1b's two exposing probes, verbatim from scripts/uniqueness_measure.py.
FAR_PROBE = dict(cL=200, cM=5, cS=9)          # obs (195, -196), dist 269.5199
EQUI_PROBE = dict(cL=10, cM=10, cS=20)        # obs (0, 0), both (+-10,0) at 10.0
# Colour identity's landed off-prototype probe (its arm A(b)): obs (6,0) -> (10,0) @4.
OFF_PROTO_PROBE = dict(cL=13, cM=7, cS=20)    # crg = 13-7 = 6, cby = 20-20 = 0

SEEDS_BOUNDARY = range(50000, 50100)          # arm E (pre-registered)
SEEDS_NOISE = range(50100, 50200)             # arm F (pre-registered)


def _boot():
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_colour_identity"])
    return s, ag


def _three_cluster_scene(*, bound: float):
    """The landed E scene: 36 cells, 3 colour clusters of 12 -> 3 category quanta."""
    s, ag = _boot()
    h = cbw.add_field(s, cells=cim._grid([A] * 12 + [B] * 12 + [C] * 12))
    cbw.set_flags(s, identity=1.0, bound=bound)
    cbw.tick(s)
    return s, h


def _probe(s, h, spec, *, bound: float):
    """Add ONE probe region to a settled scene, re-tick, return its raw readout."""
    n = cbw.add_region(s, h, dict(**spec, rrow=9, rcol=0))
    cbw.set_flags(s, identity=1.0, bound=bound)
    cbw.tick(s)
    return cbw.probe_readout(s, n)


# --- the packing-radius predicate, re-derived INDEPENDENTLY (arm E only) --------
def _packing_admits(obs, cats):
    """admit iff 2*dist(obs, winner) <= min_{c != winner} dist(winner, c).

    Recomputed here in plain Python to MEASURE the graph's decision pointwise. At
    k=1 there is no other prototype, the packing radius is undefined, and the
    predicate admits (matching the seed's Not(Exists) absence-tolerance)."""
    winner = min(cats, key=lambda c: (math.dist(obs, c), c))
    d_win = math.dist(obs, winner)
    others = [c for c in cats if c != winner]
    gap = min((math.dist(winner, o) for o in others), default=None)
    return True if gap is None else (2.0 * d_win <= gap)


def _packing_radius(cats):
    """Reported for the record: r_i for each prototype (None at k=1)."""
    out = {}
    for c in cats:
        others = [o for o in cats if o != c]
        g = min((math.dist(c, o) for o in others), default=None)
        out[str(c)] = None if g is None else round(g / 2.0, 4)
    return out


def _cat_coords(s):
    return [(c["crg"], c["cby"]) for c in cbw.categories(s)]


# ---- A: DEFECT_REPRODUCED (flag OFF — the premise) ----------------------------
def arm_A():
    out = {}
    for label, spec in [("far", FAR_PROBE), ("equidistant", EQUI_PROBE)]:
        s, h = _three_cluster_scene(bound=0.0)
        cats = _cat_coords(s)
        r = _probe(s, h, spec, bound=0.0)
        d = sorted(math.dist((r["crg"], r["cby"]), c) for c in cats)
        out[label] = {**r, "winner_dist": round(d[0], 4),
                      "runnerup_dist": round(d[1], 4),
                      "margin": round(d[1] - d[0], 6),
                      "assigned": int(r["sign_dist"] >= 0.0),
                      "refused": int(r["ci_refused"] > 0.5)}
    ok = (out["far"]["assigned"] == 1 and out["far"]["refused"] == 0
          and abs(out["far"]["sign_dist"] - 269.5199) < 1e-3
          and out["equidistant"]["assigned"] == 1
          and abs(out["equidistant"]["sign_dist"] - 10.0) < 1e-9
          and out["equidistant"]["margin"] == 0.0)
    return {"probes": out, "PASS": bool(ok)}


# ---- B: BOUND_REFUSES (flag ON) -----------------------------------------------
def arm_B():
    s, h = _three_cluster_scene(bound=1.0)
    cats = _cat_coords(s)
    r = _probe(s, h, FAR_PROBE, bound=1.0)
    ok = (r["ci_refused"] > 0.5 and r["sign_dist"] == -1.0)
    return {"categories": cats, "packing_radius": _packing_radius(cats),
            "far_probe": r, "PASS": bool(ok)}


# ---- C: NO_REGRESSION (THE CONJUNCTION) ---------------------------------------
def arm_C():
    # (a) the 36-cell E scene: every cell still assigned at dist 0, none refused.
    s, h = _three_cluster_scene(bound=1.0)
    cats = _cat_coords(s)
    dists = cbw.read_attr(s, h, "sign_dist")
    refs = cbw.refusals(s, h)
    n_assigned = sum(1 for d in dists if d >= 0.0)
    n_refused = sum(1 for x in refs if x > 0.5)
    all_zero = all(abs(d) < 1e-9 for d in dists)
    a_ok = (n_assigned == 36 and n_refused == 0 and all_zero
            and cim._all_signs_correct(s, h))

    # (b) THE DISCRIMINATING PROBE — colour identity's landed arm A(b): the
    #     off-prototype colour at (6,0) must STILL be assigned to (10,0) at dist 4.
    #     Bound is 7.8102, so this sits 3.81 INSIDE the risk region: the exact-extent
    #     bound (0), the lattice-step bound (1.0), the Times a/b trap (1.0) and a
    #     refuse-everything build ALL fail here.
    s2, h2 = _three_cluster_scene(bound=1.0)
    rb = _probe(s2, h2, OFF_PROTO_PROBE, bound=1.0)
    b_ok = (rb["ci_refused"] == 0.0 and abs(rb["sign_dist"] - 4.0) < 1e-9
            and rb["sign_rg"] == 10.0 and rb["sign_by"] == 0.0)

    # (c) a NEW instance of a SEEN colour is still recognized, not re-minted.
    s3, h3 = _three_cluster_scene(bound=1.0)
    k_before = cbw.n_categories(s3)
    rc = _probe(s3, h3, A, bound=1.0)
    k_after = cbw.n_categories(s3)
    c_ok = (rc["ci_refused"] == 0.0 and abs(rc["sign_dist"]) < 1e-9
            and k_before == k_after == 3)

    return {"a_field": {"n_assigned": n_assigned, "n_refused": n_refused,
                        "all_dist_zero": bool(all_zero), "PASS": bool(a_ok)},
            "b_off_prototype": {**rb, "packing_radius": _packing_radius(cats),
                                "PASS": bool(b_ok)},
            "c_recognize_not_remint": {**rc, "n_cats_before": k_before,
                                       "n_cats_after": k_after, "PASS": bool(c_ok)},
            "PASS": bool(a_ok and b_ok and c_ok)}


# ---- D: AMBIGUITY (the 0.0000-margin case) ------------------------------------
def arm_D():
    s, h = _three_cluster_scene(bound=1.0)
    cats = _cat_coords(s)
    r = _probe(s, h, EQUI_PROBE, bound=1.0)
    obs = (r["crg"], r["cby"])
    d = sorted(math.dist(obs, c) for c in cats)
    # Tie-independence: BOTH tied candidates lie outside their packing balls, so the
    # Argmin's arbitrary choice cannot change the verdict.
    tied = [c for c in cats if abs(math.dist(obs, c) - d[0]) < 1e-9]
    radii = _packing_radius(cats)
    tie_independent = all(d[0] > radii[str(c)] for c in tied)
    ok = (r["ci_refused"] > 0.5 and r["sign_dist"] == -1.0
          and round(d[1] - d[0], 6) == 0.0 and tie_independent)
    return {"probe": r, "winner_dist": round(d[0], 4),
            "margin": round(d[1] - d[0], 6), "n_tied": len(tied),
            "packing_radius": radii, "tie_independent": bool(tie_independent),
            "PASS": bool(ok)}


# ---- E: BOUNDARY_EXACT (n=100, seeds 50000-50099) -----------------------------
def arm_E():
    s, h = _three_cluster_scene(bound=1.0)
    cats = _cat_coords(s)
    disagreements, n_admit, n_refuse, rows = 0, 0, 0, []
    for sd in SEEDS_BOUNDARY:
        rng = random.Random(sd)
        spec = dict(cL=rng.randint(0, 60), cM=rng.randint(0, 60),
                    cS=rng.randint(0, 60))
        r = _probe(s, h, spec, bound=1.0)
        graph_admits = (r["ci_refused"] < 0.5)
        derived = _packing_admits((r["crg"], r["cby"]), cats)
        disagreements += int(graph_admits != derived)
        n_admit += int(graph_admits)
        n_refuse += int(not graph_admits)
        rows.append({"seed": sd, "obs": [r["crg"], r["cby"]],
                     "graph_admits": int(graph_admits), "derived": int(derived)})
    ok = (disagreements == 0 and n_admit >= 1 and n_refuse >= 1)
    return {"n": len(rows), "disagreements": disagreements,
            "n_admitted": n_admit, "n_refused": n_refuse,
            "seeds": [SEEDS_BOUNDARY.start, SEEDS_BOUNDARY.stop - 1],
            "rows": rows, "PASS": bool(ok)}


# ---- F: NOISE_FLOOR (n=100, seeds 50100-50199) --------------------------------
def arm_F():
    minted, signed = 0, 0
    for sd in SEEDS_NOISE:
        rng = random.Random(sd)
        s, ag = _boot()
        cells = cim._grid([dict(cL=rng.randint(0, 99), cM=rng.randint(0, 99),
                                cS=rng.randint(0, 99)) for _ in range(36)])
        h = cbw.add_field(s, cells=cells)
        cbw.set_flags(s, identity=1.0, bound=1.0)
        cbw.tick(s)
        minted += int(cbw.n_categories(s) > 0)
        signed += int(any(d >= 0.0 for d in cbw.read_attr(s, h, "sign_dist")))
    ok = (minted == 0 and signed == 0)
    return {"n": len(SEEDS_NOISE), "fields_minting": minted,
            "fields_with_signs": signed,
            "seeds": [SEEDS_NOISE.start, SEEDS_NOISE.stop - 1], "PASS": bool(ok)}


# ---- X: OFFDAY (§9) -----------------------------------------------------------
def arm_X():
    s, h = _three_cluster_scene(bound=0.0)
    r = _probe(s, h, FAR_PROBE, bound=0.0)
    max_ref = max(cbw.refusals(s, h))
    ok = (max_ref == 0.0 and r["ci_refused"] == 0.0
          and r["ci_refused_dist"] == -1.0 and r["sign_dist"] > 0.0)
    return {"max_ci_refused": max_ref, "far_probe": r, "PASS": bool(ok)}


# ---- DELTA_ON: what changes in the LANDED rungs when the flag is ON ------------
def delta_on():
    """Re-run the landed scenes with bound OFF and ON; report EVERY changed number.

    REPORTED, NOT GATED (§9 measurement). Covers colour identity's own scenes and
    achromatopsia's, including the k=1 scenes where the packing radius is undefined.
    """
    def scene_stats(cells, *, achrom=0.0, bound):
        s, ag = _boot()
        h = cbw.add_field(s, cells=cells)
        cbw.set_flags(s, identity=1.0, achromatopsia=achrom, bound=bound)
        cbw.tick(s)
        dists = cbw.read_attr(s, h, "sign_dist")
        return {"n_categories": cbw.n_categories(s),
                "categories": cbw.categories(s),
                "n_assigned": sum(1 for d in dists if d >= 0.0),
                "n_refused": sum(1 for x in cbw.refusals(s, h) if x > 0.5),
                "signs": cbw.signs(s, h),
                "max_sign_dist": max(dists), "epoch": cbw.scene_epoch(s, h)}

    grid6 = lambda pat: cim._grid(pat)
    # colour identity: E (3 clusters), G (36-shade gradient)
    ramp = [dict(cL=10 + i, cM=10, cS=20) for i in range(36)]
    # achromatopsia: DISSOCIATION (equiluminant A/B figure, k=2),
    # SPLIT_CLEAN (luminance edge, k=1), FLOOR (achromatic ramp, k=1)
    diss = [dict(cL=15, cM=5, cS=20) if (1 <= r <= 3 and 1 <= c <= 3)
            else dict(cL=5, cM=15, cS=20)
            for r in range(6) for c in range(6)]
    split = [dict(cL=10, cM=10, cS=20) if c < 3 else dict(cL=20, cM=20, cS=40)
             for r in range(6) for c in range(6)]
    floor = [dict(cL=v, cM=v, cS=2 * v)
             for v in [3 + i for i in range(36)]]

    scenes = {
        "colour_identity_E_3clusters": grid6([A] * 12 + [B] * 12 + [C] * 12),
        "colour_identity_G_gradient": grid6(ramp),
        "achromatopsia_DISSOCIATION": grid6(diss),
        "achromatopsia_SPLIT_CLEAN": grid6(split),
        "achromatopsia_FLOOR": grid6(floor),
    }
    out, n_changed = {}, 0
    for name, cells in scenes.items():
        off = scene_stats(cells, bound=0.0)
        on = scene_stats(cells, bound=1.0)
        changed = {k: [off[k], on[k]] for k in off if off[k] != on[k]}
        n_changed += len(changed)
        cats = [(c["crg"], c["cby"]) for c in off["categories"]]
        out[name] = {"k": off["n_categories"],
                     "packing_radius": _packing_radius(cats),
                     "off": off, "on": on, "changed": changed}
    # The two L1b probes are NOT landed gate assertions — they are the defect. Their
    # change is the POINT of the rung and is reported separately, not counted here.
    return {"n_changed_fields_across_landed_scenes": n_changed, "scenes": out}


def main():
    t0 = time.time()
    res = {
        "rung": "colour identity refusal bound (packing radius)",
        "prereg": "VISION_COLOUR_BOUND_PREREG.md",
        "engine": provenance_line(),
        "seeds_burned": {"boundary_exact": [50000, 50099],
                         "noise_floor": [50100, 50199]},
        "A_defect_reproduced": arm_A(),
        "B_bound_refuses": arm_B(),
        "C_no_regression": arm_C(),
        "D_ambiguity": arm_D(),
        "E_boundary_exact": arm_E(),
        "F_noise_floor": arm_F(),
        "X_offday": arm_X(),
        "DELTA_ON": delta_on(),
    }
    res["ALL_GATED_ARMS_PASS"] = all(
        res[k]["PASS"] for k in
        ["A_defect_reproduced", "B_bound_refuses", "C_no_regression",
         "D_ambiguity", "E_boundary_exact", "F_noise_floor", "X_offday"])
    res["elapsed_s"] = round(time.time() - t0, 1)

    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(here, "results", "colour_bound_measure.json")
    with open(out, "w") as f:
        json.dump(res, f, indent=1)
        f.write("\n")

    print(res["engine"])
    for k in ["A_defect_reproduced", "B_bound_refuses", "C_no_regression",
              "D_ambiguity", "E_boundary_exact", "F_noise_floor", "X_offday"]:
        print(f"  {k:24s} PASS={res[k]['PASS']}")
    print(f"  DELTA_ON changed fields across landed scenes: "
          f"{res['DELTA_ON']['n_changed_fields_across_landed_scenes']}")
    print(f"ALL_GATED_ARMS_PASS = {res['ALL_GATED_ARMS_PASS']}  ({res['elapsed_s']}s)")
    print("wrote", out)


if __name__ == "__main__":
    main()
