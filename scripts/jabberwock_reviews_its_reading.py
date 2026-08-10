"""The jabberwock REVIEWS its own reading.

reading_collapse.read_clause is surface-noise-robust but commits to the FIRST
shape-match with no meaning-level review: 'I could of done that' decodes the faulty
'of' as the LEARNED possessive and grounds the nonsense `[of, i_could, done_that]` —
residual empty, no flag, confident-wrong. This script shows the review it lacked.

ONE mechanism, TWO error classes. An incoherent shape has ADJACENT shapes
(near-neighbours in some domain's dimension-space); the resolution is the adjacent
shape that COHERES; WHICH domain the corruption came from EMERGES from which
adjacency resolves it:

  READ -> COHERENCE-SALIENCE -> ORDER-N ESCALATING REVIEW
       -> CROSS-DOMAIN ADJACENCY COLLAPSE (phonology / keyboard / glyph / concept)
       -> STOP BY SUFFICIENCY

The order (gap_priority), the escalate-or-stay (review_escalate), the winning
neighbour (candidate_pick) and the stop (should_continue) are seeded graph Programs
evaluated in Rust; the adjacency is seeded dimension-space structure; the re-decode
is the collapse (read_clause). Nothing here is a from->to correction table.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_reviews_its_reading.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core            # noqa: E402
from domains import dictionary_lexicon as dl          # noqa: E402
from domains import reading_review as rr              # noqa: E402


class _Agent:
    def __init__(self, s, node):
        self.s, self.inner, self.agent = s, s._inner, node


def _line(c: str = "-") -> None:
    print(c * 74)


def _show_clause(agent, clause: str) -> None:
    r = rr.review_clause(agent, clause)
    read = r["reading"]
    print("  clause      : %r" % clause)
    print("  read as     : %s  (construction %r)"
          % (read["predications"] or read["roles"], read["construction"]))
    print("  salience    : %.2f  (incoherence of the grounded reading)" % r["salience"])
    if not r["repaired"]:
        print("  verdict     : COHERENT — not reviewed (below the sufficiency floor)")
        return
    rep = r["repair"]
    ladder = " -> ".join("%s(%d cand, coh %.1f)" % (x["domain"], x["n_candidates"], x["best_coherence"])
                         for x in rep["ladder"])
    print("  escalate    : %s" % ladder)
    print("  neighbour   : %r -> %r  (%s-adjacent)" % (rep["token"], rep["neighbor"], rep["domain"]))
    print("  re-decodes  : %s  COHERENT" % rep["new_predications"])
    print("  DOMAIN      : %s  <-- emerged from the adjacency that resolved it" % rep["domain"].upper())


def main() -> None:
    dl.warm_wordnet("en")
    s, node = boot_core()
    agent = _Agent(s, node)
    rr.ensure_review_seed(agent)

    print("\nTHE JABBERWOCK REVIEWS ITS OWN READING")
    print("shape + adjacency, any domain: an incoherent shape's coherent neighbour "
          "collapses out,\nand the corruption's DOMAIN emerges from which adjacency "
          "resolved it.\n")

    _line("=")
    print("TRANSCRIPTION errors  (the surface got corrupted; SURFACE adjacency)")
    _line("=")
    for c in ("I could of done that", "I should of known better",
              "the child hugged her freind", "the boy watched the mvoie",
              "the dog wagged its tai1"):
        _show_clause(agent, c)
        _line()

    _line("=")
    print("COGNITIVE error  (wrong-but-close WORD, recoverable; CONCEPT adjacency)")
    _line("=")
    _show_clause(agent, "for all intensive purposes")
    _line()

    _line("=")
    print("NO FALSE REPAIR  (a correct reading scores low salience — untouched)")
    _line("=")
    for c in ("the capital of france", "the king of spain",
              "the cat chased the mouse", "I gave it to her"):
        r = rr.review_clause(agent, c)
        print("  %-26s incoherence %.2f  repaired=%s" % (c, r["incoherence"], r["repaired"]))
    _line()

    _line("=")
    print("ORDER-N review  (order most-incoherent-first; recurse; stop by sufficiency)")
    _line("=")
    text = "the freind chased the mvoie. the dog wagged its tai1."
    print("  text: %r\n" % text)
    out = rr.review_text(agent, text)
    for i, p in enumerate(out["passes"], 1):
        rank = "  |  ".join("%r sal %.2f" % (x["clause"], x["salience"]) for x in p["ranking"])
        print("  pass %d ranking : %s" % (i, rank))
        if p.get("repaired"):
            rp = out["repairs"][i - 1] if i - 1 < len(out["repairs"]) else {}
            print("         repair  : top clause -> %s-adjacent %r -> %r"
                  % (rp.get("domain"), rp.get("token"), rp.get("neighbor")))
    print("\n  passes        : %d" % out["n_passes"])
    print("  final reading : %s" % out["clauses"])
    print("  domains       : %s" % [rp["domain"] for rp in out["repairs"]])
    _line()

    _line("=")
    print("RICHER COHERENCE — cohere-in-CONTEXT catches a malapropism groundability missed")
    _line("=")
    print("  'the report infers ...' GROUNDS (infer is a real verb, report a real noun),")
    print("  so groundability scores it coherent. The RELATION's selectional fit does not:")
    print("  a mental verb ('infers') needs a sentient subject — a report cannot infer.\n")
    _show_clause(agent, "the report infers that prices will rise")
    _line()

    _line("=")
    print("HOLD-OPEN — collapse only when LICENSED; else flag + hold (the anti-polygraph)")
    _line("=")
    print("  SAME token 'bst', SAME two groundable neighbours (bat animate / bet inanimate).")
    print("  UNDER-FORMED: a perception verb does not disambiguate -> HELD OPEN.")
    print("  WELL-FORMED : a COGNITION verb excludes the inanimate 'bet' -> collapse to 'bat'.\n")
    for c in ("she saw the bst", "the bst understood the plan"):
        r = rr.review_clause(agent, c)
        rep = r["repair"] or {}
        if r["held_open"]:
            cands = ", ".join("%s(coh %.2f)" % (d["neighbor"], d["coherence"])
                              for d in rep.get("candidates") or [])
            print("  %-30s HELD OPEN  candidates: %s  (best-runnerup within margin)"
                  % (repr(c), cands))
        elif r["repaired"]:
            print("  %-30s COLLAPSE   %r -> %r  (best %.2f  runnerup %.2f  self %.2f)"
                  % (repr(c), rep["token"], rep["neighbor"], rep["coherence"],
                     rep["runnerup_coherence"], rep["self_coherence"]))
    _line()

    _line("=")
    print("FALSE FRIENDS — surface-adjacency and contextual-meaning DIVERGE, both ways")
    _line("=")
    print("  DIRECTION A (do NOT repair a correctly-used real word — context licenses it):")
    for c in ("the horse has a peculiar gait", "he plays the bass",
              "he was chomping at the bit", "the noise will affect his sleep"):
        r = rr.review_clause(agent, c)
        why = ("etymology!=usage: 'chomping' is current-usage-correct"
               if "chomping" in c else "context licenses the token as-itself")
        print("  %-34s selectional %.2f -> LEFT   (%s)"
              % (repr(c), rr.selectional_incoherence(agent, r["reading"]), why))
    print("\n  DIRECTION B (DO recover a false-friend misuse — grounds but misfits context):")
    r = rr.review_clause(agent, "the report infers that prices will rise")
    print("  %-34s -> %s-adjacent %r  (%s)"
          % (repr("the report infers ..."), r["repair"]["domain"],
             r["repair"]["neighbor"], "a report implies, it cannot infer"))
    _line()

    _line("=")
    print("A coherent text needs NO review pass (sufficiency, not completion):")
    out2 = rr.review_text(agent, "the cat chased the mouse. the capital of france.")
    print("  %r -> %d review passes" % ("the cat chased the mouse. the capital of france.",
                                        out2["n_passes"]))
    _line("=")
    print("\nThe reader read; the reviewer escalated; the coherent neighbour collapsed "
          "out;\nthe domain emerged. Surface AND concept errors, one collapse.\n")


if __name__ == "__main__":
    main()
