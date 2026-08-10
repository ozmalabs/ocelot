"""IDENTITY UNTANGLING — the objecthood "what" wall — confirmatory runner.

Realizes `VISION_VENTRAL_GROUNDING.md` BUILD-IMPLICATION #1/#5 by COMPOSITION
over the existing sd loop (no new Rust, no covariance/Hebbian):

    IDENTITY   = covered_by (the base a discovered transform maps FROM)
    NUISANCE   = the Transform on has_transform (generator + k)
    RECOGNITION= same-orbit membership decided by run_rules

See `VISION_IDENTITY_UNTANGLING_PREREG.md` for the pre-registered arms/
thresholds/predictions. Writes `results/identity_untangling.json`.

The adapter only builds ShapeSignature objects + Observation views, calls
run_rules, and reads status/covered_by. Every DECISION lives in the seed rules /
Rust Terms.
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

# 7 full-rank free pentominoes (distinct D4 orbits by definition; distinct under
# the held invertible discrete-similarity generators — verified by the
# discrimination arm below).
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

# discrete-similarity class (held, invertible/injective) as integer matrices
XF_DS = {
    "identity": [1, 0, 0, 1], "rot90": [0, -1, 1, 0], "rot180": [-1, 0, 0, -1],
    "rot270": [0, 1, -1, 0], "refl_r": [-1, 0, 0, 1], "refl_c": [1, 0, 0, -1],
    "scale2": [2, 0, 0, 2],
}
SHEARS = {"shearX": [1, 1, 0, 1], "shearY": [1, 0, 1, 1]}


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


def _boot(codebook, gen_infer):
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    # ISOLATE the codebook: remove the 17 pre-seeded symbolic ShapeSignatures so
    # only the objects under test are candidate identities.
    for n in list(s.nodes("ShapeSignature")):
        s.remove_node(n)
    if gen_infer:
        s.set_attr(ag, "gen_infer_enabled", 1.0)
    for nm, cs in codebook.items():
        s.add_node("ShapeSignature", {"name": nm, "signature": json.dumps(sig(cs)),
                   "kind": "faculty", "faculty": nm, "dim_types": DT})
    return s, ag, native


def identify(codebook, view_cells, gen_infer=False):
    """Present a view; return (status, covered_by_or_None)."""
    s, ag, native = _boot(codebook, gen_infer)
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
    return st, cov


def raw_nearest(view_cells):
    """Naive template match in raw (origin-normalized) cell space — the
    tangled 'image-space' baseline (translation-normalized only)."""
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


def regime_A():
    out = {}
    # H_invariance + H_untangling
    inv_ok = inv_wrong = inv_new = 0
    raw_ok = raw_wrong = 0
    wrong_detail = []
    for src, xf, view in _views(XF_DS):
        _, cov = identify(OBJ, view, gen_infer=False)
        if cov == src:
            inv_ok += 1
        elif cov is None:
            inv_new += 1
            wrong_detail.append([src, xf, "NEW"])
        else:
            inv_wrong += 1
            wrong_detail.append([src, xf, cov])
        if raw_nearest(view) == src:
            raw_ok += 1
        else:
            raw_wrong += 1
    total = len(OBJ) * len(XF_DS)
    out["invariance"] = {"correct": inv_ok, "wrong_id": inv_wrong, "new": inv_new,
                         "total": total, "wrong_detail": wrong_detail}
    out["untangling"] = {"raw_correct": raw_ok, "raw_wrong": raw_wrong,
                         "orbit_wrong": inv_wrong, "total": total}
    # H_discrimination — pairwise cross-map
    fails = []
    for i in OBJ:
        for j in OBJ:
            if i == j:
                continue
            st, cov = identify({i: OBJ[i]}, OBJ[j], gen_infer=False)
            if st in ("recognized", "recognized_transformed"):
                fails.append([j, i, st, cov])
    out["discrimination"] = {"fails": len(fails), "total": len(OBJ) * (len(OBJ) - 1),
                             "fail_detail": fails}
    # H_floor_a — noise objects, seeds 37000-37099
    force = []
    for i in range(100):
        rng = random.Random(37000 + i)
        cells = set()
        while len(cells) < 5:
            cells.add((rng.randint(0, 7), rng.randint(0, 7)))
        _, cov = identify(OBJ, list(cells), gen_infer=False)
        if cov is not None:
            force.append([37000 + i, cov])
    out["floor_a_noise"] = {"force_maps": len(force), "total": 100, "detail": force}
    # H_floor_b — non-rigid single-cell warp
    fb = []
    for src, cs in OBJ.items():
        nn = norm(cs)[:]
        r, c = nn[-1]
        nn[-1] = (r + 2, c + 2)
        _, cov = identify(OBJ, nn, gen_infer=False)
        if cov is not None:
            fb.append([src, cov])
    out["floor_b_warp"] = {"force_maps": len(fb), "total": len(OBJ), "detail": fb}
    return out


def regime_B():
    out = {}
    # B1 — singular-map leak: collinear target vs full-rank codebook
    st, cov = identify(OBJ, COLLINEAR, gen_infer=True)
    out["B1_collinear_leak"] = {"status": st, "covered_by": cov,
                                "leak": cov is not None}
    # B2 — not-a-group: invariance/discrimination with shears, gen_infer ON
    xf_all = {**XF_DS, **SHEARS}
    wrong = []
    correct = new = 0
    for src, xf, view in _views(xf_all):
        _, cov = identify(OBJ, view, gen_infer=True)
        if cov == src:
            correct += 1
        elif cov is None:
            new += 1
        else:
            wrong.append([src, xf, cov])
    out["B2_invariance_genON"] = {"correct": correct, "wrong_id": len(wrong),
                                  "new": new, "total": len(OBJ) * len(xf_all),
                                  "wrong_detail": wrong}
    # B2 floor-b under gen ON: real-angle rotation (the aliasing/identifiability
    # probe) + non-rigid warp
    def rrot(cs, deg):
        th = math.radians(deg)
        return [(round(r * math.cos(th) - c * math.sin(th)),
                 round(r * math.sin(th) + c * math.cos(th))) for r, c in norm(cs)]
    fb = []
    n = 0
    for src, cs in OBJ.items():
        for deg in (37, 53):
            n += 1
            _, cov = identify(OBJ, rrot(cs, deg), gen_infer=True)
            if cov is not None:
                fb.append([src, "rrot%d" % deg, cov])
        nn = norm(cs)[:]
        r, c = nn[-1]; nn[-1] = (r + 2, c + 2)
        n += 1
        _, cov = identify(OBJ, nn, gen_infer=True)
        if cov is not None:
            fb.append([src, "warp", cov])
    out["B2_floor_b_genON"] = {"force_maps": len(fb), "total": n, "detail": fb}
    # discrimination under gen ON
    fails = []
    for i in OBJ:
        for j in OBJ:
            if i == j:
                continue
            st, cov = identify({i: OBJ[i]}, OBJ[j], gen_infer=True)
            if st in ("recognized", "recognized_transformed"):
                fails.append([j, i, cov])
    out["B2_discrimination_genON"] = {"fails": len(fails),
                                      "total": len(OBJ) * (len(OBJ) - 1),
                                      "fail_detail": fails}
    return out


def main():
    res = {"provenance": _PROV,
           "objects": list(OBJ), "n_objects": len(OBJ),
           "regime_A_discrete_similarity_gen_OFF": regime_A(),
           "regime_B_general_integer_linear_gen_ON": regime_B()}
    outp = os.path.join(_ROOT, "results", "identity_untangling.json")
    os.makedirs(os.path.dirname(outp), exist_ok=True)
    with open(outp, "w") as f:
        json.dump(res, f, indent=2)
    print(_PROV)
    A = res["regime_A_discrete_similarity_gen_OFF"]
    B = res["regime_B_general_integer_linear_gen_ON"]
    print("== REGIME A (held invertible discrete-similarity, gen_infer OFF) ==")
    print("  INVARIANCE   : %(correct)d/%(total)d correct, %(wrong_id)d wrong, %(new)d new" % A["invariance"])
    print("  DISCRIMINATION: %(fails)d/%(total)d spurious cross-maps" % A["discrimination"])
    print("  UNTANGLING   : raw_wrong=%(raw_wrong)d  orbit_wrong=%(orbit_wrong)d  (of %(total)d)" % A["untangling"])
    print("  FLOOR-a noise: %(force_maps)d/%(total)d force-maps" % A["floor_a_noise"])
    print("  FLOOR-b warp : %(force_maps)d/%(total)d force-maps" % A["floor_b_warp"])
    print("== REGIME B (general integer-linear discovery, gen_infer ON) ==")
    print("  B1 collinear leak: covered_by=%(covered_by)s  leak=%(leak)s" % B["B1_collinear_leak"])
    print("  B2 invariance    : %(correct)d/%(total)d correct, %(wrong_id)d WRONG-id, %(new)d new" % B["B2_invariance_genON"])
    print("  B2 discrimination: %(fails)d/%(total)d spurious cross-maps" % B["B2_discrimination_genON"])
    print("  B2 floor-b       : %(force_maps)d/%(total)d force-maps" % B["B2_floor_b_genON"])
    print("wrote", outp)
    return res


if __name__ == "__main__":
    main()
