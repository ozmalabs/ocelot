#!/usr/bin/env python3
"""jabberwock_infers -- STEP 3: THE JABBERWOCK GENERATES THE UNSTATED INFERENCE.

situation_model_reader (step 2) builds a situation model but only from what
the text STATES: bare "John dropped the glass." infers `on_floor` (fell's own
consequence) but never `broken`, because event_reasoning.json's `infer_broken`
rule also needs `fragile`, and the bare sentence never states it. Honest
residual, documented in tests/test_situation_model_wire.py.

domains/inference_generation.py closes it: a stalled rule precondition (or a
definite NP with no discourse antecedent) is a GAP; the gap is DECODED against
a small knowledge codebook (seeds/inference_knowledge.json) by the SAME
ShapeDecode collapse reading_collapse.py uses for syntax; the winning schema's
own `supplies` data (never a Python pick) is minted, and the EXISTING
run_rules fixpoint (situation_model_reader.ingest_predication, unchanged)
completes the chain.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_infers.py
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
from domains import inference_generation as ig

SEP = "=" * 92


class _Agent:
    def __init__(self, s, node):
        self.s, self.inner, self.agent = s, s._inner, node


def _fresh():
    s, node = boot_core()
    return _Agent(s, node)


def _fmt(st: dict) -> str:
    order = ["location", "holder", "fell", "on_floor", "fragile", "broken", "made_of_glass",
             "worthless", "intact"]
    keys = [k for k in order if k in st] + [k for k in st if k not in order and not k.endswith("_inferred")]
    return ", ".join("%s=%s" % (k, st[k]) for k in keys) or "(empty)"


def main():
    dl.warm_wordnet("en")

    print(SEP)
    print("STEP 3 -- GENERATE THE UNSTATED INFERENCE (gap-decode-mint, graph-native)")
    print(SEP)

    # ---- HEADLINE: closes the spine's own documented residual -----------------
    text = "John dropped the glass."
    ag = _fresh()
    r = ig.read_and_infer(ag, text)
    print("\n  passage: %r\n" % text)
    print("  BEFORE (situation_model_reader ALONE -- the spine, unchanged):")
    print("    glass: %s" % _fmt(r["before_situation_model"]["glass"]))
    print("    -> on_floor is inferred; BROKEN is NOT -- fragility is world knowledge,")
    print("       an honest residual (tests/test_situation_model_wire.py's own words).")

    b = r["blocking"][0]
    print("\n  GAP DETECTED: rule %r needs %r on %r (on_floor already holds, fragile does not)"
          % (b["gap"]["rule"], b["gap"]["need_attr"], b["gap"]["entity"]))
    print("  DECODE: winning schema = %r (ShapeDecode over seeds/inference_knowledge.json)"
          % b["schema"])
    print("  MINT: supplies=%s -> situation_model_reader.ingest_predication (unchanged, re-runs "
          "the fixpoint)" % b["supplies"])

    print("\n  AFTER (the supplied fragility cascaded through the UNCHANGED fixpoint):")
    print("    glass: %s" % _fmt(r["situation_model"]["glass"]))
    print("    glass is BROKEN    (%s)  <- on_floor + SUPPLIED fragile -> broken"
          % (r["situation_model"]["glass"].get("broken") == 1))
    print("    glass is WORTHLESS (%s)  <- broken -> worthless"
          % (r["situation_model"]["glass"].get("worthless") == 1))

    # ---- BRIDGING ---------------------------------------------------------------
    print("\n" + SEP)
    print("  BRIDGING -- a definite with NO antecedent, no lexical cue")
    print(SEP)
    text2 = "We checked the picnic supplies. The beer was warm."
    ag2 = _fresh()
    r2 = ig.read_and_infer(ag2, text2)
    print("\n  passage: %r\n" % text2)
    br = r2["bridging"][0]
    print("  GAP: %r is a definite NP with no resident antecedent (no cue word used)" % br["gap"]["entity"])
    print("  DECODE: winning schema = %r  ->  supplies=%s" % (br["schema"], br["supplies"]))
    print("  MINT: part_of(%s, %s)" % (br["gap"]["entity"], br["supplies"]["object"]))
    print("  situation model: beer -> %s" % _fmt(r2["situation_model"]["beer"]))

    # ---- STANDARD OF COHERENCE ---------------------------------------------------
    print("\n" + SEP)
    print("  STANDARD OF COHERENCE -- one tunable node flips elaborative inference")
    print(SEP)
    ag3 = _fresh()
    r3 = ig.read_and_infer(ag3, text)
    print("\n  SHALLOW (minimalist, McKoon & Ratcliff -- the seed default):")
    print("    blocking (fragile) fired: %s" % any(x["minted"] for x in r3["blocking"]))
    elab3 = [e for e in r3["elaborative"] if e["schema"] == "glassware_composition"][0]
    print("    elaborative (made_of_glass) fired: %s  (%s)" % (elab3["minted"], elab3["reason"]))

    ag4 = _fresh()
    ig.set_coherence_depth(ag4, "deep")
    r4 = ig.read_and_infer(ag4, text)
    print("\n  DEEP (constructionist, Graesser) -- SAME passage, ONE node flipped:")
    print("    blocking (fragile) fired: %s" % any(x["minted"] for x in r4["blocking"]))
    elab4 = [e for e in r4["elaborative"] if e["schema"] == "glassware_composition"][0]
    print("    elaborative (made_of_glass) fired: %s" % elab4["minted"])
    print("    glass: %s" % _fmt(r4["situation_model"]["glass"]))

    # ---- DISCRIMINATIVE -----------------------------------------------------------
    print("\n" + SEP)
    print("  DISCRIMINATIVE -- no over-inference")
    print(SEP)
    ag5 = _fresh()
    r5 = ig.read_and_infer(ag5, "John dropped the ball.")
    print("\n  'John dropped the ball.' -- gap IS detected (ball needs fragile) but the")
    print("  codebook does NOT know a ball is fragile -- honest null, nothing minted:")
    print("    minted=%s  schema=%s" % (r5["blocking"][0]["minted"], r5["blocking"][0]["schema"]))
    print("    ball: %s" % _fmt(r5["situation_model"]["ball"]))

    ag6 = _fresh()
    r6 = ig.read_and_infer(ag6, "The glass is fragile. John dropped the glass.")
    print("\n  'The glass is fragile. John dropped the glass.' -- fully STATED, no gap at all:")
    print("    gaps detected: %d" % len(r6["blocking"]))

    print("\n" + SEP)
    print("  Mechanism: gap-detect (graph read) -> ShapeDecode collapse (the decision) ->")
    print("  mint (mechanical) -> re-run the existing fixpoint. Knowledge is FINITE and")
    print("  seeded (seeds/inference_knowledge.json); the MECHANISM is general.")
    print(SEP)


if __name__ == "__main__":
    main()
