"""MAIN-VERB / NESTED-OF PRECEDENCE (Phase 1 of READER_PARSER_MIGRATION.md) —
"He promoted the burning of fossil fuels." used to read `of(he_promoted_burning,
fossil_fuels)` (construction None, no predication grounded): the nested 'of' fired
as the clause's skeleton marker and pre-empted the finite verb 'promoted', which
never reached `_find_main_verb`'s bare-S-V-O fallback (that ladder only runs when
NO skeleton marker fired at all).

THE DECISION MOVED GRAPH-NATIVE: "does a nested 'of' defer to an already-seen
finite verb, or does it head the clause itself" is now a HELD FACT
(`MarkerClass{cls:'OF', yields_to_finite_verb:true}`,
seeds/reading_constructions.json) that `_of_yields_to_finite_verb` reads —
mirroring the pre-existing QUANTIFIER-partitive-glue / BUT-contrast-coordinator
precedent in `domains.reading_collapse._skeleton_from_words` (held MarkerClass
DATA the parser reads, not a Python literal `if`). Hand-authored bootstrapping
DATA (see the commit/report): the parser-internal nature of this decision (it
lives inside the token-by-token skeleton scan, not a rule the agent's own
composer/induce_concern machinery reaches) made agent self-authoring infeasible
here, so the MarkerClass row was hand-added exactly like its QUANTIFIER/BUT
precedents were.

Four additional held-DATA-gated conditions (all measured + audited against the
frozen Aesop+Grimm parity corpus, tests/fixtures/reading_parity/reading.json,
regenerated for this phase) keep the guard from over-firing:
  (a) a genuine TIER-A finite verb precedes the 'of' phrase's own head noun
      (`_left_run_has_finite_verb`) — a verbless genitive/partitive NP ('the son
      of a man') is untouched;
  (b) the clause carries AT MOST ONE finite verb overall
      (`_clause_is_simple_svo`) — a compound/coordinated multi-verb sentence is
      untouched (glueing 'of' away there would exile the WHOLE span to the
      whole-span bare-S-V-O ladder and mash unrelated coordinate clauses);
  (c) no OTHER skeleton marker fires LATER in the clause
      (`_no_later_skeleton_marker`) — a clause with its own downstream
      segmentation point is untouched;
  (d) no marker has fired EARLIER either (`not markers`) — 'of' only glues away
      when it is the clause's SOLE candidate skeleton marker; an
      already-anchored multi-role construction (POSSESS/COP/REL/...) that
      expects 'of' to supply its second role keeps it.

Run: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 python3 -m pytest \
    tests/test_main_verb_of_migrated.py -p no:randomly -q
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
#  HEADLINE — the finite verb wins over a nested 'of' in a simple SVO clause.
# --------------------------------------------------------------------------- #
def test_headline_promoted_burning_of_fossil_fuels(agent):
    r = rc.read_clause(agent, "He promoted the burning of fossil fuels.", write=True)
    assert r["construction"] == "event", r
    assert r["predications"] == [["promoted", "he", "burning_of_fossil_fuels"]], r
    assert r["residual"] == [], r


def test_control_promoted_fossil_fuels_unaffected(agent):
    """The already-working no-'of' control stays byte-identical."""
    r = rc.read_clause(agent, "He promoted fossil fuels.", write=True)
    assert r["construction"] == "event", r
    assert r["predications"] == [["promoted", "he", "fossil_fuels"]], r


def test_corpus_pattern_lion_demanded_daughter_of_woodcutter(agent):
    """The SAME bug pattern found (and fixed) elsewhere in the frozen Aesop
    corpus during the phase-1 diff audit."""
    r = rc.read_clause(
        agent, "A LION demanded the daughter of a woodcutter in marriage.",
        write=True)
    assert r["construction"] == "event", r
    assert r["predications"] == [
        ["demanded", "lion", "daughter_of_woodcutter_in_marriage"]], r


# --------------------------------------------------------------------------- #
#  GENITIVE / PARTITIVE 'of' — UNCHANGED (no finite verb competes for headship).
# --------------------------------------------------------------------------- #
def test_verbless_genitive_of_unchanged(agent):
    """'the son of a man' has no finite verb before the OF phrase's head, so the
    guard never fires -- OF still heads the nested relation exactly as before
    this phase."""
    r = rc.read_clause(agent, "He is the son of a man.", write=True)
    assert r["construction"] == "definitional", r
    assert r["predications"] == [["is_a", "he", "son"]], r
    assert r["residual"] == [["OF"]], r


def test_quantifier_partitive_of_unchanged(agent):
    """The pre-existing QUANTIFIER partitive glue ('hundreds OF protesters')
    is a DIFFERENT held-DATA path and stays untouched by this phase."""
    r = rc.read_clause(agent, "Hundreds of protesters were detained.", write=True)
    assert r["construction"] == "passive", r
    assert r["predications"] == [["detain", "_", "hundreds_of_protesters"]], r


def test_gerund_headed_subject_of_unchanged(agent):
    """A gerund immediately before 'of' ('the BURNING of fossil fuels...') is
    the OF phrase's OWN head, never a competing finite verb -- explicitly
    excluded ('-ing' forms are never finite) so this stays UNCHANGED (still an
    ungrounded residual, not a wrong confident read). write=False/learn=False
    matches the parity-fixture capture discipline (tests/fixtures/
    reading_parity/capture.py) -- this isolates the SKELETON-level decision
    this phase touches from the (unrelated, working-as-designed) sd-loop
    self-learning pipeline that a write=True call would additionally trigger
    for any residual skeleton."""
    r = rc.read_clause(
        agent, "The burning of fossil fuels harmed the planet.",
        write=False, learn=False)
    assert r["construction"] is None, r
    assert r["predications"] == [], r
    assert r["residual"] == [["OF"]], r


def test_compound_sentence_unchanged(agent):
    """A compound/coordinated sentence with ONLY 'of' as a candidate marker
    stays UNCHANGED (the `_clause_is_simple_svo` gate) -- absorbing it would
    otherwise dump the WHOLE multi-verb span into the bare-S-V-O fallback and
    mash independent coordinate clauses into one wrong predication.
    write=False/learn=False -- see the docstring above."""
    r = rc.read_clause(
        agent, "Hans took out his pocket-handkerchief, put the piece of "
               "silver into it, threw it over his shoulder, and jogged off "
               "on his road homewards.", write=False, learn=False)
    assert r["construction"] is None, r
    assert r["predications"] == [], r
    assert r["residual"] == [["OF"]], r


# --------------------------------------------------------------------------- #
#  GRAPH-NATIVE — the decision is HELD DATA, not a Python literal `if`:
#  ablating the OF MarkerClass's `yields_to_finite_verb` fact REVERTS the read.
# --------------------------------------------------------------------------- #
def test_ablating_the_held_fact_reverts_the_read(agent):
    sub, _, _ = rc._resolve(agent)
    rc.ensure_codebook(agent)
    node = rc._marker_node_for_cls(sub, "OF")
    assert node is not None
    assert sub.node(node)["attrs"].get("yields_to_finite_verb") is True

    # Ablate the held fact (simulating an agent that was never taught it, or
    # one where the fact was retracted).
    sub.set_attr(node, "yields_to_finite_verb", False)
    assert rc._of_yields_to_finite_verb(sub) is False

    r = rc.read_clause(agent, "He promoted the burning of fossil fuels.", write=True)
    # Reverted to the PRE-PHASE-1 (buggy) reading: 'of' pre-empts the verb again.
    assert r["skeleton"] == [["OF"]], r
    assert r["construction"] != "event", r
    assert r["predications"] != [["promoted", "he", "burning_of_fossil_fuels"]], r


def test_held_fact_present_by_default_on_a_fresh_agent(agent):
    """A freshly-seeded agent already carries the taught fact (bootstrapped
    graph DATA, not runtime-only test scaffolding)."""
    sub, _, _ = rc._resolve(agent)
    rc.ensure_codebook(agent)
    assert rc._of_yields_to_finite_verb(sub) is True


# --------------------------------------------------------------------------- #
#  SOURCE AUDIT — the decision is a graph read + held POS/WordNet faculties,
#  never a hardcoded verb list or a bare unconditional `if c == "OF"`.
# --------------------------------------------------------------------------- #
def test_source_audit_no_hardcoded_verb_list():
    mod_path = os.path.join(ROOT, "domains", "reading_collapse.py")
    src = open(mod_path).read()
    assert "PROMOTED_VERBS" not in src
    assert "TRANSITIVE_VERBS" not in src
    # the deciding fact is read off the graph (MarkerClass attr), never a
    # bare Python boolean literal guarding the branch.
    assert "def _of_yields_to_finite_verb(sub)" in src
    assert 'at.get("yields_to_finite_verb")' in src


def test_source_audit_guard_reads_held_fact_not_literal():
    import inspect
    src = inspect.getsource(rc._skeleton_from_words)
    assert "_of_yields_to_finite_verb(sub)" in src
    # the finite-verb signal is the SAME held POS/WordNet faculty used
    # throughout this module (no separate ad-hoc verb detector).
    assert "_inflected_verb" in inspect.getsource(rc._left_run_has_finite_verb)
    assert "ir.is_verb_headed" in inspect.getsource(rc._left_run_has_finite_verb)
