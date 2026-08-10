"""Load the agent with ALL seeds and have IT understand its LibriSpeech WER result and
reason the gaps. NO-DONKEY: the residual (its 100%-WER failure, structurally honest, NO
fix named) is registered as a held postulate; the agent's OWN harvested shape library
(158 domain seeds) fires over it via differentiate + synthesize_gaps; whatever it derives
IS its understanding of what it lacks. Reported VERBATIM, then ranked by its own
compression selector.

Run: python -m scripts.agent_reasons_wer
"""
from __future__ import annotations
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate
from domains.arc3_full_seed import _discover_substrate_seed_installers
from domains.phonology import install_phonology
from domains.speech_science import install_speech_science
from domains.concept_expansions import install_all_concept_expansions
from domains.code_authoring import _install_concept
from domains.implication_harvester import harvest_shapes_combined
from domains.order_n_postulates import synthesize_gaps, differentiate
from domains import breadth_audit

NAME = "librispeech_wer_total_failure"
DEFN = (
    "The agent recognises speech by acquiring one acoustic SIGN per spoken word and "
    "grounding that sign to the word; at test it transcribes by matching the incoming "
    "audio to its stored signs and voting for the grounded words. Measured on real "
    "continuous read sentences spoken by people it never trained on, it transcribed "
    "EVERY test utterance to NOTHING — it produced no words at all, so its word error "
    "rate was total (100%). The structural facts behind the empty output: (1) its signs "
    "were each formed from a particular training speaker's audio for a particular whole "
    "word, and a new speaker's audio for the same word produces a sign that matches none "
    "of the stored ones, so no vote ever crosses threshold; (2) the test sentences "
    "contain many words the agent never heard during its small training, and it has no "
    "stored sign for a word it has never encountered; (3) in the sentence the words are "
    "run together with no silence between them and spoken at a continuous rate, but the "
    "agent only ever stored whole-word signs from isolated training items; (4) it holds "
    "no model of which words tend to follow which, so it cannot use the surrounding "
    "words to recover a doubtful one; (5) it has no way to produce a word as a sequence "
    "of smaller recurring parts, so every word is an all-or-nothing whole it either has "
    "stored or cannot say.")


def _build_full_mind():
    s = Substrate()
    ok = 0
    for _name, fn in _discover_substrate_seed_installers():
        try:
            fn(s); ok += 1
        except Exception:
            pass
    for fn in (install_phonology, install_speech_science, install_all_concept_expansions):
        try:
            fn(s)
        except Exception:
            pass
    return s, ok


def main():
    print("=" * 84, flush=True)
    print("AGENT UNDERSTANDS ITS WER RESULT + REASONS THE GAPS (all seeds, live, verbatim)",
          flush=True)
    print("=" * 84, flush=True)
    s, ok = _build_full_mind()
    print(f"\n[boot] {ok} domain seeds installed; held Concepts = {len(s.nodes('Concept'))}",
          flush=True)
    mt = s.add_node("Microtheory", {"name": "wer_failure_paradigm", "origin": "reasons_wer"})
    try:
        s.add_production({"src": {"type": "Microtheory", "var": "a"},
                          "edge_type": "has_concept",
                          "tgt": {"type": "Concept", "var": "b"},
                          "provenance": "wer:has_concept"})
    except Exception:
        pass
    _install_concept(s, mt, NAME, DEFN)
    lib = harvest_shapes_combined(s)
    print(f"[harvest] shape library = {len(lib)}", flush=True)
    print("\n[the agent's own statement of its failure]\n  ", DEFN, flush=True)

    print("\n" + "=" * 84, flush=True)
    print("[order-1] the agent's shapes that FIRE on its WER failure (what it lacks):",
          flush=True)
    print("=" * 84, flush=True)
    for im in differentiate(DEFN, shapes=lib):
        print(f"\n   via_shape  : {im['via_shape']}  (concept '{im.get('source_concept')}')",
              flush=True)
        print(f"   names      : {im['name_keys']}", flush=True)
        print(f"   the gap    : {im['consequence']}", flush=True)

    print("\n" + "=" * 84, flush=True)
    print("[synthesize_gaps] the agent's full derivation of what it needs (order<=3):",
          flush=True)
    print("=" * 84, flush=True)
    gaps = synthesize_gaps(s, NAME, shapes=lib, record=False, prune=False, max_order=3)
    print(f"  derived gaps: {len(gaps)}\n", flush=True)
    for g in sorted(gaps, key=lambda g: -g["order"]):
        roles = breadth_audit.classify_shape_role(breadth_audit._gap_to_shapelike(g))
        print(f"  [{','.join(roles) or 'gap':16}] order-{g['order']} {g['capability_keys']}",
              flush=True)
        print(f"     via {g['via_shapes']}: {g['gap']}", flush=True)


if __name__ == "__main__":
    main()
