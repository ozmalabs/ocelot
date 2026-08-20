"""Speech-to-semiotics — audio becomes graph-resident sign objects.

NOT speech-to-text. Speech-to-text outputs an orthographic string
whose meaning lives elsewhere — some other module has to interpret
the letters. Speech-to-semiotics outputs **sign-objects** directly:
each utterance is a graph node with a form (acoustic fingerprint),
a denoted Concept, and a place in a Lexicon.

Peirce's three-part sign maps onto the substrate's existing pieces:

* **Sign** (representamen) — :data:`AcousticSign` node carrying a
  band-energy feature vector (the "shape" of an utterance in
  cochlear-feature space).
* **Object** (what it refers to) — :data:`Concept` node, the
  agent's existing concept-as-Term-tree shape.
* **Interpretant** (the mental act it triggers) — the agent
  evaluating the Concept's Term-tree.

The pipeline
------------
1. **Detect** acoustic activity windows in an audio stream using the native
   codec hints we already extract (Opus SILK mode regions; MP3
   short-block clusters; energy thresholding via the bitrate profile). These
   are I/O extraction windows only, not linguistic boundaries or commitment
   points. No ASR.
2. **Extract** a per-utterance feature vector by running the
   :mod:`substrate_rs.audio` cochlear bank on the decoded segment
   and summarising per-band energy over time windows.
3. **Match or acquire**: compare to existing AcousticSigns in the
   target Lexicon via cosine similarity. If match above threshold,
   bump the sign's `hearings` count (Hebbian-shape: repetition
   strengthens). If no match, mint a new AcousticSign.
4. **Ground** (optional, called separately by teaching code) — link
   the AcousticSign to a Concept via the standard ``denotes`` edge
   so the agent's lexicon can resolve form → meaning the same way
   text signs already do.

The whole loop runs on graph data. The agent that built its
acoustic lexicon can read every sign it knows: name, feature
vector, denotation, hearing count, provenance. Nothing opaque.

Biology
-------
Pre-linguistic infants do this. They notice which acoustic patterns
RECUR (Saffran et al. 1996 — statistical learning of word boundaries
in 8-month-olds); only later do they map recurring patterns to
meanings via co-occurrence with referents. We model both steps:
acquisition is statistical (recurrence → sign creation), grounding
is symbolic (teacher or context provides the Concept).
"""
from __future__ import annotations

import math
from typing import Any, Iterable, Optional

import numpy as np

from . import Substrate as _PySubstrate
from . import audio as _audio

# Re-export the relevant audio-module edge type so the speech-module
# code below can name it locally without an `_audio.` prefix
# everywhere.
HAS_FRAME = _audio.HAS_FRAME


# --- Node + edge type constants ----------------------------------------

LEXICON = "AcousticLexicon"
ACOUSTIC_SIGN = "AcousticSign"
UTTERANCE = "Utterance"

HAS_ENTRY = "has_entry"            # Lexicon → AcousticSign
HEARD_AS = "heard_as"              # Utterance → AcousticSign (matched/acquired)
DENOTES = "denotes"                # AcousticSign → Concept (Peirce: sign → object)
FROM_STREAM = "from_stream"        # Utterance → AudioStream provenance
CONTINUES_TO = "continues_to"      # AcousticSign → possible next AcousticSign


def _native(s):
    return s._inner if isinstance(s, _PySubstrate) else s


# --- Grammar seeding ---------------------------------------------------

def seed_speech_grammar(s, namespace: str | None = None) -> int:
    """Add productions for the speech-semiotic node types + edges.
    Idempotent within a single substrate the way the other seeders
    are. Returns the production count added."""
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

    _perm(LEXICON, HAS_ENTRY, ACOUSTIC_SIGN, "speech:lex_entry")
    _perm(UTTERANCE, HEARD_AS, ACOUSTIC_SIGN, "speech:utt_heard_as")
    # We can't pin a concrete Concept type here (different domains use
    # different concept type names — Concept, Phrase, Meaning). The
    # caller seeds whatever Concept-shape they use AND wires a
    # specific production: AcousticSign -denotes-> <ConceptType>.
    # We declare ONE permissive production using the bare "Concept"
    # type name; callers using a different type can add their own.
    _perm(ACOUSTIC_SIGN, DENOTES, "Concept", "speech:sign_denotes_concept")
    _perm(ACOUSTIC_SIGN, CONTINUES_TO, ACOUSTIC_SIGN,
          "speech:sign_continues_to_sign")
    _perm(UTTERANCE, FROM_STREAM, _audio.AUDIO_STREAM,
          "speech:utt_from_stream")

    for p in prods:
        inner.add_production(p.to_dict())
    return len(prods)


# --- Lexicon -----------------------------------------------------------

def open_lexicon(s, name: str = "default",
                 origin: str = "user_authored",
                 *, match_threshold: float = 0.85) -> Any:
    """Create a Lexicon anchor — a graph-resident vocabulary the
    agent grows. Multiple lexicons can coexist (one per cortex,
    one per domain, etc.); each owns its own AcousticSigns.

    ``match_threshold`` lives on the Lexicon as a graph attr so the
    agent can tighten / loosen its own discrimination by mutating
    one Lit (or by spawning sibling lexicons with different
    thresholds). The default 0.85 matches the prior hard-coded
    cosine cutoff in :func:`acquire_sign` / :func:`match_sign`.

    Returns the Lexicon NodeID.
    """
    inner = _native(s)
    return inner.add_node(LEXICON, {
        "name": name,
        "origin": origin,
        "n_signs": 0,
        "match_threshold": float(match_threshold),
    })


def _lexicon_threshold(s, lexicon_nid, override: float | None) -> float:
    """If the caller passed an explicit threshold, honour it.
    Otherwise pull the threshold from the Lexicon's graph attr
    (default 0.85 for older lexicons that pre-date the attr)."""
    if override is not None:
        return float(override)
    inner = _native(s)
    return float(inner.node(lexicon_nid)["attrs"].get("match_threshold", 0.85))


def lexicon_signs(s, lexicon_nid) -> list:
    """Every AcousticSign in this lexicon. The agent's catalog of
    'words I know' (where 'word' = recurring acoustic pattern)."""
    inner = _native(s)
    return list(inner.neighbours(lexicon_nid, HAS_ENTRY))


def lexicon_describe(s, lexicon_nid) -> dict:
    """Snapshot — name, sign count, sample of sign labels."""
    inner = _native(s)
    a = inner.node(lexicon_nid)["attrs"]
    signs = lexicon_signs(s, lexicon_nid)
    sample_names = []
    for sid in signs[:10]:
        sample_names.append(inner.node(sid)["attrs"].get("label", "?"))
    return {
        "name": a.get("name"),
        "n_signs": len(signs),
        "sample_labels": sample_names,
    }


# --- Utterance detection ----------------------------------------------

def detect_utterances(
    s,
    stream_nid,
    *,
    min_duration_s: float = 0.2,
    max_duration_s: float = 5.0,
    mode_hint: str | None = None,
) -> list[Any]:
    """Find candidate utterances in the parsed audio stream WITHOUT
    decoding samples. Uses the native codec hints we already
    extracted (Opus SILK regions for speech; MP3 long-block regions
    for tonal/voiced content; FLAC non-constant subframes for
    non-silence; per-frame coded_size as energy proxy).

    Returns a list of Utterance NodeIDs.

    ``mode_hint``: optional codec-specific hint ("opus_silk_only",
    "mp3_long_blocks"). When None, uses an energy-based fallback
    that works across codecs: a contiguous run of frames whose
    coded_size exceeds the stream median is one utterance.
    """
    inner = _native(s)
    codec = str(inner.node(stream_nid)["attrs"].get("codec", ""))
    stream_attrs = inner.node(stream_nid)["attrs"]
    framerate = float(stream_attrs.get("framerate", 0.0)) or None

    # Gather frames sorted by time + collect (time, predicate-truth).
    frames = inner.neighbours(stream_nid, HAS_FRAME)
    items = []
    for f in frames:
        a = inner.node(f)["attrs"]
        t = float(a.get("time_s", 0.0))
        items.append((t, f, a))
    items.sort(key=lambda x: x[0])

    # Per-codec speech-region predicate.
    def is_speechlike(frame_attrs: dict) -> bool:
        if codec == "opus":
            # Opus tags speech vs music: SILK is speech-only, Hybrid
            # is mostly speech with music elements, CELT is music.
            # Default: accept all three (the agent may want music
            # utterances too). `mode_hint="opus_silk_only"` filters
            # to pure-speech regions.
            mode = frame_attrs.get("opus_mode")
            if mode_hint == "opus_silk_only":
                return mode == "SILK"
            return mode in ("SILK", "Hybrid", "CELT")
        if codec.startswith("mp3"):
            # Speech-like = MP3 LONG blocks (sustained voicing).
            # The Mp3Granule children carry block_type — but we
            # don't want to walk per-granule here; we use the
            # transient detector's inverse: NOT in transient_frames.
            # Approximated by frame coded_size against a baseline.
            return True   # rely on energy fallback below
        if codec == "vorbis":
            return frame_attrs.get("vorbis_packet_type") == "audio"
        if codec == "flac":
            # FLAC frames are always speechlike if not silent; we
            # use the energy fallback for silence detection.
            return True
        if codec == "aac":
            return True
        return True

    # Energy fallback: a frame is "active" if its coded_size is
    # above the stream's 25th percentile. Cuts silence cleanly
    # without needing to decode.
    sizes = [a.get("coded_size", 0) for _, _, a in items]
    if sizes:
        size_p25 = float(np.percentile(sizes, 25))
    else:
        size_p25 = 0.0

    def is_active(frame_attrs: dict) -> bool:
        return float(frame_attrs.get("coded_size", 0)) >= size_p25

    # Walk contiguous runs of (speechlike AND active) frames into
    # Utterance segments.
    utterances: list[Any] = []
    cur_start: Optional[tuple] = None    # (start_time, first_frame_id)
    cur_end: Optional[float] = None
    cur_frames: list = []
    for t, fid, fattrs in items:
        if is_speechlike(fattrs) and is_active(fattrs):
            if cur_start is None:
                cur_start = (t, fid)
            cur_end = t
            cur_frames.append(fid)
        else:
            if cur_start is not None:
                duration = max(0.0, (cur_end or cur_start[0]) - cur_start[0])
                if duration >= min_duration_s and duration <= max_duration_s:
                    utterances.append(_make_utterance(
                        s, stream_nid, cur_start[0], cur_end or cur_start[0],
                        cur_frames))
                cur_start = None
                cur_end = None
                cur_frames = []
    if cur_start is not None:
        duration = max(0.0, (cur_end or cur_start[0]) - cur_start[0])
        if duration >= min_duration_s and duration <= max_duration_s:
            utterances.append(_make_utterance(
                s, stream_nid, cur_start[0], cur_end or cur_start[0],
                cur_frames))

    # --- STRUCTURAL FALLBACK for CONTINUOUS REAL audio --------------------
    # The silence-gap walk above segments by DROPS in coded energy below the
    # stream's own 25th percentile — it needs SILENCE GAPS to break the stream
    # into utterances. Clean / synthetic speech has them; REAL continuous audio
    # (children's TV: speech over continuous background music) does NOT — every
    # frame stays above p25, so the whole stream is ONE un-broken active run.
    # That single run then exceeds `max_duration_s` and is DROPPED -> n=0
    # utterances (the under-segmentation floor: the loop banks 0.0 with n=0).
    #
    # When the gap-walk yields no usable utterance (or one near-whole-stream
    # blob), fall back to the agent's HELD word-segmenter: it does not depend on
    # silence gaps — it reads WORD BOUNDARIES from the TRANSITIONAL-PROBABILITY
    # structure of its own sub-word units (Saffran statistical learning), the
    # grid-robust prominent-trough rule (local_min AND below-median) compiled to
    # the native primitive `segment_units` (be50a0c7). The DECISION (where to
    # cut) is the agent's held Term / native primitive; the codebook is k-means
    # fit on THIS clip's own cochlear frames (an adaptive statistic of the
    # signal, not a magic codebook). donkey=0 — no LLM, no hand-tuned constant.
    span = (items[-1][0] - items[0][0]) if len(items) >= 2 else 0.0
    # Codec frame rate: prefer the stream attr; many real streams don't carry it
    # (it reads 0.0), so derive it from the observed frame-time span — a statistic
    # of the data, not a constant.
    fr_eff = framerate or ((len(items) - 1) / span if span > 0.0 else 0.0)
    # The DIAGNOSED failure is precise: on continuous real audio (speech over
    # continuous background music) NO codec frame ever drops below the stream's
    # own p25, so the whole stream is ONE un-broken active run; that run exceeds
    # max_duration_s and is DROPPED -> the gap-walk mints NOTHING (n=0 — the
    # floor the loop banks 0.0 on). The fix fires ONLY in that case: the gap-walk
    # found NO usable utterance. When it DID mint utterance(s) — short clips kept
    # as a coarse blob, or speech with real pauses cut at the gaps — the gap-walk
    # worked as designed and is left untouched. Scoped to the actual bug, no
    # magic threshold.
    degenerate = not utterances
    if degenerate and len(items) >= 8 and fr_eff > 0.0:
        # Emit the segmenter's OWN chunks. We do NOT re-impose a min-duration
        # MERGE here: the prominent-trough rule already chose the boundaries from
        # the TP structure; a post-hoc duration floor would merge real cuts away
        # and DESTROY the discriminative structure (it collapses the agent's
        # word/sub-word cuts to a few blobs whose boundaries then no longer beat
        # random). The agent's cut density IS the result. max_duration still
        # guards against a runaway un-cut chunk.
        struct = _structural_segment(
            s, stream_nid, items, fr_eff,
            min_duration_s=0.0, max_duration_s=max_duration_s)
        if struct:
            # Drop the degenerate gap-walk blob(s) in favour of the structural
            # word-scale units (don't double-count the same audio).
            return struct
    return utterances


def _structural_segment(s, stream_nid, items, framerate,
                        *, min_duration_s, max_duration_s,
                        n_bands: int = 32, codebook_k: int = 48):
    """The agent's HELD word-segmenter as the fallback for continuous audio.

    Decode the active region's samples, build the agent's cochleagram, quantise
    each frame to a codebook id (k-means on THIS clip's own frames — adaptive,
    not a fixed/magic codebook), then run the held prominent-trough segmenter
    (native `segment_units`, mode 2 = local_min AND below-median, the grid-robust
    word-scale rule). Each chunk of cochlear frames becomes one Utterance, its
    frame_index_start / n_frames mapped back to the codec frames so
    extract_features can decode it. Returns the minted Utterance NodeIDs, or [].

    NOTE: the segmentation DECISION is the agent's held native primitive; this
    function is mechanical I/O (decode, cochleagram, mint nodes)."""
    inner = _native(s)
    try:
        from . import _native as _nat
    except Exception:
        return []
    # Decode the whole active span (codec frames items[0]..items[-1]).
    start_fi = int(inner.node(items[0][1])["attrs"]["frame_index"])
    n_codec = len(items)
    samples = _decode_utterance_samples(s, stream_nid, start_fi, n_codec)
    if samples is None or len(samples) == 0:
        return []
    if samples.ndim > 1:
        samples = samples.mean(axis=1)
    fs = float(inner.node(stream_nid)["attrs"].get("sample_rate", 0.0)) or 0.0
    if fs <= 0.0:
        # derive from samples-per-codec-frame and the codec framerate.
        fs = (len(samples) / max(n_codec, 1)) * float(framerate)
    if fs <= 0.0:
        return []
    # The agent's cochleagram at a per-frame grid (~100 fps — the grid the
    # prominent rule was validated grid-robust on).
    dur_s = len(samples) / fs
    n_frames = max(8, int(round(dur_s * 100.0)))
    flat = _nat.cochleagram(np.asarray(samples, dtype=np.float32),
                            int(round(fs)), 50.0, 80.0, n_frames)
    M = np.asarray(flat, dtype=np.float64).reshape(n_frames, n_bands)
    # L2-normalise each frame (gain-invariance), as the agent's frames() does.
    e = np.linalg.norm(M, axis=1)
    Mn = M / (e[:, None] + 1e-9)
    # Quantise to codebook ids — k-means on THIS clip's own frames (adaptive
    # statistic of the signal; the agent's held LEARNING primitive). Cap k to
    # the number of frames.
    k = int(min(codebook_k, max(2, n_frames // 2)))
    cflat = _nat.kmeans(list(Mn.flatten().astype(float)), n_frames, n_bands, k, 15)
    C = np.asarray(cflat, dtype=np.float64).reshape(k, n_bands)
    # nearest centroid per frame (squared-euclidean — same as kmeans assignment).
    d2 = ((Mn[:, None, :] - C[None, :, :]) ** 2).sum(-1)
    seq = [int(i) for i in d2.argmin(1)]
    # The held prominent-trough segmenter (native primitive), mode 2.
    lens = _nat.segment_units([seq], True, 2)
    if not lens or not lens[0]:
        return []
    chunk_lens = list(lens[0])
    # Map cochlear-frame chunks to (a) boundary TIMES on the FINE cochlear grid
    # (~100 fps — the agent's segmenter found the cuts there, so the times must
    # come from there, NOT round-tripped through the coarse codec grid which
    # would blur the boundaries), and (b) the codec frame_ids that span each
    # chunk (needed by extract_features to decode the audio).
    out = []
    t_base = items[0][0]
    coch_hop = dur_s / float(n_frames)               # seconds per cochlear frame
    frames_per_codec = n_frames / float(n_codec)     # cochlear frames per codec frame
    f0 = 0
    for ln in chunk_lens:
        f1 = f0 + ln
        # FINE-grid boundary times (the segmenter's actual resolution).
        t0 = t_base + f0 * coch_hop
        t1 = t_base + f1 * coch_hop
        dur = max(0.0, t1 - t0)
        # codec-frame span for decoding (coarse is fine for decode coverage).
        c0 = int(f0 / max(frames_per_codec, 1e-9))
        c1 = int(np.ceil(f1 / max(frames_per_codec, 1e-9)))
        c0 = max(0, min(c0, n_codec - 1)); c1 = max(c0 + 1, min(c1, n_codec))
        f0 = f1
        if dur < min_duration_s or dur > max_duration_s:
            continue
        frame_ids = [items[i][1] for i in range(c0, c1)]
        if not frame_ids:
            continue
        out.append(_make_utterance(s, stream_nid, t0, t1, frame_ids))
    return out


def _make_utterance(s, stream_nid, t_start, t_end, frame_ids) -> Any:
    """Mint an Utterance node, wire FROM_STREAM provenance."""
    inner = _native(s)
    nid = inner.add_node(UTTERANCE, {
        "start_time_s": float(t_start),
        "end_time_s": float(t_end),
        "duration_s": float(t_end - t_start),
        "n_frames": int(len(frame_ids)),
        "frame_index_start": int(inner.node(frame_ids[0])["attrs"]["frame_index"])
            if frame_ids else 0,
    })
    inner.add_edge(nid, FROM_STREAM, stream_nid)
    return nid


# --- Feature extraction -----------------------------------------------

def extract_features(
    s,
    utterance_nid,
    *,
    n_bands: int = 16,
    n_time_windows: int = 4,
    fs: int = 22050,
    cochlea_bank: list | None = None,
) -> np.ndarray:
    """Compute a fixed-size acoustic fingerprint for the utterance.

    Pipeline: locate the utterance's source AudioStream → decode the
    relevant frames → build (or reuse) a cochlear bank → apply each
    band to the samples → bucket the time axis into ``n_time_windows``
    bins → mean energy per (band, window). Returns the flattened
    feature vector of length ``n_bands * n_time_windows``.

    Note: this is the ONLY step in the pipeline that decodes audio.
    Detection (above) and matching (below) are sample-free. We
    decode here because acoustic features are inherently sample-
    level; the alternative would be to compute features from the
    encoder's spectral coefficients, which requires deep codec-
    specific work (Phase 14b's MDCT-coefficient direct read is a
    future enhancement that would skip this step too).
    """
    inner = _native(s)
    # Walk back to the stream + container.
    stream_nid = None
    for tgt in inner.neighbours(utterance_nid, FROM_STREAM):
        stream_nid = tgt
        break
    if stream_nid is None:
        return np.zeros(n_bands * n_time_windows, dtype=np.float32)

    # Decode the utterance's frames into a contiguous sample buffer.
    # We use frame_index_start + n_frames to get the relevant frames.
    n_frames = int(inner.node(utterance_nid)["attrs"]["n_frames"])
    start_idx = int(inner.node(utterance_nid)["attrs"]["frame_index_start"])
    samples = _decode_utterance_samples(s, stream_nid, start_idx, n_frames)
    if samples is None or len(samples) == 0:
        return np.zeros(n_bands * n_time_windows, dtype=np.float32)
    if samples.ndim > 1:
        samples = samples.mean(axis=1)

    # Build a fresh cochlear bank if the caller didn't supply one.
    # Reuses existing nodes when called multiple times in the same
    # substrate — there's no de-dup so we'd accumulate; for repeated
    # calls callers should pre-build a bank and pass it.
    if cochlea_bank is None:
        cochlea_bank = _audio.cochlea(s, n_bands=n_bands, fs=fs)
    # Apply each band; band-pass energy per time window.
    buf_nid = _audio.audio_from_array(s, samples, sample_rate=fs)
    band_responses = _audio.a1_responses(s, buf_nid, cochlea_bank)
    features = np.zeros((len(cochlea_bank), n_time_windows), dtype=np.float32)
    for b_idx, r_nid in enumerate(band_responses):
        resp = _audio.audio_to_array(s, r_nid).astype(np.float32)
        if resp.ndim > 1:
            resp = resp.mean(axis=1)
        # Bucket into time windows and compute RMS energy per bucket.
        n = len(resp)
        if n == 0:
            continue
        window_len = max(1, n // n_time_windows)
        for w in range(n_time_windows):
            seg = resp[w * window_len:(w + 1) * window_len]
            if len(seg) > 0:
                features[b_idx, w] = float(np.sqrt(np.mean(seg ** 2)))
    return features.flatten()


def extract_trajectory(
    s,
    utterance_nid,
    *,
    n_bands: int = 16,
    n_frames: int = 16,
    fs: int = 22050,
    cochlea_bank: list | None = None,
) -> list[list[float]]:
    """Return the sign's time-indexed cochlear shape.

    This is the temporal counterpart of :func:`extract_features`.  It is
    deliberately still a sign form, not a word/phoneme label: each row is
    one observed acoustic slice that a future-manifold caller can compare
    with a candidate sign's predicted continuation.
    """
    inner = _native(s)
    stream_nid = next(iter(inner.neighbours(utterance_nid, FROM_STREAM)), None)
    if stream_nid is None:
        return []
    n_codec_frames = int(inner.node(utterance_nid)["attrs"].get("n_frames", 0))
    start_idx = int(inner.node(utterance_nid)["attrs"].get("frame_index_start", 0))
    samples = _decode_utterance_samples(s, stream_nid, start_idx, n_codec_frames)
    if samples is None or len(samples) == 0:
        return []
    if samples.ndim > 1:
        samples = samples.mean(axis=1)
    if cochlea_bank is None:
        cochlea_bank = _audio.cochlea(s, n_bands=n_bands, fs=fs)
    buf_nid = _audio.audio_from_array(s, samples, sample_rate=fs)
    responses = _audio.a1_responses(s, buf_nid, cochlea_bank)
    out = np.zeros((n_frames, len(cochlea_bank)), dtype=np.float32)
    for band, response_nid in enumerate(responses):
        response = _audio.audio_to_array(s, response_nid).astype(np.float32)
        if response.ndim > 1:
            response = response.mean(axis=1)
        if len(response) == 0:
            continue
        window_len = max(1, len(response) // n_frames)
        for frame in range(n_frames):
            segment = response[frame * window_len:(frame + 1) * window_len]
            if len(segment):
                out[frame, band] = float(np.sqrt(np.mean(segment ** 2)))
    norm = float(np.linalg.norm(out))
    if norm > 1e-8:
        out /= norm
    return out.tolist()


def _decode_utterance_samples(s, stream_nid, start_idx: int,
                              n_frames: int) -> Optional[np.ndarray]:
    """Decode a contiguous range of audio frames into a numpy array.
    Skips priming packets (zero-sample decode) the same way
    :func:`audio.decode_frame` does."""
    inner = _native(s)
    container_nid = None
    for src in inner.in_neighbours(stream_nid, _audio.HAS_STREAM):
        container_nid = src
        break
    if container_nid is None:
        return None
    handle = _audio._handle_for(container_nid)
    handle.av_container.seek(0)
    import av  # noqa: F401 — provided by audio module's import path
    av_stream = handle.av_container.streams[handle.stream_index]
    seen = 0
    target_end = start_idx + n_frames
    chunks: list[np.ndarray] = []
    for packet in handle.av_container.demux(av_stream):
        if packet.size == 0:
            continue
        if seen >= start_idx and seen < target_end:
            for frame in packet.decode():
                arr = frame.to_ndarray()
                if arr.ndim == 2 and arr.shape[0] < arr.shape[1]:
                    arr = arr.T
                chunks.append(arr.astype(np.float32))
        seen += 1
        if seen >= target_end:
            break
    if not chunks:
        return None
    return np.concatenate(chunks, axis=0)


# --- Sign acquisition + matching --------------------------------------

def acquire_sign(
    s,
    lexicon_nid,
    features: np.ndarray,
    *,
    label: str | None = None,
    threshold: float | None = None,
    origin: str = "acquired",
    trajectory: list[list[float]] | None = None,
) -> tuple[Any, bool]:
    """Match `features` against existing AcousticSigns in the
    lexicon. If a sign matches above the lexicon's discrimination
    threshold (cosine similarity), increment its `hearings` count
    and return it. Otherwise mint a fresh AcousticSign carrying
    these features as its prototype.

    Threshold resolution:
      * pass ``threshold=`` to override per-call (escape hatch);
      * otherwise the Lexicon's ``match_threshold`` attr is used —
        the agent edits *that* to retune its own ear.

    Returns ``(sign_nid, is_new)``.
    """
    inner = _native(s)
    threshold = _lexicon_threshold(s, lexicon_nid, threshold)
    existing = lexicon_signs(s, lexicon_nid)
    best_match: Optional[Any] = None
    best_sim = -1.0
    f = features.astype(np.float32)
    f_norm = float(np.linalg.norm(f))
    if f_norm == 0:
        # All-zero features (silence) — don't mint a sign.
        return None, False  # type: ignore[return-value]
    for sid in existing:
        proto = np.frombuffer(
            inner.node(sid)["attrs"]["features"], dtype=np.float32)
        p_norm = float(np.linalg.norm(proto))
        if p_norm == 0:
            continue
        sim = float(np.dot(f, proto) / (f_norm * p_norm))
        if sim > best_sim:
            best_sim = sim
            best_match = sid
    if best_match is not None and best_sim >= threshold:
        # Update the existing sign: bump hearings + maintain a running
        # mean of the prototype (gives the sign a centroid in feature
        # space — better than first-seen alone).
        attrs = inner.node(best_match)["attrs"]
        n = int(attrs.get("hearings", 1))
        old = np.frombuffer(attrs["features"], dtype=np.float32)
        new_proto = (old * n + f) / (n + 1)
        inner.set_attr(best_match, "features", new_proto.tobytes())
        inner.set_attr(best_match, "hearings", n + 1)
        inner.set_attr(best_match, "last_similarity",
                       float(round(best_sim, 4)))
        if trajectory:
            # Keep the sign's forward form as a running temporal centroid.
            # Shape mismatch is an honest replacement: unlike a word label,
            # a sign's time grid is allowed to change with the observation.
            old_t = attrs.get("future_manifold_values")
            if isinstance(old_t, list) and len(old_t) == len(trajectory):
                try:
                    old = np.asarray(old_t, dtype=np.float32)
                    new = np.asarray(trajectory, dtype=np.float32)
                    if old.shape == new.shape:
                        hearings = max(n, 1)
                        trajectory = ((old * hearings + new) / (hearings + 1)).tolist()
                except (TypeError, ValueError):
                    pass
            inner.set_attr(best_match, "future_manifold_values", trajectory)
            inner.set_attr(best_match, "future_manifold_trajectory_length", len(trajectory))
        return best_match, False
    # Mint a new sign.
    sign = inner.add_node(ACOUSTIC_SIGN, {
        "label": label or f"sign_{len(existing)}",
        "features": f.tobytes(),
        "feature_length": int(len(f)),
        "hearings": 1,
        "origin": origin,
    })
    if trajectory:
        inner.set_attr(sign, "future_manifold_values", trajectory)
        inner.set_attr(sign, "future_manifold_trajectory_length", len(trajectory))
    inner.add_edge(lexicon_nid, HAS_ENTRY, sign)
    # Update the lexicon's count.
    cur = int(inner.node(lexicon_nid)["attrs"].get("n_signs", 0))
    inner.set_attr(lexicon_nid, "n_signs", cur + 1)
    return sign, True


def match_sign(
    s,
    lexicon_nid,
    features: np.ndarray,
    *,
    threshold: float | None = None,
) -> tuple[Any | None, float]:
    """Find the closest AcousticSign in the lexicon. Returns
    ``(sign_nid, similarity)`` if similarity ≥ threshold, else
    ``(None, best_similarity_seen)``. Doesn't mutate the lexicon —
    pure query.

    Threshold resolution mirrors :func:`acquire_sign`: explicit
    keyword wins, otherwise the Lexicon's ``match_threshold`` attr."""
    inner = _native(s)
    threshold = _lexicon_threshold(s, lexicon_nid, threshold)
    existing = lexicon_signs(s, lexicon_nid)
    best: Optional[Any] = None
    best_sim = -1.0
    f = features.astype(np.float32)
    f_norm = float(np.linalg.norm(f))
    if f_norm == 0:
        return None, -1.0
    for sid in existing:
        proto = np.frombuffer(
            inner.node(sid)["attrs"]["features"], dtype=np.float32)
        p_norm = float(np.linalg.norm(proto))
        if p_norm == 0:
            continue
        sim = float(np.dot(f, proto) / (f_norm * p_norm))
        if sim > best_sim:
            best_sim = sim
            best = sid
    if best is not None and best_sim >= threshold:
        return best, best_sim
    return None, best_sim


# --- Grounding: link a Sign to a Concept ------------------------------

def ground_sign(s, sign_nid, concept_nid) -> None:
    """Wire ``sign --denotes--> concept`` — the Peircean mapping
    from form (sign) to object (Concept). The Concept must already
    exist in the graph; this just adds the denotation edge.

    No idempotence check: re-grounding adds a second `denotes` edge.
    Callers who want one-sense-per-sign should check first via
    `denoted_concepts(s, sign)`.
    """
    _native(s).add_edge(sign_nid, DENOTES, concept_nid)


def denoted_concepts(s, sign_nid) -> list:
    """Concepts this AcousticSign points at (via `denotes`). For
    monosemic signs the list has one entry; polysemic ones can have
    multiple."""
    return _native(s).neighbours(sign_nid, DENOTES)


# --- The full pipeline (convenience for the simple case) -------------

def ingest_speech(
    s,
    stream_nid,
    lexicon_nid,
    *,
    n_bands: int = 16,
    n_time_windows: int = 4,
    fs: int = 22050,
    threshold: float | None = None,
    cochlea_bank: list | None = None,
    detect_kwargs: dict | None = None,
    feature_transform=None,
) -> list[tuple[Any, Any, bool]]:
    """End-to-end: detect → extract → acquire-or-match for every
    utterance in the stream. Returns a list of
    ``(utterance_nid, sign_nid, is_new)`` per detected utterance.

    Wires `Utterance -heard_as-> AcousticSign` for each match.

    ``feature_transform``: optional callable applied to each utterance's raw
    cochlear feature vector before acquire_sign — e.g. a relational-invariance
    (ordinal-rank) map so the lexicon's units are gain/speaker-invariant.
    """
    inner = _native(s)
    utterances = detect_utterances(s, stream_nid, **(detect_kwargs or {}))
    # Share one cochlear bank across all utterances (avoid re-minting
    # the same Filters per utterance).
    if cochlea_bank is None:
        cochlea_bank = _audio.cochlea(s, n_bands=n_bands, fs=fs)
    out: list[tuple[Any, Any, bool]] = []
    for u in utterances:
        f = extract_features(
            s, u, n_bands=n_bands, n_time_windows=n_time_windows,
            fs=fs, cochlea_bank=cochlea_bank)
        trajectory = extract_trajectory(
            s, u, n_bands=n_bands, n_frames=n_time_windows,
            fs=fs, cochlea_bank=cochlea_bank)
        if feature_transform is not None:
            f = feature_transform(f)
        sign, is_new = acquire_sign(
            s, lexicon_nid, f, threshold=threshold, trajectory=trajectory)
        if sign is not None:
            inner.add_edge(u, HEARD_AS, sign)
        out.append((u, sign, is_new))
    return out


def project_sign_future_manifold(
    s,
    sign_nid,
    observed_trajectory: list[list[float]],
    bounds: list[list[float]],
    *,
    projection_budget: int | None = None,
    physical_horizon: int | None = None,
) -> dict[str, float] | None:
    """Audit one AcousticSign against the observed future sign shape.

    The sign is the recovered object.  This function produces manifold
    evidence only; it does not choose a word, segment, denotation, or commit.
    The candidate sign carries its forward continuation in
    ``future_manifold_values``.  The observed continuation and its admissible
    tube are graph inputs to the modality-independent Rust projector.
    """
    inner = _native(s)
    attrs = inner.node(sign_nid)["attrs"]
    predicted = attrs.get("future_manifold_values")
    if not isinstance(predicted, list):
        return None
    if not observed_trajectory or not bounds:
        return None
    horizon = int(physical_horizon or len(observed_trajectory))
    budget = int(projection_budget or horizon)
    episode = inner.add_node("SpeechFutureManifoldEpisode", {
        "future_manifold_target": observed_trajectory,
        "future_manifold_bounds": bounds,
    })
    policy = inner.add_node("SpeechFutureManifoldPolicy", {
        "future_manifold_projection_budget": float(budget),
        "future_manifold_physical_horizon": float(horizon),
    })
    fields = (
        "support", "resolved", "termination_code", "horizon", "budget",
        "loss", "information_loss", "retained_width", "anchor_count",
        "refinement_count", "certified_interval_count",
        "ambiguous_interval_count", "max_enclosure_width",
        "max_shape_order", "earliest_decisive_tick",
    )
    reports = {}
    for field in fields:
        term = {
            "type": "FutureManifoldProjection",
            "episode": {"type": "Var", "name": "episode"},
            "policy": {"type": "Var", "name": "policy"},
            "source": {"type": "Var", "name": "sign"},
            "field": field,
        }
        reports[field] = float(inner.evaluate(
            term, {"episode": episode, "policy": policy, "sign": sign_nid}))
    return reports


def report_sign_future_manifolds(
    s,
    lexicon_nid,
    observed_trajectory: list[list[float]],
    bounds: list[list[float]],
    *,
    projection_budget: int | None = None,
    physical_horizon: int | None = None,
) -> list[tuple[Any, dict[str, float]]]:
    """Return evidence for every trajectory-bearing sign in a lexicon.

    The returned collection is intentionally not ranked or collapsed.  The
    graph's later sign-recovery process owns what happens with retained and
    escaped candidates.
    """
    reports = []
    for sign in lexicon_signs(s, lexicon_nid):
        report = project_sign_future_manifold(
            s, sign, observed_trajectory, bounds,
            projection_budget=projection_budget,
            physical_horizon=physical_horizon,
        )
        if report is not None:
            reports.append((sign, report))
    return reports


def link_sign_continuation(s, source_sign, target_sign) -> None:
    """Record a graph-level continuation possibility between two signs.

    This is a semiotic relation, not a word or segment relation.  It narrows
    sequence hypotheses after a sign manifold has supplied a viable temporal
    match.  If a sign has no continuation edges, the open lexicon remains the
    fallback candidate set.
    """
    _native(s).add_edge(source_sign, CONTINUES_TO, target_sign)


def recover_sign_sequence(
    s,
    lexicon_nid,
    observed_trajectory: list[list[float]],
    bounds: list[list[float]],
    *,
    projection_budget: int | None = None,
    max_paths: int = 256,
) -> dict[str, Any]:
    """Recover a continuous stream as a path of signs.

    Candidate signs are tested at every possible stream start.  A match is
    admitted only when the candidate's whole learned trajectory is supported
    by the corresponding acoustic slice; its start and end ticks therefore
    come from the sign manifold itself.  No word, phoneme, silence, or segment
    boundary is supplied.

    The returned ``events`` are sign-level temporal events.  ``paths`` are
    graph-consistent sequences that cover the stream from tick zero to its end;
    ``matches`` exposes all locally supported sign hypotheses, including ones
    that do not participate in a complete path.  This keeps ambiguity visible
    instead of turning a local match into a word-level winner.
    """
    if len(observed_trajectory) != len(bounds) or max_paths <= 0:
        return {"matches": [], "paths": [], "truncated": False}

    inner = _native(s)
    signs = lexicon_signs(s, lexicon_nid)
    candidates = []
    for sign in signs:
        values = inner.node(sign)["attrs"].get("future_manifold_values")
        if isinstance(values, list) and values:
            candidates.append((sign, values))

    matches_by_start: dict[int, list[dict[str, Any]]] = {}
    matches = []
    stream_length = len(observed_trajectory)
    for start in range(stream_length):
        for sign, values in candidates:
            length = len(values)
            end = start + length
            if end > stream_length:
                continue
            report = project_sign_future_manifold(
                s, sign,
                observed_trajectory[start:end], bounds[start:end],
                projection_budget=projection_budget,
                physical_horizon=length,
            )
            if report is None:
                continue
            if (
                report.get("support") != 1.0
                or report.get("resolved") != 1.0
                or report.get("loss") != 0.0
                or report.get("horizon") != float(length)
            ):
                continue
            match = {
                "sign": sign,
                "start_tick": float(start),
                "end_tick": float(end),
                "report": report,
            }
            matches_by_start.setdefault(start, []).append(match)
            matches.append(match)

    def successors(sign):
        linked = inner.neighbours(sign, CONTINUES_TO)
        return linked if linked else signs

    # A path is extended only when the next sign starts exactly where the
    # previous sign's supported trajectory ends.  That adjacency is inferred
    # from the manifolds; it is not an externally declared word boundary.
    paths = []
    frontier = [
        [{"sign": match["sign"], "start_tick": match["start_tick"],
          "end_tick": match["end_tick"], "report": match["report"]}]
        for match in matches_by_start.get(0, [])
    ]
    truncated = False
    while frontier:
        next_frontier = []
        for path in frontier:
            end = int(path[-1]["end_tick"])
            if end == stream_length:
                paths.append(path)
                if len(paths) >= max_paths:
                    truncated = bool(next_frontier or frontier)
                    break
                continue
            for match in matches_by_start.get(end, []):
                if match["sign"] not in successors(path[-1]["sign"]):
                    continue
                next_frontier.append(path + [{
                    "sign": match["sign"],
                    "start_tick": match["start_tick"],
                    "end_tick": match["end_tick"],
                    "report": match["report"],
                }])
                if len(next_frontier) + len(paths) >= max_paths:
                    truncated = True
                    break
            if truncated:
                break
        if truncated or not next_frontier:
            break
        frontier = next_frontier

    return {
        "matches": matches,
        "paths": [{
            "signs": [event["sign"] for event in path],
            "events": path,
            "start_tick": path[0]["start_tick"],
            "end_tick": path[-1]["end_tick"],
        } for path in paths],
        "truncated": truncated,
    }


def recover_sign_stream(
    s,
    lexicon_nid,
    observed_trajectory: list[list[float]],
    bounds: list[list[float]],
    *,
    projection_budget: int | None = None,
) -> list[dict[str, Any]]:
    """Project and audit a continuous acoustic trajectory one tick at a time.

    Each entry is a time-indexed sign-evidence snapshot.  The observed prefix
    may end in the middle of any linguistic unit; no word, phoneme, segment,
    or silence boundary is consulted.  ``reports`` remains a collection of
    sign reports.  ``retained_signs`` are still inside their projected tube
    at that tick; ``escaped_signs`` are candidates whose prediction first left
    the observed tube.  Neither list is a commitment or a sentence decode.
    """
    if len(observed_trajectory) != len(bounds):
        return []
    timeline = []
    for end in range(1, len(observed_trajectory) + 1):
        reports = report_sign_future_manifolds(
            s, lexicon_nid,
            observed_trajectory[:end], bounds[:end],
            projection_budget=projection_budget,
            physical_horizon=end,
        )
        escaped = [
            sign for sign, report in reports
            if report.get("earliest_decisive_tick") == float(end)
        ]
        retained = [
            sign for sign, report in reports
            if report.get("support") == 1.0
            and report.get("loss") == 0.0
            and report.get("retained_width", 0.0) > 0.0
        ]
        timeline.append({
            "time": float(end),
            "reports": reports,
            "retained_signs": retained,
            "escaped_signs": escaped,
        })
    return timeline


# --- Diagnostics -------------------------------------------------------

def sign_describe(s, sign_nid) -> dict:
    """Human/agent-readable snapshot of an AcousticSign."""
    inner = _native(s)
    a = inner.node(sign_nid)["attrs"]
    denoted = denoted_concepts(s, sign_nid)
    return {
        "id": sign_nid,
        "label": a.get("label"),
        "hearings": int(a.get("hearings", 0)),
        "feature_length": int(a.get("feature_length", 0)),
        "denotes_count": len(denoted),
        "origin": a.get("origin", ""),
        "last_similarity": a.get("last_similarity"),
    }


def lexicon_grounded_fraction(s, lexicon_nid) -> float:
    """Fraction of signs in the lexicon that have at least one
    `denotes` edge — the agent's grounding ratio. Starts at 0
    (unsupervised acquisition produces ungrounded signs), grows as
    a teacher provides Concepts."""
    signs = lexicon_signs(s, lexicon_nid)
    if not signs:
        return 0.0
    grounded = sum(1 for sid in signs if denoted_concepts(s, sid))
    return grounded / len(signs)


__all__ = [
    "LEXICON", "ACOUSTIC_SIGN", "UTTERANCE",
    "HAS_ENTRY", "HEARD_AS", "DENOTES", "FROM_STREAM", "CONTINUES_TO",
    "seed_speech_grammar",
    "open_lexicon", "lexicon_signs", "lexicon_describe",
    "detect_utterances", "extract_features",
    "extract_trajectory",
    "acquire_sign", "match_sign",
    "ground_sign", "denoted_concepts",
    "ingest_speech",
    "project_sign_future_manifold", "report_sign_future_manifolds",
    "link_sign_continuation", "recover_sign_sequence", "recover_sign_stream",
    "sign_describe", "lexicon_grounded_fraction",
]
