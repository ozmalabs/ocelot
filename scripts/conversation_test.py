"""End-to-end CONVERSATION over the gamma-substrate language stack — the
whole pipeline wired into a multi-turn dialogue:

    USER text -> COMPREHEND (text->frame) -> KNOW (KnownFact graph nodes)
              -> PRODUCE (goal->utterance) -> SELF-MONITOR -> AGENT reply

Setup: train the comprehension LanguageWorld on the 12-sentence bank (teacher
ON, so the grammar / lexicon / function-words ground), then run the
conversation with the teacher DISABLED — every reply is the agent's own
grounded stack (comprehend -> match KnownFact -> produce -> monitor).

Demonstrated turns (assert, then query — a CONFIDENCE CONTINUUM):
  USER: "The cat sat on the mat."   -> ack             (KnownFact stored)
  USER: "Mary loves John."          -> ack             (KnownFact stored)
  USER: "Who sat on the mat?"       -> answer-by-graph-match   (HIGH, conf 1.0)
  USER: "Who broke the vase?"       -> CONJECTURE              (LOW,  conf 0.1)

The QA is a GRAPH MATCH over KnownFact nodes (indexed nodes_where = NodesWhere,
then bound-slot equality on node attrs), NOT a Python dict lookup.

CHANGED BEHAVIOUR (intended): "Who broke the vase?" has no stored fact and no
chain, but the agent HOLDS a shape — the 'agent' role's expected category
(person/animal, from the RolePrior graph data). So it no longer says
"I don't know"; it CONJECTURES "I think it's like an animal." at epsilon weight
(conf 0.1, LOW band), with its basis reported. "I don't know" is now reserved
for the genuinely INADMISSIBLE case (no fact, no chain, AND no shape) — shown
in scripts/conjecture_test.py. The confidence + basis are graph-resident
(a Conjecture node) and inspectable; a conjecture is never presented as a fact.

STRETCH: a cross-lingual turn — assert in English, ASK in Spanish — to test
whether the language-neutral frame lets an es question match an en-stored fact.
Reported exactly as far as it gets.

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


def _print_turn(cw: ConversationWorld, idx: int) -> None:
    """Print the per-turn trace from the last appended transcript record."""
    rec = cw.transcript[idx]
    print()
    print(f"USER : {rec['user']}   [{rec['language']}]")
    print(f"   comprehended frame : {rec['frame']}")
    print(f"   speech_act         : {rec['speech_act']}")
    print(f"   knowledge op       : {rec['knowledge_op']}")
    print(f"   response goal      : {rec['response_goal']}")
    mp = rec.get("monitor_passes", 0)
    if rec.get("monitor_trace"):
        for t in rec["monitor_trace"]:
            disc = [f"{d['kind']}:{d['slot']}" for d in t["discrepancy"]]
            print(f"     monitor pass {t['pass_index']}: {t['utterance']!r}"
                  f"  discrepancy={disc if disc else '(none)'} -> {t['outcome']}")
        conv = "converged" if rec.get("converged") else "NOT converged"
        print(f"     -> {conv} in {mp} self-monitor pass(es)")
    else:
        print(f"     (reply is a fixed grounded discourse token; "
              f"{mp} self-monitor passes)")
    if "band" in rec:
        c = rec.get("confidence")
        print(f"   confidence         : {c:.3f}  band={rec['band']}"
              if isinstance(c, (int, float)) else f"   band={rec['band']}")
    print(f"AGENT: {rec['reply']}")


def main(argv: list[str]) -> int:
    s = _native.Substrate()

    print("=" * 72)
    print("Setup: train comprehension (LanguageWorld) on the 12-sentence bank")
    print("=" * 72)
    world = LanguageWorld(s, training_bank(), teacher_stub)
    comp_log = world.run()
    comp_summ = LanguageWorld.summary(comp_log)
    print(f"  comprehension trained: {comp_summ['matched']}/{comp_summ['tasks']}"
          f" matched, {comp_summ['teacher_calls']} teacher calls")
    # Teacher OFF for the conversation — the agent's own grounded stack only.
    world.teacher_disabled = True

    cw = ConversationWorld(world)

    print()
    print("=" * 72)
    print("CONVERSATION  (teacher OFF — agent's own comprehend/know/produce)")
    print("=" * 72)

    turns = [
        ("The cat sat on the mat.", "en"),
        ("Mary loves John.", "en"),
        ("Who sat on the mat?", "en"),
        ("Who broke the vase?", "en"),
    ]
    for i, (text, lang) in enumerate(turns):
        cw.turn(text, lang)
        _print_turn(cw, i)

    # ----- the conjecture turn, called out explicitly ---------------------
    print()
    print("-" * 72)
    print("CONJECTURE turn (CHANGED — was 'I don't know'): 'Who broke the vase?'")
    print("has no stored KnownFact and no chain, but the agent holds a SHAPE")
    print("(the 'agent' role's expected category, RolePrior graph data), so it")
    print("CONJECTURES at epsilon weight ('I think it's like an animal.', LOW,")
    print("conf 0.1) instead of declining. 'I don't know' is now reserved for")
    print("the genuinely inadmissible case (see scripts/conjecture_test.py).")
    print("-" * 72)

    # ----- graph-resident knowledge inspection ----------------------------
    print()
    print("=" * 72)
    print("Knowledge is graph-resident: stored KnownFact nodes")
    print("=" * 72)
    facts = s.nodes("KnownFact")
    print(f"  {len(facts)} KnownFact node(s) stored; QA is a GRAPH MATCH over")
    print(f"  them (nodes_where index = NodesWhere, then bound-slot equality):")
    for f in facts:
        a = s.node(f)["attrs"]
        content = {k: v for k, v in a.items() if k != "language"}
        print(f"    KnownFact: {content}")

    # ----- STRETCH: cross-lingual turn ------------------------------------
    print()
    print("=" * 72)
    print("STRETCH: cross-lingual — assert in EN, ask in ES (frame is")
    print("language-neutral; does an es question match the en-stored fact?)")
    print("=" * 72)
    n0 = len(cw.transcript)
    cw.turn("¿Quién se sentó en la alfombra?", "es")
    _print_turn(cw, n0)
    xl = cw.transcript[n0]
    xl_matched = "matched KnownFact" in xl["knowledge_op"]
    print()
    if xl_matched:
        print("  STRETCH RESULT: cross-lingual match WORKED — the es question")
        print("  comprehended to a language-neutral frame that matched the")
        print("  en-stored KnownFact (canonical concepts are shared).")
    else:
        print("  STRETCH RESULT (HONEST): the es question did NOT match the")
        print("  en-stored fact. Why: KnownFact match is bound-slot equality")
        print("  on CANONICAL concept fillers (cat/sit/mat) — those ARE shared")
        print("  cross-lingually — so a match depends on the es parse")
        print("  recovering the SAME canonical fillers. See the comprehended")
        print("  frame above for exactly which slots the es parse recovered.")

    # ----- no-regression --------------------------------------------------
    print()
    print("=" * 72)
    print("No-regression")
    print("=" * 72)
    ok = comp_summ["matched"] == 12 and comp_summ["tasks"] == 12
    print(f"  comprehension bank (language_test): "
          f"{comp_summ['matched']}/12  {'OK' if ok else 'FAIL'}")

    # Sanity: the two subject-wh answers + the honest unknown.
    ans = cw.transcript[2]
    answered = "matched KnownFact" in ans["knowledge_op"]
    print(f"  'Who sat on the mat?' answered by graph match: "
          f"{'OK' if answered else 'FAIL'}  -> {ans['reply']!r}")
    conjd = cw.transcript[3]
    is_conj = conjd.get("band") == "LOW" and "CONJECTURE" in conjd["knowledge_op"]
    print(f"  'Who broke the vase?' now CONJECTURES (was 'I don't know'): "
          f"{'OK' if is_conj else 'FAIL'}  -> {conjd['reply']!r} "
          f"(conf {conjd.get('confidence')}, band {conjd.get('band')})")
    # Genuinely-inadmissible -> STILL 'I don't know' (the categorical no). A bare
    # "Why?" queries the CAUSE slot with NO bound entity: no role prior (no
    # shape / no conjecture), no entity in play to route to transactively, the
    # interlocutor is not a generic source for a contentless query, and a cause
    # question is not a lookupable solved_class -> the route-finder returns None
    # -> INADMISSIBLE -> the categorical 'I don't know'.
    #
    # DOCUMENTED CHANGE: "Why did Mary love John?" (the old inadmissible probe)
    # now legitimately GAINS a route — Mary/John are discourse entities in play,
    # so transactively they are sources for facts about themselves; that gap is
    # RESOLVABLE_VIA_ROUTE (banked, since value <= social cost), no longer
    # inadmissible. The categorical 'I don't know' is reserved for the case with
    # NO route AND no shape, shown here with a contentless "Why?".
    n_inadm = len(cw.transcript)
    cw.turn("Why?", "en")
    inadm = cw.transcript[n_inadm]
    declined = inadm.get("band") == "INADMISSIBLE" \
        and "don't know" in inadm["reply"].lower()
    print(f"  inadmissible query (no fact/chain/shape/route) STILL 'I don't "
          f"know': {'OK' if declined else 'FAIL'}  -> {inadm['reply']!r} "
          f"(band {inadm.get('band')})")
    ok &= answered and is_conj and declined

    print()
    print(f"NO-REGRESSION: {'ALL OK' if ok else 'FAILURES ABOVE'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
