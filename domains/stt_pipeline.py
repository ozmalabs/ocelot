"""STTPipeline — top-level world adapter that wires the full
biology-aligned auditory pathway onto a substrate and gives the
caller three operations:

  ingest(audio)        Process audio through the pathway. Returns
                       the list of AcousticSigns that were heard.
  teach(audio, label)  Same as ingest, but then ground each heard
                       sign to a Concept{name=label}. The lexicon
                       learns from supervised pairs of audio +
                       label.
  transcribe(audio)    Process audio, return a text string of
                       recognised labels (signs grounded to
                       Concepts; ungrounded signs become "[?]").

The full pathway: cochlea → cochlear_nucleus → IC → A1 →
categorical_perception → lexical_access. Each layer is graph-
resident; the adapter wires them per-stream and runs the substrate
pipeline.

Multiple streams share the substrate's Phoneme + AcousticLexicon
nodes — the agent's vocabulary accumulates across all audio it
hears.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import json as _json
import pathlib as _pathlib

import numpy as np

from .auditory_cortex import attach_a1_pipeline
from .categorical_perception import attach_categorical_perception
from .cochlear_nucleus import attach_default_pipeline as attach_cochlear
from .lexical_access import attach_lexical_access
from .sonority_valley import attach_sonority_valley


_SEED_DIR = _pathlib.Path(__file__).resolve().parent.parent / "seeds"


def _manifest_for(seed_id: str) -> dict:
    """Read the captured seed manifest seeds/<id>.json. Pure file I/O
    (world-adapter work) — the Rust runtime's
    ``Substrate.load_seed_manifest`` does the graph mutation. Replaces
    the old ``substrate.seed_loader.manifest_for`` so the live STT path
    no longer imports the legacy Python substrate."""
    return _json.loads((_SEED_DIR / f"{seed_id}.json").read_text())


def _rust(sub):
    return sub._inner if hasattr(sub, "_inner") else sub


def _node_sort_key(n):
    """Stable sort key for NodeIDs — use the underlying u32 if it's
    exposed, else fall back to repr (substrate_rs._native.NodeID
    doesn't implement int() but has .value)."""
    v = getattr(n, "value", None)
    return v if v is not None else repr(n)


def _estimate_f0(samples: np.ndarray, fs: int,
                   fmin: float = 70.0, fmax: float = 400.0) -> float:
    """Estimate fundamental frequency via autocorrelation. Returns
    Hz, or 0.0 if the signal is unvoiced / too short / no peak.

    Searches lags corresponding to [fmin, fmax] Hz, picks the
    largest peak. Voiced threshold: peak score must be > 30% of
    the zero-lag energy (typical heuristic). Cheap, single-frame —
    we'll average across the utterance by computing on a few
    windows and taking the median.
    """
    n = len(samples)
    lag_min = int(fs / fmax)
    lag_max = int(fs / fmin)
    if n < lag_max * 2 or lag_min < 1:
        return 0.0
    # Take a few overlapping windows + median the per-window F0
    # estimate. Less sensitive to brief unvoiced regions.
    win = min(int(0.04 * fs), n)  # 40ms windows
    hop = max(win // 2, 1)
    f0s: list[float] = []
    energy_floor = 0.001
    for start in range(0, n - win, hop):
        x = samples[start:start + win]
        zero_lag = float(np.dot(x, x))
        if zero_lag < energy_floor:
            continue
        best_score = 0.0
        best_lag = 0
        for lag in range(lag_min, min(lag_max, win // 2)):
            s = float(np.dot(x[:-lag], x[lag:]))
            if s > best_score:
                best_score = s
                best_lag = lag
        # Voiced criterion: peak > 30% of zero-lag.
        if best_lag > 0 and best_score / zero_lag > 0.30:
            f0s.append(fs / best_lag)
    if not f0s:
        return 0.0
    return float(np.median(f0s))


def _resonator_bandpass(x: np.ndarray, fs: int, centre_hz: float,
                            q: float = 4.0) -> np.ndarray:
    """2nd-order IIR bandpass (constant-skirt, biquad). Mimics one
    formant resonance — useful as a vocal-tract filter applied to
    a source signal. Direct-form 1 transposed; cheap enough inline.
    """
    omega = 2.0 * np.pi * centre_hz / fs
    alpha = np.sin(omega) / (2.0 * q)
    cos_o = np.cos(omega)
    # Biquad bandpass coefficients (RBJ cookbook).
    b0 = alpha
    b1 = 0.0
    b2 = -alpha
    a0 = 1.0 + alpha
    a1 = -2.0 * cos_o
    a2 = 1.0 - alpha
    b0n, b1n, b2n = b0 / a0, b1 / a0, b2 / a0
    a1n, a2n = a1 / a0, a2 / a0
    y = np.zeros_like(x)
    x1 = x2 = 0.0
    y1 = y2 = 0.0
    for n in range(len(x)):
        xn = float(x[n])
        yn = (b0n * xn + b1n * x1 + b2n * x2
                - a1n * y1 - a2n * y2)
        y[n] = yn
        x2 = x1; x1 = xn
        y2 = y1; y1 = yn
    return y


def _reconcile_groups(groups: list[list], n_words: int) -> list[list]:
    """Make `groups` match `n_words` in length. If too many groups,
    merge smallest adjacent pairs. If too few, split largest groups
    proportionally. Pure list manipulation, no graph state."""
    if not groups or n_words <= 0:
        return groups
    if len(groups) == n_words:
        return groups
    if len(groups) > n_words:
        # Merge smallest adjacent pairs.
        while len(groups) > n_words and len(groups) > 1:
            # Find adjacent pair with smallest combined size.
            best_i = 0
            best_size = len(groups[0]) + len(groups[1])
            for i in range(1, len(groups) - 1):
                size = len(groups[i]) + len(groups[i + 1])
                if size < best_size:
                    best_size = size
                    best_i = i
            groups = (groups[:best_i]
                       + [groups[best_i] + groups[best_i + 1]]
                       + groups[best_i + 2:])
        return groups
    # Too few groups → split largest.
    while len(groups) < n_words:
        # Find largest group.
        best_i = max(range(len(groups)), key=lambda i: len(groups[i]))
        big = groups[best_i]
        if len(big) < 2:
            break  # can't split a singleton
        half = len(big) // 2
        groups = groups[:best_i] + [big[:half], big[half:]] + groups[best_i + 1:]
    return groups


# Default cochlear band layout — 32 log-spaced bands from 80 to
# 7500 Hz. MelHuBERT 2022 + ZeroSpeech baselines converged on 40
# mel channels as the sweet spot; 32 is a touch under (8 bits of
# headroom for the dispatcher / DTW / trajectory store). The
# substrate's gammatone bank approximates the same log-tonotopic
# layout biology uses.
import math as _math
_LOG_LO = _math.log(80.0)
_LOG_HI = _math.log(7500.0)
DEFAULT_BANDS = [
    _math.exp(_LOG_LO + (_LOG_HI - _LOG_LO) * i / 31.0)
    for i in range(32)
]


@dataclass
class STTParams:
    """Tunable substrate-STT knobs. All defaults are reasonable
    starting points; production deployments will tune these against
    a real corpus."""
    sample_rate: int = 22050
    band_centres_hz: tuple = tuple(DEFAULT_BANDS)
    # lexical_access — DTW distance threshold. DTW-Euclidean on
    # unit-normalised multi-channel trajectories tightens as the
    # channel count grows:
    #     6 channels  wanted 0.10  (FSDD acc 33.6%)
    #     25 channels wants  0.02  (FSDD acc 44.4%)
    # Calibrated for the current 25-patch A1 library + 32-band
    # cochlear stack. Sweep confirmed 0.02 is the empirical peak
    # — tighter loses signal (over-clusters with one-shot signs),
    # looser merges genuinely-distinct units. Agent's tune-Rule
    # can re-find the right value per corpus.
    la_distance_threshold: float = 0.02
    # categorical_perception
    cp_distance_threshold: float = 0.05
    cp_sample_interval_ms: float = 25.0
    cp_smoothing_ms: float = 40.0
    cp_min_magnitude: float = 0.01
    # sonority_valley (word-boundary detector)
    sv_smoothing_ms: float = 30.0
    sv_min_separation_ms: float = 80.0
    sv_depth_threshold: float = 0.30
    # lexical_access
    gap_threshold_ms: float = 80.0
    lexicon_name: str = "stt"
    # Warped formant-dense front-end (the agent's runtime_design
    # request). When True, the pipeline replaces the default log
    # layout with a warped one that oversamples 250-2500 Hz and adds
    # extra A1 patches at formant-region centres. Same gammatone
    # primitive, just more bands where F1/F2 live. See
    # domains.formant_frontend (the mechanical generator) and
    # domains.runtime_design.agent_specify_frontend (the spec).
    warped_frontend: bool = False
    warped_extra_patches: bool = True

    @classmethod
    def warped(cls, **kw):
        """Build params with the agent's warped formant-dense
        front-end. ``band_centres_hz`` is overridden with the warped
        layout unless the caller passes one explicitly."""
        from .formant_frontend import warped_band_centres
        if "band_centres_hz" not in kw:
            kw["band_centres_hz"] = tuple(warped_band_centres())
        kw["warped_frontend"] = True
        return cls(**kw)


class STTPipeline:
    """Substrate-native STT adapter.

    Lifecycle:
        attach(sub)            load all required seeds (idempotent)
        ingest(sub, audio)     process one audio buffer
        teach(sub, audio, w)   process + ground signs to a label
        transcribe(sub, audio) process + emit text

    The pipeline IS graph-resident (Operation nodes per stream);
    this adapter just orchestrates seed loading, stream creation,
    and post-run graph queries.
    """

    def __init__(self, params: STTParams | None = None) -> None:
        self.params = params or STTParams()
        # Per-substrate cache of the shared audio-pipeline ops.
        # Keyed by id(substrate); populated on first _build_stream
        # call. After that, per-stream setup is just mint an
        # AudioStream + wire has_pipeline_entry edges to the cached
        # gammatone ops. The pipeline ops themselves are shared
        # across every stream the substrate sees.
        self._pipeline_cache: dict = {}

    def attach(self, sub) -> None:
        """Load the seeds the STT pipeline needs. Idempotent."""
        for seed_id in (
            "audio", "cochlear_nucleus", "inferior_colliculus",
            "auditory_cortex", "categorical_perception",
            "sonority_valley", "speech", "lexical_access",
            "tunable_parameter", "reconsider",
            "compositional_chunking", "speech_bootstrap",
        ):
            try:
                sub.load_seed_manifest(_manifest_for(seed_id))
            except Exception:
                # Already loaded; the seed loader raises on dup
                # productions, which is fine.
                pass
        # Mint the speech-concept vocabulary + tag existing
        # instance nodes with is_a edges. Idempotent; safe to call
        # every attach.
        from .speech_bootstrap import bootstrap_speech_concepts
        bootstrap_speech_concepts(sub)

    def _ensure_audio_pipeline(self, sub) -> dict:
        """Build the shared audio pipeline ops once per substrate.
        Subsequent calls return the cached entry — O(1) instead of
        the O(total_ops) walk attach_* would do per ingest. After
        this returns, each per-stream call just mints an AudioStream
        and adds has_pipeline_entry edges to the cached gammatone
        ops.

        The pipeline ops are graph data; the cache here is just a
        Python-side reference to skip re-iterating Operation nodes.
        """
        key = id(sub)
        if key in self._pipeline_cache:
            return self._pipeline_cache[key]
        p = self.params
        # Persistence path: if the substrate was loaded from a
        # saved session, the audio pipeline ops already exist in
        # the graph (along with a template AudioStream marked
        # `_pipeline_template: True`). Detect that and rebuild the
        # cache pointing at the existing ops — minting fresh ops
        # would duplicate every gammatone / patch_evaluate node
        # and break trajectory channel-count consistency for the
        # saved AcousticSigns.
        existing_template = None
        for s in sub.nodes("AudioStream"):
            if sub.node(s)["attrs"].get("_pipeline_template"):
                existing_template = s
                break
        if existing_template is not None:
            existing_gammatones = []
            for op in sub.nodes("Operation"):
                a = sub.node(op)["attrs"]
                if a.get("kind") == "gammatone":
                    existing_gammatones.append(op)
            entry = {"gammatone_ops": existing_gammatones}
            self._pipeline_cache[key] = entry
            return entry
        # Fresh-substrate path: mint the pipeline from scratch.
        template = sub.add_node("AudioStream", {
            "codec": "raw_pcm",
            "sample_rate": int(p.sample_rate),
            "_pipeline_template": True,
        })
        cochlear = attach_cochlear(
            sub, template,
            band_centres_hz=list(p.band_centres_hz),
            sample_rate=int(p.sample_rate),
        )
        # Agent's warped front-end: add extra A1 patches at dense
        # formant-region centres before wiring. attach_a1_pipeline
        # mints one patch_evaluate per A1Patch node present, so any
        # patches added here are picked up automatically.
        if p.warped_frontend and p.warped_extra_patches:
            from .formant_frontend import warped_patch_library
            existing = {sub.node(n)["attrs"].get("name")
                        for n in sub.nodes("A1Patch")}
            for patch in warped_patch_library():
                if patch["name"] in existing:
                    continue
                sub.add_node("A1Patch", patch)
        attach_a1_pipeline(sub, template)
        attach_categorical_perception(
            sub, template,
            sample_interval_ms=p.cp_sample_interval_ms,
            distance_threshold=p.cp_distance_threshold,
        )
        # Tune the CP op's smoothing + magnitude floor.
        for op in sub.nodes("Operation"):
            attrs = sub.node(op)["attrs"]
            if attrs.get("kind") != "categorical_perception":
                continue
            sub.set_attr(op, "feature_smoothing_ms",
                          float(p.cp_smoothing_ms))
            sub.set_attr(op, "min_magnitude", float(p.cp_min_magnitude))
        attach_sonority_valley(
            sub, template,
            smoothing_ms=p.sv_smoothing_ms,
            min_separation_ms=p.sv_min_separation_ms,
            depth_threshold=p.sv_depth_threshold,
        )
        attach_lexical_access(sub, template, lexicon_name=p.lexicon_name)
        # Tune the LA op's threshold attrs.
        for op in sub.nodes("Operation"):
            attrs = sub.node(op)["attrs"]
            if attrs.get("kind") != "lexical_access":
                continue
            sub.set_attr(op, "gap_threshold_ms",
                          float(p.gap_threshold_ms))
            sub.set_attr(op, "distance_threshold",
                          float(p.la_distance_threshold))
        entry = {
            "gammatone_ops": cochlear["gammatone_ops"],
        }
        self._pipeline_cache[key] = entry
        return entry

    def _build_stream(self, sub):
        """Mint an AudioStream + wire its has_pipeline_entry edges to
        the shared pipeline. First call per substrate builds the
        pipeline; subsequent calls are O(n_bands)."""
        pipeline = self._ensure_audio_pipeline(sub)
        p = self.params
        stream = sub.add_node(
            "AudioStream",
            {"codec": "raw_pcm", "sample_rate": int(p.sample_rate)},
        )
        for gt_op in pipeline["gammatone_ops"]:
            sub.add_edge(stream, "has_pipeline_entry", gt_op)
        # All downstream ops (envelope / onset_detect /
        # broadband_coincidence / IC / A1 / CP / SV / LA) are
        # already shared and wired by _ensure_audio_pipeline above.
        # Per-stream output (Utterances, audio events) is minted by
        # the dispatch helpers using the audio_stream_nid passed
        # to run_audio_pipeline. Compositional chunking is purely
        # graph Rules fired by sub.tick().
        return stream

    # --- core operations -------------------------------------------

    def ingest(self, sub, audio_samples: np.ndarray) -> list:
        """Process one audio buffer through the pipeline. Returns
        the list of AcousticSign NodeIDs that the new Utterances
        heard_as'd.

        Also EMA-updates each grounded sign's `f0_hz` attr from
        the audio's estimated fundamental — gives speak() a
        per-sign voicing pitch so synthesis matches the lexicon's
        learned voice rather than a fixed 120 Hz fallback.
        """
        stream = self._build_stream(sub)
        raw = np.ascontiguousarray(audio_samples,
                                      dtype=np.float32).tobytes()
        _rust(sub).run_audio_pipeline(
            stream, raw, int(self.params.sample_rate))
        # Estimate F0 once for this ingest — same audio over the
        # whole utterance, EMA the per-sign attr toward it.
        f0 = _estimate_f0(audio_samples, int(self.params.sample_rate))
        signs = []
        for utt in sub.in_neighbours(stream, "from_stream"):
            if sub.node(utt)["type"] != "Utterance":
                continue
            for s in sub.neighbours(utt, "heard_as"):
                signs.append(s)
                if f0 > 0:
                    a = sub.node(s)["attrs"]
                    prev = float(a.get("f0_hz", 0.0))
                    h = max(int(a.get("hearings", 1)), 1)
                    alpha = 1.0 / float(h)
                    new_f0 = (f0 if prev <= 0
                                else prev * (1.0 - alpha) + f0 * alpha)
                    sub.set_attr(s, "f0_hz", float(new_f0))
        return signs

    def refine_lexicon(self, sub,
                          merge_distance: float = 0.06,
                          vote_counts: dict | None = None,
                          require_dominant_word: bool = True) -> dict:
        """Iterative-refinement pass — HuBERT-style. After training,
        walk the lexicon and merge sign pairs that the in-streaming
        threshold left as separate but are effectively the same
        sound: DTW distance below `merge_distance` (wider than the
        per-ingest threshold) AND their top-voted word agrees (or
        one's votes are absent — implies low-evidence duplicate of
        the other).

        Merged signs sum hearings, average trajectories
        (hearing-weighted), and (if vote_counts is given) sum
        their per-word vote tallies. The losing sign's `denotes`
        edges are redirected to the surviving sign, then it's
        deleted.

        The point: clusters that the streaming threshold couldn't
        decide between converge once we see the full distribution.
        Same idea as HuBERT iterating k-means on better features —
        we're iterating clustering on the lexicon itself.
        """
        # Locate the lex.
        lex_nid = None
        for n in sub.nodes("AcousticLexicon"):
            if sub.node(n)["attrs"].get("name") == self.params.lexicon_name:
                lex_nid = n
                break
        if lex_nid is None:
            return {"merged": 0, "before": 0, "after": 0}

        # Snapshot the sign data.
        signs = list(sub.neighbours(lex_nid, "has_entry"))
        sign_data = []
        for s in signs:
            a = sub.node(s)["attrs"]
            if a.get("composed", False):
                continue  # skip compositional signs; they're chunked
            traj_tuple = a.get("trajectory")
            if not traj_tuple:
                continue
            traj = np.asarray([float(t) for t in traj_tuple],
                                dtype=np.float32)
            sign_data.append({
                "sign": s,
                "traj": traj,
                "hearings": int(a.get("hearings", 1)),
                "f0_hz": float(a.get("f0_hz", 0.0)),
            })
        n_before = len(sign_data)
        if n_before < 2:
            return {"merged": 0, "before": n_before, "after": n_before}

        # Figure out n_patches so DTW frame Euclidean works.
        # The lexical_access op stores trajectory_samples; assume
        # default 32 if not available. Patch count = traj_len / 32.
        spp = 32  # matches lexical_access default trajectory_samples
        # If the trajectory length doesn't divide cleanly, infer
        # patches from the first sign's stored channel count.
        traj_len = len(sign_data[0]["traj"])
        if traj_len % spp != 0:
            spp = max(1, traj_len // 6)  # fall back: 6 patches × spp
        n_patches = max(1, traj_len // spp)

        def dtw_dist(a, b):
            """Banded DTW-Euclidean between two flat multi-channel
            trajectories. Pure Python — n²/8 ops on 32×32 frames
            is fine for the post-training cleanup pass."""
            if len(a) != len(b):
                return float("inf")
            band = max(2, spp // 4)
            inf = float("inf")
            prev = [inf] * (spp + 1)
            curr = [inf] * (spp + 1)
            prev[0] = 0.0
            for i in range(1, spp + 1):
                jlo = max(1, i - band)
                jhi = min(spp, i + band)
                for j in range(spp + 1):
                    curr[j] = inf
                ai = (i - 1) * n_patches
                for j in range(jlo, jhi + 1):
                    bj = (j - 1) * n_patches
                    s = 0.0
                    for k in range(n_patches):
                        d = a[ai + k] - b[bj + k]
                        s += d * d
                    s = s ** 0.5
                    curr[j] = s + min(prev[j], curr[j - 1],
                                          prev[j - 1])
                prev, curr = curr, prev
            return prev[spp] / spp

        def top_word(sign_id):
            if vote_counts is None:
                return None
            sk = _node_sort_key(sign_id)
            best_w = None
            best_c = -1
            for (sgn_k, w), c in vote_counts.items():
                if sgn_k != sk:
                    continue
                if c > best_c:
                    best_c = c
                    best_w = w
            return best_w

        # Greedy merge: sort signs by hearings desc; for each, find
        # any later sign close enough + with compatible top-word,
        # merge into the bigger one.
        sign_data.sort(key=lambda d: -d["hearings"])
        merged_into: dict = {}  # losing sign -> winner sign
        merged_count = 0
        for i in range(len(sign_data)):
            a = sign_data[i]
            if a["sign"] in merged_into:
                continue
            for j in range(i + 1, len(sign_data)):
                b = sign_data[j]
                if b["sign"] in merged_into:
                    continue
                d = dtw_dist(a["traj"], b["traj"])
                if d > merge_distance:
                    continue
                # Vote compatibility — same top-voted word OR one
                # has no votes (it's a low-evidence dupe).
                a_top = top_word(a["sign"])
                b_top = top_word(b["sign"])
                if (vote_counts is not None
                        and a_top is not None
                        and b_top is not None
                        and a_top != b_top):
                    continue
                # Merge b into a. Hearing-weighted average of
                # trajectories, sum hearings, F0 EMA, vote sum.
                ah, bh = a["hearings"], b["hearings"]
                total = max(ah + bh, 1)
                new_traj = (a["traj"] * ah + b["traj"] * bh) / total
                # Re-normalise.
                norm = float(np.linalg.norm(new_traj))
                if norm > 1e-9:
                    new_traj = new_traj / norm
                a["traj"] = new_traj
                a["hearings"] = ah + bh
                if a["f0_hz"] > 0 and b["f0_hz"] > 0:
                    a["f0_hz"] = (a["f0_hz"] * ah + b["f0_hz"] * bh) / total
                elif b["f0_hz"] > 0:
                    a["f0_hz"] = b["f0_hz"]
                merged_into[b["sign"]] = a["sign"]
                merged_count += 1
        # Apply merges to the substrate.
        from substrate_rs import speech as _sp
        rust_sub = _rust(sub)
        traj_sym = "trajectory"
        for d in sign_data:
            s = d["sign"]
            if s in merged_into:
                continue
            # Write back updated trajectory + hearings + f0_hz.
            tup = tuple(float(x) for x in d["traj"])
            sub.set_attr(s, traj_sym, tup)
            sub.set_attr(s, "hearings", int(d["hearings"]))
            if d["f0_hz"] > 0:
                sub.set_attr(s, "f0_hz", float(d["f0_hz"]))
        # For merged losers: redirect denotes edges to the winner,
        # then delete the loser.
        for loser, winner in merged_into.items():
            for concept in list(sub.neighbours(loser, "denotes")):
                if concept not in list(sub.neighbours(winner, "denotes")):
                    _sp.ground_sign(rust_sub, winner, concept)
            # Sum vote_counts entries.
            if vote_counts is not None:
                lk = _node_sort_key(loser)
                wk = _node_sort_key(winner)
                losers_votes = [(w, c) for (sk, w), c in vote_counts.items()
                                  if sk == lk]
                for w, c in losers_votes:
                    vote_counts[(wk, w)] = vote_counts.get((wk, w), 0) + c
                    vote_counts.pop((lk, w), None)
            # Delete the loser via remove_node (cascades edges).
            try:
                rust_sub.remove_node(loser)
            except Exception:
                pass

        return {
            "merged": merged_count,
            "before": n_before,
            "after": n_before - merged_count,
        }

    def teach(self, sub, audio_samples: np.ndarray,
                label: str) -> dict:
        """Process audio + ground each resulting AcousticSign to a
        Concept{name=label}. The supervised path: agent hears the
        audio AND is told what it means; lexicon learns the
        binding.

        Returns a summary: {label, signs_grounded, concept_id}.
        """
        signs = self.ingest(sub, audio_samples)
        # Find or mint the Concept node.
        concept_id = None
        for c in sub.nodes("Concept"):
            if sub.node(c)["attrs"].get("name") == label:
                concept_id = c
                break
        if concept_id is None:
            concept_id = sub.add_node("Concept", {"name": label})
        # Ground each sign to the concept (via speech.ground_sign,
        # which is just an add_edge).
        from substrate_rs import speech as _sp
        n_grounded = 0
        for sig in signs:
            # Skip if the sign is already grounded to this concept.
            existing = list(sub.neighbours(sig, "denotes"))
            if concept_id in existing:
                continue
            _sp.ground_sign(_rust(sub), sig, concept_id)
            n_grounded += 1
        return {
            "label": label,
            "signs_grounded": n_grounded,
            "concept_id": concept_id,
            "signs": signs,
        }

    def transcribe(self, sub, audio_samples: np.ndarray) -> str:
        """Process audio, return the recognised text — labels of
        grounded signs joined by spaces. Ungrounded signs become
        '[?]' placeholders."""
        signs = self.ingest(sub, audio_samples)
        out: list[str] = []
        for sig in signs:
            concepts = list(sub.neighbours(sig, "denotes"))
            if concepts:
                name = sub.node(concepts[0])["attrs"].get("name", "[?]")
                out.append(str(name))
            else:
                out.append("[?]")
        return " ".join(out)

    def speak(self, sub, word: str,
              duration_s: float = 0.35,
              f0_hz: float | None = None,
              q_factor: float = 4.0) -> np.ndarray:
        """Generate audio for `word` from the substrate's own
        lexicon. Thin world-adapter wrapper around the Rust
        source-filter voicebox primitive (audio_primitives.rs ::
        synthesize_from_trajectory).

        Adapter does the graph lookup (Concept → most-heard sign
        → trajectory + patch metadata) and hands the resulting
        arrays to the substrate's native synthesise. The
        synthesis itself is in Rust; the composition (which sign,
        which patches, what duration / pitch / Q) is graph data
        the adapter reads.

        Substrate lexicon is bidirectional — same nodes recognise
        AND produce. No separate generative model, no numpy
        synthesis path.
        """
        fs = int(self.params.sample_rate)
        n_out = max(int(duration_s * fs), 1)
        target = word.lower()

        concept = None
        for c in sub.nodes("Concept"):
            if sub.node(c)["attrs"].get("name") == target:
                concept = c
                break
        if concept is None:
            return np.zeros(n_out, dtype=np.float32)

        best_sign = None
        best_hearings = -1
        for s in sub.in_neighbours(concept, "denotes"):
            if sub.node(s)["type"] != "AcousticSign":
                continue
            h = int(sub.node(s)["attrs"].get("hearings", 0))
            if h > best_hearings:
                best_hearings = h
                best_sign = s
        if best_sign is None:
            return np.zeros(n_out, dtype=np.float32)

        traj_tuple = sub.node(best_sign)["attrs"].get("trajectory")
        if not traj_tuple:
            return np.zeros(n_out, dtype=np.float32)
        traj = [float(t) for t in traj_tuple]

        # Read patch metadata from the graph in the same alphabetical
        # order lexical_access used to build the trajectory.
        patches: list[tuple[str, float, float, str]] = []
        for p in sub.nodes("A1Patch"):
            a = sub.node(p)["attrs"]
            patches.append((a.get("name", ""),
                              float(a.get("centre_hz", 1000.0)),
                              float(a.get("freq_sigma_hz", 400.0)),
                              a.get("kind", "sustained")))
        patches.sort(key=lambda t: t[0])
        if not patches:
            return np.zeros(n_out, dtype=np.float32)

        spp = len(traj) // len(patches)
        if spp == 0:
            return np.zeros(n_out, dtype=np.float32)

        # Clamp centre frequencies safely under Nyquist — biquads at
        # centre_hz >= fs/2 are unstable and produce NaN audio.
        # Necessary for low-sample-rate corpora like FSDD (8 kHz)
        # where default sibilant/burst patches are above Nyquist.
        nyquist_safe = float(fs) / 2.0 * 0.95
        patch_centres = [min(c, nyquist_safe) for _, c, _, _ in patches]
        patch_sigmas = [s for _, _, s, _ in patches]
        patch_kinds = [k for _, _, _, k in patches]
        patch_is_sibilant = ["sib" in n for n, _, _, _ in patches]

        # Use the sign's learned F0 if available, else fall back
        # to caller-provided f0_hz, else 120 Hz default. The
        # learned F0 is what makes synthesis sound like the voice
        # the lexicon was taught on.
        if f0_hz is None:
            sign_f0 = float(sub.node(best_sign)["attrs"].get("f0_hz", 0.0))
            effective_f0 = sign_f0 if sign_f0 > 0 else 120.0
        else:
            effective_f0 = float(f0_hz)

        audio_bytes = _rust(sub).synthesize_from_trajectory(
            traj, patch_centres, patch_sigmas,
            patch_kinds, patch_is_sibilant,
            spp, n_out, fs, effective_f0, float(q_factor),
        )
        return np.frombuffer(audio_bytes, dtype=np.float32).copy()

    def speak_trajectory(self, sub, trajectory,
                          duration_s: float = 0.4,
                          f0_hz: float | None = None,
                          q_factor: float = 4.0) -> np.ndarray:
        """Synthesise audio from an EXPLICIT A1-patch trajectory (rather than a
        word's stored most-heard sign). Thin world-adapter: reads the graph's A1
        patch layout (same alphabetical order lexical_access uses), clamps centres
        under Nyquist, and hands trajectory + patches to the Rust voicebox. The
        analysis-by-synthesis loop uses this to voice a word→sound FORWARD MODEL
        whose per-word trajectory is graph data (e.g. the mean trajectory of a
        word's exemplars) in the HEARD voice (f0). Synthesis is in Rust; the
        trajectory + voice are graph/adapter data."""
        fs = int(self.params.sample_rate)
        n_out = max(int(duration_s * fs), 1)
        traj = [float(t) for t in trajectory]
        if not traj:
            return np.zeros(n_out, dtype=np.float32)
        patches: list[tuple[str, float, float, str]] = []
        for p in sub.nodes("A1Patch"):
            a = sub.node(p)["attrs"]
            patches.append((a.get("name", ""),
                            float(a.get("centre_hz", 1000.0)),
                            float(a.get("freq_sigma_hz", 400.0)),
                            a.get("kind", "sustained")))
        patches.sort(key=lambda t: t[0])
        if not patches:
            return np.zeros(n_out, dtype=np.float32)
        spp = len(traj) // len(patches)
        if spp == 0:
            return np.zeros(n_out, dtype=np.float32)
        nyquist_safe = float(fs) / 2.0 * 0.95
        patch_centres = [min(c, nyquist_safe) for _, c, _, _ in patches]
        patch_sigmas = [s for _, _, s, _ in patches]
        patch_kinds = [k for _, _, _, k in patches]
        patch_is_sibilant = ["sib" in n for n, _, _, _ in patches]
        effective_f0 = float(f0_hz) if f0_hz and f0_hz > 0 else 120.0
        audio_bytes = _rust(sub).synthesize_from_trajectory(
            traj, patch_centres, patch_sigmas,
            patch_kinds, patch_is_sibilant,
            spp, n_out, fs, effective_f0, float(q_factor),
        )
        return np.frombuffer(audio_bytes, dtype=np.float32).copy()

    def speak_sequence(self, sub, words: list[str],
                          gap_s: float = 0.05) -> np.ndarray:
        """Concatenate `speak(word)` for each word in `words` with
        a small silence gap between. Returns the full audio."""
        fs = int(self.params.sample_rate)
        gap = np.zeros(int(gap_s * fs), dtype=np.float32)
        parts: list[np.ndarray] = []
        for w in words:
            parts.append(self.speak(sub, w))
            parts.append(gap)
        if not parts:
            return np.zeros(1, dtype=np.float32)
        return np.concatenate(parts)

    def teach_via_valleys(self, sub, audio_samples: np.ndarray,
                             transcript: str,
                             vote_counts: dict | None = None) -> dict:
        """Ground signs to words using the substrate's OWN
        word-boundary signal — sonority valleys — as alignment
        anchors. Per ingest:

          1. Run the audio pipeline; collect Utterances + their
             heard_as signs in time order, plus this stream's
             SonorityValley times.
          2. Partition the sign sequence at valley times → N groups.
          3. Align groups to transcript words; if counts match,
             1-to-1; else merge smallest / split largest groups
             monotonically.
          4. Ground every sign in group g to word[g] (denotes
             edge + vote count for downstream majority pick).

        `vote_counts` is a caller-provided dict keyed by
        (sign_nodeid, word_str). Incremented per grounding so
        `transcribe_via_votes` can pick the majority word at test
        time. Pass the same dict across many teach calls to
        accumulate.
        """
        import re
        words = [w for w in re.findall(r"[\w']+",
                                          transcript.lower()) if w]
        if not words:
            return {"signs": 0, "words": 0, "signs_grounded": 0,
                      "groups": 0}
        if vote_counts is None:
            vote_counts = {}

        # 1. Ingest + collect ordered signs with their times.
        signs = self.ingest(sub, audio_samples)
        if not signs:
            return {"signs": 0, "words": len(words),
                      "signs_grounded": 0, "groups": 0}

        # Find this run's stream — the newest AudioStream with
        # an Utterance pointing to it via from_stream. Quickest:
        # walk each sign's heard_as ← Utterance ← from_stream → stream.
        sign_with_time: list[tuple[float, object]] = []
        stream = None
        for s in signs:
            for utt in sub.in_neighbours(s, "heard_as"):
                a = sub.node(utt)["attrs"]
                t = a.get("start_time_s")
                if t is not None:
                    sign_with_time.append((float(t), s))
                if stream is None:
                    for st in sub.neighbours(utt, "from_stream"):
                        if sub.node(st)["type"] == "AudioStream":
                            stream = st
                            break
                break
        sign_with_time.sort(key=lambda x: x[0])
        ordered_signs = [s for _, s in sign_with_time]

        # 2. Valley times on this stream.
        valley_times: list[float] = []
        if stream is not None:
            for v in sub.neighbours(stream, "has_sonority_valley"):
                t = sub.node(v)["attrs"].get("time_s")
                if t is not None:
                    valley_times.append(float(t))
        valley_times.sort()

        # 3. Partition signs at valley times into groups.
        groups: list[list[object]] = []
        current_group: list[object] = []
        v_idx = 0
        for t, s in sign_with_time:
            # Advance valley pointer past any valleys at or before t
            # except the LAST one we crossed → that one opens a new
            # group. We open a new group when t passes a NEW valley.
            while v_idx < len(valley_times) and valley_times[v_idx] <= t:
                v_idx += 1
                if current_group:
                    groups.append(current_group)
                    current_group = []
            current_group.append(s)
        if current_group:
            groups.append(current_group)
        if not groups:
            groups = [[s for _, s in sign_with_time]]

        # 4. Align groups to words. Three cases:
        #    a) len(groups) == len(words): 1-to-1.
        #    b) len(groups) > len(words): merge smallest adjacent
        #       groups until counts match.
        #    c) len(groups) < len(words): split largest groups
        #       (by proportional sub-positioning).
        groups = _reconcile_groups(groups, len(words))

        # 5. Ground every sign in group i to words[i].
        word_to_concept: dict[str, object] = {}
        for w in set(words):
            nid = None
            for c in sub.nodes("Concept"):
                if sub.node(c)["attrs"].get("name") == w:
                    nid = c
                    break
            if nid is None:
                nid = sub.add_node("Concept", {"name": w,
                                                   "origin": "speech_grounding"})
            word_to_concept[w] = nid

        from substrate_rs import speech as _sp
        rust_sub = _rust(sub)
        n_grounded = 0
        for gi, group in enumerate(groups):
            if gi >= len(words):
                break
            word = words[gi]
            concept = word_to_concept[word]
            for sign in group:
                key = (_node_sort_key(sign), word)
                vote_counts[key] = vote_counts.get(key, 0) + 1
                existing = list(sub.neighbours(sign, "denotes"))
                if concept not in existing:
                    _sp.ground_sign(rust_sub, sign, concept)
                    n_grounded += 1
        return {
            "signs": len(ordered_signs),
            "words": len(words),
            "groups": len(groups),
            "signs_grounded": n_grounded,
        }

    def transcribe_via_votes(self, sub, audio_samples: np.ndarray,
                                 vote_counts: dict,
                                 prefer_composed: bool = True) -> str:
        """Walk signs in time order; for each, emit the word that
        accumulated the most votes during teach_via_valleys. Collapse
        consecutive duplicates.

        With prefer_composed=True (default), compositional signs
        (word-sized chunks of base signs) suppress overlapping base
        signs: each Utterance is checked, and if any compositional
        Utterance covers its time range, we emit the compositional
        sign instead. This is the right granularity for word-level
        WER — base signs are sub-word.
        """
        # Re-ingest the audio AND collect Utterance metadata so we
        # can prefer compositional ones.
        stream = self._build_stream(sub)
        raw = np.ascontiguousarray(audio_samples,
                                      dtype=np.float32).tobytes()
        _rust(sub).run_audio_pipeline(
            stream, raw, int(self.params.sample_rate))
        # Let the compositional Rules fire so we get compositional
        # Utterances on this stream where learned chunks recur.
        # Without this, prefer_composed has nothing to prefer.
        sub.tick(50000)

        # Collect (start_t, end_t, sign, is_composed) for every
        # utterance on this stream.
        utts: list[tuple[float, float, object, bool]] = []
        for utt in sub.in_neighbours(stream, "from_stream"):
            if sub.node(utt)["type"] != "Utterance":
                continue
            a = sub.node(utt)["attrs"]
            st = a.get("start_time_s")
            en = a.get("end_time_s")
            if st is None or en is None:
                continue
            for s in sub.neighbours(utt, "heard_as"):
                is_comp = bool(sub.node(s)["attrs"].get("composed",
                                                            False))
                utts.append((float(st), float(en), s, is_comp))

        if prefer_composed:
            # If a base utt is fully contained in a composed utt's
            # range, drop the base one.
            comp_ranges = [(st, en) for st, en, _, c in utts if c]
            def is_covered(st, en):
                for cst, cen in comp_ranges:
                    if cst <= st and cen >= en and (cst, cen) != (st, en):
                        return True
                return False
            utts = [u for u in utts
                      if u[3] or not is_covered(u[0], u[1])]

        utts.sort(key=lambda u: u[0])

        out_words: list[str] = []
        for st, en, sign, is_comp in utts:
            sign_key = _node_sort_key(sign)
            best_word = None
            best_count = 0
            for (sk, w), cnt in vote_counts.items():
                if sk != sign_key:
                    continue
                if cnt > best_count:
                    best_word = w
                    best_count = cnt
            if best_word is None:
                concepts = list(sub.neighbours(sign, "denotes"))
                if concepts:
                    c = sorted(concepts, key=_node_sort_key)[0]
                    best_word = sub.node(c)["attrs"].get("name")
            if best_word and (not out_words or out_words[-1] != best_word):
                out_words.append(best_word)
        return " ".join(out_words)

    def teach_aligned(self, sub, audio_samples: np.ndarray,
                        transcript: str) -> dict:
        """Pair audio with a known word-level transcript. Ingest
        produces a time-ordered list of AcousticSigns; we ground
        each to the word at its proportional position in the
        transcript (signs[i] → words[floor(i * |W| / |S|)]).

        Crude alignment — signs are emergent acoustic units, not
        words, and the mapping is many-to-one. Sufficient as a V1
        for measuring WER on top of the substrate's emergent
        lexicon.
        """
        import re
        words = [w for w in re.findall(r"[\w']+",
                                          transcript.lower()) if w]
        if not words:
            return {"signs": 0, "words": 0, "signs_grounded": 0}
        signs = self.ingest(sub, audio_samples)
        if not signs:
            return {"signs": 0, "words": len(words), "signs_grounded": 0}

        # Find or mint a Concept per distinct word.
        word_to_concept: dict[str, object] = {}
        for w in set(words):
            nid = None
            for c in sub.nodes("Concept"):
                if sub.node(c)["attrs"].get("name") == w:
                    nid = c
                    break
            if nid is None:
                nid = sub.add_node("Concept", {"name": w})
            word_to_concept[w] = nid

        from substrate_rs import speech as _sp
        rust_sub = _rust(sub)
        n_grounded = 0
        for i, sign in enumerate(signs):
            word_idx = min(int(i * len(words) / len(signs)),
                             len(words) - 1)
            word = words[word_idx]
            concept = word_to_concept[word]
            existing = list(sub.neighbours(sign, "denotes"))
            if concept in existing:
                continue
            _sp.ground_sign(rust_sub, sign, concept)
            n_grounded += 1
        return {
            "signs": len(signs),
            "words": len(words),
            "signs_grounded": n_grounded,
        }

    def transcribe_aligned(self, sub, audio_samples: np.ndarray) -> str:
        """Walk signs in time order; emit each sign's first-grounded
        word; collapse consecutive duplicates. Returns the predicted
        text — usable for WER measurement against a known transcript."""
        signs = self.ingest(sub, audio_samples)
        out_words: list[str] = []
        for sign in signs:
            concepts = list(sub.neighbours(sign, "denotes"))
            if not concepts:
                continue
            # Pick the first concept by NodeID — deterministic and
            # rough proxy for "most-canonical grounding". A proper
            # vote-counted choice would need denote-edge attrs;
            # leave that for V2 once we know if WER is in a useful
            # ballpark.
            c = sorted(concepts, key=_node_sort_key)[0]
            word = sub.node(c)["attrs"].get("name")
            if not word:
                continue
            if not out_words or out_words[-1] != word:
                out_words.append(word)
        return " ".join(out_words)

    # --- introspection ---------------------------------------------

    def lexicon(self, sub) -> list:
        """All AcousticSigns in this STTPipeline's lexicon."""
        for n in sub.nodes("AcousticLexicon"):
            if sub.node(n)["attrs"].get("name") == self.params.lexicon_name:
                return list(sub.neighbours(n, "has_entry"))
        return []

    def set_frozen(self, sub, frozen: bool) -> int:
        """Flip the `frozen` attr on every lexical_access op feeding
        this STTPipeline's lexicon. When frozen, the Rust matcher
        always reuses the closest existing sign and never mints —
        the same primitive, the same dispatch, just a different
        decision controlled from graph data. Returns the number of
        ops touched. Pure world-adapter call: one attr, one Rust
        branch."""
        lex_nid = None
        for n in sub.nodes("AcousticLexicon"):
            if sub.node(n)["attrs"].get("name") == self.params.lexicon_name:
                lex_nid = n
                break
        if lex_nid is None:
            return 0
        touched = 0
        for op in sub.nodes("Operation"):
            if sub.node(op)["attrs"].get("kind") != "lexical_access":
                continue
            uses = list(sub.neighbours(op, "uses_lexicon"))
            if lex_nid not in uses:
                continue
            sub.set_attr(op, "frozen", bool(frozen))
            touched += 1
        return touched

    def vocabulary(self, sub) -> dict:
        """Mapping label → AcousticSign NodeID for grounded signs.
        The agent's emergent vocabulary."""
        out: dict = {}
        for sig in self.lexicon(sub):
            concepts = list(sub.neighbours(sig, "denotes"))
            if not concepts:
                continue
            name = sub.node(concepts[0])["attrs"].get("name")
            if name:
                out[name] = sig
        return out


__all__ = ["STTPipeline", "STTParams", "DEFAULT_BANDS"]
