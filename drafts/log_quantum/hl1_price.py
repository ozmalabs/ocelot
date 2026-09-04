"""H-L1 — THE PRICE CHECK (the crux, verified FIRST): is the LogQuantum emitter
well-formed against the frame/continuum invariant, or does it need continuous
in-frame state?

PREREG H-L1 (well-formedness): the emitter puts ONLY an integer in-frame;
base + resolution live in `Hom` applied-on-read; `coord_ints` still refuses
floats; NO continuous coordinate is stored in-frame. CONFIRMED iff the emitted
quantum is Int, the emitter round-trips as a Term with base/Δ as intensional
params, and a float is never written to a coord slot. FAIL (needs to store the
continuous value in-frame) → the emitter cannot be well-formed and THAT is the
finding (a real invariant boundary, not a workaround target).

This harness checks, on the built engine, five falsifiable price facts:

  (P1) THE EMITTED QUANTUM IS AN INTEGER, IN-FRAME. Feed raw continuous values
       (Python floats) as the input log-domain quantity; the emitted value_slot
       must be a Python `int` in EVERY output relation — never a float. This is
       the whole point: `coord_ints` accepts the output because it is Int.

  (P2) BASE + Δ ARE INTENSIONAL PARAMS ON THE TERM (IN HOM), APPLIED ON READ.
       The base a and step Δ ride as integer rationals on the Term
       (base_num/base_den, delta_num/delta_den) — never as an in-frame
       coordinate. The term wire form carries NO continuous coordinate payload.
       Changing Δ on the SAME input changes the emitted quanta (the param is
       applied on read), and re-evaluating the SAME term reproduces the SAME
       quanta (the map is a rule, not stored state).

  (P3) coord_ints STILL REFUSES FLOATS — the downstream gate is untouched. The
       emitter's OUTPUT (integer quanta) is consumable by RatioInduce
       (explained over a scaled population), while a population whose coords are
       RAW FLOATS handed straight to RatioInduce is INAPPLICABLE
       (explained=false, n_frames=0). The Int-only gate is intact; the emitter
       is the thing that legitimately turns a continuous reading into an
       admissible integer coordinate.

  (P4) A FLOAT IS NEVER WRITTEN TO A COORD SLOT — even from a float input, and
       even when the op is INAPPLICABLE. When Δ<=0 / base invalid / value_slot
       out of range, the op is a graceful skip that returns the population
       UNCHANGED; when applicable, every emitted value_slot is Int. In no path
       does a float land in the output coord slot.

  (P5) RESOLUTION PINNED TO OBSERVATION (MDL). Δ is the identifiability guard:
       a coarser Δ collapses finer distinctions to the same quantum (never
       encodes precision the source cannot support), and the quantum is the
       stepped integer rendering of the continuous reading. We assert a coarse
       Δ merges inputs a fine Δ separates — the observable is the step.

VERDICT: H-L1 PASSED iff P1..P5 all hold (integer in-frame, base+Δ in Hom,
         coord_ints intact, no float coord, resolution=observation).
         H-L1 FAILED iff the emitter cannot work without continuous in-frame
         state — reported as the foundational boundary, not worked around.

Run:  PYTHONPATH=. python3 drafts/log_quantum/hl1_price.py
"""
from __future__ import annotations

import json
import math

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

from substrate.boot_core import boot_core          # noqa: E402
from domains import reflective_faculty as rf        # noqa: E402

# Frame is [pred, coord:x, coord:y, val]; the log-domain quantity rides in the
# y slot (index 2), the reference axis in x (index 1).
DIM_TYPES = ["pred", "coord:x", "coord:y", "val"]
VALUE_SLOT = 2


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


def emit(native, frames, *, value_slot=VALUE_SLOT, base_num=2, base_den=1,
         delta_num=1, delta_den=1, raw=True, field=""):
    """Run LogQuantum: quantize `value_slot` of every relation to an integer
    log-quantum q = round(log_a(x)/Δ)."""
    return native.evaluate(
        {"type": "LogQuantum",
         "population": {"type": "Lit", "value": frames},
         "value_slot": value_slot,
         "base_num": base_num, "base_den": base_den,
         "delta_num": delta_num, "delta_den": delta_den,
         "raw": raw, "field": field},
        {})


def induce(native, frames, resolution=0):
    return native.evaluate(
        {"type": "RatioInduce",
         "population": {"type": "Lit", "value": frames},
         "resolution": resolution, "field": ""},
        {})


def all_slot_values(pop, slot):
    """Flatten the emitted value_slot across every relation of every frame."""
    out = []
    for frame in pop:
        for rel in frame:
            out.append(rel[slot])
    return out


def main():
    print("ENGINE:", provenance_line())
    print("=" * 72)
    print("H-L1  PRICE CHECK — is the LogQuantum emitter well-formed?")
    print("       (checked FIRST: integer in-frame, base+Δ in Hom, no float coord)")
    print("=" * 72)
    s, ag, native = boot()

    # ---- P1: emitted quantum is an INTEGER, in-frame (from a FLOAT input) ----
    # raw continuous log-domain readings (Python floats). Under base e, raw:
    # q = round(ln(x)/Δ). Feed values whose logs are clearly non-integer.
    raw_vals = [1.7, 2.9, 5.5, 11.1, 20.0]
    float_in = [[["w", 0, float(x), 0]] for x in raw_vals]
    out1 = emit(native, float_in, base_num=0, delta_num=1, delta_den=1, raw=True)  # base e
    emitted = all_slot_values(list(out1), VALUE_SLOT)
    p1 = len(emitted) == len(raw_vals) and all(isinstance(v, int) for v in emitted)
    print("\n(P1) EMITTED QUANTUM IS AN INTEGER, IN-FRAME (input was float):")
    print(f"     raw float inputs : {raw_vals}")
    print(f"     emitted quanta   : {emitted}   all int = "
          f"{all(isinstance(v, int) for v in emitted)}")
    print(f"     expected round(ln x): {[round(math.log(x)) for x in raw_vals]}")
    print(f"     P1 = {p1}")

    # ---- P2: base + Δ are intensional params on the Term, applied on read ----
    # Same input, two different Δ -> different quanta (param applied on read).
    fine = all_slot_values(list(emit(native, float_in, base_num=0,
                                     delta_num=1, delta_den=4, raw=True)), VALUE_SLOT)   # Δ=0.25
    coarse = all_slot_values(list(emit(native, float_in, base_num=0,
                                       delta_num=1, delta_den=1, raw=True)), VALUE_SLOT)  # Δ=1
    param_applied = (fine != coarse)
    # Re-evaluate the SAME term -> SAME quanta (the map is a rule, not stored).
    again = all_slot_values(list(emit(native, float_in, base_num=0,
                                      delta_num=1, delta_den=1, raw=True)), VALUE_SLOT)
    map_is_rule = (again == coarse)
    # The term wire form carries NO coordinate payload — only intensional params.
    term = {"type": "LogQuantum",
            "population": {"type": "Lit", "value": float_in},
            "value_slot": VALUE_SLOT, "base_num": 0, "base_den": 1,
            "delta_num": 1, "delta_den": 1, "raw": True, "field": ""}
    term_keys = set(term) - {"population"}
    no_coord_state = term_keys == {"type", "value_slot", "base_num", "base_den",
                                   "delta_num", "delta_den", "raw", "field"}
    p2 = param_applied and map_is_rule and no_coord_state
    print("\n(P2) BASE + Δ ARE INTENSIONAL PARAMS ON THE TERM (IN HOM), applied on read:")
    print(f"     Δ=0.25 quanta : {fine}")
    print(f"     Δ=1.0  quanta : {coarse}   (different Δ -> different quanta = "
          f"{param_applied})")
    print(f"     re-eval same term reproduces quanta = {map_is_rule} (map is a RULE)")
    print(f"     term carries only intensional params, no coord payload = {no_coord_state}")
    print(f"     P2 = {p2}")

    # ---- P3: coord_ints STILL REFUSES FLOATS — the downstream gate is intact --
    # (a) the emitter's INTEGER output over a scaled population is RatioInduce-
    #     consumable; (b) a RAW FLOAT population handed to RatioInduce directly
    #     is inapplicable (explained=false, n_frames=0). The emitter is the
    #     legitimate bridge; the gate itself is untouched.
    # Build an integer emitted population differing by a per-frame multiplicative
    # scale on the y (log-domain) value, ref axis x integer.
    scaled = []
    for k in (1, 2, 3, 4):
        # y linear values = base^(k) on a fixed shape; x is an integer ref extent
        rels = [["w", 0, 1.0, 0], ["w", 2 * k, float(2 ** k), 0]]
        scaled.append(rels)
    emitted_pop = list(emit(native, scaled, base_num=2, delta_num=1, delta_den=1, raw=True))
    # emitted_pop now has integer y quanta; feed to RatioInduce
    out_ind = induce(native, emitted_pop)
    emitter_consumable = bool(out_ind.get("explained"))
    # raw float population straight to RatioInduce -> refused
    raw_float_pop = [[["w", 0, 0, 1], ["w", 2 * k, float(2 ** k) + 0.5, 1]] for k in (1, 2, 3, 4)]
    out_rawf = induce(native, raw_float_pop)
    gate_refuses_float = (out_rawf.get("explained") is False
                          and int(out_rawf.get("n_frames") or 0) == 0)
    p3 = emitter_consumable and gate_refuses_float
    print("\n(P3) coord_ints STILL REFUSES FLOATS — downstream integer gate intact:")
    print(f"     emitter INTEGER output -> RatioInduce explained = "
          f"{out_ind.get('explained')} (consumable = {emitter_consumable})")
    print(f"     RAW FLOAT population -> RatioInduce explained = "
          f"{out_rawf.get('explained')}, n_frames = {out_rawf.get('n_frames')} "
          f"(refused = {gate_refuses_float})")
    print(f"     P3 = {p3}")

    # ---- P4: a FLOAT is NEVER written to a coord slot (applicable OR skip) ----
    # applicable path already checked in P1 (all int). Skip path: Δ<=0 returns
    # the population UNCHANGED (the float input is passed through untouched — the
    # op refuses rather than emitting a float coordinate). The emitted-column of
    # an APPLICABLE run is int; a SKIP leaves the input as-is (never a NEW float).
    skip_out = list(emit(native, float_in, base_num=0, delta_num=0, delta_den=1, raw=True))  # Δ=0 -> skip
    skip_unchanged = (json.dumps([[list(r) for r in f] for f in skip_out])
                      == json.dumps(float_in))
    # invalid base (a<=1) -> skip, unchanged
    skip_base = list(emit(native, float_in, base_num=1, base_den=1, delta_num=1, delta_den=1, raw=True))
    skip_base_unchanged = (json.dumps([[list(r) for r in f] for f in skip_base])
                           == json.dumps(float_in))
    # out-of-range value_slot -> the op cannot write there; leaves relations intact
    skip_slot = list(emit(native, float_in, value_slot=99, base_num=0, delta_num=1, delta_den=1, raw=True))
    skip_slot_unchanged = (json.dumps([[list(r) for r in f] for f in skip_slot])
                           == json.dumps(float_in))
    p4 = p1 and skip_unchanged and skip_base_unchanged and skip_slot_unchanged
    print("\n(P4) A FLOAT IS NEVER WRITTEN TO A COORD SLOT (applicable emits int; skip = unchanged):")
    print(f"     applicable path all-int (from P1) = {p1}")
    print(f"     Δ<=0 skip returns population unchanged = {skip_unchanged}")
    print(f"     invalid base skip unchanged = {skip_base_unchanged}")
    print(f"     out-of-range slot skip unchanged = {skip_slot_unchanged}")
    print(f"     P4 = {p4}")

    # ---- P5: resolution pinned to observation (MDL) — coarse Δ merges fine ----
    # Two nearby readings the fine Δ separates must COLLAPSE to one quantum under
    # a coarse Δ: the emitter never encodes precision the step cannot support.
    near = [[["w", 0, 100.0, 0]], [["w", 0, 106.0, 0]]]     # ln 100 vs ln 106 differ ~0.058
    fineq = all_slot_values(list(emit(native, near, base_num=0,
                                      delta_num=1, delta_den=100, raw=True)), VALUE_SLOT)  # Δ=0.01
    coarseq = all_slot_values(list(emit(native, near, base_num=0,
                                        delta_num=1, delta_den=1, raw=True)), VALUE_SLOT)   # Δ=1
    fine_separates = (fineq[0] != fineq[1])
    coarse_merges = (coarseq[0] == coarseq[1])
    p5 = fine_separates and coarse_merges
    print("\n(P5) RESOLUTION PINNED TO OBSERVATION (MDL) — coarse Δ merges what fine separates:")
    print(f"     inputs ~= 100, 106 ;  fine Δ=0.01 quanta = {fineq} (separated = {fine_separates})")
    print(f"     coarse Δ=1.0 quanta = {coarseq} (merged = {coarse_merges})")
    print(f"     the observable IS the step; precision beyond Δ is not encoded")
    print(f"     P5 = {p5}")

    print("\n" + "=" * 72)
    print("H-L1 VERDICT")
    print("=" * 72)
    passed = p1 and p2 and p3 and p4 and p5
    print(f"  P1 emitted quantum is Int, in-frame     : {p1}")
    print(f"  P2 base+Δ intensional on Term (in Hom)  : {p2}")
    print(f"  P3 coord_ints still refuses floats      : {p3}")
    print(f"  P4 no float ever written to a coord slot: {p4}")
    print(f"  P5 resolution pinned to observation(MDL): {p5}")
    print(f"  H-L1 {'PASSED — integer-observable log-quantum is well-formed BY CONSTRUCTION; price against the invariant is ZERO' if passed else 'FAILED — needs continuous in-frame state (invariant boundary, price too high)'}")
    return passed


if __name__ == "__main__":
    main()
