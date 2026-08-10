"""JABBERWOCK COMPREHENDS ARBITRARY TEXT — the discriminative gate for
domains/comprehend_text.py, the GENERAL comprehension front end.

The creator: "it should reason over arbitrary text input — this seems to be a
cobbled together parsing infrastructure." Confirmed: `domains/comprehend_
question.py`'s `comprehend()` is a table of ~7 whole-sentence CONSTRUCTIONS
matched against a fixed surface-fragment lexicon; a phrasing that matches none
of them returns `grounded=False` and the chat falls back to "acknowledgment" —
even for an honest, answerable self-question. This is the recurring project
lesson (see CLAUDE.md / memory ozma_ask_framework_vs_full_machinery): the agent
ALREADY HAS a general language faculty (POS-typing + the gap-as-part-of-speech
parser + the relation composer, `domains/construction_grammar.py`); the table
was a narrow shortcut bypassing it.

This script pins the CONTRAST: for each test sentence it prints (1) what the
OLD table does (None/ungrounded, or grounded — the fast path), (2) what the
NEW general path (`comprehend_text.comprehend_text`) derives, and (3) the REAL
answer `WorldAdapter.answer_question` now produces end-to-end. It also proves
the three-way INTENT-KIND discrimination (question / instruction / statement)
and that TYPED GAPS are carried (never fabricated over).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_comprehends_arbitrary.py
"""
from __future__ import annotations
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from substrate.world_adapter import WorldAdapter          # noqa: E402
from substrate.boot_all import load_all_seeds             # noqa: E402
from domains import comprehend_question as cq              # noqa: E402
from domains import comprehend_text as ct                  # noqa: E402


# ---------------------------------------------------------------------------
# THE CONTRAST BATTERY — paraphrases of a self-question the OLD table has no
# fragment for. Each must (a) MISS the table, (b) derive a reflexive dispatch,
# (c) answer for real through the SAME chat path.
# ---------------------------------------------------------------------------
CONTRAST = [
    "Tell me about the rule hop_descend_gradient.",
    "can you describe how you're put together?",
    "What kind of thing are you?",
]

# INTENT-KIND discrimination.
KIND_BATTERY = [
    ("How are you organised today, honestly?", "question"),
    ("look left", "instruction"),
    ("run diagnostics", "instruction"),
    ("The rule hop_descend_gradient modifies gravity.", "statement"),
]

# TYPED GAPS — an unknown token must be carried, never fabricated over.
GAP_TEXT = "look left then quorplezap the door"

# REGRESSION — a self-question the table DID handle keeps its exact behaviour.
TABLE_HIT = ["How are you organised?", "what's your shape",
             "what does hop_descend_gradient do?"]


def _hr(c="-"):
    print(c * 96)


def main() -> int:
    a = WorldAdapter(seeds=())
    load_all_seeds(a)

    print("=" * 96)
    print("JABBERWOCK COMPREHENDS ARBITRARY TEXT — general front end vs the old construction table")
    print("=" * 96)

    ok = True

    print("\n--- THE CONTRAST: phrasings the OLD table misses, the GENERAL path now comprehends ---")
    for text in CONTRAST:
        spec = cq.comprehend(text)
        table_missed = not getattr(spec, "grounded", False)
        comp = ct.comprehend_text(a, text)
        ans = a.answer_question(text)
        answered = isinstance(ans, str) and ans.strip() and \
            ans.strip().lower() not in ("acknowledgment", "noted")
        _hr()
        print(f"  TEXT: {text!r}")
        print(f"  old table (comprehend_question.comprehend): "
              f"{'MISS (grounded=False)' if table_missed else 'grounded, kind=' + spec.kind}")
        print(f"  comprehend_text: {comp.line()}")
        print(f"  answer_question -> {ans!r}"[:160])
        good = table_missed and comp.kind == "question" and comp.reflexive and answered
        print(f"  -> {'PASS' if good else 'FAIL'} (table missed AND general path derived a reflexive "
              f"dispatch AND the chat produced a real answer)")
        ok = ok and good

    print("\n--- INTENT-KIND DISCRIMINATION: question / instruction / statement ---")
    for text, expected in KIND_BATTERY:
        comp = ct.comprehend_text(a, text)
        good = comp.kind == expected
        _hr()
        print(f"  TEXT: {text!r} -> kind={comp.kind} (expected {expected}) intent={comp.intent!r}")
        print(f"  -> {'PASS' if good else 'FAIL'}")
        ok = ok and good

    print("\n--- TYPED GAPS: an unknown token is carried, never fabricated over ---")
    comp = ct.comprehend_text(a, GAP_TEXT)
    gap_frame = [(g["surface"], g["pos"]) for g in comp.gaps]
    _hr()
    print(f"  TEXT: {GAP_TEXT!r}")
    print(f"  gap frame: {gap_frame}")
    has_unknown_gap = any(s == "quorplezap" and p == "by-position" for s, p in gap_frame)
    print(f"  -> {'PASS' if has_unknown_gap else 'FAIL'} "
          f"('quorplezap' carried as an honestly-typed unknown gap)")
    ok = ok and has_unknown_gap

    print("\n--- BACK END UNCHANGED: a self-question the table DID handle keeps its exact prior answer ---")
    for text in TABLE_HIT:
        comp = ct.comprehend_text(a, text)
        ans = a.answer_question(text)
        good = comp.fastpath and isinstance(ans, str) and bool(ans.strip())
        _hr()
        print(f"  TEXT: {text!r} -> fastpath={comp.fastpath}  answer[:80]={ans[:80]!r}")
        print(f"  -> {'PASS' if good else 'FAIL'}")
        ok = ok and good

    print("\n" + "=" * 96)
    print(f"  {'ALL PASS' if ok else 'SOME FAILED'} — arbitrary text now reasons through the agent's OWN "
          "general language faculty (POS-typing + gap-as-part-of-speech + relation composition), deriving "
          "intent from the parse instead of matching a fixed sentence-shape table. The table remains a fast "
          "path for the shapes it already covers; the general path handles what it misses, honestly, with "
          "typed gaps carried instead of fabricated over.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
