"""audio_coding_theory + the audio decomposition packs."""
from __future__ import annotations

import pytest
from substrate_rs import _native


_NODE_TYPES = (
    "Microtheory", "Concept", "Rule",
    "DesignPattern", "ProgrammingLanguage", "CodeTarget",
    "DesignExclusion", "LanguageExclusion", "LanguageScoringConfig",
    "CodeWritingCortex", "CodeAuthoringRoot", "Reflex",
    "ReplacementTarget", "CodeDraft", "ValidationResult",
    "CodeInstallation",
)
_EDGE_TYPES = (
    "genlMt", "has_concept", "has_rule", "owns_microtheory",
    "owns_root", "has_reflex", "current_target", "has_draft",
    "validated_by", "installed_as", "authored_in", "uses_pattern",
    "subClassOf", "in_category", "decomposes",
)


def _fresh_substrate():
    s = _native.Substrate()
    for src_t in _NODE_TYPES:
        for tgt_t in _NODE_TYPES:
            for et in _EDGE_TYPES:
                s.add_production({
                    "src": {"type": src_t, "var": "src"},
                    "edge_type": et, "tgt": {"type": tgt_t, "var": "tgt"},
                    "where": None,
                    "weight": {"type": "Lit", "value": 1.0},
                    "provenance": "test:open",
                })
    s.add_node("Microtheory", {"name": "compiler_theory"})
    return s


def test_audio_coding_theory_installs_with_genlmt():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "audio_coding_theory")
    assert mt is not None
    assert s.node(mt)["attrs"]["name"] == "audio_coding_theory"
    parents = {s.node(p)["attrs"]["name"]
               for p in s.neighbours(mt, "genlMt")}
    assert "compiler_theory" in parents


def test_audio_coding_theory_carries_foundations():
    """Sampling, Nyquist, ATH, masking, critical bands — the
    foundations of psychoacoustic audio coding."""
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "audio_coding_theory")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("sampling_rate", "nyquist_theorem", "aliasing",
                     "PCM_pulse_code_modulation", "psychoacoustic_model",
                     "critical_band", "absolute_threshold_of_hearing",
                     "frequency_masking", "temporal_masking",
                     "JND_audio"):
        assert required in names, f"missing foundation {required!r}"


def test_audio_coding_theory_carries_codecs():
    """All the major codec families covered as standards."""
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "audio_coding_theory")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("MP3", "AAC", "HE_AAC", "HE_AAC_v2", "xHE_AAC",
                     "Vorbis", "Opus", "AC3", "E_AC3", "DTS",
                     "FLAC", "ALAC", "LC3", "LDAC", "aptX",
                     "G_711", "G_722", "G_729",
                     "AMR_NB", "AMR_WB", "EVS",
                     "SoundStream", "EnCodec", "Lyra", "DAC_descript",
                     "audio_diffusion_codec"):
        assert required in names, f"missing codec {required!r}"


def test_audio_coding_theory_carries_mechanisms():
    """Core mechanisms: MDCT, polyphase, LPC, CELP, joint stereo, TNS,
    SBR, parametric stereo, etc."""
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "audio_coding_theory")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("MDCT", "polyphase_filterbank", "subband_coding",
                     "bit_allocation_audio",
                     "linear_predictive_coding", "CELP", "ACELP",
                     "vector_quantisation", "joint_stereo_MS",
                     "intensity_stereo", "temporal_noise_shaping",
                     "spectral_band_replication", "parametric_stereo",
                     "window_switching", "pre_echo_control",
                     "noise_substitution", "huffman_coding_audio"):
        assert required in names


def test_audio_coding_theory_carries_rules():
    """Derivation rules link the concepts and back to compiler_theory."""
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "audio_coding_theory")
    names = {s.node(r)["attrs"]["name"]
             for r in s.neighbours(mt, "has_rule")}
    for required in ("psychoacoustic_masking_enables_perceptual_compression",
                     "nyquist_bounds_recoverable_frequency_range",
                     "linear_prediction_models_speech_autocorrelation",
                     "mdct_perfect_reconstruction_at_50_percent_overlap",
                     "window_switching_handles_transients",
                     "joint_stereo_exploits_channel_correlation",
                     "opus_unifies_speech_and_music_via_mode_switching",
                     "neural_codecs_extend_audio_to_very_low_bitrates",
                     "lossless_compression_ratio_limited_by_signal_entropy"):
        assert required in names


def test_audio_coding_theory_rules_carry_soundness_category():
    """Each rule's soundness_category links to compiler_theory."""
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "audio_coding_theory")
    valid = {"denotational_equivalence", "algebraic_law",
             "extensional_equivalence", "cost_equivalence",
             "referential_transparency"}
    n_with_cat = 0
    for r in s.neighbours(mt, "has_rule"):
        if s.node(r)["attrs"].get("soundness_category") in valid:
            n_with_cat += 1
    assert n_with_cat >= 14


def test_audio_decomposition_packs_load():
    """The 8 audio-specific expansion packs are picked up."""
    from substrate.boot_all import load_one_seed
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    mt = load_one_seed(s, "audio_coding_theory")
    ids = install_all_concept_expansions(s)
    for required in ("mdct_decomposition",
                     "mp3_internals_decomposition",
                     "aac_internals_decomposition",
                     "opus_codec_decomposition",
                     "celp_decomposition",
                     "flac_decomposition",
                     "sbr_decomposition",
                     "psychoacoustic_model_decomposition",
                     "neural_audio_codec_decomposition",
                     "spatial_audio_decomposition"):
        assert required in ids, f"audio pack {required!r} not loaded"


def test_audio_pack_sub_mechanisms_mount_correctly():
    """Sample sub-mechanisms from each audio pack are reachable
    under audio_coding_theory."""
    from substrate.boot_all import load_one_seed
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    mt = load_one_seed(s, "audio_coding_theory")
    install_all_concept_expansions(s)
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    # MDCT pack
    for n in ("dct_iv_basis", "fifty_percent_overlap",
              "time_domain_aliasing_cancellation", "sine_window"):
        assert n in names
    # MP3 pack
    for n in ("mp3_frame_structure", "polyphase_32_band",
              "mp3_bit_reservoir", "mp3_huffman_tables"):
        assert n in names
    # AAC pack
    for n in ("aac_profile_lc", "aac_tns_inverse_filter",
              "aac_noise_substitution_pns"):
        assert n in names
    # Opus pack
    for n in ("silk_layer", "celt_layer", "hybrid_mode_switching",
              "fec_forward_error_correction"):
        assert n in names
    # CELP pack
    for n in ("lpc_short_term_filter", "lsf_line_spectral_frequencies",
              "adaptive_codebook_pitch", "analysis_by_synthesis"):
        assert n in names
    # FLAC pack
    for n in ("flac_rice_coding", "flac_lpc_predictors",
              "flac_channel_decorrelation"):
        assert n in names
    # SBR pack
    for n in ("qmf_filterbank", "patching_high_from_low",
              "envelope_adjustment"):
        assert n in names
    # Psychoacoustic model pack
    for n in ("ath_curve", "bark_scale", "spreading_function",
              "global_masking_threshold", "signal_to_mask_ratio"):
        assert n in names
    # Neural audio codec pack
    for n in ("convolutional_encoder", "residual_vector_quantisation",
              "adversarial_loss", "discrete_token_stream"):
        assert n in names
    # Spatial audio pack
    for n in ("channel_based_5_1", "dolby_atmos_objects",
              "ambisonics_first_order", "binaural_rendering"):
        assert n in names


def test_total_audio_concept_count():
    """Sanity: foundation + 10 audio packs ≈ 70 base + ~100 pack = 170+."""
    from substrate.boot_all import load_one_seed
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    mt = load_one_seed(s, "audio_coding_theory")
    install_all_concept_expansions(s)
    n_concepts = len(s.neighbours(mt, "has_concept"))
    n_rules = len(s.neighbours(mt, "has_rule"))
    assert n_concepts >= 165, f"only {n_concepts} concepts"
    assert n_rules >= 50, f"only {n_rules} rules"
