#!/usr/bin/env python3
"""jabberwock_wordplay — the namesake demo: the jabberwock ENGAGES a nonsense
coinage (a shape-inferred playful reading), and reaches the real intent behind
ornate / satisfiable / world-less inputs instead of collapsing them to
"understood". donkey=0 — the reading is the morphology faculty's, no teacher.

Run:  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_wordplay.py
"""
from __future__ import annotations

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds


def _boot():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    a.learn_sign("hello", "greeting")
    a.learn_sign("noted", "acknowledgment")
    a._donkey = {"n": 0}
    a.set_self_teacher(lambda q: (a._donkey.__setitem__("n", a._donkey["n"] + 1), "D")[1])
    return a


# (input, what it exercises)
_TURNS = [
    ("Pray, what manner of thing are you?",        "POLITENESS  -> self-identity"),
    ("kindly tell me what you are",                "POLITENESS  -> self-identity"),
    ("Name one of your rules.",                    "SATISFIABLE -> names a held rule"),
    ("Describe what you perceive.",                "NO-WORLD    -> honest, not 'understood'"),
    ("Do you find yourself capable of frobulation?", "WORDPLAY  -> shape-inferred coinage"),
    ("What does slithy mean?",                     "WORDPLAY    -> portmanteau (slimy+lithe)"),
    ("What is a Zanzibar?",                        "UNKNOWN     -> honest, NOT wordplay"),
    ("quorplezap the door",                        "GAP         -> ask back (real unknown)"),
]


def main() -> int:
    a = _boot()
    print("=" * 78)
    print("JABBERWOCK WORDPLAY + ROBUST COMPREHENSION  (donkey=0)")
    print("=" * 78)
    for text, what in _TURNS:
        act = a.classify_speech_act(text)
        reply = a.converse(text, act)
        print(f"\n[{what}]")
        print(f"  user : {text}")
        print(f"  jabb : {reply}")
    print("\n" + "-" * 78)
    print(f"teacher calls (donkey): {a._donkey['n']}   (0 == the reading is the agent's own)")
    print("-" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
