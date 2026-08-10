"""Probe: TYPED new-concept grounding for unknown words.

The insight (user): "John said hello" — we can infer John is almost
certainly a person's NAME even if never seen before, from context. The
substrate should TYPE a genuinely-new word from context and ground it as
a NEW concept, instead of substituting the nearest known concept
(the old behaviour: dog → cat).

This probe:
  1. trains the EN grammar via the existing 12-sentence harness;
  2. "John said hello." (teacher disabled) — shows the substrate grounds
     `john` as a NEW Concept typed category=person, proper=true (a NAME),
     NOT substituted with "Mary";
  3. EN held-out "The dog chased the ball." (teacher disabled) — grounds
     dog{animal}, chase{event}, ball{object} as NEW concepts → strict
     frame match (was 0 under substitution);
  4. prints the grounded Concept nodes + attrs so the typing is visible.

Per CLAUDE.md this is a thin runner: instantiate the native substrate,
hand the world its tasks + teacher, read graph state back, print. No
agent decisions in Python.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native
from domains.language_world import LanguageWorld, teacher_stub
from scripts.language_test import training_bank


def concept_attrs(s, name: str) -> dict | None:
    """Read back a grounded Concept node's attrs by name (graph query)."""
    for cid in s.nodes("Concept"):
        a = s.node(cid)["attrs"]
        if a.get("name") == name:
            return a
    return None


def lex_entries_for(s, surface: str) -> list[dict]:
    out = []
    for eid in s.nodes("LexEntry"):
        a = s.node(eid)["attrs"]
        if a.get("surface") == surface:
            out.append(a)
    return out


def main() -> int:
    s = _native.Substrate()

    # --- Train the EN (+ the other) grammars from the existing harness.
    print("=" * 72)
    print("Train (teacher = stub) — ground EN/es/zh/ja grammar + lexicon")
    print("=" * 72)
    world = LanguageWorld(s, training_bank(), teacher_stub)
    log = world.run()
    summ = LanguageWorld.summary(log)
    print(f"  trained tasks matched: {summ['matched']}/{summ['tasks']} "
          f"(teacher calls {summ['teacher_calls']})")

    # RolePrior / category seed data backing the typing.
    print(f"  RolePrior nodes (slot->category priors): "
          f"{len(s.nodes('RolePrior'))}")
    for rid in s.nodes("RolePrior"):
        a = s.node(rid)["attrs"]
        print(f"    {a.get('slot'):8} -> category={a.get('category')}, "
              f"proper_category={a.get('proper_category')}")
    print(f"  SelectionalRestriction nodes mined from frames: "
          f"{len(s.nodes('SelectionalRestriction'))}")
    for rid in s.nodes("SelectionalRestriction"):
        a = s.node(rid)["attrs"]
        print(f"    {a.get('key'):16} -> category={a.get('category')}")
    print()

    # --- 1. John said hello. ------------------------------------------------
    print("=" * 72)
    print('Probe 1: "Sasha said hello." (teacher DISABLED)')
    print("  'Sasha' is a GENUINELY-NEW word (not in training; 'John' was "
          "already grounded by 'Mary loves John', so we use a fresh name).")
    print("  expect: sasha grounded as a NEW concept, category=person, "
          "proper=true (a NAME) — NOT substituted with Mary.")
    print("=" * 72)
    name_task = [{
        "text": "Sasha said hello.", "language": "en",
        # We don't have a 'say'/'hello' grounding; the point is the AGENT
        # typing. expected only asserts the agent is the new name.
        "expected_meaning": {"agent": "sasha"},
    }]
    w1 = LanguageWorld(s, name_task, teacher_stub, teacher_disabled=True)
    log1 = w1.run()
    e = log1[0]
    print(f"  frame    = {e['frame']}")
    if e.get("inferred"):
        print("  inferred = " + ", ".join(
            f"{surf}->{cand} (w={w:.2f})" for _, surf, cand, w in e["inferred"]))
    name_c = concept_attrs(s, "sasha")
    print(f"  grounded Concept 'sasha' = {name_c}")
    mary_substituted = any(cand == "Mary" for _, _, cand, _ in e.get("inferred", []))
    ok_john = (name_c is not None
               and name_c.get("category") == "person"
               and bool(name_c.get("proper")) is True
               and e["frame"].get("agent") == "sasha"
               and not mary_substituted)
    print(f"  RESULT: {'PASS' if ok_john else 'FAIL'} — "
          f"sasha typed as person NAME, not substituted with Mary")
    print()

    # --- 2. EN held-out: The dog chased the ball. --------------------------
    print("=" * 72)
    print('Probe 2: "The dog chased the ball." (teacher DISABLED)')
    print("  expect: dog{animal}, chase{event}, ball{object} grounded as "
          "NEW concepts → strict frame match.")
    print("=" * 72)
    dog_task = [{
        "text": "The dog chased the ball.", "language": "en",
        "expected_meaning": {"event": "chase", "agent": "dog",
                             "patient": "ball", "tense": "past"},
    }]
    w2 = LanguageWorld(s, dog_task, teacher_stub, teacher_disabled=True)
    log2 = w2.run()
    e2 = log2[0]
    print(f"  expected = {e2['expected']}")
    print(f"  frame    = {e2['frame']}")
    if e2.get("inferred"):
        print("  inferred = " + ", ".join(
            f"{surf}->{cand} (w={w:.2f})" for _, surf, cand, w in e2["inferred"]))
    for name in ("dog", "chase", "ball"):
        print(f"  grounded Concept '{name}' = {concept_attrs(s, name)}")
    ok_dog = e2["matched"]
    print(f"  RESULT: {'PASS (STRICT)' if ok_dog else 'FAIL'} — "
          f"new concepts typed + strict frame match")
    print()

    print("=" * 72)
    print("Summary")
    print("=" * 72)
    print(f"  Probe 1 (John -> person NAME, no substitution): "
          f"{'PASS' if ok_john else 'FAIL'}")
    print(f"  Probe 2 (EN held-out strict via typed new concepts): "
          f"{'PASS' if ok_dog else 'FAIL'}")
    print()
    print("  Honest data boundary:")
    print("    * Structural typing (person/animal/object/event, "
          "proper-vs-common, 'it's a name') is inferable now, no data — "
          "this is the win.")
    print("    * Fine-grained (male vs female name) + cross-lingual concept "
          "naming (es perro -> en dog) need data (name lists / "
          "translation). es/zh/ja held-out STRICT will NOT lift without it; "
          "they correctly TYPE the new concept but under its own surface "
          "name.")

    return 0 if (ok_john and ok_dog) else 1


if __name__ == "__main__":
    raise SystemExit(main())
