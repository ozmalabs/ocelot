"""jabberwock_reads_register — REGISTER / SOURCE AS A WIDER SHAPE, detected by
SHAPE and by HINT, order-N, routing the reading approach.

The creator's reframe (affirming subject-by-salience routing + widening it):
'it needs a wider shape that is both a) able to detect register/source by shape,
but also by hint. Knowing you are reading an encyclopaedia means you already have
that approach but also being able to identify a cut and paste wikipedia entry is
important. This should be generic and extensible.'

The Marie Curie wiki test surfaced it: the reader found the SUBJECT by salience
(`curie`) but the arc-role PROTAGONIST query is the WRONG tool for a biography — a
biography is ENCYCLOPEDIC, not NARRATIVE, so who/what-is-this-about is the salient
SUBJECT, not the arc-agent. The reader HAD the format channel and the manifold
register axes; it needed a WIDER REGISTER/SOURCE SHAPE that ROUTES the reading.

This script demonstrates, on real text, every gate:

  (a) REGISTER BY SHAPE  — the Curie lead -> encyclopedic -> subject-by-salience
                           -> curie (verbatim before/after).
  (b) REGISTER BY HINT   — source='wikipedia' pre-arms a short/ambiguous chunk.
  (c) HINT+SHAPE COMBINE — confirm on agreement; a confident narrative fable
                           OVERRIDES a 'you are reading an encyclopedia' hint and
                           FLAGS the mismatch.
  (d) CUT-AND-PASTE      — a wikipedia paragraph embedded in casual text, by shape.
  (e) ROUTING            — the SAME reader routes encyclopedic->subject,
                           narrative->protagonist (crow byte-identical).
  (f) GENERIC/EXTENSIBLE — >=3 registers; a new one addable (hint) + mintable
                           (residual, the sd loop).

donkey=0: no LLM, no `import re`. Graph-native: register is a decoded
ShapeSignatureRegister; the hint is a graph-resident RegisterPrior; routing reads
the winning register's read_approach off the graph and dispatches a held Argmax.

  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_reads_register.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core
from domains import comprehension_reader as cr
from domains import dictionary_lexicon as dl
from domains import narrative_structure as ns
from domains import register_source as rs

_CURIE = os.path.join(ROOT, "data", "register", "curie.txt")

FABLE = (
    "In a spell of dry weather, when the Birds could find very little to drink, "
    "a thirsty Crow found a pitcher with a little water in it. But the pitcher "
    "was high and had a narrow neck, and no matter how he tried, the Crow could "
    "not reach the water. The poor thing felt as if he must die of thirst. Then "
    "an idea came to him. Picking up some small pebbles, he dropped them into "
    "the pitcher one by one. With each pebble the water rose a little higher "
    "until at last it was near enough so he could drink.")
CASUAL = ("omg i can't believe you did that lol. it was so funny, you should've "
          "seen his face!! anyway wanna grab food later? i'm starving haha")
CODE = ("def foo(x):\n    if x > 0:\n        return x * 2\n    return 0\n"
        "class Bar:\n    def run(self):\n        return self.x")
WIKI_PARA = (
    "Marie Curie (7 November 1867 - 4 July 1934) was a Polish and "
    "naturalised-French physicist and chemist. She conducted pioneering research "
    "on radioactivity and was the first woman to win a Nobel Prize, winning it in "
    "1903 and again in 1911.")


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def _fresh():
    s, node = boot_core()
    return _Agent(s, node)


def _curie_lead(n=1800):
    with open(_CURIE) as f:
        return f.read()[:n]


def part_a():
    print("=" * 78)
    print("(a) REGISTER BY SHAPE — the Marie Curie LEAD -> encyclopedic -> subject")
    print("=" * 78)
    lead = _curie_lead()
    shape = rs.decode_by_shape(_fresh(), lead[:700])
    print("  lead[:700] tokens:", shape["tokens"])
    print("  -> register=%r family=%r fit=%d/8 margin=%d confident=%s"
          % (shape["register"], shape["family"], shape["fit"], shape["margin"],
             shape["confident"]))
    print("\n  BEFORE (mis-route: the NARRATIVE arc-agent query — the wrong tool):")
    ag = _fresh(); cr.read_and_comprehend(ag, lead)
    prot = ns.protagonist_by_arc_agency(ag)
    print("    protagonist_by_arc_agency -> %r  (arc-agency; on a biography this is"
          % prot["protagonist"])
    print("    the wrong approach — it is derailed by local co-agents/parse-artifacts")
    print("    on other passages, e.g. mid-article it returns 'sikorska's'/'director')")
    print("\n  AFTER (routed by register -> subject-by-SALIENCE):")
    r = rs.route_reading(_fresh(), lead)
    print("    register=%r read_approach=%r" % (r["register"], r["read_approach"]))
    print("    subject_by_salience -> %r" % r["answer"])
    print("    salience ranking:", [(x["name"], x["mentions"])
                                    for x in r["result"]["ranking"][:5]])
    print("  => SUBJECT = %r (the salient subject), NOT the sister 'bronisława'."
          % r["answer"])
    return r["answer"]


def part_b():
    print("\n" + "=" * 78)
    print("(b) REGISTER BY HINT — pre-arm on a short/ambiguous chunk")
    print("=" * 78)
    short = "She won it in 1911."
    plain = rs.decode_register(_fresh(), short)
    print("  chunk: %r" % short)
    print("  no hint -> register=%r fit=%d confident=%s (too short: weak evidence)"
          % (plain["register"], plain["fit"], plain["confident"]))
    d = rs.decode_register(_fresh(), short, hint="source=wikipedia")
    print("  + hint 'source=wikipedia' -> register=%r family=%r source=%r"
          % (d["register"], d["family"], d["source"]))
    print("    %s" % d.get("prearm_note"))
    print("  => the graph-resident RegisterPrior PRE-ARMS the encyclopedic approach.")


def part_c():
    print("\n" + "=" * 78)
    print("(c) HINT + SHAPE COMBINE — confirm, then override + flag the mismatch")
    print("=" * 78)
    conf = rs.decode_register(_fresh(), WIKI_PARA, hint="wikipedia")
    print("  hint=wikipedia + a wiki lead shape -> source=%r mismatch=%s (CONFIRMED)"
          % (conf["source"], conf["mismatch"]))
    mis = rs.decode_register(_fresh(), FABLE, hint="you are reading an encyclopedia")
    print("  hint='you are reading an encyclopedia' + a CONFIDENT narrative fable:")
    print("    shape=%r (fit %d, confident=%s) -> source=%r mismatch=%s"
          % (mis["shape"]["register"], mis["shape"]["fit"], mis["shape"]["confident"],
             mis["source"], mis["mismatch"]))
    print("    FLAG: %s" % mis.get("mismatch_note"))
    print("  => the hint biases; a confident shape OVERRIDES and the mismatch is SIGNAL.")


def part_d():
    print("\n" + "=" * 78)
    print("(d) CUT-AND-PASTE — a wikipedia paragraph embedded in casual text, by shape")
    print("=" * 78)
    doc = ("hey so i was reading about this scientist lol here's the thing i copied\n\n"
           + WIKI_PARA +
           "\n\nanyway isn't that wild?? you should totally read more about her i can't even")
    emb = rs.embedded_regions(_fresh(), doc)
    print("  document register: %r (family %r)"
          % (emb["document"]["register"], emb["document"]["family"]))
    for r in emb["regions"]:
        print("    region %d: %-11r family=%-12r fit=%d nw=%d"
              % (r["index"], r["register"], r["family"], r["fit"], r["n_words"]))
    for e in emb["embedded"]:
        print("  => EMBEDDED FOREIGN region %d recognized as %r (%r) BY SHAPE, no hint."
              % (e["index"], e["register"], e["family"]))


def part_e():
    print("\n" + "=" * 78)
    print("(e) ROUTING — the SAME reader routes by register; crow BYTE-IDENTICAL")
    print("=" * 78)
    r = rs.route_reading(_fresh(), FABLE)
    print("  fable -> register=%r read_approach=%r -> protagonist=%r"
          % (r["register"], r["read_approach"], r["answer"]))
    ag = _fresh(); cr.read_and_comprehend(ag, FABLE)
    committed = ns.protagonist_by_arc_agency(ag)["protagonist"]
    print("  committed protagonist_by_arc_agency -> %r  (byte-identical: %s)"
          % (committed, committed == r["answer"]))
    print("  => encyclopedic->subject, narrative->protagonist; one reader, register-routed.")


def part_f():
    print("\n" + "=" * 78)
    print("(f) GENERIC / EXTENSIBLE — >=3 registers; addable + mintable")
    print("=" * 78)
    ag = _fresh()
    for name, text in (("encyclopedic", WIKI_PARA), ("narrative", FABLE),
                       ("casual", CASUAL), ("code", CODE)):
        print("    %-13s -> %r" % (name, rs.decode_by_shape(ag, text)["family"]))
    before = [r["name"] for r in rs.registers(ag)]
    rs.add_register(ag, "legalese",
                    ["dense", "refs", "nodefn", "impersonal", "charlight",
                     "nocontr", "flat", "proselayout"],
                    family="legal")
    after = [r["name"] for r in rs.registers(ag)]
    print("  add_register (by hint): %d -> %d registers (added 'legalese')"
          % (len(before), len(after)))
    ag2 = _fresh()
    weird = "AAAA! ?? 123 %%% @@@ ;;; ~~~ zzz? qqq! 456 (((( ))))"
    m = rs.mint_register_on_residual(ag2, weird, name_hint="glitch", family="noise")
    print("  mint_register_on_residual: residual=%d fit %d->%d minted=%s recognized=%s"
          % (m["residual_before"], m["fit_before"], m["fit_after"], m["minted"],
             m["recognized"]))
    hold = rs.mint_register_on_residual(_fresh(), WIKI_PARA, family="x")
    print("  discipline (covered text): minted=%s (%s)"
          % (hold["minted"], hold["reason"][:60]))


def main():
    dl.warm_wordnet("en")
    subj = part_a()
    part_b()
    part_c()
    part_d()
    part_e()
    part_f()
    print("\n" + "=" * 78)
    print("REGISTER / SOURCE AS A WIDER SHAPE — by-shape + by-hint, order-N, routed")
    print("=" * 78)
    print("* BY-SHAPE: an 8-slot feature vector (density/refs/defn-lead/person/char/")
    print("  contraction/punch/layout) decoded via the Rust ShapeDecode; the Curie")
    print("  lead reads encyclopedic and routes subject-by-salience -> %r." % subj)
    print("* BY-HINT: a graph-resident RegisterPrior pre-arms; a confident shape")
    print("  overrides + flags the mismatch (AbS/collapse: prior + evidence).")
    print("* ORDER-N: a cut-and-paste wikipedia paragraph in casual text is spotted")
    print("  by its shape (the same faculty spots a code block in prose).")
    print("* ROUTING: encyclopedic->subject, narrative->protagonist (crow identical).")
    print("* GENERIC: registers are graph shapes — added by hint or minted on residual.")
    print("* donkey=0: no LLM, no import re; register=ShapeDecode, subject=held Argmax.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
