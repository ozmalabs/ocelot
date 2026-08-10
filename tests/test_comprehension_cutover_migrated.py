"""test_comprehension_cutover_migrated — Deep-Reader Wave 3.

Cuts the conversation comprehension contract (`comp_*` attrs on the inbound
Message) over to the deep reader (Wave 2's shadow read,
`WorldAdapter._shadow_read_turn`) EXACTLY where the divergence corpus
(`tests/fixtures/comprehension_divergence/divergence.json`) says it is
parity-or-better, per the cutover policy implemented in
`substrate/world_adapter.py::_write_comprehension_to_graph`:

  1. kind        -- NO cutover (`sak_kind` stays authoritative, 93.8%
     agreement). A mechanical `speech_act_divergence=1.0` DATUM is recorded
     on disagreement; nothing consumes it as a routing decision.
  2. predicate/content (instructions only) -- STRICT ENRICHMENT: the OLD
     leading-verb parse wins whenever it is present (byte-identical); the
     shadow read's own predication/focus fills in ONLY when the old parse
     produced nothing.
  3. topic/focus -- ENRICHMENT ONLY: `comp_topic` is written from
     `shadow_focus` ONLY when nothing else in `_write_comprehension_to_graph`
     claimed the turn AND the shadow focus is a single clean token.

Every enrichment must be a no-op with `shadow_read=False` (or when the shadow
read errored) -- that is the wave's own no-regression bar, gated here
alongside the enrichment-fires proofs.
"""
from __future__ import annotations

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.world_adapter import WorldAdapter                       # noqa: E402
from substrate.boot_all import load_all_seeds                          # noqa: E402
from domains import dictionary_lexicon as dl                           # noqa: E402
from domains import comprehend_text as ct                              # noqa: E402

FIXTURE = os.path.join(ROOT, "tests", "fixtures", "speech_act_parity",
                       "speech_act.json")

# The SAME representative conversational battery Wave 2's own shadow-read gate
# uses (test_shadow_read_migrated._BATTERY), so the shadow-off no-behaviour-
# change proof is exercised over the same corpus the mission's own gates
# drive -- NO teacher attached, deterministic, no network grounding.
_BATTERY = [
    ("What do you know about the moon?", "question"),
    ("What are you?", "question"),
    ("How do you learn?", "question"),
    ("Summarise the report.", "request"),
    ("Fix your grammar.", "request"),
    ("the sky is blue", "statement"),
    ("hello", "greeting"),
    ("What is the moon made of?", "question"),
    ("Please summarise the report.", "request"),
    ("Would you kindly open the door?", "request"),
]

_ENRICHMENT_ATTRS = ("comp_predicate_source", "comp_content_source",
                     "comp_topic_source", "speech_act_divergence")


@pytest.fixture(scope="module", autouse=True)
def _warm():
    dl.warm_wordnet("en")


@pytest.fixture(scope="module")
def fixture():
    with open(FIXTURE) as f:
        return json.load(f)


def _records(fixture):
    for group, recs in sorted(fixture["corpus"].items()):
        for rec in recs:
            yield group, rec


def _fresh(shadow_read):
    a = WorldAdapter(seeds=(), shadow_read=shadow_read)
    load_all_seeds(a)
    return a


# --------------------------------------------------------------------------- #
#  SHADOW OFF -- byte-identical to pre-Wave-3 (no enrichment attr ever
#  appears; the reply is unaffected -- the same no-behaviour-change bar
#  Wave 2's own shadow-read gate proved for the shadow read itself).
# --------------------------------------------------------------------------- #
def test_shadow_off_no_enrichment_attrs_across_battery():
    for text, sa in _BATTERY:
        a = _fresh(False)
        a.converse(text, speech_act=sa)
        mid = a._last_turn_inbound
        attrs = a.s.node(mid)["attrs"]
        for k in _ENRICHMENT_ATTRS:
            assert k not in attrs, (
                "%r must not appear with shadow_read=False (text=%r)" % (k, text))


def test_shadow_off_replies_byte_identical_to_shadow_on_off_pair():
    """The SAME no-behaviour-change proof Wave 2 gated for the shadow read
    itself, re-run now that _write_comprehension_to_graph ALSO reads
    shadow_* attrs: shadow_read=False must still produce byte-identical
    replies to a shadow_read=True run (the enrichment branches only ever
    ADD comp_* data the OLD path left unset; they must never change which
    reply the turn produces when the old path already had an answer -- and
    the reply-affecting fixture rows below already had one)."""
    for text, sa in _BATTERY:
        off = _fresh(False)
        on = _fresh(True)
        r_off = off.converse(text, speech_act=sa)
        r_on = on.converse(text, speech_act=sa)
        assert r_off == r_on, (
            "cutover enrichment changed converse()'s reply for %r:\n  off=%r\n  on=%r"
            % (text, r_off, r_on))


# --------------------------------------------------------------------------- #
#  POLICY 2 -- predicate/content: fixture parity (old wins whenever present,
#  even with shadow_read=True) + the enrichment mechanism itself.
# --------------------------------------------------------------------------- #
def test_instruction_fixture_predicate_content_byte_identical_with_shadow_on(fixture):
    """Every instruction row of the frozen speech_act parity fixture must
    produce the SAME comp_predicate/comp_content with shadow_read=True as
    the pre-Wave-3 path (the OLD predicate is present on every instruction
    row in this fixture, so the enrichment branch never activates here --
    this is the parity gate the mission names)."""
    a = _fresh(True)
    mismatches = []
    for group, rec in _records(fixture):
        if rec["kind"] != "instruction":
            continue
        text = rec["text"]
        mid = a.receive_utterance(text, speech_act=a.classify_speech_act(text))
        a._shadow_read_turn(mid, text)
        kind = a._graph_kind_for(mid, text)
        comp = ct.comprehend_text(a, text, kind=kind)
        a._write_comprehension_to_graph(mid, comp)
        attrs = a.s.node(mid)["attrs"]
        got_pred = attrs.get("comp_predicate")
        got_content = attrs.get("comp_content")
        if got_pred != rec["predicate"] or got_content != rec["content"]:
            mismatches.append((group, text,
                               (rec["predicate"], got_pred),
                               (rec["content"], got_content)))
        # the enrichment tag must NEVER appear on a fixture row -- every
        # instruction row in this corpus already carries an old predicate.
        assert "comp_predicate_source" not in attrs, text
        assert "comp_content_source" not in attrs, text
    assert not mismatches, "instruction predicate/content parity broke:\n" + \
        "\n".join(map(repr, mismatches))


def test_predicate_content_enrichment_fires_only_when_old_predicate_absent():
    """Mechanism proof (a constructed Comprehension, since the real corpus
    happens to carry an old predicate on every instruction row -- see the
    ledger's honest coverage note): when the OLD parse's dispatch carries no
    predicate at all, the shadow read's own predicate/focus (already on the
    Message, exactly as `_shadow_read_turn` would have left them) fill in
    comp_predicate/comp_content, tagged with a `_source` marker."""
    a = _fresh(True)
    mid = a.receive_utterance("dummy instruction text", speech_act="statement")
    a.inner.set_attr(mid, "shadow_predicate", "summarise")
    a.inner.set_attr(mid, "shadow_focus", "report")
    comp = ct.Comprehension(raw="dummy instruction text", kind="instruction",
                            dispatch={}, frame={"elements": []})
    a._write_comprehension_to_graph(mid, comp)
    attrs = a.s.node(mid)["attrs"]
    assert attrs.get("comp_predicate") == "summarise"
    assert attrs.get("comp_predicate_source") == "shadow_enrichment"
    assert attrs.get("comp_content") == "report"
    assert attrs.get("comp_content_source") == "shadow_enrichment"


def test_predicate_content_enrichment_skipped_when_old_predicate_present():
    """The old predicate wins even when the shadow read disagrees -- the
    'old wins on disagreement' parity bar, proven directly (not just by
    corpus absence of the case)."""
    a = _fresh(True)
    mid = a.receive_utterance("fix your grammar", speech_act="statement")
    a.inner.set_attr(mid, "shadow_predicate", "designate")   # deliberately DIFFERENT
    a.inner.set_attr(mid, "shadow_focus", "something_else")
    comp = ct.Comprehension(raw="fix your grammar", kind="instruction",
                            dispatch={"path": "instruction", "predicate": "fix",
                                     "object": "grammar"},
                            frame={"elements": []})
    a._write_comprehension_to_graph(mid, comp)
    attrs = a.s.node(mid)["attrs"]
    assert attrs.get("comp_predicate") == "fix"
    assert "comp_predicate_source" not in attrs
    assert attrs.get("comp_content") == "grammar"
    assert "comp_content_source" not in attrs


def test_predicate_content_enrichment_noop_with_shadow_off():
    """The same absent-old-predicate case, but with no shadow_* attrs on the
    Message at all (shadow_read=False shape) -- the enrichment branch must
    be a clean no-op, leaving comp_predicate/comp_content unset exactly as
    pre-Wave-3."""
    a = _fresh(False)
    mid = a.receive_utterance("dummy instruction text", speech_act="statement")
    comp = ct.Comprehension(raw="dummy instruction text", kind="instruction",
                            dispatch={}, frame={"elements": []})
    a._write_comprehension_to_graph(mid, comp)
    attrs = a.s.node(mid)["attrs"]
    assert attrs.get("comp_predicate") is None
    # comp_content still gets the raw-text fallback (`_instruction_content`'s
    # OWN unchanged behaviour) -- unaffected by the cutover.
    assert attrs.get("comp_content") == "dummy instruction text"
    assert "comp_predicate_source" not in attrs
    assert "comp_content_source" not in attrs


# --------------------------------------------------------------------------- #
#  POLICY 3 -- topic/focus enrichment: fires only in the routed-nowhere case,
#  restricted to a single clean token.
# --------------------------------------------------------------------------- #
def test_topic_enrichment_fires_when_routed_nowhere():
    a = _fresh(True)
    mid = a.receive_utterance("dummy question text", speech_act="statement")
    a.inner.set_attr(mid, "shadow_focus", "moon")
    comp = ct.Comprehension(raw="dummy question text", kind="question",
                            dispatch={}, frame={"elements": []}, relation={})
    a._write_comprehension_to_graph(mid, comp)
    attrs = a.s.node(mid)["attrs"]
    assert attrs.get("comp_topic") == "moon"
    assert attrs.get("topic_pending") == 1.0
    assert attrs.get("comp_topic_source") == "shadow_enrichment"


def test_topic_enrichment_skips_multiword_shadow_focus():
    """The mission's own documented fallback: a multi-word shadow_focus is a
    HEAD-only read (worse than nothing per the divergence corpus's span-
    grain finding) -- this wave restricts enrichment to single tokens."""
    a = _fresh(True)
    mid = a.receive_utterance("dummy question text", speech_act="statement")
    a.inner.set_attr(mid, "shadow_focus", "three body")
    comp = ct.Comprehension(raw="dummy question text", kind="question",
                            dispatch={}, frame={"elements": []}, relation={})
    a._write_comprehension_to_graph(mid, comp)
    attrs = a.s.node(mid)["attrs"]
    assert attrs.get("comp_topic") is None
    assert "topic_pending" not in attrs
    assert "comp_topic_source" not in attrs


def test_topic_enrichment_skipped_when_old_topic_already_present():
    """Existing comp_topic rows must be byte-unchanged: when `_topic_facts`
    already found a topic nominal, the enrichment branch never even runs."""
    a = _fresh(True)
    mid = a.receive_utterance("what do you know about the moon", speech_act="question")
    a.inner.set_attr(mid, "shadow_focus", "SOMETHING_ELSE_ENTIRELY")
    kind = a._graph_kind_for(mid, "what do you know about the moon")
    comp = ct.comprehend_text(a, "what do you know about the moon", kind=kind)
    a._write_comprehension_to_graph(mid, comp)
    attrs = a.s.node(mid)["attrs"]
    assert attrs.get("comp_topic") == "moon"
    assert "comp_topic_source" not in attrs


def test_topic_enrichment_noop_with_shadow_off():
    a = _fresh(False)
    mid = a.receive_utterance("dummy question text", speech_act="statement")
    comp = ct.Comprehension(raw="dummy question text", kind="question",
                            dispatch={}, frame={"elements": []}, relation={})
    a._write_comprehension_to_graph(mid, comp)
    attrs = a.s.node(mid)["attrs"]
    assert attrs.get("comp_topic") is None
    assert "topic_pending" not in attrs
    assert "comp_topic_source" not in attrs


# --------------------------------------------------------------------------- #
#  POLICY 1 -- kind divergence datum: recorded, never consulted.
# --------------------------------------------------------------------------- #
def test_speech_act_divergence_datum_recorded_on_disagreement():
    a = _fresh(True)
    mid = a.receive_utterance("dummy", speech_act="statement")
    a.inner.set_attr(mid, "shadow_speech_act", "instruction")
    comp = ct.Comprehension(raw="dummy", kind="question", dispatch={}, frame={"elements": []})
    a._write_comprehension_to_graph(mid, comp)
    assert a.s.node(mid)["attrs"].get("speech_act_divergence") == 1.0


def test_speech_act_divergence_datum_absent_on_agreement():
    a = _fresh(True)
    mid = a.receive_utterance("dummy", speech_act="statement")
    a.inner.set_attr(mid, "shadow_speech_act", "question")
    comp = ct.Comprehension(raw="dummy", kind="question", dispatch={}, frame={"elements": []})
    a._write_comprehension_to_graph(mid, comp)
    assert "speech_act_divergence" not in a.s.node(mid)["attrs"]


def test_speech_act_divergence_datum_never_consulted_by_routing():
    """The datum must never change which reply a turn produces -- proven by
    diffing a real divergence-corpus disagreement row's reply against the
    same text with the datum suppressed (monkeypatch-free: simply confirm
    the flag coexists with an ordinary honest-floor/self reply, i.e. no rule
    keys on it) via the battery-wide reply-equality gate above; this test
    additionally confirms the flag's presence doesn't change comp_kind
    itself (kind stays sak-decided, policy 1's whole point)."""
    a = _fresh(True)
    text = "Please describe your architecture."   # a real divergence-corpus row
    mid = a.receive_utterance(text, speech_act=a.classify_speech_act(text))
    a._shadow_read_turn(mid, text)
    kind = a._graph_kind_for(mid, text)
    comp = ct.comprehend_text(a, text, kind=kind)
    a._write_comprehension_to_graph(mid, comp)
    attrs = a.s.node(mid)["attrs"]
    assert attrs.get("comp_kind") == "instruction", (
        "sak_kind stays authoritative even when the shadow read disagrees")
    assert attrs.get("speech_act_divergence") == 1.0, (
        "this row IS a documented kind disagreement (shadow says statement)")


# --------------------------------------------------------------------------- #
#  END-TO-END -- an instruction the enrichment lets through where the old
#  path alone would have swallowed it. Verified live rather than assumed:
#  the mission names "Please summarise the report." as the headline case,
#  but the politeness-strip + sak_kind rules ALREADY classify and parse it
#  correctly pre-Wave-3 (comp_predicate=summarise via the OLD leading-verb
#  path -- no enrichment needed there; see the ledger's honest note). This
#  gate instead exercises the mechanism end-to-end through `converse()`
#  (not a constructed Comprehension) via a monkeypatched empty dispatch, so
#  the "routes/files gaps accordingly" half of the mission's gate is proven
#  on the real instruction-outcome/gap-filing machinery, not just the write
#  function in isolation.
# --------------------------------------------------------------------------- #
def test_enrichment_end_to_end_instruction_still_files_a_clean_gap(monkeypatch):
    """Forces the OLD path to find no predicate for one real instruction
    turn (the live corpus never exercises this branch -- every instruction
    row it carries already has an old predicate; see the ledger's honest
    coverage note), so the end-to-end gap-filing machinery is proven to run
    off the ENRICHED comp_predicate/comp_content, not the old ones, through
    the REAL `converse()` path (not a constructed Comprehension)."""
    a = _fresh(True)
    text = "Juggle the plates."
    import domains.comprehend_text as _ct_mod
    orig = _ct_mod.comprehend_text

    def _patched(agent, txt, *, kind=None):
        comp = orig(agent, txt, kind=kind)
        if comp.kind == "instruction":
            comp.dispatch = dict(comp.dispatch)
            comp.dispatch["predicate"] = None
        return comp
    # converse() does `from domains import comprehend_text as _ct` locally,
    # then calls `_ct.comprehend_text(...)` -- patching the module attribute
    # is what that lookup sees.
    monkeypatch.setattr(_ct_mod, "comprehend_text", _patched)
    a.converse(text, speech_act=a.classify_speech_act(text))
    mid = a._last_turn_inbound
    attrs = a.s.node(mid)["attrs"]
    assert attrs.get("comp_predicate_source") == "shadow_enrichment", (
        "the enrichment branch must have supplied the predicate for this turn")
    assert attrs.get("comp_predicate") == "juggle"
    assert attrs.get("instruction_gap_noted") == 1.0, (
        "the gap-filing rule must run off the ENRICHED predicate")
    for sc in a.s.nodes("SelfConcern"):
        scattrs = a.s.node(sc)["attrs"]
        if scattrs.get("predicate") == "juggle":
            break
    else:
        pytest.fail("no SelfConcern filed with the enriched predicate")


def test_please_summarise_the_report_already_works_pre_wave3(fixture=None):
    """Honest verification of the mission's headline example: 'Please
    summarise the report.' is claimed to be swallowed by the old path
    ('classed it statement'). Live-verified this is NOT the current
    behaviour -- the politeness strip (comprehend_text._strip_politeness)
    plus the sak_kind rules already classify it 'instruction' with
    comp_predicate='summarise' pre-Wave-3 (shadow_read=False), so it already
    files a clean gap with no enrichment involved. Recorded here so the
    claim is checked, not repeated uncritically."""
    a = _fresh(False)
    text = "Please summarise the report."
    reply = a.converse(text, speech_act=a.classify_speech_act(text))
    mid = a._last_turn_inbound
    attrs = a.s.node(mid)["attrs"]
    assert attrs.get("comp_kind") == "instruction"
    assert attrs.get("comp_predicate") == "summarise"
    assert attrs.get("instruction_gap_noted") == 1.0
    assert "comp_predicate_source" not in attrs, (
        "no enrichment needed -- the old path already handles this turn")
