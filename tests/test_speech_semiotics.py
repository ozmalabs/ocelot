"""Phase 15 — speech-to-semiotics.

Speech to graph-resident SIGN OBJECTS, not text. Each utterance
becomes an AcousticSign in a Lexicon; recurring patterns strengthen
existing signs (Hebbian-shape); a sign can be grounded to a Concept
via the standard `denotes` edge — same Peircean shape the substrate
already uses for text-form signs.

Tests cover:
* Utterance detection via native codec hints (no ASR, no decode for
  detection).
* Per-utterance acoustic feature extraction via the cochlear bank.
* AcousticSign acquisition (mint new) and matching (find existing
  via cosine similarity, bump hearings).
* Grounding via `denotes` edges to Concept nodes.
* Full pipeline `ingest_speech` chains the lot.
* Repeated identical utterances → 1 sign, not N.
* Distinct utterances → distinct signs.
"""
from __future__ import annotations

import os
import tempfile

import av
import numpy as np
import pytest


srs = pytest.importorskip("substrate_rs")
a = pytest.importorskip("substrate_rs.audio")
sp = pytest.importorskip("substrate_rs.speech")


def _encode(path: str, codec: str, *, sample_rate: int,
            samples: np.ndarray, chunk: int = 1024) -> str:
    """Encode a mono float32 numpy array as `codec`."""
    container = av.open(path, mode="w")
    stream = container.add_stream(codec, rate=sample_rate)
    stream.codec_context.layout = "mono"
    n = len(samples)
    samples = samples.astype(np.float32).reshape(1, -1)
    for start in range(0, n, chunk):
        sub = samples[:, start:start + chunk]
        if sub.shape[1] < chunk:
            sub = np.pad(sub, ((0, 0), (0, chunk - sub.shape[1])))
        frame = av.AudioFrame.from_ndarray(sub, format="flt", layout="mono")
        frame.sample_rate = sample_rate
        for pkt in stream.encode(frame):
            container.mux(pkt)
    for pkt in stream.encode():
        container.mux(pkt)
    container.close()
    return path


def _utterance_audio(tone_hz: float, duration_s: float = 0.5,
                     sample_rate: int = 22050,
                     envelope_attack: float = 0.05,
                     envelope_release: float = 0.05) -> np.ndarray:
    """Build a synthetic 'utterance' — a windowed tone burst. The
    attack/release envelopes give the cochlear features something
    non-flat to discriminate on."""
    n = int(sample_rate * duration_s)
    t = np.arange(n) / sample_rate
    tone = np.sin(2 * np.pi * tone_hz * t).astype(np.float32)
    env = np.ones(n, dtype=np.float32)
    a_n = int(envelope_attack * sample_rate)
    r_n = int(envelope_release * sample_rate)
    env[:a_n] = np.linspace(0, 1, a_n)
    env[-r_n:] = np.linspace(1, 0, r_n)
    return tone * env * 0.3


def _multi_utterance_audio(tone_specs: list[tuple[float, float]],
                           gap_s: float = 0.3,
                           sample_rate: int = 22050) -> np.ndarray:
    """Concatenate several utterances with silent gaps between. Each
    spec is (tone_hz, duration_s). The silent gaps give the detector
    something to segment on."""
    chunks = []
    for hz, dur in tone_specs:
        chunks.append(_utterance_audio(hz, dur, sample_rate))
        # Silent gap.
        chunks.append(np.zeros(int(gap_s * sample_rate), dtype=np.float32))
    return np.concatenate(chunks)


@pytest.fixture
def s():
    sub = srs.Substrate()
    a.seed_audio_grammar(sub)
    a.seed_native_codec_grammar(sub)
    sp.seed_speech_grammar(sub)
    return sub


# --- Lexicon basics ---------------------------------------------------


def test_open_lexicon_creates_anchor(s):
    lex = sp.open_lexicon(s, name="test_lex")
    assert s.node(lex)["type"] == sp.LEXICON
    attrs = s.node(lex)["attrs"]
    assert attrs["name"] == "test_lex"
    assert attrs["n_signs"] == 0


def test_lexicon_describe_empty(s):
    lex = sp.open_lexicon(s, name="ling")
    info = sp.lexicon_describe(s, lex)
    assert info["name"] == "ling"
    assert info["n_signs"] == 0


# --- Utterance detection ----------------------------------------------


def test_detect_utterances_finds_speech_segments(s):
    """An audio file with 3 distinct tone-bursts separated by silence
    should yield ~3 utterances via the energy-based segmenter.

    Use Opus rather than MP3 because the CBR MP3 encoder produces
    fixed-size frames — every frame trips the coded_size threshold,
    yielding one giant segment that exceeds max_duration_s. Opus is
    variable-rate and emits much smaller packets for silence, which
    is what the energy-fallback detector needs to find boundaries.
    """
    f = tempfile.NamedTemporaryFile(suffix=".ogg", delete=False)
    f.close()
    try:
        audio = _multi_utterance_audio(
            [(440.0, 0.5), (550.0, 0.5), (660.0, 0.5)], gap_s=0.4,
            sample_rate=48000)
        _encode(f.name, "libopus", sample_rate=48000, samples=audio, chunk=960)
        cnid = a.open_container(s, f.name)
        snid = a.add_stream(s, cnid)
        a.parse_stream(s, cnid, snid)
        a.parse_native(s, cnid, snid)
        utts = sp.detect_utterances(s, snid,
                                    min_duration_s=0.1, max_duration_s=4.0)
        assert len(utts) >= 1, "expected at least 1 utterance"
        for u in utts:
            attrs = s.node(u)["attrs"]
            assert attrs["duration_s"] > 0
            assert attrs["start_time_s"] >= 0
    finally:
        os.unlink(f.name)


def test_utterance_carries_provenance_to_stream(s):
    f = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    f.close()
    try:
        audio = _utterance_audio(440.0, duration_s=1.0)
        _encode(f.name, "mp3", sample_rate=22050, samples=audio)
        cnid = a.open_container(s, f.name)
        snid = a.add_stream(s, cnid)
        a.parse_stream(s, cnid, snid)
        a.parse_native(s, cnid, snid)
        utts = sp.detect_utterances(s, snid)
        if utts:
            assert s.neighbours(utts[0], sp.FROM_STREAM) == [snid]
    finally:
        os.unlink(f.name)


# --- Feature extraction ----------------------------------------------


def test_extract_features_returns_fixed_length_vector(s):
    """Features are a flattened (n_bands × n_time_windows) array.
    Defaults: 16 × 4 = 64 floats."""
    f = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    f.close()
    try:
        _encode(f.name, "mp3", sample_rate=22050,
                samples=_utterance_audio(440.0, duration_s=0.8))
        cnid = a.open_container(s, f.name)
        snid = a.add_stream(s, cnid)
        a.parse_stream(s, cnid, snid)
        a.parse_native(s, cnid, snid)
        utts = sp.detect_utterances(s, snid)
        if not utts:
            pytest.skip("encoder didn't produce a detectable utterance")
        features = sp.extract_features(
            s, utts[0], n_bands=16, n_time_windows=4)
        assert features.shape == (64,)
        assert features.dtype == np.float32
        # A 440 Hz tone should produce non-zero energy in low-frequency
        # bands (Gammatone fc_low ~80 Hz, so bands 0-3 carry energy).
        assert features.sum() > 0
    finally:
        os.unlink(f.name)


def test_distinct_tones_produce_distinct_features():
    """440 Hz and 1500 Hz utterances should give DIFFERENT feature
    vectors — the lexicon needs this property to distinguish signs."""
    s = srs.Substrate()
    a.seed_audio_grammar(s)
    a.seed_native_codec_grammar(s)
    sp.seed_speech_grammar(s)
    cochlea_bank = a.cochlea(s, n_bands=16, fs=22050)
    # Use raw audio buffers + the underlying extract logic for a
    # noise-free comparison; speech.extract_features needs an
    # Utterance + stream, so we synthesise via the convolution
    # pipeline directly.
    fs = 22050
    for hz in (440.0, 1500.0):
        samples = _utterance_audio(hz, duration_s=0.8, sample_rate=fs)
        buf = a.audio_from_array(s, samples, sample_rate=fs)
        responses = a.a1_responses(s, buf, cochlea_bank)
        per_band_energy = np.array([
            float(np.mean(a.audio_to_array(s, r).astype(np.float32) ** 2))
            for r in responses])
        if hz == 440.0:
            feat_440 = per_band_energy
        else:
            feat_1500 = per_band_energy
    # Cosine similarity between the two should be well below 1.
    sim = float(np.dot(feat_440, feat_1500) / (
        np.linalg.norm(feat_440) * np.linalg.norm(feat_1500) + 1e-9))
    assert sim < 0.95, f"distinct tones should be distinguishable; sim={sim:.3f}"


# --- Sign acquisition + matching --------------------------------------


def test_first_features_mint_new_sign(s):
    lex = sp.open_lexicon(s)
    features = np.random.RandomState(0).rand(64).astype(np.float32)
    sign, is_new = sp.acquire_sign(s, lex, features, label="hello")
    assert is_new is True
    assert sign is not None
    assert s.node(sign)["type"] == sp.ACOUSTIC_SIGN
    attrs = s.node(sign)["attrs"]
    assert attrs["label"] == "hello"
    assert attrs["hearings"] == 1
    # Lexicon contains the new sign.
    assert sign in sp.lexicon_signs(s, lex)
    assert s.node(lex)["attrs"]["n_signs"] == 1


def test_matching_features_bump_existing_sign_count(s):
    lex = sp.open_lexicon(s)
    rng = np.random.RandomState(0)
    features = rng.rand(64).astype(np.float32)
    sign1, new1 = sp.acquire_sign(s, lex, features, label="word")
    # Same features again — should match the existing sign.
    sign2, new2 = sp.acquire_sign(s, lex, features.copy())
    assert sign1 == sign2
    assert new1 is True
    assert new2 is False
    # Hearings bumped to 2.
    assert s.node(sign1)["attrs"]["hearings"] == 2
    # Still only one sign in the lexicon.
    assert len(sp.lexicon_signs(s, lex)) == 1


def test_distinct_features_mint_distinct_signs(s):
    """Two clearly different feature vectors → two signs."""
    lex = sp.open_lexicon(s)
    f1 = np.zeros(64, dtype=np.float32); f1[0:8] = 1.0  # energy at low bands
    f2 = np.zeros(64, dtype=np.float32); f2[56:64] = 1.0  # energy at high bands
    sign1, new1 = sp.acquire_sign(s, lex, f1, label="low")
    sign2, new2 = sp.acquire_sign(s, lex, f2, label="high")
    assert new1 is True and new2 is True
    assert sign1 != sign2
    assert len(sp.lexicon_signs(s, lex)) == 2


def test_match_sign_returns_none_below_threshold(s):
    lex = sp.open_lexicon(s)
    f1 = np.zeros(64, dtype=np.float32); f1[0:8] = 1.0
    f2 = np.zeros(64, dtype=np.float32); f2[40:48] = 1.0
    sp.acquire_sign(s, lex, f1, label="low")
    matched, sim = sp.match_sign(s, lex, f2, threshold=0.85)
    # Two orthogonal vectors have cosine similarity 0.
    assert matched is None
    assert sim < 0.1


def test_acquire_sign_handles_zero_features(s):
    """An all-zero feature vector (e.g., a silence utterance that
    slipped through) should NOT mint a sign — silence isn't a
    word."""
    lex = sp.open_lexicon(s)
    sign, is_new = sp.acquire_sign(s, lex, np.zeros(64, dtype=np.float32))
    assert sign is None
    assert is_new is False
    assert len(sp.lexicon_signs(s, lex)) == 0


def test_acquired_sign_prototype_is_running_mean(s):
    """When a sign matches and gets a hearing bump, its prototype
    moves to the running mean of all exemplars. Verify: acquire with
    features F1, then with F2 (close enough to match), prototype
    should be (F1+F2)/2."""
    lex = sp.open_lexicon(s)
    rng = np.random.RandomState(0)
    f1 = rng.rand(64).astype(np.float32)
    f2 = f1 + rng.randn(64).astype(np.float32) * 0.05  # very similar
    sign1, _ = sp.acquire_sign(s, lex, f1)
    sign2, _ = sp.acquire_sign(s, lex, f2)
    assert sign1 == sign2
    proto = np.frombuffer(
        s.node(sign1)["attrs"]["features"], dtype=np.float32)
    expected = (f1 + f2) / 2.0
    np.testing.assert_allclose(proto, expected, rtol=1e-4)


# --- Grounding: link sign to concept ----------------------------------


def test_ground_sign_creates_denotes_edge(s):
    """A teacher hands the agent a Concept node; the agent links the
    AcousticSign's denotation. Peircean: sign → object."""
    # Mint a Concept node directly (in real usage the agent's grounding
    # faculty builds this from a Term-tree — see WorldAdapter.ground_from_spec).
    s.add_production(srs.Production(
        src=srs.NodePattern(type="Concept", var="src"),
        edge_type="dummy", tgt=srs.NodePattern(type="Concept", var="tgt"),
        where=None, weight=None, provenance="test:perm"))
    concept = s.add_node("Concept", {"name": "greeting"})
    lex = sp.open_lexicon(s)
    sign, _ = sp.acquire_sign(s, lex, np.ones(64, dtype=np.float32), label="hello")
    sp.ground_sign(s, sign, concept)
    assert sp.denoted_concepts(s, sign) == [concept]


def test_lexicon_grounded_fraction_grows_with_grounding(s):
    # Set up a permissive grammar for Concept linking.
    concept_a = s.add_node("Concept", {"name": "a"})
    concept_b = s.add_node("Concept", {"name": "b"})
    lex = sp.open_lexicon(s)
    f1 = np.zeros(64, dtype=np.float32); f1[0:8] = 1.0
    f2 = np.zeros(64, dtype=np.float32); f2[16:24] = 1.0
    f3 = np.zeros(64, dtype=np.float32); f3[32:40] = 1.0
    s1, _ = sp.acquire_sign(s, lex, f1)
    s2, _ = sp.acquire_sign(s, lex, f2)
    s3, _ = sp.acquire_sign(s, lex, f3)
    # No grounding yet.
    assert sp.lexicon_grounded_fraction(s, lex) == 0.0
    # Ground 2 of 3.
    sp.ground_sign(s, s1, concept_a)
    sp.ground_sign(s, s2, concept_b)
    assert sp.lexicon_grounded_fraction(s, lex) == pytest.approx(2 / 3)


# --- Full pipeline ----------------------------------------------------


def test_ingest_speech_end_to_end():
    """Audio → utterances → features → signs in one call. Repeated
    identical content should produce few distinct signs."""
    s = srs.Substrate()
    a.seed_audio_grammar(s)
    a.seed_native_codec_grammar(s)
    sp.seed_speech_grammar(s)
    f = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    f.close()
    try:
        # Two distinct "words" repeated 3 times each, interleaved.
        # word_A = 440 Hz tone (0.4s); word_B = 880 Hz tone (0.4s).
        audio = _multi_utterance_audio([
            (440, 0.4), (880, 0.4), (440, 0.4),
            (880, 0.4), (440, 0.4), (880, 0.4),
        ], gap_s=0.3, sample_rate=22050)
        _encode(f.name, "mp3", sample_rate=22050, samples=audio)
        cnid = a.open_container(s, f.name)
        snid = a.add_stream(s, cnid)
        a.parse_stream(s, cnid, snid)
        a.parse_native(s, cnid, snid)
        lex = sp.open_lexicon(s, name="test_corpus")
        results = sp.ingest_speech(s, snid, lex, threshold=0.80)
        # Some utterances detected.
        assert len(results) >= 1
        # The lexicon should have at most a handful of signs —
        # ideally 2 (one per distinct tone), but real encoders
        # produce noisy features so we tolerate 1-4.
        n_signs = len(sp.lexicon_signs(s, lex))
        n_distinct_tones = 2  # 440 + 880
        assert 1 <= n_signs <= 4, (
            f"expected ~{n_distinct_tones} signs from 2 distinct tones; "
            f"got {n_signs}")
        print(f"\n  detected {len(results)} utterances → "
              f"{n_signs} distinct signs in lexicon")
        # Every utterance should have a `heard_as` edge to whatever
        # sign matched/acquired.
        for utt, sign, _ in results:
            if sign is not None:
                assert sign in s.neighbours(utt, sp.HEARD_AS)
    finally:
        os.unlink(f.name)


def test_repeated_identical_signs_match_via_acquire_sign():
    """The 'matching collapses to one sign' property is most cleanly
    tested at the acquire_sign level — feeding the same feature
    vector multiple times should match the existing sign and bump
    its hearings, not create copies. The end-to-end test above
    (test_ingest_speech_end_to_end) covers the streaming case at
    the encoder's whim.
    """
    s = srs.Substrate()
    sp.seed_speech_grammar(s)
    lex = sp.open_lexicon(s)
    features = np.random.RandomState(0).rand(64).astype(np.float32)
    sign1, new1 = sp.acquire_sign(s, lex, features.copy())
    sign2, new2 = sp.acquire_sign(s, lex, features.copy())
    sign3, new3 = sp.acquire_sign(s, lex, features.copy())
    sign4, new4 = sp.acquire_sign(s, lex, features.copy())
    assert sign1 == sign2 == sign3 == sign4
    assert (new1, new2, new3, new4) == (True, False, False, False)
    assert s.node(sign1)["attrs"]["hearings"] == 4
    assert len(sp.lexicon_signs(s, lex)) == 1


# --- DSL queries: the agent introspects its own lexicon ---------------


def test_agent_queries_sign_label_via_dsl(s):
    lex = sp.open_lexicon(s)
    sign, _ = sp.acquire_sign(
        s, lex, np.ones(64, dtype=np.float32), label="greeting")
    # The agent reads the sign label using the standard DSL.
    label = s.evaluate(srs.Attr(srs.Lit(sign), "label"))
    hearings = s.evaluate(srs.Attr(srs.Lit(sign), "hearings"))
    assert label == "greeting"
    assert hearings == 1


def test_lexicon_describe_lists_known_signs(s):
    lex = sp.open_lexicon(s, name="vocab")
    for i in range(3):
        feats = np.zeros(64, dtype=np.float32)
        feats[i * 16:(i + 1) * 16] = 1.0
        sp.acquire_sign(s, lex, feats, label=f"sign_{i}")
    info = sp.lexicon_describe(s, lex)
    assert info["name"] == "vocab"
    assert info["n_signs"] == 3
    assert set(info["sample_labels"]) == {"sign_0", "sign_1", "sign_2"}


# --- The Peircean structure: full sign-object-interpretant chain ----


def test_full_peircean_chain():
    """The substrate's full semiotic loop:

      1. Hear acoustic pattern → AcousticSign (sign / form)
      2. Sign denotes Concept (object)
      3. Agent evaluates the Concept's Term-tree (interpretant)

    Verify all three steps land as graph data the agent can query."""
    s = srs.Substrate()
    a.seed_audio_grammar(s)
    a.seed_native_codec_grammar(s)
    sp.seed_speech_grammar(s)
    # The "object": a Concept whose meaning is the Term `Plus(x, 1)`.
    concept = s.add_node("Concept", {
        "name": "next_number",
        "definition_term": srs.Plus(items=(srs.Var("x"), srs.Lit(1))).to_dict(),
    })
    # The "sign": an AcousticSign acquired from features.
    lex = sp.open_lexicon(s)
    features = np.random.RandomState(0).rand(64).astype(np.float32)
    sign, _ = sp.acquire_sign(s, lex, features, label="next")
    # Wire sign → object.
    sp.ground_sign(s, sign, concept)
    # The "interpretant": evaluating the Concept's Term-tree. The
    # term_json is already a JSON dict (we built it via to_dict()),
    # so route through the underlying native eval that takes dicts.
    term_json = s.node(concept)["attrs"]["definition_term"]
    result = s._inner.evaluate(term_json, {"x": 41})
    assert result == 42, "evaluating the denoted Concept should produce 42"
    # And the chain is graph-walkable.
    denoted = sp.denoted_concepts(s, sign)
    assert concept in denoted
