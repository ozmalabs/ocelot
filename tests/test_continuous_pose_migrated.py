"""CONTINUOUS POSE (FRONTIER rung T1) — gate.

Real-angle rotation recognized as a cross-frame generator (Rotate, continuous theta)
rendered to the stepped lattice, decided by the held PointSetDist verdict over a
discrete codebook proposal (bins propose, continuous decides). All graph-native:
covered_by = Argmin over ShapeSignature candidates of MinOver over angles of
PointSetDist(render, obs.points), via the seed rules cp_recognize / cp_refuse gated on
agent.cont_pose (OFF by default). NO new Rust.

See VISION_CONTINUOUS_POSE_PREREG.md / VISION_CONTINUOUS_POSE_RESULTS.md.
"""
import os
import sys
import math
import random

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
sys.path.insert(0, _ROOT)

from substrate.boot_core import boot_core          # noqa: E402
from substrate.seed_loader import manifest_for      # noqa: E402
from domains import reflective_faculty as rf        # noqa: E402

DT = ["pred", "coord:r", "coord:c", "val"]
OBJ = {
    "F": [(0, 1), (0, 2), (1, 0), (1, 1), (2, 1)],
    "T": [(0, 0), (0, 1), (0, 2), (1, 1), (2, 1)],
    "U": [(0, 0), (0, 2), (1, 0), (1, 1), (1, 2)],
    "V": [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)],
    "L": [(0, 0), (1, 0), (2, 0), (3, 0), (3, 1)],
    "N": [(0, 0), (1, 0), (2, 0), (2, 1), (3, 1)],
    "X": [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],
}
GRID = [math.radians(d) for d in range(0, 360, 2)]


def _center(pts):
    mx = sum(p[0] for p in pts) / len(pts)
    my = sum(p[1] for p in pts) / len(pts)
    return [[float(p[0] - mx), float(p[1] - my)] for p in pts]


def _dense(cells, s):
    pts = set()
    for (r, c) in cells:
        for i in range(s):
            for j in range(s):
                pts.add((r * s + i, c * s + j))
    return _center([[float(a), float(b)] for a, b in pts])


def _observe(cells, s, deg):
    th = math.radians(deg)
    pc = _dense(cells, s)
    r = {(round(x * math.cos(th) - y * math.sin(th)),
          round(x * math.sin(th) + y * math.cos(th))) for x, y in pc}
    return _center([[float(a), float(b)] for a, b in r])


def _boot(scale, flag=True):
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    native.load_seed_manifest(manifest_for("continuous_pose"), ag)
    if flag:
        s.set_attr(ag, "cont_pose", 1.0)
    s.set_attr(ag, "cp_angles", GRID)
    for nm, cs in OBJ.items():
        s.add_node("ShapeSignature", {"name": nm, "points": _dense(cs, scale),
                   "kind": "faculty", "faculty": nm, "dim_types": DT})
    return s, ag, native


def _present(s, ag, native, view):
    o = s.add_node("Observation", {"points": view, "status": "cp_decoded"})
    s.add_edge(ag, "observed", o)
    native.run_rules()
    at = s.node(o)["attrs"]
    return at.get("status"), at.get("covered_by")


def test_seed_installs_two_rules():
    m = manifest_for("continuous_pose")
    names = {r["name"] for r in m["rules"]}
    assert names == {"cp_recognize", "cp_refuse"}


def test_invariance_recognizes_rotated_identity_at_adequate_resolution():
    # A1: every object rotated by real angles -> recognized as its own identity (s=4).
    s, ag, native = _boot(4)
    ok = 0
    tot = 0
    for tk in OBJ:
        for deg in (23, 41, 67):
            tot += 1
            st, cov = _present(s, ag, native, _observe(OBJ[tk], 4, deg))
            if st == "recognized_continuous" and cov == tk:
                ok += 1
    assert ok == tot, "expected all rotated identities recognized at s=4, got %d/%d" % (ok, tot)


def test_discrimination_no_wrong_id_merge():
    # A2: the argmin picks the TRUE identity — different shapes are not merged under theta.
    s, ag, native = _boot(4)
    wrong = 0
    for tk in OBJ:
        st, cov = _present(s, ag, native, _observe(OBJ[tk], 4, 47))
        if st == "recognized_continuous" and cov is not None and cov != tk:
            wrong += 1
    assert wrong == 0


def test_noise_is_refused_not_force_merged():
    # A5 floor: a random blob is a rotation of no candidate -> cp_refused (residual > sqrt2/2).
    s, ag, native = _boot(4)
    forced = 0
    for i in range(20):
        rng = random.Random(40000 + i)
        cells = set()
        while len(cells) < 5:
            cells.add((rng.randint(0, 7), rng.randint(0, 7)))
        st, cov = _present(s, ag, native, _observe(list(cells), 4, 0))
        if st == "recognized_continuous" and cov is not None:
            forced += 1
    assert forced == 0


def test_off_by_default_neither_rule_fires():
    # sec 9: with cont_pose absent the cp rules do NOT fire — the observation keeps its
    # marker status (no recognized_continuous / cp_refused), so the sd loop is untouched.
    s, ag, native = _boot(4, flag=False)
    st, cov = _present(s, ag, native, _observe(OBJ["F"], 4, 41))
    assert st == "cp_decoded"
    assert cov is None


def test_continuous_decides_where_discrete_aliases_or_mints():
    # A3 crux (one case, light): the discrete-similarity path MINTS a real-angle
    # rotation (no exact lattice similarity); the continuous verdict recognizes it.
    import json as _json
    # continuous
    s, ag, native = _boot(2)
    st, cov = _present(s, ag, native, _observe(OBJ["F"], 2, 37))
    assert st == "recognized_continuous" and cov == "F"
    # discrete-similarity on the same dense rounded rotation
    sd, agd = boot_core()
    natd = rf._native_eval2(sd)
    rf._ensure_shape_decode_loop(sd, natd, agd)
    for n in list(sd.nodes("ShapeSignature")):
        sd.remove_node(n)
    sd.set_attr(agd, "gen_infer_enabled", 1.0)
    sd.set_attr(agd, "gen_similarity", 1.0)

    def cells(cs, s_):
        out = set()
        for (r, c) in cs:
            for i in range(s_):
                for j in range(s_):
                    out.add((r * s_ + i, c * s_ + j))
        return sorted(out)

    def sig(cs):
        mr = min(r for r, _ in cs); mc = min(c for _, c in cs)
        return [["cell", r, c, "red"] for r, c in sorted((r - mr, c - mc) for r, c in cs)]

    for nm, cs in OBJ.items():
        sd.add_node("ShapeSignature", {"name": nm, "signature": _json.dumps(sig(cells(cs, 2))),
                    "kind": "faculty", "faculty": nm, "dim_types": DT})
    th = math.radians(37)
    pc = cells(OBJ["F"], 2)
    mx = sum(p[0] for p in pc) / len(pc); my = sum(p[1] for p in pc) / len(pc)
    view = list({(round((x - mx) * math.cos(th) - (y - my) * math.sin(th)),
                  round((x - mx) * math.sin(th) + (y - my) * math.cos(th))) for x, y in pc})
    goal = [["cell", r, c, "red"] for r, c in sorted((r - min(a for a, _ in view),
            c - min(b for _, b in view)) for r, c in view)]
    ep = sd.node(agd)["attrs"].get("codebook_epoch") or 0.0
    obs = sd.add_node("Observation", {"signature": goal, "key": ["probe"], "status": "decoded",
                      "residual": goal, "decoded_epoch": ep, "dim_types": DT})
    sd.add_edge(agd, "observed", obs)
    natd.run_rules()
    dstatus = sd.node(obs)["attrs"].get("status")
    # the discrete path does NOT recognize it as F (mints novel / refuses)
    dcov = sd.node(obs)["attrs"].get("covered_by") if dstatus in ("recognized", "recognized_transformed") else None
    assert dcov != "F", "discrete unexpectedly recognized the real rotation as F (crux would be void)"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
