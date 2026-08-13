"""MAC/FAC A5 + A6 structural fallback — the live Class A/Class B (and, for
A5, false-abstain/no-regression) demonstration, permanently encoded as a
pytest gate, mirroring `tests/test_seed_signature_structural_fallback.py`
(A3) and `tests/test_editop_applicability_gate.py` (A4) exactly.

A5 (`domains/reflective_faculty.py::_compose_datum_feedback_rule`): the
primary `keywords_text` Argmax over `_DATUM_FEEDBACK_CANDIDATES` is
UNCHANGED and tried first; only on genuine abstain does a fallback score
each row by its own real operational identity (`node_type`/`datum_attr`/
`belief_attr`) instead of the hand-authored prose blurb. The real table has
exactly ONE row, so this suite demonstrates FALSE-ABSTAIN AVOIDANCE (a real,
useful fix) rather than multi-candidate discrimination (not measurable at
N=1) — see `MAC_FAC_A5_A6_RESULTS.md` for the honest scope statement this
mirrors.

A6 (`domains/reflective_faculty.py::_compose_rule_literal_variant`): the
primary per-(rule,literal)-pair local-vocabulary Argmax is UNCHANGED and
tried first; only on system-wide abstain does a two-tier fallback pick the
RULE by its own `where_signature_json` (the FULL where-clause structural
signature, covering sibling guard conditions the local per-literal vocab
scorer can never see) and then the literal WITHIN that rule by the
unchanged local vocab scorer, floor lifted. Probes are mechanically
discovered by `scripts/a6_discover_probes.py` over the REAL, full-boot
`writes_where_literal==1.0 AND skippable==1.0` RuleSummary population --
never hand-invented.
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.world_adapter import WorldAdapter          # noqa: E402
from substrate.boot_all import load_all_seeds              # noqa: E402

import domains.reflective_faculty as rf                                  # noqa: E402


@pytest.fixture(scope="module")
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


def _promote(a, content, kind="reported", tag="probe"):
    sc = a.s.add_node("SelfConcern", {"status": "noted", "source": "explicit_report",
                                      "kind": kind, "content": content})
    st = a.s.add_node("StandingConcern", {"name": tag, "kind": kind})
    a.inner.add_edge_unchecked(sc, "promoted_to", st)
    return sc, st


# --------------------------------------------------------------------------- #
#  A5 -- _compose_datum_feedback_rule
# --------------------------------------------------------------------------- #

def test_a5_class_b_primary_unchanged_fallback_never_used(agent):
    """A concern whose words already hit >= 2 keywords_text tokens must be
    resolved by the PRIMARY alone -- byte-identical to pre-fix behaviour,
    fallback never consulted."""
    a = agent
    _promote(a, "your reliability trust tracking is broken", tag="a5_classb")
    rep = rf._compose_datum_feedback_rule(a, ["a5_classb"], "a5b")
    assert rep["built"] is True, rep
    assert rep["fallback_used"] is False
    assert rep["datum_attr"] == "self_report_contradiction_count"
    assert rep["belief_attr"] == "self_report_reliability"


def test_a5_class_a_false_abstain_recovered_by_structural_fallback(agent):
    """A concern that names the row's own structural identity
    (node_type='Interlocutor', a token of datum_attr='count') but hits ZERO
    keywords_text tokens must be recovered by the fallback -- the primary
    alone would abstain (see the standalone reproduction below)."""
    a = agent
    content = "the interlocutor object's count field is climbing every single week"
    # confirm, mechanically, that the PRIMARY alone genuinely abstains on
    # this exact content -- not assumed, reproduced from the unmodified
    # keywords_text row.
    words = [w.lower().strip(".,;:!?'\"") for w in content.split()]
    words = [w for w in words if len(w) > 2]
    kw_row = rf._DATUM_FEEDBACK_CANDIDATES[0]["keywords_text"].split()
    assert sum(1 for w in words if w in kw_row) < 2, "probe must genuinely abstain on the primary"

    _promote(a, content, tag="a5_classa")
    rep = rf._compose_datum_feedback_rule(a, ["a5_classa"], "a5a")
    assert rep["built"] is True, rep
    assert rep["fallback_used"] is True
    assert rep["datum_attr"] == "self_report_contradiction_count"
    assert rep["belief_attr"] == "self_report_reliability"


def test_a5_still_abstains_when_neither_signal_names_it(agent):
    """Regression: content naming NEITHER the prose blurb NOR the row's own
    structural identity must still abstain honestly (byte-identical to
    pre-fix)."""
    a = agent
    _promote(a, "you always mumble incoherently", tag="a5_none")
    rep = rf._compose_datum_feedback_rule(a, ["a5_none"], "a5n")
    assert rep["built"] is False
    assert "abstain" in rep["wall"]


# --------------------------------------------------------------------------- #
#  A6 -- _compose_rule_literal_variant
# --------------------------------------------------------------------------- #

# Probes mechanically discovered by scripts/a6_discover_probes.py over the
# REAL, full-boot writes_where_literal==1.0 & skippable==1.0 RuleSummary
# population (642 rules, 13016 (rule,literal) pairs, 746 distinct local-
# vocab words). "adopt"/"denied" are confirmed ABSENT from the GLOBAL
# local-vocab union (no (rule,candidate) pair anywhere can ever locally
# score on them) but present in adopt_denied_on_regression's own
# where_signature_json (its sibling `Not(Eq(adopt_denied, true))` guard,
# invisible to the local per-candidate scorer, which only ever sees the
# `regressions > 0` candidate's own narrow subtree).

def test_a6_class_b_primary_unchanged_fallback_never_used(agent):
    """The existing, already-passing probe
    (test_rule_literal_variation_migrated.py) must stay byte-identical:
    primary alone resolves it, fallback never consulted."""
    a = agent
    _promote(a, "your narrative shape escalation floor of three sentences read before it "
                "fires makes you escalate too rarely on short stories", tag="a6_classb")
    rep = rf._compose_rule_literal_variant(a, ["a6_classb"], "a6b")
    assert rep["built"] is True, rep
    assert rep["fallback_used"] is False
    assert rep["removed_rule"] == "escalate_narrative_shape"
    assert rep["direction"] == "increase_fires"


def test_a6_class_a_recovered_by_full_where_signature_fallback(agent):
    """A concern that names adopt_denied_on_regression's SIBLING guard
    condition (adopt/denied -- reachable only from the rule's FULL
    where-signature, not from the regressions>0 candidate's own local
    subtree) must be recovered by the fallback -- the primary alone
    genuinely abstains system-wide on these exact words (mechanically
    confirmed by the discovery script, not assumed)."""
    a = agent
    content = ("it keeps getting denied and I never actually get to adopt anything, "
               "this happens too rarely")
    words = [w.lower().strip(".,;:!?'\"") for w in content.split()]
    words = [w for w in words if len(w) > 2]
    # confirm, mechanically, that NO (rule, candidate) pair anywhere in the
    # real pool scores >= 2 on these exact words under the unchanged primary
    # -- not assumed, reproduced live against the real provenance.
    sub, native, _ag = rf._resolve_agent(a)
    rf._ensure_where_literal_rule_provenance(sub, native)
    import json as _json
    max_local = 0
    for n in sub.nodes("RuleSummary"):
        at = sub.node(n)["attrs"]
        if at.get("writes_where_literal") != 1.0 or at.get("skippable") != 1.0:
            continue
        try:
            rj = _json.loads(at.get("rule_json") or "{}")
        except Exception:
            continue
        for cand in rf._find_where_lits(rj.get("where")):
            vocab = rf._collect_vocab_tokens(cand)
            overlap = sum(1 for w in words if w in vocab)
            max_local = max(max_local, overlap)
    assert max_local < 2, "probe must genuinely abstain system-wide on the primary"

    _promote(a, content, tag="a6_classa")
    rep = rf._compose_rule_literal_variant(a, ["a6_classa"], "a6a")
    assert rep["built"] is True, rep
    assert rep["fallback_used"] is True
    assert rep["removed_rule"] == "adopt_denied_on_regression"
    assert rep["direction"] == "increase_fires"


def test_a6_still_abstains_when_neither_signal_names_it(agent):
    """Regression: content naming NEITHER a local candidate vocabulary NOR
    any rule's own full where-signature must still abstain honestly
    (byte-identical to pre-fix)."""
    a = agent
    _promote(a, "you always mumble incoherently and nothing makes sense", tag="a6_none")
    rep = rf._compose_rule_literal_variant(a, ["a6_none"], "a6n")
    assert rep["built"] is False
    assert "abstain" in rep["wall"]
