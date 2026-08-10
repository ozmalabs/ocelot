"""test_shadow_read_migrated — Deep-Reader Wave 2 Task 2: the SHADOW READ
gateway in `WorldAdapter.converse()` (`substrate/world_adapter.py::
_shadow_read_turn`).

Every chat turn CAN now get a light deep-read of its own text on the live
substrate: `coref_entities.arm_deictic_centre` from the turn's own provenance
(the Message's `sent_by` Interlocutor is the speaker, the agent's own
`substrate_name` is the addressee), then `reading_drive.run_reading_flow`
under the `conversational` register's APERTURE (Wave 2 Task 1 —
`stages=['spine']` only), linked back via `Message -comprehended_as->
SentenceParse`, with the flow's own outputs recorded onto the Message as
`shadow_speech_act` / `shadow_focus` / `shadow_predicate` / `shadow_latency_ms`.

This is PURELY ADDITIVE and OPT-IN (`WorldAdapter(shadow_read=True)` or
`OZMA_SHADOW_READ=1`, default OFF): `comp_*` stays authoritative for the
reply, so `converse()`'s return value must be byte-identical whether the
shadow read runs or not — that is this gate's headline proof, the
no-behaviour-change contract Wave 3's cutover depends on.
"""
from __future__ import annotations

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
from domains import coref_entities as ce                               # noqa: E402


# A representative battery spanning the kinds the mission's own conversation
# gates exercise (question / instruction-request / statement / greeting) —
# NO teacher attached, so no network grounding fires either side (an honest,
# deterministic reply comparison).
_BATTERY = [
    ("What do you know about the moon?", "question"),
    ("What are you?", "question"),
    ("How do you learn?", "question"),
    ("Summarise the report.", "request"),
    ("Fix your grammar.", "request"),
    ("the sky is blue", "statement"),
    ("hello", "greeting"),
    ("What is the moon made of?", "question"),
]


@pytest.fixture(scope="module", autouse=True)
def _warm():
    dl.warm_wordnet("en")


def _fresh(shadow_read):
    a = WorldAdapter(seeds=(), shadow_read=shadow_read)
    load_all_seeds(a)
    return a


# --------------------------------------------------------------------------- #
#  NO-BEHAVIOUR-CHANGE — the headline proof.
# --------------------------------------------------------------------------- #
def test_shadow_on_replies_byte_identical_to_shadow_off():
    off = _fresh(False)
    on = _fresh(True)
    for text, sa in _BATTERY:
        r_off = off.converse(text, speech_act=sa)
        r_on = on.converse(text, speech_act=sa)
        assert r_off == r_on, (
            "shadow_read=True changed converse()'s reply for %r:\n  off=%r\n  on=%r"
            % (text, r_off, r_on))


def test_shadow_read_defaults_off():
    a = WorldAdapter(seeds=())
    assert a.shadow_read is False, "shadow_read must default OFF (bench discipline)"


def test_shadow_read_env_var_turns_it_on(monkeypatch):
    monkeypatch.setenv("OZMA_SHADOW_READ", "1")
    a = WorldAdapter(seeds=())
    assert a.shadow_read is True
    monkeypatch.setenv("OZMA_SHADOW_READ", "0")
    a2 = WorldAdapter(seeds=())
    assert a2.shadow_read is False


def test_explicit_kwarg_wins_over_env_var(monkeypatch):
    monkeypatch.setenv("OZMA_SHADOW_READ", "1")
    a = WorldAdapter(seeds=(), shadow_read=False)
    assert a.shadow_read is False


# --------------------------------------------------------------------------- #
#  RECORDED ON THE MESSAGE — the shadow outputs + the comprehended_as link.
# --------------------------------------------------------------------------- #
def test_message_carries_shadow_attrs_and_comprehended_as_link():
    a = _fresh(True)
    a.converse("What do you know about the moon?", speech_act="question")
    mid = a._last_turn_inbound
    attrs = a.s.node(mid)["attrs"]
    assert attrs.get("shadow_error") is None, "shadow read raised: %r" % attrs
    assert attrs.get("shadow_speech_act") == "question"
    assert attrs.get("shadow_focus") == "moon"
    assert attrs.get("shadow_predicate"), "no shadow_predicate recorded"
    assert isinstance(attrs.get("shadow_latency_ms"), float)

    linked = list(a.inner.neighbours(mid, "comprehended_as"))
    assert linked, "Message -comprehended_as-> SentenceParse link missing"
    for spn in linked:
        sp_at = a.s.node(spn)["attrs"]
        assert sp_at.get("sentence"), "linked SentenceParse carries no sentence"


def test_instruction_turn_shadow_speech_act():
    a = _fresh(True)
    a.converse("Fix your grammar.", speech_act="request")
    mid = a._last_turn_inbound
    attrs = a.s.node(mid)["attrs"]
    assert attrs.get("shadow_speech_act") == "instruction"


def test_shadow_read_off_records_nothing():
    a = _fresh(False)
    a.converse("What do you know about the moon?", speech_act="question")
    mid = a._last_turn_inbound
    attrs = a.s.node(mid)["attrs"]
    for k in ("shadow_speech_act", "shadow_focus", "shadow_predicate",
             "shadow_latency_ms", "shadow_error"):
        assert k not in attrs, "%r must not be written when shadow_read is off" % k
    assert list(a.inner.neighbours(mid, "comprehended_as")) == []


# --------------------------------------------------------------------------- #
#  DEIXIS — 'you' resolves to the agent-side entity in THIS turn's own flow.
# --------------------------------------------------------------------------- #
def test_deictic_armed_you_resolves_to_the_agent_in_this_turn():
    a = _fresh(True)
    a.converse("What do you know about the moon?", speech_act="question")
    sub, _native = ce._resolve(a)
    nid = ce._deictic_node(a, create=False)
    assert nid is not None, "arm_deictic_centre never ran"
    at = sub.node(nid)["attrs"]
    expected_addressee = sub.node(a.agent)["attrs"].get("substrate_name") or "jabberwock"
    assert at.get("addressee") == expected_addressee
    assert at.get("speaker") == "user"


# --------------------------------------------------------------------------- #
#  COST — steady-state per-turn SHADOW-READ latency is bounded. Measured off
#  the `shadow_latency_ms` attr `_shadow_read_turn` itself records (the
#  shadow read's OWN cost — arm + run_reading_flow + read_clause), NOT
#  `converse()`'s whole wall-clock (which is dominated by the pre-existing
#  front end: comprehend_text + the rule-tick passes + `_dispatch_pending_io`
#  — none of that is what Wave 2 Task 2 adds or is being measured here).
# --------------------------------------------------------------------------- #
def test_steady_state_shadow_latency_is_bounded():
    a = _fresh(True)
    a.converse("What do you know about the moon?", speech_act="question")  # pay first-call cost
    latencies = []
    for i in range(6):
        a.converse("Tell me a fact about topic number %d." % i, speech_act="statement")
        mid = a._last_turn_inbound
        latencies.append(a.s.node(mid)["attrs"].get("shadow_latency_ms"))
    avg = sum(latencies) / len(latencies)
    # Median, not mean, and a loose ceiling: this is a wall-clock probe on a
    # shared machine (concurrent cargo builds/benches routinely double it) —
    # the gate exists to catch pathological regressions (seconds per turn),
    # not to pin the ~40-250ms healthy range.
    med = sorted(latencies)[len(latencies) // 2]
    print("\nsteady-state shadow_latency_ms: avg=%.1fms med=%.1fms max=%.1fms"
         % (avg, med, max(latencies)))
    assert med < 1000.0, "steady-state shadow-read latency pathological: %.1fms median" % med


# --------------------------------------------------------------------------- #
#  DIVERGENCE CAPTURE — runs the harness in-process, checks the summary rates
#  land (the actual per-field agreement TABLE is reported by the caller from
#  `tests/fixtures/comprehension_divergence/divergence.json`, not gated here
#  to a specific floor — Wave 3 reads the numbers, this only proves the
#  harness itself runs clean end-to-end and produces a well-formed summary).
# --------------------------------------------------------------------------- #
def test_divergence_capture_runs_and_writes_summary_rates():
    import importlib.util
    path = os.path.join(ROOT, "tests", "fixtures", "comprehension_divergence", "capture.py")
    spec = importlib.util.spec_from_file_location("comprehension_divergence_capture", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    rc = mod.main()
    assert rc == 0

    out_path = os.path.join(ROOT, "tests", "fixtures", "comprehension_divergence",
                            "divergence.json")
    import json
    with open(out_path) as f:
        data = json.load(f)
    summary = data["summary"]
    assert summary["n_utterances"] > 100
    assert summary["n_speech_act_parity"] == 133
    for field in ("kind", "predicate", "topic"):
        assert summary[field]["total"] == summary["n_utterances"]
        assert summary[field]["rate"] is not None
    assert summary["shadow_errors"] == 0, (
        "the shadow read must never raise on the real divergence corpus")
