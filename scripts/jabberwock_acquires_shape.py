"""jabberwock_acquires_shape — the agent ACQUIRES the missing re_represent shape
from its WORLD, then re-derives the perceptual frame (iter-21).

The deepest autopoietic close: diagnose -> acquire -> harvest -> derive.

iter-20 (scripts/jabberwock_breadth_audit.py) had the agent diagnose that its entire
SUBSTRATE-CHANGING side is EMPTY: the role `re_represent` holds ZERO shapes. Its
gloss is the agent's statement of the missing shape-KIND:

    "describe the object by the RELATIONS among its parts — a configuration /
     structure / graph, an invariant-by-construction representation, not its
     absolute values"

That gloss SELECTS a domain to acquire from the world: the general mathematical
theory of characterising an object by the invariant relations among its parts —
INVARIANT THEORY and Klein's ERLANGEN PROGRAM. domains/invariant_representation.py
INGESTS that GENERAL domain (Concepts + Rules in the agent's exact seed format,
cited from Wikipedia; nothing speech, nothing for the perceptual frame).

This script:
  (A) installs the SAME agent iter-19/20 built, PLUS the acquired domain;
  (B) runs the agent's OWN harvester and reports the shape it abstracts VERBATIM;
  (C) re-runs the breadth-audit and reports whether re_represent is now non-empty;
  (D) re-runs the iter-19 perceptual derivation over the SAME honest frame and
      reports whether synthesize_gaps now surfaces a relational representation.

NO-DONKEY: this script does not author the shape or the representation. It installs
general domain knowledge and runs the agent's mechanisms. The harvested shape and
the derivation are the agent's output, reported verbatim.

Run:  python scripts/jabberwock_acquires_shape.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate

from domains.stt_pipeline import STTPipeline, STTParams
from domains.phonology import install_phonology
from domains.speech_development import install_speech_development
from domains.speech_cortex import SpeechCortex
from domains.speech_science import install_speech_science
from domains.mathematics import install_mathematics_seed
from domains.engineering import install_engineering_seed
from domains.machine_learning import install_machine_learning_seed
from domains.concept_expansions import install_all_concept_expansions
from domains.invariant_representation import install_invariant_representation_seed
from domains.code_authoring import _install_concept
from domains import breadth_audit
from domains.implication_harvester import harvest_shapes_combined
from domains.order_n_postulates import synthesize_gaps


_FRAME_TEXT = (
    "Speech recognition represents each unit by its SURFACE acoustic features "
    "— the per-frame gammatone / cepstral VALUES measured directly off the "
    "waveform — and matches those raw feature values against stored exemplars, "
    "voting for the nearest. These surface VALUES depend on the speaker and the "
    "accent: a change of talker or accent SHIFTS and SCALES the measured "
    "feature values even when the spoken word is the same. The values vary with "
    "the talker; they are NON-INVARIANT to the speaker. With correct word "
    "boundaries this surface representation still CONFUSES instances of the "
    "same word spoken by different talkers, because the raw values it compares "
    "are not the same across talkers.")


def _build(with_acquired: bool):
    sub = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=8000))
    pipe.attach(sub)
    pipe._ensure_audio_pipeline(sub)
    install_phonology(sub)
    install_speech_development(sub)
    SpeechCortex(sub, lexicon_name="stt", tick_period_ms=99999).install()
    install_speech_science(sub)
    install_mathematics_seed(sub)
    install_engineering_seed(sub)
    install_machine_learning_seed(sub)
    install_all_concept_expansions(sub)
    if with_acquired:
        install_invariant_representation_seed(sub)
    return sub


def _register_frame(sub):
    mt = sub.add_node("Microtheory", {
        "name": "perceptual_representation_paradigm",
        "description": "the agent's current frame for how it REPRESENTS a "
                       "perceptual unit, registered as a higher-order postulate",
        "origin": "jabberwock_acquires_shape"})
    try:
        sub.add_production({
            "src": {"type": "Microtheory", "var": "a"},
            "edge_type": "has_concept",
            "tgt": {"type": "Concept", "var": "b"},
            "provenance": "jabberwock_acquires_shape:has_concept"})
    except Exception:
        pass
    _install_concept(sub, mt, "surface_feature_representation_frame", _FRAME_TEXT)
    return mt


def _show_gap(g):
    print(f"    => GAP (order-{g['order']}): keys={g['capability_keys']}")
    print(f"       via_shapes={g['via_shapes']}  domains={g['source_domains']}")
    print(f"       source_concepts={g.get('source_concepts')}")


def main():
    print("=" * 78)
    print("STEP 4 — HARVEST: run the agent's OWN harvester over the enriched breadth")
    print("=" * 78)
    sub = _build(with_acquired=True)
    shapes = harvest_shapes_combined(sub)
    print(f"  shapes harvested: {len(shapes)}")
    found = []
    for sh in shapes:
        if "re_represent" in breadth_audit.classify_shape_role(sh):
            found.append(sh)
    if not found:
        print("  >>> the harvester abstracted NO re_represent shape (harvester limit)")
    for sh in found:
        print("\n  RE_REPRESENT SHAPE (verbatim, the agent's harvest):")
        print(f"    name        : {sh.get('name')}")
        print(f"    kind        : {sh.get('kind')}")
        print(f"    domain      : {sh.get('domain')}")
        print(f"    match_mode  : {sh.get('match_mode')}")
        print(f"    consequence : {sh.get('consequence')}")
        print(f"    match_keys  : {sh.get('match_keys')}")
        print(f"    name_keys   : {sh.get('name_keys')}")
        print(f"    match_patterns: {sh.get('match_patterns')}")

    print("\n" + "=" * 78)
    print("STEP 5 — VERIFY breadth: re-run the audit (is re_represent now non-empty?)")
    print("=" * 78)
    _register_frame(sub)
    audit = breadth_audit.run_audit(
        sub, frames=["surface_feature_representation_frame"])
    lib = audit["library_role_distribution"]
    for role, info in lib["roles"].items():
        n = lib["role_counts"].get(role, 0)
        flag = "" if n else "   <<< EMPTY"
        print(f"    [{info['side']:8}] {role:14} = {n:>4} shapes{flag}")
    print(f"\n  side totals: {lib['side_counts']}")
    print(f"  empty roles: {lib['empty_roles']}")
    print(f"  empty sides: {lib['empty_sides']}")

    print("\n" + "=" * 78)
    print("STEP 6 — DERIVE (the test): synthesize_gaps over the SAME honest frame")
    print("=" * 78)
    for label in ("WITHOUT acquired domain (iter-19 baseline)", "WITH acquired domain"):
        with_acq = label.startswith("WITH ")
        s2 = _build(with_acquired=with_acq)
        _register_frame(s2)
        gaps = synthesize_gaps(s2, "surface_feature_representation_frame",
                               shapes="harvested", record=False, prune=False,
                               max_order=3)
        print(f"\n  --- {label} ---")
        print(f"  n gaps surfaced: {len(gaps)}")
        relational = [g for g in gaps
                      if breadth_audit.classify_shape_role(
                          breadth_audit._gap_to_shapelike(g))]
        for g in gaps:
            roles = breadth_audit.classify_shape_role(
                breadth_audit._gap_to_shapelike(g))
            print(f"    [{','.join(roles) or 'unclassified':12}] ", end="")
            _show_gap(g)
        change_side = [g for g in gaps
                       if "re_represent" in breadth_audit.classify_shape_role(
                           breadth_audit._gap_to_shapelike(g))]
        print(f"  >>> change-side (re_represent) gaps surfaced: {len(change_side)}")


if __name__ == "__main__":
    main()
