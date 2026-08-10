"""test_embedded_clause_migrated — Phase 2 of READER_PARSER_MIGRATION.md: a
finite-clause complement of a REPORT/communication verb (say/said/wrote/...) is a
NESTED CLAUSE to decompose, not a flat object NP to mash.

THE BUG. "Public Citizen said Big Oil captured the government." used to read as
ONE flat clause: `_skeleton_from_words` finds exactly one skeleton marker (the
finite verb 'said'), so the whole complement 'Big Oil captured the government'
became a single mashed object-NP entity (`big_oil_captured_government`) instead of
grounding as its own event. The pre-existing COMPLEMENTIZER path
(`_is_complementizer_that`) already splits an embedded clause opened by an
EXPLICIT 'that'/'whether' ("the robbers saw THAT the lights were out") — but a
report verb's complement is very often introduced with NO complementizer at all
("Public Citizen said Big Oil captured..."), and that case fell through untouched.

THE DECISION MOVED GRAPH-NATIVE: "does a finite clause immediately following a
REPORT verb open an embedded clause even with no complementizer present" is now a
HELD DATA fact -- the SET of report/communication verbs the agent recognises
(`ReportClass{cls:'REPORT'}`, seeds/reading_constructions.json) -- read by
`reading_collapse._report_literal_member` / `_is_report_complement_here`, which
`_segment_into_clauses` consults exactly the way it already consults the
COMPLEMENTIZER/CLAUSE_LINK marker classes. Absent that class (an older/ablated
seed), this never fires and every report-verb sentence decomposes exactly as it
did before this phase (see the ablation test below).

HAND-WRITTEN BOOTSTRAPPING DATA (honest): the report-verb vocabulary is a
hand-curated SEED list (say/said/reply/replied/write/wrote/announce/announced/
state/stated/declare/declared/exclaim/exclaimed/remark/remarked/whisper/
whispered/shout/shouted/murmur/murmured/mutter/muttered), exactly like Phase 1's
`yields_to_finite_verb` fact and the pre-existing QUANTIFIER/BUT MarkerClass
precedents -- the decompose-time consultation this module performs is too deep
inside the token-by-token clause segmenter for the agent's own composer/
induce_concern machinery to reach, so agent self-authoring was infeasible here,
matching Phase 1's documented precedent exactly. `report_membership` (the more
general lookup, mirroring situation_model_reader.cos_membership /
character_tom.attitude_membership) DOES support live ADJACENCY join for other
callers, but `_is_report_complement_here` deliberately restricts itself to
LITERAL seed membership only (`_report_literal_member`, read-only, no side
effect): the frozen parity-corpus audit for this phase found common light verbs
('have'/'give'/'know'/'hold') clear this class's own adjacency threshold against
'say'/'tell'/'announce'/'declare' by WordNet lexical accident, and because a
`_join_class` join PERSISTS into the class's `forms` for the rest of the session,
even gating on the adjacency RESULT would not have been enough -- the mutation
already happened as a side effect of computing it. Scoped conservatively:
(a) the candidate embedded-clause subject span must be ENTIRELY unmarked plain
content (no complementizer/preposition/CLAUSE_LINK/etc token) -- excludes
ditransitive 'told him OF the difficulty they were...' and clause-initial
'now WHEN the forester comes...'; (b) a non-empty accumulated run must precede
the report verb (a real matrix subject) -- excludes clause-initial dialogue tags
('SAID the fox to the crow', '"..." said the wolf' after a comma) entirely, so
DIRECT quoted speech (overwhelmingly the majority of report-verb occurrences in
the frozen Aesop+Grimm corpus) is untouched.

SCOPE (deliberately narrow, reported honestly): only INDIRECT-speech finite-
clause complements with NO comma/quote boundary before the report verb are
affected. Direct quotes ("'...' said X" / "X said, '...'") are UNCHANGED --
`_segment_into_clauses`'s pre-existing comma-boundary handling already isolates
them into their own (verb-initial, subject-less) clause, so this phase's `cur`
non-empty guard never fires there. Measured against the frozen Aesop+Grimm
corpus: the real diff was audited down to 2 sentences, BOTH neutral-or-
improvement (predications identical, or a strict superset with one honestly-
additional 'X said Y' fact) -- zero regressions, see the commit for the full
audit.

Run: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 python3 -m pytest \
    tests/test_embedded_clause_migrated.py -p no:randomly -q
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core            # noqa: E402
from domains import dictionary_lexicon as dl          # noqa: E402
from domains import reading_collapse as rc            # noqa: E402
from domains import comprehension_reader as cr        # noqa: E402


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


@pytest.fixture()
def agent():
    # function-scoped: each test gets a FRESH graph, the reading-parity
    # discipline this project's tests always follow.
    dl.warm_wordnet("en")
    s, node = boot_core()
    return _Agent(s, node)


# --------------------------------------------------------------------------- #
#  HEADLINE — the report-verb complement decomposes to its OWN nested event
#  instead of mashing into one flat object NP.
# --------------------------------------------------------------------------- #
def test_headline_report_verb_complement_decomposes(agent):
    d = rc.decompose_sentence(agent, "Public Citizen said Exxon captured the government.")
    assert d["multi_clause"] is True, d
    assert d["clauses"] == [
        ["public", "citizen", "said"],
        ["exxon", "captured", "the", "government"],
    ], d
    # the matrix's own predication (report verb, subject, the complement's OWN
    # subject) AND the complement's OWN clean event both ground -- no flat
    # 'exxon_captured_government' mega-entity anywhere in this list.
    assert d["predications"] == [
        ["said", "citizen", "exxon"],
        ["captured", "exxon", "government"],
    ], d
    assert not any("captured_government" in str(p[-1]) for p in d["predications"]), d


def test_headline_end_to_end_situation_model_nests_the_event_under_the_say(agent):
    """The full comprehension pipeline: a distinct `capture` SmEvent grounds
    (not a `said_exxon_captured_government` mega-entity), and it is NESTED under
    the `say` event -- the say event's theme/object and the capture event's own
    agent are the SAME SmEntity node (graph-reachable from the report)."""
    cr.read_and_comprehend(agent, "Public Citizen said Exxon captured the government.")
    sub = agent.s
    events = {sub.node(n)["attrs"].get("verb"): sub.node(n)["attrs"] for n in sub.nodes("SmEvent")}
    assert "say" in events, events
    assert "capture" in events, events
    say_ev, cap_ev = events["say"], events["capture"]
    # NOT a mega-entity: no SmEntity name contains the mashed compound anywhere.
    names = [sub.node(n)["attrs"].get("name") for n in sub.nodes("SmEntity")]
    assert not any(nm and "captured_government" in nm for nm in names), names
    assert not any(nm and "captured_the_government" in nm for nm in names), names
    # NESTED: the say event's own object/theme IS the capture event's agent --
    # the same entity, graph-reachable in one hop from the report.
    assert say_ev.get("arg1") == cap_ev.get("idx_protagonist"), (say_ev, cap_ev)


# --------------------------------------------------------------------------- #
#  CONTROLS — non-report sentence and direct quoted speech are UNTOUCHED.
# --------------------------------------------------------------------------- #
def test_control_non_report_sentence_unchanged(agent):
    """A sentence with no report verb at all decomposes exactly as a single
    plain SVO clause (this phase adds no new boundary)."""
    d = rc.decompose_sentence(agent, "The dog chased the cat.")
    assert d["multi_clause"] is False, d
    assert d["clauses"] == [["the", "dog", "chased", "the", "cat"]], d
    assert d["predications"] == [["chased", "dog", "cat"]], d


def test_control_direct_quote_unchanged(agent):
    """Direct quoted speech ('QUOTE,' said X) is UNTOUCHED -- the comma already
    isolates 'said the wolf' into its OWN clause with 'said' CLAUSE-INITIAL (no
    subject accumulated before it), so this phase's `cur`-non-empty guard never
    fires. This is the OVERWHELMING majority shape of report-verb occurrences in
    the frozen Aesop+Grimm corpus."""
    d = rc.decompose_sentence(agent, "'I am hungry,' said the wolf.")
    assert d["clauses"] == [["i", "am", "hungry"], ["said", "the", "wolf"]], d
    assert d["predications"] == [["is_a", "i", "hungry"], ["is_a", "i", "wolf"]], d


def test_control_ditransitive_report_verb_unchanged(agent):
    """A ditransitive report verb (indirect object + oblique PP, no embedded
    clause) is UNTOUCHED -- 'told him OF the difficulty' is not a clause subject
    ('of' is an ordinary oblique argument of 'told'). This exact sentence is the
    audited false positive this phase's guard was tightened against."""
    d = rc.decompose_sentence(
        agent, "The fox told him of the difficulty they were both in.")
    assert d["multi_clause"] is False, d
    assert d["n_boundaries"] == 0, d


def test_control_explicit_that_complementizer_path_unchanged(agent):
    """The PRE-EXISTING explicit-'that' complementizer path
    (`_is_complementizer_that`) is untouched by this phase -- a ditransitive
    report verb with an explicit 'that' ('assured him THAT...') keeps its
    indirect object in the matrix clause exactly as before, never swallowed as a
    bogus embedded-clause subject by this phase's NEW implicit-complement
    branch."""
    d = rc.decompose_sentence(
        agent, "The Bat assured him that he was not a bird, but a mouse.")
    assert d["clauses"][0] == ["the", "bat", "assured", "him"], d
    assert ["assured", "bat", "him"] in d["predications"], d


# --------------------------------------------------------------------------- #
#  GRAPH-NATIVE — the decision is HELD DATA, not a Python literal `if`:
#  ablating the REPORT class's seed forms REVERTS the read.
# --------------------------------------------------------------------------- #
def test_ablating_the_held_report_class_reverts_the_read(agent):
    sub, _, _ = rc._resolve(agent)
    rc.ensure_codebook(agent)
    node = rc._report_class_node(sub)
    assert node is not None
    assert "said" in [str(f).lower() for f in sub.node(node)["attrs"].get("forms") or []]
    assert rc._report_literal_member(agent, "said") is True

    # Ablate the held class (simulating an agent that was never taught it, or one
    # where the fact was retracted) -- clear the seed forms list.
    sub.set_attr(node, "forms", [])
    assert rc._report_literal_member(agent, "said") is False

    d = rc.decompose_sentence(agent, "Public Citizen said Exxon captured the government.")
    # Reverted to the PRE-PHASE-2 (buggy) reading: 'said' no longer opens an
    # implicit complement -- the whole span reads as one un-decomposed clause
    # (falls through to the single-clause reader downstream, exactly as before).
    assert d["multi_clause"] is False, d
    assert d["n_boundaries"] == 0, d


def test_held_class_present_by_default_on_a_fresh_agent(agent):
    """A freshly-seeded agent already carries the taught REPORT class (bootstrapped
    graph DATA, not runtime-only test scaffolding)."""
    sub, _, _ = rc._resolve(agent)
    rc.ensure_codebook(agent)
    node = rc._report_class_node(sub)
    assert node is not None
    forms = [str(f).lower() for f in sub.node(node)["attrs"].get("forms") or []]
    for w in ("say", "said", "wrote", "replied"):
        assert w in forms, forms


# --------------------------------------------------------------------------- #
#  SOURCE AUDIT — the decision is a graph read (held class membership), never a
#  hardcoded Python conditional on the verb surface.
# --------------------------------------------------------------------------- #
def test_source_audit_no_hardcoded_verb_branch():
    mod_path = os.path.join(ROOT, "domains", "reading_collapse.py")
    src = open(mod_path).read()
    assert 'w == "said"' not in src
    assert "def _report_literal_member(agent, word: str) -> bool" in src
    assert "def _is_report_complement_here(agent, lex: dict, region: list, wi: int) -> bool" in src


def test_source_audit_guard_reads_held_class_not_literal():
    import inspect
    src = inspect.getsource(rc._is_report_complement_here)
    assert "_report_literal_member(agent, w)" in src
    src2 = inspect.getsource(rc._report_literal_member)
    assert '_report_class_node(sub)' in src2
    assert 'sub.node(node)["attrs"].get("forms")' in src2
