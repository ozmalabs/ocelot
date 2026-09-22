"""Speech grounding bench — the per-turn caregiver-enrollment -> graph-native
recognition loop (domains/speech_enrollment.py + the recognition Rules
domains/voice_world.py installs).

WHAT IS GATED (per the task brief):
  (a) enroll() persists — a Concept/LexEntry/AcousticExemplar taught (teach(),
      idempotent) and the live grounding survives a checkpoint save/load.
  (b) a HELD-OUT utterance of an enrolled word gets a `denotes` edge minted by
      `run_rules()` alone — zero Python matching (the DTW distance and the
      argmin-then-threshold decision are graph Terms/Rules, not a Python fn).
  (c) an utterance of a NON-enrolled word stays ungrounded (the reject path;
      discriminative, not "always match something").
  (d) the reply differs from the generic "noted" once grounding fires (the
      speech-bridge -> reply chain).
  (e) ACTUAL recall/precision over the enrolled vocabulary, reported plainly
      (capsys), not asserted tight.
  Plus: daemon boot sanity with the new /api/enroll route, and the mock
  server's enrollment path (web UI verification level).

REPRESENTATION HONESTY: Piper (this repo's only installed TTS) is NOT
available in this environment (`VW.piper_available()` is False here), and
LibriSpeech dev-clean's VAD granularity is SENTENCE-level, not word-level
(tests/test_voice_world.py's own honest note: "real continuous read speech
... VAD typically finds ONE utterance spanning (most of) the clip") — there
is no forced-aligner in this repo to slice word-level LibriSpeech segments.
So the quantitative recall/precision numbers below come from SYNTHETIC
multi-harmonic "tone word" fixtures (3 stacked harmonics + phase/frequency/
duration/noise jitter per rendering, so no two renderings are bit-identical —
a genuine "same word, different recording" regime), run through the REAL
pipeline end to end: ffmpeg wav write/read, `substrate_rs.audio` cochlea,
`substrate_rs.speech.extract_features`/`acquire_sign`, the graph Rules
(`DtwTo`, `MinOver`, `run_rules`). Where LibriSpeech IS present, a real-speech
discriminative sanity check runs too (skipped otherwise) — reported, not the
headline number.
"""
from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request

import numpy as np
import pytest

pytest.importorskip("substrate_rs")
pytest.importorskip("av")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.world_adapter import WorldAdapter          # noqa: E402
import domains.voice_world as VW                          # noqa: E402
import domains.speech_enrollment as SE                    # noqa: E402

LIBRISPEECH_DEV_CLEAN = "/home/matt/data/LibriSpeech/dev-clean"


# --------------------------------------------------------------------------- #
#  seeds/speech_enrollment.json guard — enroll()/materialize_enrollments()
#  persist real teach() data (by design: caregiver teaching must survive a
#  reboot). Snapshot + restore the file's exact bytes around every test in
#  this module, same shape as tests/fixtures/composer_driver_parity/
#  capture.py's `_ProgramsJsonGuard` (the established precedent for a test
#  that exercises real `teach()` persistence without leaving fixture-only
#  words in the real seed corpus).
# --------------------------------------------------------------------------- #
_SEED_PATH = os.path.join(ROOT, "seeds", "speech_enrollment.json")


@pytest.fixture(autouse=True)
def _speech_enrollment_seed_guard():
    existed = os.path.exists(_SEED_PATH)
    before = open(_SEED_PATH).read() if existed else None
    try:
        yield
    finally:
        if existed:
            with open(_SEED_PATH, "w") as f:
                f.write(before)
        elif os.path.exists(_SEED_PATH):
            os.unlink(_SEED_PATH)


# --------------------------------------------------------------------------- #
#  synthetic "tone word" fixtures — see module docstring's honesty note.
# --------------------------------------------------------------------------- #
def _tone_word(hz: float, dur_s: float = 0.4, fs: int = VW.FS, amp: float = 0.3,
              freq_jit: float = 0.03, noise: float = 0.02, dur_jitter: float = 0.05,
              seed: int = 0) -> np.ndarray:
    """A "word" = 3 stacked harmonics at `hz` with per-rendering jitter (freq,
    duration, phase, additive noise) so repeated calls are genuinely different
    recordings, not bit-identical repeats (which acquire_sign's cosine
    pre-merge would trivially "recognise" without exercising the DTW Rules)."""
    rng = np.random.RandomState(seed)
    hz2 = hz * (1 + freq_jit * (rng.rand() * 2 - 1))
    d = dur_s * (1 + dur_jitter * (rng.rand() * 2 - 1))
    n = int(fs * d)
    t = np.arange(n) / fs
    x = np.sin(2 * np.pi * hz2 * t + rng.rand() * 6.28).astype(np.float32)
    x += 0.5 * np.sin(2 * np.pi * hz2 * 2 * t + rng.rand() * 6.28).astype(np.float32)
    x += 0.25 * np.sin(2 * np.pi * hz2 * 3 * t + rng.rand() * 6.28).astype(np.float32)
    x *= amp
    if noise > 0:
        x = x + rng.randn(n).astype(np.float32) * noise
    a = max(1, int(0.02 * fs))
    x[:a] *= np.linspace(0, 1, a, dtype=np.float32)
    x[-a:] *= np.linspace(1, 0, a, dtype=np.float32)
    pad = np.zeros(int(0.15 * fs), dtype=np.float32)
    return np.concatenate([pad, x, pad]).astype(np.float32)


WORDS = {"alpha": 300.0, "beta": 450.0, "gamma": 600.0, "delta": 750.0}
NEGATIVE_WORDS = {"epsilon": 1000.0, "zeta": 1250.0}


def _fresh_lexicon(lex="voice_test_lex"):
    """A fresh, per-test AcousticLexicon name so signs from earlier tests in
    this process (same interpreter, module-level substrate_rs) never bleed in."""
    import itertools
    _fresh_lexicon.counter = getattr(_fresh_lexicon, "counter", itertools.count())
    return f"{lex}_{next(_fresh_lexicon.counter)}"


def _enroll_words(wa, words, lexicon_name, n_exemplars=2, seed_base=100):
    for w, hz in words.items():
        for i in range(n_exemplars):
            samp = _tone_word(hz, seed=seed_base + i)
            SE.enroll(wa, samp, w, lexicon_name=lexicon_name)


# --------------------------------------------------------------------------- #
#  (a) enrollment persists — teach() idempotent + survives save/load
# --------------------------------------------------------------------------- #
def test_enroll_persists_lex_entry_and_exemplar_idempotent():
    wa = WorldAdapter()
    lex = _fresh_lexicon()
    samp = _tone_word(WORDS["alpha"], seed=1)
    r1 = SE.enroll(wa, samp, "alpha", lexicon_name=lex)
    assert r1["n_exemplars"] == 1
    assert wa.s.node(r1["concept"])["attrs"].get("name") == "alpha"

    lex_entries_before = [n for n in wa.s.nodes("LexEntry")
                          if wa.s.node(n)["attrs"].get("surface") == "alpha"]
    assert len(lex_entries_before) == 1, "enroll() should mint exactly one LexEntry per word"

    # re-teaching the identical LexEntry content is a no-op (teach()'s own
    # idempotence, exercised through enroll()'s call to it).
    from domains.teach import teach
    res = teach(wa, "LexEntry",
               {"surface": "alpha", "concept": "alpha", "language": "en", "status": "confirmed"},
               category=SE.SEED_CATEGORY)
    assert res["saved"] is False, "re-teaching identical LexEntry content should be a no-op"

    m = json.loads(open(_SEED_PATH).read())
    kinds = {(n["type"], n["attrs"].get("word") or n["attrs"].get("surface") or n["attrs"].get("name"))
            for n in m["nodes"]}
    assert ("LexEntry", "alpha") in kinds
    assert ("Concept", "alpha") in kinds
    assert ("AcousticExemplar", "alpha") in kinds
    rule_names = {r["name"] for r in m["rules"]}
    assert rule_names == {"sg_denote_best_dist", "sg_denote_ground"}


def test_enroll_survives_save_load():
    wa = WorldAdapter()
    lex = _fresh_lexicon()
    samp = _tone_word(WORDS["beta"], seed=2)
    r = SE.enroll(wa, samp, "beta", lexicon_name=lex)
    sign = r["signs"][0]
    assert r["concept"] in set(wa.inner.neighbours(sign, "denotes"))

    fd, ckpt_path = tempfile.mkstemp(suffix=".save")
    os.close(fd)
    try:
        wa.save(ckpt_path)
        wa2 = WorldAdapter.load(ckpt_path)
        assert wa2.s.has_node(sign)
        assert r["concept"] in set(wa2.inner.neighbours(sign, "denotes")), \
            "the denotes edge is plain graph state — a checkpoint round-trip must keep it"
        lex_entries = [n for n in wa2.s.nodes("LexEntry")
                      if wa2.s.node(n)["attrs"].get("surface") == "beta"]
        assert lex_entries, "the taught LexEntry must also survive save/load"
        # the recognition rules themselves are graph engine state too (add_rule's
        # own store) — export_rules must still list them after reload.
        rule_names = {rr.get("name") for rr in wa2.inner.export_rules()}
        assert {"sg_denote_best_dist", "sg_denote_ground"} <= rule_names
    finally:
        os.unlink(ckpt_path)


def test_materialize_enrollments_rehydrates_after_fresh_boot():
    """The scenario save/load doesn't exercise: a FRESH seed boot (no
    checkpoint) that nonetheless loaded the taught AcousticExemplar/LexEntry/
    Concept records (seeds/speech_enrollment.json, via this test's own guard
    fixture + a manual load_seed_manifest here, since load_all_seeds()'s
    dependency closure resolution is out of scope for this bench). Rehydrating
    them (`materialize_enrollments`) must reconstruct a live, wired
    AcousticSign the recognition Rules can match against."""
    wa = WorldAdapter()
    lex = "materialize_test"
    samp = _tone_word(WORDS["gamma"], seed=3)
    SE.enroll(wa, samp, "gamma", lexicon_name=lex)

    # Simulate "fresh boot with only the taught seed data": a second agent that
    # loads JUST the persisted speech_enrollment manifest (no live AcousticSign
    # yet -- that's the point).
    from substrate.seed_loader import manifest_for
    wa2 = WorldAdapter()
    manifest = manifest_for(SE.SEED_CATEGORY)
    wa2.inner.load_seed_manifest(manifest, wa2.agent)
    assert any(wa2.s.node(n)["attrs"].get("word") == "gamma"
              for n in wa2.s.nodes("AcousticExemplar")), \
        "sanity: the taught AcousticExemplar loaded as inert data"
    assert not list(wa2.s.nodes("AcousticSign")), \
        "sanity: no live AcousticSign exists yet on this fresh agent"

    n = SE.materialize_enrollments(wa2, lexicon_name=lex)
    assert n >= 1
    signs = [s for s in wa2.s.nodes("AcousticSign")
            if wa2.s.node(s)["attrs"].get("label") == "gamma"]
    assert signs, "materialize_enrollments should mint a live AcousticSign for the taught word"
    concept = SE._concept_by_name(wa2, "gamma")
    assert concept is not None
    assert concept in set(wa2.inner.neighbours(signs[0], "denotes"))
    # idempotent within the same session
    n2 = SE.materialize_enrollments(wa2, lexicon_name=lex)
    assert n2 == 0


# --------------------------------------------------------------------------- #
#  (b)/(c) the graph-native recognition Rule: ground / reject
# --------------------------------------------------------------------------- #
def test_held_out_enrolled_word_gets_denotes_from_run_rules_alone():
    wa = WorldAdapter()
    lex = _fresh_lexicon()
    _enroll_words(wa, {"alpha": WORDS["alpha"]}, lex, n_exemplars=2, seed_base=10)

    vw = VW.VoiceWorld(wa, lexicon_name=lex, match_threshold=SE.DEFAULT_MATCH_THRESHOLD)
    held_out = _tone_word(WORDS["alpha"], seed=999)
    results = vw.hear(held_out, fs=VW.FS)
    sign = results[0]["sign"]
    assert sign is not None
    # Before run_rules: the freshly-minted sign is (honestly) ungrounded.
    assert not list(wa.inner.neighbours(sign, "denotes"))
    n_applied = wa.inner.run_rules()
    assert n_applied > 0, "the recognition Rules should have fired"
    denoted = list(wa.inner.neighbours(sign, "denotes"))
    assert denoted, "run_rules() alone should have grounded the held-out sign"
    assert wa.s.node(denoted[0])["attrs"].get("name") == "alpha"


def test_non_enrolled_word_stays_ungrounded_reject_path():
    wa = WorldAdapter()
    lex = _fresh_lexicon()
    _enroll_words(wa, WORDS, lex, n_exemplars=2, seed_base=20)

    vw = VW.VoiceWorld(wa, lexicon_name=lex, match_threshold=SE.DEFAULT_MATCH_THRESHOLD)
    novel = _tone_word(NEGATIVE_WORDS["epsilon"], seed=888)
    results = vw.hear(novel, fs=VW.FS)
    sign = results[0]["sign"]
    wa.inner.run_rules()
    assert not list(wa.inner.neighbours(sign, "denotes")), \
        "a non-enrolled word must stay ungrounded — the discriminative reject path"


# --------------------------------------------------------------------------- #
#  (d) the reply differs once grounding fires
# --------------------------------------------------------------------------- #
def test_reply_differs_when_grounded_vs_ungrounded():
    wa = WorldAdapter()
    lex = _fresh_lexicon()
    _enroll_words(wa, {"alpha": WORDS["alpha"]}, lex, n_exemplars=2, seed_base=30)
    vw = VW.VoiceWorld(wa, lexicon_name=lex, match_threshold=SE.DEFAULT_MATCH_THRESHOLD)

    grounded_out = vw.hear_and_reply(_tone_word(WORDS["alpha"], seed=777), fs=VW.FS)
    ungrounded_out = vw.hear_and_reply(_tone_word(NEGATIVE_WORDS["epsilon"], seed=776), fs=VW.FS)

    assert grounded_out and ungrounded_out
    grounded_reply = grounded_out[0]["reply"]
    ungrounded_reply = ungrounded_out[0]["reply"]
    assert ungrounded_reply == "ERROR: no communicative response could be generated.", ungrounded_reply
    assert "noted" not in grounded_reply.lower(), grounded_reply
    assert "heard: alpha" in grounded_reply, grounded_reply
    assert vw.grounded_words_for(grounded_out[0]["message"]) == ["alpha"]
    assert vw.grounded_words_for(ungrounded_out[0]["message"]) == []


# --------------------------------------------------------------------------- #
#  (e) recall / precision — reported plainly, over the synthetic vocabulary
# --------------------------------------------------------------------------- #
def test_recognition_recall_precision_report(capsys):
    wa = WorldAdapter()
    lex = _fresh_lexicon()
    _enroll_words(wa, WORDS, lex, n_exemplars=2, seed_base=100)
    vw = VW.VoiceWorld(wa, lexicon_name=lex, match_threshold=SE.DEFAULT_MATCH_THRESHOLD)

    n_trials_per_word = 8
    tp = fp = fn = 0
    for w, hz in WORDS.items():
        for i in range(n_trials_per_word):
            samp = _tone_word(hz, seed=1000 + i)
            r = vw.hear_and_reply(samp, fs=VW.FS)[0]
            got = set(vw.grounded_words_for(r["message"]))
            if w in got:
                tp += 1
            elif got:
                fp += 1
            else:
                fn += 1

    n_pos = tp + fp + fn
    recall = tp / n_pos if n_pos else float("nan")
    precision = tp / (tp + fp) if (tp + fp) else float("nan")

    neg_false_accepts = 0
    n_neg_trials = 8
    for w, hz in NEGATIVE_WORDS.items():
        for i in range(n_neg_trials):
            samp = _tone_word(hz, seed=2000 + i)
            r = vw.hear_and_reply(samp, fs=VW.FS)[0]
            if vw.grounded_words_for(r["message"]):
                neg_false_accepts += 1
    n_neg = len(NEGATIVE_WORDS) * n_neg_trials
    false_accept_rate = neg_false_accepts / n_neg

    print(f"\n  [speech_enrollment recall/precision report — synthetic tone-word fixtures, "
          f"real DtwTo/run_rules pipeline]")
    print(f"  enrolled vocabulary: {sorted(WORDS)} (2 exemplars each)")
    print(f"  positive trials: {n_pos} ({n_trials_per_word}/word x {len(WORDS)} words)")
    print(f"    TP={tp} FP(wrong word)={fp} FN(missed, stayed ungrounded)={fn}")
    print(f"    recall={recall:.3f} precision={precision:.3f}")
    print(f"  negative trials: {n_neg} ({n_neg_trials}/word x {len(NEGATIVE_WORDS)} "
          f"non-enrolled words)")
    print(f"    false_accepts={neg_false_accepts} false_accept_rate={false_accept_rate:.3f}")
    print(f"  threshold: DtwTo distance <= {VW.DENOTE_THRESHOLD} (calibrated: same-word "
          f"held-out distances measured ~1000-9600, different-word ~16000-42000 on this "
          f"pipeline's own cochlear features)")

    # Not asserted tight (per the task brief) -- these fixtures are cleanly
    # separable by construction, so a healthy pipeline should do well, but the
    # NUMBER above is the honest report, not this floor.
    assert recall >= 0.7, f"recall {recall:.3f} unexpectedly low for well-separated fixtures"
    assert false_accept_rate <= 0.3, f"false_accept_rate {false_accept_rate:.3f} unexpectedly high"


@pytest.mark.skipif(
    not os.path.isdir(LIBRISPEECH_DEV_CLEAN),
    reason="LibriSpeech dev-clean not present on this machine")
def test_real_speech_never_falsely_grounds_synthetic_vocabulary(capsys):
    """Honest cross-domain discriminative check: real LibriSpeech utterances
    (whole sentences — this repo has no word-level alignment for dev-clean,
    see module docstring) run through the exact same recognition Rules against
    the synthetic enrolled vocabulary above must NOT spuriously ground (wildly
    different signal shape). Not the headline recall number (that needs
    isolated-word same-speaker audio this environment can't produce — no
    Piper, no forced aligner) — reported honestly as a negative control only."""
    import glob
    wa = WorldAdapter()
    lex = _fresh_lexicon()
    _enroll_words(wa, WORDS, lex, n_exemplars=2, seed_base=40)
    vw = VW.VoiceWorld(wa, lexicon_name=lex, match_threshold=SE.DEFAULT_MATCH_THRESHOLD)

    flacs = sorted(glob.glob(os.path.join(LIBRISPEECH_DEV_CLEAN, "*", "*", "*.flac")))[:3]
    false_accepts = 0
    n = 0
    for flac in flacs:
        samples, sr = VW.load_audio_any(flac, fs=VW.FS)
        utts = VW.segment_utterances(samples, fs=sr)
        for utt in utts[:1]:
            r = vw.hear_and_reply(utt, fs=VW.FS)[0]
            n += 1
            if vw.grounded_words_for(r["message"]):
                false_accepts += 1
    print(f"\n  real LibriSpeech utterances tested: {n}, false_accepts against the "
          f"synthetic vocabulary: {false_accepts}")
    assert false_accepts == 0


# --------------------------------------------------------------------------- #
#  daemon boot sanity + the new /api/enroll route
# --------------------------------------------------------------------------- #
def _wait_for_http(url, timeout=20.0):
    deadline = time.monotonic() + timeout
    last_err = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2.0) as resp:
                return resp.status
        except (urllib.error.URLError, ConnectionError) as e:
            last_err = e
            time.sleep(0.3)
    raise RuntimeError(f"server never came up at {url}: {last_err}")


def test_daemon_boots_and_enroll_route_works():
    ckpt_dir = tempfile.mkdtemp(prefix="jbw_speech_ckpt_")
    port = 8799
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{os.path.join(ROOT, 'runners', 'dsl', 'python')}:{ROOT}"
    proc = subprocess.Popen(
        [sys.executable, os.path.join(ROOT, "scripts", "jabberwock_daemon.py"),
         "--seeds", "chat", "--ckpt-dir", ckpt_dir, "--http-port", str(port),
         "--socket", "", "--interval", "3600"],
        cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        _wait_for_http(f"http://127.0.0.1:{port}/api/status")

        samples = _tone_word(WORDS["alpha"], seed=50)
        wav_path = tempfile.mktemp(suffix=".wav")
        VW._write_wav(wav_path, samples, VW.FS)
        try:
            audio_b64 = base64.b64encode(open(wav_path, "rb").read()).decode("ascii")
        finally:
            os.unlink(wav_path)

        body = json.dumps({"label": "alpha", "audio_b64": audio_b64,
                          "filename": "alpha.wav"}).encode("utf-8")
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/enroll", data=body, method="POST",
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30.0) as resp:
            payload = json.loads(resp.read())
        assert payload["ok"] is True, payload
        assert payload["word"] == "alpha"
        assert payload["n_exemplars"] >= 1

        # missing fields -> a clean 400, not a crash.
        bad_req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/enroll", data=b"{}", method="POST",
            headers={"Content-Type": "application/json"})
        try:
            urllib.request.urlopen(bad_req, timeout=10.0)
            raised = False
        except urllib.error.HTTPError as e:
            raised = True
            assert e.code == 400
        assert raised
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10.0)
        except subprocess.TimeoutExpired:
            proc.kill()


# --------------------------------------------------------------------------- #
#  mock server: enrollment path is testable standalone (no real daemon)
# --------------------------------------------------------------------------- #
def test_mock_server_enroll_and_sse():
    port = 8788   # web/mock_server.py's fixed PORT
    env = dict(os.environ)
    proc = subprocess.Popen(
        [sys.executable, os.path.join(ROOT, "web", "mock_server.py")],
        cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        _wait_for_http(f"http://127.0.0.1:{port}/api/status")

        body = json.dumps({"label": "cat", "audio_b64": base64.b64encode(b"x").decode(),
                          "filename": "cat.wav"}).encode("utf-8")
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/enroll", data=body, method="POST",
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10.0) as resp:
            payload = json.loads(resp.read())
        assert payload == {"ok": True, "word": "cat", "n_exemplars": 1}

        # a second enrollment of the same word bumps the exemplar count
        with urllib.request.urlopen(req, timeout=10.0) as resp:
            payload2 = json.loads(resp.read())
        assert payload2["n_exemplars"] == 2

        # missing fields -> 400
        bad = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/enroll", data=b"{}", method="POST",
            headers={"Content-Type": "application/json"})
        try:
            urllib.request.urlopen(bad, timeout=10.0)
            raised = False
        except urllib.error.HTTPError as e:
            raised = True
            assert e.code == 400
        assert raised

        # static files: the enroll UI affordances are actually present
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/index.html", timeout=10.0) as resp:
            html = resp.read().decode("utf-8")
        assert 'id="enroll-form"' in html
        assert 'id="enroll-file"' in html
        assert 'id="enroll-record"' in html

        with urllib.request.urlopen(f"http://127.0.0.1:{port}/app.js", timeout=10.0) as resp:
            js = resp.read().decode("utf-8")
        assert "/api/enroll" in js
        assert "MediaRecorder" in js
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10.0)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
