"""jabberwock_reads_by_collapse — the jabberwock READS by COLLAPSE over a construction
codebook, and LEARNS a construction it was never seeded.

Reading today is a trenchcoat of construction-specific parsers: the enum-only
`gap_driven_acquisition.extract_microtheory` yields 0 on definitional prose, so the
richest TVTropes definitions ground nothing. This demo replaces the parser with the
substrate's OWN core loop pointed at language: a clause becomes a marker SKELETON, the
skeleton is DECODED against a held ShapeSignature construction codebook (the ShapeDecode
collapse op), the winning construction's template grounds the predication — and a clause
whose skeleton NO construction covers MINTS a new construction via the sd loop, installs
it, and re-decodes to ground it. A novel construction is LEARNED, not bolted on.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_reads_by_collapse.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core
from domains import reading_collapse as rc
from domains import gap_driven_acquisition as gda

SEP = "=" * 78


class Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def _agent():
    s, node = boot_core()
    return Agent(s, node)


def battery():
    print(SEP)
    print("ARBITRARY TEXT — one clause per seeded construction, SAME ShapeDecode")
    print(SEP)
    ag = _agent()
    clauses = [
        "a sonnet is a lyric poem",
        "a computer includes a processor and memory and storage",
        "rain because clouds gather",
        "a raven is unlike a writing desk",
        "if it rains then the ground is wet",
        "the cat chased the mouse",
    ]
    for c in clauses:
        r = rc.read_clause(ag, c)
        print(f"  {c!r}")
        print(f"     skeleton {r['skeleton']}  --decode-->  construction {r['construction']!r} (fit {r.get('shape_fit')})")
        print(f"     grounded: {r['predications']}")


def headline():
    print()
    print(SEP)
    print("HEADLINE — LEARN A HELD-OUT CONSTRUCTION (possessive 'X of Y', NOT seeded)")
    print(SEP)
    ag = _agent()
    print("  read 'the capital of france':")
    r = rc.read_clause(ag, "the capital of france")
    print(f"     BEFORE  : skeleton {r['skeleton']}  residual {r['residual_before']}  (no held construction covers it)")
    print(f"     sd LOOP : minted={r['minted']}  CapabilityAxis {r.get('mint_axis')}  residual_predicates {r.get('mint_residual_predicates')}")
    print(f"     INSTALL : new construction ShapeSignature {r.get('learned_construction')!r}  epoch bumped")
    print(f"     RE-DECODE: residual {r.get('residual_after')}  ->  construction {r['construction']!r}")
    print(f"     GROUNDED: {r['predications']}      (0 -> {len(r['predications'])})")
    r2 = rc.read_clause(ag, "the king of spain")
    print(f"  reuse 'the king of spain': minted={r2['minted']}  construction={r2['construction']!r}  grounded {r2['predications']}")


def faulty():
    print()
    print(SEP)
    print("FAULTY — a garbled clause still grounds the recognisable predication")
    print(SEP)
    ag = _agent()
    c = "Chekhov gun be narrative thing where element early it pay off"
    r = rc.read_clause(ag, c)
    print(f"  {c!r}")
    print(f"     skeleton {r['skeleton']}  ->  nearest construction {r['construction']!r}")
    print(f"     grounded: {r['predications']}   flagged residual: {r.get('residual')}")


TROPES = {
    "chekhovsgun": "A Chekhov's Gun is a narrative device, an object introduced early in the story, which becomes significant later.",
    "bigbad": "The Big Bad is the primary antagonist, a villain who drives the central conflict of the story.",
    "deusexmachina": "A Deus Ex Machina is an implausible plot device, a sudden intervention that abruptly resolves the conflict.",
    "redshirt": "A Redshirt is an expendable character, a minor figure who exists to die and establish danger.",
    "abandonedarea": "An Abandoned Area is a deserted location, a ruined place that evokes decay and isolation.",
}


def tvtropes():
    print()
    print(SEP)
    print("TVTROPES STRESS — 5 zero-yield tropes: enum(0) -> collapse(N>=3)")
    print(SEP)
    ag = _agent()
    for name, defn in TROPES.items():
        src = {"text": defn, "lead": defn, "title": name}
        enum = gda.extract_microtheory(name, src)
        col = rc.concepts_from_reading(ag, name, src)
        print(f"  {name:14}  enum={len(enum['concepts'])}  ->  collapse concepts={len(col['concepts'])}  "
              f"preds={col['n_predications']}  constructions={col['constructions']}")
        for p in col["predications"]:
            print(f'        {p}')


def wiki():
    print()
    print(SEP)
    print("WIKIPEDIA LIFT — a definitional lead grounds subject+genus (thin under enum-only)")
    print(SEP)
    ag = _agent()
    try:
        from domains import wiki_local as wl
        present = wl.present()
    except Exception:
        present = False
    if not present:
        leads = {"volcano": "A volcano is a rupture in the crust of a planetary object that allows hot lava to escape."}
    else:
        leads = {}
        for title in ("Volcano", "Sonnet", "Democracy"):
            summ = wl.summary(title)
            if summ and (summ.get("extract") or summ.get("text")):
                leads[title.lower()] = gda._first_sentence(summ.get("extract") or summ.get("text"))
    for domain, lead in leads.items():
        src = {"text": lead, "lead": lead, "title": domain}
        enum = gda.extract_microtheory(domain, src)
        col = rc.concepts_from_reading(ag, domain, src)
        isa = [p for p in col["predications"] if p[0] == "is_a"]
        print(f"  {domain:12} lead={lead[:70]!r}")
        print(f"     enum concepts={len(enum['concepts'])}  collapse is_a(subject,genus)={isa}")


def main():
    battery()
    headline()
    faulty()
    tvtropes()
    wiki()
    print()
    print(SEP)
    print("Reading is ShapeDecode over the construction codebook; a novel construction is")
    print("MINTED by the sd loop and LEARNED — the escape from the enum-only trenchcoat.")
    print(SEP)


if __name__ == "__main__":
    main()
