"""self_directed_speech_world — the SELF-DIRECTED SPEECH-LEARNING WORLD.

The babble loop matured into the POLYGLOT: a WORLD the agent inhabits where it
self-directs a 3-AXIS curriculum (TYPE x SOURCE x LANGUAGE), commits a BLIND guess
on speech it generated/heard, gets a COOKIE iff right, and LEARNS — banking the
exemplar + growing its lexicon. It saves itself and reports per-cell held-out
progress every 60s.

ARCHITECTURE (CLAUDE.md, strictly): the agent is the GRAPH; THIS is only the world
adapter. Python here does exactly the permitted I/O-boundary jobs:
  · download / synthesise speech (espeak-ng TTS) + load corpora (FSDD, TVTropes text)
  · draw real text from a source, voice it in a chosen language, inject noise
  · turn audio into substrate feature mutations (ingest), read graph state back
  · deliver the cookie BIT, fire the 60s timer, save/load the graph (graph_to_dict)
NO Python decisions. The 3-axis CHOICE (which cell to drill), the BLIND GUESS
(Argmax-of-product over banked exemplars), the LEARN (cookie -> bank), and the
REPORT/SAVE reflexes are all GRAPH-RESIDENT Rules / Terms the Rust runtime
evaluates (install_speech_world_rules below).

THE RECOGNIZER is the cognition+hat IN FEATURE SPACE (iter-46/49): each clip ->
a few L2 feature channels (gammatone flat + a freq-sharp FFT ear + the sharp
all-pole spectral envelope), recognised by the agent's many-settings
Argmax-of-product graph Term over banked exemplars. The TTS is the WORLD (it
teaches); it is NEVER inverted and NEVER used FOR recognition (no-donkey).

COOKIE = FEEDBACK ("this structure is admissible" -> bank the exemplar), NOT an RL
reward optimised by gradient. PROGRESS is HELD-OUT per cell (a fixed balanced probe
set the agent cannot bank), so it cannot game its own curriculum.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np

import domains.many_settings_recognizer as MS
from domains.filter_settings import cochleagram, COCHLEAR_SETTINGS, fft_ear
from domains.allpole_spectral_envelope import allpole_ear
from domains.grown_representation import seed_patches, bands_to_patches
import domains.agent_frontend as FE
from substrate_rs import (Attr, Lit, Var, Div, Count, Neighbours, Argmax,
                          NodeID, IfThenElse, Gt, Gte, Lte, Abs, And, Minus, Plus,
                          Eq, Max)


# ---------------------------------------------------------------------------
# Feature channels — the agent's GRAPH-RESIDENT, AGENT-MODIFIABLE front end.
#
# Perception of a clip = the L2 readout of every ACTIVE Cue in the agent's FrontEnd
# graph (domains/agent_frontend). The agent SELF-DESIGNS this front end: it boots
# with three robust channels (gammatone flat / FFT ear / all-pole ear) and, when it
# plateaus on a cell, ADDS / TUNES / INVENTS cues — the audio hat is the agent's to
# build (ozma_wall_is_self_imposed). Pure I/O-boundary DSP dispatched by each cue's
# `extractor` attr; the SET and PARAMS are graph data the agent modifies. NO fit, NO
# learned filter, NO TTS inversion.
#
# CHANNEL COUNT IS NOW DYNAMIC: it equals the number of active cues, which the agent
# grows. The recognizer's Argmax-of-product Term is rebuilt to match the live count.
# ---------------------------------------------------------------------------

# the seed front end's channel names (the boot configuration). The LIVE set is read
# from the graph via FE.active_cues; this is only the documented starting point.
CHANNEL_NAMES = [name for name, *_ in FE.SEED_CUES]
N_CHANNELS = len(CHANNEL_NAMES)

_MIDDLE = next(s for s in COCHLEAR_SETTINGS if s[0] == "middle")
_SEED_PATCHES = seed_patches()


def _l2(v):
    v = np.asarray(v, dtype=np.float64)
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v


def _cmvn_enabled(substrate) -> bool:
    """The agent's graph-resident choice: apply the composed CMVN Term iff an EarConfig node
    flags cmvn. Mechanical read of graph state, no decision."""
    try:
        for n in substrate.nodes("EarConfig"):
            if float(substrate.node(n)["attrs"].get("cmvn", 0.0)) >= 1.0:
                return True
    except Exception:
        pass
    return False


def feature_channels(substrate, x, fs) -> list:
    """The agent's perception of one clip THROUGH ITS CURRENT GRAPH front end: the
    L2 readout of every ACTIVE cue, in graph order (domains/agent_frontend). The SET
    and PARAMS come from the graph — so when the agent self-modifies its front end,
    what it hears changes. Pure I/O-boundary DSP; NO fit, NO learned filter, NO TTS
    inversion. Falls back to the three seed channels if no FrontEnd is installed."""
    if next((n for n in substrate.nodes("FrontEnd")), None) is not None:
        return FE.feature_channels(substrate, x, fs)
    # fallback: the three seed channels (a fresh substrate with no front end yet).
    x = np.asarray(x, dtype=np.float64)
    _, env_cut, dur_cut, nf = _MIDDLE
    M = cochleagram(x, fs, env_cut, dur_cut, nf)
    # Speaker normalisation is the agent's GRAPH-NATIVE CMVN Term (domains/cmvn), not numpy:
    # per-band mean+variance removal over time = subtract the speaker's constant offset/scale.
    # Gated by a graph-resident `cmvn` flag (a SpeechFrontEnd node) so it's the agent's choice;
    # when on, the per-band stats come out of the substrate evaluator, never np.mean.
    if _cmvn_enabled(substrate):
        from domains.cmvn import apply_cmvn
        M = apply_cmvn(M)
    flat = _l2(bands_to_patches(M, _SEED_PATCHES).flatten())
    return [flat, _l2(fft_ear(x, fs)), _l2(allpole_ear(x, fs))]


# ---------------------------------------------------------------------------
# The blind-guess recognizer = the agent's many-settings Argmax-of-product graph
# Term over BANKED exemplars. The bank lives in the substrate as Exemplar nodes
# (vectors stored as attrs) wired to their word Concept. The guess is the Term's
# value, evaluated natively — the cognition+hat in feature space.
# ---------------------------------------------------------------------------

WORD_ATTR = MS.WORD_ATTR
# The recognition Argmax-of-product is built for the LIVE channel count (the number
# of active cues in the graph front end). Cached per count so adding a cue rebuilds
# the Term to the new width. (A fresh substrate with no front end uses the 3 seed
# channels.)
_GUESS_TERMS: dict = {}


def _guess_term(n_channels: int):
    t = _GUESS_TERMS.get(n_channels)
    if t is None:
        t = MS._Pred(MS.predict_many_settings_term(n_channels))
        _GUESS_TERMS[n_channels] = t
    return t


def live_n_channels(substrate) -> int:
    """The agent's CURRENT front-end width = the number of active cues in the graph
    (falls back to the 3 seed channels if no FrontEnd is installed)."""
    n = FE.n_active(substrate)
    return n if n > 0 else N_CHANNELS


GUESS_TERM = _guess_term(N_CHANNELS)   # back-compat alias (the seed-width Term)


def _word_concept(substrate, word, cell_key):
    """Find / mint the Concept for (word, cell). The CELL (granularity|source|
    language) is part of lexical identity: each curriculum cell grows its OWN
    lexicon + exemplar bank, so a digit cell never matches a word exemplar and the
    noisy condition is a separate (harder) lexicon. Across languages the same
    orthographic word is two entries -> the agent grows a per-language lexicon ->
    the POLYGLOT. Tagged is_word so the recognition Argmax ranges over it."""
    key = f"{cell_key}::{word}"
    for c in substrate.nodes("Concept"):
        a = substrate.node(c)["attrs"]
        if a.get("lex_key") == key:
            return c
    lang = cell_key.split("|")[-1]
    c = substrate.add_node("Concept", {"name": word, "language": lang,
                                       "cell_key": cell_key, "lex_key": key,
                                       "origin": "speech_world"})
    substrate.set_attr(c, WORD_ATTR, 1.0)
    return c


def bank_exemplar(substrate, word, cell_key, x, fs):
    """LEARN: bank one heard clip as an Exemplar of (word, cell) — the agent grows
    that cell's lexicon + exemplar bank. We store the RAW WAVEFORM (audio + fs), NOT
    the extracted feature vectors: the per-cue feature vector is re-derived through the
    agent's CURRENT front end at recognition/probe time. This is what makes a
    self-modified front end automatically consistent — the bank holds the clip, never a
    stale fixed-dimension descriptor, so when the agent adds/tunes/invents a cue the
    query and the bank are ALWAYS extracted by the same (current) front end. A
    has_exemplar edge ties it to the word Concept. This is the cookie's effect."""
    c = _word_concept(substrate, word, cell_key)
    ex = substrate.add_node("Exemplar", {"word": word, "cell_key": cell_key,
                                         "origin": "speech_world"})
    audio = np.asarray(x, dtype=np.float32)
    substrate.set_attr(ex, "audio", tuple(float(t) for t in audio))
    substrate.set_attr(ex, "fs", float(fs))
    substrate.add_edge(c, "has_exemplar", ex)
    return ex


def cap_bank(substrate, cap=200) -> int:
    """BANK CAP — bound per-(word, cell) exemplar count so the bank is BOUNDED and
    memory cannot grow without limit (the OOM the unbounded parent run hit). For each
    word Concept, if it holds more than `cap` exemplars, drop the OLDEST ones,
    keeping the `cap` MOST-RECENT (Exemplar node ids are monotonically increasing, so
    the highest ids are the most recently banked). Recency keeps the freshest clips —
    which, under the IDS->ADS register gate, are the ones banked closest to the test
    register. Returns the number of exemplars pruned.

    This is WORLD-ADAPTER BANKING MECHANICS (a fixed-capacity store), NOT a decision:
    no graph state is read to decide WHAT to keep beyond the mechanical recency rule,
    the same way bank_exemplar / prune_stale_banks are mechanical store operations."""
    pruned = 0
    for c in substrate.nodes("Concept"):
        a = substrate.node(c)["attrs"]
        if a.get("origin") != "speech_world":
            continue
        exs = list(substrate.neighbours(c, "has_exemplar"))
        if len(exs) <= cap:
            continue
        # keep the `cap` highest node-ids (most recently banked); drop the rest.
        # NodeIDs are not directly comparable; their str form is "#<n>" (monotonic
        # allocation order) — parse the integer for a recency ordering.
        def _nid(ex):
            return int(str(ex).lstrip("#"))
        exs_sorted = sorted(exs, key=_nid)
        drop = exs_sorted[:len(exs_sorted) - cap]
        for ex in drop:
            substrate.remove_node(ex)
            pruned += 1
    if pruned:
        _FEAT_CACHE.clear()
    return pruned


def bank_count(substrate) -> int:
    """Total banked Exemplar nodes across all cells — the memory probe the bounded
    loop reports to show the bank stays flat under the cap. Mechanical query."""
    return len(list(substrate.nodes("Exemplar")))


def _exemplar_audio(ea):
    """The banked raw waveform (audio, fs) for one Exemplar, or None if this entry
    predates raw-audio banking (a stale fixed-dimension descriptor that can no longer
    be re-extracted through the current front end)."""
    a = ea.get("audio")
    if a is None:
        return None
    return np.asarray(a, dtype=np.float64), float(ea.get("fs", _TARGET_FS))


# Per-exemplar extracted-feature CACHE. Keyed by (exemplar_id, front_end_signature)
# so the bank's features are re-derived through the agent's CURRENT front end exactly
# once per front-end configuration — cheap reuse, and AUTOMATICALLY invalidated the
# moment the agent self-modifies its front end (the signature changes). This is what
# keeps query and bank the same dimension across a modify_frontend: both are extracted
# by the same current front end; nothing banked is ever a stale fixed-dim descriptor.
_FEAT_CACHE: dict = {}


def _frontend_signature(substrate) -> tuple:
    """A hashable signature of the agent's CURRENT front end (the active cues' ids in
    graph order). When the agent adds / tunes / invents a cue this changes, so the
    re-extraction cache below is invalidated and the bank is re-derived at the new
    width/order. World-adapter bookkeeping (no decision)."""
    return tuple(cid for cid, _a in FE.active_cues(substrate))


_FEAT_CACHE_SIG: list = [None]


def _exemplar_channels(substrate, ex, sig):
    """The banked clip's feature channels THROUGH THE CURRENT FRONT END, cached per
    (exemplar, front-end signature). Returns None if the entry has no raw audio (a
    pre-raw-audio bank entry that cannot be re-extracted)."""
    if _FEAT_CACHE_SIG[0] != sig:
        # the agent self-modified its front end -> the cache is stale; drop it so the
        # bank is re-extracted at the new width/order.
        _FEAT_CACHE.clear()
        _FEAT_CACHE_SIG[0] = sig
    key = (ex, sig)
    hit = _FEAT_CACHE.get(key)
    if hit is not None:
        return hit
    aud = _exemplar_audio(substrate.node(ex)["attrs"])
    if aud is None:
        return None
    x, fs = aud
    ch = feature_channels(substrate, x, fs)
    _FEAT_CACHE[key] = ch
    return ch


def _bank_matrix(substrate, cell_key, n_channels):
    """Pull the banked exemplars for one CELL out of the graph and RE-EXTRACT each
    clip's feature channels through the agent's CURRENT front end (mechanical query —
    the recognition Argmax then ranges over that cell's word Concepts). Because every
    exemplar is re-extracted by the same current front end, all per-channel vectors
    are guaranteed dimension-consistent with the live query. Entries with no raw audio
    (stale pre-raw-audio banks) are skipped. Returns (per_channel_train_vecs,
    train_words, candidate_concepts)."""
    sig = _frontend_signature(substrate)
    per_ch = [[] for _ in range(n_channels)]
    words = []
    cands = {}
    for c in substrate.nodes("Concept"):
        a = substrate.node(c)["attrs"]
        if a.get("origin") != "speech_world" or a.get("cell_key") != cell_key:
            continue
        cw = a.get("name")
        for ex in substrate.neighbours(c, "has_exemplar"):
            ch = _exemplar_channels(substrate, ex, sig)
            if ch is None or len(ch) < n_channels:
                continue
            for i in range(n_channels):
                per_ch[i].append(np.asarray(ch[i], dtype=np.float64))
            words.append(cw)
        cands[cw] = c
    return per_ch, words, cands


def reset_caches() -> None:
    """Drop the module-level per-exemplar feature cache + the recognition-Term cache.
    The cache keys on (exemplar NODE-ID, front-end signature); a SECOND fresh
    Substrate in the same process reuses NodeIDs from zero with the same seed cues, so
    without this reset the new substrate would read the OLD substrate's cached feature
    vectors for colliding ids (cross-contamination). The live single-process loop never
    needs it; an A/B harness that builds two substrates in one process MUST call it
    between regimes. World-adapter bookkeeping — no decision."""
    _FEAT_CACHE.clear()
    _FEAT_CACHE_SIG[0] = None


def prune_stale_banks(substrate) -> int:
    """RESUME repair: drop every banked Exemplar that carries NO raw audio (a
    pre-raw-audio entry whose stored feature vectors were fixed at an OLD front-end
    dimension and can no longer be re-extracted through the current, self-modified
    front end). The learned FRONT END (FrontEnd + Cue nodes), the CURRICULUM cells,
    and the word Concepts (the lexicon) are all kept — only the unrecoverable
    fixed-dimension exemplars are removed, so the agent re-banks them through its
    current front end as it continues. Returns the number pruned. World-adapter
    plumbing (mechanical graph repair, no decision)."""
    stale = [ex for ex in substrate.nodes("Exemplar")
             if substrate.node(ex)["attrs"].get("audio") is None]
    for ex in stale:
        substrate.remove_node(ex)
    _FEAT_CACHE.clear()
    return len(stale)


def invent_frontend_cue(substrate, cell_key, seed=0):
    """The OPEN-ENDED novelty move (the third plateau response): when the agent's
    repertoire is EXHAUSTED but the wall holds, it INVENTS a novel band-combination
    cue (feature_generator's generative grammar, MDL-selected) and gates it into its
    front end.

    THIS function is the world-adapter HARVEST only — it is mechanical I/O translation
    with NO decision: for each banked clip in the cell it computes the SAME middle
    cochleagram the invented-cue extractor evaluates over (domains/agent_frontend
    _eval_band_term_trajectory) and mints one BandFrame node PER FRAME on a fresh
    scratch substrate, carrying the per-band attrs b0..b{nb-1}, grouped by word label.
    It then hands (by_label, bands, scratch substrate) to FE.invent_cue. The GENERATE
    (compose a novel Term from the grammar) + SELECT (MDL/compression on two halves) +
    MINT decision all live in FE.invent_cue / feature_generator — the agent's own
    generative grammar and compression selector. The adapter NEVER picks a feature,
    NEVER fits, NEVER trains; it only translates the banked audio into the band frames
    the selector reads. Returns the invent dict {cue, name, kind} or None (no honest
    harvest possible — e.g. no banked clips with raw audio, or <2 labels)."""
    from substrate_rs import Substrate
    # the EXACT cochleagram the invented-cue extractor evaluates over (the middle
    # setting, domains/agent_frontend._eval_band_term_trajectory + _MIDDLE).
    _, env_cut, dur_cut, nf = _MIDDLE
    scratch = Substrate()
    by_label: dict = {}
    nb = None
    for c in substrate.nodes("Concept"):
        a = substrate.node(c)["attrs"]
        if a.get("origin") != "speech_world" or a.get("cell_key") != cell_key:
            continue
        word = a.get("name")
        for ex in substrate.neighbours(c, "has_exemplar"):
            aud = _exemplar_audio(substrate.node(ex)["attrs"])
            if aud is None:
                continue                      # stale/no-raw-audio entry — skip honestly
            x, fs = aud
            M = cochleagram(np.asarray(x, dtype=np.float64), fs, env_cut, dur_cut, nf)
            if nb is None:
                nb = M.shape[1]
            for r in range(M.shape[0]):
                bf = scratch.add_node("BandFrame", {"word": word, "origin": "invent"})
                for j in range(M.shape[1]):
                    scratch.set_attr(bf, f"b{j}", float(M[r, j]))
                by_label.setdefault(word, []).append(bf)
    # an honest harvest needs >=2 labels each with band frames (the selector compares
    # discrimination ACROSS labels on two cross-validation halves).
    usable = {k: v for k, v in by_label.items() if len(v) >= 2}
    if len(usable) < 2 or nb is None:
        return None
    bands = [f"b{j}" for j in range(nb)]
    FE._SEL_SUB_HOLDER["sub"] = scratch       # hand the selector its band frames
    try:
        return FE.invent_cue(substrate, usable, bands, seed=seed)
    finally:
        FE._SEL_SUB_HOLDER.pop("sub", None)


def blind_guess(substrate, channels, cell_key, restrict_to=None):
    """COMMIT a BLIND guess for one heard clip within a CELL: populate each
    candidate word Concept with its per-channel softmax likelihood (the channel's
    own 1-NN exemplar evidence over the cell's banked exemplars), then evaluate the
    agent's Argmax-of-product Term natively. The product ranges over the LIVE
    front-end width — capped to the channels every banked exemplar shares — so a
    self-modified front end PHASES IN as the bank refreshes (no empty-bank collapse).
    Returns the guessed word (or None if the bank is empty). FEATURE SPACE only; never
    inverts the TTS, never a neural net — the cognition+hat (iter-46/49).

    OSTENSIVE NAMING (the PARENT, restricted-competitor set): `restrict_to` is an
    optional iterable of competitor words the agent's guess is narrowed to — the
    parent's "highlight the target / suppress competitors" lever (research finding:
    joint attention's real lever is competitor-suppression, not pointing). It does
    NOT hand over the answer: the agent still RECOGNISES the clip; the parent only
    reduces the candidate pool the SAME way the cross-cell zeroing already does. The
    held-out yardstick ALWAYS calls with restrict_to=None (full lexicon) so teaching
    cannot inflate the measured capability. NO-DONKEY: this is candidate scoping, the
    recognition stays the agent's Argmax-of-product over its own exemplars."""
    # The query and the bank are BOTH extracted by the agent's current front end, so
    # they are always the same width; the product simply ranges over every live cue.
    n_channels = min(len(channels), live_n_channels(substrate))
    if n_channels <= 0:
        return None
    per_ch, words, cands = _bank_matrix(substrate, cell_key, n_channels)
    if not words:
        return None
    candidate_words = sorted(set(words))
    for i in range(n_channels):
        Xtr = np.asarray(per_ch[i])
        p = MS.channel_likelihood(np.asarray(channels[i]), Xtr, words,
                                  candidate_words)
        for w in candidate_words:
            substrate.set_attr(cands[w], MS.channel_attr(i), float(p[w]))
    # The recognition Argmax ranges over ALL is_word Concepts; restrict to THIS
    # cell's candidates by zeroing every other cell's likelihoods so they cannot win.
    for c in substrate.nodes("Concept"):
        a = substrate.node(c)["attrs"]
        if a.get("origin") == "speech_world" and a.get("cell_key") != cell_key \
                and a.get(WORD_ATTR):
            for i in range(n_channels):
                substrate.set_attr(c, MS.channel_attr(i), 0.0)
    # OSTENSIVE NAMING: suppress in-cell competitors NOT in the restricted set, the
    # same zeroing mechanism — the parent narrows attention to a few words. The agent
    # still recognises; this only scopes the candidate pool (never the held-out path).
    if restrict_to is not None:
        keep = set(restrict_to)
        for w in candidate_words:
            if w not in keep:
                for i in range(n_channels):
                    substrate.set_attr(cands[w], MS.channel_attr(i), 0.0)
    pred = substrate.evaluate(_guess_term(n_channels), {})
    if pred is None:
        return None
    return substrate.node(pred)["attrs"].get("name")


# ---------------------------------------------------------------------------
# TTS (the WORLD) + corpora (the WORLD). espeak-ng synthesises speech in any
# language; FSDD is real human digits; the TVTropes index is a real text source.
# All pure I/O — the agent grounds what the world plays.
# ---------------------------------------------------------------------------

_FSDD_DIR = "/tmp/fsdd/recordings"
_FSDD_FN = re.compile(r"(\d)_([a-z]+)_(\d+)\.wav")
_TVTROPES_INDEX = Path.home() / ".cache" / "ozma" / "tvtropes_index.json"
_TARGET_FS = 8000

# Google Speech Commands — real multi-speaker source (~2000 speakers, 35 words).
# <word>/<speaker_hash>_nohash_<n>.wav, 16 kHz mono. The robust cross-speaker LOSO
# yardstick: many held-out speaker hashes (vs FSDD's handful), their clips never
# banked. Pure world I/O — the speaker split is probe-construction mechanics.
_SC_DIR = "/tmp/sc"
_SC_FN = re.compile(r"([0-9a-f]+)_nohash_(\d+)\.wav")
# the digit words present as Speech Commands sub-directories (the fast small set).
_SC_DIGITS = ["zero", "one", "two", "three", "four", "five", "six", "seven",
              "eight", "nine"]

_DIGIT_WORDS = {
    "en": ["zero", "one", "two", "three", "four", "five", "six", "seven",
           "eight", "nine"],
    "fr": ["zero", "un", "deux", "trois", "quatre", "cinq", "six", "sept",
           "huit", "neuf"],
    "de": ["null", "eins", "zwei", "drei", "vier", "funf", "sechs", "sieben",
           "acht", "neun"],
    "es": ["cero", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete",
           "ocho", "nueve"],
}

_ESPEAK_VOICE = {"en": "en", "fr": "fr", "de": "de", "es": "es"}


def espeak_available() -> bool:
    return _which("espeak-ng") or _which("espeak")


def _which(name):
    from shutil import which
    return which(name)


def _read_wav(path):
    with wave.open(path, "rb") as w:
        fs = w.getframerate()
        raw = w.readframes(w.getnframes())
    x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    return x, fs


def tts(text, lang) -> tuple:
    """Voice `text` in `lang` via espeak-ng, resampled to 8 kHz mono (matching
    FSDD). Returns (audio float32, fs). Pure world I/O."""
    voice = _ESPEAK_VOICE.get(lang, "en")
    exe = _which("espeak-ng") or _which("espeak")
    with tempfile.TemporaryDirectory() as d:
        raw = os.path.join(d, "raw.wav")
        out = os.path.join(d, "out.wav")
        subprocess.run([exe, "-v", voice, "-w", raw, text],
                       check=True, capture_output=True)
        if _which("ffmpeg"):
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw,
                            "-ar", str(_TARGET_FS), "-ac", "1",
                            "-sample_fmt", "s16", out],
                           check=True, capture_output=True)
            return _read_wav(out)
        return _read_wav(raw)


# ---------------------------------------------------------------------------
# PIPER — NEURAL TTS as a realistic-speech WORLD source (per-language voices).
#
# Piper is a neural text-to-speech model (VITS). Here it is the WORLD: it PLAYS
# realistic audio the agent must RECOGNIZE through its front end (in feature space).
# The agent NEVER inverts Piper and NEVER uses it FOR recognition (no-donkey): the
# net synthesises the stimulus; the agent grounds it with its OWN cognition+hat.
# If Piper is not installed (offline), the in-thesis espeak fallback is used.
# ---------------------------------------------------------------------------

_PIPER_DIR = Path.home() / ".cache" / "ozma" / "piper_voices"
# language -> a downloaded Piper voice model (realistic per-language voices).
_PIPER_VOICE = {
    "en": "en_US-lessac-medium",
    "fr": "fr_FR-siwis-medium",
    "de": "de_DE-thorsten-medium",
    "es": "es_ES-davefx-medium",
}
_PIPER_CACHE: dict = {}        # lang -> loaded PiperVoice (loaded once)


def piper_available(lang: str = "en") -> bool:
    """True iff the piper package imports AND the voice model for `lang` is present."""
    try:
        import piper  # noqa: F401
    except Exception:
        return False
    name = _PIPER_VOICE.get(lang)
    return bool(name) and (_PIPER_DIR / f"{name}.onnx").exists()


def _piper_voice(lang: str):
    if lang in _PIPER_CACHE:
        return _PIPER_CACHE[lang]
    from piper import PiperVoice
    name = _PIPER_VOICE.get(lang, _PIPER_VOICE["en"])
    v = PiperVoice.load(str(_PIPER_DIR / f"{name}.onnx"))
    _PIPER_CACHE[lang] = v
    return v


def _resample_to_target(x, src_fs):
    """Linear resample float audio src_fs -> _TARGET_FS (8 kHz) mono. Boundary DSP."""
    x = np.asarray(x, dtype=np.float64)
    if src_fs == _TARGET_FS or x.size == 0:
        return x.astype(np.float32), _TARGET_FS
    n_out = max(1, int(round(x.size * _TARGET_FS / src_fs)))
    idx = np.linspace(0, x.size - 1, n_out)
    return np.interp(idx, np.arange(x.size), x).astype(np.float32), _TARGET_FS


def piper_tts(text, lang) -> tuple:
    """Voice `text` in `lang` with the NEURAL Piper model, resampled to 8 kHz mono
    (matching FSDD + the espeak path). Returns (audio float32, fs). Pure world I/O —
    the net produces the stimulus; the agent recognises it, never inverts it."""
    v = _piper_voice(lang)
    chunks = list(v.synthesize(text))
    if not chunks:
        return np.zeros(1, dtype=np.float32), _TARGET_FS
    src_fs = int(getattr(chunks[0], "sample_rate", v.config.sample_rate))
    audio = np.concatenate([c.audio_float_array for c in chunks]).astype(np.float64)
    return _resample_to_target(audio, src_fs)


def inject_noise(x, snr_db=5.0, seed=0) -> np.ndarray:
    """The HARD version: additive white noise at a fixed SNR (the noisy-corpus
    source). Pure DSP at the boundary."""
    x = np.asarray(x, dtype=np.float64)
    rng = np.random.default_rng(seed)
    p_sig = float(np.mean(x ** 2)) + 1e-12
    p_noise = p_sig / (10 ** (snr_db / 10.0))
    return (x + rng.normal(0.0, np.sqrt(p_noise), size=x.shape)).astype(np.float32)


def fsdd_index() -> dict:
    """Map digit-word -> list of (path) for the real-human FSDD source."""
    idx = {w: [] for w in _DIGIT_WORDS["en"]}
    if not os.path.isdir(_FSDD_DIR):
        return idx
    for fn in sorted(os.listdir(_FSDD_DIR)):
        m = _FSDD_FN.match(fn)
        if not m:
            continue
        idx[_DIGIT_WORDS["en"][int(m.group(1))]].append(
            os.path.join(_FSDD_DIR, fn))
    return idx


def fsdd_speakers() -> list:
    """The distinct speaker names in the real-human FSDD corpus (filename group 2 of
    `{digit}_{speaker}_{index}.wav`). Used to build a LEAVE-ONE-SPEAKER-OUT split for
    the cross-speaker held-out probe. Mechanical filename parsing — pure I/O."""
    spk = set()
    if not os.path.isdir(_FSDD_DIR):
        return []
    for fn in os.listdir(_FSDD_DIR):
        m = _FSDD_FN.match(fn)
        if m:
            spk.add(m.group(2))
    return sorted(spk)


def fsdd_index_for(speakers) -> dict:
    """Map digit-word -> list of FSDD clip paths SPOKEN BY a speaker in `speakers`
    (the train side of a LOSO split, or the held-out side for the probe). Same parse
    as fsdd_index, scoped to a speaker set. Mechanical I/O — the speaker split is a
    probe-construction mechanic (which clips the agent may bank vs which are held out),
    NOT a decision."""
    keep = set(speakers)
    idx = {w: [] for w in _DIGIT_WORDS["en"]}
    if not os.path.isdir(_FSDD_DIR):
        return idx
    for fn in sorted(os.listdir(_FSDD_DIR)):
        m = _FSDD_FN.match(fn)
        if not m or m.group(2) not in keep:
            continue
        idx[_DIGIT_WORDS["en"][int(m.group(1))]].append(
            os.path.join(_FSDD_DIR, fn))
    return idx


def fsdd_available() -> bool:
    return os.path.isdir(_FSDD_DIR) and bool(os.listdir(_FSDD_DIR))


def load_fsdd_clip(path):
    x, fs = _read_wav(path)
    if fs != _TARGET_FS and _which("ffmpeg"):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "o.wav")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path,
                            "-ar", str(_TARGET_FS), "-ac", "1",
                            "-sample_fmt", "s16", out],
                           check=True, capture_output=True)
            return _read_wav(out)
    return x, fs


# ---------------------------------------------------------------------------
# Google Speech Commands SOURCE — real multi-speaker, robust LOSO. Mirrors the
# fsdd_index / fsdd_index_for / fsdd_speakers pattern over /tmp/sc. Speaker hash is
# the filename prefix (<hash>_nohash_<n>.wav). Pure I/O — the loader resamples each
# clip 16 kHz -> 8 kHz to match the cochlea (the same target as FSDD).
# ---------------------------------------------------------------------------

def sc_available() -> bool:
    return os.path.isdir(_SC_DIR) and any(
        os.path.isdir(os.path.join(_SC_DIR, w)) for w in _SC_DIGITS)


def sc_words(min_clips=200) -> list:
    """The digit words present as Speech Commands directories with enough clips
    (the small fast set: the spoken digits zero..nine). Mechanical I/O."""
    out = []
    for w in _SC_DIGITS:
        d = os.path.join(_SC_DIR, w)
        if os.path.isdir(d) and sum(1 for f in os.listdir(d)
                                    if f.endswith(".wav")) >= min_clips:
            out.append(w)
    return out


def sc_speakers(words=None) -> list:
    """The distinct speaker hashes across `words` (the parsed filename prefix). Used
    to build a robust LEAVE-MANY-SPEAKERS-OUT cross-speaker split. Mechanical parse —
    the speaker split is probe-construction mechanics, NOT a decision."""
    words = words or sc_words()
    spk = set()
    for w in words:
        d = os.path.join(_SC_DIR, w)
        if not os.path.isdir(d):
            continue
        for fn in os.listdir(d):
            m = _SC_FN.match(fn)
            if m:
                spk.add(m.group(1))
    return sorted(spk)


def sc_index(words=None) -> dict:
    """Map word -> list of (path, speaker_hash) for the real Speech Commands source.
    Mechanical filename parse — pure I/O."""
    words = words or sc_words()
    idx = {w: [] for w in words}
    for w in words:
        d = os.path.join(_SC_DIR, w)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            m = _SC_FN.match(fn)
            if not m:
                continue
            idx[w].append((os.path.join(d, fn), m.group(1)))
    return idx


def sc_index_for(speakers, words=None) -> dict:
    """Map word -> list of SC clip paths SPOKEN BY a speaker hash in `speakers` (the
    train side, or the held-out side, of a robust multi-speaker LOSO split). Same
    parse as sc_index, scoped to a speaker set. The held-out speakers' clips are
    NEVER banked — the ungameable cross-speaker yardstick. Mechanical I/O."""
    keep = set(speakers)
    words = words or sc_words()
    idx = {w: [] for w in words}
    for w in words:
        d = os.path.join(_SC_DIR, w)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            m = _SC_FN.match(fn)
            if not m or m.group(1) not in keep:
                continue
            idx[w].append(os.path.join(d, fn))
    return idx


def load_sc_clip(path):
    """Load one Speech Commands wav, resampled to 8 kHz mono (matching FSDD + the
    cochlea front end). Pure boundary DSP."""
    x, fs = _read_wav(path)
    if fs == _TARGET_FS or x.size == 0:
        return np.ascontiguousarray(x.astype(np.float32)), _TARGET_FS
    return _resample_to_target(x, fs)


# ---------------------------------------------------------------------------
# LINGUA LIBRE — the GATELESS, MULTILINGUAL real teaching-voice source.
#
# Lingua Libre (lingualibre.org, Wikimedia) is recorded ISOLATED-WORD
# pronunciations, free/CC, many languages, many speakers, NO access gate. It is
# the gateless multilingual version of the clear pronunciation-model register —
# the PARENT's real "second-language-learning material" (citation-form clear
# speech), replacing synthetic espeak where a word is covered.
#
# These loaders mirror fsdd_index EXACTLY: {word: [path]}, 8 kHz 16-bit WAV, with
# the speaker encoded in the filename ({word}_{speaker}_{idx}.wav) so the
# leave-one-speaker-out held-out probe is a pure filename filter — the SAME LOSO
# mechanic as FSDD. The clips are populated OFFLINE by scripts/fetch_lingua_libre.py
# (the world-prep tool); these are pure I/O reads. DONKEY BOUNDARY: this is the
# WORLD's teaching speech (the agent grounds it; recognition stays the agent's);
# held-out speakers are a filename filter and are never banked.
# ---------------------------------------------------------------------------

_LL_DIR = Path.home() / ".cache" / "ozma" / "lingualibre"
_LL_FN = re.compile(r"([a-z]+)_([a-z0-9]+)_(\d+)\.wav$")


def _ll_lang_dir(lang) -> Path:
    return _LL_DIR / lang


def ll_available(lang="en") -> bool:
    """True iff the Lingua Libre cache for `lang` exists and holds clips. The cache
    is produced offline by scripts/fetch_lingua_libre.py (gateless SPARQL fetch)."""
    d = _ll_lang_dir(lang)
    return d.is_dir() and any(_LL_FN.match(fn) for fn in os.listdir(d))


def ll_index(lang="en") -> dict:
    """Map word -> [clip_path, ...] for the Lingua Libre source in `lang`. Same shape
    as fsdd_index. Mechanical filename parse — pure I/O. Keys are the words the cache
    actually contains (the covered subset; not every digit/word has LL audio)."""
    d = _ll_lang_dir(lang)
    idx: dict = {}
    if not d.is_dir():
        return idx
    for fn in sorted(os.listdir(d)):
        m = _LL_FN.match(fn)
        if not m:
            continue
        idx.setdefault(m.group(1), []).append(str(d / fn))
    return idx


def ll_speakers(lang="en") -> list:
    """The distinct speaker tokens in the Lingua Libre cache for `lang` (filename
    group 2 of {word}_{speaker}_{idx}.wav) — for a LEAVE-ONE-SPEAKER-OUT split, the
    SAME mechanic as fsdd_speakers. Pure I/O."""
    d = _ll_lang_dir(lang)
    spk = set()
    if not d.is_dir():
        return []
    for fn in os.listdir(d):
        m = _LL_FN.match(fn)
        if m:
            spk.add(m.group(2))
    return sorted(spk)


def ll_index_for(speakers, lang="en") -> dict:
    """Map word -> [LL clip paths in `lang` SPOKEN BY a speaker in `speakers`] — the
    train side of a LOSO split, or the held-out side for the cross-speaker probe.
    Same parse as ll_index, scoped to a speaker set. Mechanical I/O — the speaker
    split is probe construction (which clips may be banked vs held out), NOT a
    decision; the held-out speakers are never banked."""
    keep = set(speakers)
    d = _ll_lang_dir(lang)
    idx: dict = {}
    if not d.is_dir():
        return idx
    for fn in sorted(os.listdir(d)):
        m = _LL_FN.match(fn)
        if not m or m.group(2) not in keep:
            continue
        idx.setdefault(m.group(1), []).append(str(d / fn))
    return idx


def load_ll_clip(path):
    """Read one Lingua Libre clip -> (audio float32, fs). The cache is already 8 kHz
    16-bit mono (fetch_lingua_libre resamples on prep); resample defensively if a
    stray clip is off-rate, the same as load_fsdd_clip. Pure boundary I/O."""
    x, fs = _read_wav(path)
    if fs != _TARGET_FS and _which("ffmpeg"):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "o.wav")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path,
                            "-ar", str(_TARGET_FS), "-ac", "1",
                            "-sample_fmt", "s16", out],
                           check=True, capture_output=True)
            return _read_wav(out)
    return x, fs


def tvtropes_words(limit=200) -> list:
    """Real text from the agent's TVTropes corpus: the trope phrases (1-2 word
    names), a real English vocabulary source for the WORD granularity."""
    if not _TVTROPES_INDEX.exists():
        return []
    with _TVTROPES_INDEX.open() as f:
        idx = json.load(f)
    words = []
    for entry in idx.values():
        phrase = entry.get("phrase", "")
        for tok in re.findall(r"[a-z]+", phrase.lower()):
            if 3 <= len(tok) <= 10:
                words.append(tok)
                if len(words) >= limit:
                    return sorted(set(words))
    return sorted(set(words))


# ---------------------------------------------------------------------------
# GRAPH-RESIDENT decisions: the 2 goals + the curriculum-pick Rule + the
# report/save reflexes. Installed as graph data; the Rust runtime evaluates them.
# ---------------------------------------------------------------------------

def _native(substrate):
    return substrate._inner if hasattr(substrate, "_inner") else substrate


def install_speech_world_rules(substrate) -> dict:
    """Install the world's graph-resident mind: a SpeechWorldRoot carrying the two
    seeded GOALS, one Cell node per (granularity x source x language) carrying its
    held-out cookie-rate, and the Rules that DECIDE — pick the worst cell (active
    curriculum), flag a report, flag a save. NO Python decides any of these; Python
    only records measurements onto the cells + acts on the chosen-cell / flags."""
    nat = _native(substrate)

    # Productions FIRST — they register the node + edge types in Γ so the nodes /
    # edges below are admissible (the substrate refuses unknown types).
    for src_t, et, tgt_t, prov in (
        ("SpeechWorldRoot", "owns", "CurriculumCell", "speech_world:owns"),
        ("SpeechWorldRoot", "self", "SpeechWorldRoot", "speech_world:self"),
        ("SpeechWorldRoot", "pursues", "Goal", "speech_world:pursues"),
        ("SpeechWorldRoot", "selected", "CurriculumCell", "speech_world:selected"),
        ("Concept", "has_exemplar", "Exemplar", "speech_world:bank"),
    ):
        try:
            substrate.add_production({"src": {"type": src_t, "var": "a"},
                                      "edge_type": et,
                                      "tgt": {"type": tgt_t, "var": "b"},
                                      "provenance": prov})
        except Exception:
            pass

    # The SpeechWorldRoot — holds the goals + clock state the report/save reflexes read.
    root = next((n for n in substrate.nodes("SpeechWorldRoot")), None)
    if root is None:
        root = substrate.add_node("SpeechWorldRoot", {
            "origin": "speech_world",
            "report_period_s": 60.0,       # "report progress every 60s" goal
            "save_period_s": 120.0,
            "secs_since_report": 0.0,
            "secs_since_save": 0.0,
            "report_due": 0,
            "save_due": 0,
        })
    # The seeded GOALS as graph nodes the root pursues.
    for gid, desc, kind in (
        ("understand_voice",
         "maximise understanding (cookies) across granularity x source x language",
         "maximise_cookies"),
        ("report_progress",
         "report progress every 60 seconds", "periodic_report"),
        ("improve_front_end",
         "when a cell PLATEAUS (held-out cookie-rate stalls = the front-end wall), "
         "MODIFY the front end (add an ear / gate in a banked cue / invent) and retry",
         "self_design_frontend")):
        if not any(substrate.node(g)["attrs"].get("goal_id") == gid
                   for g in substrate.nodes("Goal")):
            g = substrate.add_node("Goal", {"goal_id": gid, "description": desc,
                                            "kind": kind, "origin": "speech_world"})
            substrate.add_edge(root, "pursues", g)

    # The agent's GRAPH-RESIDENT, AGENT-MODIFIABLE FRONT END (the audio hat it owns
    # and self-designs). Installed here so the world boots with it; the agent reads
    # the active cues to perceive and modifies the graph to change what it hears.
    FE.install_frontend(substrate)

    if root not in substrate.neighbours(root, "self"):
        try:
            substrate.add_edge(root, "self", root, {})
        except Exception:
            pass

    # RULE 2 — report reflex: when secs_since_report >= report_period_s, raise
    # report_due and reset the clock. The periodic-report GOAL, graph-resident.
    R = Var("R")
    rule_report = {
        "name": "speech_world_report_reflex",
        "match": [["R", "self", "R"]],
        "where": Gte(a=Attr(R, "secs_since_report"),
                     b=Attr(R, "report_period_s")).to_dict(),
        "effects": [
            ["set_attr", "R", "report_due", 1],
            ["set_attr", "R", "secs_since_report", 0.0],
        ],
    }
    # RULE 3 — save reflex: when secs_since_save >= save_period_s, raise save_due.
    rule_save = {
        "name": "speech_world_save_reflex",
        "match": [["R", "self", "R"]],
        "where": Gte(a=Attr(R, "secs_since_save"),
                     b=Attr(R, "save_period_s")).to_dict(),
        "effects": [
            ["set_attr", "R", "save_due", 1],
            ["set_attr", "R", "secs_since_save", 0.0],
        ],
    }
    # RULE 4 — PLATEAU detect (the front-end wall): for each CurriculumCell, when it
    # is still HARD (held-out cookie-rate below `plateau_ceiling`) AND its progress
    # has STALLED across reports (|held_delta| <= `plateau_band`) AND it has had real
    # effort (`n_probes` measured), the agent has hit a wall the current front end
    # cannot pass -> raise `frontend_mod_due`. This is the effort-without-payoff
    # signal specialised to a cell: the lever that isn't moving the outcome is the
    # FRONT END, so the agent's response (the adapter enacts) is to modify it. NO
    # Python conditional makes this judgement — it is this graph Rule.
    C = Var("Cc")
    hard = Lte(a=Attr(C, "held_cookie_rate"), b=Attr(C, "plateau_ceiling"))
    stalled = Lte(a=Abs(Attr(C, "held_delta")), b=Attr(C, "plateau_band"))
    had_effort = Gte(a=Attr(C, "n_probes"), b=Lit(1.0))
    not_already = Eq(a=Attr(C, "frontend_mod_due"), b=Lit(0))
    # the treadmill fix, in the judgement: a cell already flagged a DEEPER WALL
    # (the front end is not the lever there) must NOT keep triggering mods, and a
    # cell with a pending un-judged mod must wait for the effect-gate's verdict
    # before stacking another mod (no inventing cue #N+1 before #N is judged).
    not_deeper = Eq(a=Attr(C, "deeper_wall"), b=Lit(0))
    no_pending = Eq(a=Attr(C, "mod_eval_pending"), b=Lit(0))
    rule_plateau = {
        "name": "speech_world_plateau_detect",
        "match": [["Root", "owns", "Cc"]],
        "where": And(items=(hard, stalled, had_effort, not_already,
                            not_deeper, no_pending)).to_dict(),
        "effects": [["set_attr", "Cc", "frontend_mod_due", 1]],
    }
    idx_report = nat.add_rule(rule_report)
    idx_save = nat.add_rule(rule_save)
    idx_plateau = nat.add_rule(rule_plateau)
    # the EFFECT-GATE + DEEPER-WALL judgements (the treadmill fix), installed here so
    # the world boots with them. The KEEP/DROP and the FLAG decisions are these Rules.
    gate = install_effect_gate_rules(substrate)
    return {"root": root, "pick_term": PICK_TERM,
            "rule_report": idx_report, "rule_save": idx_save,
            "rule_plateau": idx_plateau,
            "rule_effect_gate": gate["effect_gate"],
            "rule_deeper_wall": gate["deeper_wall"]}


# ---------------------------------------------------------------------------
# THE EFFECT-GATE + DEEPER-WALL judgements (the invention-treadmill fix).
#
# The treadmill: the agent invents a front-end cue on every plateau, the cues are
# MDL-valid (compress) but DON'T LIFT the held-out recognition on the deeper
# exemplar/representation wall, and nothing measured that — so it span, ballooning
# the front end to 30+ cues with the same ~20 cells flat. The fix is fix-the-fixer
# using the agent's OWN effort-without-payoff meta-monitor:
#
#  EFFECT-GATE (per cell): after a mod, on the NEXT held-out measurement, KEEP the
#    mod iff this cell's held-out rate LIFTED beyond noise (gain > lift_band); else
#    REVERT it (the adapter drops the cue) and grow the non-lift streak. The KEEP/
#    DROP decision is this Rule's `mod_lifted` Term; the adapter only enacts the drop.
#
#  DEEPER-WALL (per cell, the meta-monitor wiring): when the non-lift streak reaches
#    deeper_wall_n (effort rising — more mods — while payoff stays flat = exactly
#    effort_without_payoff specialised to a cell), the cell is a DEEPER-THAN-FRONT-
#    END wall; set `deeper_wall` = 1 so the plateau judgement stops triggering mods
#    on it and the curriculum redirects effort to cells the front end can still help.
#
# Both are graph Rules (composed Term-trees, native eval); Python only measures the
# held-out rate (the agent's own yardstick) and enacts the revert. No Python branch
# makes the keep/drop/flag decision.
# ---------------------------------------------------------------------------

def install_effect_gate_rules(substrate) -> dict:
    """Install the two treadmill-fix Rules over each CurriculumCell:
      EFFECT-GATE  — judge the last mod KEPT/REVERTED by whether the cell's held-out
                     LIFTED beyond lift_band; grow nonlift_streak when it didn't.
      DEEPER-WALL  — when nonlift_streak reaches deeper_wall_n (effort_without_payoff
                     on this cell), flag deeper_wall so mods stop + the agent moves on.
    Returns the two rule indices."""
    nat = _native(substrate)

    # EFFECT-GATE: fires for a cell that HAS a pending mod AND a fresh held-out is in
    # (mod_eval_pending). lift = held_cookie_rate - pending_mod_baseline. lifted iff
    # lift > lift_band. Records the verdict, grows the streak on a non-lift, resets it
    # on a lift, and clears the pending flag. The KEEP/DROP is `mod_lifted`; the
    # adapter reverts the cue when mod_lifted == 0.
    C = Var("Cc")
    lift = Minus(a=Attr(C, "held_cookie_rate"), b=Attr(C, "pending_mod_baseline"))
    lifted = Gt(a=lift, b=Attr(C, "lift_band"))
    lifted_next = IfThenElse(lifted, Lit(1), Lit(0))
    # streak: +1 when NOT lifted, reset to 0 when lifted.
    streak_next = IfThenElse(lifted, Lit(0.0),
                            Plus(items=(Attr(C, "nonlift_streak"), Lit(1.0))))
    rule_gate = {
        "name": "speech_world_effect_gate",
        "match": [["Root", "owns", "Cc"]],
        "where": Eq(a=Attr(C, "mod_eval_pending"), b=Lit(1)).to_dict(),
        "effects": [
            ["set_attr", "Cc", "mod_lifted", {"__term__": lifted_next.to_dict()}],
            ["set_attr", "Cc", "nonlift_streak",
             {"__term__": streak_next.to_dict()}],
            ["set_attr", "Cc", "mod_eval_pending", 0],
        ],
    }

    # DEEPER-WALL (the meta-monitor's effort_without_payoff, per cell): when the
    # non-lift streak reaches deeper_wall_n, set deeper_wall = 1. Effort (mods) rose
    # while payoff (held-out) stayed flat -> the front end is not the lever here.
    enough = Gte(a=Attr(C, "nonlift_streak"), b=Attr(C, "deeper_wall_n"))
    wall_next = IfThenElse(enough, Lit(1), Attr(C, "deeper_wall"))
    rule_wall = {
        "name": "speech_world_deeper_wall_flag",
        "match": [["Root", "owns", "Cc"]],
        "where": Gte(a=Attr(C, "nonlift_streak"), b=Lit(1.0)).to_dict(),
        "effects": [
            ["set_attr", "Cc", "deeper_wall", {"__term__": wall_next.to_dict()}],
        ],
    }
    return {"effect_gate": nat.add_rule(rule_gate),
            "deeper_wall": nat.add_rule(rule_wall)}


def note_frontend_mod(substrate, cell, cue) -> None:
    """Record (mechanically) that the agent just made a front-end mod FOR `cell`:
    stash the cue id to revert if it doesn't lift, and the cell's CURRENT held-out
    rate as the baseline the effect-gate will compare the NEXT measurement against.
    World-adapter bookkeeping — no decision (the keep/drop is the gate Rule)."""
    a = substrate.node(cell)["attrs"]
    cue_val = float(cue.value) if cue is not None and hasattr(cue, "value") \
        else (float(cue) if cue is not None else -1.0)
    substrate.set_attr(cell, "pending_mod_cue", cue_val)
    substrate.set_attr(cell, "pending_mod_baseline",
                       float(a.get("held_cookie_rate", 0.0)))


def run_effect_gate(substrate, rules: dict, max_iters: int = 400) -> list:
    """Drive the effect-gate + deeper-wall Rules after a fresh held-out report, then
    REVERT every cue the gate judged non-lifting (mod_lifted == 0 with a pending
    cue). The KEEP/DROP and DEEPER-WALL decisions were the Rules'; this only reads
    them and enacts the drop. Returns the list of cells newly flagged deeper-wall."""
    nat = _native(substrate)
    root = next((n for n in substrate.nodes("SpeechWorldRoot")), None)
    if root is None:
        return []
    # fire the gate over every cell whose held-out just refreshed (mod_eval_pending),
    # then the deeper-wall flag over every cell that has a non-lift streak.
    for _ in range(max_iters):
        pending = [c for c in substrate.neighbours(root, "owns")
                   if substrate.node(c)["attrs"].get("mod_eval_pending") == 1]
        if not pending:
            break
        nat.apply_rule_once(rules["rule_effect_gate"])
    for _ in range(max_iters):
        nat.apply_rule_once(rules["rule_deeper_wall"])
        if all(substrate.node(c)["attrs"].get("deeper_wall") == 1 or
               substrate.node(c)["attrs"].get("nonlift_streak", 0.0) <
               substrate.node(c)["attrs"].get("deeper_wall_n", 3.0)
               for c in substrate.neighbours(root, "owns")):
            break
    # ENACT the reverts the gate decided (mod_lifted == 0 + a pending cue id).
    newly_walled = []
    for c in substrate.neighbours(root, "owns"):
        a = substrate.node(c)["attrs"]
        cue_id = a.get("pending_mod_cue", -1.0)
        if cue_id is not None and float(cue_id) >= 0.0:
            if a.get("mod_lifted") == 0:
                # the gate judged this mod NON-LIFTING -> drop it (don't accumulate).
                from substrate_rs import NodeID as _NodeID
                FE.revert_cue(substrate, _NodeID(int(cue_id)))
            # clear the pending cue either way (kept or reverted, it's been judged).
            substrate.set_attr(c, "pending_mod_cue", -1.0)
        if a.get("deeper_wall") == 1 and not a.get("_wall_announced"):
            substrate.set_attr(c, "_wall_announced", 1)
            newly_walled.append(a.get("name"))
    return newly_walled


# The 3-AXIS CURRICULUM CHOICE as a graph Term (the "understand_voice" goal's
# active curriculum): Argmax over CurriculumCell of the cell's PRIORITY =
# DEFICIT (1 - held_out_cookie_rate) + an exploration bonus while under-probed.
# The DECISION is this Term, evaluated natively by substrate.evaluate; the world
# adapter only READS its value (the same pattern the recognition Argmax uses).
# NO Python sort, NO Python conditional chooses the cell.
def _pick_term():
    C = Var("C")
    # deficit drives toward the cell the agent understands LEAST. live_rate is a
    # recency-weighted online cookie-rate the adapter updates each step (seeded from
    # the authoritative held-out rate at each report), so the choice rotates between
    # reports without waiting 60s for the held-out measurement.
    deficit = Minus(a=Lit(1.0), b=Attr(C, "live_rate"))
    # exploration bonus: a cell with few LIVE attempts looks maximally deficient so
    # every cell gets visited before the measured deficit takes over. live_attempts
    # is updated immediately each step (n_probes only at the 60s report), so the
    # bonus decays in real time and the choice ROTATES across cells. The bonus is
    # the under-explored mass = max(0, min_visits - live_attempts)/min_visits.
    min_visits = Attr(C, "explore_min_visits")
    seen = Attr(C, "live_attempts")
    explore = Max(items=(Lit(0.0),
                         Div(a=Minus(a=min_visits, b=seen), b=min_visits)))
    priority = Plus(items=(deficit, explore))
    return MS._Pred(Argmax(
        source={"type": "NodesWhere", "node_type": "CurriculumCell",
                "attr_key": "is_cell", "value": Lit(1.0).to_dict()},
        var_name="C", value=priority.to_dict(), default=None).to_dict())


PICK_TERM = _pick_term()


# The PLATEAU JUDGEMENT as a graph boolean Term (the SAME condition as the
# speech_world_plateau_detect Rule's `where`). The adapter evaluates it per cell each
# report to find cells at the front-end wall. This is the established project pattern
# (PICK_TERM / GUESS_TERM): the DECISION is the graph Term the runtime evaluates, the
# adapter only reads its value — used here because the Rust rule engine fires a given
# match-binding once, so a plateau that must be RE-checked every report needs the
# Term-evaluation form, not a one-shot Rule effect. No Python conditional makes the
# judgement; the And(...) Term does.
def _plateau_predicate():
    C = Var("Cc")
    hard = Lte(a=Attr(C, "held_cookie_rate"), b=Attr(C, "plateau_ceiling"))
    stalled = Lte(a=Abs(Attr(C, "held_delta")), b=Attr(C, "plateau_band"))
    had_effort = Gte(a=Attr(C, "n_probes"), b=Lit(1.0))
    # the treadmill fix: a DEEPER-WALL cell (front end is not the lever) is NOT
    # plateaued-for-front-end-mods, and a cell still awaiting the effect-gate's
    # verdict on its last mod must not trigger another. Same exclusions as the Rule.
    not_deeper = Eq(a=Attr(C, "deeper_wall"), b=Lit(0))
    no_pending = Eq(a=Attr(C, "mod_eval_pending"), b=Lit(0))
    return MS._Pred(And(items=(hard, stalled, had_effort,
                              not_deeper, no_pending)).to_dict())


PLATEAU_TERM = _plateau_predicate()


def cell_plateaued(substrate, cell) -> bool:
    """True iff the cell satisfies the agent's graph-resident PLATEAU judgement (HARD
    + STALLED + had effort) — i.e. it has hit the front-end wall. The decision is the
    PLATEAU_TERM; this only reads its value for the named cell."""
    return bool(substrate.evaluate(PLATEAU_TERM, {"Cc": cell}))


def pick_cell(substrate):
    """The agent's 3-axis curriculum choice: evaluate the PICK_TERM Argmax natively
    and return the chosen CurriculumCell node (the cell it is WORST at / least
    explored). The decision is the graph Term; this only reads its value."""
    return substrate.evaluate(PICK_TERM, {})


def install_cell(substrate, granularity, source, language) -> int:
    """Mint one CurriculumCell for an axis combination (granularity x source x
    language), owned by the root. Carries the held-out cookie-rate the pick Rule
    reads + the running counters. The agent SELF-DIRECTS over the cells it owns."""
    root = next((n for n in substrate.nodes("SpeechWorldRoot")), None)
    name = f"{granularity}|{source}|{language}"
    # the EFFECT-GATE + DEEPER-WALL attrs the treadmill-fix Rules read (defaults a
    # resumed pre-fix cell lacks). Migrated onto an existing cell so a loaded save
    # gains the gate state without losing its learned rates/banks.
    _gate_defaults = {
        "pending_mod_cue": -1.0, "pending_mod_baseline": 0.0,
        "mod_eval_pending": 0, "mod_lifted": 0, "nonlift_streak": 0.0,
        "lift_band": 0.03, "deeper_wall_n": 3.0, "deeper_wall": 0,
    }
    for c in substrate.nodes("CurriculumCell"):
        a = substrate.node(c)["attrs"]
        if a.get("name") == name:
            for k, v in _gate_defaults.items():
                if k not in a:
                    substrate.set_attr(c, k, v)
            return c
    c = substrate.add_node("CurriculumCell", {
        "name": name, "granularity": granularity, "source": source,
        "language": language, "is_cell": 1.0,
        "held_cookie_rate": 0.0,     # held-out understanding (the progress signal)
        "live_rate": 0.0,            # online recency-weighted rate (steers the pick)
        "n_probes": 0.0,             # how many held-out probes measured
        "live_cookies": 0.0, "live_attempts": 0.0,  # online cookie tally
        "explore_min_visits": 12.0,  # visits before the explore bonus fully decays
        # PLATEAU detection (the front-end wall): held_delta = the change in held-out
        # rate across the last two reports; when a HARD cell's progress STALLS the
        # plateau Rule raises frontend_mod_due -> the agent modifies its front end.
        "held_delta": 1.0,           # init high so a fresh cell is never "plateaued"
        # below this held-out rate the cell is still worth pushing on. Set HIGH (0.80)
        # because the 3-cue seed front end already lifts the old ~0.30-0.40 FSDD wall to
        # ~0.60-0.70 — so a cell stalled below near-perfect is where the agent should try
        # widening its front end. (A cell that saturates ~1.0, e.g. espeak, never stalls
        # below this and so never triggers a needless modification.)
        "plateau_ceiling": 0.80,
        "plateau_band": 0.03,        # |held_delta| <= this = progress has STALLED
        "frontend_mod_due": 0,       # the plateau Rule raises this; adapter enacts
        # EFFECT-GATE + META-MONITOR state (the treadmill fix). A front-end mod is
        # only KEPT if it LIFTS this cell's held-out rate; otherwise it is reverted
        # and the non-lift streak grows. When the streak reaches deeper_wall_n the
        # cell is a DEEPER-THAN-FRONT-END wall (the exemplar/representation residual)
        # — the front end is NOT the lever there, so the agent STOPS modifying it.
        "pending_mod_cue": -1.0,     # the cue id added on the last plateau (-1 = none)
        "pending_mod_baseline": 0.0, # held-out rate WHEN that mod was made
        "mod_eval_pending": 0,       # a fresh held-out is in -> the gate should judge
        "mod_lifted": 0,             # the gate's verdict: did the last mod LIFT?
        "nonlift_streak": 0.0,       # consecutive non-lifting mods (effort, payoff flat)
        "lift_band": 0.03,           # held-out gain beyond this = a real LIFT (not noise)
        "deeper_wall_n": 3.0,        # this many non-lifting mods -> flag deeper wall
        "deeper_wall": 0,            # set by the meta-monitor: front end is not the lever
        "origin": "speech_world"})
    if root is not None:
        substrate.add_edge(root, "owns", c)
    return c


__all__ = [
    "CHANNEL_NAMES", "N_CHANNELS", "feature_channels", "live_n_channels",
    "blind_guess", "bank_exemplar", "cap_bank", "bank_count",
    "prune_stale_banks", "reset_caches",
    "invent_frontend_cue",
    "GUESS_TERM",
    "tts", "espeak_available", "inject_noise",
    "piper_tts", "piper_available",
    "fsdd_index", "fsdd_index_for", "fsdd_speakers", "fsdd_available",
    "load_fsdd_clip",
    "ll_index", "ll_index_for", "ll_speakers", "ll_available", "load_ll_clip",
    "sc_available", "sc_words", "sc_speakers", "sc_index", "sc_index_for",
    "load_sc_clip",
    "tvtropes_words", "_DIGIT_WORDS",
    "install_speech_world_rules", "install_cell", "pick_cell", "PICK_TERM",
    "install_effect_gate_rules", "note_frontend_mod", "run_effect_gate",
    "cell_plateaued", "PLATEAU_TERM",
]
