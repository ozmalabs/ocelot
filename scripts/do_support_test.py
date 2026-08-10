"""Do-support tense/event reconstruction test.

English do-support inserts a dummy auxiliary (do/does/did) that carries the
clause TENSE+agreement in questions/negation, leaving the lexical verb a BARE
infinitive stem ("...does Mary LOVE?", "...did the cat BREAK?"). The
morphology-based event/tense probe keys off -ed/-s/irregular surface, so it
never flags the bare verb: the EVENT slot was LOST and the tense stranded on
the auxiliary.

The fix (domains/language_world._do_support_event_tense) reads GROUNDED cues:
  * EVENT  = the bare lexical verb after the grounded AUXILIARY FunctionWord
             (do/does/did, function=auxiliary), skipping the inverted-subject
             NP — the do-support cue, not a keyword test.
  * TENSE  = the auxiliary form's tense via the morphology reference
             (morphology_reference.auxiliary_tense: did->past, do/does->present).

Regression: NON-do-support sentences (love/loves/broke detected by the
morphology probe) must be UNCHANGED.

Vocabulary is grounded with the teacher ON for the bank + the bare verb stems,
then teacher OFF — every parse below is the agent's own grounded stack.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import _native  # noqa: E402
from domains.language_world import LanguageWorld, teacher_stub  # noqa: E402
from domains.conversation_world import ConversationWorld  # noqa: E402
from scripts.language_test import training_bank  # noqa: E402


def _frame_str(f: dict) -> str:
    keys = ("event", "tense", "agent", "patient", "recipient", "location",
            "speech_act")
    return "{" + ", ".join(f"{k}:{f[k]}" for k in keys if k in f) + "}"


def _queried(f: dict) -> str | None:
    for slot in ("agent", "patient", "recipient", "location"):
        if f.get(slot) in ("?WHO", "?WHAT"):
            return slot
    return None


def _parse(world: LanguageWorld, text: str, lang: str) -> dict:
    _l, _sk, shape = world._identify(text, lang)
    return world._parse_with_grounded(text, lang, shape)


def _check(frame: dict, expect: dict) -> bool:
    """Every expected key present + equal (case-insensitive for strings)."""
    for k, v in expect.items():
        pv = frame.get(k)
        if pv is None:
            return False
        if isinstance(v, str) and isinstance(pv, str):
            if v.lower() != pv.lower():
                return False
        elif pv != v:
            return False
    return True


def main() -> int:
    s = _native.Substrate()
    print("=" * 72)
    print("Setup: train comprehension on the 12-sentence bank (teacher ON)")
    print("=" * 72)
    world = LanguageWorld(s, training_bank(), teacher_stub)
    log = world.run()
    summ = LanguageWorld.summary(log)
    print(f"  trained: {summ['matched']}/{summ['tasks']} matched, "
          f"{summ['teacher_calls']} teacher calls")
    # Ground the bare verb stems + the "what"/"who" wh-words + "dog"/"chase"
    # so they exist as grounded lexemes for the teacher-OFF parse. The
    # do-support reconstruction is what's under test; this is just vocab.
    world.tasks = [
        {"text": "Who does Mary love?", "language": "en",
         "expected_meaning": {}},
        {"text": "What did the cat break?", "language": "en",
         "expected_meaning": {}},
        {"text": "The dog chased the ball.", "language": "en",
         "expected_meaning": {}},
        {"text": "Who does the dog chase?", "language": "en",
         "expected_meaning": {}},
    ]
    world.run()
    world.teacher_disabled = True

    # (text, lang, expected-frame-subset, note)
    cases = [
        # --- DO-SUPPORT: event was LOST, now reconstructed ---------------
        ("Who does Mary love?", "en",
         {"event": "love", "tense": "present", "agent": "Mary",
          "patient": "?WHO"},
         "do-support: event=love now PRESENT (was lost), tense from 'does'"),
        ("What did the cat break?", "en",
         {"event": "break", "tense": "past", "agent": "cat",
          "patient": "?WHAT"},
         "do-support: event=break, tense=past from 'did'"),
        ("Who does the dog chase?", "en",
         {"event": "chase", "tense": "present", "patient": "?WHO"},
         "do-support: event=chase, tense=present from 'does'"),
        # --- REGRESSION: NON-do-support, must be UNCHANGED ---------------
        ("Mary loves John.", "en",
         {"event": "love", "tense": "present", "agent": "Mary",
          "patient": "John"},
         "regression: morphology probe (-s) -> event=love present"),
        ("Who broke the vase?", "en",
         {"event": "break", "tense": "past", "agent": "?WHO",
          "patient": "vase"},
         "regression: morphology probe (irregular) -> event=break past"),
        ("The cat sat on the mat.", "en",
         {"event": "sit", "tense": "past", "agent": "cat", "location": "mat"},
         "regression: morphology probe (irregular) -> event=sit past"),
    ]

    print()
    print("=" * 72)
    print("DO-SUPPORT reconstruction vs NON-do-support  (teacher OFF)")
    print("=" * 72)
    all_ok = True
    for text, lang, expect, note in cases:
        frame = _parse(world, text, lang)
        ok = _check(frame, expect)
        all_ok = all_ok and ok
        print()
        print(f"  text    : {text}  [{lang}]")
        print(f"  expect  : {note}")
        print(f"  frame   : {_frame_str(frame)}")
        print(f"  queried : {_queried(frame)!r}")
        print(f"  correct : {'OK' if ok else 'MISMATCH'}")

    # ----- END-TO-END through ConversationWorld -----------------------------
    print()
    print("=" * 72)
    print("END-TO-END: store a fact, then ask the do-support question")
    print("=" * 72)
    cw = ConversationWorld(world)
    for text in ("Mary loves John.", "Who does Mary love?"):
        reply = cw.turn(text, "en")
        rec = cw.transcript[-1]
        print()
        print(f"  USER : {text}")
        print(f"    frame      : {_frame_str(rec['frame'])}")
        print(f"    speech_act : {rec['speech_act']}")
        print(f"    knowledge  : {rec.get('knowledge_op')}")
        print(f"  AGENT: {reply}")

    print()
    print("=" * 72)
    print(f"RESULT: {'ALL OK' if all_ok else 'SOME MISMATCH'}")
    print("=" * 72)
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
