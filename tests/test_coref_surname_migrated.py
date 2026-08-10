"""test_coref_surname_migrated — Phase 3 of READER_PARSER_MIGRATION.md: coref /
entity naming keeps a multi-token PROPER NAME's full span.

THE BUG. "Robert Levy, an attorney at ExxonMobil, will join the Justice
Department." grounds the person entity as `robert` -- the surname "Levy" is
dropped. Root cause (traced live, not assumed): the comma-appositive clause
segmentation (`reading_collapse.decompose_sentence` / `_clause_subject_words`)
carries only the FIRST token of the pre-comma subject NP forward as the
`shared_subject` thread for the verb-bearing continuation clause -- sometimes
because the appositive's own clause has no finite verb at all (`_clause_
subject_words` returns None so the second/later token of the name is simply
never re-examined once the reduction has already discarded it), sometimes
because a surname collides with a common verb sense ('Levy'/'levy' -- "to
levy a tax") and the clause-internal main-verb tier wrongly treats the
surname AS the verb. By the time the predication reaches coref, all that
remains is the string "robert" -- there is no longer a Python "pick the head
token" line to delete; the second token is already gone upstream, and fixing
the deep clause-segmentation collision is a much larger, riskier change (and
is Phase 1/2's territory, not Phase 3's).

THE DECISION MOVED GRAPH-NATIVE. Rather than chase the drop through every
upstream mis-segmentation path, coref/entity-naming now COMPLETES a proper
name from the ORIGINAL sentence's orthography at first-mention time: "Robert
Levy" is ONE entity keyed by its FULL capitalised span, never just its head
token. This is `domains.coref_entities._proper_name_span`, gated by a HELD
graph policy flag (`CorefNamingPolicy.keep_full_proper_span`, defaulting ON)
that `resolve_and_ingest` consults after pronoun/deixis substitution and
before bookkeeping/ingest -- so BOTH `_touch_entity` and `situation_model_
reader.ingest_predication` see the extended name, and the state change lands
on ONE entity (`robert_levy`), not a truncated head plus an orphaned
appositive fact. Ablating the flag (this file's own test, below) reverts the
read to the pre-phase truncated name, proving the decision is the held datum,
not a Python `if`.

SCOPE (deliberately narrow, reported honestly): only a genuinely PROPER
(capitalised-in-source) SINGLE-token name immediately followed by further
CAPITALISED, punctuation-free tokens is extended; a name already spanning
multiple tokens (the parse sometimes gets this right on its own -- "John
Kerry", "Robert Smith" with no verb-collision) is left untouched (idempotent
-- no double-extension); a common noun, a lone single-token name with no
capitalised continuation, and a non-proper subject are all unaffected.

BYTE PARITY: `tests/fixtures/reading_parity/reading.json`'s capture.py exercises
only `domains.reading_collapse` (skeleton/decode/ground/event/decompose/heads)
-- it never calls `coref_entities.py` at all, so this phase's change cannot
perturb that fixture (verified: `pytest tests/test_reading_parity_migrated.py`
stays green, unmodified fixture, see the commit/report for the audit).

Run: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 python3 -m pytest \
    tests/test_coref_surname_migrated.py -p no:randomly -q
"""
from __future__ import annotations

import inspect
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core            # noqa: E402
from domains import dictionary_lexicon as dl          # noqa: E402
from domains import coref_entities as ce              # noqa: E402


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


@pytest.fixture(scope="module", autouse=True)
def _warm():
    dl.warm_wordnet("en")


def _fresh():
    s, node = boot_core()
    return _Agent(s, node)


ARTICLE_SENTENCE = ("Robert Levy, an attorney at ExxonMobil, will join "
                     "the Justice Department.")


# --------------------------------------------------------------------------- #
#  HEADLINE — the reported bug, fixed: the full multi-token proper name is
#  kept whole as ONE entity.
# --------------------------------------------------------------------------- #
def test_headline_multitoken_proper_name_kept_whole():
    ag = _fresh()
    r = ce.read_into_situation_model(ag, ARTICLE_SENTENCE)
    model = r["situation_model"]
    assert "robert_levy" in model, model
    assert "robert" not in model, model
    assert "levy" not in model, model


def test_headline_state_lands_on_the_full_span_entity():
    """Not just present in the naming index -- the ACTUAL predication's
    protagonist is the full-span entity (the join event's agent)."""
    ag = _fresh()
    ce.read_into_situation_model(ag, ARTICLE_SENTENCE)
    sub = ag.s
    events = [sub.node(n)["attrs"] for n in sub.nodes("SmEvent")]
    assert any(ev.get("idx_protagonist") == "robert_levy" for ev in events), events


# --------------------------------------------------------------------------- #
#  CONTROLS — single-token names and common nouns are unaffected; a name the
#  parse ALREADY kept whole is not double-extended.
# --------------------------------------------------------------------------- #
def test_control_single_token_name_unaffected():
    ag = _fresh()
    r = ce.read_into_situation_model(ag, "Levy visited the school.")
    assert "levy" in r["situation_model"], r["situation_model"]


def test_control_common_noun_subject_unaffected():
    ag = _fresh()
    r = ce.read_into_situation_model(ag, "The crow sat on the branch.")
    assert "crow" in r["situation_model"], r["situation_model"]


def test_control_already_full_span_name_not_double_extended():
    """'John Kerry visited the school.' already grounds the whole name
    ('john_kerry') via the ordinary parse (no verb-collision, no comma-
    appositive truncation) -- this phase's completion must be a no-op here,
    not a further/duplicate extension."""
    ag = _fresh()
    r = ce.read_into_situation_model(ag, "John Kerry visited the school.")
    assert "john_kerry" in r["situation_model"], r["situation_model"]
    assert "john" not in r["situation_model"], r["situation_model"]


# --------------------------------------------------------------------------- #
#  GRAPH-NATIVE — the decision is HELD DATA, not a Python literal `if`:
#  ablating the naming-policy flag REVERTS the read to the truncated name.
# --------------------------------------------------------------------------- #
def test_ablating_the_held_naming_policy_reverts_the_read():
    ag = _fresh()
    node = ce._naming_policy_node(ag)
    assert node is not None
    assert ce._keep_full_proper_span(ag) is True

    ag.s.set_attr(node, "keep_full_proper_span", 0.0)
    assert ce._keep_full_proper_span(ag) is False

    r = ce.read_into_situation_model(ag, ARTICLE_SENTENCE)
    model = r["situation_model"]
    # reverted to the PRE-PHASE-3 (buggy) reading: the surname is dropped.
    assert "robert" in model, model
    assert "robert_levy" not in model, model


def test_held_policy_present_and_on_by_default_on_a_fresh_agent():
    ag = _fresh()
    assert ce._keep_full_proper_span(ag) is True
    node = ce._naming_policy_node(ag)
    assert ag.s.node(node)["attrs"].get("keep_full_proper_span") == 1.0


# --------------------------------------------------------------------------- #
#  SOURCE AUDIT — the decision is a graph read (a held policy attr), never a
#  hardcoded Python conditional deciding meaning; the orthographic scan itself
#  is the same documented I/O-boundary carve-out `_looks_proper` already uses.
# --------------------------------------------------------------------------- #
def test_source_audit_span_completion_reads_held_policy():
    src = inspect.getsource(ce._proper_name_span)
    assert "_keep_full_proper_span(agent)" in src
    src2 = inspect.getsource(ce._keep_full_proper_span)
    assert '"keep_full_proper_span"' in src2
    assert 'sub.node(nid)["attrs"]' in src2


def test_source_audit_resolve_and_ingest_calls_the_span_completion():
    src = inspect.getsource(ce.resolve_and_ingest)
    assert "_proper_name_span(agent, sentence, arg)" in src


def test_source_audit_no_new_import_re():
    mod_path = os.path.join(ROOT, "domains", "coref_entities.py")
    lines = [ln.strip() for ln in open(mod_path).read().splitlines()]
    assert "import re" not in lines
