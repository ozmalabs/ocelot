"""PURE CONJECTURE + the CONFIDENCE CONTINUUM — the agent answers with an
explicit confidence on a continuum, not a binary fact/no-fact:

    grounded fact        conf ~1.0      HIGH         -> "X."
    order-N chain        product/hops   HIGH/MID     -> "X." / "Probably X."
    conjecture (shape)   epsilon ~0.1   LOW          -> "I think it's like X."
    no shape at all      —              INADMISSIBLE -> "I don't know."

The project's admissibility thesis, REFINED: admissibility is binary FOR A
SPECIFIC grounded structure, but the agent can hold a LOW-WEIGHT CONJECTURED
structure ALONGSIDE the (absent) grounded one, with explicit confidence. "I
don't know" is the categorical no — reserved for when there is no shape to even
guess from (the structure is genuinely inadmissible).

Conjectures are generated from the agent's OWN abstract-shape machinery (no
hardcoded guess table):
  * TYPE/ROLE — the queried slot's expected category (RolePrior graph data:
    a 'location' query expects a place; an 'agent' query a person/animal).
  * ANALOGY  — transfer from same-type-same-slot grounded facts (other persons
    live in cities -> conjecture a city).
And the conjecture weight ENTERS THE CALCULATION: a chain with one conjectured
hop returns confidence = product(grounded_hops) * epsilon — the guess
participates, it is not excluded.

HONEST: every conjecture is reported with its weight + basis; never presented as
a fact. Reply hedging uses the agent's HELD epistemic markers (EpistemicMarker
graph data realising the held 'think'/'possibility'/'necessity' concepts).

Cases below print, per query: grounded? chain? conjecture(candidate, weight,
basis)? -> confidence band -> reply form. The PARSE BOUNDARY is the same as
order_n_reasoning_test: surfaces the stub teacher can't ground (lives/Paris/...)
are asserted directly as KnownFact graph nodes so the CALCULUS is exercised on a
real graph; the end-to-end conversation path is shown where the surface parses
(the grounded HIGH case and the INADMISSIBLE case run through
ConversationWorld.turn).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native
from domains.language_world import LanguageWorld, teacher_stub
from domains.conversation_world import ConversationWorld
from domains import conjecture as conj
from scripts.language_test import training_bank


def _fact(s, **slots):
    return s.add_node("KnownFact", dict(slots, language="en"))


def _print_answer(res: dict) -> None:
    print(f"   source        : {res['source']}")
    print(f"   answer         : {res.get('answer')!r}")
    print(f"   confidence     : {res['confidence']:.4f}   band={res['band']}")
    print(f"   conjectured    : {res.get('conjectured')}")
    print(f"   basis          : {res.get('basis')}")
    if res.get("chain_str"):
        print(f"   chain          : {res['chain_str']}")
    if res.get("alternatives"):
        print("   alternatives   :")
        for cand, w, basis in res["alternatives"]:
            print(f"       ({cand!r}, weight={w}, basis={basis})")


def case_grounded(cw, s):
    print("=" * 72)
    print("CASE 1 — GROUNDED (HIGH): a stored fact, full confidence.")
    print("=" * 72)
    cw.turn("Mary loves John.", "en")
    r = cw.turn("Who does Mary love?", "en")
    rec = cw.transcript[-1]
    print("   USER : Who does Mary love?   (end-to-end through ConversationWorld)")
    print(f"   AGENT: {r!r}")
    print(f"   confidence     : {rec.get('confidence')}   band={rec.get('band')}")
    print("   -> grounded fact = HIGH, asserted plain (no hedge).")
    return rec


def case_order_n(s):
    print()
    print("=" * 72)
    print("CASE 2 — ORDER-N (HIGH/MID): a 2-hop grounded chain, confidence")
    print("decayed by the hops (product of grounded-hop weights).")
    print("=" * 72)
    _fact(s, event="live", agent="John", location="Paris", tense="present")
    print("   facts: love(Mary,John) [case 1] + live(John,Paris)")
    print("   query (graph level): where does Mary's beloved live? "
          "(anchor=Mary, relation=live, slot=location)")
    res = conj.answer(s, anchor_entity="Mary", queried_relation="live",
                      queried_slot="location", anchor_slot="agent")
    _print_answer(res)
    print(f"   -> order-{res['order']} chain: conf = {conj.GROUNDED_HOP}"
          f"^{res['order']} = {res['confidence']:.3f}  (decays with hops).")
    return res


def case_conjecture_type(s):
    print()
    print("=" * 72)
    print("CASE 3a — CONJECTURE / TYPE-ROLE (LOW): no live(Mary,?) anchor fact,")
    print("but the agent holds the 'location' role's expected category.")
    print("=" * 72)
    # PURE type guess: query a relation with NO grounded fact at all (so analogy
    # finds no same-slot filler), but a slot WITH a role prior. 'work' has no
    # stored fact; the 'location' slot's prior still gives the type shape.
    print("   query: where does Zara work?  (no work-fact anywhere -> no")
    print("          analogy; but the 'location' slot has a type prior)")
    res = conj.answer(s, anchor_entity="Zara", queried_relation="work",
                      queried_slot="location", anchor_slot="agent")
    conj.record_conjecture(s, res)
    _print_answer(res)
    print("   -> NOT 'I don't know': a PURE type-level shape-guess at epsilon "
          "('a place').")
    return res


def case_conjecture_analogy(s):
    print()
    print("=" * 72)
    print("CASE 3b — CONJECTURE / ANALOGY (LOW): no fact for the queried entity,")
    print("but OTHER entities fill the same slot of the same relation -> transfer.")
    print("=" * 72)
    # live(John,Paris) exists. Ask where Mary lives — no Mary-fact, but the
    # analogy 'a live's location is a place like Paris' transfers from John.
    print("   facts: live(John,Paris)  [a same-slot grounded analogue]")
    print("   query: where does Mary live?  (no live(Mary,?) fact)")
    cands = conj.conjecture(s, queried_relation="live", queried_slot="location",
                            anchor_entity="Mary", anchor_slot="agent")
    print("   conjecture candidates (candidate, weight, basis):")
    for cand, w, basis in cands:
        print(f"       ({cand!r}, weight={w}, basis={basis})")
    print("   -> analogy transfers the concrete filler (Paris) AND the type")
    print("      gloss (a place), both at epsilon weight.")
    return cands


def case_include_in_calc(s):
    print()
    print("=" * 72)
    print("CASE 4 — INCLUDE-IN-CALC: a chain with ONE conjectured hop. The")
    print("conjecture weight PARTICIPATES: conf = product(grounded) * epsilon.")
    print("=" * 72)
    # Grounded: know(Ann,Bea). NO live-fact for Bea. So Ann->Bea grounds (1 hop),
    # then the final live(Bea,?location) hop is CONJECTURED at epsilon.
    _fact(s, event="know", agent="Ann", patient="Bea")
    print("   facts: know(Ann,Bea)   [grounded]   (NO live(Bea,?) fact)")
    print("   query: where does the person Ann knows live? (anchor=Ann,")
    print("          relation=live, slot=location)")
    res = conj.answer(s, anchor_entity="Ann", queried_relation="live",
                      queried_slot="location", anchor_slot="agent")
    conj.record_conjecture(s, res)
    _print_answer(res)
    g = conj.chain_confidence(res.get("grounded_order", 1))
    print(f"   -> {res.get('grounded_order')} grounded hop(s) "
          f"(conf {g:.3f}) * epsilon ({conj.EPSILON}) = {res['confidence']:.4f}")
    print("      The conjectured hop's weight is MULTIPLIED IN, not dropped.")
    return res


def case_inadmissible(cw):
    print()
    print("=" * 72)
    print("CASE 5 — INADMISSIBLE: no fact, no chain, NO shape, NO route ->")
    print("'I don't know'.")
    print("=" * 72)
    print("   END-TO-END through ConversationWorld.turn. A bare 'Why?' queries the")
    print("   CAUSE slot with NO bound entity: no role prior (no type shape / no")
    print("   conjecture), no entity in play to route to transactively, the")
    print("   interlocutor is not a generic source for a contentless query, and a")
    print("   cause question is not a lookupable solved_class -> NO acquisition")
    print("   route -> INADMISSIBLE.")
    print("   DOCUMENTED CHANGE: 'Why did Mary love John?' (the old probe) now")
    print("   GAINS a transactive route (Mary/John are entities in play) and is")
    print("   RESOLVABLE_VIA_ROUTE, not inadmissible. The categorical 'I don't")
    print("   know' is reserved for the no-route, no-shape case.")
    r = cw.turn("Why?", "en")
    rec = cw.transcript[-1]
    print(f"   USER : Why?")
    print(f"   AGENT: {r!r}")
    print(f"   band           : {rec.get('band')}")
    print(f"   knowledge op   : {rec['knowledge_op']}")
    print("   -> the categorical no: 'I don't know' fires ONLY here.")
    return rec


def main(argv):
    s = _native.Substrate()
    print("=" * 72)
    print("Setup: train comprehension (teacher ON), then answer (teacher OFF).")
    print("=" * 72)
    world = LanguageWorld(s, training_bank(), teacher_stub)
    summ = LanguageWorld.summary(world.run())
    print(f"  comprehension trained: {summ['matched']}/{summ['tasks']} matched")
    world.teacher_disabled = True
    cw = ConversationWorld(world)
    print(f"  confidence model: grounded=1.0, grounded-hop={conj.GROUNDED_HOP}, "
          f"epsilon={conj.EPSILON}")
    print(f"  bands: HIGH>= {conj.BAND_HIGH}  MID>= {conj.BAND_MID}  "
          f"LOW>0  INADMISSIBLE=no candidate")
    print()

    r1 = case_grounded(cw, s)
    r2 = case_order_n(s)
    r3a = case_conjecture_type(s)
    r3b = case_conjecture_analogy(s)
    r4 = case_include_in_calc(s)
    r5 = case_inadmissible(cw)

    # ----- graph-resident inspection: the Conjecture trace nodes ----------
    print()
    print("=" * 72)
    print("Conjecture is graph-resident: Conjecture trace nodes")
    print("=" * 72)
    cns = s.nodes("Conjecture")
    print(f"  {len(cns)} Conjecture node(s) recorded (inspectable, like a")
    print(f"  ReasoningChain); each carries weight + band + basis:")
    for cn in cns:
        a = s.node(cn)["attrs"]
        print(f"    Conjecture {cn}: answer={a.get('answer')!r} "
              f"weight={a.get('weight')} band={a.get('band')} "
              f"basis={a.get('basis')!r}")

    # ----- summary / checks -----------------------------------------------
    print()
    print("=" * 72)
    print("RESULTS")
    print("=" * 72)
    ok = True

    def chk(name, cond, detail=""):
        nonlocal ok
        ok &= bool(cond)
        print(f"  [{'OK' if cond else 'FAIL'}] {name}  {detail}")

    chk("grounded = HIGH, conf 1.0",
        r1.get("band") == "HIGH" and r1.get("confidence") == 1.0,
        f"-> {r1.get('reply')!r}")
    chk("order-N chain decays with hops (conf < 1.0, band HIGH/MID)",
        r2["source"] == "chain" and r2["confidence"] < 1.0,
        f"-> conf {r2['confidence']:.3f} band {r2['band']}")
    chk("type/role conjecture (LOW, epsilon, NOT inadmissible)",
        r3a["source"] == "conjecture" and r3a["band"] == "LOW"
        and r3a["confidence"] == conj.EPSILON,
        f"-> {r3a['answer']!r} weight {r3a['confidence']}")
    chk("analogy conjecture transfers a concrete same-slot filler",
        any(c[0] == "Paris" for c in r3b),
        f"-> {[c[0] for c in r3b]}")
    chk("include-in-calc: conjectured hop weight multiplied in",
        r4["source"] == "conjecture" and r4.get("conjectured")
        and abs(r4["confidence"]
                - conj.chain_confidence(r4.get("grounded_order", 1))
                * conj.EPSILON) < 1e-9,
        f"-> conf {r4['confidence']:.4f}")
    chk("INADMISSIBLE -> 'I don't know' (the ONLY case that declines)",
        r5.get("band") == "INADMISSIBLE"
        and "don't know" in r5["reply"].lower(),
        f"-> {r5['reply']!r}")
    chk("Conjecture trace nodes recorded", len(cns) >= 1,
        f"({len(cns)} nodes)")

    # The key behavioral assertion: 'I don't know' fires ONLY for inadmissible.
    print()
    print("  KEY: 'I don't know' now fires ONLY for the inadmissible case;")
    print("       every query with a shape returns a conjecture with its")
    print("       confidence interval, not silence.")
    print()
    print(f"CONJECTURE / CONFIDENCE CONTINUUM: "
          f"{'ALL OK' if ok else 'FAILURES ABOVE'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
