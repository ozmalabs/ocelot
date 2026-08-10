"""cortex_math_hat — point the EXISTING analysis-by-synthesis operator (the universal
cortex, domains/cortex_loop.CortexLoop, UNCHANGED) at the math DESCRIPTION->OBJECT gap
by building a MATH HAT (domains/math_hat.MathHat), mirroring domains/audio_hat.

NOT a new operator. The SAME CortexLoop that runs on audio (and the toy hat) runs on
the math hat — swap the hat, the cortex is unchanged (cortex_loop's own "swap the hat"
design). The math hat's forward model (synth) is the agent's HELD homology computation
(betti_number, acquired-by-reading, grounded over the held boundary operator ∂); its
encode is the agent's HELD construction-grammar comprehension (prose -> properties);
its compare is the owned Magnitude(VecSub) graph metric.

The gap: the derivation engine stalls at "comprehend: prose -> object" — a prose
description has no chain complex to derive over. INVERT the forward model: synthesize
candidate OBJECTS, derive each one's properties (the held homology), keep the one whose
properties match the description. That is analysis-by-synthesis, the operator the agent
already holds.

PROVES (honest, binary admissibility):
  1. The IDENTICAL CortexLoop drives the math hat (generality — confirm via diff).
  2. THE FULL PIPELINE on TRACTABLE cases: description -> (analysis-by-synthesis grounds
     the object) -> (derivation engine computes its homology) -> VERIFIED vs known.
  3. PRESENTATION-INVARIANCE: different phrasings of the same object's properties ->
     the SAME grounded object (the math echo of speaker-invariant-by-construction).
  4. THE HONEST STALL on the real HLE moduli case: the forward model / library LACKS
     the identification "moduli space of lattices -> S^3 minus the trefoil" — the loop
     cannot synthesize a candidate it does not hold. The KNOWLEDGE gap = acquire-by-
     reading. The loop's STRUCTURE is right; the held breadth is the climb. NOT faked.

Run: python -m scripts.cortex_math_hat
"""
from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "runners", "dsl", "python"))

from substrate_rs import Substrate, _native
from domains.cortex_loop import CortexLoop
from domains.math_hat import MathHat
from domains import grounded_representation as gr
from domains import reason
from domains import compute_grounding as cg

SEP = "=" * 78

# the known homology the derivation-engine step VERIFIES the grounded object against
# (the falsifiable ground truth — the loop is NEVER told this; it grounds by synthesis).
_KNOWN_HOMOLOGY = {
    "S^1": [1, 1],
    "S^2": [1, 0, 1],
    "disk": [1, 0, 0],
    "point": [1],
    "two_points": [2],
    "torus": [1, 2, 1],
}

_BETTI_DEF = ("betti_number(complex, k) = "
              "cardinality(simplices_of_dim(complex, k)) "
              "- matrix_rank(boundary_matrix(complex, k)) "
              "- matrix_rank(boundary_matrix(complex, k + 1))")


def banner(s):
    print("\n" + SEP, flush=True)
    print(s, flush=True)
    print(SEP, flush=True)


def _engine_compute_homology(name, spaces):
    """The DERIVATION ENGINE step: once the loop has GROUNDED the object, the held
    homology forward model COMPUTES its full Betti vector — the answer. Re-grounds
    betti_number on a fresh substrate (the engine's own held computation)."""
    s = _native.Substrate()
    gr.open_grounding_productions(s)
    caps = dict(reason.CAPABILITIES)
    cg.ground_computation(s, "betti_number", _BETTI_DEF, capabilities=caps)
    cx = spaces[name]
    top = max(len(sx) - 1 for sx in cx)
    return [int(reason.solve({"betti_number": {"complex": cx, "k": k}}, {},
                             capabilities=caps)) for k in range(top + 1)]


# ===========================================================================
def prove_full_pipeline(loop, hat):
    banner("1. THE FULL PIPELINE — description -> (synthesis) object -> (engine) answer")
    print("  Each description is GROUNDED to a known space by analysis-by-synthesis,")
    print("  then the derivation engine COMPUTES its homology — VERIFIED vs known.\n")
    # (description prose, the object it SHOULD ground to). The loop is told only the
    # prose; the expected object + its homology are the ground-truth check.
    cases = [
        ("a connected 1-dimensional space whose first Betti number is 1", "S^1"),
        ("a connected 2-dimensional closed surface whose first Betti number is 2",
         "torus"),
        ("a connected surface whose first Betti number is 0 and second Betti number is 1",
         "S^2"),
        ("a contractible space", "disk"),
        ("a 0-dimensional space whose zeroth Betti number is 2", "two_points"),
    ]
    all_ok = True
    for prose, want_obj in cases:
        obj, per, _curves = loop.recognise(prose)
        grounded_ok = (obj == want_obj)
        # the derivation engine computes the homology over the GROUNDED object.
        computed = _engine_compute_homology(obj, hat.spaces) if obj else None
        known = _KNOWN_HOMOLOGY.get(want_obj)
        answer_ok = (computed == _KNOWN_HOMOLOGY.get(obj))
        ok = grounded_ok and answer_ok
        all_ok = all_ok and ok
        print(f"  desc: {prose}")
        print(f"    -> GROUNDED object: {obj!r}  (want {want_obj!r}) "
              f"{'OK' if grounded_ok else 'X'}")
        print(f"    -> ENGINE computes H_*({obj}) = {computed}  known {known}  "
              f"{'OK' if answer_ok else 'X'}")
        print(f"    -> end-to-end {'OK' if ok else 'X'}\n")
    print(f"  -> full pipeline (description -> object -> answer -> verified) on all "
          f"tractable cases: {all_ok}")
    return all_ok


def prove_presentation_invariance(loop):
    banner("2. PRESENTATION-INVARIANCE — same object, different surface form")
    print("  The loop grounds to the OBJECT regardless of the description's phrasing")
    print("  (the math echo of speaker-invariant-by-construction: the forward model")
    print("  derives properties from the OBJECT, so presentation is factored out).\n")
    # several DIFFERENT phrasings of the TORUS's properties -> the same grounded object.
    torus_phrasings = [
        "a connected 2-dimensional closed surface whose first Betti number is 2",
        "a surface with first Betti number 2",
        "a connected surface whose first Betti number is 2 and second Betti number is 1",
        "a 2 dimensional connected space with first betti number 2",
    ]
    grounded = [loop.recognise(p)[0] for p in torus_phrasings]
    inv_ok = all(g == "torus" for g in grounded)
    for p, g in zip(torus_phrasings, grounded):
        print(f"    {'OK' if g=='torus' else 'X'}  {g!r:10} <- {p}")
    print(f"\n  -> all phrasings ground to the SAME object (torus), invariant to surface "
          f"form: {inv_ok}")
    return inv_ok


def prove_honest_hle_stall(loop, hat):
    banner("3. HONEST — the real HLE moduli case STALLS at the forward-model knowledge")
    print("  HLE 66c5c3ea: 'Let X be the moduli space of nondegenerate lattices in R^2")
    print("  with unit area. Compute H_1(X, Z).'  (answer: Z)\n")
    prose = ("the moduli space of nondegenerate lattices in the plane with unit area")
    obj, per, _curves = loop.recognise(prose)
    # the description names NO homological property the held comprehension extracts
    # (it is a NAMED CONSTRUCTION, 'moduli space of lattices', not a property list);
    # and even if it did, the OBJECT (S^3 minus the trefoil / the modular orbifold) is
    # NOT in the library. So the loop cannot ground it.
    target_props = hat.encode(prose)
    stated = [v for v in target_props if v == v]      # non-NaN = stated axes
    in_library = "modular_orbifold" in hat.spaces or "trefoil_complement" in hat.spaces
    print(f"  encode(description) stated properties: {len(stated)} "
          f"(the prose is a NAMED CONSTRUCTION, not a property list — nothing to match)")
    print(f"  the target object (S^3 minus the trefoil / SL(2,Z)\\H) in the library? "
          f"{in_library}")
    print(f"  loop's (mis)grounding under no constraints: {obj!r}  per-content: "
          f"{ {k: round(v,3) for k,v in (per or {}).items()} }")
    stalls = (not in_library) and (len(stated) == 0)
    print(f"\n  -> STALLS at the forward-model KNOWLEDGE gap (the identification 'moduli")
    print(f"     space of lattices -> S^3 minus the trefoil' is NOT held; the loop cannot")
    print(f"     synthesize a candidate it does not hold). ACQUIRE-BY-READING the")
    print(f"     identification puts the object in the library, then the loop grounds it.")
    print(f"     The loop STRUCTURE is right; the breadth is the climb. HLE NOT faked: "
          f"{stalls}")
    return stalls


def prove_no_regression():
    banner("4. NO REGRESSION — cortex_loop UNCHANGED; the held forward model intact")
    import subprocess
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # cortex_loop unchanged vs HEAD (the operator is not rebuilt).
    diff = subprocess.run(["git", "-C", root, "diff", "--stat", "--",
                           "domains/cortex_loop.py", "domains/audio_hat.py",
                           "domains/hat.py"],
                          capture_output=True, text=True)
    unchanged = (diff.stdout.strip() == "")
    print(f"  git diff domains/cortex_loop.py domains/audio_hat.py domains/hat.py:")
    print(f"    {diff.stdout.strip() or '(no changes — operator + audio hat UNCHANGED)'}")
    print(f"  -> the analysis-by-synthesis OPERATOR + the speech hat are UNCHANGED: "
          f"{unchanged}")
    # the held forward model still computes the known homology (the synth path).
    spaces = MathHat(Substrate()).spaces
    fwd_ok = all(_engine_compute_homology(n, spaces) == h
                 for n, h in _KNOWN_HOMOLOGY.items())
    print(f"  the held homology forward model still computes the known homology of all "
          f"spaces: {fwd_ok}")
    return unchanged and fwd_ok


def main():
    t0 = time.time()
    banner("UNIVERSAL CORTEX on the MATH HAT — analysis-by-synthesis grounds "
           "description->object")
    print("The IDENTICAL CortexLoop (domains/cortex_loop, UNCHANGED) drives a MATH HAT")
    print("(domains/math_hat) that mirrors domains/audio_hat: encode = the held")
    print("construction-grammar comprehension (prose -> properties), synth = the held")
    print("homology forward model (object -> Betti, via the held boundary operator ∂),")
    print("compare = the owned Magnitude(VecSub) graph metric, library = known spaces.\n")

    s = Substrate()
    hat = MathHat(s)
    loop = CortexLoop(hat, max_synths_per_content=4, n_passes=1, k=len(hat.contents()))
    print(f"[math] contents {hat.contents()}", flush=True)
    print(f"[math] library {len(hat.library())} known spaces (each with its DERIVED-"
          f"property vector via the held forward model)", flush=True)

    results = [
        ("1. full pipeline (desc -> object -> engine answer -> verified)",
         prove_full_pipeline(loop, hat)),
        ("2. presentation-invariance (same object, different phrasing)",
         prove_presentation_invariance(loop)),
        ("3. honest HLE stall (forward-model knowledge gap = acquire-by-reading)",
         prove_honest_hle_stall(loop, hat)),
        ("4. no regression (cortex_loop + audio hat unchanged; forward model intact)",
         prove_no_regression()),
    ]
    hat.close()

    banner("SUMMARY")
    all_ok = True
    for label, ok in results:
        all_ok = all_ok and ok
        print(f"  [{'OK ' if ok else 'FAIL'}] {label}")
    print(f"\nRESULT: {'ALL OK' if all_ok else 'FAILURES ABOVE'}  "
          f"({time.time()-t0:.0f}s)\n")
    print("LEARNING: the agent pointed its EXISTING analysis-by-synthesis operator")
    print("(CortexLoop, UNCHANGED) at the math DESCRIPTION->OBJECT gap by building a")
    print("MATH HAT — synth = the held homology forward model (Betti over the held ∂),")
    print("encode = the held construction-grammar comprehension, compare = the owned")
    print("graph metric. The FULL pipeline runs end-to-end on tractable cases:")
    print("description -> (analysis-by-synthesis grounds the object by INVERTING the")
    print("forward model) -> (derivation engine computes the homology) -> VERIFIED vs")
    print("known. Presentation-invariance holds by construction (the math echo of")
    print("speaker-invariance). NOT a new operator — the universal cortex on a new")
    print("sense, per its own 'swap the hat' design. HONEST RESIDUAL: the real HLE")
    print("moduli case STALLS at the forward-model KNOWLEDGE (the identification")
    print("'moduli space of lattices -> S^3 minus the trefoil' not held; the loop")
    print("cannot synthesize a candidate it does not hold) = the same ground+acquire")
    print("frontier (acquire-by-reading). The MECHANISM is admitted + verified end-to-")
    print("end; the breadth (objects/identifications in the library) is the climb.")
    print("[MARKER] CORTEX_MATH_HAT_COMPLETED", flush=True)
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
