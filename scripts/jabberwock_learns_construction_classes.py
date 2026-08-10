"""CONSTRUCTION-LEARNING IS CLASS-LEARNING — the jabberwock reads a designation
FAMILY through ONE class-construction, and an UNSEEN designation surface joins the
class BY ADJACENCY (not by editing a list).

Naming / classification / "known as" / "termed" / "described as" / "defined as" are
INSTANCES of ONE relation — DESIGNATION (a thing bound to what it is CALLED). The
codebook grows by ABSTRACTIONS (a marker-CLASS + ONE construction over it), so the
unseen tail is covered on arrival. This is the correction of the Basalt enum
artifacts (europium_anomaly / scoria came from a naming construction the enum parser
mis-grounded as part_of).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_learns_construction_classes.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core          # noqa: E402
from domains import comprehend_text as ct           # noqa: E402
from domains import reading_collapse as rc          # noqa: E402


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def _designation_count(s):
    return sum(1 for nd in s.nodes("ShapeSignature")
               if s.node(nd)["attrs"].get("class_marker") == "DESIGNATE")


def _learned(s):
    return sorted(s.node(nd)["attrs"].get("name") for nd in s.nodes("ShapeSignature")
                  if s.node(nd)["attrs"].get("learned"))


def _member(agent, clause):
    _, _, ms = rc._skeleton_from_words(agent, ct._recognise_words(agent, clause))
    return [w for cl, w in ms if cl == "DESIGNATE"]


def main():
    s, node = boot_core()
    ag = _Agent(s, node)
    rc.ensure_codebook(ag)

    print("=" * 74)
    print("ONE CLASS COVERS THE FAMILY (called / described as / known as + UNSEEN termed)")
    print("=" * 74)
    for clause in ("a sonnet is called a poem", "a sonnet is described as a poem",
                   "a sonnet is known as a poem", "a sonnet is termed a poem"):
        r = rc.read_clause(ag, clause, write=False)
        print("  %-32s -> %-12s marker=%-10s %s"
              % (clause, r["construction"], _member(ag, clause), r["predications"]))
    print("  designation class-constructions in codebook =", _designation_count(s),
          "(ONE class, not four leaves); learned leaves =", _learned(s))

    print()
    print("=" * 74)
    print("NEW MARKER JOINS BY ADJACENCY (semantic nearness, not a hardcoded hit)")
    print("=" * 74)
    for w in ("termed", "dubbed", "styled", "christened"):
        ev = rc.adjacency_evidence(ag, w)
        print("  %-12s cls=%-10s nearness=%.2f -> nearest member %r via %s"
              % (w, ev["cls"], ev["nearness"], ev["nearest_member"], ev["signal"]))
    ev = rc.adjacency_evidence(ag, "chased")
    print("  %-12s cls=%-10s nearness=%.2f  (a content verb — NOT near designation)"
          % ("chased", ev["cls"], ev["nearness"]))

    print()
    print("=" * 74)
    print("CLASS vs LEAF MINT (the abstraction, not a designation hack)")
    print("=" * 74)
    before = _learned(s)
    r = rc.read_clause(ag, "a sonnet is styled a poem", write=False)
    print("  'a sonnet is styled a poem'  shares DESIGNATE shape -> constr=%s minted=%s"
          % (r["construction"], r["minted"]), "-> leaves unchanged:", _learned(s) == before)
    r = rc.read_clause(ag, "the capital of france", write=False)
    print("  'the capital of france'      NOVEL shape [OF]        -> minted=%s learned leaf=%s"
          % (r["minted"], _learned(s)))

    print()
    print("=" * 74)
    print("BASALT re-read corrected (enum: part_of  ->  reader: designation is_a)")
    print("=" * 74)
    for clause in ("the rock is described as scoria",
                   "the deviation is called the europium anomaly"):
        r = rc.read_clause(ag, clause, write=False)
        print("  %-45s -> %-12s %s" % (clause, r["construction"], r["predications"]))

    print()
    print("=" * 74)
    print("A SECOND CLASS FROM SEED DATA — POSSESSION -> has_property (NOT is_a)")
    print("=" * 74)
    print("  (added as pure seed data: a POSSESS MarkerClass + ONE class-construction;")
    print("   the only reading_collapse.py touch is 'POSSESS' in the _SKELETON set.)")
    for clause in ("a diamond exhibits hardness", "a diamond possesses hardness",
                   "a diamond features hardness", "a diamond bears hardness",
                   "a diamond demonstrates hardness"):    # last is UNSEEN (joins by adjacency)
        r = rc.read_clause(ag, clause, write=False)
        _, _, ms = rc._skeleton_from_words(ag, ct._recognise_words(ag, clause))
        mem = [w for cl, w in ms if cl == "POSSESS"]
        print("  %-30s -> %-11s marker=%-11s %s"
              % (clause, r["construction"], mem, r["predications"]))
    n_poss = sum(1 for nd in s.nodes("ShapeSignature")
                 if s.node(nd)["attrs"].get("class_marker") == "POSSESS")
    print("  possession class-constructions =", n_poss, "(ONE class, not five leaves);",
          "learned leaves =", _learned(s))

    print()
    print("=" * 74)
    print("POSSESSION unseen-join by adjacency (main-verb slot, threshold 0.7)")
    print("=" * 74)
    for w in ("demonstrates", "evidences", "displays", "manifests", "runs", "chased", "have", "point"):
        ev = rc.adjacency_evidence(ag, w)
        raw, arg = rc._wordnet_nearness(w, ["exhibit", "display", "manifest"])
        note = "" if ev["cls"] else "  (raw nearness %.2f < 0.7 -> rejected, stays content)" % raw
        print("  %-10s cls=%-9s nearness=%.2f nearest=%s%s"
              % (w, ev["cls"], ev["nearness"], ev["nearest_member"], note))

    print()
    print("=" * 74)
    print("TWO CLASSES COEXIST — no cross-fire (designation is_a vs possession has_property)")
    print("=" * 74)
    for clause in ("a sonnet is called a poem", "a diamond exhibits hardness"):
        r = rc.read_clause(ag, clause, write=False)
        print("  %-30s -> %-12s %s" % (clause, r["construction"], r["predications"]))


if __name__ == "__main__":
    main()
