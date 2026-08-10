"""test_event_grounding_migrated — the graph-native event reader's BYTE-IDENTITY gate.

`reading_collapse._event_predication_graph` is the graph-native replacement for the
Python `_event_predication`: it ingests the clause-graph (Phase 1), precomputes the
role candidates as `EventClause` attrs (mechanical held-faculty reads), resolves the
roles, and emits via `_ground_event` (mode=event). This gate asserts it reproduces —
byte-for-byte — the frozen `event` predications of the whole Aesop+Grimm corpus
(`tests/fixtures/reading_parity/reading.json`, captured from `_event_predication`
BEFORE the migration) plus the tricky inversion / OSV / ditransitive / oblique cases
the behavioural wall guards. This is the oracle the migration is measured against;
once the SELECTION cascade is fully graph-resident and `_event_predication` is
deleted, this stays green as the durable regression.
"""
from __future__ import annotations

import json
import os

import pytest

from substrate.boot_core import boot_core
from domains import dictionary_lexicon as dl
from domains import reading_collapse as rc
from domains import comprehend_text as ct

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE = os.path.join(ROOT, "tests", "fixtures", "reading_parity", "reading.json")
# The tricky inversion/OSV/ditransitive/oblique cases the corpus may not exercise,
# FROZEN from `_event_predication` BEFORE its deletion (the shadow-oracle output is
# now a literal fixture, so the gate stands alone once the Python reducer is gone).
TRICKY = os.path.join(ROOT, "tests", "fixtures", "reading_parity", "event_tricky.json")


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


@pytest.fixture(scope="module")
def agent():
    dl.warm_wordnet("en")
    s, node = boot_core()
    ag = _Agent(s, node)
    rc.ensure_codebook(ag)
    return ag


def _graph_event(agent, sentence, intransitive_ok):
    sub, _, _ = rc._resolve(agent)
    lex = rc._marker_lexicon(sub)
    words = [w for w in ct._recognise_words(agent, sentence) if str(w).strip()]
    preds, inverted = rc._event_predication_graph(
        agent, list(words), lex, intransitive_ok=intransitive_ok, return_meta=True)
    return preds, inverted


def test_graph_reader_matches_frozen_corpus_event(agent):
    """The graph-native reader reproduces every frozen corpus `event` predication."""
    with open(FIXTURE) as f:
        corpus = json.load(f)["corpus"].get("CORPUS") or []
    if not corpus:
        pytest.skip("Aesop+Grimm corpus not cached — event oracle unavailable")
    for rec in corpus:
        ev = rec.get("event") or {}
        if "predications" not in ev:
            continue
        preds, inverted = _graph_event(agent, rec["sentence"], intransitive_ok=True)
        assert preds == ev["predications"], rec["sentence"]
        assert inverted == ev["inverted"], rec["sentence"]


with open(TRICKY) as _f:
    _TRICKY_CASES = json.load(_f)


@pytest.mark.parametrize("rec", _TRICKY_CASES, ids=[r["sentence"] for r in _TRICKY_CASES])
@pytest.mark.parametrize("io", [True, False])
def test_graph_reader_matches_tricky_cases(agent, rec, io):
    """Inversion / OSV / ditransitive / oblique cases the corpus may not exercise —
    byte-identical to the FROZEN `_event_predication` output (captured before its
    deletion) under both intransitive_ok modes."""
    sub, _, _ = rc._resolve(agent)
    lex = rc._marker_lexicon(sub)
    words = [w for w in ct._recognise_words(agent, rec["sentence"]) if str(w).strip()]
    want = rec["io_%s" % io]
    preds, inverted = rc._event_predication_graph(
        agent, list(words), lex, intransitive_ok=io, return_meta=True)
    assert preds == want["preds"], rec["sentence"]
    assert inverted == want["inverted"], rec["sentence"]
