#!/usr/bin/env python3
"""jabberwock_speaks_to_audience -- GATE for `domains/audience_driven_production.py`, the
communication loop's THIRD PIECE grounded: does the speaker tailor its produced utterance to a
GROUNDED audience model (terse to a rich, actually-OBSERVED interlocutor), and does it refuse to
tailor to an UNGROUNDED one (falls back to explicit, even when handed the same "known_concepts"
hint)? donkey=0, earn-not-borrow, graph-native.

THE ARC (reused, not rebuilt): `pragmatic_speaker.choose_encoding` (the held Argmax-of-Plus
J = recovery - lambda*cost Term) picks the rung; `system_model.model_system` grounds the audience
via a `foreign_snapshot` + `SensorAnchor`; `audience.knows` reads the theory-of-mind known/new
split; `language.produce` renders the real utterance string. This script is a THIN reporting
wrapper around `domains.audience_driven_production` -- no new decision logic.

GATE (all reported honestly, exit 0 iff every assertion holds):
 1 SPOUSE-VS-STRANGER -- a rich GROUNDED audience model (observed knowing most of the context) gets
   a TERSE utterance (fewer words, terseness > 0, conveys only the residual); a wide/UNKNOWN
   (ungrounded) audience gets the EXPLICIT rendering (all concepts, terseness == 0.0).
 2 GROUNDED-ONLY TAILORING -- an interlocutor with the SAME believed-known concepts as the spouse,
   but marked NOT observed, must NOT terse-tailor: the known_concepts hint is never credited without
   grounding. Discriminative against gate 1's spouse result.
 3 THE PRODUCED UTTERANCE IS REAL -- both utterances are genuine strings out of `language.produce`;
   the terse one is a strict subset-by-word of the explicit one's information content (every word in
   the terse utterance names a concept that is NOT in the ungrounded/observed-empty audience's
   credited-known set).
 4 FROZEN CORE + fast regression pointer (this script only asserts 1-3; run
   `jabberwock_frozen_core_check.py` + the pytest files separately, as documented in the module
   docstring's "GATE" section of the parent task).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_speaks_to_audience.py
"""
from __future__ import annotations
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.boot_core import boot_core                     # noqa: E402
import domains.audience_driven_production as adp              # noqa: E402

LEXICON = [
    {"form": "dinner", "concept": "dinner"},
    {"form": "seven pm", "concept": "seven_pm"},
    {"form": "the italian place", "concept": "italian_place"},
    {"form": "a reservation", "concept": "reservation"},
    {"form": "table for two", "concept": "table_for_two"},
]
MEANING = {"dinner", "seven_pm", "italian_place", "reservation", "table_for_two"}
SHARED = ["dinner", "seven_pm", "italian_place"]   # what the spouse has actually been observed to know


def main() -> int:
    s, ag = boot_core()
    ok = True

    # ---- 1. SPOUSE-VS-STRANGER ------------------------------------------------------------
    spouse = adp.audience_model(s, {"id": "spouse", "observed": True, "known_concepts": SHARED})
    stranger = adp.audience_model(s, {"id": "stranger", "observed": False})

    assert spouse["grounded"] is True, "spouse (observed) must ground"
    assert stranger["grounded"] is False, "stranger (unobserved) must NOT ground"

    r_spouse = adp.select_utterance(s, MEANING, spouse, LEXICON)
    r_stranger = adp.select_utterance(s, MEANING, stranger, LEXICON)

    print("=== 1. SPOUSE-VS-STRANGER ===")
    print(f"  spouse   (grounded, shared={SHARED}):")
    print(f"    utterance='{r_spouse['utterance']}'  terseness={r_spouse['terseness']:.2f}"
          f"  grounded_used={r_spouse['grounded_used']}")
    print(f"  stranger (ungrounded, no observation):")
    print(f"    utterance='{r_stranger['utterance']}'  terseness={r_stranger['terseness']:.2f}"
          f"  grounded_used={r_stranger['grounded_used']}")

    spouse_words = len(r_spouse["utterance"].split())
    stranger_words = len(r_stranger["utterance"].split())
    print(f"  word counts: spouse={spouse_words}  stranger={stranger_words}")

    cond1 = (r_spouse["grounded_used"] is True and r_stranger["grounded_used"] is False
             and r_spouse["terseness"] > 0.0 and r_stranger["terseness"] == 0.0
             and spouse_words < stranger_words
             and set(r_stranger["conveyed"]) == MEANING)
    print(f"  PASS: {cond1}")
    ok &= cond1

    # ---- 2. GROUNDED-ONLY TAILORING --------------------------------------------------------
    ghost = adp.audience_model(s, {"id": "ghost", "observed": False, "known_concepts": SHARED})
    r_ghost = adp.select_utterance(s, MEANING, ghost, LEXICON)

    print("\n=== 2. GROUNDED-ONLY TAILORING (same known_concepts hint, but UNOBSERVED) ===")
    print(f"  ghost (same known_concepts={SHARED}, observed=False):")
    print(f"    utterance='{r_ghost['utterance']}'  terseness={r_ghost['terseness']:.2f}"
          f"  grounded_used={r_ghost['grounded_used']}")

    cond2 = (ghost["grounded"] is False and r_ghost["grounded_used"] is False
              and r_ghost["terseness"] == 0.0
              and set(r_ghost["conveyed"]) == MEANING
              and len(r_ghost["utterance"].split()) == stranger_words
              and r_ghost["utterance"] != r_spouse["utterance"])
    print(f"  PASS (discriminative vs spouse, despite identical known_concepts hint): {cond2}")
    ok &= cond2

    # ---- 3. THE PRODUCED UTTERANCE IS REAL -------------------------------------------------
    print("\n=== 3. THE PRODUCED UTTERANCE IS REAL ===")
    by_concept = {e["concept"]: e["form"] for e in LEXICON}
    spouse_conveyed_forms = {by_concept[c] for c in r_spouse["conveyed"]}
    residual_new = set(r_spouse["residual"]["new"])
    cond3 = (spouse_conveyed_forms <= {by_concept[c] for c in residual_new}
             and r_spouse["utterance"] != r_stranger["utterance"]
             and all(c not in SHARED for c in r_spouse["conveyed"]))
    print(f"  spouse conveys only residual concepts (never a shared/known one): "
          f"conveyed={r_spouse['conveyed']}  shared={SHARED}")
    print(f"  PASS: {cond3}")
    ok &= cond3

    print(f"\n{'GATE PASS' if ok else 'GATE FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
