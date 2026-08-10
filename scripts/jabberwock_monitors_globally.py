"""GLOBAL comprehension monitoring, demonstrated — the jabberwock catches a
contradiction the LOCAL review can't see.

domains/reading_review.py is a strong LOCAL (within-clause) standards-of-
coherence monitor — but it is local: it scores one clause's own predications
and cannot see a contradiction between two facts far apart in the text
(Glenberg, Meyer & Lindem 1982's illusion-of-knowing; O'Brien & Cook 2016's
RI-Val model assigns exactly this to its VALIDATION stage — a new
proposition checked against the WHOLE situation model, not the current
clause). domains/global_monitoring.py is THE ONE WIRE for that: it points
reading_review's own incoherence discipline (salience, licensing) at the
ACCUMULATED situation model (domains/situation_model_reader.py) instead of a
single clause, using a graph-native Program (Var/Eq/Not/And — the SAME
vocabulary seeds/reading_review.json's `review_license` Program already
proves sufficient) to decide whether a newly-entailed fact CONTRADICTS an
established one. A fired contradiction escalates to reading_scope's
EXISTING retained-trace / cold re-read path — never silently accepted.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_monitors_globally.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core
from domains import dictionary_lexicon as dl
from domains import global_monitoring as gm
from domains import reading_review as rr

SEP = "=" * 92


class _Agent:
    def __init__(self, s, node):
        self.s, self.inner, self.agent = s, s._inner, node


def _fresh():
    s, node = boot_core()
    return _Agent(s, node)


def _print_textbase(r: dict) -> None:
    for tb in r["textbase"]:
        print("    %-32s -> %-45s local_incoherence=%.2f [%s]"
              % (tb["sentence"], tb["predications"], tb["local_incoherence"], tb["source"]))


def _print_checks(r: dict) -> None:
    for c in r["checks"]:
        flag = "** GLOBAL INCOHERENCE FIRED **" if c["contradiction"] else "(consistent)"
        note = c.get("note")
        if note:
            print("    %-32s kin=%-40s %s" % (c["sentence"], note, flag))
        else:
            print("    %-32s %s.%-10s established=%-10r new=%-10r  %s"
                  % (c["sentence"], c["entity"], c["attr"], c["established"], c["new"], flag))


def main():
    dl.warm_wordnet("en")

    print(SEP)
    print("GLOBAL COMPREHENSION MONITORING — reading_review pointed at the situation model")
    print(SEP)

    # ---- HEADLINE ---------------------------------------------------------- #
    print("\n  HEADLINE — the far-apart contradiction LOCAL review can't catch:\n")
    passage = "The lawyer had no children. She was busy. His daughter arrived home."
    print("  passage: %r\n" % passage)
    ag = _fresh()
    r = gm.read_and_monitor(ag, passage)

    print("  LOCAL — each clause reviewed on its OWN (reading_review.combined_incoherence,")
    print("  reused verbatim). Every clause independently reads as COHERENT:")
    _print_textbase(r)

    print("\n  Confirming reading_review itself sees nothing wrong with EITHER clause of the")
    print("  contradiction, taken alone:")
    for sent in ("The lawyer had no children.", "His daughter arrived home."):
        tb = next(e for e in r["textbase"] if e["sentence"] == sent)
        incoh = rr.combined_incoherence(ag, {"predications": tb["predications"]})
        print("    reading_review.combined_incoherence(%r) = %.2f  (passes)" % (sent, incoh))

    print("\n  GLOBAL — validated against the ACCUMULATED situation model instead:")
    _print_checks(r)

    print("\n  lawyer's situation-model state slice after all three sentences:")
    print("    %s" % r["situation_model"]["lawyer"])

    print("\n  ESCALATION — a fired contradiction is NOT silently accepted; it re-invokes")
    print("  reading_scope's EXISTING retained-trace / cold re-read path (RI-Val:")
    print("  Validation -> failure -> reprocess), unchanged:")
    for esc in r["escalations"]:
        print("    prior:   %r" % esc["prior_sentence"])
        print("    trigger: %r" % esc["trigger_sentence"])
        print("    path:    %s" % esc["path"])
        print("    note:    %s" % esc["note"])

    # ---- DISCRIMINATIVE: no false alarm ------------------------------------ #
    print("\n" + SEP)
    print("  DISCRIMINATIVE — no false alarm")
    print(SEP)

    print("\n  (a) a GLOBALLY-CONSISTENT continuation ('two children' -> 'his daughter'):")
    passage2 = "The lawyer had two children. She was busy. His daughter arrived home."
    ag2 = _fresh()
    r2 = gm.read_and_monitor(ag2, passage2)
    print("  passage: %r\n" % passage2)
    _print_checks(r2)
    print("    n_escalations = %d  (none — nothing contradicts)" % len(r2["escalations"]))

    print("\n  (b) an UNRELATED-but-consistent continuation (no kinship term at all):")
    passage3 = "The lawyer had two children. She was busy. The weather was nice."
    ag3 = _fresh()
    r3 = gm.read_and_monitor(ag3, passage3)
    print("  passage: %r\n" % passage3)
    _print_textbase(r3)
    print("    checks fired: %d  (only the kinship-bearing clause is ever checked)"
          % sum(1 for c in r3["checks"] if c["contradiction"]))

    # ---- HONEST RESIDUALS --------------------------------------------------- #
    print("\n" + SEP)
    print("  HONEST SCOPE — what this catches vs what is a residual")
    print(SEP)
    print("\n  CAUGHT (a): a DIRECT attr conflict already in the codebook's own canon")
    print("    (has_child 0 vs 1) -- the headline above.")
    print("\n  CAUGHT (b): an ENTAILED conflict via the seeded KINSHIP class (daughter/")
    print("    son/child/children all canonicalise to has_child) -- also the headline.")

    print("\n  MISSED (residual): an unseen kinship term the codebook does not name.")
    ag4 = _fresh()
    mem = gm.kinship_membership(ag4, "grandchild")
    print("    kinship_membership(ag, 'grandchild') = %s  (exact-form only; unlike COS's" % mem)
    print("    verb class, the WordNet nearness helper is verb-scoped and does not")
    print("    transplant onto a noun class -- see domains/global_monitoring.py docstring.)")

    print("\n  MISSED (residual): a bare kinship subject with no possessive determinant")
    print("    has no resolvable possessor -- held open, not guessed:")
    ag5 = _fresh()
    r5 = gm.read_and_monitor(ag5, "Daughter arrived home.")
    print("    'Daughter arrived home.' -> %s" % r5["checks"][0]["note"])

    print("\n" + SEP)
    print("  The situation model is now globally monitored, not just locally reviewed:")
    print("  reading_review's OWN incoherence discipline, reused unchanged, pointed at")
    print("  the accumulated model instead of a single clause.")
    print(SEP)


if __name__ == "__main__":
    main()
