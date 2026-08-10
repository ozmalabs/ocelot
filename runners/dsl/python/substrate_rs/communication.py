"""The pragmatic / prosodic / register layer of speech.

A separate module from :mod:`substrate_rs.speech` because biology
splits the streams. Left-hemisphere (Wernicke's area) processes
linguistic content — words, syntax, semantics — and is what
``speech.py`` models with its Sign / Lexicon shape. Right-
hemisphere homologs (and structures like the right superior
temporal sulcus, the insula, anterior cingulate) process
*everything else speech encodes*: prosody, voice quality, speaker
identity, affect, communicative intent, sarcasm.

The dissociation is clinically established. **Aphasia** (Wernicke's
damage) flattens linguistic content but preserves prosody —
patients can still tell anger from calm in someone's voice.
**Aprosodia** (right-hemisphere damage) does the inverse: linguistic
content intact, but the patient hears *what* was said and not *how*.
Two cortical streams, two substrate modules.

The motivating benchmark: the Dead Parrot sketch (Monty Python,
1969). Read the script flat and it's nonsense; the comedy lives
entirely in what text throws away — register escalation, prosodic
exaggeration, intentional irony, turn-taking pacing. The mark of
success for this module is being able to discriminate a synthetic
two-speaker dialogue with asymmetric affect trajectories *without
ever transcribing a word*.

What this module extracts
-------------------------

Per Utterance (from :mod:`substrate_rs.speech`):

* **ProsodyProfile** — F0 (pitch) mean/range/slope/contour bucket
  + energy envelope + speaking rate.
* **Affect** — categorical: ``calm`` / ``agitated`` / ``pressed`` /
  ``breathy`` / ``pleading``. Combines pitch range, intensity,
  spectral tilt.
* **SpeechAct** — ``assertion`` / ``question`` / ``denial`` /
  ``accusation`` / ``insistence``. From final-pitch contour
  direction + intensity pattern + repetition.
* **Register** — ``formal`` / ``casual`` / ``florid`` / ``clipped``.
  From speaking-rate variability + articulation precision (spectral
  coherence).
* **Speaker** — cluster identity in (F0 median, F1/F2 ratio)
  space against a Speaker lexicon the agent maintains.
* **TurnDynamics** — gap to previous utterance, overlap flag,
  interruption flag.
* **IronicStance** — heuristic boolean. Triggered when pitch range
  is grossly inconsistent with the affect classification (e.g.,
  formal register × very wide pitch range = mocking / sarcastic) OR
  when stress pattern is atypical for the speech act.
* **Stance** — the aggregate. One Stance per utterance binding
  speaker + affect + speech_act + register + irony_flag. The agent
  reasons about the *communicative situation*, not just the words.
"""
from __future__ import annotations

import math
from typing import Any, Optional

import numpy as np

from . import Substrate as _PySubstrate
from . import audio as _audio
from . import speech as _speech


# --- Node + edge type constants ----------------------------------------

PROSODY_PROFILE = "ProsodyProfile"
AFFECT = "Affect"
SPEECH_ACT = "SpeechAct"
REGISTER = "Register"
SPEAKER = "Speaker"
SPEAKER_LEXICON = "SpeakerLexicon"
TURN_DYNAMICS = "TurnDynamics"
STANCE = "Stance"

# Graph-resident decision rules — one PragmaticConcept node per
# affect / speech-act / register / ironic category. Each carries a
# `definition_term` attr holding a DSL Term-tree the classifier
# evaluates against the ProsodyProfile (and, for ironic-stance,
# the Affect / SpeechAct / Register nodes too). The agent reads /
# edits these like any other graph data — *no Python if/elif*.
PRAGMATIC_CONCEPT = "PragmaticConcept"

HAS_PROSODY = "has_prosody"
HAS_AFFECT = "has_affect"
HAS_SPEECH_ACT = "has_speech_act"
HAS_REGISTER = "has_register"
HAS_SPEAKER = "has_speaker"
HAS_TURN_DYNAMICS = "has_turn_dynamics"
HAS_STANCE = "has_stance"
HAS_SPEAKER_ENTRY = "has_speaker_entry"
FOLLOWS_UTTERANCE = "follows_utterance"


# --- Categorical buckets (kept small + agent-readable) ------------------

AFFECT_CATEGORIES = ("calm", "agitated", "pressed", "breathy", "pleading", "flat")
SPEECH_ACT_CATEGORIES = ("assertion", "question", "denial", "accusation", "insistence")
REGISTER_CATEGORIES = ("formal", "casual", "florid", "clipped")


def _native(s):
    return s._inner if isinstance(s, _PySubstrate) else s


# --- Grammar seeding ---------------------------------------------------

def seed_pragmatic_concepts(s) -> dict[str, list]:
    """Mint graph-resident decision rules — one Concept node per
    affect / speech-act / register / ironic category. Each carries
    a ``definition_term`` attr: a DSL Term-tree evaluated against
    the ProsodyProfile (and, for ironic, also against Affect /
    SpeechAct / Register).

    Returns a dict mapping ``"affect"`` / ``"speech_act"`` /
    ``"register"`` / ``"ironic"`` to the list of Concept NodeIDs in
    priority order. The classifiers below walk this list and
    short-circuit on the first match — same semantics as the prior
    Python if/elif chain, but now the rules are graph data the agent
    reads via ``Attr(Var, "definition_term")`` and edits by mutating
    the Lit-node thresholds inside the Term-tree.

    Idempotent: re-seeding adds duplicate Concepts (no de-dup here;
    the classifier dispatch handles equal-priority by taking the
    first match seen). Call once at substrate setup.

    Default catch-all categories (``calm`` / ``assertion`` /
    ``casual``) are NOT minted as Concepts — they're the fall-through
    when no other rule fires. The agent can still mint them as
    explicit Concepts to give them definitions later.
    """
    from . import And, Or, Eq, Lt, Gt, Attr, Var, Lit, Not, Abs
    inner = _native(s)

    def define(label: str, kind: str, definition_term, priority: int) -> Any:
        return inner.add_node(PRAGMATIC_CONCEPT, {
            "label": label,
            "kind": kind,
            "definition_term": definition_term.to_dict(),
            "priority": int(priority),
            "origin": "seeded",
        })

    out: dict[str, list] = {"affect": [], "speech_act": [],
                            "register": [], "ironic": []}

    # --- Affect concepts. ProsodyProfile bound as `p`. ---
    out["affect"].append(define(
        "pleading", "affect",
        And(items=[
            Eq(Attr(Var("p"), "f0_contour"), Lit("rising")),
            Gt(Attr(Var("p"), "f0_range_hz"), Lit(40.0)),
        ]), priority=10))
    out["affect"].append(define(
        "agitated", "affect",
        And(items=[
            Gt(Attr(Var("p"), "f0_range_hz"), Lit(40.0)),
            Gt(Attr(Var("p"), "energy_mean"), Lit(0.15)),
        ]), priority=20))
    out["affect"].append(define(
        "pressed", "affect",
        Gt(Attr(Var("p"), "energy_mean"), Lit(0.20)),
        priority=30))
    out["affect"].append(define(
        "breathy", "affect",
        Lt(Attr(Var("p"), "energy_mean"), Lit(0.04)),
        priority=40))
    out["affect"].append(define(
        "flat", "affect",
        And(items=[
            Lt(Attr(Var("p"), "f0_range_hz"), Lit(15.0)),
            Lt(Attr(Var("p"), "energy_std"), Lit(0.01)),
        ]), priority=50))
    # "calm" is the fall-through default — no Concept.

    # --- Speech-act concepts. ProsodyProfile bound as `p`. ---
    out["speech_act"].append(define(
        "question", "speech_act",
        Gt(Attr(Var("p"), "f0_tail_slope"), Lit(1.5)),
        priority=10))
    out["speech_act"].append(define(
        "accusation", "speech_act",
        And(items=[
            Gt(Attr(Var("p"), "energy_max"), Lit(0.25)),
            Gt(Attr(Var("p"), "f0_range_hz"), Lit(100.0)),
        ]), priority=20))
    out["speech_act"].append(define(
        "insistence", "speech_act",
        And(items=[
            Gt(Attr(Var("p"), "energy_mean"), Lit(0.12)),
            Lt(Abs(Attr(Var("p"), "f0_tail_slope")), Lit(0.5)),
        ]), priority=30))
    out["speech_act"].append(define(
        "denial", "speech_act",
        And(items=[
            Lt(Attr(Var("p"), "f0_tail_slope"), Lit(-1.5)),
            Gt(Attr(Var("p"), "energy_mean"), Lit(0.08)),
        ]), priority=40))
    # "assertion" is the fall-through default.

    # --- Register concepts. ProsodyProfile bound as `p`. ---
    out["register"].append(define(
        "clipped", "register",
        And(items=[
            Gt(Attr(Var("p"), "speaking_rate_proxy"), Lit(15.0)),
            Lt(Attr(Var("p"), "f0_range_hz"), Lit(50.0)),
        ]), priority=10))
    out["register"].append(define(
        "florid", "register",
        And(items=[
            Lt(Attr(Var("p"), "speaking_rate_proxy"), Lit(8.0)),
            Gt(Attr(Var("p"), "f0_range_hz"), Lit(80.0)),
        ]), priority=20))
    out["register"].append(define(
        "formal", "register",
        Lt(Attr(Var("p"), "speaking_rate_proxy"), Lit(6.0)),
        priority=30))
    # "casual" is the fall-through default.

    # --- Ironic-stance concepts. The Term references multiple bound
    # variables: `p` (ProsodyProfile), `aff` (Affect), `act`
    # (SpeechAct), `reg` (Register). The dispatcher binds all four
    # before evaluating.
    out["ironic"].append(define(
        "ironic_formal_wide", "ironic",
        And(items=[
            Or(items=[
                Eq(Attr(Var("reg"), "label"), Lit("formal")),
                Eq(Attr(Var("reg"), "label"), Lit("florid")),
            ]),
            Gt(Attr(Var("p"), "f0_range_hz"), Lit(150.0)),
        ]), priority=10))
    out["ironic"].append(define(
        "ironic_incongruent_calm_accusation", "ironic",
        And(items=[
            Eq(Attr(Var("aff"), "label"), Lit("calm")),
            Eq(Attr(Var("act"), "label"), Lit("accusation")),
        ]), priority=20))
    out["ironic"].append(define(
        "ironic_incongruent_agitated_assertion", "ironic",
        And(items=[
            Eq(Attr(Var("aff"), "label"), Lit("agitated")),
            Eq(Attr(Var("act"), "label"), Lit("assertion")),
        ]), priority=30))
    out["ironic"].append(define(
        "ironic_incongruent_pleading_denial", "ironic",
        And(items=[
            Eq(Attr(Var("aff"), "label"), Lit("pleading")),
            Eq(Attr(Var("act"), "label"), Lit("denial")),
        ]), priority=40))

    return out


def list_pragmatic_concepts(s, kind: str | None = None) -> list:
    """Walk all PragmaticConcept nodes (optionally filtered by kind),
    return them sorted by priority."""
    inner = _native(s)
    out = []
    for c in inner.nodes(PRAGMATIC_CONCEPT):
        a = inner.node(c)["attrs"]
        if kind is not None and a.get("kind") != kind:
            continue
        out.append((int(a.get("priority", 999)), c))
    out.sort()
    return [c for _, c in out]


def _classify_by_concept(s, utterance_nid, kind: str,
                         default_label: str, env_extra: dict | None = None
                         ) -> str:
    """Polymorphic graph-driven classifier. Walks PragmaticConcept
    nodes of the given kind in priority order; evaluates each
    Concept's `definition_term` against an env binding
    `p` → ProsodyProfile NodeID (+ any extras the caller supplies);
    returns the label of the first matching Concept, or
    `default_label` when nothing fires."""
    inner = _native(s)
    prosody_nids = inner.neighbours(utterance_nid, HAS_PROSODY)
    if not prosody_nids:
        return default_label
    env = {"p": prosody_nids[0]}
    if env_extra:
        env.update(env_extra)
    for c in list_pragmatic_concepts(s, kind=kind):
        term = inner.node(c)["attrs"]["definition_term"]
        if inner.evaluate(term, env):
            return str(inner.node(c)["attrs"]["label"])
    return default_label


def seed_communication_grammar(s, namespace: str | None = None,
                               *, seed_concepts: bool = True) -> int:
    """Productions for the communication-layer node types + edges
    from Utterance / Stance to each. Also seeds the graph-resident
    PragmaticConcept rules by default (pass ``seed_concepts=False``
    to skip — useful when the agent wants to author its own rules
    from scratch). Idempotent on the productions; concepts are
    minted afresh on every call so don't seed twice."""
    from . import NodePattern, Production
    inner = _native(s)

    def _t(name: str) -> str:
        if namespace is None or ":" in name:
            return name
        return f"{namespace}:{name}"

    prods = []

    def _perm(src, et, tgt, prov):
        prods.append(Production(
            src=NodePattern(type=_t(src), var="src"),
            edge_type=et,
            tgt=NodePattern(type=_t(tgt), var="tgt"),
            where=None, weight=None, provenance=prov,
        ))

    # Utterance → each profile node.
    for et, tgt in [
        (HAS_PROSODY, PROSODY_PROFILE),
        (HAS_AFFECT, AFFECT),
        (HAS_SPEECH_ACT, SPEECH_ACT),
        (HAS_REGISTER, REGISTER),
        (HAS_SPEAKER, SPEAKER),
        (HAS_TURN_DYNAMICS, TURN_DYNAMICS),
        (HAS_STANCE, STANCE),
    ]:
        _perm(_speech.UTTERANCE, et, tgt, f"comm:utt_{et}")
    # SpeakerLexicon → Speaker entries.
    _perm(SPEAKER_LEXICON, HAS_SPEAKER_ENTRY, SPEAKER,
          "comm:speaker_lex_entry")
    # Utterance → previous Utterance (turn ordering).
    _perm(_speech.UTTERANCE, FOLLOWS_UTTERANCE, _speech.UTTERANCE,
          "comm:utt_follows_utt")

    for p in prods:
        inner.add_production(p.to_dict())
    if seed_concepts:
        seed_pragmatic_concepts(s)
    return len(prods)


# --- Sample fetch helper (reuse the speech module's decode path) -------

def _utterance_samples(s, utterance_nid) -> tuple[Optional[np.ndarray], int]:
    """Decode the utterance's audio samples + return (samples, fs).
    Reuses the speech module's private decoder."""
    inner = _native(s)
    stream_nid = None
    for tgt in inner.neighbours(utterance_nid, _speech.FROM_STREAM):
        stream_nid = tgt
        break
    if stream_nid is None:
        return None, 0
    a = inner.node(utterance_nid)["attrs"]
    samples = _speech._decode_utterance_samples(
        s, stream_nid,
        int(a["frame_index_start"]), int(a["n_frames"]))
    if samples is None:
        return None, 0
    if samples.ndim > 1:
        samples = samples.mean(axis=1)
    fs = int(inner.node(stream_nid)["attrs"].get("sample_rate", 0))
    return samples.astype(np.float32), fs


# --- F0 estimation (autocorrelation) -----------------------------------

def _estimate_f0_per_window(samples: np.ndarray, fs: int,
                            win_size_ms: float = 30.0,
                            hop_ms: float = 10.0,
                            f0_min: float = 60.0,
                            f0_max: float = 600.0) -> np.ndarray:
    """Per-window F0 via autocorrelation. Returns a 1-D array of F0
    (Hz) per analysis window, zero where unvoiced. Window size 30ms
    matches the typical phoneme duration; hop 10ms gives a smooth
    contour."""
    win_n = int(fs * win_size_ms / 1000)
    hop_n = int(fs * hop_ms / 1000)
    n_windows = max(0, 1 + (len(samples) - win_n) // hop_n)
    if n_windows <= 0:
        return np.zeros(0, dtype=np.float32)
    out = np.zeros(n_windows, dtype=np.float32)
    min_lag = max(1, int(fs / f0_max))
    max_lag = min(win_n - 1, int(fs / f0_min))
    for i in range(n_windows):
        seg = samples[i * hop_n:i * hop_n + win_n].astype(np.float64)
        # Centre + normalise.
        seg = seg - seg.mean()
        # Voicing check via short-term energy.
        if (seg * seg).sum() < 1e-8:
            continue
        # Autocorrelation via numpy.correlate (faster than np.correlate
        # for windowed segments because the result is small).
        ac = np.correlate(seg, seg, mode="full")
        ac = ac[len(ac) // 2:]
        if max_lag <= min_lag:
            continue
        peak_region = ac[min_lag:max_lag]
        if len(peak_region) == 0:
            continue
        peak_lag = min_lag + int(np.argmax(peak_region))
        # Accept the lag only if its peak is meaningful — peak/zero-
        # lag ratio above 0.3. This is a standard voicing heuristic.
        if ac[peak_lag] / max(ac[0], 1e-9) > 0.3:
            out[i] = fs / peak_lag
    return out


def _energy_envelope(samples: np.ndarray, fs: int,
                     win_size_ms: float = 30.0,
                     hop_ms: float = 10.0) -> np.ndarray:
    """RMS energy per window — same windowing as F0."""
    win_n = int(fs * win_size_ms / 1000)
    hop_n = int(fs * hop_ms / 1000)
    n = max(0, 1 + (len(samples) - win_n) // hop_n)
    out = np.zeros(n, dtype=np.float32)
    for i in range(n):
        seg = samples[i * hop_n:i * hop_n + win_n]
        out[i] = float(np.sqrt((seg * seg).mean()))
    return out


def _spectral_tilt(samples: np.ndarray, fs: int) -> float:
    """Slope of log-magnitude spectrum (dB/octave). Negative tilt
    (high frequencies attenuated relative to low) = breathy /
    soft. Flat or positive tilt = pressed / loud / harsh. Used as
    a voice-quality discriminator for affect classification."""
    if len(samples) < 256:
        return 0.0
    spectrum = np.abs(np.fft.rfft(samples * np.hanning(len(samples))))
    spectrum = np.maximum(spectrum, 1e-9)
    log_spec = 20 * np.log10(spectrum)
    freqs = np.fft.rfftfreq(len(samples), 1 / fs)
    # Restrict to the speech band (300-3400 Hz) where tilt is
    # informative.
    band = (freqs >= 300) & (freqs <= 3400)
    if not band.any():
        return 0.0
    log_f = np.log2(freqs[band] + 1)
    log_s = log_spec[band]
    # Linear regression slope.
    slope, _ = np.polyfit(log_f, log_s, 1)
    return float(slope)


def _zero_crossing_rate(samples: np.ndarray) -> float:
    """ZCR per sample — a cheap correlate of articulation precision
    and (loosely) speaking rate. Fricatives / sibilants have high
    ZCR; vowels low."""
    if len(samples) < 2:
        return 0.0
    crossings = np.diff(np.sign(samples)) != 0
    return float(crossings.sum()) / len(samples)


# --- ProsodyProfile ---------------------------------------------------

def compute_prosody(s, utterance_nid) -> Optional[Any]:
    """Extract a ProsodyProfile from the utterance's samples. Mints a
    ProsodyProfile node carrying the standard prosodic stats and
    wires it to the utterance via :data:`HAS_PROSODY`.

    Returns the ProsodyProfile NodeID, or None if the utterance has
    no decodable samples.
    """
    samples, fs = _utterance_samples(s, utterance_nid)
    if samples is None or len(samples) == 0 or fs == 0:
        return None
    inner = _native(s)
    f0 = _estimate_f0_per_window(samples, fs)
    voiced_f0 = f0[f0 > 0]
    energy = _energy_envelope(samples, fs)
    tilt = _spectral_tilt(samples, fs)
    zcr = _zero_crossing_rate(samples)

    # Pitch contour bucket: rising / falling / flat / undulating.
    # Compute by fitting a line over the voiced F0 trajectory + the
    # final 30% slope (used by SpeechAct).
    if len(voiced_f0) >= 4:
        x = np.arange(len(voiced_f0)).astype(np.float64)
        slope, intercept = np.polyfit(x, voiced_f0, 1)
        # Final-third slope — distinguishes "question rises" from
        # "assertion falls".
        tail_start = max(1, int(len(voiced_f0) * 0.7))
        tail = voiced_f0[tail_start:]
        if len(tail) >= 2:
            tail_x = np.arange(len(tail)).astype(np.float64)
            tail_slope, _ = np.polyfit(tail_x, tail, 1)
        else:
            tail_slope = 0.0
        if abs(slope) < 0.5:
            contour = "flat"
        elif slope > 0:
            contour = "rising"
        else:
            contour = "falling"
    else:
        slope = 0.0
        tail_slope = 0.0
        contour = "flat"

    nid = inner.add_node(PROSODY_PROFILE, {
        "f0_mean_hz": float(voiced_f0.mean()) if len(voiced_f0) else 0.0,
        "f0_median_hz": float(np.median(voiced_f0)) if len(voiced_f0) else 0.0,
        "f0_range_hz": float(voiced_f0.max() - voiced_f0.min())
            if len(voiced_f0) else 0.0,
        "f0_slope_hz_per_window": float(slope),
        "f0_tail_slope": float(tail_slope),
        "f0_contour": contour,
        "voiced_fraction": float(len(voiced_f0)) / max(len(f0), 1),
        "energy_mean": float(energy.mean()) if len(energy) else 0.0,
        "energy_std": float(energy.std()) if len(energy) else 0.0,
        "energy_max": float(energy.max()) if len(energy) else 0.0,
        "spectral_tilt": float(tilt),
        "zcr": float(zcr),
        "speaking_rate_proxy": float(zcr * 100.0),  # rough syllable-rate proxy
        "duration_s": float(len(samples)) / fs,
    })
    inner.add_edge(utterance_nid, HAS_PROSODY, nid)
    return nid


# --- Speaker identity --------------------------------------------------

def open_speaker_lexicon(s, name: str = "default") -> Any:
    """Create a SpeakerLexicon — the agent's catalog of known
    speakers. Each speaker is a graph-resident prototype in (F0
    median, spectral tilt) space."""
    return _native(s).add_node(SPEAKER_LEXICON, {
        "name": name, "n_speakers": 0,
    })


def assign_speaker(s, utterance_nid, speaker_lexicon_nid,
                   *, threshold: float = 25.0) -> tuple[Any, bool]:
    """Match the utterance's prosody to a known speaker in the
    lexicon, or mint a new Speaker. Speaker prototype is (F0 median,
    spectral tilt). Distance is normalised so 1.0 ≈ "different
    person", threshold default 25.0 Hz on F0 median + tilt slack.

    Returns ``(speaker_nid, is_new)``.

    Requires :func:`compute_prosody` to have been called on the
    utterance first.
    """
    inner = _native(s)
    # Pull the utterance's prosody profile.
    prosody_nids = inner.neighbours(utterance_nid, HAS_PROSODY)
    if not prosody_nids:
        return None, False  # type: ignore[return-value]
    p_attrs = inner.node(prosody_nids[0])["attrs"]
    f0_median = float(p_attrs.get("f0_median_hz", 0.0))
    tilt = float(p_attrs.get("spectral_tilt", 0.0))
    if f0_median == 0.0:
        return None, False  # type: ignore[return-value]

    # Walk existing speakers; find nearest in F0 space.
    best: Optional[Any] = None
    best_dist = float("inf")
    for sp in inner.neighbours(speaker_lexicon_nid, HAS_SPEAKER_ENTRY):
        a = inner.node(sp)["attrs"]
        sp_f0 = float(a.get("f0_median_hz", 0.0))
        sp_tilt = float(a.get("spectral_tilt", 0.0))
        # Distance weights F0 heavily (the primary speaker
        # discriminator) + tilt as a tiebreaker.
        dist = abs(sp_f0 - f0_median) + 5.0 * abs(sp_tilt - tilt)
        if dist < best_dist:
            best_dist = dist
            best = sp
    if best is not None and best_dist < threshold:
        # Update existing speaker prototype as a running mean.
        n = int(inner.node(best)["attrs"].get("n_utterances", 1))
        old_f0 = float(inner.node(best)["attrs"]["f0_median_hz"])
        old_tilt = float(inner.node(best)["attrs"]["spectral_tilt"])
        inner.set_attr(best, "f0_median_hz",
                       (old_f0 * n + f0_median) / (n + 1))
        inner.set_attr(best, "spectral_tilt",
                       (old_tilt * n + tilt) / (n + 1))
        inner.set_attr(best, "n_utterances", n + 1)
        inner.add_edge(utterance_nid, HAS_SPEAKER, best)
        return best, False
    # Mint new speaker.
    sp_nid = inner.add_node(SPEAKER, {
        "label": f"speaker_{len(inner.neighbours(speaker_lexicon_nid, HAS_SPEAKER_ENTRY))}",
        "f0_median_hz": f0_median,
        "spectral_tilt": tilt,
        "n_utterances": 1,
    })
    inner.add_edge(speaker_lexicon_nid, HAS_SPEAKER_ENTRY, sp_nid)
    inner.add_edge(utterance_nid, HAS_SPEAKER, sp_nid)
    cur = int(inner.node(speaker_lexicon_nid)["attrs"].get("n_speakers", 0))
    inner.set_attr(speaker_lexicon_nid, "n_speakers", cur + 1)
    return sp_nid, True


# --- Affect ------------------------------------------------------------

def classify_affect(s, utterance_nid) -> Optional[Any]:
    """Categorical affect bucket from prosody. The decision rule
    is graph-resident: walks `PragmaticConcept` nodes of kind
    "affect" in priority order, evaluates each Concept's
    `definition_term` Term-tree against the ProsodyProfile bound as
    `p`. First match wins; falls through to "calm" if no rule fires.

    Call :func:`seed_pragmatic_concepts` once at substrate setup so
    the Concepts exist; otherwise this returns "calm" for every
    input.
    """
    inner = _native(s)
    prosody_nids = inner.neighbours(utterance_nid, HAS_PROSODY)
    if not prosody_nids:
        return None
    p_attrs = inner.node(prosody_nids[0])["attrs"]
    label = _classify_by_concept(s, utterance_nid, kind="affect",
                                 default_label="calm")
    nid = inner.add_node(AFFECT, {
        "label": label,
        # Carry the prosodic discriminators for the agent's
        # introspection (the Concept Term used these to decide).
        "f0_range_hz": float(p_attrs.get("f0_range_hz", 0.0)),
        "energy_mean": float(p_attrs.get("energy_mean", 0.0)),
        "spectral_tilt": float(p_attrs.get("spectral_tilt", 0.0)),
    })
    inner.add_edge(utterance_nid, HAS_AFFECT, nid)
    return nid


# --- SpeechAct ---------------------------------------------------------

def detect_speech_act(s, utterance_nid) -> Optional[Any]:
    """Speech-act classification — graph-resident decision rules.
    Walks `PragmaticConcept` nodes of kind "speech_act" in priority
    order; falls through to "assertion"."""
    inner = _native(s)
    prosody_nids = inner.neighbours(utterance_nid, HAS_PROSODY)
    if not prosody_nids:
        return None
    p = inner.node(prosody_nids[0])["attrs"]
    label = _classify_by_concept(s, utterance_nid, kind="speech_act",
                                 default_label="assertion")
    nid = inner.add_node(SPEECH_ACT, {
        "label": label,
        "tail_slope": float(p.get("f0_tail_slope", 0.0)),
        "energy_mean": float(p.get("energy_mean", 0.0)),
        "f0_range_hz": float(p.get("f0_range_hz", 0.0)),
    })
    inner.add_edge(utterance_nid, HAS_SPEECH_ACT, nid)
    return nid


# --- Register ----------------------------------------------------------

def estimate_register(s, utterance_nid) -> Optional[Any]:
    """Register classification — graph-resident decision rules.
    Walks `PragmaticConcept` nodes of kind "register" in priority
    order; falls through to "casual"."""
    inner = _native(s)
    prosody_nids = inner.neighbours(utterance_nid, HAS_PROSODY)
    if not prosody_nids:
        return None
    p = inner.node(prosody_nids[0])["attrs"]
    label = _classify_by_concept(s, utterance_nid, kind="register",
                                 default_label="casual")
    nid = inner.add_node(REGISTER, {
        "label": label,
        "speaking_rate": float(p.get("speaking_rate_proxy", 0.0)),
        "f0_range_hz": float(p.get("f0_range_hz", 0.0)),
        "duration_s": float(p.get("duration_s", 0.0)),
    })
    inner.add_edge(utterance_nid, HAS_REGISTER, nid)
    return nid


# --- TurnDynamics ------------------------------------------------------

def compute_turn_dynamics(s, utterance_nid,
                          prev_utterance_nid: Any | None = None) -> Optional[Any]:
    """Gap / overlap / interruption stats relative to the previous
    utterance. Mints a TurnDynamics node + wires
    :data:`FOLLOWS_UTTERANCE` from this utterance to the previous.

    First utterance in a dialogue (no prev) returns None.
    """
    inner = _native(s)
    if prev_utterance_nid is None:
        return None
    cur_attrs = inner.node(utterance_nid)["attrs"]
    prev_attrs = inner.node(prev_utterance_nid)["attrs"]
    cur_start = float(cur_attrs.get("start_time_s", 0.0))
    prev_end = float(prev_attrs.get("end_time_s", 0.0))
    gap = cur_start - prev_end
    overlap = gap < 0
    # Interruption heuristic: the current utterance starts within
    # 100ms of the previous's end + speaker changed (caller wires
    # this in via the speaker context — for now we encode "very
    # short gap" as a hint).
    interruption_hint = abs(gap) < 0.10
    nid = inner.add_node(TURN_DYNAMICS, {
        "gap_s": float(gap),
        "overlap": bool(overlap),
        "interruption_hint": bool(interruption_hint),
        "prev_utterance_id": prev_utterance_nid.value if hasattr(prev_utterance_nid, "value") else int(prev_utterance_nid),
    })
    inner.add_edge(utterance_nid, HAS_TURN_DYNAMICS, nid)
    inner.add_edge(utterance_nid, FOLLOWS_UTTERANCE, prev_utterance_nid)
    return nid


# --- IronicStance heuristic --------------------------------------------

def detect_ironic_stance(s, utterance_nid) -> bool:
    """Heuristic ironic-stance detection — graph-resident decision
    rules. Walks `PragmaticConcept` nodes of kind "ironic" with full
    env binding ``{p, aff, act, reg}``: prosody profile, affect,
    speech-act, register all available to the Term-tree. Returns
    True if any Concept matches.

    Real irony detection is research-grade (requires theory of mind);
    this is a heuristic flag the agent can introspect on by walking
    the Concept's `definition_term` and asking 'why was this
    triggered?'.
    """
    inner = _native(s)
    prosody_nids = inner.neighbours(utterance_nid, HAS_PROSODY)
    affect_nids = inner.neighbours(utterance_nid, HAS_AFFECT)
    act_nids = inner.neighbours(utterance_nid, HAS_SPEECH_ACT)
    register_nids = inner.neighbours(utterance_nid, HAS_REGISTER)
    if not (prosody_nids and affect_nids and act_nids and register_nids):
        return False
    env_extra = {
        "aff": affect_nids[0],
        "act": act_nids[0],
        "reg": register_nids[0],
    }
    for c in list_pragmatic_concepts(s, kind="ironic"):
        term = inner.node(c)["attrs"]["definition_term"]
        env = {"p": prosody_nids[0], **env_extra}
        if inner.evaluate(term, env):
            return True
    return False


# --- Stance: the aggregate -------------------------------------------

def compute_stance(s, utterance_nid,
                   *, speaker_lexicon_nid: Any | None = None,
                   prev_utterance_nid: Any | None = None,
                   wire_provenance: bool = True) -> Optional[Any]:
    """Run the full communication-layer pipeline on `utterance_nid`:
    prosody → speaker → affect → speech-act → register → turn
    dynamics → ironic-stance heuristic, then mint a single Stance
    node binding the labels together. The agent's *communicative
    situation* for this utterance, all on the graph.

    Caller supplies `speaker_lexicon_nid` if speaker tracking is
    wanted, and `prev_utterance_nid` to enable turn-dynamics. Both
    optional.
    """
    inner = _native(s)
    p_nid = compute_prosody(s, utterance_nid)
    if p_nid is None:
        return None
    speaker_nid = None
    if speaker_lexicon_nid is not None:
        speaker_nid, _ = assign_speaker(s, utterance_nid, speaker_lexicon_nid)
    affect_nid = classify_affect(s, utterance_nid)
    act_nid = detect_speech_act(s, utterance_nid)
    register_nid = estimate_register(s, utterance_nid)
    turn_nid = None
    if prev_utterance_nid is not None:
        turn_nid = compute_turn_dynamics(s, utterance_nid, prev_utterance_nid)
    ironic = detect_ironic_stance(s, utterance_nid)
    # Aggregate Stance node — the communicative situation summary.
    stance_attrs = {
        "speaker": inner.node(speaker_nid)["attrs"].get("label", "?")
            if speaker_nid else "unknown",
        "affect": inner.node(affect_nid)["attrs"]["label"] if affect_nid else "?",
        "speech_act": inner.node(act_nid)["attrs"]["label"] if act_nid else "?",
        "register": inner.node(register_nid)["attrs"]["label"] if register_nid else "?",
        "ironic": ironic,
    }
    s_nid = inner.add_node(STANCE, stance_attrs)
    if wire_provenance:
        inner.add_edge(utterance_nid, HAS_STANCE, s_nid)
    return s_nid


# --- Diagnostics + the agent's introspection --------------------------

def stance_describe(s, stance_nid) -> dict:
    return dict(_native(s).node(stance_nid)["attrs"])


def affect_trajectory(s, utterance_nids: list) -> list[str]:
    """The sequence of affect labels across a dialogue. Lets the
    agent ask 'did this speaker's affect escalate?'."""
    inner = _native(s)
    out = []
    for u in utterance_nids:
        for a in inner.neighbours(u, HAS_AFFECT):
            out.append(inner.node(a)["attrs"].get("label", "?"))
            break
    return out


def turn_gaps(s, utterance_nids: list) -> list[float]:
    """List of gaps (seconds) between consecutive utterances. Long
    gaps = formal turn-taking; near-zero or negative = interruption
    pattern."""
    inner = _native(s)
    gaps = []
    for u in utterance_nids:
        for td in inner.neighbours(u, HAS_TURN_DYNAMICS):
            gaps.append(float(inner.node(td)["attrs"].get("gap_s", 0.0)))
            break
    return gaps


__all__ = [
    "PROSODY_PROFILE", "AFFECT", "SPEECH_ACT", "REGISTER",
    "SPEAKER", "SPEAKER_LEXICON", "TURN_DYNAMICS", "STANCE",
    "PRAGMATIC_CONCEPT",
    "HAS_PROSODY", "HAS_AFFECT", "HAS_SPEECH_ACT", "HAS_REGISTER",
    "HAS_SPEAKER", "HAS_TURN_DYNAMICS", "HAS_STANCE",
    "HAS_SPEAKER_ENTRY", "FOLLOWS_UTTERANCE",
    "AFFECT_CATEGORIES", "SPEECH_ACT_CATEGORIES", "REGISTER_CATEGORIES",
    "seed_communication_grammar",
    "seed_pragmatic_concepts", "list_pragmatic_concepts",
    "compute_prosody",
    "open_speaker_lexicon", "assign_speaker",
    "classify_affect", "detect_speech_act", "estimate_register",
    "compute_turn_dynamics", "detect_ironic_stance",
    "compute_stance",
    "stance_describe", "affect_trajectory", "turn_gaps",
]
