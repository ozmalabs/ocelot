#!/usr/bin/env python3
"""jabberwock_registers — demonstrate the jabberwock's register VOICE and its
always-honest conversational surface.

The bug this closes: replies used to leak the bare speech-act NAME as text
("acknowledgment", "greeting") or fall SILENT (None -> "(the jabberwock is
silent)"). The register machinery (`_REGISTER_SURFACES` / `note_register` /
`surface_for`) already existed but was never consulted by `emit_reply`.

This driver shows, on the LIVE `converse` loop (donkey=0):
  1. NO bare token / NO silence across a battery of turn kinds.
  2. REGISTER MATCH — the same speech act renders a different surface depending
     on the register the interlocutor has been using (casual vs formal).
  3. HONEST FALLBACKS — an unanswerable question, an unperformable instruction,
     and a comprehension gap each produce an honest, substantive reply.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_registers.py
"""
from __future__ import annotations

import sys

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds


_BARE = {"greeting", "acknowledgment", "thanks", "farewell", "closing",
         "statement", "answer", "backchannel", "clarification", "inquire_unknown",
         "instruction"}


def _agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    a._donkey = {"n": 0}
    a.set_self_teacher(lambda q: (a._donkey.__setitem__("n", a._donkey["n"] + 1), "D")[1])
    return a


def _leak(reply) -> bool:
    return reply is None or not str(reply).strip() or str(reply).strip().lower() in _BARE


def main() -> int:
    ok = True

    print("=" * 66)
    print("1. NO BARE TOKEN / NO SILENCE — every turn is honest & substantive")
    print("=" * 66)
    a = _agent()
    battery = [
        ("hey there", "greeting"), ("thanks a lot", "thanks"),
        ("what is a borogove", "question"), ("move north", "statement"),
        ("quorplezap the door", "statement"), ("the sky is blue", "statement"),
        ("goodbye", "farewell"), ("it is blue", "answer"), ("bye", "closing"),
    ]
    for text, sa in battery:
        reply = a.converse(text, sa)
        flag = "LEAK!" if _leak(reply) else "ok"
        ok = ok and not _leak(reply)
        print(f"  [{flag:5}] ({sa:10}) {text!r:26} -> {reply!r}")
    print(f"  donkey (LLM calls) = {a._donkey['n']}")

    print("\n" + "=" * 66)
    print("2. REGISTER MATCH — same act, surface by the tracked register")
    print("=" * 66)
    casual = _agent()
    cg = casual.converse("hey, what's up?", "greeting")
    ck = casual.converse("yeah cool, the sky is blue", "statement")
    formal = _agent()
    fg = formal.converse("Good day, kindly tell me the time.", "greeting")
    fk = formal.converse("Indeed, the sky is certainly blue.", "statement")
    print(f"  CASUAL  (register={casual.register()!r:8}): greeting={cg!r:8}  acknowledgment={ck!r}")
    print(f"  FORMAL  (register={formal.register()!r:8}): greeting={fg!r:8}  acknowledgment={fk!r}")
    contrast = (cg != fg and ck != fk)
    ok = ok and contrast
    print(f"  same act -> different surface by register: {contrast}")

    print("\n" + "=" * 66)
    print("3. HONEST FALLBACKS — 'I don't ...' / 'no world' / register-matched ask")
    print("=" * 66)
    b = _agent()
    print(f"  unanswerable question   -> {b.converse('what is a borogove', 'question')!r}")
    print(f"  unperformable instruction-> {b.converse('move north', 'statement')!r}")
    print(f"  comprehension gap (ask)  -> {b.converse('quorplezap the door', 'statement')!r}")

    print("\n" + ("PASS" if ok else "FAIL") + f" — no leaks/silence, register contrast held")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
