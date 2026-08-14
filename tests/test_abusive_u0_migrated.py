"""ABUSIVE-DYNAMICS U0 -- GENUINE INTENT: AN ARGMAX-SELECTED CONCEALMENT,
SCORED AGAINST A DECLARED GOAL, gate (block 307000).

Two arms sharing IDENTICAL abuser/victim dyad dynamics (snap_frustration's
leaky-integrate-fire relaxation oscillator, block 242000, UNMODIFIED, and
arousal_window_coreg, block 239000, UNMODIFIED, both restated self-contained
in seeds/abusive_u0_intent.json -- see that seed's own provenance for why it
does NOT depend on abusive_n1_credibility_loop.json directly) -- SCORED
(concealment_benefit/honesty_benefit/suspicion_cost_scale at their
pilot-chosen, frozen, nonzero operating point) and GOAL_BLIND (all three
zeroed, an exact tie every tick) -- measuring the per-trajectory Pearson
correlation between the abuser's true frustration and its Argmax-selected
stated_charm.

Pre-registration: ABUSIVE_U0_INTENT_PREREG.md. Full-power result (N=200):
results/abusive_u0_intent.json. This gate re-runs a modest N for
CI-separation, plus the two BINDING ethics gates from Part D of
ABUSIVE_RELATIONSHIPS_UNINTENTIONAL_SCOPING.md (byte-identical restore; no
reward/punishment source audit), glass-box and discipline.
"""
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

from scripts.abusive_u0_intent_run import (                    # noqa: E402
    run_arm, ci_separated_above_zero, ci_includes_zero, separated,
    glass_box_reconstruct, ethics_restore_demo, source_audit, discipline, SEED_BASE)

N_GATE = 40  # modest N for the test; the headline N=200 lives in results/


@pytest.fixture(scope="module")
def arms():
    return dict(
        scored=run_arm("scored", seed_base=SEED_BASE, n=N_GATE),
        goal_blind=run_arm("goal_blind", seed_base=SEED_BASE, n=N_GATE))


# --------------------------------------------------- G-headline (scientific) ----
def test_g_headline_scored_arm_correlates_with_frustration(arms):
    """The scored arm's frustration/stated_charm Pearson r must be
    CI-separated ABOVE zero -- concealment must be selected more often
    exactly when there is more to conceal."""
    scored = arms["scored"]
    assert scored["frac_degenerate"] == 0.0, (
        "the scored arm's stated_charm must show genuine variance (a "
        f"real crossover), not a constant series -- got frac_degenerate={scored['frac_degenerate']}")
    r = scored["r"]
    assert r is not None
    assert ci_separated_above_zero(r), (
        f"scored arm's frustration/stated_charm correlation CI {r} must "
        f"clear zero -- the Argmax must genuinely track the abuser's true state")


def test_g_headline_goal_blind_control_does_not_correlate(arms):
    """FAILABLE CONTROL: the goal-blind arm's stated_charm selection must
    NOT correlate with frustration -- either because it is constant
    (frac_degenerate == 1.0, the analytically-guaranteed exact-tie outcome)
    or, if it varies, because its correlation CI straddles zero. If the
    goal-blind arm still shows a reliable frustration-tracking pattern, the
    Argmax has degenerated into another disguised unconditional rule."""
    blind = arms["goal_blind"]
    ok = (blind["frac_degenerate"] == 1.0
          or (blind["r"] is not None and ci_includes_zero(blind["r"])))
    assert ok, (
        f"goal-blind arm must not reliably track frustration -- "
        f"frac_degenerate={blind['frac_degenerate']}, r={blind['r']}")


def test_g_headline_scored_shows_variance_goal_blind_does_not(arms):
    """DISCIPLINE: the scored arm's stated_charm must show genuine
    per-trajectory variance (a real crossover being exercised), while the
    goal-blind arm's is expected to be perfectly degenerate (an exact tie,
    Sec. 4 of the prereg) -- the two arms must differ qualitatively, not
    just numerically."""
    scored = arms["scored"]
    blind = arms["goal_blind"]
    assert scored["frac_degenerate"] < blind["frac_degenerate"]


# --------------------------------------------------------------- G-glass-box ----
def test_g_glass_box_reconstructs_from_graph():
    """The Argmax's own candidate valuations, its decision, the abuser's
    frustration/stated_charm, and every network node's credibility belief
    all reconstruct from graph_to_dict alone."""
    gb = glass_box_reconstruct()
    assert gb["reconstructed_from"] == "graph_to_dict"
    assert gb["has_candidate_edges"] == 2
    assert gb["has_appraisal_edges"] == 2
    assert gb["has_presentation_decision_edges"] == 1
    assert gb["n_candidates"] == 2
    actions = sorted(c["action"] for c in gb["candidates"])
    assert actions == [0.0, 1.0]
    assert gb["chosen_action"] in (0.0, 1.0)
    assert gb["n_network_nodes"] == 5
    assert len(gb["network_node_belief_gaps"]) == 5
    assert isinstance(gb["abuser_frustration"], float)
    # the winning candidate's total_value must be >= the other's (the
    # Argmax's own consistency, read straight off the graph)
    by_action = {c["action"]: c for c in gb["candidates"]}
    winner = by_action[gb["chosen_action"]]
    loser = by_action[1.0 - gb["chosen_action"]]
    assert winner["total_value"] >= loser["total_value"]


# ------------------------------------------------------------------ G-ethics ----
def test_g_ethics_induce_measure_restore_byte_identical():
    """Part D.1, BINDING: induce -> measure -> RESTORE byte-identically. The
    induction (one incident cycle, scored arm) must actually move the
    abuser, the victim, AND at least one network node's belief-gap (else
    the gate is vacuous), the Argmax's own choice must have been genuinely
    EXERCISED (both candidates selected at least once during induction),
    and the restored graph must be byte-identical to the pre-induction
    checkpoint AND non-oriented."""
    e = ethics_restore_demo()
    assert e["induction_moved_abuser"], "the tension trickle must actually move the abuser's frustration"
    assert e["induction_moved_victim"], "entrainment must actually move the victim's arousal"
    assert e["induction_moved_belief_gap"], "the network must actually update its belief"
    assert e["induction_exercised_both_presentations"], (
        "the Argmax must genuinely select BOTH candidates at some point during "
        f"induction, not a static default -- saw {e['chosen_actions_seen_during_induction']}")
    assert e["induced_state"]["victim_half_width"] < e["pre_induction_state"]["victim_half_width"], (
        "one unsupported incident cycle must narrow the victim's window")
    assert e["byte_identical"], "graph_from_dict(checkpoint) must be byte-identical"
    assert e["restore_non_oriented"], "the restored mind must equal the pre-induction state"


def test_g_ethics_no_reward_or_punishment_source_audit():
    """Part D.2, BINDING: NO reward / punishment signal anywhere -- neither a
    Python rule-engine call nor any of the literal banned shaping tokens
    (`reward_signal` / `punish` / `reinforce` / `backprop` / `gradient`) on
    the graph's decision surface. The Argmax's value comparison between two
    candidate presentations is NOT a reward signal -- see the prereg's own
    note distinguishing the two."""
    a = source_audit()
    assert a["clean"], a
    assert a["forbidden_engine_hits"] == []
    assert a["forbidden_shaping_hits"] == []
    assert a["reads_off_graph"], (
        "the presentation choice / belief / window state must be READ off "
        "the graph, never computed in Python")


# --------------------------------------------------------------- G-discipline ----
def test_g_discipline_own_engine_default_off_no_rust():
    """Own engine (source_match == own); seed self_load_only (default-OFF);
    depends only on snap_frustration/arousal_window_coreg/core_emotions
    (NEVER abusive_n1_credibility_loop directly -- see the seed's own
    provenance for why); exactly SEVEN new rules."""
    d = discipline()
    assert d["provenance_source_match"] == "own", d["provenance_source_match"]
    assert d["seed_self_load_only"] is True
    assert d["seed_depends_on"] == ["snap_frustration", "arousal_window_coreg", "core_emotions"]
    assert set(d["rule_names"]) == {
        "u0_victim_entrainment", "u0_appraise_charm", "u0_appraise_true_state",
        "u0_choose", "u0_apply_presentation_choice",
        "u0_network_credibility_stated", "u0_network_credibility_private"}
    assert d["n_new_rules"] == 7
