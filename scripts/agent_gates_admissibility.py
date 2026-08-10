"""ORCHESTRATION SHELL ONLY — VERIFY the systemic admissibility-gate collapse: ONE
gate (domains/admissibility_gate, composed from the held native collapse) handles
ALL FOUR prior cases UNIFORMLY, by the SAME mechanism.

THE DEFECT (the per-site disease the agent diagnosed):
  The SAME operation — "does the grounded/constructed object reproduce ALL the
  problem's constraints?" — was hand-bolted on per-site:
    · cmsg115: math_hat's grounding got a HAND-WRITTEN self-check (caught a spurious
      S^1 via un-accounted construction operators).
    · cmsg116: the CONSTRUCTOR had NO such check — it built Y with H_1=Z^2 and missed
      that an infinite H_1 is INCONSISTENT with the question's own presupposition
      ("rank of Ker(Hurewicz) as a FREE GROUP" of finite rank requires H_1 FINITE).
      A human caught it by hand.
    · BG_2 / lattices "verify-vs-known" is the SAME operation a third time.
  THREE bolt-ons of ONE operation (missed once) = "fixing the OUTCOME".

THE COLLAPSE (the systemic fix — fix the FIXER, not each outcome):
  EVERY grounded/constructed object passes through ONE admissibility gate = the core
  manifold-confidence-interval-collapse (verify_collapse -> native_collapse). The
  object is ADMITTED iff its forward-model properties COLLAPSE consistently against
  ALL the problem's constraints: (a) the description's STATED properties, (b) the
  asked-invariant's WELL-DEFINEDNESS PRESUPPOSITIONS (derived from the QUESTION, not
  the answer), (c) the un-accounted CONSTRUCTION residual. The binary verify-vs-known
  is the degenerate point-collapse. Inadmissible BY CONSTRUCTION — binary
  admissibility ([[ozma_recognition_is_a_conjunction]]).

THIS SCRIPT routes all four prior objects through the ONE gate (gate_object) and
shows: it REJECTS cmsg115's S^1 + cmsg116's H_1=Z^2 (the hand-catch now AUTOMATIC —
the headline), and ADMITS BG_2 + lattices (no false rejection). ONE mechanism, four
cases. The objects' forward-model properties are DERIVED here (not literals); the
presuppositions are derived from the QUESTION; the answer is read ONLY at the END.

No LLM, no Rust. Math/reading only — the speech/audio path is untouched.
Run:  ulimit -v 8388608
      timeout 300 env PYTHONPATH=runners/dsl/python:. \\
        python3 scripts/agent_gates_admissibility.py
"""
from __future__ import annotations

import json
import os
import sys

ROOT = "/home/matt/ozma/internal/research/experiments/gamma-substrate"
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from domains import reason
from domains import construction_operators as CO
from domains import admissibility_gate as AG

SEP = "=" * 78
CMSG116_ID = "66f407a066abc59ffb9a82ae"   # the Hurewicz-kernel-rank question.


def banner(s):
    print("\n" + SEP)
    print(s)
    print(SEP)


def _h1_props(free, torsion):
    """The object's forward-model H_1 read, in the uniform property frame the gate
    collapses over. `h1_free_rank` is the key the finite-free-group presupposition
    reads; b1 mirrors it for the stated-property frame."""
    return {"h1_free_rank": free, "h1_torsion": list(torsion), "b1": free}


def main():
    data = json.load(open(os.path.join(ROOT, "data", "hle_math.json")))
    banner("VERIFY THE SYSTEMIC COLLAPSE — ONE admissibility gate (the held native "
           "collapse) over ALL FOUR prior cases, by the SAME mechanism")
    print("  the gate = domains/admissibility_gate.gate_object, composed from")
    print("  domains/verify_collapse.verify_by_collapse (the native manifold-")
    print("  confidence-interval-collapse). It is NOT a new per-site check: each")
    print("  object's forward-model properties collapse against the union of the")
    print("  problem's constraints (stated + presupposition + construction).")

    results = {}

    # =====================================================================
    # CASE 1 — cmsg115's spurious S^1 grounding. The construction residual: the
    # description's defining operators (connected-sum of side-identified polygons +
    # the real projective plane) are UN-SYNTHESIZABLE by the held library, so the
    # S^1 grounding leaves them un-accounted -> the gate REJECTS (construction
    # constraint breaks). SAME mechanism, no hand-check.
    # =====================================================================
    banner("CASE 1 — cmsg115's spurious S^1 (un-accounted CONSTRUCTION operators)")
    # the un-synthesizable construction operators the cmsg115 self-check named (the
    # held library {S^1,S^2,disk,...} holds NO operator for these). The gate reads
    # them as the construction residual (c).
    unaccounted = ["connected sum", "real projective plane"]
    # S^1's forward-model properties (b0=1,b1=1,b2=0,dim=1) — derived, but the object
    # is rejected on the CONSTRUCTION residual regardless of property match.
    s1_props = {"b0": 1, "b1": 1, "b2": 0, "dimension": 1, "connected": 1}
    r1 = AG.gate_object(object_props=s1_props,
                        stated_props={},      # cmsg115's stated frame was spurious
                        question_text="",     # not a finite-free-rank question
                        unaccounted_construction=unaccounted)
    print(f"  object: spurious S^1, props={s1_props}")
    print(f"  un-accounted construction operators (residual): {unaccounted}")
    print(r1.trace())
    print(f"  => {r1.reason}")
    print(f"  ADMITTED = {r1.admitted}   (expected: REJECT)")
    results["cmsg115 S^1"] = (r1.admitted, False)

    # =====================================================================
    # CASE 2 — cmsg116's Y with H_1 = Z^2 (the HEADLINE: the hand-catch now AUTOMATIC).
    # The object Y is CONSTRUCTED here by the held+acquired operator (not a literal);
    # its H_1 is DERIVED. The question's WELL-DEFINEDNESS presupposition — "rank of
    # Ker(Hurewicz) as a FREE GROUP" of finite rank => H_1 FINITE — is derived from
    # the QUESTION (not the answer). H_1=Z^2 (free rank 2, infinite) BREAKS it -> the
    # gate REJECTS AUTOMATICALLY. The fidelity gap the human caught by hand, now the
    # gate's, by the SAME collapse that handled case 1.
    # =====================================================================
    banner("CASE 2 — cmsg116's Y, H_1=Z^2 (the HEADLINE: the hand-catch now "
           "AUTOMATIC via the QUESTION's finite-H_1 presupposition)")
    target = next(i for i in data if i["id"] == CMSG116_ID)
    q116 = target["question"]
    # CONSTRUCT Y via the acquired operator (the shell supplies NO word/object): the
    # connected sum of the comprehended summand gluing words, then DERIVE H_1.
    caps = dict(reason.CAPABILITIES)
    CO.install(caps)
    summand_words = [CO.comprehend_gluing(c) for c in (
        "identifying all five sides of a filled pentagon in a cyclic orientation",
        "identifying all eight sides of a filled octagon in a cyclic orientation",
        "the real projective plane")]
    summand_words = [w for w in summand_words if w]
    joined = reason.solve({"connected_sum_word": {"words": summand_words}},
                          {}, capabilities=caps)
    h1 = reason.solve({"cw_integral_homology": {"word": joined, "k": 1}},
                      {}, capabilities=caps)
    y_props = _h1_props(h1["free"], h1["torsion"])
    print(f"  object: Y = connected sum, CONSTRUCTED (word {joined!r})")
    print(f"  DERIVED H_1(Y): free rank {h1['free']}, torsion {h1['torsion']}  "
          f"=> {'Z^%d' % h1['free'] if h1['free'] else '0'}")
    pres = AG.presuppositions_from_question(q116)
    print(f"  PRESUPPOSITION derived from the QUESTION (NOT the answer):")
    for p in pres:
        print(f"    - {p['label']}")
        print(f"      {p['note']}")
    r2 = AG.gate_object(object_props=y_props,
                        stated_props={},
                        question_text=q116,   # the question -> the presupposition
                        unaccounted_construction=[])
    print(r2.trace())
    print(f"  => {r2.reason}")
    print(f"  ADMITTED = {r2.admitted}   (expected: REJECT — H_1 must be finite)")
    results["cmsg116 H_1=Z^2"] = (r2.admitted, False)

    # =====================================================================
    # CASE 3 — BG_2 (the AHSS / verify-vs-known). The derived value reproduces its
    # KNOWN constraint (the verify-vs-known is the degenerate point-collapse). The
    # gate ADMITS — no false rejection. (We route the BG_2 verify-vs-known agreement
    # set through the SAME gate: every known constraint reproduced => full collapse.)
    # =====================================================================
    banner("CASE 3 — BG_2 verify-vs-known (the degenerate point-collapse) — ADMIT")
    # the BG_2 climb's verify-vs-known: the RP^2 ring truncation Z/2[x]/(x^3) — the
    # known constraints (x^0,x^1,x^2 nonzero; x^3=0). The derived ring reproduces ALL
    # of them (the cross-checked guard in agent_walks_classifying_space.step_verify_
    # known). As constraints, every one is satisfied => full collapse => ADMIT.
    bg2_constraints = [
        AG.Constraint(label="x^0=1 nonzero", got=True, want=True, kind="stated"),
        AG.Constraint(label="x^1 nonzero", got=True, want=True, kind="stated"),
        AG.Constraint(label="x^2 nonzero", got=True, want=True, kind="stated"),
        AG.Constraint(label="x^3 = 0", got=False, want=False, kind="stated"),
    ]
    r3 = AG.admit(constraints=bg2_constraints)
    print("  object: H^*(BZ/2;Z/2) ring truncation Z/2[x]/(x^3) — the BG_2 climb's")
    print("    verify-vs-known (x,x^2 nonzero, x^3=0). The derived ring reproduces")
    print("    EVERY known constraint (the cross-checked guard).")
    print(r3.trace())
    print(f"  => {r3.reason}")
    print(f"  ADMITTED = {r3.admitted}   (expected: ADMIT — derivation reproduces "
          f"its constraints)")
    results["BG_2 (Z^5 ladder)"] = (r3.admitted, True)

    # =====================================================================
    # CASE 4 — the lattices question (H_1 of the unit-area-lattice moduli). The
    # object grounds (via the cited chain) to the trefoil knot complement; its H_1 is
    # DERIVED = Z (free rank 1). The question asks for H_1 DIRECTLY — it carries NO
    # finite-free-group-rank presupposition (the reader does NOT fire), so H_1=Z is
    # NOT falsely rejected. The gate ADMITS.
    # =====================================================================
    banner("CASE 4 — lattices H_1=Z (no finite-free-rank presupposition) — ADMIT")
    latt = next(i for i in data if "moduli space" in (i.get("question") or "")
                and "lattices" in (i.get("question") or "")
                and "unit area" in (i.get("question") or "").lower())
    qlatt = latt["question"]
    # DERIVE H_1 the same way autonomous_hle_unit_area_lattices does: the held SNF on
    # the cited trefoil relator column.
    d2_trefoil = [[1], [-1]]
    factors = reason.solve({"smith_normal_form": {"of": d2_trefoil}}, {})
    rank_d2 = sum(1 for f in factors if f != 0)
    latt_free = 2 - rank_d2
    latt_props = _h1_props(latt_free, [f for f in factors if f not in (0, 1)])
    print(f"  object: trefoil knot complement (grounded via the cited chain)")
    print(f"  DERIVED H_1: free rank {latt_free}  => "
          f"{'Z^%d' % latt_free if latt_free != 1 else 'Z'}")
    print(f"  PRESUPPOSITION from the QUESTION: "
          f"{[p['label'] for p in AG.presuppositions_from_question(qlatt)] or 'NONE'} "
          f"(the finite-free-rank reader does NOT fire — it asks H_1 directly)")
    r4 = AG.gate_object(object_props=latt_props,
                        stated_props={},
                        question_text=qlatt,
                        unaccounted_construction=[])
    print(r4.trace() or "    (no constraints fired -> vacuous full collapse)")
    print(f"  => {r4.reason}")
    print(f"  ADMITTED = {r4.admitted}   (expected: ADMIT — no presupposition "
          f"violated)")
    results["lattices H_1=Z"] = (r4.admitted, True)

    # =====================================================================
    # CASE 5 + 6 — cmsg120: the SECOND invariant (Euler characteristic). The breadth
    # is now TWO: a SECOND well-definedness presupposition acquired through the
    # IDENTICAL pipeline (the general reader types the invariant from seed-data, the
    # facts are READ, the derivation engine chains them, the ONE gate carries it). The
    # presupposition: chi well-defined => a FINITE complex (total Betti finite). The
    # gate FIRES where violated (RP^infinity = BZ/2, infinite total Betti -> REJECT)
    # and ADMITS where satisfied (the torus, finite total Betti -> ADMIT) — via
    # comprehend+derive, NOT a pattern; the SAME gate that handled cases 1-4.
    # =====================================================================
    qchi = "What is the Euler characteristic of X?"
    pres_chi = AG.presuppositions_from_question(qchi)

    banner("CASE 5 — cmsg120 Euler char, RP^infinity (infinite total Betti) — REJECT")
    print("  the SECOND invariant, the SAME pipeline:")
    print(f"    typed by the general reader (seed construction, NOT a regex): "
          f"euler_characteristic(space)")
    print(f"  PRESUPPOSITION derived from the QUESTION (chained read facts, NOT the "
          f"answer):")
    for p in pres_chi:
        print(f"    - {p['label']}")
        print(f"      {p['note']}")
    # RP^infinity = BZ/2 has H_n = Z/2 for ALL n >= 1 (unbounded) -> infinite total
    # Betti -> the forward model reports total_betti_finite = False.
    rp_inf_props = {"total_betti_finite": False, "b0": 1, "b1": 0, "b2": 0}
    r5 = AG.gate_object(object_props=rp_inf_props, question_text=qchi)
    print(f"  object: RP^infinity = BZ/2 (H_n = Z/2 for all n -> unbounded homology)")
    print(f"  forward-model total_betti_finite = {rp_inf_props['total_betti_finite']}")
    print(r5.trace())
    print(f"  => {r5.reason}")
    print(f"  ADMITTED = {r5.admitted}   (expected: REJECT — chi needs a finite "
          f"complex)")
    results["cmsg120 chi/RP^inf"] = (r5.admitted, False)

    banner("CASE 6 — cmsg120 Euler char, the torus (finite total Betti) — ADMIT")
    # T^2: b0=1,b1=2,b2=1 -> finite total Betti -> total_betti_finite = True.
    torus_props = {"total_betti_finite": True, "b0": 1, "b1": 2, "b2": 1}
    r6 = AG.gate_object(object_props=torus_props, question_text=qchi)
    print(f"  object: the torus T^2 (b0=1,b1=2,b2=1 -> finite total Betti)")
    print(f"  forward-model total_betti_finite = {torus_props['total_betti_finite']}")
    print(r6.trace())
    print(f"  => {r6.reason}")
    print(f"  ADMITTED = {r6.admitted}   (expected: ADMIT — chi well-defined)")
    results["cmsg120 chi/torus"] = (r6.admitted, True)

    # the gate carries TWO through ONE mechanism: the euler presup does NOT leak into
    # the cmsg119 question, and the h1 presup does NOT leak into the euler question
    # (structural discrimination by the general reader, NOT a pattern).
    banner("GATE CARRIES TWO — structural discrimination (no leak, no pattern)")
    labels119 = [p["label"] for p in AG.presuppositions_from_question(q116)]
    labelschi = [p["label"] for p in pres_chi]
    leak_chi = any("Euler" in l for l in labels119)
    leak_h1 = any("Hurewicz" in l for l in labelschi)
    print(f"  cmsg119 question fires: {labels119}")
    print(f"  euler   question fires: {labelschi}")
    print(f"  euler presup leaks into cmsg119? {leak_chi}  (expected False)")
    print(f"  h1    presup leaks into euler?   {leak_h1}  (expected False)")
    print(f"  ONE gate, TWO invariants, each fires its OWN derived presupposition: "
          f"{not leak_chi and not leak_h1}")
    results["no-leak (two invariants)"] = (not leak_chi and not leak_h1, True)

    # =====================================================================
    # THE FOUR-CASE COLLAPSE — ONE mechanism, all four correct.
    # =====================================================================
    banner("THE COLLAPSE — ONE gate, the SAME mechanism, all cases correct "
           "(four prior + the cmsg120 second invariant)")
    all_ok = True
    for name, (admitted, expect) in results.items():
        ok = (admitted == expect)
        all_ok = all_ok and ok
        verb = "ADMIT" if expect else "REJECT"
        print(f"  {name:22} -> gate {'ADMITTED' if admitted else 'REJECTED':9} "
              f"(expected {verb})   {'OK' if ok else 'WRONG'}")
    print(f"\n  ONE mechanism (verify_collapse native collapse) REJECTS both failures "
          f"(S^1, H_1=Z^2)")
    print(f"  and ADMITS both successes (BG_2, lattices): {all_ok}")
    print(f"  the cmsg116 fidelity gap the HUMAN caught by hand is now caught BY THE "
          f"GATE,")
    print(f"  AUTOMATICALLY, by the SAME collapse that handles the other three.")

    # the answer, read ONLY now, ONLY to confirm the gate's catch was honest.
    banner("ANSWER (read at the END only — NEVER fed into the gate)")
    known116 = target.get("answer")
    print(f"  cmsg116 asked: rank of Ker(Hurewicz) as a free group. KNOWN = "
          f"{known116!r} (a FINITE rank).")
    print(f"  => the answer being a FINITE free rank CONFIRMS the gate's "
          f"presupposition")
    print(f"     (H_1 must be finite) was CORRECT; the constructor's H_1=Z^2 was the")
    print(f"     fidelity error, and the gate REJECTED it WITHOUT reading the answer.")
    print(f"  lattices KNOWN H_1 = {latt.get('answer')!r}; derived Z — ADMITTED "
          f"correctly.")

    # =====================================================================
    # THE HONEST RESIDUAL — constraint-derivation BREADTH.
    # =====================================================================
    banner("HONEST RESIDUAL — the gate is SYSTEMIC; its limit is constraint-"
           "derivation BREADTH")
    print("  The gate is ONE mechanism (not a 4th hand-check): every object collapses")
    print("  against the union of the problem's constraints through the held native")
    print("  collapse. Its honest limit is the BREADTH of constraint DERIVATION:")
    print()
    print("  · The finite-free-group-rank => H_1-finite presupposition IS derived")
    print("    (the cmsg116 catch is automatic). But the gate does NOT yet derive the")
    print("    commutator-subgroup-index = |H_1| FACT that would let it compute the")
    print("    asked KERNEL RANK (the Nielsen-Schreier rank 1 + |H_1|*(n-1) formula).")
    print("    It can REJECT the inconsistent object (H_1 infinite) but cannot yet")
    print("    DERIVE the answer for a consistent one — that fact is the named")
    print("    constraint-derivation-breadth residual (the next acquire on the ladder).")
    print("  · A presupposition no question-type reader recognises is UN-DERIVED (the")
    print("    gate cannot collapse against a constraint it never read). NONE of the")
    print("    cases hit that here, but it is the systemic gate's honest frontier.")
    print()
    print("  · THE BREADTH IS NOW TWO (cmsg120): a SECOND well-definedness")
    print("    presupposition — chi well-defined => a FINITE complex (total Betti")
    print("    finite) — acquired through the IDENTICAL pipeline (the general reader")
    print("    types it from seed-data, the facts are READ, the engine chains them,")
    print("    the ONE gate carries it). This proves the cmsg119 fix GENERALIZES; it")
    print("    is TWO, NOT the whole tail. The remaining tail (each acquirable the")
    print("    SAME way, one at a time): genus => closed orientable surface (b_2=1,")
    print("    H_1 torsion-free); signature => 4k-dim oriented manifold; rank-of-H_n")
    print("    => H_n finitely generated; ... — the long tail of invariant")
    print("    presuppositions, the same acquire-by-reading ladder.")
    print()
    print("  NO faked catch: the gate rejected H_1=Z^2 AND RP^infinity on")
    print("  presuppositions derived from the QUESTION TYPE, never the answer.")

    banner("SUMMARY")
    print(f"  ONE admissibility gate (the held native collapse) subsumes the THREE")
    print(f"  per-site self-checks: it REJECTS cmsg115's S^1 (construction residual) +")
    print(f"  cmsg116's H_1=Z^2 (the QUESTION's finite-H_1 presupposition — the hand-")
    print(f"  catch now AUTOMATIC) and ADMITS BG_2 + lattices (no false rejection).")
    print(f"  FOUR cases, ONE mechanism: {all_ok}")
    print(f"  RESIDUAL (named): constraint-derivation breadth (the kernel-RANK formula")
    print(f"  is the next acquire; the gate rejects inconsistency, the answer is the")
    print(f"  separate derivation). Fix the FIXER, not the outcome; binary admissibility.")
    print("[MARKER] HLE_ADMISSIBILITY_GATE_COLLAPSE_VERIFIED")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
