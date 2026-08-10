"""jabberwock_recounts_article -- READING IS WRITING REVERSED, applied to a
document. Demonstrates the Jabberwock BUILDING a "recount what I read"
faculty (via its own self-build composer, ``domains.recount_faculty``) and
then genuinely SPEAKING a recount of a real short article, in two registers,
donkey=0.

Run: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 python3 \
     scripts/jabberwock_recounts_article.py
"""
from __future__ import annotations
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains import dictionary_lexicon as dl
from domains import recount_faculty as rf
from domains import audience_driven_production as adp
from domains.language_world import LanguageWorld, teacher_stub
from domains.language_production import LanguageProduction
from scripts.language_test import training_bank

ARTICLE = ("Robert Levy, an attorney at ExxonMobil, will join the Justice Department. "
          "He promoted the burning of fossil fuels. "
          "Public Citizen said Big Oil captured the government.")


def main() -> int:
    dl.warm_wordnet("en")
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    donkey = {"n": 0}
    a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])

    world = LanguageWorld(a.inner, training_bank(), teacher_stub)
    world.run()
    world.teacher_disabled = True
    prod = LanguageProduction(world)

    print("=" * 94)
    print("THE JABBERWOCK READS AN ARTICLE, BUILDS A RECOUNT FACULTY, AND RECOUNTS IT")
    print("=" * 94)
    print("\n  ARTICLE:\n    %r" % ARTICLE)

    print("\n  -- self-build (watch for '[self-build] minted live rule ...') --")
    formal = rf.recount_what_read(a, world, prod, ARTICLE,
                                  instruction="Recount what you read.", register="formal")
    print("\n  n_goals=%d n_subgoals=%d accepted=%s" %
         (formal["n_goals"], formal["n_subgoals"], formal["accepted"]))
    print("\n  PER-EVENT PRODUCED LINES (each is LanguageProduction.produce's own overt_speech):")
    for ln in formal["lines"]:
        print("    %r" % ln)
    if formal["residuals"]:
        print("\n  HONEST RESIDUALS (predications skipped, not faked):")
        for r in formal["residuals"]:
            print("    sentence=%r predication=%r" % (r["sentence"], r["predication"]))
            print("      reason: %s" % r["reason"])

    print("\n  FORMAL register:")
    print("    %r" % formal["prose"])

    casual = rf.recount_what_read(a, world, prod, ARTICLE,
                                  instruction="Summarize the article.", register="casual")
    print("\n  CASUAL register (asked with 'Summarize the article.' instead):")
    print("    %r" % casual["prose"])

    # TARGET / audience design: a party the agent has actually watched know
    # sentence 1's content already gets a SHORTER recount (real audience
    # design, via audience_driven_production.residual_vs_audience, reused
    # verbatim -- not reimplemented here).
    grounded_friend = adp.audience_model(
        a, {"id": "friend", "observed": True,
            "known_concepts": ["Robert", "joined", "Department"]})
    targeted = rf.recount_what_read(a, world, prod, ARTICLE,
                                    instruction="Recount what you read.",
                                    register="neutral", audience=grounded_friend)
    print("\n  TARGET: recounting to a friend who already knows sentence 1:")
    print("    %r" % targeted["prose"])
    print("    (skipped as already-known: %d event(s))" % len(targeted["skipped_known_to_audience"]))

    print("\n" + "=" * 94)
    print("  donkey (LLM calls): %d" % donkey["n"])
    ok = (formal["n_goals"] >= 1 and len(formal["lines"]) >= 1
         and all(formal["accepted"]) and donkey["n"] == 0)
    print("  %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
