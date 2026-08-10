#!/usr/bin/env python3
"""DEPTH AS AN INFERRED DIMENSION — the confirmatory measurement (VISION_DEPTH_PREREG.md).

Monocular structure-from-motion: the residual of TimeInfer's single-generator
question, read as discrete depth. Every arm is DETERMINISTIC except H_shuffle,
whose random shuffles draw from declared seeds 27100-27499. Run from the
gamma-substrate dir:

    PYTHONPATH=runners/dsl/python:. python scripts/depth_measure.py
"""
from __future__ import annotations
import json, random, sys

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

from substrate.boot_core import boot_core           # noqa: E402
from domains import reflective_faculty as rf         # noqa: E402
from substrate.seed_loader import manifest_for       # noqa: E402

DT = ["pred", "coord:r", "coord:c", "val"]
# Surfaces sharing the SAME coordinate span (r 0..2, c 0..1), so no position
# gradient / shear can fake a velocity difference — only their appearance (a
# non-coord slot) distinguishes them. This is the interleaved discrete-depth case.
RED = [["cell", 0, 0, "red"],  ["cell", 1, 0, "red"],  ["cell", 2, 1, "red"]]
BLU = [["cell", 0, 1, "blue"], ["cell", 1, 1, "blue"], ["cell", 2, 0, "blue"]]
GRN = [["cell", 0, 0, "green"], ["cell", 1, 1, "green"], ["cell", 2, 0, "green"]]


def trans(dv, cs):
    return [["cell", r + dv[0], c + dv[1], v] for _, r, c, v in cs]


def scene(specs, n=6):
    """specs: list of (base, velocity). n frames, surfaces merged per tick."""
    surfs = [list(b) for b, _ in specs]
    out = []
    for _ in range(n):
        frame = []
        for s in surfs:
            frame += [list(x) for x in s]
        out.append(frame)
        surfs = [trans(v, s) for s, (_, v) in zip(surfs, specs)]
    return out


def boot(enabled):
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    native.load_seed_manifest(manifest_for("depth_axis"), ag)
    if enabled:
        s.set_attr(ag, "depth_infer_enabled", 1.0)
    s.add_node("ShapeSignature", {"name": "base", "signature": json.dumps(RED + BLU),
               "kind": "faculty", "faculty": "base", "dim_types": DT})
    return s, ag, native


def depth_lds(s):
    out = []
    for n in s.nodes("LatentDimension"):
        a = s.node(n)["attrs"]
        if a.get("name") == "latent:depth":
            out.append(dict(n_layers=a.get("n_layers"),
                            velocities=tuple(tuple(v) for v in (a.get("velocities") or ())),
                            ordering=tuple(tuple(o) for o in (a.get("ordering") or ())),
                            window=a.get("window")))
    return out


def run(enabled, frames):
    s, ag, native = boot(enabled)
    o = s.add_node("Observation", {"frames": frames, "dim_types": DT,
                   "status": "depth_seq", "key": ["depth"]})
    s.add_edge(ag, "observed", o)
    native.run_rules()
    at = s.node(o)["attrs"]
    return dict(status=at.get("status"), n_layers=at.get("n_layers"),
                predicted=at.get("predicted"), lds=depth_lds(s))


def ncells(frames):
    return sum(len(f) for f in frames)


def main():
    R = {"engine": provenance_line()}
    ok = {}
    print("ENGINE:", R["engine"])

    # --- H_flat: THE DECISIVE ANTI-FORCED CONTROL — a flat scene mints NOTHING ---
    print("\n[H_flat] flat (one velocity) AND multi-colour-single-velocity -> depth_none, NO mint")
    flat1 = run(True, scene([(RED, (2, 0)), (BLU, (2, 0))]))          # two colours, one velocity
    flat2 = run(True, scene([(RED, (2, 0))]))                          # single surface, one velocity
    ok["H_flat"] = (flat1["status"] == "depth_none" and not flat1["lds"]
                    and flat2["status"] == "depth_none" and not flat2["lds"])
    R["H_flat"] = {"multicolour_one_velocity": flat1["status"], "single_surface": flat2["status"],
                   "lds": flat1["lds"] + flat2["lds"],
                   "report": "no depth dimension shorter than a single generator (provisional)"}
    print(f"  => multicolour1v={flat1['status']} single={flat2['status']} lds={flat1['lds']}  PASS={ok['H_flat']}")
    print("     (a flat plane minting depth would be hallucinating structure -- DISQUALIFYING)")

    # --- H_depth: IDEAL — multi-depth mints latent:depth AND compresses (MDL) ---
    print("\n[H_depth] 2-layer (red (2,0), blue (1,0)) -> latent:depth, 2 layers + MDL compression")
    K = 6
    frames = scene([(RED, (2, 0)), (BLU, (1, 0))], K)
    r = run(True, frames)
    got = r["lds"][0] if len(r["lds"]) == 1 else None
    minted = (got is not None and got["n_layers"] == 2
              and got["velocities"] == ((2, 0), (1, 0))
              and got["ordering"] == (("cell", "red"), ("cell", "blue")))
    # MDL (predicate tokens): WITHOUT depth = enumeration (no single generator carries
    # the scene) = K frames stored; WITH depth = f0 cells + Sum(distinct velocity
    # offsets) + per-surface depth index + 1 dimension.
    nsurf, nf0 = 2, len(frames[0])
    mdl_without = ncells(frames)
    mdl_with = nf0 + (2 + 2) + nsurf + 1   # 2 distinct offsets * 2 coords + 2 indices + 1
    ok["H_depth"] = minted and mdl_with < mdl_without
    R["H_depth"] = {"minted": r["lds"], "status": r["status"],
                    "n_layers_read": got["n_layers"] if got else None,
                    "mdl_without": mdl_without, "mdl_with": mdl_with,
                    "ratio": round(mdl_without / mdl_with, 3)}
    print(f"  => minted={r['lds']}  MDL {mdl_without}->{mdl_with} "
          f"({mdl_without/mdl_with:.2f}x)  PASS={ok['H_depth']}")

    # --- H_multiheld: §13.1 — DIFFERENT structures -> DIFFERENT correct orderings ---
    print("\n[H_multiheld] frozen DepthInfer -> correct DIFFERENT depth ordering per scene")
    scenes = {
        "2-layer[red>blue]": (scene([(RED, (2, 0)), (BLU, (1, 0))]),
                              2, (("cell", "red"), ("cell", "blue"))),
        "3-layer[r>b>g]":    (scene([(RED, (3, 0)), (BLU, (2, 0)), (GRN, (1, 0))]),
                              3, (("cell", "red"), ("cell", "blue"), ("cell", "green"))),
        "reversed[blue>red]": (scene([(RED, (1, 0)), (BLU, (3, 0))]),
                               2, (("cell", "blue"), ("cell", "red"))),
        "dedup[3surf,2vel]":  (scene([(RED, (3, 0)), (BLU, (3, 0)), (GRN, (1, 0))]),
                               2, None),  # ordering not pinned for the shared-velocity pair
    }
    mh = {}; orderings = set()
    for name, (fr, exp_layers, exp_order) in scenes.items():
        r = run(True, fr)
        got = r["lds"][0] if len(r["lds"]) == 1 else None
        layers_ok = got is not None and got["n_layers"] == exp_layers
        order_ok = (exp_order is None) or (got is not None and got["ordering"] == exp_order)
        correct = layers_ok and order_ok
        if got:
            orderings.add(got["ordering"])
        mh[name] = {"expected_layers": exp_layers, "got_layers": got["n_layers"] if got else None,
                    "expected_order": exp_order, "got_order": got["ordering"] if got else None,
                    "correct": correct}
        print(f"  {name:20} -> layers={got['n_layers'] if got else None} "
              f"order={got['ordering'] if got else None}  CORRECT={correct}")
    # different structures must yield different orderings (not same-regardless = forced)
    ok["H_multiheld"] = all(v["correct"] for v in mh.values()) and len(orderings) >= 3
    R["H_multiheld"] = mh
    print(f"  => all correct AND >=3 distinct orderings: {ok['H_multiheld']}")

    # --- H_shuffle: THE FLOOR — random shuffles, longest window K=8, 0 spurious ---
    print("\n[H_shuffle] random shuffles (seeds 27100-27499), LONGEST window K=8; gate: 0 spurious mints")
    K8 = 8
    base_scenes = {
        "2-layer": scene([(RED, (2, 0)), (BLU, (1, 0))], K8),
        "3-layer": scene([(RED, (3, 0)), (BLU, (2, 0)), (GRN, (1, 0))], K8),
    }
    spurious = 0; reversals = 0; originals = 0; examples = []
    seed = 27100
    for kind, ob in base_scenes.items():
        for _ in range(200):
            random.seed(seed); seed += 1
            sh = [list(f) for f in ob]; random.shuffle(sh)
            r = run(True, sh)
            if r["lds"]:
                if sh == ob:
                    originals += 1
                elif sh == ob[::-1]:
                    reversals += 1     # a reversal is a legitimate depth orbit (negated velocities)
                else:
                    spurious += 1
                    if len(examples) < 3:
                        examples.append((kind, seed - 1, r["lds"]))
    ok["H_shuffle"] = (spurious == 0)
    R["H_shuffle"] = {"n": 400, "window": K8, "spurious_mints": spurious,
                      "legitimate_reversals": reversals, "legitimate_originals": originals,
                      "examples": examples,
                      "report": "no multi-velocity constant-motion field found in 400 random "
                                "shuffles at K=8 beyond the original/reversal orbits (provisional)"}
    print(f"  => spurious mints: {spurious} (gate: 0); reversals: {reversals}; originals: {originals}  "
          f"PASS={ok['H_shuffle']}")

    # --- H_downstream: LOAD-BEARING (§1 clause 5 / §13.2) — predict an UNSEEN view ---
    print("\n[H_downstream] minted depth predicts the UNSEEN view at tick K (each surface by its OWN velocity)")
    specs = [(RED, (2, 0)), (BLU, (1, 0))]
    frames6 = scene(specs, 6)          # f0..f5 seen; K=6
    withheld = []
    for b, v in specs:
        withheld += [list(x) for x in trans((v[0] * 6, v[1] * 6), b)]
    withheld = sorted(tuple(x) for x in withheld)
    on = run(True, frames6)
    off = run(False, frames6)
    on_pred = sorted(tuple(x) for x in on["predicted"]) if on["predicted"] else None
    pred_ok = (on_pred == withheld)
    d_mint = len(on["lds"]) - len(off["lds"])
    d_pred = (1 if on["predicted"] else 0) - (1 if off["predicted"] else 0)
    ok["H_downstream"] = pred_ok and len(on["lds"]) == 1 and not off["lds"] and d_mint > 0 and d_pred > 0
    R["H_downstream"] = {"predicted_matches_withheld_view": pred_ok,
                         "on_lds": on["lds"], "off_lds": off["lds"],
                         "D_mint": d_mint, "D_pred": d_pred}
    print(f"  => predicted==withheld view: {pred_ok}  D_mint={d_mint} D_pred={d_pred}  PASS={ok['H_downstream']}")

    # --- H_offday: §9 — flag OFF is inert ---
    print("\n[H_offday] flag OFF -> multi-depth scene does NOT mint (inert)")
    offd = run(False, scene([(RED, (2, 0)), (BLU, (1, 0))]))
    ok["H_offday"] = (offd["status"] == "depth_seq" and not offd["lds"])
    R["H_offday"] = {"status": offd["status"], "lds": offd["lds"]}
    print(f"  => OFF status={offd['status']} lds={offd['lds']}  PASS={ok['H_offday']}")

    # --- cardinality audit: no hardcoded frame/layer count in a decision path ---
    # n_layers is read from the graph attr the RULE set (Count of distinct velocities);
    # window is read from the Term. Verified here by reading them back, never asserting a literal.
    R["cardinality"] = {"n_layers_read_from_graph": R["H_depth"]["n_layers_read"],
                        "window_read_from_graph": R["H_depth"]["minted"][0]["window"] if R["H_depth"]["minted"] else None}

    R["verdict"] = ok
    passed = all(ok.values())
    R["depth_is_inferred_dimension"] = passed
    print("\n" + "=" * 68)
    for k, v in ok.items():
        print(f"  {k:16} {'PASS' if v else 'FAIL'}")
    print(f"  DEPTH IS AN INFERRED DIMENSION (monocular, discrete integer-velocity class): {passed}")
    print("=" * 68)

    json.dump(R, open("results/depth_measure.json", "w"), indent=1, default=str)
    print("wrote results/depth_measure.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
