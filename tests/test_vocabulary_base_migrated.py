"""The English vocabulary base (seeds/vocabulary_base_en.json, 2026-10-10).

Pinned claims:
  * derived from the Brown corpus (+ a conversational supplement): contractions
    carry their parts, interjections and function words are closed, "fun" is
    an open noun, "like" is mixed;
  * the POS faculty types a token it could not type otherwise from the base:
    "Wow" is an interjection, "I'm" a function word, "What's" a wh-focus --
    and only such tokens change (OZMA_VOCABULARY_BASE=0 restores the gap);
  * the base is graph data: a taught VocabEntry is consulted;
  * the reply-quality criterion can read its function words from the base
    (`function_words`, a human-adopted criterion edit); absent, nothing changes.
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from domains import construction_grammar as cg     # noqa: E402
from domains import reply_quality as rq            # noqa: E402
from domains import vocabulary_base as vb          # noqa: E402


def _entries():
    d = json.load(open(os.path.join(ROOT, "seeds", "vocabulary_base_en.json")))
    return {n["attrs"]["form"]: n["attrs"] for n in d["nodes"]}


def test_derived_entries():
    e = _entries()
    assert e["i'm"]["pos"] == "contraction" and e["i'm"]["expands"] == ["pronoun", "auxiliary"]
    assert e["don't"]["expands"] == ["auxiliary", "negation"]
    assert e["wow"]["pos"] == "interjection" and e["wow"]["klass"] == "closed"
    assert e["the"]["klass"] == "closed" and e["they"]["pos"] == "pronoun"
    assert e["fun"]["klass"] == "open" and e["fun"]["pos"] == "noun"
    assert e["like"]["klass"] == "mixed"
    assert len(e) > 5000


def _heads(text):
    return [(x["role"], x["pos"]) for x in cg.parse_with_gaps(text)["elements"]]


def test_pos_faculty_types_untyped_tokens_from_the_base(monkeypatch):
    monkeypatch.delenv("OZMA_VOCABULARY_BASE", raising=False)
    assert _heads("Wow, that sounds fun.")[0] == ("function", "interjection")
    assert _heads("I'm sure.")[0] == ("function", "pronoun")          # a subject, not question inversion
    assert _heads("What's it like?")[0] == ("focus", "thing")
    assert cg.parse_with_gaps("What's it like?")["focus"] == "thing"
    on = _heads("I like to play video games.")
    monkeypatch.setenv("OZMA_VOCABULARY_BASE", "0")
    assert _heads("Wow, that sounds fun.")[0] == ("gap", "by-position")
    assert _heads("I like to play video games.") == on, "a token another source typed is unchanged"


def test_a_taught_entry_in_the_graph_is_consulted(monkeypatch):
    monkeypatch.delenv("OZMA_VOCABULARY_BASE", raising=False)
    from substrate.world_adapter import WorldAdapter
    a = WorldAdapter(seeds=())
    assert vb.lookup("zorblat", a) is None                # not in the base
    assert cg._pos_token("zorblat", None, substrate=a) == ("gap", "by-position")
    a.s.add_node("VocabEntry", {"form": "zorblat", "pos": "noun", "klass": "open", "source": "taught"})
    assert vb.lookup("zorblat", a)["source"] == "taught"
    assert cg._pos_token("zorblat", None, substrate=a) == ("content", "noun")


def test_criterion_reads_function_words_from_the_base_only_when_held():
    q, d = "What else do you like to do for fun?", 'Fun is defined by the Oxford English Dictionary as "pleasure".'
    base = rq.criteria()
    assert not base.get("function_words")
    assert rq.assess(q, d)["on_topic"] is False           # the hand stoplist holds "fun"
    c = dict(base, function_words={"source": "vocabulary_base_en", "klass": ["closed", "mixed"], "mode": "replace"})
    assert rq.assess(q, d, None, c)["on_topic"] is True    # "fun" is an open noun in the base
