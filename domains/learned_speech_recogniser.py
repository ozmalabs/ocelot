"""learned_speech_recogniser — graph-native word recognition via a learned encoder.

A world-adapter capability (the shape of comprehend_speech_clip.SpeechComprehender):
the recognition DECISION is the held Dot Term + an argmax loop (mirrors _ground's
argmin); the learned word-CENTROID templates and the linear ENCODER are GRAPH DATA
(WordCentroid / SpeechEncoder nodes, booted from var/speech_word_templates.json);
the feature transform (peel + velocity + fixed length, then the linear projection) is
mechanical adapter I/O. No fitted model lives in the decision: the encoder is
graph-resident parameters, the match is a substrate Term.

CLAUDE.md: this is admissible adapter/capability work — it sequences the agent's own
machinery (the Dot Term on the Rust substrate) over graph-resident learned data, the
same way SpeechComprehender sequences the DtwTo Term over exemplar nodes. The encoder
is FIT offline by a tool (scripts/jabberwock_wire_learned_recogniser.py), like a
k-means codebook or the forced-aligned phonebank — it emits the seed; the agent uses it.
"""
from __future__ import annotations
import json
import math
import os
import numpy as np

_L = 20            # fixed length (rate peel) — must match the fit
_NB = 32
_SEED = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "var", "speech_word_templates.json")


def install_templates(substrate, seed_path=_SEED):
    """Mechanical ingest (world-adapter I/O): add the seed's WordCentroid +
    SpeechEncoder nodes into the substrate so the recogniser reads them as graph
    data. Skips if WordCentroid nodes are already present. Returns the count added."""
    if list(substrate.nodes("WordCentroid")):
        return 0
    with open(seed_path) as f:
        d = json.load(f)
    n = 0
    for node in d.get("nodes", []):
        substrate.add_node(node["type"], node["attrs"]); n += 1
    return n


def _resample(fr, length=_L):
    fr = np.asarray(fr, dtype=np.float64)
    n = len(fr)
    if n == length:
        return fr
    idx = np.linspace(0, n - 1, length)
    lo = np.floor(idx).astype(int); hi = np.clip(lo + 1, 0, n - 1); t = (idx - lo)[:, None]
    return fr[lo] * (1 - t) + fr[hi] * t


def feature(frames, env):
    """Mechanical feature transform: peel the speaker-shape `env` (a band-envelope),
    rate-peel to fixed length, append the velocity (residual) channel, flatten, L2.

    This shape feature is SCALE-BLIND (rate-peel resamples every span to a fixed length),
    so duration is carried SEPARATELY: the duration-aware match is duration_match_term,
    which scores shape similarity against the unit's duration model."""
    x = _resample(np.asarray(frames, float) - np.asarray(env, float)[None, :])
    d = np.vstack([np.zeros((1, x.shape[1])), np.diff(x, axis=0)])
    v = np.concatenate([x, d], axis=1).reshape(-1)
    return v / max(np.linalg.norm(v), 1e-9)


def duration_match_term(emb, vec, mu, sig, qdur):
    """The agent's DURATION-AWARE match score as a graph Term, composed from its OWN
    normalisation science (the same move CMVN/speaker_norm make: a characteristic is a
    constant to SUBTRACT, the spread a scale to DIVIDE by — domains/cmvn.py) applied to
    the duration dimension:

        match = Dot(emb, vec) - 0.5 * ((qdur - mu) / sig)^2

    i.e. shape similarity MINUS the squared duration z-score (a Gaussian duration
    log-likelihood; the -0.5 z^2 is the Gaussian constant, not a tuned knob). Worked in
    the LOG-duration domain (qdur = log frames; mu, sig = the unit's log-duration mean/std
    from its instances) because speech rate is multiplicative — DERIVED FROM data, not a
    hand-picked band. Built from the agent's held primitives (Dot/Minus/Div/Times/Lit);
    evaluated natively. When sig<=0 (unknown spread) the duration term drops to a plain Dot."""
    dot = {"type": "Dot", "a": {"type": "Lit", "value": list(map(float, emb))},
           "b": {"type": "Lit", "value": list(map(float, vec))}}
    if sig is None or sig <= 0.0:
        return dot
    z = {"type": "Div",
         "a": {"type": "Minus", "a": {"type": "Lit", "value": float(qdur)},
               "b": {"type": "Lit", "value": float(mu)}},
         "b": {"type": "Lit", "value": float(sig)}}
    pen = {"type": "Times", "items": [{"type": "Lit", "value": 0.5},
                                      {"type": "Times", "items": [z, z]}]}
    return {"type": "Minus", "a": dot, "b": pen}


class LearnedSpeechRecogniser:
    """Recognise a word from its frames via the graph-resident learned encoder +
    word-centroid templates. Decision = held Dot Term; templates/encoder = graph data."""

    def __init__(self, substrate):
        self.s = substrate
        self._inner = getattr(substrate, "_inner", None) or getattr(substrate, "inner", substrate)
        self._cent = []
        dmu, dsig = [], []
        for n in substrate.nodes("WordCentroid"):
            a = substrate.node(n)["attrs"]
            self._cent.append((a["word"], [float(x) for x in a["vec"]]))
            # per-unit duration statistics (frames) — the agent's duration model
            # parameters, DERIVED FROM the unit's instances (data, not a hand-set band).
            dmu.append(float(a.get("dur_mu", a.get("dur", 0.0))))
            dsig.append(float(a.get("dur_sig", 0.0)))     # 0 => unknown spread, no duration term
        self._words = [w for w, _ in self._cent]
        self._cmat = (np.asarray([c for _w, c in self._cent], dtype=np.float32)
                      if self._cent else np.zeros((0, 0), dtype=np.float32))
        self._dmu = np.asarray(dmu, dtype=np.float32)
        self._dsig = np.asarray(dsig, dtype=np.float32)
        self._has_dur = bool(self._dsig.size) and float(self._dsig.max()) > 0.0
        # Cache the flattened lists ONCE — the native call copies them, but recomputing
        # numpy->list (800k floats) per query was the hot-path cost.
        self._cmat_flat = self._cmat.reshape(-1).tolist()
        self._dmu_list = self._dmu.tolist()
        self._dsig_list = self._dsig.tolist()
        self._ncent = int(self._cmat.shape[0]) if self._cmat.size else 0
        self._dim = int(self._cmat.shape[1]) if self._cmat.ndim == 2 and self._cmat.size else 0
        self.mu = self.pca = self.lda = None
        for n in substrate.nodes("SpeechEncoder"):
            a = substrate.node(n)["attrs"]
            self.mu = np.asarray(a["mu"], float)
            self.pca = np.asarray(a["pca"], float)
            self.lda = np.asarray(a["lda"], float)
            break

    def encode(self, feat):
        """Adapter feature transform: project the feature through the graph-resident
        linear encoder (PCA -> LDA) and L2-normalise. Mechanical matmul."""
        z = (np.asarray(feat, float) - self.mu) @ self.pca @ self.lda
        return z / max(np.linalg.norm(z), 1e-9)

    def ground_topk(self, embedding, k=5, qdur=None):
        """The DECISION as top-k under the agent's DURATION-AWARE match Term. When qdur
        (the query span's frame count) is given and the templates carry duration stats,
        the score is the agent's composed model (in the LOG-duration domain, because
        speech rate is multiplicative — normal ±25% rate variation is a small z, a 2x
        scale mismatch is a large z; self-calibrating, no fusion knob):

            match(c) = Dot(emb, cent_c) - 0.5*((log qdur - dur_mu_c)/dur_sig_c)^2

        — shape similarity minus the squared log-duration z-score (the agent's
        normalisation science applied to duration; see duration_match_term). dur_mu_c,
        dur_sig_c are the unit's log-duration mean/std (data). Fast path = the native
        topk_match primitive (the compiled form of that Term); the per-centroid held-Term
        loop below is the DEFINITION + fallback. Returns [(word, score)]."""
        if not self._cent:
            return []
        e = np.asarray(embedding, dtype=np.float32)
        dur = qdur is not None and self._has_dur
        qd = math.log(max(float(qdur), 1.0)) if dur else 0.0     # log-duration domain
        try:
            from substrate_rs import _native
            el = e.reshape(-1).tolist()
            if dur:
                idx, sc = _native.topk_match(
                    el, self._cmat_flat, self._dmu_list, self._dsig_list,
                    self._ncent, self._dim, int(k), float(qd))
            else:
                idx, sc = _native.topk_dot(el, self._cmat_flat, self._ncent, self._dim, int(k))
            return [(self._words[i], float(s)) for i, s in zip(idx, sc)]
        except Exception:
            pass
        # Fallback DEFINITION: evaluate the agent's composed match Term per centroid.
        ef = [float(x) for x in embedding]
        scored = []
        for i, (w, c) in enumerate(self._cent):
            mu, sig = float(self._dmu[i]), float(self._dsig[i])
            term = duration_match_term(ef, c, mu, sig, qd) if dur else \
                {"type": "Dot", "a": {"type": "Lit", "value": ef},
                 "b": {"type": "Lit", "value": c}}
            scored.append((w, float(self._inner.evaluate(term, {}))))
        scored.sort(key=lambda x: -x[1])
        return scored[:k]

    def ground(self, embedding) -> str | None:
        """The DECISION, mirroring _ground: argmax over WordCentroid graph nodes of
        the held Dot Term (run by the Rust substrate)."""
        top = self.ground_topk(embedding, k=1)
        return top[0][0] if top else None

    def recognise(self, frames, env=None, qdur=None) -> str | None:
        """frames -> (peel env) -> feature -> encode -> ground. env defaults to the
        per-utterance band-mean. The duration term is OFF by default here: isolated
        single-word recognition has no scale ambiguity (all candidates are words), so
        duration only adds noise. Pass qdur (or use the span-lattice, which passes the
        span's frame count) to switch on the duration-aware match where unit SCALE is a
        free variable (1-word vs multi-word spans)."""
        frames = np.asarray(frames, float)
        if env is None:
            env = frames.mean(0)
        top = self.ground_topk(self.encode(feature(frames, env)), k=1, qdur=qdur)
        return top[0][0] if top else None

    def recognise_feature(self, feat) -> str | None:
        """Ground a precomputed (peel+velocity) feature vector — the encoder's input."""
        return self.ground(self.encode(feat))
