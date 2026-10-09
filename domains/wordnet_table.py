"""wordnet_table -- WordNet senses from the persisted on-disk table.

domain_data/wordnet_senses.sqlite (scripts/gen_wordnet_sense_table.py) is
NLTK's WordNet index verbatim: lemma -> (pos, synset, rank), synset -> (lemma,
pos, depth), hypernym edges, morphology exceptions and substitution rules.
`synsets(word)` reproduces NLTK 3.10's `wn.synsets(word)` exactly (its
`_morphy`: the exception list if the form is listed, else one pass of the
suffix rules, then keep the forms the lemma table holds for that POS, the
original form first). The generator verifies the equality before writing.

sqlite is queried on disk: no corpus load, near-zero resident memory
(measured: NLTK's in-process WordNet is ~200 MB RSS and ~1.4 s cold).
Mechanical lookup only.
"""
from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Optional

_DB = Path(__file__).resolve().parents[1] / "domain_data" / "wordnet_senses.sqlite"
_POS_LIST = ("n", "v", "a", "r")
_LOCAL = threading.local()
_SUBST: Optional[dict] = None


def _reset():
    global _SUBST
    _SUBST = None
    c = getattr(_LOCAL, "con", None)
    if c is not None:
        c.close()
        _LOCAL.con = None


def available() -> bool:
    return _DB.exists()


def _con():
    c = getattr(_LOCAL, "con", None)
    if c is None:
        c = sqlite3.connect("file:%s?mode=ro" % _DB, uri=True, check_same_thread=False)
        _LOCAL.con = c
    return c


def _subst() -> dict:
    global _SUBST
    if _SUBST is None:
        out: dict = {}
        for pos, _ord, old, new in _con().execute("SELECT pos, ord, old, new FROM subst ORDER BY pos, ord"):
            out.setdefault(pos, []).append((old, new))
        _SUBST = out
    return _SUBST


def _has_lemma(form: str, pos: str) -> bool:
    return _con().execute("SELECT 1 FROM lemma WHERE form=? AND pos=? LIMIT 1", (form, pos)).fetchone() is not None


def _morphy(form: str, pos: str) -> list:
    exc = [r[0] for r in _con().execute("SELECT base FROM exc WHERE pos=? AND form=? ORDER BY ord", (pos, form))]
    if exc:
        forms = exc
    else:
        forms = [form[: -len(old)] + new for old, new in _subst().get(pos, []) if form.endswith(old)]
    out, seen = [], set()
    for f in [form] + forms:
        if f not in seen and _has_lemma(f, pos):
            out.append(f)
            seen.add(f)
    return out


def synsets(word: str) -> list:
    """Synset names for `word`, in NLTK's order (duplicates kept, as NLTK does)."""
    word = str(word).lower()
    out = []
    for p in _POS_LIST:
        for f in _morphy(word, p):
            out += [r[0] for r in _con().execute(
                "SELECT s.name FROM lemma l JOIN synset s ON s.id = l.sid WHERE l.form=? AND l.pos=? ORDER BY l.rank",
                (f, p))]
    return out


def synset(name: str) -> Optional[dict]:
    r = _con().execute("SELECT name, pos, depth FROM synset WHERE name=?", (name,)).fetchone()
    return None if r is None else {"name": r[0], "pos": r[1], "depth": int(r[2])}


def hypernyms(name: str) -> list:
    return [r[0] for r in _con().execute(
        "SELECT p.name FROM hyper h JOIN synset c ON c.id = h.child JOIN synset p ON p.id = h.parent "
        "WHERE c.name=? ORDER BY p.name", (name,))]


__all__ = ["available", "synsets", "synset", "hypernyms"]
