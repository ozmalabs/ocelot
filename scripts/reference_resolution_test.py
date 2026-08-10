"""CROSS-UTTERANCE REFERENCE RESOLUTION — end-to-end through ConversationWorld.

Built to the taught ``reference_resolution`` model (seeds/reference_resolution.json):
a graph-resident discourse_referent_store + Centering/Givenness/Accessibility
procedure (domains/reference_resolution.py) wired into ConversationWorld.turn.
Before this the conversation was AMNESIAC about entities across turns; now a
pronoun ("it"/"he"/"she") or a definite ("the cat") in a later turn binds to the
entity introduced earlier.

Dialogues demonstrated (teacher OFF for the dialogue — the agent's own stack):
  1. "The cat sat on the mat."  then "Where is it?"
       -> "it" binds to cat (in_focus, non-person agreement) -> answer location.
  2. "Mary loves John."  then "Where does he live?" (+ "John lives in Paris.")
       -> "he" binds to John via agreement(person) + salience/Cb.
  3. definite re-mention: "A cat sat on the mat." ... "The cat is happy."
       -> "the cat" binds to the SAME DiscourseReferent (uniquely_identifiable).
  4. HONEST ambiguity/fail: a pronoun with NO agreeing in-focus referent ->
     unresolved, reported honestly (not bound to a wrong entity).

Per turn we print: the referring expression -> candidates (status / agreement /
salience) -> resolved referent (+ which rule: Cb / recency / agreement) -> the
answer; plus the discourse_referent_store + Cb evolution.

HONEST COVERAGE:
  * GROUNDED: animacy/number agreement from the Concept ``category`` attr
    (seeds/conceptual_categories.json); recency + grammatical-role salience;
    Cb/centering.
  * COARSE: gender (he vs she). No grounded gender data exists (Mary/John are
    both category=person), so he/she filter to PERSON and are disambiguated by
    SALIENCE/Cb, not gender. Reported per binding.
  * NOT BUILT: bridging_anaphora + deixis (seed scaffolding only).

No-regression: prints the 12-sentence comprehension bank score (must be 12/12)
and re-runs the non-pronoun conversation_test turns.
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


# Extra demo vocabulary grounded with the teacher ON (lives/Paris, happy).
_GROUNDING_BANK = [
    {"text": "John lives in Paris.", "language": "en", "expected_meaning": {}},
    {"text": "The cat is happy.", "language": "en", "expected_meaning": {}},
]


def _print_turn(rec: dict) -> None:
    print()
    print(f"USER : {rec['user']}")
    print(f"   frame (bound) : {rec['frame']}")
    rr = rec.get("reference_resolution")
    if rr:
        for r in rr:
            print(f"   REFERRING EXPRESSION: {r['surface']!r}  "
                  f"(kind={r['kind']}, slot={r.get('slot')})")
            for c in r.get("candidates", []):
                tag = []
                if "licensed_in_focus" in c:
                    tag.append("in_focus" if c["licensed_in_focus"]
                               else "NOT-in_focus")
                if "agreement" in c:
                    tag.append(c["agreement"])
                print(f"        candidate {c.get('concept')!r:10} "
                      f"status={c.get('status')} recency={c.get('recency')} "
                      f"role={c.get('last_role')!r}  [{'; '.join(tag)}]")
            if r.get("resolved"):
                print(f"     -> RESOLVED to {r['concept']!r}  via {r['rule']}"
                      f"   (substituted={r.get('substituted')})")
            else:
                print(f"     -> UNRESOLVED (honest): {r.get('reason')}")
    cen = rec.get("centering")
    if cen:
        print(f"   centering : Cf={cen['cf']}  Cb={cen['cb']!r}  "
              f"Cp={cen['cp']!r}  transition={cen['transition']}")
    print(f"   knowledge : {rec.get('knowledge_op')}")
    print(f"AGENT: {rec['reply']}")


def _print_store(cw: ConversationWorld) -> None:
    print("   discourse_referent_store (by recency):")
    for d in cw.transcript[-1].get("discourse_store", []):
        print(f"     {d['concept']!r:10} status={d['status']:22} "
              f"recency={d['recency']} role={d['role']!r} "
              f"animacy={d['animacy']} cat={d['category']} "
              f"mentions={d['mentions']}")


def _fresh_world():
    """A fresh substrate + trained LanguageWorld (teacher OFF for dialogue).
    Each dialogue gets its own so the discourse_referent_store starts EMPTY —
    the bindings shown are within that dialogue, not leaked from a prior one.
    Returns (world, base_matched)."""
    s = _native.Substrate()
    world = LanguageWorld(s, training_bank() + _GROUNDING_BANK, teacher_stub)
    comp_log = world.run()
    base_matched = sum(
        1 for r in comp_log
        if r["text"] in {t["text"] for t in training_bank()} and r["matched"])
    world.teacher_disabled = True
    return world, base_matched


def main(argv: list[str]) -> int:
    print("=" * 72)
    print("Setup: train comprehension + ground demo vocab (teacher ON)")
    print("  (a FRESH substrate per dialogue -> the discourse store starts")
    print("   empty; every binding shown is within-dialogue, not leaked)")
    print("=" * 72)
    world, base_matched = _fresh_world()
    print(f"  base comprehension bank: {base_matched}/12 matched")

    results: dict[str, bool] = {}

    # ===================================================================
    # DIALOGUE 1 — "it" -> cat (non-person agreement), location answer.
    # ===================================================================
    print()
    print("=" * 72)
    print("DIALOGUE 1 — pronoun 'it' binds to the earlier 'cat' (non-person")
    print("agreement); the where-question then answers the cat's location.")
    print("=" * 72)
    cw = ConversationWorld(world)
    cw.turn("The cat sat on the mat.", "en")
    _print_turn(cw.transcript[-1]); _print_store(cw)
    cw.turn("Where is it?", "en")
    _print_turn(cw.transcript[-1]); _print_store(cw)
    rec = cw.transcript[-1]
    rr = (rec.get("reference_resolution") or [{}])[0]
    results["D1 it->cat"] = (rr.get("concept") == "cat"
                             and "mat" in rec["reply"].lower())

    # ===================================================================
    # DIALOGUE 2 — "he" -> John via agreement(person) + salience/Cb.
    # ===================================================================
    print()
    print("=" * 72)
    print("DIALOGUE 2 — 'he' binds to John. Agreement leaves Mary AND John")
    print("(both person; no grounded gender), so SALIENCE/Cb disambiguates.")
    print("=" * 72)
    world2, _ = _fresh_world()
    cw2 = ConversationWorld(world2)
    cw2.turn("Mary loves John.", "en")
    _print_turn(cw2.transcript[-1]); _print_store(cw2)
    cw2.turn("John lives in Paris.", "en")   # establishes John as recent + fact
    _print_turn(cw2.transcript[-1]); _print_store(cw2)
    cw2.turn("Where does he live?", "en")
    _print_turn(cw2.transcript[-1]); _print_store(cw2)
    rec2 = cw2.transcript[-1]
    rr2 = (rec2.get("reference_resolution") or [{}])[0]
    results["D2 he->John"] = (rr2.get("concept") == "John"
                              and "paris" in rec2["reply"].lower())

    # ===================================================================
    # DIALOGUE 3 — definite re-mention binds to the same DiscourseReferent.
    # ===================================================================
    print()
    print("=" * 72)
    print("DIALOGUE 3 — definite re-mention: 'A cat sat ...' then 'The cat is")
    print("happy.' -> 'the cat' binds to the SAME DiscourseReferent")
    print("(uniquely_identifiable).")
    print("=" * 72)
    world3, _ = _fresh_world()
    cw3 = ConversationWorld(world3)
    cw3.turn("A cat sat on the mat.", "en")
    _print_turn(cw3.transcript[-1]); _print_store(cw3)
    cw3.turn("The cat is happy.", "en")
    _print_turn(cw3.transcript[-1]); _print_store(cw3)
    rec3 = cw3.transcript[-1]
    rr3 = (rec3.get("reference_resolution") or [{}])
    def_bind = next((r for r in rr3 if r.get("kind") == "definite"), {})
    # The SAME referent node was reused (one DiscourseReferent for 'cat').
    cat_refs = [d for d in cw3.transcript[-1]["discourse_store"]
                if d["concept"] == "cat"]
    results["D3 the-cat re-mention"] = (def_bind.get("concept") == "cat"
                                        and len(cat_refs) == 1)

    # ===================================================================
    # DIALOGUE 4 — HONEST FAIL: a pronoun with no agreeing in-focus referent.
    # ===================================================================
    print()
    print("=" * 72)
    print("DIALOGUE 4 — HONEST FAIL: 'they' (plural) has NO agreeing in-focus")
    print("referent (all referents singular) -> UNRESOLVED, reported honestly")
    print("(NOT bound to a wrong entity).")
    print("=" * 72)
    world4, _ = _fresh_world()
    cw4 = ConversationWorld(world4)
    cw4.turn("Mary loves John.", "en")
    _print_turn(cw4.transcript[-1])
    cw4.turn("Where do they live?", "en")
    _print_turn(cw4.transcript[-1]); _print_store(cw4)
    rec4 = cw4.transcript[-1]
    rr4 = (rec4.get("reference_resolution") or [{}])[0]
    results["D4 honest unresolved"] = (rr4.get("resolved") is False)

    # ===================================================================
    # Cb / store evolution summary (Dialogue 1).
    # ===================================================================
    print()
    print("=" * 72)
    print("Cb / centering evolution across DIALOGUE 1 turns")
    print("=" * 72)
    for i, r in enumerate(cw.transcript):
        cen = r.get("centering", {})
        print(f"  turn {i}: {r['user']!r:32}  Cf={cen.get('cf')}  "
              f"Cb={cen.get('cb')!r}  transition={cen.get('transition')}")

    # ===================================================================
    # WHICH MECHANISM resolved each binding.
    # ===================================================================
    print()
    print("=" * 72)
    print("WHICH MECHANISM resolved each binding")
    print("=" * 72)
    for cwx, label in ((cw, "D1 'it'"), (cw2, "D2 'he'"),
                       (cw3, "D3 'the cat'")):
        for r in cwx.transcript[-1].get("reference_resolution", []):
            if r.get("resolved"):
                print(f"  {label:14} {r['surface']!r:8} -> {r['concept']!r:8} "
                      f"by {r['rule']}")

    # ===================================================================
    # No-regression.
    # ===================================================================
    print()
    print("=" * 72)
    print("No-regression")
    print("=" * 72)
    base_ok = base_matched == 12
    print(f"  comprehension bank (language_test): "
          f"{base_matched}/12  {'OK' if base_ok else 'FAIL'}")
    # The non-pronoun turns still answer correctly (no spurious bindings).
    world5, _ = _fresh_world()
    cw5 = ConversationWorld(world5)
    cw5.turn("The cat sat on the mat.", "en")
    cw5.turn("Who sat on the mat?", "en")
    nonpron_ok = "cat" in cw5.transcript[-1]["reply"].lower()
    print(f"  non-pronoun 'Who sat on the mat?' still answers: "
          f"{'OK' if nonpron_ok else 'FAIL'} -> {cw5.transcript[-1]['reply']!r}")

    all_ok = base_ok and nonpron_ok
    print()
    for name, ok in results.items():
        print(f"  {name:26}: {'OK' if ok else 'FAIL'}")
        all_ok &= ok

    print()
    print(f"REFERENCE RESOLUTION TEST: "
          f"{'ALL OK' if all_ok else 'FAILURES ABOVE'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
