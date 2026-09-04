"""H-L2 — LOG-RATIO COMPOSITION (synthetic): a DIFFERENCE of two log-quanta is
an integer log-ratio that RatioInduce consumes.

PREREG H-L2: quantities related by a multiplicative factor `f` emit log-quanta
differing by the constant integer `round(log_a(f)/Δ)`, so a population of frames
differing by a per-frame MULTIPLICATIVE scale becomes a population of
integer-coordinate frames differing by a per-frame ADDITIVE log-offset that
RatioInduce factors. CONFIRMED iff, on a synthetic population with planted
per-frame multiplicative scales, emitting log-quanta then running RatioInduce
recovers the invariant AND factors the per-frame scale — the reasoning-layer
analogue of RATIO_INVARIANCE H-R1, now VIA THE EMITTER instead of raw integer
extents.

THE SHAPE (why the emitter is the bridge). RatioInduce reads the ORIGIN-
NORMALIZED EXTENT (max − min) of each coord slot and finds the cross-coordinate
extent ratio fixed across the population. On the LOG AXIS the emitter builds:
  * within one frame, the log-quanta on an axis span an integer EXTENT;
  * a per-frame MULTIPLICATIVE scale `s_f` on the underlying LINEAR quantities
    becomes a per-frame ADDITIVE log-offset (log(s_f·x) = log s_f + log x), which
    shifts every quantum on that frame's axis by the SAME integer and therefore
    CANCELS in the extent (a difference) — exactly the common-mode nuisance a
    ratio is built to cancel;
  * the cross-AXIS log-extent ratio (y-log-extent : x-log-extent) is the planted
    invariant, and it is what survives.
So a whole multiplicative-scale FAMILY collapses to one held ratio, recovered by
RatioInduce from the EMITTER'S integer output — no raw integer extents handed in.

DISCIPLINE (the emitter/op are NOT handed the answer):
  * The harness plants the linear values and per-frame scales; the emitter
    receives only the raw (float) linear readings, the op only the emitted
    integer quanta. Neither is told the ratio or the scales.
  * A DIRECT log-quantum-DIFFERENCE check (two quantities differing by a fixed
    multiplicative f across frames emit quanta differing by the CONSTANT integer
    round(log_a f / Δ)) is asserted independently of RatioInduce, as the literal
    statement of H-L2.
  * NEGATIVE CONTROL: a population whose per-axis multiplicative structure is
    NOT a single common scale (independent per-axis stretch) must come back
    explained=false after emission — the honest MDL floor survives the emitter.

Run:  PYTHONPATH=. python3 drafts/log_quantum/hl2_synthetic.py
"""
from __future__ import annotations

import json
import math
import random

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

from substrate.boot_core import boot_core          # noqa: E402
from domains import reflective_faculty as rf        # noqa: E402

DIM_TYPES = ["pred", "coord:x", "coord:y", "val"]
XSLOT, YSLOT = 1, 2


def boot():
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    s.add_node("ShapeSignature", {
        "name": "frame_probe",
        "signature": json.dumps([["cell", 0, 0, 1]]),
        "kind": "faculty", "faculty": "frame_probe",
        "dim_types": list(DIM_TYPES),
    })
    return s, ag, native


def emit(native, frames, slot, *, base_num, base_den=1, delta_num=1, delta_den=1, raw=True):
    return native.evaluate(
        {"type": "LogQuantum",
         "population": {"type": "Lit", "value": frames},
         "value_slot": slot,
         "base_num": base_num, "base_den": base_den,
         "delta_num": delta_num, "delta_den": delta_den,
         "raw": raw, "field": ""},
        {})


def emit_both_axes(native, frames, *, base_num, base_den=1, delta_num=1, delta_den=1):
    """Quantize BOTH the x and y linear values of every relation to integer
    log-quanta (two LogQuantum passes, one per axis) — the emitter output is an
    all-integer population ready for RatioInduce."""
    step1 = list(emit(native, frames, XSLOT, base_num=base_num, base_den=base_den,
                      delta_num=delta_num, delta_den=delta_den, raw=True))
    step1 = [[list(r) for r in f] for f in step1]
    step2 = list(emit(native, step1, YSLOT, base_num=base_num, base_den=base_den,
                      delta_num=delta_num, delta_den=delta_den, raw=True))
    return [[list(r) for r in f] for f in step2]


def induce(native, frames, resolution=0):
    return native.evaluate(
        {"type": "RatioInduce",
         "population": {"type": "Lit", "value": frames},
         "resolution": resolution, "field": ""},
        {})


def parse_ratios(out):
    flat = list(out.get("ratios") or ())
    triples = [tuple(flat[i:i + 3]) for i in range(0, len(flat), 3)]
    return {int(s): (int(n), int(d)) for (s, n, d) in triples}


def make_linear_frame(scale_f, x_span_pow, y_span_pow, base, seed):
    """A frame of LINEAR (float) readings. Along x the values run from base^0 to
    base^x_span_pow (a geometric progression -> AFTER log, an integer extent of
    x_span_pow); along y from base^0 to base^y_span_pow (log-extent y_span_pow).
    EVERY linear value is multiplied by the per-frame scale `scale_f` (a
    MULTIPLICATIVE per-frame nuisance -> an ADDITIVE log-offset that the extent
    cancels). Interior points are random geometric fill (do not change extent).
    """
    rng = random.Random(seed)
    xs_pow = {0, x_span_pow}
    ys_pow = {0, y_span_pow}
    for _ in range(4):
        xs_pow.add(rng.randint(0, x_span_pow))
        ys_pow.add(rng.randint(0, y_span_pow))
    rels = []
    # a small grid: pair the corner powers so extents are well defined on both axes
    pts = sorted({(px, py) for px in sorted(xs_pow) for py in sorted(ys_pow)})
    for (px, py) in pts:
        xlin = scale_f * (base ** px)
        ylin = scale_f * (base ** py)
        rels.append(["cell", float(xlin), float(ylin), 1])
    return rels


def main():
    print("ENGINE:", provenance_line())
    print("=" * 72)
    print("H-L2  LOG-RATIO COMPOSITION — emit log-quanta, RatioInduce factors scale")
    print("=" * 72)
    s, ag, native = boot()

    # ============================================================
    # (A) THE LITERAL H-L2 STATEMENT: a fixed multiplicative factor f between two
    #     quantities emits log-quanta differing by the CONSTANT integer
    #     round(log_a f / Δ), across frames with random per-frame scales.
    # ============================================================
    print("\n(A) DIRECT log-quantum difference == round(log_a f / Δ) (constant across frames):")
    base = 2
    f = 8               # multiplicative factor between the two quantities (log2 8 = 3)
    delta_num, delta_den = 1, 1     # Δ = 1
    expected_diff = round(math.log(f, base) / (delta_num / delta_den))   # = 3
    diffs = []
    for i, s_f in enumerate([1.3, 2.7, 5.1, 9.9, 100.0]):   # random per-frame scales
        # two quantities in ONE frame: q1 = s_f * v, q2 = s_f * (f*v)
        v = 3.0
        frame = [["cell", 0, float(s_f * v), 1], ["cell", 0, float(s_f * f * v), 1]]
        eq = list(emit(native, [frame], YSLOT, base_num=base,
                       delta_num=delta_num, delta_den=delta_den, raw=True))[0]
        q1, q2 = eq[0][YSLOT], eq[1][YSLOT]
        diffs.append(q2 - q1)
        print(f"    scale={s_f:6}: quanta=({q1},{q2})  diff={q2 - q1}  "
              f"(expected {expected_diff})")
    a_ok = all(d == expected_diff for d in diffs)
    print(f"    all diffs == {expected_diff}: {a_ok}  "
          f"(the per-frame multiplicative scale CANCELLED in the difference)")

    # ============================================================
    # (B) POPULATION: plant a cross-axis log-extent ratio, random per-frame
    #     multiplicative scales, emit both axes to integer quanta, RatioInduce
    #     recovers the ratio and factors the scale.
    # ============================================================
    print("\n(B) POPULATION RECOVERY — planted log-extent ratio y:x, per-frame scales:")
    trials = [
        # (base, x_span_pow, y_span_pow, per-frame scales)  planted y:x = y_pow:x_pow
        (2, 2, 6, [1.3, 2.7, 5.1, 9.9]),        # 6:2 -> 3:1 power-of-two? 3 not pow2 -> latent:ratio
        (2, 3, 3, [1.1, 4.4, 8.8, 20.0]),       # 3:3 -> 1:1
        (2, 1, 4, [2.2, 3.3, 7.7, 13.0]),       # 4:1 pow2 -> latent:scale2
        (3, 2, 4, [1.5, 6.0, 11.1, 30.0]),      # 4:2 -> 2:1 pow2 -> latent:scale2
        (2, 4, 6, [1.7, 3.9, 8.1, 50.0]),       # 6:4 -> 3:2 -> latent:ratio
    ]
    n_ok = 0
    for (b, xp, yp, scales) in trials:
        frames = [make_linear_frame(sf, xp, yp, b, seed=17 * i + b)
                  for i, sf in enumerate(scales)]
        emitted = emit_both_axes(native, frames, base_num=b, delta_num=1, delta_den=1)
        out = induce(native, emitted)
        explained = bool(out.get("explained"))
        ratios = parse_ratios(out)
        # planted y:x log-extent ratio reduced
        g = math.gcd(yp, xp) if xp else yp
        planted = (yp // g, xp // g) if xp else None
        recovered = ratios.get(YSLOT)
        latent = out.get("latent_name")
        ok = explained and recovered == planted
        n_ok += int(ok)
        print(f"    base={b} planted y:x log-extent = {planted!s:6}  "
              f"induced = {recovered!s:8} latent={latent!s:14} "
              f"n_frames={out.get('n_frames')}  {'OK' if ok else 'MISS'}")

    # ============================================================
    # (C) NEGATIVE CONTROL: independent per-axis multiplicative stretch (no single
    #     common scale) must FALSIFY after emission — the honest floor survives.
    # ============================================================
    print("\n(C) NEGATIVE CONTROL — independent per-axis stretch must FALSIFY:")
    b = 2
    indep_lin = []
    for i, (sx, sy) in enumerate([(1, 1), (2, 3), (3, 2), (5, 4)]):
        # x log-extent = 2*sx-ish via powers; y log-extent = 3*sy — independent
        rels = []
        for px in (0, 2 * sx):
            for py in (0, 3 * sy):
                rels.append(["cell", float(b ** px), float(b ** py), 1])
        indep_lin.append(rels)
    emitted_indep = emit_both_axes(native, indep_lin, base_num=b, delta_num=1, delta_den=1)
    out_indep = induce(native, emitted_indep)
    c_ok = (out_indep.get("explained") is False)
    print(f"    independent-axis-stretch explained = {out_indep.get('explained')}  "
          f"{'OK (floored)' if c_ok else 'MISS (falsely explained!)'}")

    print("\n" + "=" * 72)
    print("H-L2 VERDICT")
    print("=" * 72)
    print(f"  (A) log-quantum difference == round(log_a f/Δ), scale cancelled : "
          f"{'PASS' if a_ok else 'FAIL'}")
    print(f"  (B) population recovery via emitter + RatioInduce               : "
          f"{n_ok}/{len(trials)}")
    print(f"  (C) independent-axis floor survives emission                    : "
          f"{'PASS' if c_ok else 'FAIL'}")
    confirmed = a_ok and (n_ok == len(trials)) and c_ok
    print(f"  H-L2 CONFIRMED: {confirmed}")
    return confirmed


if __name__ == "__main__":
    main()
