"""MULTI-HOP QUESTION SURFACES — order-N reasoning end-to-end in natural
language, through ConversationWorld (comprehend -> know -> reason -> reply).

Before this work the order-N operator (domains/order_n_reasoning.py) ran only on
the KnownFact GRAPH; the multi-hop QUESTION SURFACES were not parseable. This
test exercises the surfaces that now parse end-to-end:

  1. 1-HOP LOCATION (wh->role proform)   : the closed-class interrogative
     proform fact (domains/interrogative_reference.py) — where->location,
     when->time, why->cause, how->manner. "Where does John live?" parses to
     {event:live, agent:John, location:?WHERE} and matches the stored fact.

  2. TRANSITIVE POLAR (comparative)       : a POLAR (copula/aux-initial, no wh)
     COMPARATIVE ("Is the cat bigger than the mouse?") -> {event:bigger,
     agent:cat, standard:mouse, polar:True} -> onr.reason_transitive (order-2
     transitive closure over the stored bigger-facts) -> "Yes."

  3. GENUINE 2-HOP (embedded relative)    : "Where does the person Mary loves
     live?" — comprehension CALLS the reasoner to resolve the embedded entity
     (the patient of love(Mary,?) = John, hop-1), substitutes it into the
     matrix, then the matrix where-question runs (hop-2). End-to-end order-N.

  4. HONEST FAIL                          : an unanswerable multi-hop -> the
     honest "I don't know" (NOT fabricated).

HONEST FRAMING (printed per case):
  * wh->role is a CLOSED-CLASS PROFORM FACT (a finite list, like the do-support
    auxiliaries) — grounded as reference data, not a parser rule.
  * comparative + relative-clause are CONSTRUCTIONS (grammatical templates); the
    standard-marker 'than' and the relative pronouns/generic heads are grounded
    closed-class words, the attachment is the construction.
  * Cases 1-3 are END-TO-END through ConversationWorld.turn; the embedded
    relative-clause case is the genuine 2-hop (comprehension calling reasoning).
  * BOUNDARY: the relative-clause template is BOUNDED — generic head ("person")
    + transitive zero/overt-relative; subject-gap relatives, specific heads, and
    stacked relatives are NOT covered (reported, not faked).

No-regression: prints the comprehension bank score (must be 12/12).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native
from domains.language_world import LanguageWorld, teacher_stub
from domains.conversation_world import ConversationWorld
from scripts.language_test import training_bank


# The extra demo sentences — grounded with the teacher ON so their vocabulary
# (lives/Paris, bigger/dog/mouse, person) enters the lexicon. The FACTS
# themselves are asserted in the conversation (teacher OFF) so they go through
# the agent's own grounded parse + KnownFact store.
# NOTE: "Mary loves John." is already in the base training bank, so it is NOT
# repeated here (it would double-count in the no-regression denominator).
_GROUNDING_BANK = [
    {"text": "John lives in Paris.", "language": "en", "expected_meaning": {}},
    {"text": "The cat is bigger than the dog.", "language": "en",
     "expected_meaning": {}},
    {"text": "The dog is bigger than the mouse.", "language": "en",
     "expected_meaning": {}},
    {"text": "The person sat on the mat.", "language": "en",
     "expected_meaning": {}},
]


def _print_turn(rec: dict, *, end_to_end: str) -> None:
    print()
    print(f"USER : {rec['user']}   [{rec['language']}]")
    if rec.get("relative_clause"):
        rc = rec["relative_clause"]
        print(f"   relative clause    : {rc['clause']}  (inner resolve, "
              f"order-{rc['inner_order']})")
        print(f"   rewritten matrix   : {rec['rewritten_matrix']!r}")
    frame = rec["frame"]
    queried = _queried_slot(frame)
    print(f"   comprehended frame : {frame}")
    print(f"   queried slot       : {queried!r}"
          + ("   polar=True" if frame.get("polar") else ""))
    if rec.get("reasoning_chain"):
        ch = rec["reasoning_chain"]
        print(f"   reasoning          : ORDER-{ch['order']}  chain: "
              f"{ch['chain_str']}")
    print(f"   knowledge op       : {rec['knowledge_op']}")
    print(f"AGENT: {rec['reply']}")
    print(f"   [{end_to_end}]")


_WH = ("?WHO", "?WHAT", "?WHERE", "?WHEN", "?WHY", "?HOW")


def _queried_slot(frame: dict):
    for s in ("agent", "patient", "location", "time", "cause", "manner",
              "recipient", "instrument", "source", "beneficiary", "topic"):
        if frame.get(s) in _WH:
            return s
    return None


def main(argv: list[str]) -> int:
    s = _native.Substrate()

    print("=" * 72)
    print("Setup: train comprehension + ground the demo vocabulary (teacher ON)")
    print("=" * 72)
    world = LanguageWorld(s, training_bank() + _GROUNDING_BANK, teacher_stub)
    comp_log = world.run()
    comp_summ = LanguageWorld.summary(comp_log)
    # The base 12-sentence bank is the no-regression denominator.
    base_matched = sum(
        1 for r in comp_log
        if r["text"] in {t["text"] for t in training_bank()} and r["matched"])
    print(f"  base comprehension bank: {base_matched}/12 matched")
    print(f"  demo vocab grounded (lives/Paris/bigger/dog/mouse/person)")
    world.teacher_disabled = True

    cw = ConversationWorld(world)

    print()
    print("=" * 72)
    print("GROUND FACTS (teacher OFF — the agent's own grounded parse + store)")
    print("=" * 72)
    facts = [
        "John lives in Paris.",
        "Mary loves John.",
        "The cat is bigger than the dog.",
        "The dog is bigger than the mouse.",
    ]
    for f in facts:
        cw.turn(f, "en")
        rec = cw.transcript[-1]
        print(f"  STORE {f!r}")
        print(f"        frame {rec['frame']}  -> {rec['knowledge_op']}")

    print()
    print("=" * 72)
    print("MULTI-HOP QUESTIONS")
    print("=" * 72)

    results: dict[str, bool] = {}

    # --- CASE 1: 1-hop location (wh->role proform) ------------------------
    print()
    print("-" * 72)
    print("CASE 1 — 1-hop LOCATION via the where->location proform (closed-class")
    print("interrogative-proform fact). Now parseable; matches the stored fact.")
    print("-" * 72)
    cw.turn("Where does John live?", "en")
    rec = cw.transcript[-1]
    _print_turn(rec, end_to_end="END-TO-END")
    results["1-hop location"] = "Paris" in rec["reply"].lower() or \
        "paris" in rec["reply"].lower()

    # --- CASE 2: transitive polar comparative -----------------------------
    print()
    print("-" * 72)
    print("CASE 2 — TRANSITIVE POLAR: a polar (copula-initial, no wh) comparative")
    print("-> reason_transitive (order-2 closure: cat>dog>mouse => cat>mouse).")
    print("-" * 72)
    cw.turn("Is the cat bigger than the mouse?", "en")
    rec = cw.transcript[-1]
    _print_turn(rec, end_to_end="END-TO-END (order-2 transitive)")
    results["transitive polar"] = rec["reply"].strip().lower().startswith("yes")

    # --- CASE 3: genuine 2-hop (embedded relative clause) -----------------
    print()
    print("-" * 72)
    print("CASE 3 — GENUINE 2-HOP (embedded relative clause). Comprehension CALLS")
    print("reasoning to resolve 'the person Mary loves' = John (hop-1), rewrites")
    print("the matrix, then the where-question runs (hop-2). End-to-end order-N.")
    print("-" * 72)
    cw.turn("Where does the person Mary loves live?", "en")
    rec = cw.transcript[-1]
    _print_turn(rec, end_to_end="END-TO-END (genuine 2-hop)")
    results["genuine 2-hop"] = (
        rec.get("relative_clause") is not None
        and ("paris" in rec["reply"].lower()))

    # --- CASE 4: honest fail ----------------------------------------------
    print()
    print("-" * 72)
    print("CASE 4 — HONEST FAIL: an unanswerable multi-hop -> 'I don't know'")
    print("(NOT fabricated). 'Is the mouse bigger than the cat?' has no")
    print("derivation (the order is the other way); we do NOT assert 'no'.")
    print("-" * 72)
    cw.turn("Is the mouse bigger than the cat?", "en")
    rec = cw.transcript[-1]
    _print_turn(rec, end_to_end="END-TO-END (honest unknown)")
    results["honest fail"] = "don't know" in rec["reply"].lower()

    # ----- coverage summary -----------------------------------------------
    print()
    print("=" * 72)
    print("COVERAGE — which surfaces parse END-TO-END")
    print("=" * 72)
    print("  END-TO-END (comprehend -> reason -> reply through ConversationWorld):")
    print("    * where/when/why/how -> queried role  (closed-class proform fact)")
    print("    * polar comparative  -> reason_transitive (order-N transitive)")
    print("    * embedded relative  -> genuine 2-hop (comprehension calls reason)")
    print("  BOUNDED (templated, reported honestly):")
    print("    * relative clause = generic head + transitive zero/overt relative")
    print("      ONLY; subject-gap / specific-head / stacked relatives NOT covered")
    print("    * comparative = English -er morphology + grounded 'than'; periphrastic")
    print("      'more ADJ' + irregulars (better/worse) are a later pass")
    print("  PRODUCTION-LEVEL cosmetic limit (pre-existing): the realizer emits the")
    print("    grounded preposition coarsely ('lives on paris'); the FRAME + the")
    print("    reasoning are correct (the answer entity is Paris).")

    # ----- no-regression --------------------------------------------------
    print()
    print("=" * 72)
    print("No-regression")
    print("=" * 72)
    base_ok = base_matched == 12
    print(f"  base comprehension bank (language_test): "
          f"{base_matched}/12  {'OK' if base_ok else 'FAIL'}")
    all_ok = base_ok
    for name, ok in results.items():
        print(f"  case {name:18s}: {'OK' if ok else 'FAIL'}")
        all_ok &= ok

    print()
    print(f"MULTI-HOP QUESTION TEST: {'ALL OK' if all_ok else 'FAILURES ABOVE'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
