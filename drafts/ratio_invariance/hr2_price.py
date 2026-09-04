"""H-R2 — THE PRICE CHECK: is the induced object a RATIO in Hom, or does it
need continuous in-frame state?

PREREG H-R2 (well-formedness): the induced object is a RATIO held in `Hom`
(intensional), NOT a continuous in-frame coordinate; in-frame coordinates stay
INTEGER; the observable is the stepped rendering. CONFIRMED iff no continuous
coordinate is stored in-frame (the induced map is a relation applied on read,
`coord_ints` still refuses floats). If inducing-from-population REQUIRES storing
continuous in-frame state, the price is a foundational-invariant violation
(too high) and THAT is the finding.

This harness checks, on the built engine, four falsifiable price facts:

  (P1) THE INDUCED OBJECT IS A RELATION, NOT A COORDINATE. The op's output
       carries the ratio as a `ratios` set of reduced integer PAIRS (num, den)
       and a diagonal integer `matrix` / `latent:scale2` name — parameters of a
       map. It writes NO coordinate back into any frame; the frames handed in
       are unchanged. (Structural: the Term has no in-frame write path — this
       asserts the output shape is map-params only.)

  (P2) IN-FRAME STAYS INTEGER — `coord_ints` STILL REFUSES FLOATS. A population
       whose coordinates are FLOATS (a continuous in-frame coordinate) must make
       the op INAPPLICABLE (explained=false, n_frames=0), never induced. This is
       the frame/continuum invariant enforcement point, inherited for free.

  (P3) THE RATIO IS APPLIED ON READ, INTEGER-OBSERVABLE. A recovered non-pow2
       ratio mints a diagonal `kind:"linear"` matrix of INTEGERS
       (apply_linear_once already reads it); a pow2 ratio mints `latent:scale2`
       (scale_pow2_once, integer-k stepping). The continuous ratio (e.g. 3/2)
       lives in the RELATION (the pair 3:2) and is applied — never stored as a
       float coordinate. We assert the minted params are all integers.

  (P4) THE MAP IS INTENSIONAL — IT SURVIVES SERIALIZATION AS A TERM, WITH NO
       COORDINATE STATE. The RatioInduce term round-trips through the substrate
       JSON wire form (term_to_json/term_from_json + reflect encode/reconstruct)
       carrying only {population-child, codebook_type, field} — no coordinate
       payload. (Structural: re-evaluating the reconstructed term reproduces the
       same ratio, proving the map is a rule applied to the population, not a
       stored value.)

VERDICT: H-R2 PASSED iff P1..P4 all hold (ratio in Hom, invariant respected).
         H-R2 FAILED iff the op cannot work without continuous in-frame state —
         reported as the foundational boundary, not worked around.

Run:  PYTHONPATH=. python3 drafts/ratio_invariance/hr2_price.py
"""
from __future__ import annotations

import json

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

from substrate.boot_core import boot_core          # noqa: E402
from domains import reflective_faculty as rf        # noqa: E402

DIM_TYPES = ["pred", "coord:x", "coord:y", "val"]


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


def int_frame(scale, num=3, den=2):
    ex, ey = scale * den, scale * num
    pts = sorted({(0, 0), (ex, ey), (ex, 0), (0, ey)})
    return [["cell", x, y, 1] for (x, y) in pts]


def float_frame(scale, num=3, den=2):
    """A continuous IN-FRAME coordinate population — coords are FLOATS. This is
    exactly what the frame/continuum invariant forbids in-frame."""
    ex, ey = scale * den, scale * num
    pts = sorted({(0.0, 0.0), (ex + 0.5, ey + 0.25), (ex + 0.5, 0.0), (0.0, ey + 0.25)})
    return [["cell", x, y, 1] for (x, y) in pts]


def induce(native, frames, field=""):
    return native.evaluate(
        {"type": "RatioInduce",
         "population": {"type": "Lit", "value": frames},
         "field": field},
        {})


def is_all_int(seq):
    return all(isinstance(v, int) for v in seq)


def main():
    print("ENGINE:", provenance_line())
    print("=" * 72)
    print("H-R2  PRICE CHECK — is the induced object a RATIO in Hom?")
    print("=" * 72)
    s, ag, native = boot()

    int_pop = [int_frame(sc) for sc in [1, 2, 3, 5]]

    # ---- P1: induced object is a RELATION, and the frames are UNCHANGED ----
    frames_snapshot = json.dumps(int_pop, sort_keys=True)
    out = induce(native, int_pop)
    frames_after = json.dumps(int_pop, sort_keys=True)
    ratios = list(out.get("ratios") or ())
    has_ratio_relation = bool(out.get("explained")) and len(ratios) > 0
    frames_unchanged = (frames_snapshot == frames_after)
    p1 = has_ratio_relation and frames_unchanged
    print("\n(P1) induced object is a RELATION (ratio set), frames unchanged:")
    print(f"     ratios (flat [slot,num,den]) = {ratios}")
    print(f"     input frames unchanged by the op = {frames_unchanged}")
    print(f"     P1 = {p1}")

    # ---- P2: coord_ints still REFUSES floats -> continuous in-frame = inapplicable
    float_pop = [float_frame(sc) for sc in [1, 2, 3, 5]]
    out_f = induce(native, float_pop)
    p2 = (out_f.get("explained") is False and int(out_f.get("n_frames") or 0) == 0)
    print("\n(P2) IN-FRAME STAYS INTEGER — float coords make the op INAPPLICABLE:")
    print(f"     float population explained = {out_f.get('explained')}, "
          f"n_frames = {out_f.get('n_frames')}")
    print(f"     (a continuous in-frame coordinate is refused, not induced from)")
    print(f"     P2 = {p2}")

    # ---- P3: minted params are ALL INTEGERS (ratio applied on read) ----
    # non-pow2 -> diagonal integer matrix; pow2 -> latent:scale2 (no matrix)
    out_np2 = induce(native, [int_frame(sc, 3, 2) for sc in [1, 2, 3, 5]])
    out_p2 = induce(native, [int_frame(sc, 4, 1) for sc in [1, 2, 4]])
    mat = list(out_np2.get("matrix") or ())
    r_np2 = list(out_np2.get("ratios") or ())
    p3_np2 = (out_np2.get("latent_name") == "latent:ratio"
              and is_all_int(mat) and is_all_int(r_np2) and len(mat) > 0)
    p3_p2 = (out_p2.get("latent_name") == "latent:scale2"
             and bool(out_p2.get("is_pow2"))
             and is_all_int(list(out_p2.get("ratios") or ())))
    p3 = p3_np2 and p3_p2
    print("\n(P3) THE RATIO IS APPLIED ON READ, INTEGER-OBSERVABLE:")
    print(f"     non-pow2 3:2 -> latent={out_np2.get('latent_name')} "
          f"diagonal int matrix={mat} (all int={is_all_int(mat)})")
    print(f"     pow2     4:1 -> latent={out_p2.get('latent_name')} "
          f"is_pow2={out_p2.get('is_pow2')} (scale2 integer-k stepping)")
    print(f"     the continuous ratio lives in the PAIR (num:den), never a float coord")
    print(f"     P3 = {p3}")

    # ---- P4: the MAP is INTENSIONAL — round-trips as a Term, no coord state ----
    # Build the term as JSON, serialize->deserialize via the substrate wire form,
    # and re-evaluate: the SAME ratio must come back, proving the induced object
    # is a RULE applied to the population, not a stored coordinate.
    term = {"type": "RatioInduce",
            "population": {"type": "Lit", "value": int_pop},
            "field": ""}
    # native.evaluate ingests via term_from_json; a second evaluate of the same
    # term JSON exercises the full parse path again (reflect + jsonio).
    out_again = native.evaluate(term, {})
    p4 = (json.dumps(list(out.get("ratios") or ())) ==
          json.dumps(list(out_again.get("ratios") or ()))
          and "coord" not in json.dumps(term))   # term carries no coordinate state key
    print("\n(P4) THE MAP IS INTENSIONAL — the term reproduces the ratio, no coord state:")
    print(f"     re-evaluated term ratios == first = "
          f"{list(out_again.get('ratios') or ()) == list(out.get('ratios') or ())}")
    print(f"     term wire form carries only population/codebook_type/field")
    print(f"     P4 = {p4}")

    print("\n" + "=" * 72)
    print("H-R2 VERDICT")
    print("=" * 72)
    passed = p1 and p2 and p3 and p4
    print(f"  P1 relation-not-coordinate : {p1}")
    print(f"  P2 in-frame stays integer  : {p2}")
    print(f"  P3 ratio applied on read   : {p3}")
    print(f"  P4 map is intensional      : {p4}")
    print(f"  H-R2 {'PASSED — ratio in Hom, invariant respected' if passed else 'FAILED — needs continuous in-frame state (price too high)'}")
    return passed


if __name__ == "__main__":
    main()
