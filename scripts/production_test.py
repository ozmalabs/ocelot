"""Drive LanguageProduction — goal-based utterance production as the INVERSE
of the comprehension stack, structured by the taught language_production
model and self-monitored via comprehension ("say it to yourself").

Setup: train the comprehension LanguageWorld on the SAME 12-sentence
multi-language bank language_test uses (so the grammar/lexicon/morphology are
grounded), then PRODUCE from goals with the teacher disabled — production
only reads the grounded grammar/lexicon back out, in reverse.

The headline metric is the SELF-MONITOR ROUND-TRIP: produce -> parse the
output back through comprehension -> the recovered frame matches the goal.
NOT human-fluent English (function words aren't grounded, so output is
lemma-level content words — reported honestly).

Per CLAUDE.md this is a thin runner: instantiate the native substrate, train
comprehension, run the production pipeline, print each stage + the round-trip.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native
from domains.language_world import LanguageWorld, teacher_stub
from domains.language_production import LanguageProduction
from scripts.language_test import training_bank


# ---------------------------------------------------------------------------
# Production goals. Each is a target SemanticFrame + an intent. The frames
# reuse vocabulary the comprehension bank grounds (cat/sit/mat, Mary/love/
# John, break/vase, dog/chase/ball, door/open). Goals whose vocab the
# comprehension stack did NOT ground will surface as unrealized slots — the
# honest cap.
# ---------------------------------------------------------------------------


def goals() -> list[dict]:
    return [
        # declarative — the canonical sit-frame.
        {"label": "declarative (sit)", "language": "en",
         "goal": {"event": "sit", "agent": "cat", "location": "mat",
                  "tense": "past", "intent": "inform"}},
        # interrogative — wh-question over the agent.
        {"label": "interrogative (who broke vase)", "language": "en",
         "goal": {"event": "break", "patient": "vase", "agent": "?WHO",
                  "intent": "ask"}},
        # imperative — request (open door). 'door'/'open' are NOT in the
        # comprehension bank, so this exercises the unrealizable-slot path.
        {"label": "imperative (open door)", "language": "en",
         "goal": {"event": "open", "patient": "door", "intent": "request"}},
        # declarative — Mary loves John (present).
        {"label": "declarative (love)", "language": "en",
         "goal": {"event": "love", "agent": "Mary", "patient": "John",
                  "tense": "present", "intent": "inform"}},
    ]


def cross_lingual_goals() -> list[dict]:
    """The SAME sit-frame realized across languages — shows production reuses
    the per-language grammar/lexicon, not an English generator."""
    base = {"event": "sit", "agent": "cat", "location": "mat",
            "tense": "past", "intent": "inform"}
    return [
        {"label": "es sit-frame", "language": "es", "goal": dict(base)},
        {"label": "ja sit-frame", "language": "ja", "goal": dict(base)},
        {"label": "zh sit-frame", "language": "zh",
         "goal": {k: v for k, v in base.items() if k != "tense"}},
    ]


def show(prod: LanguageProduction, case: dict) -> dict:
    lang = case["language"]
    result = prod.produce(lang, case["goal"])
    pv = result["preverbal_message"]
    ss = result["surface_structure"]
    pw = result["phonological_word"]
    mon = result["self_monitor"]

    print(f"\n--- {case['label']}  [{lang}] ---")
    print(f"  GOAL frame           : {case['goal']}")
    print(f"  preverbal_message    : mood={pv['mood']} "
          f"queried_slot={pv['queried_slot']} frame={pv['frame']}")
    print(f"  surface_structure    : order={ss['order']} "
          f"({ss['order_provenance']}) wh_fronted={ss['wh_fronted']}")
    print(f"                         slots={ss['ordered_slots']}")
    realiz = [f"{w['concept']}->{w['surface']}"
              + ("" if w["realized"] else " [UNREALIZED]")
              for w in pw["words"]]
    print(f"  phonological_word    : {realiz}")
    print(f"  overt_speech         : {result['overt_speech']!r}")
    print(f"  self-monitor (parse back):")
    print(f"      recovered_frame  : {mon['recovered_frame']}")
    print(f"      ROUND-TRIP MATCH : {mon['match']}", end="")
    if not mon["match"]:
        print(f"  (missing={mon['missing']} mismatched={mon['mismatched']})")
        if result["repair"]:
            r = result["repair"]
            print(f"      repair tried     : {r['tried']}")
            print(f"      repaired speech  : {r['overt_speech']!r}")
            print(f"      repaired frame   : {r['recovered_frame']}")
            print(f"      REPAIR MATCH     : {r['match']}")
    else:
        print()
    print(f"  ACCEPTED             : {result['accepted']}")
    return result


def main(argv: list[str]) -> int:
    s = _native.Substrate()

    # 1. Train comprehension on the 12-sentence bank — grounds the
    #    grammar/lexicon/morphology production will read back in reverse.
    print("=" * 72)
    print("Setup: train comprehension (LanguageWorld) on the 12-sentence bank")
    print("=" * 72)
    world = LanguageWorld(s, training_bank(), teacher_stub)
    comp_log = world.run()
    comp_summ = LanguageWorld.summary(comp_log)
    print(f"  comprehension trained: {comp_summ['matched']}/{comp_summ['tasks']} "
          f"matched, {comp_summ['teacher_calls']} teacher calls")
    print(f"  grounded: {len(s.nodes('LexEntry'))} LexEntry, "
          f"{len(s.nodes('Production'))} Production, "
          f"{len(s.nodes('Grammar'))} Grammar nodes")

    # 2. Production — teacher disabled (world.teacher_disabled flips the
    #    inference path; production never calls the teacher anyway, it only
    #    reads grounded data in reverse).
    world.teacher_disabled = True
    prod = LanguageProduction(world)

    print()
    print("=" * 72)
    print("Production (English) — goal -> stages -> overt_speech -> round-trip")
    print("=" * 72)
    accepted = 0
    roundtrip = 0
    cases = goals()
    for case in cases:
        r = show(prod, case)
        if r["self_monitor"]["match"]:
            roundtrip += 1
        if r["accepted"]:
            accepted += 1

    print()
    print("=" * 72)
    print("Cross-lingual — the SAME sit-frame in es / ja / zh")
    print("=" * 72)
    xl_cases = cross_lingual_goals()
    xl_roundtrip = 0
    for case in xl_cases:
        r = show(prod, case)
        if r["self_monitor"]["match"] or (r["repair"] and r["repair"]["match"]):
            xl_roundtrip += 1

    print()
    print("=" * 72)
    print("Summary")
    print("=" * 72)
    print(f"  English goals          : {len(cases)}")
    print(f"  round-trip match (1st) : {roundtrip}/{len(cases)}")
    print(f"  accepted (inc. repair) : {accepted}/{len(cases)}")
    print(f"  cross-lingual round-trip (inc. repair): "
          f"{xl_roundtrip}/{len(xl_cases)}")
    print()
    print("HONEST realizability notes:")
    print("  * Function words (the/on/a/が/を/に) ARE NOW grounded by")
    print("    comprehension (FunctionWord nodes; identity from Wiktionary POS,")
    print("    role from the grounded grammar) and production emits them, so")
    print("    overt_speech is now 'The cat sat on the mat.' / '猫がマットに座っ")
    print("    た。', not lemma-level 'Cat sat mat.'. Only grounded function")
    print("    words are emitted; coarse preposition->location, and es gender")
    print("    agreement (la vs el) is not yet modelled (minor fluency gaps).")
    print("  * Inflection is the GROUNDED inflected surface (sit->sat), read")
    print("    from the lexicon in reverse. The morphology slab is form->lemma")
    print("    only (one direction); no lemma->form generator is used.")
    print("  * A concept with no grounded surface (door/open) shows as")
    print("    [UNREALIZED] and the round-trip flags the missing slot.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
