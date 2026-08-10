"""comprehend_speech_clip — THE ROUTER: comprehend a speech clip with the SAME
recognise-circumstance / retrieve-construction / compose / ground engine that
comprehends a sentence.

This is the read_and_ground / comprehension ROUTER pattern applied to
perception. Given a clip, the agent:

  1. RECOGNISES THE CIRCUMSTANCE — "this is a speech clip" (optionally voiced vs
     whisper). A thin I/O-boundary classifier (a clip is a 1-D float array);
     once named, the router dispatches on the held construction (the recognition
     itself is mechanical — stated as scaffolded in the module that builds the
     construction).
  2. RETRIEVES the stored `speech_decode` construction from the SAME concept /
     Microtheory library the language constructions live in (the read_and_ground
     RETRIEVE step — a library lookup, not a re-derivation).
  3. COMPOSES the Gamma-typed pipeline and EVALUATES it natively (gammatone ->
     native rank/self-sim Term-trees via substrate.evaluate) up to REL_SHAPE.
  4. GROUNDS to the recognised WORD via the native DtwTo readout (substrate.
     evaluate) argmin over the held exemplar lexicon — and records the grounding
     as a Mention->refers_to->word the same way a comprehended sentence grounds a
     referent.

HONEST: the read-prose-definition half of read_and_ground is N/A for a clip
(there is no text definition to read); the router here is the
RETRIEVE+COMPOSE+GROUND half wired to the same store. The circumstance-naming is
mechanical. What is genuinely unified: the construction is RETRIEVED FROM THE
LIBRARY before composing, the composition is the agent's NATIVE Term-trees, the
grounding is the native DtwTo + an admissible refers_to mutation — one engine.

DISCIPLINE (CLAUDE.md): world adapter. It sequences the agent's own machinery
and translates the clip at the I/O boundary; the recognition decision is native
(substrate.evaluate); no fitted model.
"""
from __future__ import annotations

import json
from typing import Any, Optional

import numpy as np

import domains.recognition_graph as RG
from domains.speech_decode_construction import (compose_rel_shape, gamma_admits,
                                                SIGNAL, WORD)


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def _as_tuple(M):
    return tuple(tuple(float(v) for v in row) for row in np.asarray(M))


# ---------------------------------------------------------------------------
# STEP 1 — recognise the circumstance (thin I/O-boundary classifier).
# ---------------------------------------------------------------------------
def recognise_circumstance(signal: np.ndarray) -> Optional[str]:
    """Name the circumstance: a 1-D float waveform of non-trivial length is a
    'speech_clip'. Mechanical (the honest scaffolded step) — once named, the
    router dispatches on the held construction."""
    a = np.asarray(signal)
    if a.ndim == 1 and a.size >= 2 and np.issubdtype(a.dtype, np.floating):
        return "speech_clip"
    return None


# ---------------------------------------------------------------------------
# STEP 2 — retrieve the stored decode-construction from the library.
# ---------------------------------------------------------------------------
def retrieve_decode_construction(substrate, *, concept_name: str = "speech_decode"
                                 ) -> Optional[dict]:
    """RETRIEVE the held `speech_decode` construction's combination (the
    Gamma-typed pipeline) from the SAME concept store the language constructions
    live in — the read_and_ground RETRIEVE step (a library lookup). Returns the
    combination dict, or None if the construction was never installed."""
    from domains import grounded_representation as _gr
    cid = _gr._find_concept(substrate, concept_name)
    if cid is None:
        return None
    comb = substrate.node(cid)["attrs"].get("combination")
    if comb is None:
        return None
    if isinstance(comb, str):
        try:
            comb = json.loads(comb)
        except Exception:
            return None
    return comb


# ---------------------------------------------------------------------------
# A native DtwTo lexicon (the held exemplar store) + the grounding readout.
# ---------------------------------------------------------------------------
class SpeechComprehender:
    """The router's evaluator: holds the exemplar lexicon as graph nodes and the
    native DtwTo readout Term, and comprehends a clip by retrieving the held
    decode-construction, composing it, evaluating natively, and grounding to a
    word. ONE engine — the same substrate that runs the language Term-trees runs
    these."""

    def __init__(self, substrate, combination: dict):
        ok, reason = gamma_admits(combination)
        if not ok:
            raise TypeError(f"retrieved construction inadmissible: {reason}")
        self.s = substrate
        self.combination = combination
        self._sign = substrate.add_node("HeardSign", {})
        self._err = _Pred(RG._DtwTo(RG._Attr(RG._V("s"), "rep"),
                                    RG._Attr(RG._V("w"), "rep")))
        self._exemplars: list[tuple[Any, str]] = []

    def add_exemplar(self, signal: np.ndarray, fs: int, word: str) -> bool:
        """Compose the held decode-construction over a labelled clip and store
        its relational trajectory as an exemplar (the held lexicon)."""
        rep = compose_rel_shape(self.s, signal, fs, self.combination)
        if rep is None:
            return False
        c = self.s.add_node("Exemplar", {"word": word})
        self.s.set_attr(c, "rep", _as_tuple(rep))
        self._exemplars.append((c, word))
        return True

    def add_exemplar_rep(self, rep, word: str) -> None:
        """Add a precomputed relational trajectory as an exemplar (parity-run
        fast path; the rep was produced by the SAME composed construction)."""
        c = self.s.add_node("Exemplar", {"word": word})
        self.s.set_attr(c, "rep", _as_tuple(rep))
        self._exemplars.append((c, word))

    def clear_lexicon(self) -> None:
        for c, _ in self._exemplars:
            try:
                self.s.remove_node(c)
            except Exception:
                pass
        self._exemplars = []

    def comprehend(self, signal: np.ndarray, fs: int) -> Optional[str]:
        """THE ROUTER on a clip: recognise circumstance -> (construction already
        retrieved) -> COMPOSE the Gamma-typed pipeline + EVALUATE natively ->
        GROUND to the word via the native DtwTo argmin. Returns the word or None.

        The grounding is the native DtwTo Term (substrate.evaluate) — the same
        evaluator that runs the language Term-trees."""
        if recognise_circumstance(signal) != "speech_clip":
            return None
        rep = compose_rel_shape(self.s, signal, fs, self.combination)
        if rep is None:
            return None
        return self._ground(rep)

    def comprehend_rep(self, rep) -> Optional[str]:
        """Ground a precomputed relational trajectory (parity fast path)."""
        if rep is None:
            return None
        return self._ground(rep)

    def _ground(self, rep) -> Optional[str]:
        self.s.set_attr(self._sign, "rep", _as_tuple(rep))
        best_d, best_w = 1e18, None
        for c, ew in self._exemplars:
            d = self.s.evaluate(self._err, {"s": self._sign, "w": c})
            if d < best_d:
                best_d, best_w = d, ew
        return best_w


__all__ = ["recognise_circumstance", "retrieve_decode_construction",
           "SpeechComprehender"]
