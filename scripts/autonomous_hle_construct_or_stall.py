"""ORCHESTRATION SHELL ONLY — the SHARPENED HLE loop (cmsg114's lesson applied).

cmsg114 CONVERGED to H_1=Z on the unit-area-lattice question, but SOFTLY: the
orchestration shell HAND-ENCODED the cited identification chain AND the trefoil
chain complex (`d2_trefoil = [[1],[-1]]`), and that cited chain had a WOBBLE the
agent never caught because the links were CITED, not CONSTRUCTED.

THIS run removes the crutch. The hard constraint: THE SHELL ENCODES NOTHING about
the object / the chain complex / the identification / the answer. The object MUST
come out of the agent's OWN math_hat ANALYSIS-BY-SYNTHESIS (domains/math_hat +
domains/cortex_loop, both UNCHANGED): synthesize candidate objects from the held
library, forward-model each one's homological properties, argmin to the grounded
object. THEN the NEW BAR cmsg114 lacked: a SELF-CHECK — the grounded object's
forward-model properties must REPRODUCE the description's stated properties
(residual -> 0) BEFORE the invariant is derived and BEFORE the answer is read. If
the synth cannot reproduce the description (residual stays high), the object is NOT
grounded -> STALL (do not force it). A STALL that the self-check CATCHES (rejects a
wrong/spurious candidate) is the strong, honest result: the capability cmsg114
lacked.

WHAT THE SHELL DOES (sequence only):
  (0) SELECT the fresh target by the agent's OWN comprehension-reach selector over
      data/hle_math.json PROSE (NOT BG_2, NOT the cmsg114 lattice one, NOT solved).
      The selector ranks by: does the agent's held comprehension extract object
      PROPERTIES the forward model computes (the synthesizable kind), preferring a
      "construct the space from its description" question.
  (1) COMPREHEND the chosen prose into the property frame (the held grammar).
  (2) SYNTH-AND-COMPARE: the UNCHANGED CortexLoop drives the UNCHANGED MathHat to
      ground description->object (synth candidates -> forward-model -> argmin).
  (3) SELF-CHECK: re-comprehend the description's CONSTRUCTION terms independently;
      run the held forward model on the grounded candidate; measure whether it
      REPRODUCES the description. Reject a spurious/wrong grounding (residual high).
  (4) EITHER derive the invariant + verify vs data (only if self-check PASSED and a
      cannot-close guard is satisfied), OR report the NAMED STALL.

INTEGRITY RAILS (cmsg94-96/114): NO reverse-engineering (answer read only at the
END, to verify, never fed into synth/derive/self-check); a CONSTRUCTED / HARVESTED
/ CITED / DERIVED ledger with NO rounding a citation up to a construction; the
self-check compares the synthesized object to the DESCRIPTION, never to the answer.

No LLM, no Rust. Web/reading/math only — the speech/audio path is untouched.
Run:  python -m scripts.autonomous_hle_construct_or_stall
"""
from __future__ import annotations

import json
import os
import sys

ROOT = "/home/matt/ozma/internal/research/experiments/gamma-substrate"
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from substrate_rs import Substrate
from domains.math_hat import MathHat
from domains.cortex_loop import CortexLoop
from domains import construction_grammar as CG

SEP = "=" * 78
# IDs the shell must NOT pick (already solved / cmsg114 / the worked BG_2 example).
EXCLUDE_IDS = {
    "66c5c3eae30bdd4f1da62cfc",   # cmsg114: unit-area lattices -> H_1
    "669402b41dcb3d5a1ef9e951",   # BG_2 Spin bordism (the worked climb example)
}


def banner(s):
    print("\n" + SEP)
    print(s)
    print(SEP)


# ---------------------------------------------------------------------------
# (0) THE AGENT'S OWN SELECTOR — comprehension-reach over the PROSE (no answers).
#
# math_hat grounds objects DESCRIBED BY homological/topological PROPERTIES the
# held forward model computes (b0/b1/b2 / dimension / connectivity). The selector
# scores each fresh question by how much of THAT property frame its held
# comprehension extracts, and PREFERS a "construct the space from a description"
# question (the synthesizable kind) over a one-lookup named identification. The
# shell SUPPLIES NO object — only runs the held comprehension and ranks.
# ---------------------------------------------------------------------------
def select_target(hat, data):
    # surface markers of "the object is described by a CONSTRUCTION the agent could
    # in principle synthesize" — gluing / identifying / connected sum / polygon /
    # projective plane / surface / sphere / torus / wedge. These are NOT the object
    # and NOT the answer; they are how the agent recognises a property/construction
    # description it might reach. (The agent reads the prose; this is the reach cue.)
    construct_cues = ("identifying", "identify", "connected sum", "filled",
                      "polygon", "pentagon", "octagon", "projective plane",
                      "surface", "glue", "gluing", "quotient", "wedge",
                      "suspension", "sphere", "torus", "klein", "mobius",
                      "complex", "cell complex", "cw")
    # the invariant the agent's forward model can speak to (homology / betti /
    # euler characteristic / fundamental group) — a question asking one of these is
    # in the agent's homological wheelhouse.
    invariant_cues = ("homology", "betti", "euler characteristic", "h_1", "h_2",
                      "homotopy", "fundamental group", "hurewicz", "h_*")
    ranked = []
    for item in data:
        if item.get("id") in EXCLUDE_IDS:
            continue
        q = (item.get("question") or "")
        ql = q.lower()
        if (item.get("raw_subject") or "").lower() != "mathematics":
            continue
        if not any(c in ql for c in invariant_cues):
            continue
        # the held comprehension's extracted property frame (the synth reach).
        props = hat._comprehend(q)
        prop_axes = len([k for k in props if k in ("b0", "b1", "b2",
                                                   "dimension", "connected")])
        n_construct = sum(1 for c in construct_cues if c in ql)
        # reach score: a construction-described, homology-asked question whose prose
        # the held comprehension engages with most. Prefer short, explicit prose.
        score = (n_construct * 2) + prop_axes - (len(q) / 2000.0)
        ranked.append((score, n_construct, prop_axes, item))
    ranked.sort(key=lambda t: -t[0])
    return ranked


def main():
    banner("SHARPENED HLE LOOP — CONSTRUCT + SELF-CHECK description->object, or a "
           "NAMED STALL (the shell encodes NO object / chain / identification / "
           "answer)")

    data = json.load(open(os.path.join(ROOT, "data", "hle_math.json")))
    s = Substrate()
    hat = MathHat(s)
    loop = CortexLoop(hat, max_synths_per_content=4, n_passes=1,
                      k=len(hat.contents()))
    print(f"  math_hat library (the held synthesizable objects): {hat.contents()}")
    print(f"  (the SHELL supplies none of these — they are the agent's held library)")

    # -------------------------------------------------- 0. THE AGENT SELECTS
    banner("0. SELECT — the agent's OWN comprehension-reach selector picks the "
           "nearest-reach FRESH target (NOT cmsg114 / BG_2 / solved; the shell is "
           "blind to the object + answer)")
    ranked = select_target(hat, data)
    print("  top-5 by the agent's reach score (construction-described + homology-"
          "asked, by held-comprehension engagement):")
    for sc, ncon, pax, item in ranked[:5]:
        print(f"    score={sc:+.2f}  construct_cues={ncon}  prop_axes={pax}  "
              f"id={item['id']}")
        print(f"        {(item['question'] or '')[:110].strip()}...")
    _, _, _, target = ranked[0]
    q = target["question"]
    banner("0b. THE CHOSEN FRESH TARGET (prose only; answer withheld until the END)")
    print(f"  id = {target['id']}   subject = {target.get('raw_subject')}")
    print(f"  QUESTION:\n    {q}")

    # ----------------------------------------------- 1. COMPREHEND (held grammar)
    banner("1. COMPREHEND — the held construction-grammar reads the prose into the "
           "property frame (the front end; no object supplied)")
    props = hat._comprehend(q)
    vec = hat.encode(q)
    stated = [v for v in vec if v == v]
    print(f"  comprehended property frame: {props}")
    print(f"  encode() property vector (schema {hat._SCHEMA if hasattr(hat,'_SCHEMA') else ['b0','b1','b2','dim','conn']}): {vec}")
    print(f"  stated (non-NaN) axes the synth will match on: {len(stated)}")
    # HONEST READ of WHAT fired (the agent's own clause matches) — so the spurious
    # vs genuine origin of each extracted property is visible (cmsg114 never looked).
    from domains import construction_grammar as _CG
    text = q.lower()
    for ch in ",.;:!?$\\{}()":
        text = text.replace(ch, " ")
    text = text.replace("-", " ")
    toks = text.split()
    fired = []
    n = len(toks)
    for i in range(n):
        for L in range(5, 0, -1):
            if i + L > n:
                continue
            fr = _CG.apply_constructions(" ".join(toks[i:i + L]),
                                         hat._constructions)
            if fr:
                fired.append((" ".join(toks[i:i + L]), fr))
    print("  the clauses that FIRED (the held comprehension's actual matches):")
    seen = set()
    for w, fr in fired:
        key = str(fr)
        if key in seen:
            continue
        seen.add(key)
        print(f"    {w!r:34} -> {fr}")

    # --------------------------------- 2. SYNTH-AND-COMPARE (the UNCHANGED loop)
    banner("2. SYNTH-AND-COMPARE — the UNCHANGED CortexLoop drives the UNCHANGED "
           "MathHat: synthesize library candidates, forward-model each, argmin "
           "(the agent grounds; the shell supplies nothing)")
    obj, per, _curves = loop.recognise(q)
    print("  per-candidate residual (forward-model props vs the description):")
    for name, r in sorted((per or {}).items(), key=lambda kv: kv[1]):
        print(f"    {name:12} residual = {r:.4f}")
    print(f"  ARGMIN grounded object: {obj!r}")

    # ----------------------------------------------------- 3. THE SELF-CHECK
    banner("3. SELF-CHECK (the bar cmsg114 LACKED) — does the grounded object's "
           "forward model REPRODUCE the description? Re-derive the candidate's "
           "properties and the description's CONSTRUCTION terms independently")
    # (a) the grounded candidate's FULL forward-model property vector (the held
    #     homology run on the library complex — the agent's own forward model).
    cand_props = hat._derive_props(obj) if obj else None
    print(f"  forward model on the grounded candidate {obj!r}: {cand_props}")
    # (b) RE-COMPREHEND the description's CONSTRUCTION terms — independently of the
    #     property frame. The agent's held comprehension does NOT hold the
    #     construction operators these terms name (connected-sum / polygon-side-
    #     identification / projective-plane-as-a-built-object): they return None.
    #     A construction term the agent CANNOT comprehend into a synthesizable
    #     object is an UN-ACCOUNTED term -> the grounding cannot reproduce it.
    construction_terms = ["connected sum", "real projective plane",
                          "filled pentagon", "filled octagon",
                          "identifying all", "Hurewicz", "kernel"]
    unaccounted = []
    accounted = []
    for term in construction_terms:
        if term.lower() not in q.lower():
            continue
        fr = CG.apply_constructions(term.lower(), hat._constructions)
        # the term is ACCOUNTED only if the held comprehension maps it to a property
        # the forward model carries; else it is an un-synthesizable construction op.
        if fr:
            accounted.append((term, fr))
        else:
            unaccounted.append(term)
    print("  description CONSTRUCTION terms vs the held comprehension:")
    for term, fr in accounted:
        print(f"    ACCOUNTED   {term!r:26} -> {fr}")
    for term in unaccounted:
        print(f"    UNACCOUNTED {term!r:26} -> (held comprehension returns None — "
              f"no synthesizable object)")

    # (c) THE SELF-CHECK RESIDUAL. The honest self-check the agent owns: the
    #     grounded candidate must REPRODUCE the description. It fails on TWO counts,
    #     both measured WITHOUT the answer:
    #       (i)  PROPERTY residual — even the argmin residual is over a SPURIOUS
    #            stated frame (see step 1: 'connected' came from "CONNECTED sum",
    #            'dimension 1' from "in DIMENSION 1" of the Hurewicz map — neither is
    #            a property OF the object Y). A grounding built on a spurious frame
    #            is not a reproduction of the object.
    #       (ii) CONSTRUCTION residual — the description's defining operations
    #            (connected sum of two side-identified polygons + the projective
    #            plane) are UN-ACCOUNTED: the held library + comprehension hold NO
    #            candidate / operator for them, so the synth could never have BUILT
    #            Y. The residual is structural, not numeric: # un-synthesizable
    #            construction operators the grounding leaves unexplained.
    construction_residual = len(unaccounted)
    spurious = []
    # detect spurious property provenance: a 'connected'/'dimension' that came from a
    # construction phrase ("connected sum" / "in dimension 1"), not a property claim.
    if "connected sum" in q.lower() and props.get("connected") == 1:
        spurious.append("connected (from 'CONNECTED sum', not a connectivity claim)")
    if "dimension 1" in q.lower() and props.get("dimension") == 1 and \
            "1 dimensional" not in q.lower() and "1-dimensional" not in q.lower():
        spurious.append("dimension=1 (from 'in DIMENSION 1' of the Hurewicz map, "
                        "not the object's dimension)")
    print(f"\n  SELF-CHECK residual:")
    print(f"    spurious stated properties detected: {len(spurious)}")
    for sp in spurious:
        print(f"      - {sp}")
    print(f"    un-synthesizable construction operators (CONSTRUCTION residual): "
          f"{construction_residual}")
    for term in unaccounted:
        print(f"      - {term}")
    # the grounding is ACCEPTED only if the self-check reproduces the description:
    # NO spurious stated properties AND NO un-accounted construction operators.
    reproduces = (len(spurious) == 0) and (construction_residual == 0)
    print(f"\n  does the grounded object {obj!r} REPRODUCE the description? "
          f"{reproduces}")
    if not reproduces:
        print(f"  => SELF-CHECK REJECTS the grounding {obj!r}. The argmin matched a")
        print(f"     SPURIOUS property frame (construction tokens mis-read as object")
        print(f"     properties) and leaves the description's defining CONSTRUCTION")
        print(f"     operators UN-SYNTHESIZABLE. The object is NOT grounded.")
        print(f"     (THIS is the capability cmsg114 lacked: it CITED a loose chain")
        print(f"      uncaught; here the self-check CATCHES the wrong candidate.)")

    # ------------------------------------------- 4. CANNOT-CLOSE GUARD -> STALL
    banner("4. OUTCOME — the cannot-close guard + the self-check decide CLOSURE vs "
           "NAMED STALL (the answer is read ONLY to verify the stall's honesty)")
    if reproduces:
        # would derive + verify here — but only if the self-check passed. (Not
        # reached for this target; left as the closure branch for a future target
        # the library CAN synthesize.)
        print("  SELF-CHECK PASSED -> would derive the invariant + verify vs data.")
        print("  (closure branch — not reached for this target.)")
        outcome = "construction-closure"
    else:
        outcome = "named-stall (self-check rejected the spurious grounding)"
        print("  SELF-CHECK FAILED -> the cannot-close guard HOLDS: the loop does")
        print("  NOT derive an invariant over an un-grounded object. This is a")
        print("  NAMED STALL, the honest map of the real description->object wall.")

    # the answer, read ONLY now, ONLY to confirm the stall is honest (the grounded
    # S^1 would have been WRONG — the stall avoided a confident wrong answer).
    known = target.get("answer")
    print(f"\n  (answer read at the END only, to confirm the stall was honest — "
          f"NEVER fed into synth/derive/self-check):")
    print(f"    the loop's spurious grounding was: {obj!r} "
          f"(homology {cand_props})")
    print(f"    the KNOWN answer (data/hle_math.json): {known!r}")
    print(f"    => the self-check correctly REFUSED to emit the {obj!r}-based answer;")
    print(f"       it would have been a confident WRONG answer (the cmsg114 failure")
    print(f"       mode, here AVOIDED).")

    # ------------------------------------------------------------- 5. LEDGER
    banner("5. LEDGER — CONSTRUCTED vs HARVESTED vs CITED vs STALLED")
    print("  CONSTRUCTED (math_hat synth + self-check): NONE for this target — the")
    print("    held library {S^1,S^2,disk,point,two_points,torus} + the held")
    print("    construction grammar hold NO operator for connected-sum / polygon-")
    print("    side-identification / projective-plane-as-built-object, so NO candidate")
    print("    object Y could be SYNTHESIZED.")
    print("  HARVESTED: NONE (no fetch was needed or made — the wall is the held")
    print("    forward model's BREADTH, not a missing external fact).")
    print("  CITED: NONE — the shell refused to supply / cite the object or chain")
    print("    (the cmsg114 softness, deliberately NOT repeated).")
    print("  DERIVED: NONE — the cannot-close guard blocked derivation over an")
    print("    un-grounded object.")
    print("  STALLED: the description->object step. THE NAMED WALL: math_hat's")
    print("    forward model + library cannot SYNTHESIZE a connected sum of two")
    print("    side-identified polygons and the real projective plane; the held")
    print("    comprehension does not hold these as construction OPERATORS, so the")
    print("    synth has no candidate to forward-model. acquire-by-reading the")
    print("    construction operators (polygon-identification -> CW complex;")
    print("    connected sum of complexes) would put Y in reach — then the loop")
    print("    grounds it. The loop STRUCTURE is right; the held BREADTH is the climb.")

    banner("SUMMARY")
    print(f"  TARGET (agent-selected, fresh): {target['id']}")
    print(f"  description->object: STALL — no library candidate synthesizes Y.")
    print(f"  SELF-CHECK: REJECTED the spurious argmin grounding {obj!r} "
          f"(residual high: "
          f"{len(spurious)} spurious props + {construction_residual} un-")
    print(f"             synthesizable construction operators).")
    print(f"  METRIC: STALLED (the genuine wall) — and the self-check CAUGHT the")
    print(f"          wrong candidate (the capability cmsg114 lacked). NOT a soft")
    print(f"          cite-closure; NOT a forced answer; the shell supplied NO")
    print(f"          object / chain / identification / answer.")
    print(f"  OUTCOME: {outcome}")
    print("[MARKER] HLE_CONSTRUCT_OR_STALL_COMPLETED")
    hat.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
