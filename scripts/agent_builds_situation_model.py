"""SITUATION MODEL — the literal-comprehension base (the described world L denotes), jabberwock-designed.

Entities carry STATE; events apply a state DELTA; the model is built incrementally clause-by-clause and
indexed by who/where/when/why/what-for. Its payoff makes understanding testable:
  INFERENCE = forward productions assert the IMPLICIT post-state (drop->on the floor, shatter->broken,
              give->recipient has it & giver no longer) — things no sentence says outright;
  QUERY     = a traversal of the current state slice (where is X / who has Y / is Z intact).
The state-DELTA decisions are the agent's graph rules (seeds/situation_model.json); the host reads the
clauses in time order and advances the now-frame (mechanical incremental reading). Roles are given here
(role extraction is the adjacent semantic-roles gap); the focus is the model + inference + query.

Run: PYTHONPATH=.:runners/dsl/python python -m scripts.agent_builds_situation_model
"""
from __future__ import annotations
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.build_persona_faculty import boot
from substrate.seed_loader import manifest_for

SEP = "=" * 96
PASSAGE = ("John picked up the glass. John walked to the kitchen. John gave the glass to Mary. "
           "Mary dropped the glass. The glass shattered.")
# Clause-by-clause events as (verb, {role: entity}) — the units the model is built from, in time order.
EVENTS = [
    ("take",    {"agent": "John", "theme": "the glass"}),
    ("move",    {"agent": "John", "goal": "the kitchen"}),
    ("give",    {"agent": "John", "theme": "the glass", "recipient": "Mary"}),
    ("drop",    {"agent": "Mary", "theme": "the glass"}),
    ("shatter", {"theme": "the glass"}),
]
# (question, entity, state-attr to read, the stated/inferred answer expected)
QUERIES = [
    ("Where is John?",                 "John",      "location", "stated"),
    ("Where is the glass now?",        "the glass", "location", "INFERRED (no sentence said it)"),
    ("Who has the glass now?",         "the glass", "holder",   "INFERRED (give transferred, drop released)"),
    ("Is the glass intact?",           "the glass", "intact",   "INFERRED (shatter -> broken)"),
]


def main():
    print(SEP)
    print("SITUATION MODEL — build the described world incrementally, then query what is true NOW")
    print(SEP)
    a = boot()
    for s in ("perspective", "situation_model"):
        a.inner.load_seed_manifest(manifest_for(s), a.agent)
    print(f"\n  passage: {PASSAGE!r}\n")

    ents = {}
    def ent(name):
        if name not in ents:
            ents[name] = a.s.add_node("SmEntity", {"name": name})
        return ents[name]

    # Build events with role edges, then advance the now-frame one clause at a time; each event's DELTA
    # is applied by the agent's graph rules (the inference), latest-wins per entity attr (supersession).
    print("  building the model clause-by-clause (each event applies its state delta):")
    for t, (verb, roles) in enumerate(EVENTS, 1):
        e = a.s.add_node("SmEvent", {"verb": verb, "t": t, "active": 0})
        for role, name in roles.items():
            a.inner.add_edge_unchecked(e, role, ent(name))
        a.inner.set_attr(e, "active", 1)            # the now-frame: only this clause fires
        a.inner.run_rules(10000)                    # the agent's inference productions apply the delta
        a.inner.set_attr(e, "active", 0)
        prot = roles.get("agent") or roles.get("theme")
        gl = a.s.node(ent("the glass"))["attrs"]
        print(f"    t{t} {verb:8} ({prot:5}) -> glass: holder={gl.get('holder','?')!s:9} "
              f"location={gl.get('location','?')!s:10} intact={gl.get('intact','?')}")

    print("\n  the situation model now holds (final state slice):")
    for name, e in ents.items():
        at = {k: v for k, v in a.s.node(e)["attrs"].items() if k != "name"}
        print(f"    {name:12} {at}")

    print("\n  QUERY — answer what is true NOW (the test of comprehension):")
    for q, name, attr, kind in QUERIES:
        at = a.s.node(ents[name])["attrs"]
        val = at.get(attr)
        if attr == "intact":
            ans = "no — broken" if val == 0 else ("yes" if val is None else str(val))
        else:
            ans = str(val) if val is not None else "(unknown)"
        print(f"    Q: {q:28} A: {ans:16} [{kind}]")

    print("\n" + SEP)
    print("  The situation model is the referent-side base under the displacement ladder: entities carry")
    print("  state, events apply deltas, the model is built incrementally and queried. It answers what is")
    print("  true NOW — the glass is on the floor, broken, held by nobody — though NO sentence said any of")
    print("  that: inference filled the now-frame, query read it. That is comprehension, not word-matching,")
    print("  and it is the L the whole figure/analysis/voice ladder was assuming all along.")
    print(SEP)


if __name__ == "__main__":
    main()
