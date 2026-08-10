"""CONTINUOUS POSE — real-angle rotation as a cross-frame generator, decided by a
continuous verdict — confirmatory runner (FRONTIER rung T1).

Realizes the "bins propose, continuous decides" synthesis for ROTATION: the discrete
similarity codebook proposes the identity set; the continuous verdict RENDERS each
candidate at continuous theta (the held `Rotate` Term — the cross-frame generator,
theta a Float, never an in-frame coordinate) over an angle grid and DECIDES by the
held `PointSetDist` (Modified Hausdorff). All graph-native: covered_by = Argmin over
ShapeSignature candidates of MinOver over angles of PointSetDist(render, obs.points),
mint by the two seed rules `cp_recognize` / `cp_refuse` (seeds/continuous_pose.json),
gated on `agent.cont_pose` (OFF by default). NO new Rust.

See VISION_CONTINUOUS_POSE_PREREG.md for the pre-registered arms/thresholds/predictions.
Writes results/continuous_pose.json.

The adapter only dense-samples the codebook, generates rotated-and-rastered stimuli
(world I/O), sets the flag + angle grid, calls run_rules, and reads status/covered_by
(+ runs the discrete-similarity path as the crux baseline). Every DECISION lives in the
seed rules / held Rust Terms — no Python decision, no covariance, no Hebbian.
"""
from __future__ import annotations
import sys, os, json, math, random

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
from substrate.seed_loader import manifest_for
from domains import reflective_faculty as rf

DT = ["pred", "coord:r", "coord:c", "val"]

# 7 full-rank free pentominoes — SAME construction as the wall / det1 / similarity rungs.
OBJ = {
    "F": [(0, 1), (0, 2), (1, 0), (1, 1), (2, 1)],
    "T": [(0, 0), (0, 1), (0, 2), (1, 1), (2, 1)],
    "U": [(0, 0), (0, 2), (1, 0), (1, 1), (1, 2)],
    "V": [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)],
    "L": [(0, 0), (1, 0), (2, 0), (3, 0), (3, 1)],
    "N": [(0, 0), (1, 0), (2, 0), (2, 1), (3, 1)],
    "X": [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],
}
NAMES = list(OBJ)
ANGLE_STEP_DEG = 2   # step-invariant (2 deg == 1 deg, pilot 0 mismatches) — not tuned (sec 13)
GRID = [math.radians(d) for d in range(0, 360, ANGLE_STEP_DEG)]
GRID_FINE = [math.radians(d) for d in range(0, 360, 1)]


def center(pts):
    mx = sum(p[0] for p in pts) / len(pts)
    my = sum(p[1] for p in pts) / len(pts)
    return [[float(p[0] - mx), float(p[1] - my)] for p in pts]


def dense(cells, s):
    """Dense-sample each unit cell as an s x s block of lattice points; centroid-centre.
    A DENSER SAMPLING of the SAME shape (recovering theta), not a new object."""
    pts = set()
    for (r, c) in cells:
        for i in range(s):
            for j in range(s):
                pts.add((r * s + i, c * s + j))
    return center([[float(a), float(b)] for a, b in pts])


def observe(cells, s, deg):
    """The in-frame-INTEGER observation: dense object rotated by REAL deg (about the
    centroid), each point ROUNDED to the nearest integer cell, deduped, recentred.
    The real theta lives only in the render below; the observation is stepped."""
    th = math.radians(deg)
    pc = dense(cells, s)
    r = {(round(x * math.cos(th) - y * math.sin(th)),
          round(x * math.sin(th) + y * math.cos(th))) for x, y in pc}
    return center([[float(a), float(b)] for a, b in r])


def _boot(scale):
    """Boot the sd loop + the continuous_pose seed; install the dense codebook and the
    flag/angle-grid graph data. Returns (substrate, agent, native)."""
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    native.load_seed_manifest(manifest_for("continuous_pose"), ag)
    s.add_node("Seed", {"id": "continuous_pose", "version": "1.0.0"})
    s.set_attr(ag, "cont_pose", 1.0)
    s.set_attr(ag, "cp_angles", GRID)
    for nm, cs in OBJ.items():
        s.add_node("ShapeSignature", {"name": nm, "points": dense(cs, scale),
                   "kind": "faculty", "faculty": nm, "dim_types": DT})
    return s, ag, native


def cp_identify(s, ag, native, view_points):
    """Present one continuous-pose observation; return (status, covered_by)."""
    o = s.add_node("Observation", {"points": view_points, "status": "cp_decoded"})
    s.add_edge(ag, "observed", o)
    native.run_rules()
    at = s.node(o)["attrs"]
    return at.get("status"), at.get("covered_by")


# ---- discrete-similarity baseline (the crux) — SAME machinery as similarity_measure ----
def _sig(cells):
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    n = sorted((r - mr, c - mc) for r, c in cells)
    return [["cell", r, c, "red"] for r, c in n]


def discrete_identify(codebook_cells, view_cells):
    """gen_infer=1, gen_similarity=1 recognition (integer cell sets). Returns
    (status, covered_by) — the discrete crux baseline."""
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    for n in list(s.nodes("ShapeSignature")):
        s.remove_node(n)
    s.set_attr(ag, "gen_infer_enabled", 1.0)
    s.set_attr(ag, "gen_similarity", 1.0)
    for nm, cs in codebook_cells.items():
        s.add_node("ShapeSignature", {"name": nm, "signature": json.dumps(_sig(cs)),
                   "kind": "faculty", "faculty": nm, "dim_types": DT})
    goal = _sig(view_cells)
    ep = s.node(ag)["attrs"].get("codebook_epoch") or 0.0
    obs = s.add_node("Observation", {"signature": goal, "key": ["probe"],
                     "status": "decoded", "residual": goal, "decoded_epoch": ep,
                     "dim_types": DT})
    s.add_edge(ag, "observed", obs)
    native.run_rules()
    at = s.node(obs)["attrs"]
    st = at.get("status")
    return st, (at.get("covered_by") if st in ("recognized", "recognized_transformed") else None)


def dense_cells(cells, s):
    """Integer dense cell set (for the discrete path): rounded rotated dense sampling."""
    out = set()
    for (r, c) in cells:
        for i in range(s):
            for j in range(s):
                out.add((r * s + i, c * s + j))
    return sorted(out)


def observe_cells(cells, s, deg):
    th = math.radians(deg)
    pc = dense_cells(cells, s)
    mx = sum(p[0] for p in pc) / len(pc); my = sum(p[1] for p in pc) / len(pc)
    r = {(round((x - mx) * math.cos(th) - (y - my) * math.sin(th)),
          round((x - mx) * math.sin(th) + (y - my) * math.cos(th))) for x, y in pc}
    return list(r)


# ---------------------------------- arms ----------------------------------
def arm_invariance(scale, angles):
    s, ag, native = _boot(scale)
    ok = wrong = refused = 0
    detail = []
    for tk in NAMES:
        for deg in angles:
            st, cov = cp_identify(s, ag, native, observe(OBJ[tk], scale, deg))
            if st == "recognized_continuous" and cov == tk:
                ok += 1
            elif st == "cp_refused" or cov is None:
                refused += 1; detail.append([tk, deg, "REFUSED"])
            else:
                wrong += 1; detail.append([tk, deg, cov])
    return {"scale": scale, "correct": ok, "wrong_id": wrong, "refused": refused,
            "total": len(NAMES) * len(angles), "wrong_detail": detail}


def run():
    out = {"provenance": _PROV, "angle_step_deg": ANGLE_STEP_DEG,
           "objects": NAMES, "threshold": "sqrt(2)/2 (unit-lattice half-diagonal, falls out)"}

    # A4 — IDENTIFIABILITY curve (also supplies A1 at s=4): resolution s=1..4.
    curve = {}
    for scale in (1, 2, 3, 4):
        curve[scale] = arm_invariance(scale, list(range(5, 90, 10)))
    out["A4_identifiability_curve"] = curve
    out["A1_invariance_headline"] = curve[4]      # adequate resolution

    # step-invariance: 2 deg vs 1 deg grid at s=4 must give identical verdicts
    global GRID
    s, ag, native = _boot(4)
    mism = 0
    for tk in NAMES:
        for deg in range(5, 90, 10):
            v = observe(OBJ[tk], 4, deg)
            st2, cov2 = cp_identify(s, ag, native, v)
            s.set_attr(ag, "cp_angles", GRID_FINE)
            st1, cov1 = cp_identify(s, ag, native, v)
            s.set_attr(ag, "cp_angles", GRID)
            if (st2, cov2) != (st1, cov1):
                mism += 1
    out["A4_step_invariance_2deg_vs_1deg_mismatches"] = mism

    # A2 — DISCRIMINATION: wrong-id count at s=4 (from the headline) + pairwise.
    s4, ag4, nat4 = _boot(4)
    pair_fail = 0
    for j in NAMES:
        st, cov = cp_identify(s4, ag4, nat4, dense(OBJ[j], 4))   # untransformed O_j
        if not (st == "recognized_continuous" and cov == j):
            pair_fail += 1
    out["A2_discrimination"] = {
        "wrong_id_at_s4": curve[4]["wrong_id"],
        "untransformed_recognized": len(NAMES) - pair_fail,
        "untransformed_total": len(NAMES),
        "exact0": curve[4]["wrong_id"] == 0 and pair_fail == 0}

    # A3 — CONTINUOUS-DECIDES CRUX at s=2: discrete-similarity vs continuous verdict on
    # the SAME dense real-rotation observations.
    crux_scale = 2
    sc, agc, natc = _boot(crux_scale)
    cob = {k: dense_cells(v, crux_scale) for k, v in OBJ.items()}
    disc_ok = cont_ok = tot = 0
    crux_detail = []
    for tk in NAMES:
        for deg in (37, 53):
            tot += 1
            # continuous
            st, cov = cp_identify(sc, agc, natc, observe(OBJ[tk], crux_scale, deg))
            c_ok = (st == "recognized_continuous" and cov == tk)
            cont_ok += int(c_ok)
            # discrete
            dst, dcov = discrete_identify(cob, observe_cells(OBJ[tk], crux_scale, deg))
            d_ok = (dcov == tk)
            disc_ok += int(d_ok)
            crux_detail.append([tk, deg, {"discrete": [dst, dcov], "continuous": [st, cov]}])
    out["A3_continuous_decides_crux"] = {
        "scale": crux_scale, "total": tot,
        "discrete_correct": disc_ok, "continuous_correct": cont_ok,
        "detail": crux_detail}

    # A5 — FLOOR: noise, seeds 40000-40099 (never used), dense-sampled at s=4.
    s4b, ag4b, nat4b = _boot(4)
    nforce = []
    for i in range(100):
        rng = random.Random(40000 + i)
        cells = set()
        while len(cells) < 5:
            cells.add((rng.randint(0, 7), rng.randint(0, 7)))
        st, cov = cp_identify(s4b, ag4b, nat4b, observe(list(cells), 4, 0))
        if st == "recognized_continuous" and cov is not None:
            nforce.append([40000 + i, cov])
    out["A5_noise_floor"] = {"force_maps": len(nforce), "total": 100, "detail": nforce[:10]}

    return out


def main():
    res = run()
    outp = os.path.join(_ROOT, "results", "continuous_pose.json")
    os.makedirs(os.path.dirname(outp), exist_ok=True)
    with open(outp, "w") as f:
        json.dump(res, f, indent=2)
    print(_PROV)
    print("== CONTINUOUS POSE (cont_pose=1) ==")
    print("  A1 INVARIANCE (s=4)  : %(correct)d/%(total)d correct, %(wrong_id)d wrong, %(refused)d refused" % res["A1_invariance_headline"])
    print("  A4 identifiability curve (correct/total per scale):")
    for sc in (1, 2, 3, 4):
        c = res["A4_identifiability_curve"][sc]
        print("      s=%d : %d/%d" % (sc, c["correct"], c["total"]))
    print("  A4 step 2deg==1deg   : %d mismatches" % res["A4_step_invariance_2deg_vs_1deg_mismatches"])
    A2 = res["A2_discrimination"]
    print("  A2 DISCRIMINATION    : wrong_id=%d  untransformed=%d/%d  exact0=%s" %
          (A2["wrong_id_at_s4"], A2["untransformed_recognized"], A2["untransformed_total"], A2["exact0"]))
    A3 = res["A3_continuous_decides_crux"]
    print("  A3 CRUX (s=2)        : discrete=%d/%d   continuous=%d/%d" %
          (A3["discrete_correct"], A3["total"], A3["continuous_correct"], A3["total"]))
    F = res["A5_noise_floor"]
    print("  A5 noise floor       : %(force_maps)d/%(total)d force-maps" % F)
    print("wrote", outp)
    return res


if __name__ == "__main__":
    main()
