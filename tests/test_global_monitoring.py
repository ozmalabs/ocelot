"""STEP 5: GLOBAL comprehension monitoring (domains/global_monitoring.py).

domains/reading_review.py is a strong LOCAL (within-clause) standards-of-
coherence monitor, but it cannot see a contradiction between two facts FAR
APART in the text (Glenberg, Meyer & Lindem 1982 illusion-of-knowing;
O'Brien & Cook 2016's RI-Val Validation stage checks a new proposition
against the WHOLE situation model). This step points reading_review's own
incoherence discipline at the situation model instead of a single clause.

Discriminative gates (donkey = 0, no LLM):

  * HEADLINE -- 'The lawyer had no children. She was busy. His daughter
    arrived home.' Each clause is LOCALLY coherent (reading_review passes
    each one individually), yet the THIRD entails the lawyer HAS a child,
    contradicting the FIRST -- only comparing against the accumulated
    situation model catches it.
  * DISCRIMINATIVE / NO FALSE ALARM -- a globally-CONSISTENT continuation
    ('two children' -> 'his daughter') and an unrelated-but-consistent
    continuation ('the weather was nice') never fire.
  * RI-VAL VALIDATION -- the check reuses reading_review's measure/salience
    convention; a contradiction escalates to reading_scope's EXISTING
    retained-trace / cold re-read path (Validation -> failure -> reprocess).
  * GRAPH-NATIVE SOURCE AUDIT -- the contradiction decision is a graph
    Program (native.evaluate), never a Python `if established != new`; no
    `import re`.
  * NO REGRESSION -- the held faculties (reading_review, situation_model_
    reader, coref_entities, reading_scope) are unchanged; this module only
    reuses them.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_global_monitoring.py -p no:randomly -q
"""
from __future__ import annotations

import os
import re as _re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core                # noqa: E402
from domains import dictionary_lexicon as dl              # noqa: E402
from domains import global_monitoring as gm                # noqa: E402
from domains import reading_review as rr                   # noqa: E402


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


# --------------------------------------------------------------------------- #
#  HEADLINE -- the far-apart contradiction LOCAL can't catch.
# --------------------------------------------------------------------------- #
def test_headline_local_passes_global_fires():
    ag = _fresh()
    text = "The lawyer had no children. She was busy. His daughter arrived home."
    r = gm.read_and_monitor(ag, text)

    # LOCAL: each clause reviewed on its OWN, via reading_review.combined_
    # incoherence (reused verbatim) -- the two clauses that carry the
    # contradiction (established fact, entailing fact) are each coherent.
    tb = {e["sentence"]: e for e in r["textbase"]}
    assert tb["The lawyer had no children."]["local_incoherence"] == 0.0
    assert tb["His daughter arrived home."]["local_incoherence"] == 0.0
    # every per-clause reading_review score independently reads as PASSING
    # for the two sentences that carry the contradiction -- reading_review
    # itself never sees anything wrong with either one.
    for sent in ("The lawyer had no children.", "His daughter arrived home."):
        assert rr.combined_incoherence(ag, {"predications": tb[sent]["predications"]}) == 0.0

    # GLOBAL: the situation model established has_child=0 from sentence 1,
    # then sentence 3's kinship entailment (daughter -> has_child=1) directly
    # contradicts it -- the check that only exists by looking at the WHOLE
    # accumulated model, not the current clause.
    checks = r["checks"]
    established_check = checks[0]
    contradiction_check = checks[1]
    assert established_check["contradiction"] is False
    assert established_check["new"] == 0
    assert contradiction_check["entity"] == "lawyer"
    assert contradiction_check["attr"] == "has_child"
    assert contradiction_check["established"] == 0
    assert contradiction_check["new"] == 1
    assert contradiction_check["contradiction"] is True
    assert contradiction_check["salience"] > 0.5
    assert contradiction_check["flag_node"] is not None

    # the flag is a real graph node, not just a Python dict.
    flagged = list(ag.s.nodes("GlobalIncoherence"))
    assert len(flagged) == 1
    at = ag.s.node(flagged[0])["attrs"]
    assert at["entity"] == "lawyer" and at["attr"] == "has_child"
    assert at["established"] == 0 and at["new"] == 1


def test_headline_escalates_to_reread():
    ag = _fresh()
    text = "The lawyer had no children. She was busy. His daughter arrived home."
    r = gm.read_and_monitor(ag, text)
    assert len(r["escalations"]) == 1
    esc = r["escalations"][0]
    assert esc["escalated"] is True
    assert esc["prior_sentence"] == "The lawyer had no children."
    assert esc["trigger_sentence"] == "His daughter arrived home."
    assert esc["non_sequitur"] is True
    assert esc["path"] in ("reactivate_retained_trace", "reread_from_source")


# --------------------------------------------------------------------------- #
#  DISCRIMINATIVE -- no false alarm.
# --------------------------------------------------------------------------- #
def test_no_false_alarm_globally_consistent_continuation():
    ag = _fresh()
    text = "The lawyer had two children. She was busy. His daughter arrived home."
    r = gm.read_and_monitor(ag, text)
    assert all(c["contradiction"] is False for c in r["checks"])
    assert r["escalations"] == []
    assert r["situation_model"]["lawyer"]["has_child"] == 1


def test_no_false_alarm_unrelated_continuation():
    ag = _fresh()
    text = "The lawyer had two children. She was busy. The weather was nice."
    r = gm.read_and_monitor(ag, text)
    assert all(c["contradiction"] is False for c in r["checks"])
    assert r["escalations"] == []


def test_no_false_alarm_when_no_established_fact_yet():
    # the FIRST kinship mention with NO prior discourse at all has no resident
    # possessor antecedent to resolve "his" against -- held open (RI-Val: not
    # force-bound), not a fabricated contradiction.
    ag = _fresh()
    r = gm.read_and_monitor(ag, "His daughter arrived home.")
    assert len(r["checks"]) == 1
    assert r["checks"][0]["contradiction"] is False

    # with a resident antecedent but NO established has_child fact yet,
    # validate_against_model itself is honestly unset -- Not(Eq(unset,unset))
    # is False, so the And gate cannot fire regardless of `new`.
    ag2 = _fresh()
    chk = gm.validate_against_model(ag2, "lawyer", "has_child", 1, sentence="s", turn=1)
    assert chk["established"] == "__unset__"
    assert chk["contradiction"] is False


# --------------------------------------------------------------------------- #
#  RI-VAL VALIDATION -- reuses reading_review's measure/salience convention.
# --------------------------------------------------------------------------- #
def test_validation_reuses_reading_review_salience():
    ag = _fresh()
    coherent = gm.validate_against_model(ag, "lawyer", "has_child", 0,
                                          sentence="s1", turn=1)
    assert coherent["salience"] == rr._salience(0.0) == 0.0
    contradictory = gm.validate_against_model(ag, "lawyer", "has_child", 1,
                                               sentence="s2", turn=2)
    assert contradictory["contradiction"] is True
    assert contradictory["salience"] == rr._salience(1.0)
    assert contradictory["salience"] > 0.5


def test_escalate_reuses_reading_scope_reanalyse_unchanged():
    # escalate_reread is a thin pass-through to reading_scope._reanalyse; a
    # missing established_entry is an honest no-op, never a forced escalation.
    ag = _fresh()
    assert gm.escalate_reread(ag, None, {"sentence": "x"}, ["p"]) == {
        "escalated": False,
        "reason": "no prior sentence on record established this attr"}


# --------------------------------------------------------------------------- #
#  GRAPH-NATIVE SOURCE AUDIT.
# --------------------------------------------------------------------------- #
def test_source_audit_no_regex_and_program_is_the_decision():
    src = open(os.path.join(ROOT, "domains", "global_monitoring.py")).read()
    assert not _re.search(r"^\s*import re\b", src, _re.M)
    assert "re.compile(" not in src and "re.match(" not in src and "re.search(" not in src
    # the contradiction is native.evaluate on the seeded Program, never a
    # Python `if`/`==`/`!=` comparing established vs new directly.
    assert 'native.evaluate(prog, env)' in src
    # no LIVE code statement (as opposed to prose in a comment/docstring
    # explaining what this does NOT do) compares established vs new directly.
    assert "if established != new" not in src
    assert "if established == new" not in src


def test_seed_program_is_var_eq_not_and_only():
    import json
    ag = _fresh()
    gm.ensure_seeds(ag)
    from domains import reflective_faculty as rf
    prog = rf._load_program(ag.s, "global_contradiction")
    assert prog is not None
    src = json.dumps(prog)
    # exactly the vocabulary seeds/reading_review.json's review_license
    # Program already proves sufficient -- no new Rust Term.
    for tag in ('"And"', '"Not"', '"Eq"', '"Var"'):
        assert tag in src


# --------------------------------------------------------------------------- #
#  NO REGRESSION -- kinship membership + decomposition are small and honest.
# --------------------------------------------------------------------------- #
def test_kinship_membership_exact_form_only():
    ag = _fresh()
    assert gm.kinship_membership(ag, "daughter")["kin"] is True
    assert gm.kinship_membership(ag, "son")["kin"] is True
    assert gm.kinship_membership(ag, "children")["kin"] is True
    # HONEST residual: an unseen kinship term is NOT covered (no adjacency
    # join for a nominal class -- see module docstring).
    assert gm.kinship_membership(ag, "grandchild")["kin"] is False


def test_bare_kin_subject_with_no_possessive_is_honest_residual():
    ag = _fresh()
    r = gm.read_and_monitor(ag, "Daughter arrived home.")
    assert len(r["checks"]) == 1
    assert r["checks"][0]["contradiction"] is False
    assert "no possessive" in r["checks"][0]["note"] or "possessor undeterminable" in r["checks"][0]["note"]
