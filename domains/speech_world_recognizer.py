"""speech_world_recognizer — the cognition+hat in FEATURE SPACE for the live
self-directed speech world.

This is NOT new recognition science: it is the iter-33 / iter-46 / iter-49
combine-all PRODUCT recogniser (domains/many_settings_recognizer), narrowed to a
compact set of the agent's OWNED orthogonal feature channels so it runs in real
time inside a live learning loop. Every design choice is the established one:

  · FEATURE SPACE only. We perceive a heard waveform by reading it through the
    agent's own front-end cues (cochleagram flat readout, the freq-sharp FFT ear,
    the sharp all-pole spectral envelope). We NEVER invert a TTS, NEVER round-trip
    audio, NEVER ask a neural net for the answer (iter-40 forbids the round trip;
    the TTS is the WORLD, not the recogniser).

  · COMBINE-ALL PRODUCT. Each channel contributes a softmax-by-its-own-median
    likelihood P_c(w|s) (many_settings_recognizer.channel_likelihood); the decision
    is the graph Argmax over candidate words of the variadic Times product
    (many_settings_recognizer.predict_many_settings_term), evaluated natively by
    substrate.evaluate. No fit, no learned global weight, no select-best.

  · EXEMPLAR LEXICON IN THE GRAPH. The agent's knowledge is a bank of WordExemplar
    nodes (one per heard-and-cookied utterance), each carrying its per-channel
    feature vectors as graph attrs and a denotes-edge to the word Concept. The
    recogniser's 1-NN evidence is computed against this graph-resident bank — the
    lexicon the agent GROWS as it learns. Banking is the LEARN step of the loop.

The MEANING-bearing decision (which word) is the graph Argmax Term. Python here is
the adapter: it extracts the per-channel feature vectors at the I/O boundary, reads
the exemplar bank out of the graph, populates the per-candidate likelihood attrs,
and asks the substrate to evaluate the Argmax. No Python conditional decides the
word.
"""
from __future__ import annotations

import numpy as np

from domains.filter_settings import cochleagram, fft_ear
from domains.allpole_spectral_envelope import allpole_ear
import domains.many_settings_recognizer as MS


# The agent's owned orthogonal feature channels (a compact subset of the iter-34
# enriched graph — the three that are both cheap AND orthogonal by construction):
#   ch0 cochleagram flat   : the gammatone band-energy readout (the base spectral view)
#   ch1 fft_ear            : the freq-sharp long-window FFT ear (complementary T-F point)
#   ch2 allpole_envelope   : the sharp Levinson all-pole spectral envelope (formants)
CHANNEL_NAMES = ["cochleagram_flat", "fft_ear", "allpole_envelope"]
N_CHANNELS = len(CHANNEL_NAMES)


def _l2(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, dtype=np.float64).ravel()
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v


def feature_channels(x: np.ndarray, fs: int) -> list:
    """The per-channel feature VECTORS for one utterance — the agent reading the
    waveform through its own front-end. Returns [v_ch0, v_ch1, v_ch2], each an
    L2-normalised numpy vector. Pure I/O-boundary signal extraction, no decision."""
    x = np.asarray(x, dtype=np.float64)
    if x.size < 16:
        return [_l2(np.zeros(8)) for _ in range(N_CHANNELS)]
    M = cochleagram(x, fs)
    return [
        _l2(M.flatten()),
        _l2(fft_ear(x, fs)),
        _l2(allpole_ear(x, fs)),
    ]


# Per-channel exemplar-vector attr keys on a WordExemplar node.
def _exemplar_attr(ci: int) -> str:
    return f"feat_ch{ci}"


class GraphLexicon:
    """The agent's exemplar lexicon, resident as WordExemplar graph nodes.

    Each exemplar node:
      type    = "WordExemplar"
      attrs   = {feat_ch0:[...], feat_ch1:[...], feat_ch2:[...],
                 word:<str>, source:<str>, hearings:int}
      edge    = denotes -> Concept(word)

    Banking an exemplar IS the learn step. The bank is read at recognition time to
    form each channel's 1-NN exemplar evidence. All graph-resident — it serialises
    with graph_to_dict and resumes with graph_from_dict (the agent saving itself)."""

    def __init__(self, substrate):
        self.s = substrate

    # -- write side (the LEARN step) --

    def bank(self, channels: list, word: str, source: str) -> int:
        """Add one exemplar to the graph: a WordExemplar node carrying the per-channel
        feature vectors + a denotes-edge to the word Concept. Returns the node id."""
        attrs = {"word": word, "source": source, "hearings": 1}
        for ci, v in enumerate(channels):
            attrs[_exemplar_attr(ci)] = [float(z) for z in np.asarray(v).ravel()]
        ex = self.s.add_node("WordExemplar", attrs)
        concept = self._concept(word)
        try:
            self.s.add_edge(ex, "denotes", concept)
        except Exception:
            pass
        return ex

    def _concept(self, word: str):
        for c in self.s.nodes("Concept"):
            a = self.s.node(c)["attrs"]
            if a.get("name") == word and a.get(MS.WORD_ATTR) == 1.0:
                return c
        c = self.s.add_node("Concept", {"name": word, "origin": "speech_world"})
        self.s.set_attr(c, MS.WORD_ATTR, 1.0)
        return c

    # -- read side --

    def candidate_words(self) -> list:
        out = []
        for c in self.s.nodes("Concept"):
            a = self.s.node(c)["attrs"]
            if a.get(MS.WORD_ATTR) == 1.0 and a.get("name"):
                out.append(a["name"])
        return sorted(set(out))

    def banked(self) -> list:
        """All exemplar nodes as (word, [v_ch0, v_ch1, v_ch2]) tuples."""
        out = []
        for ex in self.s.nodes("WordExemplar"):
            a = self.s.node(ex)["attrs"]
            w = a.get("word")
            if not w:
                continue
            vecs = []
            ok = True
            for ci in range(N_CHANNELS):
                v = a.get(_exemplar_attr(ci))
                if v is None:
                    ok = False
                    break
                vecs.append(np.asarray(v, dtype=np.float64))
            if ok:
                out.append((w, vecs))
        return out

    def size(self) -> int:
        return sum(1 for _ in self.s.nodes("WordExemplar"))


class WordHat:
    """The combine-all PRODUCT recogniser as a graph Argmax Term over the lexicon.

    Holds a scratch substrate carrying one Concept per candidate word + the
    predict_many_settings_term Argmax-of-product Term. recognise() populates each
    candidate's per-channel likelihood attrs from the lexicon's 1-NN evidence, then
    asks substrate.evaluate to pick the Argmax word. The DECISION is the graph Term."""

    def __init__(self):
        from substrate_rs import Substrate
        self._sub = Substrate()
        self._term = MS._Pred(MS.predict_many_settings_term(N_CHANNELS))
        self._wc: dict = {}
        self._cands_key = None

    def _ensure_candidates(self, candidates):
        key = frozenset(candidates)
        if key != self._cands_key:
            # rebuild concept set so the Argmax ranges over exactly these words.
            for w in candidates:
                if w not in self._wc:
                    c = self._sub.add_node("Concept", {"name": w})
                    self._sub.set_attr(c, MS.WORD_ATTR, 1.0)
                    self._wc[w] = c
            self._cands_key = key

    def recognise(self, channels: list, lexicon: GraphLexicon):
        """Blind guess for one heard utterance. channels = the per-channel feature
        vectors; lexicon = the agent's exemplar bank. Returns the Argmax word (or
        None if the bank is empty). The combine-all product over feature channels,
        decided by the graph Argmax Term — NOT a TTS inversion, NOT a net."""
        banked = lexicon.banked()
        candidates = sorted({w for (w, _) in banked})
        if not candidates:
            return None
        self._ensure_candidates(candidates)
        # per channel: 1-NN exemplar evidence -> softmax-by-own-median likelihood.
        per_word_train = {ci: [] for ci in range(N_CHANNELS)}
        train_words = []
        for (w, vecs) in banked:
            train_words.append(w)
            for ci in range(N_CHANNELS):
                per_word_train[ci].append(vecs[ci])
        for ci in range(N_CHANNELS):
            Xc = np.asarray(per_word_train[ci])
            p = MS.channel_likelihood(np.asarray(channels[ci]), Xc,
                                      train_words, candidates)
            for w in candidates:
                self._sub.set_attr(self._wc[w], MS.channel_attr(ci),
                                   float(p[w]))
        pred = self._sub.evaluate(self._term, {})
        if pred is None:
            return None
        return self._sub.node(pred)["attrs"].get("name")


__all__ = [
    "CHANNEL_NAMES", "N_CHANNELS", "feature_channels",
    "GraphLexicon", "WordHat",
]
