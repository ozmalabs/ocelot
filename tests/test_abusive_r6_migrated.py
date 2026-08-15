"""ABUSIVE-DYNAMICS R6 -- DEPENDENT/RESOURCE-COST DEVALUATION gate (block 361000).

Two arms sharing IDENTICAL machinery AND identical (deterministic,
always-succeeds) escape contingency -- a ZERO-DEPENDENTS arm
(`dependent_cost=0.0`, the harness-neutrality replication of R4's own
contingent arm) vs a HIGH-DEPENDENTS arm (`dependent_cost=10.0`, large
enough that `escape_value - attempt_cost - dependent_cost < 0` even at
`contingency_prior=1.0`) -- measuring the victim's final contingency-belief
(`EscapeDecision.contingency_prior`, R4's own UNMODIFIED `r4_belief_update`)
and the escape-ATTEMPT RATE (the fraction of ticks the graph's own
`r4_choose` Argmax, UNMODIFIED, chose to attempt). Pre-registration:
ABUSIVE_R6_DEPENDENT_COST_PREREG.md. Full-power result (N=200):
results/abusive_r6_dependent_cost.json. This gate re-runs a modest N for
CI-separation, plus the harness-neutrality check, the two BINDING ethics
gates from Part D of ABUSIVE_RELATIONSHIPS_BARRIERS_AND_RETURN_SCOPING.md
(byte-identical restore; no reward/punishment source audit), glass-box and
discipline.
"""
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

from scripts.abusive_r6_dependent_cost_run import (                    # noqa: E402
    run_arm, separated_below, glass_box_reconstruct, ethics_restore_demo,
    source_audit, discipline, SEED_BASE, T_TICKS,
    R4_CONTINGENT_RATE_MEAN, R4_CONTINGENT_PRIOR_MEAN, P0_MEAN, P0_JITTER)

N_GATE = 40  # modest N for the test; the headline N=200 lives in results/


@pytest.fixture(scope="module")
def arms():
    return dict(
        zero_dependents=run_arm("zero_dependents", seed_base=SEED_BASE, n=N_GATE),
        high_dependents=run_arm("high_dependents", seed_base=SEED_BASE, n=N_GATE))


# ------------------------------------------------- G-harness-neutrality ----
def test_g_harness_neutrality_zero_dependents_replicates_r4_contingent(arms):
    """Genuinely failable: at dependent_cost=0, R6's new rule must be a
    numerical no-op, reproducing R4's own landed contingent-arm numbers
    (attempt_rate exactly 1.000, prior > 0.999) -- if R6's composition
    perturbs the baseline even here, that is a composition bug."""
    z = arms["zero_dependents"]
    assert z["attempt_rate"]["mean"] == R4_CONTINGENT_RATE_MEAN
    assert z["contingency_prior"]["mean"] > 0.999
    assert z["contingency_prior"]["mean"] == pytest.approx(R4_CONTINGENT_PRIOR_MEAN, abs=1e-6)


# --------------------------------------------------- G-headline (scientific) ----
def test_g_headline_high_dependents_attempt_rate_below_zero_dependents(arms):
    """FAILABLE CONTROL: HIGH-DEPENDENTS' attempt rate must be CI-separated
    BELOW ZERO-DEPENDENTS', despite escape being EQUALLY, PROVABLY
    contingent in both arms -- if dependent_cost were too small relative to
    escape_value, both arms would attempt identically and the claim that
    material barriers can override even a proven-working escape route would
    be wrong."""
    z = arms["zero_dependents"]["attempt_rate"]
    h = arms["high_dependents"]["attempt_rate"]
    assert separated_below(h, z), (
        f"high-dependents attempt-rate CI {h} must separate below the "
        f"zero-dependents control {z}")


def test_g_headline_high_dependents_never_attempts(arms):
    """The predicted closed-form result (ABUSIVE_R6_DEPENDENT_COST_PREREG.md
    Sec. 3): dependent_cost=10.0 makes the attempt candidate's value
    negative for EVERY possible contingency_prior in [0, 1], so the agent
    never attempts even once."""
    assert arms["high_dependents"]["attempt_rate"]["mean"] == 0.0


def test_g_headline_dissociation_belief_undisturbed_not_suppressed(arms):
    """The rung's own headline finding: because no attempt is ever made, no
    outcome is ever delivered, so r4_belief_update's guard never fires and
    contingency_prior never moves off its initial, genuinely uninformative
    value (~P0_MEAN) -- qualitatively distinct from R4's own non-contingent
    trap, where the belief is actively driven DOWN by disconfirming
    evidence before the agent freezes. Belief and value are separate axes:
    it is possible to be entirely undisturbed about the first while the
    second still says stay."""
    prior_mean = arms["high_dependents"]["contingency_prior"]["mean"]
    assert abs(prior_mean - P0_MEAN) < 3 * P0_JITTER, (
        f"high-dependents final prior {prior_mean} should remain near the "
        f"undisturbed initial belief {P0_MEAN}, never having received any "
        f"evidence")
    # And distinct from R4's own actively-suppressed non-contingent trap
    # value (~0.256, landed in ABUSIVE_R4_LEARNED_HELPLESSNESS_RESULTS.md).
    assert prior_mean > 0.35


def test_g_headline_same_arm_count(arms):
    for arm in arms.values():
        assert arm["n"] == N_GATE
        assert arm["ticks"] == T_TICKS


# --------------------------------------------------------------- G-glass-box ----
def test_g_glass_box_reconstructs_from_graph():
    """The contingency belief, the chosen action, the dependent_cost
    constant, and the harm-analog arousal all reconstruct from
    graph_to_dict alone."""
    gb = glass_box_reconstruct()
    assert gb["reconstructed_from"] == "graph_to_dict"
    assert gb["has_escape_decision_edges"] == 1
    assert 0.0 <= gb["contingency_prior"] <= 1.0
    assert gb["chosen_action"] in (0.0, 1.0)
    assert gb["dependent_cost"] == 0.0
    assert isinstance(gb["victim_arousal"], float)


# ------------------------------------------------------------------ G-ethics ----
def test_g_ethics_induce_measure_restore_byte_identical():
    """Part D.1, BINDING: induce (the ZERO-DEPENDENTS arm, per
    ABUSIVE_R6_DEPENDENT_COST_PREREG.md Sec. 4's disclosed reasoning) ->
    measure -> RESTORE byte-identically. The induction must actually move
    state (else the gate is vacuous), and the restored graph must be
    byte-identical to the pre-induction checkpoint AND non-oriented
    (identical to the pre-induction state, never merely 'close')."""
    e = ethics_restore_demo()
    assert e["induction_moved_prior"], "the delivered escape outcomes must actually move the belief"
    assert e["induction_moved_arousal"], "the harm-analog must actually move arousal"
    assert e["byte_identical"], "graph_from_dict(checkpoint) must be byte-identical"
    assert e["restore_non_oriented"], "the restored mind must equal the pre-induction state"


def test_g_ethics_no_reward_or_punishment_source_audit():
    """Part D.2, BINDING: NO reward / punishment signal anywhere -- neither
    a Python rule-engine call nor any of the literal banned shaping tokens
    (`reward_signal` / `punish` / `reinforce` / `backprop` / `gradient`) on
    the graph's decision surface (rule names + the attr keys rules actually
    read/write). `dependent_cost` is a structural FACT about material
    circumstances, exactly like R4's own `attempt_cost`, never a value
    scoring the agent's choice."""
    a = source_audit()
    assert a["clean"], a
    assert a["forbidden_engine_hits"] == []
    assert a["forbidden_shaping_hits"] == []
    assert a["reads_prior_off_graph"], (
        "the contingency belief must be READ off the graph, never computed in Python")


# --------------------------------------------------------------- G-discipline ----
def test_g_discipline_own_engine_default_off_no_rust():
    """Own engine (source_match == own); seed self_load_only (default-OFF);
    depends only on abusive_r4_learned_helplessness (R4's own file, never
    edited); exactly ONE new rule -- the minimal composition B1's own design
    settled on."""
    d = discipline()
    assert d["provenance_source_match"] == "own", d["provenance_source_match"]
    assert d["seed_self_load_only"] is True
    assert d["seed_depends_on"] == ["abusive_r4_learned_helplessness"]
    assert set(d["rule_names"]) == {"r6_appraise_attempt_dependent"}
    assert d["n_new_rules"] == 1
