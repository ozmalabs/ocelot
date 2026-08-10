"""Object-wh comprehension test — the wh-gap reconstruction fix.

English wh-OBJECT questions front the wh-word with do-support + subject-aux
inversion ("Who does Mary love?" = "Mary loves WHO?"). The fronted wh fills the
OBJECT (patient) gap, the intervening NP is the subject (agent). The fix reads
GROUNDED cues — a do-support AUXILIARY (en), the を particle (ja, role=patient),
the personal-`a` preposition (es) — to tell SUBJECT-wh from OBJECT-wh.

Ground vocab with the teacher ON (12-sentence bank), then teacher OFF; every
parse is the agent's own grounded stack.
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
    keys = ("event", "agent", "patient", "recipient", "location",
            "tense", "speech_act")
    return "{" + ", ".join(f"{k}:{f[k]}" for k in keys if k in f) + "}"


def _queried(f: dict) -> str | None:
    for slot in ("agent", "patient", "recipient", "location"):
        if f.get(slot) in ("?WHO", "?WHAT"):
            return slot
    return None


def _parse(world: LanguageWorld, text: str, lang: str) -> dict:
    _l, _sk, shape = world._identify(text, lang)
    return world._parse_with_grounded(text, lang, shape)


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
    # Ground the bare verb stems + the "what" wh-word used by the object-wh
    # probes by running them through the teacher ONCE (so 'love'/'break'/'what'
    # exist as grounded lexemes for the teacher-OFF parse). The wh-gap fix is
    # what's under test; this is just vocabulary grounding.
    world.tasks = [
        {"text": "Who does Mary love?", "language": "en",
         "expected_meaning": {}},
        {"text": "What did the cat break?", "language": "en",
         "expected_meaning": {}},
    ]
    world.run()
    world.teacher_disabled = True

    print()
    print("=" * 72)
    print("OBJECT-wh vs SUBJECT-wh  (teacher OFF — grounded stack only)")
    print("=" * 72)

    cases = [
        # (text, language, expectation note, expected_queried_slot)
        ("Who does Mary love?", "en",
         "object-wh via do-support+inversion -> patient:?WHO, agent:Mary",
         "patient"),
        ("Who broke the vase?", "en",
         "subject-wh (regression) -> agent:?WHO, patient:vase",
         "agent"),
        ("What did the cat break?", "en",
         "object-wh via do-support+inversion -> patient:?WHAT, agent:cat",
         "patient"),
        ("¿A quién ama María?", "es",
         "object-wh via personal-a -> patient:?WHO, agent:Mary",
         "patient"),
        ("¿Quién rompió el jarrón?", "es",
         "subject-wh (regression) -> agent:?WHO, patient:vase",
         "agent"),
        ("メアリーは誰を愛している？", "ja",
         "object-wh via を particle -> patient:?WHO, agent:Mary",
         "patient"),
        ("誰を愛している？", "ja",
         "object-wh via を particle (fronted) -> patient:?WHO",
         "patient"),
        ("誰が花瓶を割った？", "ja",
         "subject-wh via が particle (regression) -> agent:?WHO",
         "agent"),
    ]

    for text, lang, note, exp_slot in cases:
        frame = _parse(world, text, lang)
        q = _queried(frame)
        ok = (q == exp_slot)
        print()
        print(f"  text     : {text}  [{lang}]")
        print(f"  expect   : {note}")
        print(f"  frame    : {_frame_str(frame)}")
        print(f"  queried  : {q!r}  (expected {exp_slot!r})  "
              f"{'OK' if ok else 'MISMATCH'}")

    # ----- END-TO-END through ConversationWorld -----------------------------
    print()
    print("=" * 72)
    print("END-TO-END: store a fact, then ask the object-wh question")
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

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
