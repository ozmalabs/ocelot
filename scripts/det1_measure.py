"""|det|=1 — the UNIMODULAR restriction on GenInfer — confirmatory runner.

Realizes the named-not-built fix from the objecthood WALL rung
(`VISION_IDENTITY_UNTANGLING_RESULTS.md`, Regime B) as a SEED GUARD (no new
Rust): restrict discovered generators to |det|=1 (the unimodular group
GL(2,Z)), expressed as graph DATA over the determinant of GenInfer's inferred
`matrix`. Mode under test: gen_infer_enabled=1 AND gen_unimodular=1.

See `VISION_DET1_PREREG.md` for the pre-registered arms/thresholds/predictions.
Writes `results/det1.json`.

The adapter only builds ShapeSignature objects + Observation views, sets flags,
calls run_rules, and reads status/covered_by (+ minted generator matrices for
the audit). Every DECISION lives in the seed rules / Rust Terms.
"""
from __future__ import annotations
import sys, os, json, math, random

# Tree-relative engine resolution (§10).
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
sys.path.insert(0, _ROOT)
try:
    from domains.engine_provenance import engine_preamble, provenance_line
    engine_preamble()
    _PROV = provenance_line()
except Exception as e:  # pragma: no cover
    _PROV = "PROVENANCE UNAVAILABLE: %r" % (e,)

from substrate.boot_core import boot_core
from domains import reflective_faculty as rf

DT = ["pred", "coord:r", "coord:c", "val"]

# 7 full-rank free pentominoes — SAME construction as the wall rung.
OBJ = {
    "F": [(0, 1), (0, 2), (1, 0), (1, 1), (2, 1)],
    "T": [(0, 0), (0, 1), (0, 2), (1, 1), (2, 1)],
    "U": [(0, 0), (0, 2), (1, 0), (1, 1), (1, 2)],
    "V": [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)],
    "L": [(0, 0), (1, 0), (2, 0), (3, 0), (3, 1)],
    "N": [(0, 0), (1, 0), (2, 0), (2, 1), (3, 1)],
    "X": [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],
}
COLLINEAR = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)]  # the "I" pentomino — degenerate

XF_DS = {
    "identity": [1, 0, 0, 1], "rot90": [0, -1, 1, 0], "rot180": [-1, 0, 0, -1],
    "rot270": [0, 1, -1, 0], "refl_r": [-1, 0, 0, 1], "refl_c": [1, 0, 0, -1],
    "scale2": [2, 0, 0, 2],
}
SHEARS = {"shearX": [1, 1, 0, 1], "shearY": [1, 0, 1, 1]}  # both det=1
DET0 = [1, 1, 0, 0]      # singular (det=0) — collapses onto a line
SCALE3 = [3, 0, 0, 3]    # det=9 — a NON-held integer scale (needs discovery)


def det(M):
    return M[0] * M[3] - M[1] * M[2]


def norm(cells):
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def sig(cells):
    return [["cell", r, c, "red"] for r, c in norm(cells)]


def lin(cells, M):
    n = norm(cells)
    return [(M[0] * r + M[1] * c, M[2] * r + M[3] * c) for r, c in n]


def translate(cells, dr, dc):
    return [(r + dr, c + dc) for r, c in cells]


def _boot(codebook, gen_infer, uni):
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    for n in list(s.nodes("ShapeSignature")):
        s.remove_node(n)
    if gen_infer:
        s.set_attr(ag, "gen_infer_enabled", 1.0)
    if uni:
        s.set_attr(ag, "gen_unimodular", 1.0)
    for nm, cs in codebook.items():
        s.add_node("ShapeSignature", {"name": nm, "signature": json.dumps(sig(cs)),
                   "kind": "faculty", "faculty": nm, "dim_types": DT})
    return s, ag, native


def identify(codebook, view_cells, gen_infer=True, uni=True):
    """Present a view; return (status, covered_by_or_None, minted_linear_dets)."""
    s, ag, native = _boot(codebook, gen_infer, uni)
    goal = sig(view_cells)
    ep = s.node(ag)["attrs"].get("codebook_epoch") or 0.0
    obs = s.add_node("Observation", {"signature": goal, "key": ["probe"],
                     "status": "decoded", "residual": goal, "decoded_epoch": ep,
                     "dim_types": DT})
    s.add_edge(ag, "observed", obs)
    native.run_rules()
    at = s.node(obs)["attrs"]
    st = at.get("status")
    cov = at.get("covered_by") if st in ("recognized", "recognized_transformed") else None
    lin_dets = [det(list(s.node(n)["attrs"].get("matrix")))
                for n in s.nodes("DimensionGenerator")
                if s.node(n)["attrs"].get("kind") == "linear"]
    return st, cov, lin_dets


def raw_nearest(view_cells):
    """Naive template match in raw (origin-normalized) cell space — the tangled
    'image-space' baseline (translation-normalized only)."""
    vs = set(norm(view_cells))
    best, bd = None, 1 << 30
    for nm, cs in OBJ.items():
        d = len(vs ^ set(norm(cs)))
        if d < bd:
            bd, best = d, nm
    return best


def _views(xforms):
    for src, cs in OBJ.items():
        for xf, M in xforms.items():
            yield src, xf, translate(lin(cs, M), 3, 2)


def _invariance(xforms):
    """(correct, wrong_id, new, raw_wrong, wrong_detail, audit_dets) over the grid."""
    ok = wrong = new = raw_wrong = 0
    wrong_detail = []
    audit_dets = []  # (src, xf, minted_dets) for views recognized via a discovered gen
    for src, xf, view in _views(xforms):
        _, cov, lin_dets = identify(OBJ, view, gen_infer=True, uni=True)
        if lin_dets:
            audit_dets.append([src, xf, lin_dets])
        if cov == src:
            ok += 1
        elif cov is None:
            new += 1
            wrong_detail.append([src, xf, "NEW"])
        else:
            wrong += 1
            wrong_detail.append([src, xf, cov])
        if raw_nearest(view) != src:
            raw_wrong += 1
    total = len(OBJ) * len(xforms)
    return {"correct": ok, "wrong_id": wrong, "new": new, "raw_wrong": raw_wrong,
            "total": total, "wrong_detail": wrong_detail, "audit_minted_dets": audit_dets}


def run():
    out = {"provenance": _PROV, "mode": "gen_infer=1, gen_unimodular=1",
           "objects": list(OBJ), "n_objects": len(OBJ)}

    # A1 — INVARIANCE (held discrete-similarity)
    out["A1_invariance_held"] = _invariance(XF_DS)
    # A2 — INVARIANCE (shears, the DISCOVERY crux)
    out["A2_invariance_shears"] = _invariance(SHEARS)

    # A3 — DISCRIMINATION exact-0 crux
    st, cov, _ = identify(OBJ, COLLINEAR, gen_infer=True, uni=True)
    b1 = {"status": st, "covered_by": cov, "refused": cov is None}
    fails = []
    for i in OBJ:
        for j in OBJ:
            if i == j:
                continue
            st2, cov2, _ = identify({i: OBJ[i]}, OBJ[j], gen_infer=True, uni=True)
            if st2 in ("recognized", "recognized_transformed"):
                fails.append([j, i, cov2])
    out["A3_discrimination"] = {
        "B1_collinear": b1,
        "pairwise_fails": len(fails), "pairwise_total": len(OBJ) * (len(OBJ) - 1),
        "pairwise_fail_detail": fails,
        # exact-0 identity preservation across the discovery arms:
        "shear_wrong_id": out["A2_invariance_shears"]["wrong_id"],
        "exact0_identity": (b1["refused"] and len(fails) == 0
                            and out["A2_invariance_shears"]["wrong_id"] == 0),
    }

    # A4 — UNTANGLING (raw vs orbit), reported per grid (already in A1/A2)
    out["A4_untangling"] = {
        "held":   {"raw_wrong": out["A1_invariance_held"]["raw_wrong"],
                   "orbit_wrong": out["A1_invariance_held"]["wrong_id"],
                   "total": out["A1_invariance_held"]["total"]},
        "shears": {"raw_wrong": out["A2_invariance_shears"]["raw_wrong"],
                   "orbit_wrong": out["A2_invariance_shears"]["wrong_id"],
                   "total": out["A2_invariance_shears"]["total"]},
    }

    # A5 — FLOORS
    # noise — seeds 38000-38099 (never used)
    nforce = []
    for i in range(100):
        rng = random.Random(38000 + i)
        cells = set()
        while len(cells) < 5:
            cells.add((rng.randint(0, 7), rng.randint(0, 7)))
        _, cov, _ = identify(OBJ, list(cells), gen_infer=True, uni=True)
        if cov is not None:
            nforce.append([38000 + i, cov])
    # det=0 singular map
    d0 = []
    for src, cs in OBJ.items():
        _, cov, _ = identify(OBJ, translate(lin(cs, DET0), 3, 2), gen_infer=True, uni=True)
        if cov is not None:
            d0.append([src, cov])
    # non-held scale (det=9)
    s3 = []
    for src, cs in OBJ.items():
        _, cov, _ = identify(OBJ, translate(lin(cs, SCALE3), 3, 2), gen_infer=True, uni=True)
        if cov is not None:
            s3.append([src, cov])
    # non-rigid warp
    warp = []
    for src, cs in OBJ.items():
        nn = norm(cs)[:]
        r, c = nn[-1]; nn[-1] = (r + 2, c + 2)
        _, cov, _ = identify(OBJ, nn, gen_infer=True, uni=True)
        if cov is not None:
            warp.append([src, cov])
    # real-angle rotation (REPORTED, not gated) — the identifiability limit
    def rrot(cs, deg):
        th = math.radians(deg)
        return [(round(r * math.cos(th) - c * math.sin(th)),
                 round(r * math.sin(th) + c * math.cos(th))) for r, c in norm(cs)]
    rr = []; rr_n = 0
    for src, cs in OBJ.items():
        for deg in (37, 53):
            rr_n += 1
            _, cov, _ = identify(OBJ, rrot(cs, deg), gen_infer=True, uni=True)
            if cov is not None:
                rr.append([src, "rrot%d" % deg, cov])
    out["A5_floors"] = {
        "noise": {"force_maps": len(nforce), "total": 100, "detail": nforce},
        "det0_singular": {"force_maps": len(d0), "total": len(OBJ), "detail": d0},
        "scale3_nonheld": {"force_maps": len(s3), "total": len(OBJ), "detail": s3},
        "nonrigid_warp": {"force_maps": len(warp), "total": len(OBJ), "detail": warp},
        "real_angle_rotation_REPORTED": {"force_maps": len(rr), "total": rr_n, "detail": rr},
    }

    # AUDIT — held scale2 / rot90 preserved under uni mode (sanity for A1's claim)
    _, cov_s2, _ = identify(OBJ, translate(lin(OBJ["F"], [2, 0, 0, 2]), 3, 2), gen_infer=True, uni=True)
    _, cov_r90, _ = identify(OBJ, translate(lin(OBJ["V"], [0, -1, 1, 0]), 3, 2), gen_infer=True, uni=True)
    # AUDIT — the seed-guard veto faithfulness: every minted linear generator |det|=1
    all_minted = []
    for src, xf, dets in (out["A1_invariance_held"]["audit_minted_dets"]
                          + out["A2_invariance_shears"]["audit_minted_dets"]):
        all_minted.extend(dets)
    out["AUDIT"] = {
        "held_scale2_F_covered_by": cov_s2,
        "held_rot90_V_covered_by": cov_r90,
        "minted_linear_generator_dets": all_minted,
        "all_minted_are_unimodular": all(abs(d) == 1 for d in all_minted),
    }
    return out


def main():
    res = run()
    outp = os.path.join(_ROOT, "results", "det1.json")
    os.makedirs(os.path.dirname(outp), exist_ok=True)
    with open(outp, "w") as f:
        json.dump(res, f, indent=2)
    print(_PROV)
    print("== |det|=1 UNIMODULAR RESTRICTION (gen_infer=1, gen_unimodular=1) ==")
    A1 = res["A1_invariance_held"]; A2 = res["A2_invariance_shears"]; A3 = res["A3_discrimination"]
    print("  A1 INVARIANCE held  : %(correct)d/%(total)d correct, %(wrong_id)d wrong, %(new)d new" % A1)
    print("  A2 INVARIANCE shears: %(correct)d/%(total)d correct, %(wrong_id)d WRONG-id, %(new)d new  detail=%(wrong_detail)s" % A2)
    print("  A3 B1 collinear     : covered_by=%(covered_by)s  refused=%(refused)s" % A3["B1_collinear"])
    print("  A3 pairwise         : %(pairwise_fails)d/%(pairwise_total)d spurious" % A3)
    print("  A3 EXACT-0 identity : %s  (shear_wrong_id=%d)" % (A3["exact0_identity"], A3["shear_wrong_id"]))
    U = res["A4_untangling"]
    print("  A4 untangling held  : raw_wrong=%(raw_wrong)d orbit_wrong=%(orbit_wrong)d /%(total)d" % U["held"])
    print("  A4 untangling shears: raw_wrong=%(raw_wrong)d orbit_wrong=%(orbit_wrong)d /%(total)d" % U["shears"])
    F = res["A5_floors"]
    print("  A5 noise            : %(force_maps)d/%(total)d force-maps" % F["noise"])
    print("  A5 det=0 singular   : %(force_maps)d/%(total)d force-maps" % F["det0_singular"])
    print("  A5 scale3 non-held  : %(force_maps)d/%(total)d force-maps" % F["scale3_nonheld"])
    print("  A5 non-rigid warp   : %(force_maps)d/%(total)d force-maps" % F["nonrigid_warp"])
    print("  A5 real-angle (rep) : %(force_maps)d/%(total)d force-maps" % F["real_angle_rotation_REPORTED"])
    AU = res["AUDIT"]
    print("  AUDIT held scale2/rot90 covered_by: %s / %s" % (AU["held_scale2_F_covered_by"], AU["held_rot90_V_covered_by"]))
    print("  AUDIT minted linear gen dets: %s  all_unimodular=%s" % (AU["minted_linear_generator_dets"], AU["all_minted_are_unimodular"]))
    print("wrote", outp)
    return res


if __name__ == "__main__":
    main()
