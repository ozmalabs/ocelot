"""jabberwock_breadth_audit — the AGENT audits its OWN breadth for missing
shape-KINDS, mechanically (iter-20).

iter-19 (scripts/jabberwock_perceptual_shape.py) showed the gap-finder is blind to
shapes it LACKS: over the perceptual frame the operator derived only NORMALIZATIONS
and could not derive a relational / representation-change shape — and a HUMAN
sub-agent had to read the 181-shape library by hand to find that absence. iter-20
turns the gap-finder on the TOOLBOX: domains/breadth_audit.py classifies the agent's
own harvested shapes by structural ROLE (the preserve/change operation taxonomy),
flags the EMPTY roles, and measures whether the perceptual frame's gaps CONVERGE on
one side of that partition.

This script WIRES the same agent iter-19 built + the perceptual frame, RUNS
breadth_audit.run_audit, and reports its output VERBATIM. The audit does NOT contain
the answer (no test for "is the relational shape present"); it computes a role
distribution and reports whichever roles are empty.

Run:  python scripts/jabberwock_breadth_audit.py
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
from domains.code_authoring import _install_concept
from domains import breadth_audit


def _build():
    """The SAME agent iter-19 built — its speech impl + speech science + its
    cross-domain breadth (the source of the harvested implication-shapes)."""
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
    return sub


def _register_perceptual_frame(sub):
    """The SAME honest perceptual frame iter-19 registered (no answer seeded — the
    words shape/relational/structure/whole-unit/transform-invariant do not appear)."""
    mt = sub.add_node("Microtheory", {
        "name": "perceptual_representation_paradigm",
        "description": "the agent's current frame for how it REPRESENTS a "
                       "perceptual unit, registered as a higher-order postulate",
        "origin": "jabberwock_breadth_audit"})
    try:
        sub.add_production({
            "src": {"type": "Microtheory", "var": "a"},
            "edge_type": "has_concept",
            "tgt": {"type": "Concept", "var": "b"},
            "provenance": "jabberwock_breadth_audit:has_concept"})
    except Exception:
        pass
    _install_concept(
        sub, mt, "surface_feature_representation_frame",
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
    return mt


def main():
    sub = _build()
    _register_perceptual_frame(sub)

    audit = breadth_audit.run_audit(
        sub, frames=["surface_feature_representation_frame"])

    lib = audit["library_role_distribution"]
    print("=" * 78)
    print("BREADTH AUDIT (1) — ROLE DISTRIBUTION over the agent's OWN shape-library")
    print("=" * 78)
    print(f"  shapes harvested: {lib['n_shapes']}   "
          f"unclassified: {lib['n_unclassified']}")
    print("\n  The structural-ROLE taxonomy (preserve/change operation kinds):")
    for role, info in lib["roles"].items():
        n = lib["role_counts"].get(role, 0)
        flag = "" if n else "   <<< EMPTY (breadth gap)"
        print(f"    [{info['side']:8}] {role:14} = {n:>4} shapes{flag}")
        print(f"                 ({info['gloss']})")
    print("\n  side totals:")
    for side, n in sorted(lib["side_counts"].items()):
        print(f"    {side:10} = {n}")
    for side in lib["empty_sides"]:
        print(f"    {side:10} = 0   <<< ENTIRE SIDE EMPTY")
    print(f"\n  >>> EMPTY ROLES (breadth gaps): {lib['empty_roles']}")
    print(f"  >>> EMPTY SIDES               : {lib['empty_sides']}")

    print("\n" + "=" * 78)
    print("BREADTH AUDIT (2) — FRAME CONVERGENCE over the perceptual frame")
    print("=" * 78)
    for fr, c in audit["frame_convergence"].items():
        print(f"  frame: {fr}")
        print(f"    gaps surfaced        : {c['n_gaps']}")
        print(f"    distinct roles       : {c['n_distinct_roles']}  "
              f"({c['roles_present']})")
        print(f"    distinct sides       : {c['n_distinct_sides']}  "
              f"({c['sides_present']})")
        print(f"    role_counts          : {c['role_counts']}")
        if c["converges"]:
            print(f"    >>> BREADTH-LIMITED: all gaps converge on side "
                  f"'{c['converges_on_side']}' — the complementary side is "
                  f"UNREACHABLE with the current library.")
        else:
            print(f"    (not converged)")

    print("\n" + "=" * 78)
    print("BREADTH AUDIT (3) — DOMAIN COVERAGE")
    print("=" * 78)
    dom = audit["domain_coverage"]
    print(f"  concept domains: {dom['n_concept_domains']}   "
          f"shape domains: {dom['n_shape_domains']}")
    print(f"  concept-rich domains contributing NO shape: "
          f"{dom['concept_domains_with_no_shape']}")

    print("\n" + "=" * 78)
    print("WHAT THE AUDIT SURFACED (mechanical, no answer fed)")
    print("=" * 78)
    bg = audit["breadth_gaps"]
    print(f"  empty roles            : {bg['empty_roles']}")
    print(f"  empty sides            : {bg['empty_sides']}")
    print(f"  breadth-limited frames : {bg['breadth_limited_frames']}")


if __name__ == "__main__":
    main()
