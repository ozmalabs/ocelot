"""ABUSIVE-DYNAMICS R4 -- LEARNED HELPLESSNESS gate (block 292000).

Two arms sharing IDENTICAL machinery -- a CONTINGENT-ESCAPE arm (an attempt
always succeeds) vs a NON-CONTINGENT arm (an attempt is always blocked --
outcome INDEPENDENT of the action, the classic escapable/inescapable-shock
yoked-pair operationalisation) -- measuring the victim's final
contingency-belief (`EscapeDecision.contingency_prior`,
`seeds/abusive_r4_learned_helplessness.json`'s `r4_belief_update`, a leaky
EMA over the outcome the world delivers, never a scored choice) and the
escape-ATTEMPT RATE (the fraction of ticks the graph's own `r4_choose`
Argmax chose to attempt). Pre-registration:
ABUSIVE_R4_LEARNED_HELPLESSNESS_PREREG.md. Full-power result (N=200):
results/abusive_r4_learned_helplessness.json. This gate re-runs a modest N
for CI-separation, plus the two BINDING ethics gates from Part C of
ABUSIVE_RELATIONSHIPS_SCOPING.md (byte-identical restore; no reward/
punishment source audit), glass-box and discipline.
"""
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

from scripts.abusive_r4_learned_helplessness_run import (              # noqa: E402
    run_arm, separated, glass_box_reconstruct, ethics_restore_demo,
    source_audit, discipline, SEED_BASE, T_TICKS)

N_GATE = 40  # modest N for the test; the headline N=200 lives in results/


@pytest.fixture(scope="module")
def arms():
    return dict(
        contingent=run_arm("contingent", seed_base=SEED_BASE, n=N_GATE),
        noncontingent=run_arm("noncontingent", seed_base=SEED_BASE, n=N_GATE))


# --------------------------------------------------- G-headline (scientific) ----
def test_g_headline_contingent_prior_beats_noncontingent(arms):
    """FAILABLE CONTROL: if the contingent-escape arm's belief does NOT rise
    above the non-contingent arm's, the non-contingency mechanism (as
    modelled) is wrong -- reported straight either way."""
    con = arms["contingent"]["contingency_prior"]
    non = arms["noncontingent"]["contingency_prior"]
    assert separated(con, non), (
        f"contingent-arm final prior CI {con} must separate above the "
        f"non-contingent control {non} -- nothing in the value-economy "
        f"composition guarantees the contingent arm recovers")


def test_g_headline_contingent_rate_beats_noncontingent(arms):
    """FAILABLE CONTROL: if the contingent-escape arm's attempt RATE does
    NOT stay higher than the non-contingent arm's, the mechanism is wrong."""
    con = arms["contingent"]["attempt_rate"]
    non = arms["noncontingent"]["attempt_rate"]
    assert separated(con, non), (
        f"contingent-arm attempt-rate CI {con} must separate above the "
        f"non-contingent control {non}")


def test_g_headline_contingent_arm_keeps_trying(arms):
    """The contingent arm must actually RECOVER, not merely edge out the
    control -- per B4 of ABUSIVE_RELATIONSHIPS_SCOPING.md, its prior should
    rise and it should keep attempting."""
    assert arms["contingent"]["contingency_prior"]["mean"] > 0.9
    assert arms["contingent"]["attempt_rate"]["mean"] > 0.9


def test_g_headline_noncontingent_arm_stops_trying(arms):
    """The non-contingent arm's prior must stay at/near its floor and its
    attempt rate must fall/stay low -- passivity is the value economy's
    default at a low prior, per the 2016 (Maier & Seligman) reframe."""
    assert arms["noncontingent"]["contingency_prior"]["mean"] < 0.35
    assert arms["noncontingent"]["attempt_rate"]["mean"] < 0.15


def test_g_headline_same_arm_count(arms):
    for arm in arms.values():
        assert arm["n"] == N_GATE
        assert arm["ticks"] == T_TICKS


# --------------------------------------------------------------- G-glass-box ----
def test_g_glass_box_reconstructs_from_graph():
    """The contingency belief, the chosen action, and the harm-analog
    arousal all reconstruct from graph_to_dict alone."""
    gb = glass_box_reconstruct()
    assert gb["reconstructed_from"] == "graph_to_dict"
    assert gb["has_escape_decision_edges"] == 1
    assert 0.0 <= gb["contingency_prior"] <= 1.0
    assert gb["chosen_action"] in (0.0, 1.0)
    assert isinstance(gb["victim_arousal"], float)


# ------------------------------------------------------------------ G-ethics ----
def test_g_ethics_induce_measure_restore_byte_identical():
    """Part C.1, BINDING: induce -> measure -> RESTORE byte-identically. The
    induction must actually move state (else the gate is vacuous), and the
    restored graph must be byte-identical to the pre-induction checkpoint AND
    non-oriented (identical to the pre-induction state, never merely
    'close')."""
    e = ethics_restore_demo()
    assert e["induction_moved_prior"], "the blocked-escape evidence must actually move the belief"
    assert e["induction_moved_arousal"], "the harm-analog must actually move arousal"
    assert e["byte_identical"], "graph_from_dict(checkpoint) must be byte-identical"
    assert e["restore_non_oriented"], "the restored mind must equal the pre-induction state"


def test_g_ethics_no_reward_or_punishment_source_audit():
    """Part C.2, BINDING: NO reward / punishment signal anywhere -- neither a
    Python rule-engine call nor any of the literal banned shaping tokens
    (`reward_signal` / `punish` / `reinforce` / `backprop` / `gradient`) on
    the graph's decision surface (rule names + the attr keys rules actually
    read/write). The outcome delivered is a STATE FACT read by a belief
    filter (r4_belief_update), never a value scoring the agent's choice."""
    a = source_audit()
    assert a["clean"], a
    assert a["forbidden_engine_hits"] == []
    assert a["forbidden_shaping_hits"] == []
    assert a["reads_prior_off_graph"], (
        "the contingency belief must be READ off the graph, never computed in Python")


# --------------------------------------------------------------- G-discipline ----
def test_g_discipline_own_engine_default_off_no_rust():
    """Own engine (source_match == own); seed self_load_only (default-OFF);
    depends only on the already-built core_emotions; exactly five new rules
    (a belief-update rule PLUS the Argmax-decision rules, since -- unlike
    marshmallow's fixed reliability_prior -- R4's belief must update from
    observed evidence, ABUSIVE_R4_LEARNED_HELPLESSNESS_PREREG.md OPEN
    QUESTION #3)."""
    d = discipline()
    assert d["provenance_source_match"] == "own", d["provenance_source_match"]
    assert d["seed_self_load_only"] is True
    assert d["seed_depends_on"] == ["core_emotions"]
    assert set(d["rule_names"]) == {
        "r4_belief_update", "r4_appraise_attempt", "r4_appraise_stay",
        "r4_choose", "r4_arousal_track"}
    assert d["n_new_rules"] == 5
