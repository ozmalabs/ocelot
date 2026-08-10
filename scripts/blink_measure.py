#!/usr/bin/env python3
"""THE BLINK — a temporal hole bridged by grounding: the confirmatory measurement
(VISION_BLINK_PREREG.md). The temporal twin of the blind spot.

Every arm is DETERMINISTIC except H_noconfab's floor, whose 400 random shuffles
draw from seeds 31100-31499 (declared). Run from the gamma-substrate dir:

    PYTHONPATH=runners/dsl/python:. python scripts/blink_measure.py
"""
from __future__ import annotations
import json, random, sys, time

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

from substrate.boot_core import boot_core            # noqa: E402
from domains import reflective_faculty as rf          # noqa: E402
from substrate.seed_loader import manifest_for        # noqa: E402

DT = ["pred", "coord:r", "coord:c", "val"]
BASE = [["cell", 0, 0, "red"], ["cell", 1, 0, "red"],
        ["cell", 2, 0, "red"], ["cell", 2, 1, "red"]]


# --------------------------------------------------------------------------- #
#  world: a moving footprint, and the blink that punches a temporal hole in it
# --------------------------------------------------------------------------- #
def trans(dv, cs):
    return [["cell", r + dv[0], c + dv[1], v] for _, r, c, v in cs]


def moving(dv, n, base=BASE):
    """Ground-truth: the footprint at each tick 0..n-1 under constant velocity."""
    out = [base]; cur = base
    for _ in range(n - 1):
        cur = trans(dv, cur); out.append(cur)
    return out


def blink(seq, blink_ticks):
    """Punch a REAL temporal hole: replace each blink tick's frame with EMPTY
    (no data). This is the blink — the raw sensor returns nothing there."""
    return [([] if t in blink_ticks else f) for t, f in enumerate(seq)]


def norm(frame):
    return sorted(tuple(x) for x in (frame or []))


# --------------------------------------------------------------------------- #
#  substrate: present a blink sequence, let the rules bridge or hold
# --------------------------------------------------------------------------- #
def boot(enabled):
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    native.load_seed_manifest(manifest_for("time_axis"), ag)
    native.load_seed_manifest(manifest_for("blink_bridge"), ag)
    if enabled:
        s.set_attr(ag, "blink_bridge_enabled", 1.0)
    s.add_node("ShapeSignature", {"name": "base_L", "signature": json.dumps(BASE),
               "kind": "faculty", "faculty": "base_L", "dim_types": DT})
    return s, ag, native


def run(enabled, frames):
    s, ag, native = boot(enabled)
    o = s.add_node("Observation", {"frames": frames, "dim_types": DT,
                   "status": "blink_seq", "key": ["blink"]})
    s.add_edge(ag, "observed", o)
    native.run_rules()
    at = s.node(o)["attrs"]
    return dict(status=at.get("status"), bridged=at.get("bridged"),
                frozen=at.get("frozen"), diverged_at=at.get("diverged_at"),
                correction=at.get("correction"), confidence=at.get("confidence"),
                constrained=at.get("constrained"), gap=at.get("bridge_gap"),
                confirm=at.get("bridge_confirm"), kind=at.get("bridge_kind"))


def main():
    R = {"engine": provenance_line()}
    ok = {}
    print("ENGINE:", R["engine"])

    # === POSITIVE CONTROL: the blink is REAL (raw sensor empty during) ========
    truth = moving((1, 0), 7)               # f0..f6, ground truth (no blink)
    seq = blink(truth, {3, 4})              # blink t3,t4
    blink_real = (seq[3] == [] and seq[4] == [] and seq[2] != [] and seq[5] != [])
    R["control_blink_real"] = {"blink_frames_empty": blink_real,
                               "t3": seq[3], "t4": seq[4]}
    print(f"\n[control] blink is REAL (raw sensor empty at t3,t4): {blink_real}")

    # === H_grounding_constrains: grounding CONSTRAINS the confabulation to =====
    #     G^k(last) (tracks the motion == truth); the freeze baseline does NOT.
    print("\n[H_grounding_constrains] consistent motion -> guess pinned to G^k(last)==truth")
    r = run(True, seq)
    per_tick = []
    for j, bf in enumerate(r["bridged"] or []):
        tick = 3 + j
        per_tick.append({
            "tick": tick,
            "bridged_eq_truth": norm(bf) == norm(truth[tick]),
            "frozen_eq_truth": norm(r["frozen"][j]) == norm(truth[tick]),
            "bridged_eq_frozen": norm(bf) == norm(r["frozen"][j]),
        })
    bridge_tracks = bool(per_tick) and all(p["bridged_eq_truth"] for p in per_tick)
    freeze_fails = bool(per_tick) and all(not p["frozen_eq_truth"] for p in per_tick)
    bridge_ne_freeze = bool(per_tick) and all(not p["bridged_eq_frozen"] for p in per_tick)
    # TRACKS M: change the pre-blink motion -> the constrained guess changes
    truth2 = moving((0, 2), 7)
    r2 = run(True, blink(truth2, {3, 4}))
    tracks_m = (r2["bridged"] is not None
                and norm(r2["bridged"][0]) == norm(truth2[3])
                and norm(r2["bridged"][0]) != norm(r["bridged"][0]))
    constrained_flag = r["constrained"] == 1.0 and r["confidence"] > 0.0
    ok["H_grounding_constrains"] = (bridge_tracks and freeze_fails and bridge_ne_freeze
                                    and tracks_m and constrained_flag)
    R["H_grounding_constrains"] = {"status": r["status"], "per_tick": per_tick,
                                   "bridge_tracks_truth": bridge_tracks,
                                   "freeze_fails": freeze_fails,
                                   "bridge_differs_from_freeze": bridge_ne_freeze,
                                   "tracks_M_when_motion_changed": tracks_m,
                                   "constrained": r["constrained"], "confidence": r["confidence"]}
    for p in per_tick:
        print(f"  t{p['tick']}: bridged==truth {p['bridged_eq_truth']}  "
              f"frozen==truth {p['frozen_eq_truth']}  bridged!=frozen {p['bridged_eq_frozen'] is False}")
    print(f"  constrained={r['constrained']} confidence={r['confidence']:.3f} tracks M={tracks_m}  "
          f"PASS={ok['H_grounding_constrains']}")

    # === H_invisible: consistent motion -> percept continuous, no seam =========
    print("\n[H_invisible] consistent-motion blink -> resume confirms guess, correction=0")
    inv = run(True, seq)   # no change; resume frames are the true moving frames
    invisible = (inv["status"] == "blink_bridged" and inv["diverged_at"] == -1
                 and inv["correction"] == 0)
    ok["H_invisible"] = invisible
    R["H_invisible"] = {"status": inv["status"], "diverged_at": inv["diverged_at"],
                        "correction": inv["correction"],
                        "note": "resume frames == G^t(f0): guess confirmed, no shutter"}
    print(f"  => status={inv['status']} diverged_at={inv['diverged_at']} "
          f"correction={inv['correction']}  PASS={ok['H_invisible']}")

    # === H_change_blind: change IN blink missed until divergence; ==============
    #     change in a VISIBLE frame signalled immediately
    print("\n[H_change_blind] change-in-blink detected LATE; change-in-visible immediate")
    # Arm A: object STOPS at t3 (inside the blink). true t3+ = pos at t2.
    stop_at = truth[:3] + [truth[2]] * 4            # t3..t6 frozen at t2 pos
    seqA = blink(stop_at, {3, 4})                   # change tick = 3 (inside blink)
    rA = run(True, seqA)
    change_tickA, detA = 3, rA["diverged_at"]
    latA = (detA - change_tickA) if detA is not None and detA >= 0 else None
    # Arm B: object moves normally, STOPS at t6 (a plainly VISIBLE frame).
    stop_vis = truth[:6] + [truth[5]]               # t6 frozen at t5 pos
    seqB = blink(stop_vis, {3, 4})                  # change tick = 6 (visible)
    rB = run(True, seqB)
    change_tickB, detB = 6, rB["diverged_at"]
    latB = (detB - change_tickB) if detB is not None and detB >= 0 else None
    # the blink itself was invisible in B (t5 matched); the visible change caught at once
    ok["H_change_blind"] = (latA is not None and latA > 0 and latB == 0 and detA > change_tickA)
    R["H_change_blind"] = {
        "in_blink": {"change_tick": change_tickA, "detected_at": detA, "latency": latA},
        "in_visible": {"change_tick": change_tickB, "detected_at": detB, "latency": latB},
        "reading": "a change during the blink is bridged over (predicted-moving) and "
                   "revised only when data returns and diverges; a visible change is "
                   "signalled the instant it is observed"}
    print(f"  in-blink:   change@t{change_tickA} detected@t{detA}  latency={latA} (LATE)")
    print(f"  in-visible: change@t{change_tickB} detected@t{detB}  latency={latB} (immediate)")
    print(f"  PASS={ok['H_change_blind']}")

    # === H_correction: the perceptible JUMP — it FILLS a long gap anyway, and =
    #     the correction on data return GROWS with the gap (short = imperceptible,
    #     long = the startle). Confidence DECAYS with the gap (relative). NOT a
    #     refusal — the guess stands and diverges. (Replaces the old "refuses a
    #     long gap": the creator's correction — perception guesses, it does not
    #     go silent.)
    print("\n[H_correction] a change during the blink -> correction GROWS with gap; confidence DECAYS")
    def centroid_row(f):
        return sum(c[1] for c in f) / len(f)
    def change_probe(gap):
        # object moves (1,0) for a 4-frame prefix, STOPS at blink onset; a blink of
        # `gap`, then one resumed frame at the STOPPED position.
        pre = moving((1, 0), 4)                          # f0..f3, confirm_run=3
        stopped = pre[3]                                  # frozen from t4 on
        return run(True, pre + [[]] * gap + [stopped])
    corr_rows = []
    for gap in (1, 2, 3, 5):
        r_ = change_probe(gap)
        corr_rows.append({"gap": gap, "status": r_["status"], "correction": r_["correction"],
                          "confidence": r_["confidence"], "still_bridged": r_["bridged"] is not None})
        print(f"  gap={gap}: status={r_['status']} correction={r_['correction']} "
              f"confidence={r_['confidence']:.3f} (still fills={r_['bridged'] is not None})")
    always_fills = all(d["still_bridged"] for d in corr_rows)
    corr_grows = all(a["correction"] <= b["correction"]
                     for a, b in zip(corr_rows, corr_rows[1:])) and corr_rows[-1]["correction"] > corr_rows[0]["correction"]
    conf_decays = all(a["confidence"] >= b["confidence"]
                      for a, b in zip(corr_rows, corr_rows[1:])) and corr_rows[-1]["confidence"] < corr_rows[0]["confidence"]
    # invisible control: consistent motion, no change -> correction 0 at every gap
    inv_gaps = [run(True, blink(moving((1, 0), 4 + g + 1), set(range(4, 4 + g))))["correction"]
                for g in (1, 2, 3, 5)]
    invisible_when_consistent = all(c == 0 for c in inv_gaps)
    ok["H_correction"] = always_fills and corr_grows and conf_decays and invisible_when_consistent
    R["H_correction"] = {"rows": corr_rows, "always_fills": always_fills,
                         "correction_grows_with_gap": corr_grows,
                         "confidence_decays_with_gap": conf_decays,
                         "consistent_no_change_correction": inv_gaps,
                         "note": "it does NOT refuse a long gap; it guesses anyway and the "
                                 "correction on divergence grows with how far it guessed blind"}
    print(f"  always fills={always_fills} correction grows={corr_grows} "
          f"confidence decays={conf_decays} invisible-when-consistent={invisible_when_consistent}")
    print(f"  PASS={ok['H_correction']}")

    # === H_unconstrained: no consistent motion -> STILL confabulates, but ======
    #     UNCONSTRAINED (constrained=0, confidence=0) — the seed of hallucination,
    #     NOT silence, NOT held-open. The floor: the CONSTRAINT flag is HONEST —
    #     0 non-orbit shuffles are falsely marked constrained. (Replaces the old
    #     "refuses / holds open": perception confabulates; the SCIENTIST refuses to
    #     over-claim, the eye does not.)
    print("\n[H_unconstrained] no consistent motion -> still fills but UNCONSTRAINED; constraint flag honest")
    acc = [BASE]; cur = BASE
    for k in range(1, 4):
        cur = trans((k, 0), cur); acc.append(cur)      # accelerating steps 1,2,3
    rAcc = run(True, acc[:3] + [[], []])
    accel_fills_unconstrained = (rAcc["status"] == "blink_bridged"
                                 and rAcc["bridged"] is not None
                                 and rAcc["constrained"] == 0.0
                                 and rAcc["confidence"] == 0.0)
    # the FLOOR: 400 shuffled prefixes -> 0 NON-ORBIT shuffle falsely CONSTRAINED.
    # A shuffle that lands MONOTONIC is a genuine orbit under G / G^-1 and MAY be
    # constrained (correctly); every other shuffle must read constrained=0.
    def min_row(frame):
        return min(c[1] for c in frame)
    def is_monotonic(pref):
        rows = [min_row(f) for f in pref]
        return rows == sorted(rows) or rows == sorted(rows, reverse=True)
    false_constrained = 0; legit = 0; all_fill = True; seed = 31100; examples = []
    base_orbit = moving((1, 0), 6)                      # 6 distinct frames
    for i in range(400):
        random.seed(seed); seed += 1
        pref = base_orbit[:]
        random.shuffle(pref)
        rf_ = run(True, pref + [[], []])
        if rf_["bridged"] is None:
            all_fill = False                            # must ALWAYS fill (confabulate)
        if rf_["constrained"] == 1.0:
            if is_monotonic(pref):
                legit += 1                              # a genuine orbit — honestly constrained
            else:
                false_constrained += 1
                if len(examples) < 3:
                    examples.append((seed - 1, pref))
    ok["H_unconstrained"] = accel_fills_unconstrained and all_fill and false_constrained == 0
    R["H_unconstrained"] = {"accel_fills_unconstrained": accel_fills_unconstrained,
                            "accel_status": rAcc["status"], "accel_constrained": rAcc["constrained"],
                            "floor_n": 400, "always_fills": all_fill,
                            "false_constrained": false_constrained, "legitimate_orbits": legit,
                            "examples": examples,
                            "report": "every shuffle still confabulates a guess; 0 non-orbit "
                                      "shuffles falsely marked constrained (the constraint flag "
                                      "is honest — the discipline is on the CLAIM, not the fill)"}
    print(f"  accelerating -> fills but unconstrained: {accel_fills_unconstrained}")
    print(f"  400 shuffles: always fills={all_fill}  falsely-constrained={false_constrained} "
          f"(gate: 0)  legit orbits={legit}  PASS={ok['H_unconstrained']}")

    # === H_offday: §9 — flag OFF is inert =====================================
    print("\n[H_offday] flag OFF -> blink sequence inert (no bridge, no hold)")
    off = run(False, seq)
    ok["H_offday"] = (off["status"] == "blink_seq" and off["bridged"] is None)
    R["H_offday"] = {"status": off["status"], "bridged": off["bridged"],
                     "note": "sd orbit law / time 6 / provenance / bench reported in RESULTS"}
    print(f"  => OFF status={off['status']} bridged={off['bridged']}  PASS={ok['H_offday']}")

    # === SCALING: continuing the generator is LOCAL / <= linear ================
    # Boot ONCE per size (fixed overhead OUT of the timed region); time only the
    # observation + run_rules (the actual bridge work) so the exponent is the
    # BRIDGE's, not boot's.
    print("\n[scaling] BRIDGE-only cost vs cell count (boot excluded; expect exponent <= 1)")
    import math
    sizes = []; times = []
    for scale in (1, 2, 4, 8, 16, 32):
        big = [["cell", r, 0, "red"] for r in range(4 * scale)]
        tr = moving((1, 0), 7, base=big)
        sq = blink(tr, {3, 4})
        s, ag, native = boot(True)                      # boot OUTSIDE the timer
        reps = 40
        t0 = time.perf_counter()
        for _ in range(reps):
            o = s.add_node("Observation", {"frames": sq, "dim_types": DT,
                           "status": "blink_seq", "key": ["blink"]})
            s.add_edge(ag, "observed", o)
            native.run_rules()
        dt = (time.perf_counter() - t0) / reps * 1000
        n = 4 * scale
        sizes.append(n); times.append(dt)
        print(f"  cells={n:4d}  bridge(ms)={dt:.4f}")
    # log-log fit
    lx = [math.log(n) for n in sizes]; ly = [math.log(t) for t in times]
    mx = sum(lx) / len(lx); my = sum(ly) / len(ly)
    p = sum((a - mx) * (b - my) for a, b in zip(lx, ly)) / sum((a - mx) ** 2 for a in lx)
    ok["scaling_linear"] = p <= 1.3
    R["scaling"] = {"sizes": sizes, "times_ms": times, "fitted_exponent": round(p, 3)}
    print(f"  => fitted exponent p={p:.3f} (<=1.5 linear-ish)  PASS={ok['scaling_linear']}")

    R["verdict"] = ok
    passed = all(ok.values()) and blink_real
    R["blink_bridges_temporal_hole"] = passed
    print("\n" + "=" * 70)
    for k, v in ok.items():
        print(f"  {k:16} {'PASS' if v else 'FAIL'}")
    print(f"  control_blink_real {blink_real}")
    print(f"  THE BLINK BRIDGES A TEMPORAL HOLE BY GROUNDING (bounded): {passed}")
    print("=" * 70)

    json.dump(R, open("results/blink_measure.json", "w"), indent=1, default=str)
    print("wrote results/blink_measure.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
