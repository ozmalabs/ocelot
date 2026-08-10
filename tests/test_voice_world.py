"""VoiceWorld bench — the mic-in/speech-out world adapter (domains/voice_world.py).

No live hardware required: audio fixtures are synthesised in-process (same shape
as tests/test_speech_semiotics.py / tests/test_audio_world_migrated.py's tone
bursts) or, where available, real speech is read from the LibriSpeech dev-clean
corpus at /home/matt/data/LibriSpeech (skipped if absent — this repo's `data/`
directory itself carries no audio, only text/JSON corpora).

Covers the task's four honesty checks:
  (a) VAD segments two energy bursts separated by silence into two utterances.
  (b) A synthesised "utterance" goes through ingest -> the same AcousticSign/
      Mention/has_intent assertions tests/test_audio_world_migrated.py makes.
  (c) The reply path (VoiceWorld.reply_for, the same outbound_messages/
      responds_to primitives WorldAdapter.converse() composes) produces a
      non-empty surface for a statement -> acknowledgment adjacency pair
      (there is no ASR, so "a seeded question the chat stack can answer" is
      exercised at the Message/Intent level exactly as
      test_speech_bridge_acoustic_sign_refers_to_denoted_concept does, not
      via a spoken question whose content is understood — reported honestly).
  (d) --wav mode end-to-end smoke test (subprocess).

Where recognition quality is asserted, the ACTUAL numbers are reported via
`capsys`/print, not asserted tight — this stack's honest state (commit
c8df2dab) is ~0.37-0.93 order-1 purity depending on segmentation source and
~48% cross-speaker recall on isolated words; this file never pretends
otherwise.
"""
from __future__ import annotations

import glob
import os
import subprocess
import sys
import tempfile

import numpy as np
import pytest

pytest.importorskip("substrate_rs")
pytest.importorskip("av")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from substrate.world_adapter import WorldAdapter          # noqa: E402
import domains.voice_world as VW                          # noqa: E402

LIBRISPEECH_DEV_CLEAN = "/home/matt/data/LibriSpeech/dev-clean"
_HAS_LIBRISPEECH = bool(glob.glob(os.path.join(LIBRISPEECH_DEV_CLEAN, "*", "*", "*.flac")))


# --------------------------------------------------------------------------- #
#  Fixture audio (synthetic — same tone-burst shape the existing speech
#  benches use; VAD/ingest don't care about phonetic content).
# --------------------------------------------------------------------------- #
def _tone(hz: float, dur_s: float, fs: int, amp: float = 0.3) -> np.ndarray:
    n = int(fs * dur_s)
    t = np.arange(n) / fs
    x = np.sin(2 * np.pi * hz * t).astype(np.float32) * amp
    a = max(1, int(0.02 * fs))
    x[:a] *= np.linspace(0, 1, a, dtype=np.float32)
    x[-a:] *= np.linspace(1, 0, a, dtype=np.float32)
    return x


def _two_words_with_gap(fs=VW.FS, gap_s: float = 1.0) -> np.ndarray:
    """Two energy bursts ("words") separated by a silence gap comfortably
    longer than the VAD's close_silence_s (0.6s default)."""
    return np.concatenate([
        np.zeros(int(0.2 * fs), dtype=np.float32),
        _tone(300.0, 0.35, fs),
        np.zeros(int(gap_s * fs), dtype=np.float32),
        _tone(600.0, 0.40, fs),
        np.zeros(int(0.2 * fs), dtype=np.float32),
    ])


def _one_word(fs=VW.FS) -> np.ndarray:
    return np.concatenate([
        np.zeros(int(0.1 * fs), dtype=np.float32),
        _tone(440.0, 0.5, fs),
        np.zeros(int(0.1 * fs), dtype=np.float32),
    ])


def _librispeech_utterance(fs=VW.FS):
    flacs = sorted(glob.glob(os.path.join(LIBRISPEECH_DEV_CLEAN, "*", "*", "*.flac")))
    samples, sr = VW.load_audio_any(flacs[0], fs=fs)
    return samples, sr, flacs[0]


# --------------------------------------------------------------------------- #
#  (a) VAD segmentation
# --------------------------------------------------------------------------- #
def test_vad_segments_two_words_separated_by_silence():
    sig = _two_words_with_gap()
    utts = VW.segment_utterances(sig, fs=VW.FS)
    assert len(utts) == 2, f"expected 2 VAD-closed utterances, got {len(utts)}"
    for u in utts:
        assert 0.15 <= len(u) / VW.FS <= 0.8


def test_vad_drops_pure_silence():
    sig = np.zeros(int(1.0 * VW.FS), dtype=np.float32)
    assert VW.segment_utterances(sig, fs=VW.FS) == []


def test_vad_one_utterance_no_gap():
    sig = _one_word()
    utts = VW.segment_utterances(sig, fs=VW.FS)
    assert len(utts) == 1


def test_stream_vad_matches_offline_vad():
    """The live-capture state machine (_StreamVAD, frame-by-frame) finds the
    same utterance count as the offline whole-array segmenter on the same
    signal — the two are meant to agree (module docstring)."""
    sig = _two_words_with_gap()
    vad = VW._StreamVAD(fs=VW.FS)
    frame_len = vad.frame_len
    found = []
    n = len(sig) // frame_len
    for i in range(n):
        out = vad.push(sig[i * frame_len:(i + 1) * frame_len])
        if out is not None:
            found.append(out)
    tail = vad.flush()
    if tail is not None:
        found.append(tail)
    assert len(found) == 2


@pytest.mark.skipif(not _HAS_LIBRISPEECH, reason="LibriSpeech dev-clean not present on this machine")
def test_vad_on_real_speech_reports_honest_segment_count(capsys):
    """Real continuous read speech usually has few/no >0.6s silence gaps
    within a single sentence, so VAD typically finds ONE utterance spanning
    (most of) the clip — the honest reason a live conversational turn is
    "one utterance per breath group", not per word. Reported, not asserted
    tight."""
    samples, sr, path = _librispeech_utterance()
    utts = VW.segment_utterances(samples, fs=sr)
    print(f"\n  {os.path.basename(path)}: {len(samples)/sr:.2f}s -> "
          f"{len(utts)} VAD utterance(s): {[round(len(u)/sr, 2) for u in utts]}")
    assert len(utts) >= 1


# --------------------------------------------------------------------------- #
#  (b) ingest -> AcousticSign / Mention / comprehension nodes
#      (same assertions as tests/test_audio_world_migrated.py)
# --------------------------------------------------------------------------- #
def test_hear_writes_message_with_acoustic_mention():
    wa = WorldAdapter()
    vw = VW.VoiceWorld(wa, lexicon_name="voice_test")
    results = vw.hear(_one_word(), fs=VW.FS)
    assert len(results) >= 1, results
    for r in results:
        mid, sid = r["message"], r["sign"]
        msg = wa.s.node(mid)
        assert msg["type"] == "Message"
        assert msg["attrs"].get("source") == "audio"
        assert msg["attrs"].get("from") == "interlocutor"
        if sid is not None:
            assert sid in set(wa.inner.neighbours(mid, "has_mention"))


def test_hear_then_comprehend_builds_intent():
    wa = WorldAdapter()
    vw = VW.VoiceWorld(wa, lexicon_name="voice_test")
    results = vw.hear(_one_word(), fs=VW.FS)
    wa.comprehend()
    assert len(results) >= 1
    for r in results:
        mid = r["message"]
        assert list(wa.inner.neighbours(mid, "has_intent")), (
            "comprehend=True + comprehend() should build an Intent for the audio Message, "
            "exactly as test_ingest_then_comprehend_builds_intents asserts")


def test_repeated_identical_utterance_reuses_one_sign():
    """Same fixture heard twice -> the second hearing MATCHES the existing
    AcousticSign (is_new False), it doesn't mint a duplicate — mirrors
    test_repeated_identical_signs_match_via_acquire_sign."""
    wa = WorldAdapter()
    vw = VW.VoiceWorld(wa, lexicon_name="voice_test")
    clip = _one_word()
    r1 = vw.hear(clip, fs=VW.FS)
    r2 = vw.hear(clip, fs=VW.FS)
    assert r1 and r2
    assert r1[0]["is_new"] is True
    # a bit-identical re-hearing should match the same sign, not mint a new one
    assert r2[0]["is_new"] is False
    assert r1[0]["sign"] == r2[0]["sign"]


def test_speech_bridge_makes_a_grounded_sign_a_resolved_mention():
    """The speech-bridge shape VoiceWorld.hear() produces (Message -has_mention->
    AcousticSign) is exactly what rule_acoustic_sign_refers_to_denoted_concept
    (tests/test_intent_migrated.py:111) expects: once the sign `denotes` a
    Concept, comprehend() gives it `refers_to` that Concept."""
    wa = WorldAdapter()
    vw = VW.VoiceWorld(wa, lexicon_name="voice_test")
    wa._ensure_intent_seeds()
    concept = wa._concept_by_name("greeting") or wa.s.add_node("Concept", {"name": "greeting"})
    results = vw.hear(_one_word(), fs=VW.FS)
    sign = results[0]["sign"]
    assert sign is not None
    wa.inner.add_edge_unchecked(sign, "denotes", concept)
    wa.comprehend()
    assert concept in set(wa.inner.neighbours(sign, "refers_to"))


@pytest.mark.skipif(not _HAS_LIBRISPEECH, reason="LibriSpeech dev-clean not present on this machine")
def test_ingest_real_speech_honest_recognition(capsys):
    """Feed a real LibriSpeech utterance through the exact pipeline and report
    what actually happens: a new AcousticSign is minted (no lexicon entry
    could match yet — this is the FIRST hearing), no `denotes` edge exists
    (nothing has grounded it), so it is NOT resolved to a Concept. This is the
    honest state, not a failure of this adapter: recognition quality is the
    known frontier (c8df2dab: order-1 purity ~0.37-0.93 depending on
    segmentation source; ~48% cross-speaker recall on isolated words is the
    best donkey=0 baseline elsewhere in this repo)."""
    wa = WorldAdapter()
    vw = VW.VoiceWorld(wa, lexicon_name="voice_test")
    samples, sr, path = _librispeech_utterance()
    utts = VW.segment_utterances(samples, fs=sr)
    assert utts
    results = vw.hear_and_reply(utts[0], fs=sr)
    print(f"\n  {os.path.basename(path)} utterance[0] "
          f"({len(utts[0])/sr:.2f}s) -> {len(results)} Message(s)")
    for r in results:
        grounded = bool(wa.inner.neighbours(r["sign"], "denotes")) if r["sign"] else False
        print(f"    sign={r['sign']} is_new={r['is_new']} grounded={grounded} "
              f"reply={r['reply']!r}")
        assert r["message"] is not None
    # Honest claim: an ungrounded lexicon still produces A turn (the
    # adjacency-pair reply), just no content-level understanding.
    assert all(r["reply"] for r in results)


# --------------------------------------------------------------------------- #
#  (c) reply path
# --------------------------------------------------------------------------- #
def test_reply_for_statement_is_nonempty():
    """statement -> acknowledgment is the only adjacency pair reachable from
    an audio Message (ingest_audio_file(comprehend=True) always tags
    speech_act=statement — audio carries no orthography to classify a
    question/greeting from). VoiceWorld.reply_for renders it via
    surface_for (idiomatic: 'noted') with a graceful fallback to the raw
    concept name."""
    wa = WorldAdapter()
    vw = VW.VoiceWorld(wa, lexicon_name="voice_test")
    out = vw.hear_and_reply(_one_word(), fs=VW.FS)
    assert out and all(r["reply"] for r in out)
    assert out[0]["reply"] == "noted", out[0]["reply"]


def test_reply_for_none_before_comprehend():
    """reply_for is a pure query: with no comprehend()/tick() yet, there is no
    reply Message to find."""
    wa = WorldAdapter()
    vw = VW.VoiceWorld(wa, lexicon_name="voice_test")
    results = vw.hear(_one_word(), fs=VW.FS)
    assert vw.reply_for(results[0]["message"]) is None


# --------------------------------------------------------------------------- #
#  Synthesis (Piper — borrowed, see domains/voice_world.py module docstring)
# --------------------------------------------------------------------------- #
@pytest.mark.skipif(not VW.piper_available(), reason="Piper voice model not installed")
def test_synth_speech_produces_audio():
    got = VW.synth_speech("The thing stays.")
    assert got is not None
    samples, sr = got
    assert samples.dtype == np.int16
    assert samples.size > 0
    assert sr > 0


def test_synth_speech_missing_voice_returns_none():
    assert VW.synth_speech("hello", variant="not_a_real_voice_xyz") is None


# --------------------------------------------------------------------------- #
#  (d) --wav mode end-to-end smoke test (subprocess)
# --------------------------------------------------------------------------- #
def _write_temp_wav(samples, fs):
    fd, path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    VW._write_wav(path, samples, fs)
    return path


def test_wav_mode_smoke():
    if _HAS_LIBRISPEECH:
        samples, sr, _ = _librispeech_utterance()
        path = _write_temp_wav(samples, sr)
    else:
        path = _write_temp_wav(_two_words_with_gap(), VW.FS)
    try:
        env = dict(os.environ)
        env["PYTHONPATH"] = f"{os.path.join(ROOT, 'runners', 'dsl', 'python')}:{ROOT}"
        r = subprocess.run(
            [sys.executable, os.path.join(ROOT, "scripts", "voice_session.py"),
             "--wav", path, "--no-speak"],
            capture_output=True, text=True, timeout=180, env=env)
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"
        assert "VAD found" in r.stdout
        assert "heard:" in r.stdout
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
