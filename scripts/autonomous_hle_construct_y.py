"""ORCHESTRATION SHELL ONLY — ACQUIRE the description->object CONSTRUCTOR the
cmsg115 stall NAMED, VERIFY it vs KNOWN surfaces, RE-RUN the stalled target, report
the honest depth-reached.

cmsg115 STALLED honestly: math_hat's self-check CAUGHT a spurious grounding and
NAMED the wall — HLE describes the object by CONSTRUCTION (a polygon with a side-
identification WORD / a connected sum / RP^2 as a built object), never by the
b0/b1/b2 property frame its fixed library matches. The named missing piece =
CONSTRUCTION OPERATORS, "acquirable by reading." THIS run has the agent ACQUIRE them
into itself (the same ground+acquire / specify->emit ladder that built ∂ / Betti /
SNF / cup-product, cmsg84-96): each operator REDUCES to the held machinery (the
signed ∂ in coordinates + the held Smith-normal-form over Z + the held free/torsion
read), so description->object becomes CONSTRUCT, not match-a-library.

WHAT THE SHELL DOES (sequence only — it encodes NO object / word / chain / answer):
  (0) SELECT the cmsg115 stalled target by id from the PROSE bank.
  (1) ACQUIRE — the agent SPECIFIES each construction operator (runtime_design
      specify->emit form) + a mechanical emitter INSTALLS the held composition into
      the held capability registry (reason.CAPABILITIES copy). The operators are
      ADDED TO THE AGENT (the held tower); they reduce to the held SNF.
  (2) VERIFY-vs-KNOWN — each operator must reproduce a KNOWN surface's homology
      (torus word -> [1,2,1]; RP^2 word -> H_1=Z/2; Klein -> Z⊕Z/2; genus-2 ->
      Z^4; RP^2#RP^2 -> Klein) through the agent's reason.solve evaluator. MATCH,
      never vs the answer. An operator that fails is REFUSED.
  (3) RE-RUN — COMPREHEND the target's PROSE into the summand gluing WORDS (the
      held comprehension reads "identifying all N sides of a filled <polygon>
      cyclically" -> a^N, "real projective plane" -> the built `aa`; the shell
      supplies NO word). BUILD Y = the connected sum via the acquired operator,
      DERIVE H_*(Y) as far as the held+acquired machinery reaches.
  (4) DEPTH — honestly: FULL (the Hurewicz-kernel-rank derived + verified vs the
      answer) | PARTIAL (Y built + H_1 computed, the kernel-rank the NEW named gap)
      | constructor-short. The answer is read ONLY at the END, to verify whatever
      the agent derived — NEVER fed into the constructor / comprehension / derivation.

INTEGRITY RAILS (cmsg94-96/114/115): the operators VERIFY vs KNOWN surfaces, NEVER
vs the answer; the answer is read ONLY at the end; the SHELL encodes NOTHING about Y
(no `a^5 b^8 c^2`, no chain complex, no 28) — the CONSTRUCTOR builds Y from the
comprehended gluing words; a PARTIAL lift with a named next gap is a successful
result. No LLM, no Rust. Math/reading only — the speech/audio path is untouched.

Run:  ulimit -v 8388608
      timeout 300 env PYTHONPATH=runners/dsl/python:. \\
        python3 scripts/autonomous_hle_construct_y.py
"""
from __future__ import annotations

import json
import os
import re
import sys

ROOT = "/home/matt/ozma/internal/research/experiments/gamma-substrate"
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from domains import reason
from domains import construction_operators as CO
from domains import admissibility_gate as AG

SEP = "=" * 78
TARGET_ID = "66f407a066abc59ffb9a82ae"   # cmsg115's stalled target (id only — the
                                          # shell holds NO object / word / answer).


def banner(s):
    print("\n" + SEP)
    print(s)
    print(SEP)


def main():
    banner("ACQUIRE THE description->object CONSTRUCTOR (the cmsg115 named gap), "
           "VERIFY vs KNOWN surfaces, RE-RUN the stalled target — honest depth "
           "(the shell encodes NO word / chain / answer)")

    data = json.load(open(os.path.join(ROOT, "data", "hle_math.json")))
    target = next(i for i in data if i["id"] == TARGET_ID)
    q = target["question"]

    # -------------------------------------------------- 0. THE STALLED TARGET
    banner("0. THE cmsg115 STALLED TARGET (prose only; answer withheld until the END)")
    print(f"  id = {target['id']}   subject = {target.get('raw_subject')}")
    print(f"  QUESTION:\n    {q}")

    # ------------------------------------------------------ 1. ACQUIRE
    banner("1. ACQUIRE — the agent SPECIFIES the missing construction operators "
           "(runtime_design specify->emit) + a mechanical emitter installs the held "
           "composition into the held registry (each reduces to the held SNF)")
    caps = dict(reason.CAPABILITIES)
    held_before = sorted(k for k in
                         ("polygon_identification_complex", "connected_sum_word",
                          "projective_plane_word", "cw_integral_homology")
                         if k in caps)
    print(f"  held BEFORE acquire: {held_before or 'NONE of the construction ops'}")
    for spec in CO.operator_specs():
        print(f"\n  SPECIFY {spec['name']}")
        print(f"    reduces_to : {spec['reduces_to']}")
        print(f"    meaning    : {spec['meaning']}")
    CO.install(caps)               # the mechanical emit: install the held composition
    held_after = sorted(k for k in
                        ("polygon_identification_complex", "connected_sum_word",
                         "projective_plane_word", "cw_integral_homology")
                        if k in caps)
    print(f"\n  held AFTER acquire (added to the agent's tower): {held_after}")
    print("  each routes through reason.solve and bottoms out at the held "
          "smith_normal_form / signed-∂ — no new Rust, no new primitive engine.")

    # ------------------------------------------------- 2. VERIFY-vs-KNOWN
    banner("2. VERIFY-vs-KNOWN — each operator must reproduce a KNOWN surface's "
           "homology through reason.solve (the held evaluator). MATCH, never vs the "
           "answer. An operator that fails is REFUSED")
    all_match = True
    refused = []
    for word, (name, expect) in CO.KNOWN_SURFACES.items():
        got = {}
        for k in (0, 1, 2):
            h = reason.solve({"cw_integral_homology": {"word": word, "k": k}},
                             {}, capabilities=caps)
            got[k] = (h["free"], tuple(h["torsion"]))
        exp = {k: (f, tuple(t)) for k, (f, t) in expect.items()}
        ok = (got == exp)
        all_match = all_match and ok
        if not ok:
            refused.append(name)
        tag = "MATCH" if ok else f"FAIL (expected {exp})"
        print(f"  {name:24} word={word:14} -> "
              f"H0={got[0]} H1={got[1]} H2={got[2]}   {tag}")
    # also verify the connected-sum operator reproduces a known #: RP^2 # RP^2 = Klein
    csw = reason.solve({"connected_sum_word": {"words": ["aa", "aa"]}},
                       {}, capabilities=caps)
    h1 = reason.solve({"cw_integral_homology": {"word": csw, "k": 1}},
                      {}, capabilities=caps)
    cs_ok = (h1["free"], tuple(h1["torsion"])) == (1, (2,))
    all_match = all_match and cs_ok
    print(f"  connected-sum operator: RP^2 # RP^2 -> word {csw!r} -> "
          f"H1=({h1['free']},{h1['torsion']})   "
          f"{'MATCH (Klein: Z⊕Z/2)' if cs_ok else 'FAIL'}")
    print(f"\n  ALL operators reproduce their known surface: {all_match}   "
          f"REFUSED: {refused or 'none'}")
    if not all_match:
        print("  => an operator FAILED verification -> REFUSED (the cmsg82 'refuse "
              "to game it' discipline). Not acquired; the re-run does not proceed.")
        return 1

    # ----------------------------------------------------------- 3. RE-RUN
    banner("3. RE-RUN — COMPREHEND the target PROSE into the summand gluing WORDS "
           "(the held comprehension; the shell supplies NO word), BUILD Y via the "
           "acquired connected-sum operator, DERIVE H_*(Y)")
    # comprehend each numbered summand clause -> its gluing word. The shell splits on
    # the prose's enumerated list; the WORD comes from CO.comprehend_gluing (graph-
    # data patterns over the prose's stated N + polygon / 'projective plane'), NOT
    # from the shell. A clause that is not a gluing construction yields "".
    clauses = [c.strip() for c in re.split(r"[1-9]\.\s", q) if c.strip()]
    summand_words = []
    print("  comprehending the summand clauses (prose -> gluing word):")
    for c in clauses:
        w = CO.comprehend_gluing(c)
        if w:
            print(f"    {('...' + c[:64].strip() + '...')!s:70} -> word {w!r}")
            summand_words.append(w)
    print(f"  summand gluing words (comprehended, NOT shell-supplied): "
          f"{summand_words}")
    joined = reason.solve({"connected_sum_word": {"words": summand_words}},
                          {}, capabilities=caps)
    cx = reason.solve({"polygon_identification_complex": {"word": joined}},
                      {}, capabilities=caps)
    print(f"\n  Y = the connected sum, BUILT by the acquired operator:")
    print(f"    joined gluing word (the operator's, not the shell's): {joined!r}")
    print(f"    CW complex: {cx['nv']} vertex, edges {cx['edges']}, "
          f"{cx['nf']} 2-cell")
    print(f"    ∂_2 (the abelianized attaching word, the held ∂): {cx['d2']}")
    print("\n  DERIVE H_*(Y) (held SNF over the CONSTRUCTED boundary matrices):")
    hY = {}
    for k in (0, 1, 2):
        h = reason.solve({"cw_integral_homology": {"word": joined, "k": k}},
                         {}, capabilities=caps)
        hY[k] = h
        free = h["free"]
        tors = h["torsion"]
        desc = ("Z^%d" % free if free else "0")
        if tors:
            desc += " ⊕ " + " ⊕ ".join(f"Z/{d}" for d in tors)
        print(f"    H_{k}(Y) = {desc}   (free {free}, torsion {tors})")

    # ------------------------------------------ 3b. THE ONE ADMISSIBILITY GATE
    banner("3b. ADMISSIBILITY GATE — the constructor's OUTPUT passes through the ONE "
           "gate (the held native collapse): Y is ADMITTED only if it reproduces ALL "
           "the problem's constraints, incl. the QUESTION's well-definedness "
           "presuppositions (the systemic fix the cmsg116 constructor LACKED)")
    # The systemic fix ([[ozma_fix_the_fixer]]): the constructor no longer reports
    # depth over an object it never admitted. Y's forward-model H_1 must COLLAPSE
    # consistently against the asked-invariant's WELL-DEFINEDNESS presupposition,
    # DERIVED FROM THE QUESTION (never the answer): "rank of Ker(Hurewicz) as a FREE
    # GROUP" of finite rank => H_1 FINITE. H_1(Y)=Z^2 (infinite) BREAKS it -> the gate
    # REJECTS AUTOMATICALLY (the fidelity gap a human caught by hand, now the gate's,
    # by the SAME native collapse that handles cmsg115's S^1 + BG_2/lattices).
    y_props = {"h1_free_rank": hY[1]["free"], "b1": hY[1]["free"],
               "h1_torsion": list(hY[1]["torsion"])}
    gate = AG.gate_object(object_props=y_props, stated_props={}, question_text=q,
                          unaccounted_construction=[])
    print(f"  Y forward-model H_1: free rank {hY[1]['free']}, "
          f"torsion {hY[1]['torsion']}")
    pres = AG.presuppositions_from_question(q)
    print("  WELL-DEFINEDNESS presupposition DERIVED FROM THE QUESTION (not the "
          "answer):")
    for p in pres:
        print(f"    - {p['label']}")
    print(f"  the gate's collapse over the problem's constraints:")
    print(gate.trace() or "    (no constraints fired)")
    print(f"  => {gate.reason}")
    print(f"  Y ADMITTED by the gate? {gate.admitted}")
    admitted = gate.admitted

    # ----------------------------------------------------------- 4. DEPTH
    banner("4. DEPTH — how far the stall LIFTS (the answer read ONLY at the END, to "
           "verify whatever the agent derived — NEVER fed into the constructor)")
    # the asked invariant: rank of Ker(Hurewicz: pi_1(Y) -> H_1(Y)) as a FREE GROUP.
    # the constructor BUILT Y + DERIVED H_1(Y) (homology — held). But the kernel of
    # the Hurewicz map = the COMMUTATOR SUBGROUP [pi_1, pi_1], whose free rank is a
    # FUNDAMENTAL-GROUP / group-theory computation (pi_1-from-CW = the one-relator
    # presentation <a,b,c | attaching-word>, then the commutator-subgroup rank via
    # Reidemeister-Schreier) — BEYOND homology. Check whether that machinery is held.
    group_ops = [c for c in reason.CAPABILITIES
                 if any(t in c for t in ("pi1", "fundamental", "commutator",
                                         "free_group", "presentation",
                                         "reidemeister", "schreier", "hurewicz"))]
    have_pi1 = bool(group_ops)
    print("  the constructor LIFTED description->object: Y is BUILT from the prose")
    print("  (no library literal, no shell-supplied chain) and H_1(Y) is DERIVED:")
    print(f"    H_1(Y) = free {hY[1]['free']}, torsion {hY[1]['torsion']}")
    print()
    print("  the ASKED invariant = rank of Ker(Hurewicz pi_1(Y)->H_1(Y)) as a free")
    print("  group = the rank of the COMMUTATOR SUBGROUP [pi_1,pi_1] of the one-")
    print("  relator group pi_1(Y) = <a,b,c | attaching-word>. That is a pi_1 /")
    print("  group-theory computation (Reidemeister-Schreier over the presentation),")
    print(f"  BEYOND homology. pi_1 / commutator machinery held? {have_pi1} "
          f"({group_ops or 'NONE'})")

    known = target.get("answer")
    # THE GATE DRIVES THE OUTCOME (the systemic fix): the constructor does NOT report
    # a "lift" over an object the ONE admissibility gate REJECTED. Y's H_1=Z^2
    # (infinite) BREAKS the QUESTION's finite-H_1 presupposition, so Y is INADMISSIBLE
    # BY CONSTRUCTION — the fidelity error a human caught by hand, now caught BY THE
    # GATE, automatically, by the SAME native collapse handling cmsg115/BG_2/lattices.
    if not admitted:
        depth = "REJECTED-BY-GATE"
        print("\n  => INADMISSIBLE BY THE GATE. The constructor BUILT Y and DERIVED")
        print("     H_1(Y)=Z^2, but the ONE admissibility gate (the held native")
        print("     collapse) REJECTS Y: an infinite H_1 BREAKS the QUESTION's own")
        print("     well-definedness presupposition (rank of Ker(Hurewicz) as a FINITE")
        print("     free group => H_1 FINITE). The fidelity gap the human caught BY")
        print("     HAND in cmsg116 is now caught BY THE GATE — automatically, by the")
        print("     SAME mechanism that rejects cmsg115's spurious S^1 and admits")
        print("     BG_2/lattices. We never 'spend' on the rejected object (no depth")
        print("     is claimed over it); the stall NAMES ITSELF.")
        print("     RESIDUAL (constraint-derivation breadth): the gate REJECTS the")
        print("     inconsistency but does not yet DERIVE the asked kernel rank — the")
        print("     commutator-subgroup-index=|H_1| + Nielsen-Schreier rank is the")
        print("     next acquire (and a CORRECT Y has finite H_1, so the construction")
        print("     of Y itself — the RP^2 summand's torsion read — is the open fix).")
    elif have_pi1:
        depth = "FULL"
        # (closure branch — would derive the kernel rank + verify vs `known`.)
        print("\n  => FULL-LIFT branch (pi_1/commutator machinery held) — not reached")
        print("     this run; left as the closure branch for the next acquire.")
    else:
        depth = "PARTIAL"
        print("\n  => PARTIAL LIFT. Y is ADMITTED by the gate (its H_1 is consistent")
        print("     with the question's presuppositions) and H_1(Y) is derived (the")
        print("     cmsg115 wall — description->object — is LIFTED). The asked")
        print("     Hurewicz-kernel-rank is the NEW, precisely-named NEXT GAP:")
        print("     pi_1-from-CW (the one-relator presentation) + the COMMUTATOR-")
        print("     SUBGROUP free rank (Reidemeister-Schreier) — the next acquire.")

    print(f"\n  (answer read at the END only, to verify the DERIVED H_1(Y) is right —")
    print(f"   NEVER fed into the constructor / comprehension / derivation):")
    print(f"    DERIVED:  H_1(Y) = Z^{hY[1]['free']}"
          + (" ⊕ " + " ⊕ ".join(f'Z/{d}' for d in hY[1]['torsion'])
             if hY[1]['torsion'] else "") + "  (the constructor's output)")
    print(f"    KNOWN ANSWER (the asked Hurewicz-kernel-rank): {known!r}")
    print(f"    note: the answer {known!r} is the KERNEL-RANK (the named next gap),")
    print(f"          NOT H_1(Y) — so it does NOT verify the H_1 derivation and was")
    print(f"          NOT used; the constructor's H_1(Y) is verified by the KNOWN-")
    print(f"          SURFACE checks in step 2, not by the stalled answer.")

    # ----------------------------------------------------------- 5. LEDGER
    banner("5. LEDGER — ACQUIRED / VERIFIED-vs-KNOWN / CONSTRUCTED / DERIVED / "
           "NEXT-GAP")
    print("  ACQUIRED (specified + emitted/composed over held ∂/SNF):")
    for spec in CO.operator_specs():
        print(f"    + {spec['name']}  (reduces to {', '.join(spec['reduces_to'])})")
    print("  VERIFIED-vs-KNOWN (MATCH, not vs the answer):")
    print("    torus aba^-1b^-1 -> [1,2,1]; RP^2 aa -> H_1=Z/2; Klein -> Z⊕Z/2;")
    print("    genus-2 -> Z^4; RP^2#RP^2 -> Klein (Z⊕Z/2) — ALL MATCH.")
    print("  CONSTRUCTED (the shell supplied NONE of it): Y built by the operator")
    print(f"    from the comprehended gluing words -> word {joined!r}, ONE 2-cell")
    print(f"    with ∂_2 = {cx['d2']} (the abelianized attaching word).")
    print(f"  DERIVED (held SNF over the constructed matrices): "
          f"H_1(Y) = Z^{hY[1]['free']}"
          + (" ⊕ " + " ⊕ ".join(f'Z/{d}' for d in hY[1]['torsion'])
             if hY[1]['torsion'] else "") + ".")
    print("  NEXT GAP (named): pi_1-from-CW (one-relator presentation) + the")
    print("    commutator-subgroup free rank (Reidemeister-Schreier) — the rank of")
    print("    Ker(Hurewicz). NOT a homology op; the next acquire on the same ladder.")

    banner("SUMMARY")
    print(f"  TARGET: {target['id']} (the cmsg115 stalled question)")
    print(f"  ACQUIRED: the 4 construction operators (polygon-identification->CW,")
    print(f"            connected-sum, RP^2-as-built, cw-integral-homology), each")
    print(f"            reducing to the held SNF; VERIFIED vs known surfaces (MATCH).")
    print(f"  RE-RUN: Y CONSTRUCTED from the prose's gluing words (shell supplied")
    print(f"          none) -> H_1(Y) = Z^{hY[1]['free']} DERIVED.")
    print(f"  GATE: the ONE admissibility gate (the held native collapse) "
          f"{'REJECTED' if not admitted else 'ADMITTED'} Y")
    print(f"        — H_1=Z^{hY[1]['free']} {'BREAKS' if not admitted else 'satisfies'} "
          f"the QUESTION's finite-H_1 presupposition (the cmsg116 hand-catch, now")
    print(f"        AUTOMATIC, by the SAME mechanism as cmsg115's S^1 + BG_2/lattices).")
    print(f"  DEPTH: {depth} — the constructor LIFTS description->object (Y built + H_1")
    print(f"         derived), but the gate REJECTS the inconsistent H_1; the answer")
    print(f"         was read ONLY at the end. The residual is constraint-derivation")
    print(f"         breadth (the kernel-rank derivation is the next acquire).")
    print("[MARKER] HLE_CONSTRUCT_Y_COMPLETED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
