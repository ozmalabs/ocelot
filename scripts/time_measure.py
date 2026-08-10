#!/usr/bin/env python3
"""TIME AS AN INFERRED DIMENSION — the confirmatory measurement (VISION_TIME_PREREG.md).

Every arm is DETERMINISTIC except H_floor, whose 400 random shuffles draw from
seeds 26100-26999 (declared). Run from the gamma-substrate dir:

    PYTHONPATH=runners/dsl/python:. python scripts/time_measure.py
"""
from __future__ import annotations
import json, random, sys

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

from substrate.boot_core import boot_core           # noqa: E402
from domains import reflective_faculty as rf         # noqa: E402
from substrate.seed_loader import manifest_for       # noqa: E402

DT = ["pred", "coord:r", "coord:c", "val"]
BASE = [["cell", 0, 0, "red"], ["cell", 1, 0, "red"],
        ["cell", 2, 0, "red"], ["cell", 2, 1, "red"]]
NCELL = len(BASE)


def lin(M, cs):
    rs = [c[1] for c in cs]; cc = [c[2] for c in cs]; mr, mc = min(rs), min(cc)
    return [["cell", M[0]*(r-mr)+M[1]*(c-mc), M[2]*(r-mr)+M[3]*(c-mc), v] for _, r, c, v in cs]


def trans(dv, cs):
    return [["cell", r+dv[0], c+dv[1], v] for _, r, c, v in cs]


def orbit(fn, n=7):
    out = [BASE]; cur = BASE
    for _ in range(n - 1):
        cur = fn(cur); out.append(cur)
    return out


def boot(enabled):
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    native.load_seed_manifest(manifest_for("time_axis"), ag)
    if enabled:
        s.set_attr(ag, "time_infer_enabled", 1.0)
    s.add_node("ShapeSignature", {"name": "base_L", "signature": json.dumps(BASE),
               "kind": "faculty", "faculty": "base_L", "dim_types": DT})
    return s, ag, native


def time_lds(s):
    """Return the minted latent:time dimensions and their descriptors."""
    out = []
    for n in s.nodes("LatentDimension"):
        a = s.node(n)["attrs"]
        if a.get("name") == "latent:time":
            out.append((a.get("generator_kind"), tuple(a.get("offset") or ()),
                        tuple(a.get("matrix") or ()), a.get("window")))
    return out


def run(enabled, frames):
    s, ag, native = boot(enabled)
    o = s.add_node("Observation", {"frames": frames, "dim_types": DT,
                   "status": "motion_seq", "key": ["motion"]})
    s.add_edge(ag, "observed", o)
    native.run_rules()
    at = s.node(o)["attrs"]
    return dict(status=at.get("status"), kind=at.get("time_kind"),
                predicted=at.get("predicted"), lds=time_lds(s))


def main():
    R = {"engine": provenance_line()}
    ok = {}
    print("ENGINE:", R["engine"])

    # --- H_time: IDEAL — ordered orbit mints latent:time AND compresses ---
    print("\n[H_time] ordered translate(2,0) orbit -> latent:time + MDL compression")
    K = 7
    r = run(True, orbit(lambda c: trans((2, 0), c), K))
    minted = len(r["lds"]) == 1 and r["lds"][0][0] == "translate" and r["lds"][0][1] == (2, 0)
    # MDL (predicate tokens): WITHOUT = K frames enumerated (K*ncell); WITH =
    # f0 (ncell) + offset (2) + window (1). The generator + one base frame
    # replace K stored frames.
    mdl_without = K * NCELL
    mdl_with = NCELL + 2 + 1
    ok["H_time"] = minted and mdl_with < mdl_without
    R["H_time"] = {"minted": r["lds"], "status": r["status"],
                   "mdl_without": mdl_without, "mdl_with": mdl_with,
                   "ratio": round(mdl_without / mdl_with, 3)}
    print(f"  => minted={r['lds']}  MDL {mdl_without}->{mdl_with} "
          f"({mdl_without/mdl_with:.2f}x)  PASS={ok['H_time']}")

    # --- H_multimotion: §13.1 — 5 motions, 5 DIFFERENT correct generators ---
    print("\n[H_multimotion] frozen TimeInfer -> correct DIFFERENT generator per motion")
    motions = {
        "translate(2,0)": (lambda c: trans((2, 0), c), "translate", (2, 0), ()),
        "translate(1,3)": (lambda c: trans((1, 3), c), "translate", (1, 3), ()),
        "shear[1,0,1,1]": (lambda c: lin([1, 0, 1, 1], c), "linear", (), (1, 0, 1, 1)),
        "rotate90":       (lambda c: lin([0, -1, 1, 0], c), "linear", (), (0, -1, 1, 0)),
        "scale2":         (lambda c: lin([2, 0, 0, 2], c), "linear", (), (2, 0, 0, 2)),
    }
    mm = {}; descriptors = set()
    for name, (fn, ek, eoff, emat) in motions.items():
        n = 4 if name == "scale2" else 6  # scale grows fast; keep coords bounded
        r = run(True, orbit(fn, n))
        got = r["lds"][0] if len(r["lds"]) == 1 else None
        correct = got is not None and got[0] == ek and got[1] == eoff and got[2] == emat
        if got:
            descriptors.add((got[0], got[1], got[2]))
        mm[name] = {"expected": [ek, eoff, emat], "got": got, "correct": correct}
        print(f"  {name:16} -> {got}  CORRECT={correct}")
    ok["H_multimotion"] = all(v["correct"] for v in mm.values()) and len(descriptors) == 5
    R["H_multimotion"] = mm
    print(f"  => 5/5 correct AND all 5 distinct: {ok['H_multimotion']}")

    # --- H_floor: THE GATE — random shuffles, longest window K=8, 0 spurious ---
    print("\n[H_floor] random shuffles (seeds 26100-26999), LONGEST window K=8; gate: 0 spurious mints")
    K8 = 8
    orbits = {"shear": orbit(lambda c: lin([1, 0, 1, 1], c), K8),
              "translate": orbit(lambda c: trans((2, 0), c), K8)}
    spurious = 0; reversals = 0; examples = []
    seed = 26100
    for kind, ob in orbits.items():
        for i in range(200):
            random.seed(seed); seed += 1
            sh = ob[:]; random.shuffle(sh)
            r = run(True, sh)
            if r["lds"]:
                # a mint that is an EXACT monotone reversal is a genuine orbit
                if sh == ob[::-1]:
                    reversals += 1
                else:
                    spurious += 1
                    if len(examples) < 3:
                        examples.append((kind, seed - 1, r["lds"]))
    ok["H_floor"] = (spurious == 0)
    R["H_floor"] = {"n": 400, "window": K8, "spurious_mints": spurious,
                    "legitimate_reversals": reversals, "examples": examples,
                    "report": "no transition generator shorter than enumeration "
                              "found over 400 random shuffles at K=8 (provisional)"}
    print(f"  => spurious mints: {spurious} (gate: 0); legitimate reversals: {reversals}  PASS={ok['H_floor']}")

    # --- H_varying: the specifically-TEMPORAL control (constant vs varying) ---
    print("\n[H_varying] accelerating translate (steps 1,2,3,..) -> time_none (not constant velocity)")
    acc = [BASE]; cur = BASE
    for k in range(1, 7):
        cur = trans((k, 0), cur); acc.append(cur)
    r = run(True, acc)
    ok["H_varying"] = (r["status"] == "time_none" and not r["lds"])
    R["H_varying"] = {"status": r["status"], "lds": r["lds"]}
    print(f"  => status={r['status']} lds={r['lds']}  PASS={ok['H_varying']} "
          f"(frames are pairwise mutual-translates yet NOT an orbit)")

    # --- H_downstream: LOAD-BEARING (§1 clause 5 / §13.2) ---
    print("\n[H_downstream] minted axis predicts an UNSEEN later frame G^K(f0)=withheld f7; toggle -> D>0")
    frames7 = orbit(lambda c: trans((2, 0), c), 7)   # f0..f6
    withheld = sorted([tuple(x) for x in trans((14, 0), BASE)])   # f7, unseen
    on = run(True, frames7)
    off = run(False, frames7)
    on_pred = sorted([tuple(x) for x in on["predicted"]]) if on["predicted"] else None
    pred_ok = (on_pred == withheld)
    d_mint = len(on["lds"]) - len(off["lds"])
    d_pred = (1 if on["predicted"] else 0) - (1 if off["predicted"] else 0)
    ok["H_downstream"] = pred_ok and len(on["lds"]) == 1 and not off["lds"] and (d_mint > 0 and d_pred > 0)
    R["H_downstream"] = {"predicted_matches_withheld": pred_ok,
                         "on_lds": on["lds"], "off_lds": off["lds"],
                         "D_mint": d_mint, "D_pred": d_pred}
    print(f"  => predicted==withheld f7: {pred_ok}  D_mint={d_mint} D_pred={d_pred}  PASS={ok['H_downstream']}")

    # --- H_offday: §9 — flag OFF is inert ---
    print("\n[H_offday] flag OFF -> ordered orbit does NOT mint (inert, status unchanged)")
    off = run(False, orbit(lambda c: trans((2, 0), c), 7))
    ok["H_offday"] = (off["status"] == "motion_seq" and not off["lds"])
    R["H_offday"] = {"status": off["status"], "lds": off["lds"],
                     "note": "sd orbit law / genmint 6 / provenance / bench reported separately in RESULTS"}
    print(f"  => OFF status={off['status']} lds={off['lds']}  PASS={ok['H_offday']}")

    R["verdict"] = ok
    passed = all(ok.values())
    R["time_is_inferred_dimension"] = passed
    print("\n" + "=" * 68)
    for k, v in ok.items():
        print(f"  {k:16} {'PASS' if v else 'FAIL'}")
    print(f"  TIME IS AN INFERRED DIMENSION (bounded to the motion class): {passed}")
    print("=" * 68)

    json.dump(R, open("results/time_measure.json", "w"), indent=1, default=str)
    print("wrote results/time_measure.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
