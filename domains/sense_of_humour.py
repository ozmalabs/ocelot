"""sense_of_humour — a SENSE of humour: SALIENCE for BENIGN INCONGRUITY (creator, 2026-07-04). The
jabberwock can already process a joke's parts (wordplay, comprehension); a SENSE adds recognizing
that a turn is humorous and responding IN KIND (play along / top it), NOT literally.

THE MECHANISM (CLAUDE.md-native — reuse, no bespoke detector):
  * INCONGRUITY = a RESIDUAL / a violated expectation that RESOLVES (the collapse machinery, reused):
      - WORDPLAY incongruity: a playful COINAGE dropped in (the jabberwock's own kin — domains.wordplay
        detects the word-shape surprise), or
      - CROSS-DOMAIN incongruity: a turn that JUXTAPOSES two normally-distant worlds (a technical word
        beside a personal/emotional one). The clash is read via domains.sense_of_reference's manifold
        cue tables (reused) — a script/frame violation, the textbook incongruity of humour.
  * BENIGN = the surprise resolves PLAYFULLY, not threateningly: the turn's affect is not agitated
    (reuse interlocutor_model._affect_of, read-only). A hostile incongruity/insult is NOT play-along.
  * A turn is HUMOROUS iff an incongruity is present AND it is benign. RESPOND IN KIND: a playful
    response COMPOSED FROM THE INCONGRUITY PARTS (recognize it + a light topper), FLAGGED as play —
    never a literal parse of the setup. (Composed from parts, register-shaped — the same admissible
    shape as wordplay.compose_reply; NOT a per-phrase response table.)

This is DISCRIMINATIVE: a plain literal statement is not humorous (no incongruity); a hostile turn
with the same shape is not benign (don't play along with an insult). donkey=0 — no LM, no classifier.
"""
from __future__ import annotations

import re
from typing import Optional

from domains import wordplay as _wp
from domains import sense_of_reference as _sr
from domains.interlocutor_collapse_plug import collapse_residual
import domains.interlocutor_model as _im


_PIVOTS = (" but ", " so ", " until ", " except ", " and then ", " yet ", " — ", ": ")


def _affect(text: str) -> str:
    toks = {w.lower() for w in re.findall(r"[A-Za-z']+", text or "")}
    return _im._affect_of(toks, text or "")


def _content_words(text: str) -> list:
    return [w for w in re.findall(r"[a-z]+", (text or "").lower()) if len(w) >= 4]


def _worlds_present(text: str) -> dict:
    """Which manifold WORLDS the turn's words touch (reusing sense_of_reference's cue tables) ->
    {world: [words]}. A turn touching two distant worlds is a cross-domain juxtaposition."""
    hits: dict = {}
    for w in _content_words(text):
        for t, cues in _sr._TYPE_CUES.items():
            if w in cues:
                hits.setdefault(t, []).append(w)
    return hits


# personal/emotional words — a "world" the cue tables don't cover, but the classic clash partner
# for a technical/formal setup (a closed reference table, keyed on the word, wordplay-style).
_PERSONAL = frozenset("""love heart lonely lonely feelings feeling relationship therapy dating
    marriage divorce breakup crush emotions cuddle hugs romance advice sympathy""".split())


def detect_humour(text: str, interlocutor: Optional[dict] = None) -> dict:
    """Recognize whether a turn is HUMOROUS (a benign incongruity) and, if so, compose an IN-KIND
    response. Returns {humorous, benign, kind, incongruity, setup, punch, response}.

    kind is 'wordplay' (a coinage), 'cross_domain' (a two-world juxtaposition), or None."""
    text = str(text or "")
    benign = _affect(text) != "agitated"
    incong = None
    kind = None
    setup = punch = None

    # 1. WORDPLAY incongruity — a playful coinage (the jabberwock's kin).
    coin = None
    try:
        coin = _wp.find_coinage(text)
    except Exception:
        coin = None
    if coin is not None:
        incong = coin.get("word")
        kind = "wordplay"

    # 2. CROSS-DOMAIN incongruity — a technical/formal world beside a personal one (a script clash),
    #    read as a collapse RESIDUAL: the personal punch-concept is a gap against the setup's world.
    if kind is None:
        worlds = _worlds_present(text)
        personal = [w for w in _content_words(text) if w in _PERSONAL]
        techy = [w for wlist in worlds.values() for w in wlist]
        if worlds and personal:
            # the setup establishes a world; the personal concept is the surprising residual.
            model = {"world": {t: len(ws) for t, ws in worlds.items()}}
            residual = collapse_residual(model, {"world": "personal"})
            if residual:                     # personal world unpredicted by the setup -> incongruity
                incong = (techy[:1] + personal[:1])
                kind = "cross_domain"
                # split on a pivot for setup/punch, else whole-turn.
                low = text.lower()
                for p in _PIVOTS:
                    if p in low:
                        i = low.index(p)
                        setup, punch = text[:i].strip(), text[i + len(p):].strip()
                        break

    humorous = bool(incong) and benign
    out = {"humorous": humorous, "benign": benign, "kind": kind,
           "incongruity": incong, "setup": setup, "punch": punch}
    if humorous:
        out["response"] = compose_in_kind(out)
    else:
        out["response"] = None
    return out


def compose_in_kind(analysis: dict, register: str = "neutral") -> str:
    """Compose a PLAYFUL, in-kind response from the incongruity parts — recognize the play and TOP
    it, never a literal parse. Composed from the analysis parts (register-shaped), not a lookup."""
    kind = analysis.get("kind")
    lead = "Ha —" if register != "formal" else "I am amused —"
    if kind == "wordplay":
        word = analysis.get("incongruity")
        return (f"{lead} '{word}', a fine coinage; I'll play along rather than demand a definition. "
                f"Frabjous nonsense, in the Jabberwock spirit.")
    if kind == "cross_domain":
        comps = analysis.get("incongruity") or []
        a, b = (list(comps) + ["", ""])[:2]
        topper = f"pairing {a} with {b} is a delightful mismatch"
        return f"{lead} I catch the joke: {topper}. I'll play along rather than answer it straight."
    return f"{lead} I catch the incongruity, and I'll play along."


__all__ = ["detect_humour", "compose_in_kind"]
