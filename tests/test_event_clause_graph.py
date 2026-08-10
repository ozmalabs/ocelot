"""test_event_clause_graph — PHASE 1 of the graph-native event-grounding migration.

The clause-graph ingest (`reading_collapse._event_clause_graph`) is adapter I/O:
PURE TRANSLATION of a recognised event clause into an `EventClause` hub + one
`Token` node per word carrying HELD-FACULTY attrs + `has_token`/`next` edges. These
gates assert (a) the graph is structurally complete (membership + adjacency), and
(b) EVERY token attr equals the DIRECT held-faculty read — the no-Python-decision
audit: the ingest may only branch on a token's own lexical/POS read, never on graph
state, so each attr is reproducible from the faculty alone.
"""
from __future__ import annotations

import os

import pytest

from substrate.boot_core import boot_core
from domains import dictionary_lexicon as dl
from domains import reading_collapse as rc
from domains import comprehend_text as ct
from domains import instruction_reading as ir
from domains import preposition_roles as pr


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


def _tokens(sub, clause):
    toks = []
    for n in sub.nodes("Token"):
        a = sub.node(n)["attrs"]
        if sub.has_edge(clause, "has_token", n):
            toks.append((a["idx"], n, a))
    return [(n, a) for _idx, n, a in sorted(toks, key=lambda t: t[0])]


def test_membership_and_adjacency_complete(agent):
    sub, _, _ = rc._resolve(agent)
    words = ct._recognise_words(agent, "the crow dropped the pebbles into the pitcher")
    clause = rc._event_clause_graph(agent, list(words), rc._marker_lexicon(sub))
    toks = _tokens(sub, clause)
    assert [a["low"] for _n, a in toks] == [
        "the", "crow", "dropped", "the", "pebbles", "into", "the", "pitcher"]
    ids = [n for n, _a in toks]
    # every token is a member of its clause, and the `next` chain is unbroken.
    assert all(sub.has_edge(clause, "has_token", n) for n in ids)
    assert all(sub.has_edge(ids[i], "next", ids[i + 1]) for i in range(len(ids) - 1))
    cl = sub.node(clause)["attrs"]
    assert cl["main_verb"] == "dropped" and cl["main_verb_index"] == 2.0
    assert cl["has_verb"] == 1.0 and cl["n_tokens"] == 8.0


def test_verbless_clause_is_skipped(agent):
    sub, _, _ = rc._resolve(agent)
    # no recognised words -> nothing to ground (mirrors _event_predication's None).
    assert rc._event_clause_graph(agent, [], rc._marker_lexicon(sub)) is None


def test_prep_role_and_animacy_are_faculty_reads(agent):
    sub, _, _ = rc._resolve(agent)
    words = ct._recognise_words(agent, "the crow dropped the pebbles into the pitcher")
    clause = rc._event_clause_graph(agent, list(words), rc._marker_lexicon(sub))
    by_low = {a["low"]: a for _n, a in _tokens(sub, clause)}
    # 'into' is a preposition carrying its held VerbNet thematic role.
    assert by_low["into"]["is_prep"] == 1.0
    assert by_low["into"].get("prep_role") == pr.preposition_role("into", "en")
    # animacy is the whole-creature WordNet read: 'crow' yes, 'pitcher' no.
    assert by_low["crow"]["is_animate"] == 1.0
    assert by_low["pitcher"]["is_animate"] == 0.0


@pytest.mark.parametrize("sentence", [
    "the crow dropped the pebbles into the pitcher",
    "So rested he by the Tumtum tree",
    "the dog thanked her and gave her a whistle",
    "Into the room walked a tall man",
])
def test_every_attr_is_the_direct_faculty_read(agent, sentence):
    """No-Python-decision audit: each Token attr == the held-faculty read for that
    token surface alone. The ingest carries NO graph-state conditional — so the
    graph is exactly reconstructible from the faculties per token."""
    sub, _, _ = rc._resolve(agent)
    words = ct._recognise_words(agent, sentence)
    clause = rc._event_clause_graph(agent, list(words), rc._marker_lexicon(sub))
    for _n, a in _tokens(sub, clause):
        wl = a["low"]
        pos = rc._primary_pos(wl)
        assert a["pos"] == pos
        assert a["is_verb"] == (1.0 if ir.is_verb_headed(wl) else 0.0)
        assert a["inflected_verb"] == (1.0 if rc._inflected_verb(wl) else 0.0)
        assert a["verb_primary"] == (1.0 if pos == "verb" else 0.0)
        assert a["is_aux"] == (1.0 if wl in rc._AUX else 0.0)
        assert a["is_prep"] == (1.0 if wl in rc._PP_PREPS else 0.0)
        assert a["is_det"] == (1.0 if wl in rc._DETERMINERS else 0.0)
        assert a["is_pronoun"] == (1.0 if wl in rc._PRONOUN_FORMS else 0.0)
        assert a["is_adj"] == (1.0 if pos == "adj" else 0.0)
        assert a["is_animate"] == (1.0 if rc._animate_nominal(wl) else 0.0)
        assert a["heads_np"] == (1.0 if rc._heads_np(wl) else 0.0)
        assert a["is_np_tok"] == (1.0 if rc._is_np_tok(wl) else 0.0)
        assert a.get("case") == rc._pron_case(wl)
