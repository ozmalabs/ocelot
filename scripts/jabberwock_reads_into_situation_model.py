"""THE WIRE, demonstrated — the jabberwock READS TEXT INTO A SITUATION MODEL.

The reader was parsing-complete + grounding-strong but comprehension-SHALLOW: it
built a Kintsch TEXTBASE (grounded predications like `drop(john, glass)`) and
stopped. The SITUATION MODEL — the state of affairs the text denotes (the glass is
now on the floor, broken) — was never built, though the machinery for it existed
and was green in isolation (seeds/situation_model.json + seeds/event_reasoning.json).

This driver runs THE ONE WIRE (domains/situation_model_reader.py): read each
sentence with the HELD scoped collapse, then mint the sm_event / sm_entity nodes
the seeds' rules match on FROM the reader's predications, and let the EXISTING
run_rules fixpoint build the model. What comes out is the state the text NEVER
stated.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_reads_into_situation_model.py
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
from domains import situation_model_reader as smr

SEP = "=" * 92


class _Agent:
    def __init__(self, s, node):
        self.s, self.inner, self.agent = s, s._inner, node


def _fresh():
    s, node = boot_core()
    return _Agent(s, node)


def _fmt_state(st: dict) -> str:
    order = ["location", "holder", "fell", "on_floor", "broken", "worthless", "intact", "fragile"]
    keys = [k for k in order if k in st] + [k for k in st if k not in order and not k.endswith("_inferred")]
    return ", ".join("%s=%s" % (k, st[k]) for k in keys) or "(empty)"


def main():
    dl.warm_wordnet("en")

    print(SEP)
    print("THE WIRE — reading builds a SITUATION MODEL, not just a textbase")
    print(SEP)

    # ---- HEADLINE: textbase -> situation model ---------------------------------
    passage = "The glass is fragile. John dropped the glass."
    ag = _fresh()
    r = smr.read_into_situation_model(ag, passage)
    print("\n  passage: %r\n" % passage)
    print("  BEFORE (TEXTBASE — grounded predications, all the reader used to build):")
    for tb in r["textbase"]:
        print("    %-28s -> %s  [%s]" % (tb["sentence"], tb["predications"], tb["source"]))
    glass = r["situation_model"]["glass"]
    print("\n  AFTER (SITUATION MODEL — glass's state slice, built by the fixpoint):")
    print("    glass: %s" % _fmt_state(glass))
    print("\n  the state the text NEVER STATED (inferred by event_reasoning's 3 hops):")
    print("    glass is ON THE FLOOR   (%s)  <- fell -> on_floor" % (glass.get("on_floor") == 1))
    print("    glass is BROKEN         (%s)  <- on_floor + fragile -> broken" % (glass.get("broken") == 1))
    print("    glass is WORTHLESS      (%s)  <- broken -> worthless" % (glass.get("worthless") == 1))

    # ---- the bare sentence: honest residual ------------------------------------
    ag2 = _fresh()
    r2 = smr.read_into_situation_model(ag2, "John dropped the glass.")
    g2 = r2["situation_model"]["glass"]
    print("\n  the BARE sentence 'John dropped the glass.' (no stated fragility):")
    print("    glass: %s" % _fmt_state(g2))
    print("    -> on_floor is inferred; BROKEN is NOT (fragility is world knowledge,")
    print("       an honest RESIDUAL — the knowledge-codebook follow-on).")

    # ---- FIVE INDICES ----------------------------------------------------------
    print("\n" + SEP)
    print("  FIVE EVENT-INDEXING AXES (Zwaan & Radvansky) — filled from grounding")
    print(SEP)
    ag3 = _fresh()
    ing = smr.ingest_predication(ag3, ["entered", "she", "kitchen"], t=1)
    print("\n  'She entered the kitchen.'  (canon=%s, role frame=%s)" % (ing["canon"], ing["verb_frame"]))
    for k in ("protagonist", "entity", "space", "time", "causation", "intentionality"):
        v = ing["indices"].get(k)
        print("    %-15s %s" % (k, v if v is not None else "(RESIDUAL — not recoverable from the clause)"))

    ing2 = smr.ingest_predication(_fresh(), ["dropped", "john", "glass"], t=1)
    print("\n  'John dropped the glass.'   (canon=%s, role frame=%s)" % (ing2["canon"], ing2["verb_frame"]))
    for k in ("protagonist", "entity", "space", "time", "causation", "intentionality"):
        v = ing2["indices"].get(k)
        print("    %-15s %s" % (k, v if v is not None else "(RESIDUAL)"))

    # ---- MULTI-SENTENCE PERSISTENCE --------------------------------------------
    print("\n" + SEP)
    print("  MULTI-SENTENCE PERSISTENCE — the sm_entity survives the boundary")
    print(SEP)
    passage2 = "The cup is fragile. She entered the kitchen. She dropped the cup."
    ag4 = _fresh()
    r4 = smr.read_into_situation_model(ag4, passage2)
    print("\n  passage: %r\n" % passage2)
    print("    she: %s   <- location set in sentence 2, READ in sentence 3's frame" % _fmt_state(r4["situation_model"]["she"]))
    print("    cup: %s" % _fmt_state(r4["situation_model"]["cup"]))
    print("    (the textbase is per-clause; the situation model persists across sentences.)")

    # ---- CHANGE-OF-STATE IS A CLASS --------------------------------------------
    print("\n" + SEP)
    print("  CHANGE-OF-STATE IS A CLASS — join by adjacency; discriminative on non-COS")
    print(SEP)
    ag5 = _fresh()
    mem = smr.cos_membership(ag5, "smashed")
    print("\n  UNSEEN verb 'smashed' (not a seeded COS form):")
    print("    joins COS by adjacency: nearness=%.2f to %r -> canon=%s (via=%s)"
          % (mem["nearness"], mem["nearest"], mem["canon"], mem["via"]))
    ing5 = smr.ingest_predication(ag5, ["smashed", "john", "glass"], t=1)
    print("    triggers a transition: glass -> %s" % _fmt_state(smr.entity_state(ag5, "glass")))

    ag6 = _fresh()
    memL = smr.cos_membership(ag6, "likes")
    print("\n  NON-change-of-state verb 'likes':")
    print("    nearness=%.2f < threshold -> cos=%s (not a change of state)" % (memL["nearness"], memL["cos"]))
    ing6 = smr.ingest_predication(ag6, ["likes", "john", "glass"], t=1)
    print("    mints NO transition: glass -> %s  (%s)" % (_fmt_state(smr.entity_state(ag6, "glass")), ing6["kind"]))

    print("\n" + SEP)
    print("  The reader now COMPREHENDS, not just parses: it builds the described world.")
    print("  This is the SPINE. Follow-ons hang off it (NOT built here): inter-proposition")
    print("  inference against a knowledge codebook (fragility as world knowledge);")
    print("  coreference-into-entities (Centering resolver -> sm_entity); global monitoring")
    print("  (reading_review pointed at the situation model); ToM; scripts.")
    print(SEP)


if __name__ == "__main__":
    main()
