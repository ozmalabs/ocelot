"""implication_harvester — the agent harvests its OWN implication-shapes.

Locks the closure of order-N gap-synthesis: the implication-shapes the operator
transfers come from the agent's OWN concepts (domains/implication_harvester),
not a hand-curated stencil. The load-bearing property is SELF-SUFFICIENCY — with
the stencil OFF, the harvested shapes still derive the known gaps (LPC,
cross-speaker clustering, word-scale chunking) — plus that the selector still
PRUNES already-solved postulates.
"""
from __future__ import annotations

import pytest

srs = pytest.importorskip("substrate_rs")

from substrate_rs import Substrate
from domains.stt_pipeline import STTPipeline, STTParams
from domains.phonology import install_phonology
from domains.speech_development import install_speech_development
from domains.speech_cortex import SpeechCortex
from domains.speech_science import install_speech_science
from substrate.boot_all import load_one_seed
from domains.concept_expansions import install_all_concept_expansions
from domains.implication_harvester import harvest_shapes, harvest_report
from domains.order_n_postulates import (synthesize_gaps, synthesize_over_all,
                                        harvest_postulates)


@pytest.fixture(scope="module")
def agent():
    sub = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=8000))
    pipe.attach(sub)
    pipe._ensure_audio_pipeline(sub)
    install_phonology(sub)
    install_speech_development(sub)
    SpeechCortex(sub, lexicon_name="stt", tick_period_ms=99999).install()
    install_speech_science(sub)
    load_one_seed(sub, "mathematics")
    load_one_seed(sub, "engineering")
    load_one_seed(sub, "machine_learning")
    install_all_concept_expansions(sub)
    return sub


def _caps(syn):
    return {frozenset(k.lower() for k in g["capability_keys"])
            for gg in syn.values() for g in gg}


def test_harvest_draws_shapes_from_many_concepts_and_domains(agent):
    rep = harvest_report(agent)
    # genuine breadth: shapes from many concepts across many domains
    assert rep["n_shapes"] >= 5
    assert rep["n_donor_concepts"] >= 15
    assert rep["n_domains"] >= 4
    # the named sources are GENUINE structural donors (not noise) for the
    # load-bearing kinds.
    by_kind = {s["kind"]: s["source_concept"] for s in rep["shapes"]}
    assert "filter" in by_kind.get("parametric_allpole", "").lower()
    assert "unsupervised" in by_kind.get("latent_structure", "").lower()


def test_harvest_excludes_the_speech_science_postulates(agent):
    # shapes must come from the agent's OTHER breadth, not from the SPEECH_SCIENCE
    # postulates being differentiated. harvest_postulates' default scope is now
    # full-breadth (every Mt's concepts) — scope it to speech_science, the
    # postulates this harvester differentiates, or the exclusion is vacuous
    # (every concept would be in `posts`).
    posts = {n for _, n, _ in harvest_postulates(agent, "speech_science")}
    for s in harvest_shapes(agent):
        assert s["source_concept"] not in posts


def test_self_sufficiency_harvested_only_reproduces_known_gaps(agent):
    # THE KEY TEST: stencil OFF, shapes harvested from the agent's own concepts.
    # This tests the HARVESTER's self-sufficiency = does the transfer DERIVE the
    # known capabilities? (prune=False so it is measured independent of whether the
    # agent has since IMPLEMENTED a capability — e.g. LPC, which the iter-2 loop
    # built in sound_graph.py and the selector therefore correctly no longer flags
    # as an OPEN gap. Openness is tested separately, below.)
    caps = _caps(synthesize_over_all(agent, record=False, shapes="harvested",
                                     prune=False))
    known = {
        "lpc": frozenset(["all-pole", "levinson", "lpc-formant",
                          "autoregressive"]),
        "clustering": frozenset(["unsupervised-clustering",
                                 "cross-speaker-clustering", "cross-speaker"]),
        "chunking": frozenset(["transitional probability", "word-scale chunking",
                               "statistical segmentation", "n-gram boundary"]),
    }
    for name, key in known.items():
        assert key in caps, f"harvested shapes failed to derive {name}"


def test_lpc_gap_provenance_names_a_source_concept(agent):
    # DERIVATION test (prune=False): the all-pole shape must TRANSFER onto
    # source_filter_theory and name its source concept. (Openness is separate: the
    # agent has since implemented LPC in sound_graph.py, so with prune=True it is
    # correctly no longer an OPEN gap — but the transfer that DERIVES it still
    # works, which is what self-sufficiency means.)
    gg = synthesize_gaps(agent, "source_filter_theory", shapes="harvested",
                         record=False, prune=False)
    lpc = next(g for g in gg
               if "all-pole" in [k.lower() for k in g["capability_keys"]])
    # the gap carries the agent's OWN concept that donated the shape.
    assert lpc["source_concepts"], "no source concept recorded for the LPC gap"
    assert any("filter" in c.lower() for c in lpc["source_concepts"])


def test_lpc_is_no_longer_an_open_gap_because_implemented(agent):
    # The flip side, made explicit: with the selector ON (prune=True, the default),
    # LPC is NOT an open gap — the agent built the all-pole front-end in
    # sound_graph.py (iter-2), so the selector correctly prunes it. This guards
    # against re-introducing a faked "LPC is still a gap" claim.
    gg = synthesize_gaps(agent, "source_filter_theory", shapes="harvested",
                         record=False)  # prune=True default
    assert not any("all-pole" in [k.lower() for k in g["capability_keys"]]
                   for g in gg), "LPC should be pruned as already-implemented"


def test_allpole_shape_matches_by_resonant_filter_kind_not_keyword(agent):
    # GENERALITY guard: the all-pole shape transfers onto ANY resonant-linear-filter
    # postulate (a structural-KIND match, resonance<->pole), not just one named one,
    # and does NOT spuriously fire on unrelated postulates.
    from domains.order_n_postulates import differentiate, _resolve_shapes
    posts = {n: t for _, n, t in harvest_postulates(agent)}
    shapes, _ = _resolve_shapes(agent, "harvested")

    def fires_allpole(name):
        return any("parametric_allpole" in i["via_shape"]
                   for i in differentiate(posts.get(name, ""), shapes=shapes))

    # fires on the resonant-filter postulates (more than one => not a hardwire)
    assert fires_allpole("source_filter_theory")
    assert fires_allpole("vocal_tract_resonance_formants")
    # does NOT fire on non-filter postulates
    assert not fires_allpole("statistical_learning")
    assert not fires_allpole("lexical_access")


def test_selector_still_prunes_solved_postulates_under_harvest(agent):
    # the richer library must NOT make the selector flag already-solved gaps.
    held = {n for _, n, _ in harvest_postulates(agent)}
    for p in ("coarticulation", "lack_of_invariance", "speaker_normalization"):
        if p in held:
            assert synthesize_gaps(agent, p, shapes="harvested",
                                   record=False) == []


def test_harvested_recall_matches_stencil(agent):
    # harvested must reproduce every distinct capability the hand stencil did
    # (recall >= stencil) — the stencil is no longer load-bearing.
    caps_h = _caps(synthesize_over_all(agent, record=False, shapes="harvested"))
    caps_s = _caps(synthesize_over_all(agent, record=False, shapes="stencil"))
    assert caps_s.issubset(caps_h)
