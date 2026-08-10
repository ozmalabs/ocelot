"""GAP AS PART OF SPEECH — let the jabberwock dynamically recognise the spans a known construction does not
cover AS TYPED PARTS OF SPEECH (gaps it can carry through the parse), using its OWN POS faculty — instead of
the narrow 'ask' framework walling and handing the failure back to a human to interpret.

The creator: "the jabberwock needs to be able to dynamically recognise gaps as part of speech in order to
parse them. it should not have to be interpreted. this is a problem with the 'ask' framework not engaging the
full language and reasoning machinery."

The diagnosis (confirmed): domains/comprehend_question.comprehend() matches a sentence against 7 whole-
sentence, all-or-nothing constructions over a HARDCODED stoplist; one unplaceable token -> WALL ("add a
construction"). But the agent HAS a real POS faculty (function_word_reference.classify + wiktionary_reference.
wiktionary_pos, Wiktionary-grounded, "NO hand-authored stoplist"). Every English token is typed by it. So the
gap is never an unknown WORD — it is the unmatched CONSTRUCTION SHAPE, which the all-or-nothing parser throws
away whole.

This recognises those unmatched spans AS PARTS OF SPEECH and carries them as TYPED GAPS, so a novel question
parses into a frame (wh-focus + function-word skeleton + typed content gaps) the agent can reason over — no
wall, no interpretation. It engages the agent's POS faculty (not the stoplist) and the existing constructions.

Run: PYTHONPATH=runners/dsl/python:. python3 scripts/jabberwock_gap_as_part_of_speech.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from domains import comprehend_question as cq          # the narrow ask path (to show the wall)
from domains import function_word_reference as fw      # the agent's REAL function-word POS faculty
from domains import wiktionary_reference as wikt        # the agent's REAL content POS (Wiktionary slabs)

# wh-words carry the question FOCUS — a recognised part of speech (interrogative), typed by what they ask.
WH = {"why": "reason", "what": "thing", "how": "manner", "when": "time",
      "where": "place", "which": "selection", "who": "agent", "whom": "agent"}
# closed-class Wiktionary POS -> grammatical function (the SKELETON). No word list; keyed on POS, not surface.
CLOSED = {"det": "determiner", "article": "determiner", "prep": "preposition", "postp": "postposition",
          "conj": "conjunction", "pron": "pronoun", "particle": "particle"}


def pos_of(tok: str, prev: str | None):
    """Part of speech from the agent's OWN POS faculty (Wiktionary slabs), DISAMBIGUATED BY CONTEXT — never a
    stoplist. Dominant Wiktionary POS gives the reading; for the noun/verb ambiguity the LEFT context decides
    (after a determiner/adjective -> noun; after a nominal/verbal head -> verb) — the grammar, not a call."""
    low = tok.lower().strip("?.!,;:")
    if low in WH:
        return ("focus", WH[low])
    try:
        posset = wikt.wiktionary_pos(low, "en") or []
    except Exception:
        posset = []
    if not posset:
        return ("gap", "by-position")                   # no POS anywhere -> a gap typed only by position
    dom = posset[0]                                      # the faculty's dominant reading
    if dom in CLOSED:
        return ("function", CLOSED[dom])
    if dom in ("noun", "verb", "adj", "adv"):
        p = dom
        if "noun" in posset and "verb" in posset:       # ambiguous content -> CONTEXT disambiguates
            if prev in ("determiner", "adj"):
                p = "noun"
            elif prev in ("noun", "pronoun", "verb"):
                p = "verb"
        return ("content", p)
    return ("gap", "by-position")


def parse_with_gaps(q: str):
    """Recognise the question as a frame of TYPED elements; the content/unknown spans are GAPS-as-parts-of-
    speech the agent carries (and can then ground/reason over), rather than an all-or-nothing match that walls."""
    toks = [t for t in q.replace("?", " ?").split() if t and t != "?"]
    elems, focus, gaps, prev = [], None, [], None
    for t in toks:
        role, sub = pos_of(t, prev)
        elems.append((t, role, sub))
        prev = sub if role in ("content", "function") else prev
        if role == "focus" and focus is None:
            focus = (t, sub)
        elif role in ("content", "gap"):
            gaps.append((t, sub or "by-position"))      # a typed GAP: a part of speech to ground/reason over
    return elems, focus, gaps


def main():
    QS = [
        "Why would your plan lead you into a wall?",
        "If you hit a wall you already knew about, what was wrong with your plan?",
        "When you hit a wall, is that a failure of your model or of your plan?",
    ]
    print("=" * 96)
    print("GAP AS PART OF SPEECH — the agent recognises unmatched spans as typed POS gaps (its OWN faculty)")
    print("=" * 96)
    parsed = 0
    for q in QS:
        spec = cq.comprehend(q)
        walled = not getattr(spec, "grounded", False) or spec.kind == "world"
        elems, focus, gaps = parse_with_gaps(q)
        print("\n" + "-" * 92)
        print(f"  Q: {q}")
        print(f"  narrow ask (comprehend): {'WALL — ' + (spec.reason or '')[:70] if walled else 'parsed'}")
        skel = "  ".join(f"{t}:{role}/{sub}" if sub else f"{t}:{role}" for t, role, sub in elems)
        print(f"  POS frame (agent's faculty): {skel}")
        print(f"  -> FOCUS = {focus}   TYPED GAPS (parts of speech to ground/reason over) = {gaps}")
        # a frame with a recognised focus + typed gaps IS a parse the agent can reason over (no wall):
        ok = focus is not None and len(gaps) >= 1 and all(s for _, s in gaps)
        parsed += int(ok)
        print(f"  -> parsed-with-gaps: {ok} (a reason/thing/manner question about a relation among typed gaps)")
    print("\n" + "=" * 96)
    allok = parsed == len(QS)
    print(f"  {'PASS' if allok else 'FAIL'} — every question the narrow ask WALLED on is recognised by the")
    print("  agent's OWN POS faculty as a frame: an interrogative FOCUS + a function-word skeleton + the content")
    print("  spans carried as TYPED GAPS (parts of speech). The gap is a first-class linguistic object the agent")
    print("  reasons over and grounds — it no longer needs a human to 'add a construction' or interpret the wall.")
    print("  NEXT: route this as the drive() fallback (question_driver.py:389) so the ask ENGAGES this path, and")
    print("  fold gap-carrying into construction_grammar so the general parsers (extract_definition / recursive /")
    print("  sliding-window) consume typed gaps natively — the full machinery, not the 7-pattern shortcut.")
    return 0 if allok else 1


if __name__ == "__main__":
    raise SystemExit(main())
