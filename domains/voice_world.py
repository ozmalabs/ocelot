"""VoiceWorld — mic-in / speech-out world adapter (mechanical host I/O, per CLAUDE.md).

The VOICE loop end to end: microphone -> VAD boundary cut -> the agent's OWN
speech-understanding stack -> its reasoning (seeded Rules, run_rules) -> its
OWN reply construction -> (borrowed) audible playback. No LLM, no cloud
ASR/TTS. This module is a world adapter: it translates raw audio bytes into
substrate mutations and reads graph state back out to bytes. It makes no
agent decisions — comprehension and reply content are entirely the seeded
Rules on `substrate.world_adapter.WorldAdapter`.

REUSED PATHS (found by exploration, not reimplemented):

  INGEST  `WorldAdapter.ingest_audio_file` (substrate/world_adapter.py:279) —
          the canonical "hear a file" path: `substrate_rs.audio.open_container
          /add_stream/parse_stream/parse_native` (bitstream walk) then
          `substrate_rs.speech.ingest_speech` (detect_utterances -> cochlear
          extract_features -> acquire_sign/match_sign), which mints one
          Message{source:"audio"} -has_mention-> AcousticSign per detected
          utterance. `comprehend=True` also wires has_speech_act->statement +
          sent_by->interlocutor so the seeded intent/speech-bridge Rules
          (rule_acoustic_sign_refers_to_denoted_concept, tests/
          test_intent_migrated.py:111) can build an Intent from it — the
          SAME `AcousticSign as Mention, denotes->refers_to` shape the
          speech-bridge seed documents (seeds/lexical_access.json).
          `substrate_rs.speech.ingest_speech` (runners/dsl/python/
          substrate_rs/speech.py:683) is the SAME primitive
          scripts/jabberwock_continuous_stack.py's `harvest_stream` (commit
          c8df2dab, "WIRE THE FULL SPEECH-UNDERSTANDING STACK END-TO-END ON
          CONTINUOUS SPEECH") calls for its order-0 segmentation + cochlear
          feature extraction — we call the SAME Rust primitives via the
          SAME Python wrapper WorldAdapter already exposes, rather than
          re-running that script's heavy multi-utterance research pipeline
          (DTW word-form clustering / distributional split / category
          induction) per live turn: that pipeline needs dozens of utterances
          to fit its clustering and ~GiB-scale memory — it is a *batch
          research instrument* for measuring the stack's honest quality, not
          a per-turn comprehension mechanism. A live turn here is a SINGLE
          VAD-closed utterance, ingested exactly the way
          `WorldAdapter.ingest_audio_file` already ingests any audio file.

  REASON  `WorldAdapter.comprehend()` == `self.inner.run_rules()` — the
          seeded intent / referent-resolution / speech-bridge / (once
          `enable_replies()` loads it) conversation_reply Rules fire to a
          fixed point. No Python decision.

  REPLY   The SAME primitives `WorldAdapter.converse()` composes for text
          (substrate/world_adapter.py:561): `outbound_messages()` /
          `responds_to()` / `emit_reply()`. `converse()` itself is text-only
          (`receive_utterance` requires `text`); an audio Message has none,
          so `VoiceWorld.reply_for` applies those same three primitives
          directly to the audio Message instead of routing through
          `converse()`.

  HONEST STATE (see MEMORY ozma_trained_to_self_learning /
  jabberwock_continuous_stack.py's own verdict): word-level recognition on
  continuous speech is the known weak point — order-1 word-form purity is
  ~0.93 on forced-aligned (clean) segmentation but only ~0.37-0.38 on a
  live/earned continuous segmentation; cross-speaker recall on isolated
  words tops out around ~48% (the best "donkey=0" baseline). A raw
  AcousticSign only becomes a resolved Mention (refers_to a Concept) if it
  `denotes` a Concept already — i.e. if the lexicon has been grounded/taught
  for that sound. Absent that, `comprehend()` still produces a turn (the
  Message gets a speech_act-based adjacency-pair reply, e.g.
  statement -> acknowledgment -> "noted") but no CONTENT-level
  understanding. This module does not paper over that: it reports whatever
  `reply_for` actually returns, including None.

SYNTHESIS TIER — (a)/(b)/(c) per the task brief:
  (a) the agent's OWN from-scratch source-filter/formant voice (scripts/
      babble_genuine_voice_synth.py, babble_earned_voice.py, the "M" model)
      exists but its own gate numbers are near-chance recognition transfer
      (~0.03-0.10) — NOT demonstrated intelligible for arbitrary sentences.
      Not used.
  (b) XTTS is used elsewhere in this repo (scripts/synth_xtts_*.py) but
      ONLY as a caregiver/grounding-TARGET for training the agent's own
      voice (see MEMORY: "XTTS = caregiver grounding-target only"), always
      run from a separate XPU venv — the `TTS` package is NOT installed in
      this repo's default `.venv` (checked; ModuleNotFoundError), so pulling
      it in here would be a new dependency in this venv. Piper — an
      offline, already-installed neural TTS (`~/.cache/ozma/piper_voices/*
      .onnx`; `python -c "import piper"` succeeds) — fills the identical
      role and is ALREADY used by this repo as the agent's own "MOUTH"
      affordance (domains/speech_world.py: "MOUTH (piper TTS) — synth(word,
      voice) -> RAW audio the agent's OWN ear hears."). It renders arbitrary
      text intelligibly. We use Piper here for audible playback, but this
      is BORROWED synthesis (a pretrained neural TTS), not the agent's own
      earned voice — the WORDS spoken are the agent's own graph-authored
      reply content (`emit_reply`), only the waveform-rendering "mouth" is
      borrowed. Reported honestly, not silently blended into "the agent's
      own faculties."
  (c) Text-only (print the reply) is always available as a fallback via
      `speak()` returning None when piper/its voice model is absent.

SAMPLE RATE: 16 kHz mono. This is the agent's own EarConfig choice
(domains/speech_world.py: "16kHz = Nyquist 8kHz is the rate matched to its
80-7500Hz cochlea... at 8kHz every band above 4kHz was fed silence"), not a
value invented here.

VAD: a thin energy-threshold I/O-boundary classifier (CLAUDE.md explicitly
permits "a thin I/O-boundary classifier... when it is genuinely converting
an opaque external form into the smallest graph token"). It decides nothing
about MEANING — only where one utterance's audio ends and the next begins,
before either is handed to the real speech-understanding stack above.
"""
from __future__ import annotations

import os
import subprocess
import tempfile
import time
import wave
from typing import Iterator, Optional

import numpy as np

FS = 16000                     # the agent's own ear sample rate (see module docstring)
N_BANDS = 16                   # matches the other ingest_speech call sites in this repo
N_TIME_WINDOWS = 4
DEFAULT_VOICE_VARIANT = "lessac"


# --------------------------------------------------------------------------- #
#  WAV I/O (stdlib only) — mechanical translation between float samples and
#  the files `WorldAdapter.ingest_audio_file` / `aplay` expect.
# --------------------------------------------------------------------------- #
def _write_wav(path: str, samples: np.ndarray, fs: int) -> None:
    x = np.clip(np.asarray(samples, dtype=np.float32), -1.0, 1.0)
    pcm = (x * 32767.0).astype("<i2")
    with wave.open(path, "wb") as wv:
        wv.setnchannels(1)
        wv.setsampwidth(2)
        wv.setframerate(int(fs))
        wv.writeframes(pcm.tobytes())


def load_audio_any(path: str, fs: int = FS) -> tuple[np.ndarray, int]:
    """Decode ANY audio file (flac/wav/mp3/opus/...) to mono float32 @ `fs` Hz via ffmpeg
    (same transcode-then-read shape as scripts/jabberwock_continuous_stack.py's
    harvest_stream). World I/O only — no decision, no understanding here."""
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "in.wav")
        r = subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", path,
             "-ar", str(fs), "-ac", "1", "-sample_fmt", "s16", out],
            capture_output=True, timeout=120)
        if r.returncode != 0 or not os.path.exists(out):
            raise RuntimeError(
                f"ffmpeg failed to decode {path}: "
                f"{r.stderr.decode('utf-8', 'replace')[:300]}")
        with wave.open(out, "rb") as wv:
            raw = wv.readframes(wv.getnframes())
            sr = wv.getframerate()
    samples = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    return samples, sr


# --------------------------------------------------------------------------- #
#  VAD — thin I/O-boundary classifier (permitted by CLAUDE.md): utterance =
#  sustained energy above an adaptive floor, closed by ~0.6s of silence.
#  Two forms sharing the same threshold/close logic: `segment_utterances`
#  (offline, whole-array — used by --wav mode and tests) and `_StreamVAD`
#  (frame-by-frame, for live mic capture where the recording isn't available
#  upfront).
# --------------------------------------------------------------------------- #
def segment_utterances(samples: np.ndarray, fs: int = FS, *, frame_ms: float = 30.0,
                       energy_ratio: float = 3.0, min_utt_s: float = 0.2,
                       close_silence_s: float = 0.6,
                       floor_percentile: float = 20.0) -> list[np.ndarray]:
    """Split `samples` (float32 mono) into utterances by energy: a run of frames
    with RMS energy at least `energy_ratio`x the recording's `floor_percentile`
    energy starts an utterance; `close_silence_s` of continuous below-threshold
    frames closes it (the trailing silence is NOT included in the returned
    clip). Utterances shorter than `min_utt_s` are dropped. Pure function —
    the offline counterpart of `_StreamVAD`, used by tests and --wav mode."""
    samples = np.asarray(samples, dtype=np.float32)
    frame_len = max(1, int(fs * frame_ms / 1000.0))
    n_frames = len(samples) // frame_len
    if n_frames == 0:
        return []
    frames = samples[:n_frames * frame_len].reshape(n_frames, frame_len)
    energy = np.sqrt(np.mean(frames.astype(np.float64) ** 2, axis=1) + 1e-12)
    floor = float(np.percentile(energy, floor_percentile)) + 1e-6
    thresh = floor * energy_ratio
    close_frames = max(1, int(round(close_silence_s * 1000.0 / frame_ms)))
    min_frames = max(1, int(round(min_utt_s * 1000.0 / frame_ms)))

    utts: list[np.ndarray] = []
    in_utt = False
    start = 0
    silence_run = 0
    for i, e in enumerate(energy):
        active = e >= thresh
        if not in_utt:
            if active:
                in_utt = True
                start = i
                silence_run = 0
        else:
            if active:
                silence_run = 0
            else:
                silence_run += 1
                if silence_run >= close_frames:
                    end = i - silence_run + 1
                    if end - start >= min_frames:
                        utts.append(samples[start * frame_len:end * frame_len])
                    in_utt = False
    if in_utt:
        end = n_frames - silence_run if silence_run else n_frames
        if end - start >= min_frames:
            utts.append(samples[start * frame_len:end * frame_len])
    return utts


class _StreamVAD:
    """Frame-by-frame counterpart of `segment_utterances`, for live mic capture
    (no whole-recording energy percentile available upfront — the noise floor
    is tracked online while idle instead)."""

    def __init__(self, fs: int = FS, frame_ms: float = 30.0, energy_ratio: float = 3.0,
                min_utt_s: float = 0.2, close_silence_s: float = 0.6,
                floor_alpha: float = 0.05):
        self.fs = fs
        self.frame_len = max(1, int(fs * frame_ms / 1000.0))
        self.energy_ratio = energy_ratio
        self.close_frames = max(1, int(round(close_silence_s * 1000.0 / frame_ms)))
        self.min_frames = max(1, int(round(min_utt_s * 1000.0 / frame_ms)))
        self.floor_alpha = floor_alpha
        self.floor: Optional[float] = None
        self.in_utt = False
        self.buf: list[np.ndarray] = []
        self.silence_run = 0

    def push(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """Feed one frame_len-sample float32 frame. Returns a completed utterance
        array, or None."""
        e = float(np.sqrt(np.mean(frame.astype(np.float64) ** 2) + 1e-12))
        if self.floor is None:
            self.floor = e
        active = e >= self.floor * self.energy_ratio
        out = None
        if not self.in_utt:
            self.floor = (1.0 - self.floor_alpha) * self.floor + self.floor_alpha * e
            if active:
                self.in_utt = True
                self.buf = [frame]
                self.silence_run = 0
        else:
            self.buf.append(frame)
            if active:
                self.silence_run = 0
            else:
                self.silence_run += 1
                if self.silence_run >= self.close_frames:
                    kept = self.buf[:len(self.buf) - self.silence_run]
                    if len(kept) >= self.min_frames:
                        out = np.concatenate(kept)
                    self.in_utt = False
                    self.buf = []
                    self.silence_run = 0
        return out

    def flush(self) -> Optional[np.ndarray]:
        """Force-close whatever utterance is open (e.g. on stream end)."""
        out = None
        if self.in_utt and len(self.buf) >= self.min_frames:
            out = np.concatenate(self.buf)
        self.in_utt = False
        self.buf = []
        self.silence_run = 0
        return out


def capture_utterances_from_mic(fs: int = FS, *, frame_ms: float = 30.0,
                                device: Optional[str] = None, stop_event=None,
                                energy_ratio: float = 3.0, min_utt_s: float = 0.2,
                                close_silence_s: float = 0.6,
                                arecord_bin: str = "arecord") -> Iterator[np.ndarray]:
    """Live mic VAD segmenter: launches `arecord` (raw S16_LE mono PCM at `fs`), runs
    the SAME threshold/close-silence state machine as `segment_utterances` frame by
    frame, and YIELDS each completed utterance as a float32 [-1,1] array. Generator;
    stops when `stop_event` (a threading.Event) is set or the subprocess exits.
    Mechanical world I/O — no decisions beyond the boundary cut. Raises RuntimeError
    if `arecord` can't be started (e.g. no capture device)."""
    frame_len = max(1, int(fs * frame_ms / 1000.0))
    cmd = [arecord_bin, "-q", "-f", "S16_LE", "-r", str(fs), "-c", "1", "-t", "raw"]
    if device:
        cmd += ["-D", device]
    cmd += ["-"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    vad = _StreamVAD(fs=fs, frame_ms=frame_ms, energy_ratio=energy_ratio,
                     min_utt_s=min_utt_s, close_silence_s=close_silence_s)
    nbytes = frame_len * 2
    try:
        time.sleep(0.05)
        if proc.poll() is not None:
            err = proc.stderr.read().decode("utf-8", "replace")
            raise RuntimeError(f"arecord failed to start: {err.strip()}")
        while stop_event is None or not stop_event.is_set():
            buf = proc.stdout.read(nbytes)
            if not buf:
                break
            if len(buf) < nbytes:
                buf = buf + b"\x00" * (nbytes - len(buf))
            frame = np.frombuffer(buf, dtype="<i2").astype(np.float32) / 32768.0
            utt = vad.push(frame)
            if utt is not None:
                yield utt
        tail = vad.flush()
        if tail is not None:
            yield tail
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=1.0)
        except subprocess.TimeoutExpired:
            proc.kill()


# --------------------------------------------------------------------------- #
#  Synthesis — borrowed Piper voice (see module docstring: tier (b), not the
#  agent's own earned model). Optional at every call site: falls back to None
#  (tier (c), text-only) if piper or the voice model isn't installed.
# --------------------------------------------------------------------------- #
_PIPER_VOICE_DIR = os.environ.get(
    "PIPER_VOICE_DIR", os.path.expanduser("~/.cache/ozma/piper_voices"))
_PIPER_MODEL_FILES = {
    "lessac": "en_US-lessac-medium.onnx",
    "amy": "en_US-amy-medium.onnx",
    "ryan": "en_US-ryan-medium.onnx",
}
_piper_voice_cache: dict = {}


def _piper_model_path(variant: str) -> str:
    fn = _PIPER_MODEL_FILES.get(variant, variant if variant.endswith(".onnx") else variant + ".onnx")
    return os.path.join(_PIPER_VOICE_DIR, fn)


def piper_available(variant: str = DEFAULT_VOICE_VARIANT) -> bool:
    try:
        import piper  # noqa: F401
    except Exception:
        return False
    return os.path.exists(_piper_model_path(variant))


def synth_speech(text: str, variant: str = DEFAULT_VOICE_VARIANT) -> Optional[tuple[np.ndarray, int]]:
    """Render `text` to (int16 PCM samples, sample_rate) via the installed Piper
    voice. Returns None if piper / the named voice model isn't installed (the
    caller falls back to text-only). BORROWED synthesis — see module docstring."""
    try:
        from piper import PiperVoice, SynthesisConfig
    except Exception:
        return None
    path = _piper_model_path(variant)
    if not os.path.exists(path):
        return None
    v = _piper_voice_cache.get(path)
    if v is None:
        v = PiperVoice.load(path)
        _piper_voice_cache[path] = v
    cfg = SynthesisConfig(length_scale=1.0, noise_scale=0.667,
                          noise_w_scale=0.8, normalize_audio=False)
    try:
        chunks = list(v.synthesize(text, cfg))
    except Exception:
        return None
    if not chunks:
        return None
    sr = chunks[0].sample_rate
    audio = np.concatenate([c.audio_int16_array for c in chunks]).astype(np.int16)
    if audio.size == 0:
        return None
    return audio, sr


def play_pcm(samples: np.ndarray, sr: int, player: str = "aplay") -> bool:
    """Play int16 PCM samples via `aplay` (or `ffplay`). Returns False (silently)
    if the player binary isn't available or playback fails — never raises, this
    is best-effort output."""
    fd, path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    try:
        with wave.open(path, "wb") as wv:
            wv.setnchannels(1)
            wv.setsampwidth(2)
            wv.setframerate(int(sr))
            wv.writeframes(np.asarray(samples, dtype="<i2").tobytes())
        cmd = [player, "-q", path] if player == "aplay" else [player, "-nodisp", "-autoexit", "-loglevel", "quiet", path]
        r = subprocess.run(cmd, capture_output=True)
        return r.returncode == 0
    except Exception:
        return False
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


# --------------------------------------------------------------------------- #
#  PER-TURN RECOGNITION — graph-native (no Python matcher). An AcousticSign's
#  `features` (the flattened n_bands*n_time_windows cochlear energy summary
#  `substrate_rs.speech.extract_features` already computes) is reshaped into
#  a (n_time_windows, n_bands) frame TRAJECTORY — the Tuple-of-Tuples shape
#  the held `DtwTo` Term reads (mirrors the existing `axs_heard_feat`/
#  `axs_synth_feat` convention: `array.tolist()` onto a node attr, consumed
#  by PointSetDist elsewhere, e.g. seeds/semantic_relations.json's
#  relate_confusable rule and seeds/viterbi_autonomous.json's set_emission).
#  This reshape is mechanical re-encoding of data ingest_speech already
#  computed — no decision, same spirit as CLAUDE.md's "ingest: mechanical
#  translation" — the DECISION (which exemplar, is it close enough) is two
#  Rules run by `run_rules()`, not Python:
#
#    sg_denote_best_dist — for every AcousticSign in a Lexicon that has no
#      `denotes` edge yet, compute the MIN DtwTo distance to every OTHER
#      sign in the same Lexicon that already denotes something (an enrolled
#      exemplar), via a graph `MinOver`/`Filter` reduction (same shape as
#      seeds/viterbi_autonomous.json's `vit_step`/`finish_forward` MaxOver
#      reductions) — stores it on the sign as `denote_best_dist`.
#
#    sg_denote_ground — grounds the sign to the (an) exemplar's Concept
#      whose DtwTo distance EQUALS that stored best (the argmin, found the
#      same way seeds/viterbi_autonomous.json's `seed_terminal` finds the
#      argmax hypothesis: compare each candidate's value against the
#      already-reduced best), provided that best is under `DENOTE_THRESHOLD`
#      — else the sign stays honestly ungrounded (the reject path).
#
#  DENOTE_THRESHOLD was measured, not guessed: on this pipeline's own
#  cochlear features (16 bands x 4 time windows) with genuinely-distinct
#  AcousticSign nodes per hearing (acquire_sign's cosine pre-merge disabled
#  via a strict match_threshold so DTW does the real work), same-word
#  held-out distances landed ~1000-9600 and different-word distances
#  ~16000-42000 (see tests/test_speech_grounding.py's calibration numbers,
#  and the module's own recognition-accuracy report) — 15000.0 sits with
#  comfortable margin on both sides.
# --------------------------------------------------------------------------- #
DENOTE_THRESHOLD = 15000.0

_RECOGNITION_RULE_NAMES = ("sg_denote_best_dist", "sg_denote_ground")


def _V(name):
    return {"type": "Var", "name": name}


def _A(name, key):
    return {"type": "Attr", "node": _V(name), "key": key}


def _L(value):
    return {"type": "Lit", "value": value}


def recognition_rules(threshold: float = DENOTE_THRESHOLD) -> list[dict]:
    """Build the two per-turn recognition Rules (see block docstring above).
    A function (not a module-level constant) so a caller can persist/install a
    retuned threshold without editing this file."""
    rule1 = {
        "name": "sg_denote_best_dist",
        "match": [["lex", "has_entry", "sign"]],
        "where": {"type": "And", "items": [
            {"type": "Eq", "a": {"type": "Count", "source": {
                "type": "Neighbours", "node": _V("sign"), "edge_type": "denotes",
                "any_type": False}}, "b": _L(0)},
            {"type": "Not", "arg": {"type": "Eq", "a": _A("sign", "denote_scored"),
                                    "b": _L(1.0)}},
        ]},
        "effects": [
            ["set_attr", "sign", "denote_best_dist", {"__term__": {
                "type": "MinOver", "var_name": "e", "default": _L(1.0e9),
                "source": {"type": "Filter", "source": {
                    "type": "Neighbours", "node": _V("lex"), "edge_type": "has_entry",
                    "any_type": False},
                    "var_name": "e", "predicate": {"type": "And", "items": [
                        {"type": "Not", "arg": {"type": "Eq", "a": _V("e"), "b": _V("sign")}},
                        {"type": "Gt", "a": {"type": "Count", "source": {
                            "type": "Neighbours", "node": _V("e"), "edge_type": "denotes",
                            "any_type": False}}, "b": _L(0)},
                    ]}},
                "value": {"type": "DtwTo", "a": _A("sign", "frames"), "b": _A("e", "frames")},
            }}],
            ["set_attr", "sign", "denote_scored", 1.0],
        ],
    }
    rule2 = {
        "name": "sg_denote_ground",
        "match": [["lex", "has_entry", "sign"], ["lex", "has_entry", "ex"],
                  ["ex", "denotes", "concept"]],
        "where": {"type": "And", "items": [
            {"type": "Not", "arg": {"type": "Eq", "a": _V("sign"), "b": _V("ex")}},
            {"type": "Eq", "a": _A("sign", "denote_scored"), "b": _L(1.0)},
            {"type": "Eq", "a": {"type": "Count", "source": {
                "type": "Neighbours", "node": _V("sign"), "edge_type": "denotes",
                "any_type": False}}, "b": _L(0)},
            {"type": "Lte", "a": {"type": "DtwTo", "a": _A("sign", "frames"),
                                  "b": _A("ex", "frames")}, "b": _A("sign", "denote_best_dist")},
            {"type": "Lte", "a": _A("sign", "denote_best_dist"), "b": _L(float(threshold))},
        ]},
        "effects": [["add_edge", "sign", "denotes", "concept"]],
    }
    return [rule1, rule2]


def _installed_rule_names(wa) -> set:
    try:
        return {r.get("name") for r in wa.inner.export_rules() if isinstance(r, dict)}
    except Exception:
        return set()


def install_recognition_rules(wa, threshold: float = DENOTE_THRESHOLD) -> int:
    """LIVE-install the per-turn recognition Rules (idempotent by name — safe to
    call on every VoiceWorld construction). Does NOT persist to a seed file
    (that is a teaching action; see domains/speech_enrollment.py, which calls
    this too and additionally writes the rule JSON to seeds/speech_enrollment.json
    so a fresh boot has it). Returns how many rules were newly added."""
    installed = _installed_rule_names(wa)
    added = 0
    for r in recognition_rules(threshold):
        if r["name"] not in installed:
            wa.inner.add_rule(r)
            added += 1
    return added


def ensure_sign_frames(wa, sign_nid, n_bands: int = N_BANDS,
                       n_time_windows: int = N_TIME_WINDOWS) -> bool:
    """Give an AcousticSign its DTW-ready frame trajectory: reshape the
    `features` bytes `extract_features`/`acquire_sign` already wrote into a
    (n_time_windows, n_bands) nested list (the Tuple-of-Tuples `DtwTo` reads),
    stored as the `frames` attr. Mechanical re-encoding of existing graph
    data — no decision. Idempotent (no-op if `frames` already present).
    Returns True if it set the attr."""
    attrs = wa.s.node(sign_nid)["attrs"]
    if attrs.get("frames") is not None:
        return False
    raw = attrs.get("features")
    if raw is None:
        return False
    arr = np.frombuffer(raw, dtype=np.float32)
    if arr.size != n_bands * n_time_windows:
        return False
    frames = arr.reshape(n_bands, n_time_windows).T.tolist()
    wa.s.set_attr(sign_nid, "frames", frames)
    return True


# --------------------------------------------------------------------------- #
#  VoiceWorld — the adapter proper: ingest an utterance, hand off to the
#  agent's own comprehension, read the reply back out, (optionally) speak it.
# --------------------------------------------------------------------------- #
class VoiceWorld:
    """Mic-in / speech-out world adapter over a booted `WorldAdapter`. Every
    method is mechanical translation or a pure graph query — see the module
    docstring for exactly which existing WorldAdapter/substrate_rs primitives
    each one composes. No agent decisions live here."""

    def __init__(self, wa, *, lexicon_name: str = "default", fs: int = FS,
                n_bands: int = N_BANDS, n_time_windows: int = N_TIME_WINDOWS,
                match_threshold: float = 0.80):
        self.wa = wa
        self.lexicon_name = lexicon_name
        self.fs = fs
        self.n_bands = n_bands
        self.n_time_windows = n_time_windows
        self.match_threshold = match_threshold
        self.wa.enable_replies()          # loads conversation_reply once; idempotent
        self.wa.install_register_lexicon()  # idempotent; feeds surface_for's idiomatic surfaces
        install_recognition_rules(self.wa)  # idempotent; the per-turn DTW grounding Rules

    def hear(self, samples: np.ndarray, fs: Optional[int] = None) -> list[dict]:
        """Ingest one VAD-closed utterance: write it to a wav, run it through
        `WorldAdapter.ingest_audio_file` (comprehend=True) — the EXACT audio decode
        + speech recognition chain (see module docstring). Also gives every
        (new-or-matched) sign its DTW-ready `frames` attr (`ensure_sign_frames` —
        mechanical reshape of data already computed) so the recognition Rules have
        something to compare once the caller runs rules. Does NOT run rules itself;
        the caller ticks/comprehends (so a daemon's own tick loop stays in control of
        WHEN the graph advances — the grounding Rules fire as part of that same
        run_rules fixpoint, not here). Returns the ingest_audio_file results:
        [{"message", "utterance", "sign", "is_new"}, ...]."""
        fs = fs or self.fs
        fd, path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        try:
            _write_wav(path, samples, fs)
            results = self.wa.ingest_audio_file(
                path, lexicon_name=self.lexicon_name,
                match_threshold=self.match_threshold, n_bands=self.n_bands,
                n_time_windows=self.n_time_windows, sample_rate=fs, comprehend=True)
            for r in results:
                if r["sign"] is not None:
                    ensure_sign_frames(self.wa, r["sign"], n_bands=self.n_bands,
                                       n_time_windows=self.n_time_windows)
            return results
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass

    def grounded_words_for(self, mid) -> list[str]:
        """Pure query: the Concept names any of `mid`'s Mentions `denotes` (i.e.
        what the per-turn recognition Rules grounded this turn) — the "heard: X"
        signal a console/SSE layer surfaces. [] if nothing grounded yet."""
        out = []
        for mn in self.wa.inner.neighbours(mid, "has_mention"):
            for c in self.wa.inner.neighbours(mn, "denotes"):
                name = self.wa.s.node(c)["attrs"].get("name")
                if name:
                    out.append(name)
        return out

    def reply_for(self, mid) -> Optional[str]:
        """Pure query (call AFTER comprehend()/tick()): the surface text of the
        reply Message that responds_to `mid`, via the same primitives
        `WorldAdapter.converse()` composes for text (outbound_messages /
        responds_to), then rendered to an idiomatic surface via
        `WorldAdapter.surface_for` (register-matched surfaces, e.g.
        acknowledgment -> "noted", greeting -> "hello" — `install_register_
        lexicon()` was called once in `__init__`), falling back to
        `emit_reply`'s relational render (which, absent an installed Language/
        lexicon, returns the bare speech-act concept name, e.g.
        "acknowledgment" — reported as-is, not papered over) if `surface_for`
        has nothing. None if no reply exists yet.

        When `mid`'s own Mention `denotes` a Concept (the per-turn recognition
        Rule grounded it — see `install_recognition_rules`), the reply's plain
        adjacency-pair surface ("noted") is enriched with what was actually
        recognised ("noted — heard: cat"): this is what makes the honest
        content-vs-no-content distinction gate item (d) checks for. Pure
        rendering of graph state already resolved by the Rules — no new
        decision (mirrors `emit_reply`/`surface_for`'s existing conditionals)."""
        replies = [r for r in self.wa.outbound_messages() if mid in self.wa.responds_to(r)]
        if not replies:
            return None
        reply = replies[0]
        surface = None
        sa = list(self.wa.inner.neighbours(reply, "has_speech_act"))
        if sa:
            name = self.wa.s.node(sa[0])["attrs"].get("name")
            surface = self.wa.surface_for(name) if name else None
        if surface is None:
            surface = self.wa.emit_reply(reply)
        words = self.grounded_words_for(mid)
        if words:
            heard = "heard: " + ", ".join(words)
            return f"{surface} — {heard}" if surface else heard
        return surface

    def hear_and_reply(self, samples: np.ndarray, fs: Optional[int] = None) -> list[dict]:
        """`hear()` + `comprehend()` + `reply_for()` for every ingested Message —
        the single-utterance audio equivalent of `WorldAdapter.converse()`. Used
        by --wav mode and the interactive session (the daemon hook instead ticks
        the FULL agent between hear() and reply_for(), see jabberwock_daemon.py)."""
        results = self.hear(samples, fs=fs)
        self.wa.comprehend()
        return [{**r, "reply": self.reply_for(r["message"])} for r in results]

    def speak(self, text: str, variant: str = DEFAULT_VOICE_VARIANT,
             play: bool = True) -> Optional[tuple[np.ndarray, int]]:
        """Synth `text` via the installed Piper voice and (optionally) play it.
        Returns (int16 samples, sample_rate), or None if no synthesis path is
        available (tier (c): the caller should just print the text)."""
        got = synth_speech(text, variant=variant)
        if got is None:
            return None
        samples, sr = got
        if play:
            from domains.information_commitment import assess
            from domains.shape_tube import goal_manifold, goal_projection
            gate = assess(
                self.wa,
                commit={
                    "name": "voice_emit", "expected_goal_work": 1.0,
                    "projection": goal_projection("voice_emit_goal", active=False, action_count=1, intervention_magnitude=1.0),
                },
                wait={"delay_cost": 0.1, "projection": goal_projection("voice_emit_goal", active=False, action_count=0, intervention_magnitude=0.0)},
                refine={"refinement_cost": 1.0, "projection": goal_projection("voice_emit_goal", active=False, action_count=1, intervention_magnitude=0.5)},
                manifold=goal_manifold("voice_emit_goal"),
                retain_trace=False,
            )
            if gate["decision"] == "commit" and gate["authorized"]:
                play_pcm(samples, sr)
        return samples, sr


__all__ = [
    "FS", "N_BANDS", "N_TIME_WINDOWS", "DEFAULT_VOICE_VARIANT",
    "load_audio_any", "segment_utterances", "capture_utterances_from_mic",
    "piper_available", "synth_speech", "play_pcm", "VoiceWorld",
]
