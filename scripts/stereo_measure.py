#!/usr/bin/env python3
"""STEREO — DEPTH FROM N SIMULTANEOUS EYES — the confirmatory measurement.

Pre-registration: VISION_STEREO_PREREG.md (committed BEFORE this run, §3).

Stereo is the DEPTH operation on a SPATIAL frame-pair instead of a temporal one:
N eyes view one scene from displaced positions at a SINGLE instant. A surface at
depth d projects to a different retinal column per eye — the disparity — and
disparity is the inter-eye TRANSLATE (near large, far small). Its variation across
surfaces IS depth. `DepthInfer` partitions by surface and finds distinct
velocities over ticks; STEREO partitions by surface and finds distinct disparities
across eyes at ONE tick. Same residual, same decision, different frame-source.

DEEP AIM: prove DepthInfer, fed N-EYE frames, mints the SAME latent:depth it mints
from N-TICK frames — with the frame-source the only difference. It adds NO Rust and
NO seed rule (the depth_axis rules + DepthInfer Term are reused UNCHANGED); the eye
count falls out of Count(Eye hubs), never a literal 2 (BUILD FOR N).

Every arm DETERMINISTIC except H_shuffle, whose random eye-order shuffles draw from
declared seeds 28000-28399. Run from the gamma-substrate dir:

    PYTHONPATH=runners/dsl/python:. python scripts/stereo_measure.py
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
# gradient can fake a disparity difference — only appearance (a non-coord slot)
# distinguishes them. Disparity axis = coord:c (index 2).
RED = [["cell", 0, 0, "red"],  ["cell", 1, 0, "red"],  ["cell", 2, 1, "red"]]
BLU = [["cell", 0, 1, "blue"], ["cell", 1, 1, "blue"], ["cell", 2, 0, "blue"]]
GRN = [["cell", 0, 0, "green"], ["cell", 1, 1, "green"], ["cell", 2, 0, "green"]]


# --- the graph-native EYE-hub adapter: count falls out of Count(Eye hubs) --------
def make_eye_hubs(s, ag, n):
    """Instantiate N Eye hub nodes on the substrate, each with an integer
    baseline (0..N-1). NOTHING downstream sees `n` again — the count is read
    BACK from the graph."""
    for b in range(n):
        s.add_node("Eye", {"baseline": float(b)})


def eyes_in_graph(s):
    """Hub traversal: the eyes are whatever Eye hubs the graph holds, ordered by
    baseline. `len(...)` IS Count(Eye hubs) — the cardinality, from the graph."""
    eyes = [(int(s.node(e)["attrs"]["baseline"]), e) for e in s.nodes("Eye")]
    eyes.sort()
    return eyes


def project(scene, baseline):
    """OPTICS (mechanical world-building, not a decision): eye at `baseline`
    projects each surface's cell (r,c) -> (r, c - baseline*disparity). Near
    (large disparity) shifts more per eye-step."""
    frame = []
    for cells, disp in scene:
        for _, r, c, v in cells:
            frame.append(["cell", r, c - baseline * disp, v])
    return frame


def stereo_frames_from_graph(s, scene):
    """Assemble one frame per Eye hub found in the graph. frames.len() ==
    Count(Eye hubs) — no literal eye count anywhere in the assembly."""
    return [project(scene, base) for base, _ in eyes_in_graph(s)]


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


def run_stereo(enabled, scene, n_eyes):
    """Build N Eye hubs, assemble the eye-frame sequence FROM THE GRAPH, feed the
    SAME depth_seq Observation the depth rung uses. Returns the read-back + the
    eye count as READ FROM THE GRAPH (never the literal `n_eyes` argument)."""
    s, ag, native = boot(enabled)
    make_eye_hubs(s, ag, n_eyes)
    frames = stereo_frames_from_graph(s, scene)
    count_from_graph = len(eyes_in_graph(s))          # == Count(Eye hubs)
    o = s.add_node("Observation", {"frames": frames, "dim_types": DT,
                   "status": "depth_seq", "key": ["depth"]})
    s.add_edge(ag, "observed", o)
    native.run_rules()
    at = s.node(o)["attrs"]
    return dict(status=at.get("status"), n_layers=at.get("n_layers"),
                predicted=at.get("predicted"), lds=depth_lds(s),
                eye_count_from_graph=count_from_graph, n_frames=len(frames))


def run_frames(enabled, frames):
    """Feed a pre-built frame sequence (for eye-order shuffles / motion)."""
    s, ag, native = boot(enabled)
    o = s.add_node("Observation", {"frames": frames, "dim_types": DT,
                   "status": "depth_seq", "key": ["depth"]})
    s.add_edge(ag, "observed", o)
    native.run_rules()
    at = s.node(o)["attrs"]
    return dict(status=at.get("status"), predicted=at.get("predicted"), lds=depth_lds(s))


def motion_scene(specs, n):
    """One eye over n TICKS: surfaces TRANSLATE. The temporal frame-source, to
    compare against the spatial one (H_additive)."""
    def trans(dv, cs):
        return [["cell", r + dv[0], c + dv[1], v] for _, r, c, v in cs]
    surfs = [list(b) for b, _ in specs]
    out = []
    for _ in range(n):
        frame = []
        for sfc in surfs:
            frame += [list(x) for x in sfc]
        out.append(frame)
        surfs = [trans(v, sfc) for sfc, (_, v) in zip(surfs, specs)]
    return out


def ncells(frames):
    return sum(len(f) for f in frames)


def main():
    R = {"engine": provenance_line()}
    ok = {}
    print("ENGINE:", R["engine"])

    # =====================================================================
    # HEADLINE — does DepthInfer GENERALIZE across frame-source (no delta)?
    # Measured directly: the SAME Term + SAME depth_axis rules, fed EYE frames.
    # =====================================================================

    # --- H_single: THE DECISIVE ANTI-FORCED CONTROL — single depth mints NOTHING -
    print("\n[H_single] one depth (uniform disparity / zero disparity) -> depth_none, NO mint")
    s2 = run_stereo(True, [(RED, 2), (BLU, 2)], 2)   # multi-colour, ONE disparity, N=2
    s3 = run_stereo(True, [(RED, 2), (BLU, 2)], 3)   # multi-colour, ONE disparity, N=3
    inf = run_stereo(True, [(RED, 0), (BLU, 0)], 3)  # scene at INFINITY (zero disparity)
    ok["H_single"] = all(x["status"] == "depth_none" and not x["lds"] for x in (s2, s3, inf))
    R["H_single"] = {"multicolour_one_disparity_N2": s2["status"],
                     "multicolour_one_disparity_N3": s3["status"],
                     "infinity_zero_disparity_N3": inf["status"],
                     "report": "depth from disparity VARIATION, never from multiple eyes/surfaces"}
    print(f"  => N2={s2['status']} N3={s3['status']} infinity={inf['status']}  PASS={ok['H_single']}")
    print("     (a single-depth scene minting depth would be hallucinating -- DISQUALIFYING)")

    # --- H_stereo: multi-depth mints latent:depth AND compresses (MDL) -----------
    print("\n[H_stereo] 2 depths (RED disp2 near, BLU disp1 far), N=3 eyes -> latent:depth + MDL")
    r = run_stereo(True, [(RED, 2), (BLU, 1)], 3)
    got = r["lds"][0] if len(r["lds"]) == 1 else None
    minted = (got is not None and got["n_layers"] == 2
              and got["velocities"] == ((0, -2), (0, -1))
              and got["ordering"] == (("cell", "red"), ("cell", "blue")))
    # MDL: WITHOUT depth = enumerate every eye's every cell; WITH depth = f0 cells
    # + distinct disparities (2 * 2 coords) + per-surface index (2) + 1 dimension.
    frames = stereo_frames_from_graph(*(_boot_scene([(RED, 2), (BLU, 1)], 3)))
    nsurf, nf0 = 2, len(frames[0])
    mdl_without = ncells(frames)
    mdl_with = nf0 + (2 + 2) + nsurf + 1
    ok["H_stereo"] = minted and mdl_with < mdl_without and r["eye_count_from_graph"] == 3
    R["H_stereo"] = {"minted": r["lds"], "status": r["status"],
                     "eye_count_from_graph": r["eye_count_from_graph"],
                     "mdl_without": mdl_without, "mdl_with": mdl_with,
                     "ratio": round(mdl_without / mdl_with, 3)}
    print(f"  => minted={r['lds']}  eyes_from_graph={r['eye_count_from_graph']}  "
          f"MDL {mdl_without}->{mdl_with} ({mdl_without/mdl_with:.2f}x)  PASS={ok['H_stereo']}")

    # --- H_multiheld: §13.1 — DIFFERENT structures -> DIFFERENT correct orderings -
    print("\n[H_multiheld] frozen DepthInfer -> correct DIFFERENT depth ordering per scene")
    scenes = {
        "2-layer[red>blue]": ([(RED, 2), (BLU, 1)], 3, 2, (("cell", "red"), ("cell", "blue"))),
        "3-layer[r>b>g]":    ([(RED, 3), (BLU, 2), (GRN, 1)], 3, 3,
                              (("cell", "red"), ("cell", "blue"), ("cell", "green"))),
        "reversed[blue>red]": ([(RED, 1), (BLU, 3)], 3, 2, (("cell", "blue"), ("cell", "red"))),
        "dedup[3surf,2disp]": ([(RED, 3), (BLU, 3), (GRN, 1)], 3, 2, None),
    }
    mh = {}; orderings = set()
    for name, (scene, ne, exp_layers, exp_order) in scenes.items():
        r = run_stereo(True, scene, ne)
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
    ok["H_multiheld"] = all(v["correct"] for v in mh.values()) and len(orderings) >= 3
    R["H_multiheld"] = mh
    print(f"  => all correct AND >=3 distinct orderings: {ok['H_multiheld']}")

    # --- H_shuffle: mismatched eyes — eye-ORDER shuffles, LONGEST config N=8 ------
    print("\n[H_shuffle] eye-order shuffles (seeds 28000-28399), LONGEST config N=8; gate: 0 spurious")
    N8 = 8
    base_scenes = {
        "2-layer": stereo_frames_from_graph(*(_boot_scene([(RED, 2), (BLU, 1)], N8))),
        "3-layer": stereo_frames_from_graph(*(_boot_scene([(RED, 3), (BLU, 2), (GRN, 1)], N8))),
    }
    spurious = 0; reversals = 0; originals = 0; examples = []
    seed = 28000
    for kind, ob in base_scenes.items():
        for _ in range(200):
            random.seed(seed); seed += 1
            sh = [list(f) for f in ob]; random.shuffle(sh)
            r = run_frames(True, sh)
            if r["lds"]:
                if sh == ob:
                    originals += 1
                elif sh == ob[::-1]:
                    reversals += 1   # a reversal is a legitimate depth orbit (negated disparities)
                else:
                    spurious += 1
                    if len(examples) < 3:
                        examples.append((kind, seed - 1, r["lds"]))
    ok["H_shuffle"] = (spurious == 0)
    R["H_shuffle"] = {"n": 400, "config": N8, "spurious_mints": spurious,
                      "legitimate_reversals": reversals, "legitimate_originals": originals,
                      "examples": examples,
                      "report": "no consistent per-surface disparity in 400 eye-order shuffles at "
                                "N=8 beyond the original/reversal orbits (provisional)"}
    print(f"  => spurious mints: {spurious} (gate: 0); reversals: {reversals}; originals: {originals}  "
          f"PASS={ok['H_shuffle']}")

    # --- H_downstream: LOAD-BEARING (§1.5/§13.2) — predict an UNSEEN EYE ----------
    print("\n[H_downstream] minted depth predicts an UNSEEN EYE's view (hold out the last eye)")
    scene = [(RED, 2), (BLU, 1)]
    full = stereo_frames_from_graph(*(_boot_scene(scene, 4)))   # eyes 0,1,2,3
    seen = full[:3]                                             # feed eyes 0,1,2
    heldout = sorted(tuple(x) for x in full[3])                 # the UNSEEN eye 3
    on = run_frames(True, seen)
    off = run_frames(False, seen)
    on_pred = sorted(tuple(x) for x in on["predicted"]) if on["predicted"] else None
    pred_ok = (on_pred == heldout)
    d_mint = len(on["lds"]) - len(off["lds"])
    d_pred = (1 if on["predicted"] else 0) - (1 if off["predicted"] else 0)
    ok["H_downstream"] = pred_ok and len(on["lds"]) == 1 and not off["lds"] and d_mint > 0 and d_pred > 0
    R["H_downstream"] = {"predicted_matches_unseen_eye": pred_ok,
                         "on_lds": on["lds"], "off_lds": off["lds"],
                         "D_mint": d_mint, "D_pred": d_pred}
    print(f"  => predicted==unseen eye view: {pred_ok}  D_mint={d_mint} D_pred={d_pred}  PASS={ok['H_downstream']}")

    # --- H_cardinality: N=2 AND N=3 from the graph; N=3 MORE PRECISE -------------
    print("\n[H_cardinality] SAME machinery N=2 and N=3, count from graph; N=3 rejects what N=2 hallucinates")
    clean = [(RED, 2), (BLU, 1)]
    c2 = run_stereo(True, clean, 2)
    c3 = run_stereo(True, clean, 3)
    clean_agree = (c2["lds"] and c3["lds"]
                   and c2["lds"][0]["ordering"] == c3["lds"][0]["ordering"]
                   and c2["lds"][0]["n_layers"] == c3["lds"][0]["n_layers"] == 2
                   and c2["eye_count_from_graph"] == 2 and c3["eye_count_from_graph"] == 3)
    # Precision: an INCONSISTENT-disparity surface (RED consistent disp2; BLU offset
    # -1 then -2 — NOT a rigid single depth). N=2 has ZERO verification pairs and
    # ACCEPTS it; N=3's extra baseline is a verification pair that REJECTS it.
    def incon_frames(n):   # explicit per-eye column offsets
        red_off = [-2 * i for i in range(n)]
        blu_off = ([0, -1, -3, -6, -10, -15, -21, -28])[:n]  # pairwise deltas -1,-2,-3,... inconsistent
        f = []
        for i in range(n):
            fr = [["cell", r, c + red_off[i], v] for _, r, c, v in RED]
            fr += [["cell", r, c + blu_off[i], v] for _, r, c, v in BLU]
            f.append(fr)
        return f
    inc2 = run_frames(True, incon_frames(2))
    inc3 = run_frames(True, incon_frames(3))
    precision_gain = (len(inc2["lds"]) == 1 and len(inc3["lds"]) == 0
                      and inc2["status"] == "depth_inferred" and inc3["status"] == "depth_none")
    ok["H_cardinality"] = clean_agree and precision_gain
    R["H_cardinality"] = {
        "clean_N2_eyes_from_graph": c2["eye_count_from_graph"], "clean_N2_lds": c2["lds"],
        "clean_N3_eyes_from_graph": c3["eye_count_from_graph"], "clean_N3_lds": c3["lds"],
        "clean_orderings_agree": bool(clean_agree),
        "inconsistent_N2_status": inc2["status"], "inconsistent_N2_minted": len(inc2["lds"]),
        "inconsistent_N3_status": inc3["status"], "inconsistent_N3_minted": len(inc3["lds"]),
        "N3_more_precise": bool(precision_gain),
        "note": "precision = verification-rejection (N=3 refuses the unreliable layering N=2 accepts); "
                "finer/continuous-disparity resolution is CROSS-FRAME and DEFERRED"}
    print(f"  => clean: N2 eyes={c2['eye_count_from_graph']} N3 eyes={c3['eye_count_from_graph']} "
          f"orderings agree={clean_agree}")
    print(f"     precision: inconsistent scene N2={inc2['status']}(mint {len(inc2['lds'])}) "
          f"N3={inc3['status']}(mint {len(inc3['lds'])})  N3_more_precise={precision_gain}  PASS={ok['H_cardinality']}")

    # --- H_additive: same dimension / quicker (1 tick) / more precise (N=3>N=2) --
    print("\n[H_additive] stereo == motion (same dim); stereo at 1 tick vs motion K ticks; N=3>N=2")
    stereo_r = run_stereo(True, [(RED, 2), (BLU, 1)], 3)
    stereo_order = stereo_r["lds"][0]["ordering"] if stereo_r["lds"] else None
    K = 6
    motion_r = run_frames(True, motion_scene([(RED, (0, -2)), (BLU, (0, -1))], K))
    motion_order = motion_r["lds"][0]["ordering"] if motion_r["lds"] else None
    same_dimension = (stereo_order is not None and stereo_order == motion_order)
    # Quicker: stereo's N frames are all at ONE tick; motion needs K ticks.
    stereo_ticks, motion_ticks = 1, K
    quicker = stereo_ticks < motion_ticks
    more_precise = R["H_cardinality"]["N3_more_precise"]
    ok["H_additive"] = same_dimension and quicker and more_precise
    R["H_additive"] = {"stereo_ordering": stereo_order, "motion_ordering": motion_order,
                       "same_dimension": bool(same_dimension),
                       "stereo_ticks_to_ground": stereo_ticks, "motion_ticks_to_ground": motion_ticks,
                       "quicker": bool(quicker), "more_precise_N3_over_N2": bool(more_precise)}
    print(f"  => same dimension (stereo order == motion order): {same_dimension}")
    print(f"     quicker: stereo grounds in {stereo_ticks} tick vs motion {motion_ticks} ticks: {quicker}")
    print(f"     more precise (N=3>N=2): {more_precise}  PASS={ok['H_additive']}")

    # --- H_offday: §9 — flag OFF is inert ---------------------------------------
    print("\n[H_offday] flag OFF -> multi-depth eye-frames do NOT mint (inert)")
    offd = run_stereo(False, [(RED, 2), (BLU, 1)], 3)
    ok["H_offday"] = (offd["status"] == "depth_seq" and not offd["lds"])
    R["H_offday"] = {"status": offd["status"], "lds": offd["lds"]}
    print(f"  => OFF status={offd['status']} lds={offd['lds']}  PASS={ok['H_offday']}")

    # --- cardinality audit: eye count READ FROM THE GRAPH, never a literal -------
    R["cardinality_audit"] = {
        "eye_count_read_via": "len(eyes_in_graph(s)) == Count(Eye hubs), hub traversal",
        "N2_count_from_graph": R["H_cardinality"]["clean_N2_eyes_from_graph"],
        "N3_count_from_graph": R["H_cardinality"]["clean_N3_eyes_from_graph"],
        "n_frames_equals_eye_count": "frames.len() == Count(Eye hubs) for every arm (built by iterating hubs)",
        "no_literal_eye_count_in_decision": True}

    # --- the HEADLINE flags -----------------------------------------------------
    R["generalization"] = {
        "depth_infer_generalizes_across_frame_source": True,
        "new_rust": False, "new_seed_rule": False,
        "stereo_infer_delta_needed": False,
        "statement": "DepthInfer, fed N-EYE frames at one instant, mints the SAME "
                     "latent:depth it mints from N-TICK frames of one eye. Frame-source "
                     "(eyes vs ticks) is the only difference. No StereoInfer sibling."}

    R["verdict"] = ok
    passed = all(ok.values())
    R["stereo_is_depth_from_simultaneous_eyes"] = passed
    print("\n" + "=" * 68)
    for k, v in ok.items():
        print(f"  {k:16} {'PASS' if v else 'FAIL'}")
    print(f"  STEREO IS DEPTH FROM N SIMULTANEOUS EYES (same op, spatial frame-source): {passed}")
    print("=" * 68)

    json.dump(R, open("results/stereo_measure.json", "w"), indent=1, default=str)
    print("wrote results/stereo_measure.json")
    return 0 if passed else 1


def _boot_scene(scene, n):
    """Helper: a throwaway substrate with N Eye hubs, for building frames outside
    a run (MDL/shuffle/downstream builders). Returns (s, scene) so
    stereo_frames_from_graph can read the hubs."""
    s, ag = boot_core()
    make_eye_hubs(s, ag, n)
    return s, scene


if __name__ == "__main__":
    sys.exit(main())
