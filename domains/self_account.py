"""Self-account evidence (2026-10-10): a question about the agent's OWN
preferences or pastimes ("What do you do for fun?", "What kind of music do you
like?", "What are some of your favorite movies?") is not a request for a
definition of fun, music or movies.

Mechanical language evidence only, written onto the inbound Message by the
adapter; the graph rule seeds/self_account_reply.json decides the reply and
seeds/conversation_topic_route.json declines the topic lookup for it.

The dictionary is USED here, not recited: WordNet's hypernym chain says what
kind of thing the topic is -- a pastime (fun, hobbies, sports), something one
listens to (music, songs), watches (movies, television), reads (books), plays
(games), tastes (food), keeps (pets), or does (travel, cooking) -- which is
what decides an honest answer from an agent that does none of these. The
preference vocabulary is the lemma set of WordNet's liking synsets, and the
topic phrase is cleaned with the vocabulary base's function words.
OZMA_SELF_ACCOUNT=0 disables the evidence (measurement arms only).
"""
from __future__ import annotations

import os
import re
from functools import lru_cache
from typing import Optional

# hypernym anchor -> mode, in priority order (a media/experience reading wins
# over the generic pastime reading of the same phrase: "TV shows" -> watch)
_ANCHORS = (
    ("auditory_communication.n.01", "listen"),
    ("show.n.03", "watch"),
    ("broadcasting.n.02", "watch"),
    ("publication.n.01", "read"),
    ("written_communication.n.01", "read"),
    ("game.n.01", "play"),
    ("food.n.01", "taste"),
    ("food.n.02", "taste"),
    ("animal.n.01", "keep"),
    ("diversion.n.01", "pastime"),
    ("act.n.02", "do"),
)
_GENERIC = {"listen": "music", "watch": "films", "read": "books", "play": "games", "taste": "food"}
_LIKING_SYNSETS = ("like.v.01", "like.v.02", "love.v.01", "enjoy.v.01", "prefer.v.01", "fancy.v.02",
                   "favorite.s.01")
_SECOND_PERSON = frozenset({"you", "your", "yours", "yourself", "u"})
_WORD = re.compile(r"[a-z][a-z']*")


@lru_cache(maxsize=1)
def _wn():
    try:
        from nltk.corpus import wordnet as wn
        wn.synsets("dog")
        return wn
    except Exception:  # noqa: BLE001 -- no WordNet: no evidence
        return None


@lru_cache(maxsize=1)
def liking_lemmas() -> frozenset:
    wn = _wn()
    out = set()
    if wn is not None:
        for name in _LIKING_SYNSETS:
            try:
                out.update(l.lower().replace("_", " ") for l in wn.synset(name).lemma_names())
            except Exception:  # noqa: BLE001
                continue
    if "favorite" in out:
        out.add("favourite")                  # the British spelling WordNet lists under the same sense
    return frozenset(out)


@lru_cache(maxsize=2048)
def mode_of(noun: str) -> Optional[str]:
    """What kind of thing `noun` is, read off its first WordNet noun sense's
    hypernym closure (None when WordNet has no anchor for it)."""
    wn = _wn()
    if wn is None or not noun:
        return None
    base = wn.morphy(noun, wn.NOUN) or noun
    senses = wn.synsets(base, wn.NOUN)
    if not senses:
        return None
    s = senses[0]
    names = {s.name()} | {h.name() for h in s.closure(lambda x: x.hypernyms() + x.instance_hypernyms())}
    for anchor, mode in _ANCHORS:
        if anchor in names:
            return mode
    return None


def _clean_topic(words, substrate=None) -> list:
    from domains import vocabulary_base as vb
    skip = liking_lemmas() | {"kind", "kinds", "type", "types", "sort", "sorts", "thing", "things"}
    return [w for w in words if w not in skip and not vb.is_function_word(vb.lookup(w, substrate))]


def evidence(text: str, topic: Optional[str] = None, substrate=None) -> Optional[dict]:
    """{self_account_mode, self_account_topic} for a question about the agent's
    own preferences or pastimes, else None."""
    if os.environ.get("OZMA_SELF_ACCOUNT") == "0":
        return None
    low = str(text or "").lower().replace("\u2019", "'")
    # only the question itself: "That would be fun! What's your favorite
    # store?" asks about a store, not about fun
    questions = [q for q in re.split(r"(?<=[.!?])\s+", low.strip()) if q.endswith("?")]
    low = questions[-1] if questions else low
    words = _WORD.findall(low)
    if not words or not (set(words) & _SECOND_PERSON) or not low.strip().endswith("?"):
        return None
    liking = liking_lemmas()
    cue = bool(set(words) & liking) or "for fun" in low
    from domains import vocabulary_base as vb
    # candidates: the question's nouns first ("What kind of relaxing games do
    # you like to play?" -> games), else the words after the liking cue ("Do
    # you like to travel?" -> travel), else the asked topic phrase
    content = _clean_topic(words, substrate)
    if "for fun" in low and "fun" not in content:
        content = content + ["fun"]
    nouns = [w for w in content if (e := vb.lookup(w, substrate)) and e.get("pos") == "noun"]
    pool = nouns
    if not pool:
        idx = max((i for i, w in enumerate(words) if w in liking), default=None)
        pool = _clean_topic(words[idx + 1:], substrate) if idx is not None else []
    if not pool and topic:
        pool = _clean_topic(_WORD.findall(str(topic).lower()), substrate)
    modes = [(w, mode_of(w)) for w in pool]
    modes = [(w, m) for w, m in modes if m]
    if not modes:
        return None
    rank = {m: i for i, (_a, m) in enumerate(_ANCHORS)}
    word, mode = min(modes, key=lambda wm: rank[wm[1]])
    # a pastime question needs no liking verb ("What are your hobbies?"); any
    # other mode does ("What do you do for work?" is not about a preference)
    if not cue and mode != "pastime":
        return None
    # the noun phrase as asked around the chosen word: its contiguous content
    # words, joined across "and" ("movies and tv shows"), never a whole clause
    at = words.index(word) if word in words else None
    phrase = word
    if at is not None:
        keep = set(content) | {"and"}
        lo = at
        while lo > 0 and words[lo - 1] in keep:
            lo -= 1
        hi = at
        while hi + 1 < len(words) and words[hi + 1] in keep:
            hi += 1
        span = [w for w in words[lo:hi + 1]]
        while span and span[0] == "and":
            span = span[1:]
        while span and span[-1] == "and":
            span = span[:-1]
        phrase = " ".join(span) or word
    # "What do you like to read?": the topic is the experience verb itself;
    # name the kind of thing instead ("books")
    e = vb.lookup(phrase, substrate)
    if mode in _GENERIC and e and e.get("pos") == "verb":
        phrase = _GENERIC[mode]
    # a single count noun is spoken of in the plural ("favorite book" -> books)
    if (mode in ("listen", "watch", "read", "play") and " " not in phrase and not phrase.endswith("s")
            and vb.lookup(phrase + "s", substrate)):
        phrase = phrase + "s"
    return {"self_account_mode": mode, "self_account_topic": phrase}
