"""H-R1 — POPULATION RATIO-INVARIANCE INDUCTION, synthetic clean-mechanism gate.

PREREG H-R1 (mechanism, clean ground truth): on a SYNTHETIC population with a
PLANTED invariant cross-coordinate ratio structure and PER-FRAME random
multiplicative scales, the `RatioInduce` op INDUCES the planted ratios (the
cross-coordinate ratio set fixed across frames), and the induced map APPLIED
collapses the population onto its shared invariant. CONFIRMED iff the recovered
ratio set matches the planted one (within observation resolution) and the
residual per-frame scale is cancelled. NULL iff it cannot recover a planted
ratio from a population.

DISCIPLINE (the op is NOT handed the answer):
  * The planted ratio is chosen by the harness; the op receives ONLY the raw
    per-frame integer coordinate observations (frames), never the ratio.
  * Per-frame scales are random and unknown to the op.
  * A NEGATIVE CONTROL (non-multiplicative nuisance: one frame perturbed by an
    ADDITIVE offset that no common scale explains) MUST come back
    `explained=false` — the honest MDL floor. If the op "recovers" a ratio from
    a genuinely non-multiplicative population it is rigged / vacuous.

Run:  python drafts/ratio_invariance/hr1_synthetic.py
"""
from __future__ import annotations

import json
import math
import random

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

from substrate.boot_core import boot_core          # noqa: E402
from domains import reflective_faculty as rf        # noqa: E402

# The frame is [pred, coord:x, coord:y, val] — a 2-coord lattice, slot 0 the
# reference axis (x), slot 1 the ratio-carrying axis (y). dim_types names them.
DIM_TYPES = ["pred", "coord:x", "coord:y", "val"]


def boot():
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    # A held part so RatioInduce can read the frame's coord slots from
    # dim_types (all parts in a codebook share the frame; the part's own
    # signature is irrelevant to the induction — only its dim_types is read).
    s.add_node("ShapeSignature", {
        "name": "frame_probe",
        "signature": json.dumps([["cell", 0, 0, 1]]),
        "kind": "faculty", "faculty": "frame_probe",
        "dim_types": list(DIM_TYPES),
    })
    return s, ag, native


def make_frame(scale: int, ratio_num: int, ratio_den: int, seed: int) -> list:
    """A single frame: a set of integer coordinate observations whose EXTENT on
    the ref axis (x) is `scale*ratio_den` and on the y axis is `scale*ratio_num`
    — so the cross-coordinate extent ratio y:x is EXACTLY ratio_num:ratio_den,
    independent of `scale`. The interior points are RANDOM (jittered lattice
    fill) so the op sees a real observation, not two corner cells; only the
    EXTENT carries the planted ratio, which is what the op reads.
    """
    rng = random.Random(seed)
    ex = scale * ratio_den          # x extent
    ey = scale * ratio_num          # y extent
    pts = {(0, 0), (ex, ey), (ex, 0), (0, ey)}   # guarantee the extent box
    # random interior fill inside the box (does not change the extent)
    for _ in range(6):
        pts.add((rng.randint(0, ex), rng.randint(0, ey)))
    return [["cell", int(x), int(y), 1] for (x, y) in sorted(pts)]


def induce(native, frames) -> dict:
    return native.evaluate(
        {"type": "RatioInduce",
         "population": {"type": "Lit", "value": frames},
         "field": ""},
        {})


def parse_ratios(out: dict):
    """ratios is a flat tuple of [slot, num, den] triples."""
    flat = list(out.get("ratios") or ())
    triples = [tuple(flat[i:i + 3]) for i in range(0, len(flat), 3)]
    return {int(s): (int(n), int(d)) for (s, n, d) in triples}


def apply_cancels_scale(out: dict, frames) -> bool:
    """The induced map, APPLIED, collapses the population onto its shared
    invariant: after dividing each frame's y-extent by the induced ratio
    (y_extent * den / num), every frame's normalized (x, y) extent pair is a
    COMMON SCALE multiple of one canonical pair — i.e. the ratio between frames
    is a pure scalar (the per-frame scale), with NO residual cross-coordinate
    structure. We verify this in INTEGER arithmetic: for the ref axis, the
    per-frame x-extent IS the recovered scale (up to the canonical den); the y
    axis, mapped through the ratio, must equal that same scale — leaving only a
    single scalar per frame, which is exactly 'the per-frame scale cancelled'.
    """
    ratios = parse_ratios(out)
    ref = int(out.get("ref_dim"))
    # coord slot indices in dim_types order: x=1, y=2 -> but ratios keyed by slot
    # ref axis extent per frame, and target axis extent per frame:
    def extent(frame, slot):
        vs = [rel[slot] for rel in frame]
        return max(vs) - min(vs)
    if not ratios:
        return False
    # the single non-ref slot in this 2-coord test
    tgt = next(iter(ratios))
    num, den = ratios[tgt]
    scales = []
    for f in frames:
        ex = extent(f, ref)
        ey = extent(f, tgt)
        # map y through the ratio: y * den should equal x * num (cross-mult
        # invariant). The 'cancelled scale' is ex/den == ey/num (integer).
        if ey * den != ex * num:
            return False
        # per-frame scale (in canonical units): ex must be a multiple of den
        if den == 0 or ex % den != 0:
            return False
        scales.append(ex // den)
    # scales differ per frame (that IS the per-frame scale we cancelled); the
    # ratio structure is identical across frames -> collapse succeeded.
    return len(scales) >= 2


def main():
    print("ENGINE:", provenance_line())
    print("=" * 72)
    print("H-R1  POPULATION RATIO-INVARIANCE INDUCTION — synthetic recovery")
    print("=" * 72)

    s, ag, native = boot()

    # ---- PRIMARY: plant a ratio, random per-frame scales, recover it ----
    trials = [
        # (planted y:x ratio, list of per-frame scales)
        ((3, 2), [1, 2, 3, 5, 7, 11]),          # 3:2, non-power-of-two -> latent:ratio
        ((5, 1), [1, 3, 4, 6, 9]),              # 5:1
        ((4, 1), [1, 2, 4, 8]),                 # 4:1 power-of-two -> latent:scale2
        ((2, 1), [1, 2, 3, 4, 5]),              # 2:1 power-of-two -> latent:scale2
        ((7, 3), [1, 2, 5, 8, 13]),             # 7:3
    ]
    n_ok = 0
    print("\n(1) RECOVERY — planted ratio vs induced (op sees only raw frames):")
    for (rn, rd), scales in trials:
        frames = [make_frame(sc, rn, rd, seed=1000 * rn + 7 * i)
                  for i, sc in enumerate(scales)]
        out = induce(native, frames)
        explained = bool(out.get("explained"))
        ratios = parse_ratios(out)
        # planted ratio reduced
        g = math.gcd(rn, rd)
        planted = (rn // g, rd // g)
        # recovered: the single non-ref slot's (num, den)
        recovered = next(iter(ratios.values())) if ratios else None
        latent = out.get("latent_name")
        is_pow2 = bool(out.get("is_pow2"))
        cancels = apply_cancels_scale(out, frames) if explained else False
        ok = explained and recovered == planted and cancels
        n_ok += int(ok)
        print(f"    planted y:x = {planted!s:7}  induced = {recovered!s:9}  "
              f"latent={latent!s:14} pow2={is_pow2!s:5} cancels_scale={cancels!s:5} "
              f"n_frames={out.get('n_frames')}  {'OK' if ok else 'MISS'}")

    # ---- NEGATIVE CONTROL: EXTENT-breaking nuisance (NOT purely multiplicative) ----
    # NOTE the correct shape of this control. The ratio reads the ORIGIN-
    # NORMALIZED EXTENT (max - min), which is by construction TRANSLATION-
    # INVARIANT: a uniform additive offset shifts a frame but does not change
    # its extent, and a ratio SHOULD be robust to that (it is a common-mode
    # nuisance, exactly what a ratio cancels). So the falsifying perturbation
    # must change the CROSS-COORDINATE EXTENT relationship in a way no single
    # common scale explains: STRETCH one frame's y-extent by a factor different
    # from its x-extent (an independent per-axis stretch on one member).
    print("\n(2) NEGATIVE CONTROL — extent-breaking nuisance must FALSIFY (explained=false):")
    base = [make_frame(sc, 3, 2, seed=555 + i) for i, sc in enumerate([1, 2, 3, 4])]
    bad = [list(f) for f in base]
    # frame 2: stretch y by an EXTRA +7 on the max-y point only -> its y-extent
    # is no longer scale*3, so y:x is not 3:2 for this frame. No common scale
    # relates this frame's (x,y) extents to the others'.
    fy = [rel[2] for rel in bad[2]]
    maxy = max(fy)
    bad[2] = [[p, x, (y + 7 if y == maxy else y), v] for (p, x, y, v) in bad[2]]
    out_bad = induce(native, bad)
    neg_ok = (out_bad.get("explained") is False)
    print(f"    extent-broken population explained = {out_bad.get('explained')}  "
          f"{'OK (floored)' if neg_ok else 'MISS (falsely explained!)'}")

    # ---- NEGATIVE CONTROL 1b: confirm a PURE TRANSLATION does NOT falsify ----
    # (the ratio is translation-invariant BY DESIGN — this is a feature, and
    #  we assert it explicitly so the extent-reading is not mistaken for a bug)
    trans = [list(f) for f in base]
    trans[1] = [[p, x + 9, y + 4, v] for (p, x, y, v) in trans[1]]   # rigid shift
    out_trans = induce(native, trans)
    trans_inv = (out_trans.get("explained") is True
                 and parse_ratios(out_trans) == parse_ratios(induce(native, base)))
    print(f"    pure-translation population still explained (ratio translation-"
          f"invariant BY DESIGN) = {out_trans.get('explained')}  "
          f"{'OK' if trans_inv else 'unexpected'}")

    # ---- NEGATIVE CONTROL 2: two independent axes (no single common scale) ----
    print("\n(3) NEGATIVE CONTROL — axes scaled INDEPENDENTLY must FALSIFY:")
    indep = []
    for i, (sx, sy) in enumerate([(1, 1), (2, 3), (3, 2), (5, 4)]):
        ex, ey = 2 * sx, 3 * sy
        pts = sorted({(0, 0), (ex, ey), (ex, 0), (0, ey)})
        indep.append([["cell", x, y, 1] for (x, y) in pts])
    out_indep = induce(native, indep)
    indep_ok = (out_indep.get("explained") is False)
    print(f"    independently-scaled-axes explained = {out_indep.get('explained')}  "
          f"{'OK (floored)' if indep_ok else 'MISS (falsely explained!)'}")

    print("\n" + "=" * 72)
    print("H-R1 VERDICT")
    print("=" * 72)
    print(f"  recovery:            {n_ok}/{len(trials)} planted ratios recovered "
          f"AND scale-cancelled")
    print(f"  extent-break floor:  {'PASS' if neg_ok else 'FAIL'}")
    print(f"  translation-invariance (feature): {'PASS' if trans_inv else 'FAIL'}")
    print(f"  independent-axis floor: {'PASS' if indep_ok else 'FAIL'}")
    confirmed = (n_ok == len(trials)) and neg_ok and indep_ok and trans_inv
    print(f"  H-R1 CONFIRMED:      {confirmed}")
    return confirmed


if __name__ == "__main__":
    main()
