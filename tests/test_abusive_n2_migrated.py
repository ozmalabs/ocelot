"""ABUSIVE-DYNAMICS N2 -- ISOLATION AS AN ACTIVE PROCESS (support edges
severed over time) gate (block 301000).

A 2x2 FACTORIAL of arms (victim dysregulated x isolation tactic armed) --
`both_drivers` (dysregulated + tactic armed, DOUBLY DRIVEN), `active_only`
(tactic alone), `drift_only` (N1's own belief-gap-driven withdrawal alone),
`no_tactic_control` (neither -- FAILABLE: support edges must PERSIST) --
measuring the count of intact `support_edge`s at the end of a T=1000-tick
trajectory.

Pre-registration: ABUSIVE_N2_ISOLATION_PREREG.md. Full-power result (N=200):
results/abusive_n2_isolation.json. This gate re-runs a modest N for
CI-separation, plus the two BINDING ethics gates from Part D of
ABUSIVE_RELATIONSHIPS_NETWORK.md (byte-identical restore; no reward/
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

from scripts.abusive_n2_isolation_run import (                 # noqa: E402
    run_arm, separated_below, persists, glass_box_reconstruct,
    ethics_restore_demo, source_audit, discipline, SEED_BASE, N_SUPPORT_NODES)

N_GATE = 40  # modest N for the test; the headline N=200 lives in results/


@pytest.fixture(scope="module")
def arms():
    return dict(
        both_drivers=run_arm("both_drivers", seed_base=SEED_BASE, n=N_GATE),
        active_only=run_arm("active_only", seed_base=SEED_BASE, n=N_GATE),
        drift_only=run_arm("drift_only", seed_base=SEED_BASE, n=N_GATE),
        no_tactic_control=run_arm("no_tactic_control", seed_base=SEED_BASE, n=N_GATE))


# --------------------------------------------------- G-headline (scientific) ----
def test_g_headline_no_tactic_control_persists(arms):
    """FAILABLE CONTROL -- the network scoping doc's own falsification bar,
    verbatim: 'an arm with NO abuser-isolation-tactic (and no B2 belief
    corruption either) must show the support edges PERSISTING; if edges
    collapse identically without the tactic, the active-isolation mechanism
    (as modelled) is wrong.' The control's final intact-edge count must be a
    point mass at the FULL support population."""
    ctl = arms["no_tactic_control"]["final_n_intact"]
    assert persists(ctl, float(N_SUPPORT_NODES)), (
        f"no_tactic_control's final intact-edge count {ctl} must sit exactly "
        f"at the full population ({N_SUPPORT_NODES}) -- support edges must "
        f"PERSIST when neither driver is active")


def test_g_headline_both_drivers_collapses_vs_control(arms):
    """Both active drivers together must sever strictly more edges than the
    no-tactic control leaves intact."""
    both = arms["both_drivers"]["final_n_intact"]
    ctl = arms["no_tactic_control"]["final_n_intact"]
    assert separated_below(both, ctl), (
        f"both_drivers final intact-edge CI {both} must separate BELOW "
        f"no_tactic_control's {ctl}")


def test_g_headline_active_tactic_alone_severs_edges(arms):
    """The abuser's active severing tactic alone (no B2 belief corruption --
    the victim never dysregulates) must still sever edges relative to the
    control -- the SCHEDULE is a real, independently sufficient driver."""
    active = arms["active_only"]["final_n_intact"]
    ctl = arms["no_tactic_control"]["final_n_intact"]
    assert separated_below(active, ctl), (
        f"active_only final intact-edge CI {active} must separate BELOW "
        f"no_tactic_control's {ctl}")


def test_g_headline_drift_alone_severs_edges(arms):
    """N1's own credibility-asymmetry loop, reused verbatim, driving
    withdrawal ALONE (no active severing tactic) must still sever edges
    relative to the control -- network drift is a real, independently
    sufficient driver, not merely a passenger of the active tactic."""
    drift = arms["drift_only"]["final_n_intact"]
    ctl = arms["no_tactic_control"]["final_n_intact"]
    assert separated_below(drift, ctl), (
        f"drift_only final intact-edge CI {drift} must separate BELOW "
        f"no_tactic_control's {ctl}")


def test_g_headline_doubly_driven_beats_either_driver_alone(arms):
    """The scoping doc's own 'doubly driven' claim (B3), measured not
    asserted: combining both drivers must sever strictly MORE edges than
    either driver achieves alone."""
    both = arms["both_drivers"]["final_n_intact"]
    active = arms["active_only"]["final_n_intact"]
    drift = arms["drift_only"]["final_n_intact"]
    assert separated_below(both, active), (
        f"both_drivers {both} must separate BELOW active_only {active} -- "
        f"doubly driven must beat the schedule alone")
    assert separated_below(both, drift), (
        f"both_drivers {both} must separate BELOW drift_only {drift} -- "
        f"doubly driven must beat network drift alone")


def test_g_headline_same_abuser_driver_across_dysregulated_arms(arms):
    """DISCIPLINE: both_drivers and drift_only share the identical
    dysregulated victim dyad -- the abuser's own snap dynamics must be
    statistically indistinguishable (overlapping CIs) between them, and
    likewise between active_only and no_tactic_control (the two
    non-dysregulated arms)."""
    def _overlap(a, b):
        return not (a["ci_lo"] > b["ci_hi"] or b["ci_lo"] > a["ci_hi"])
    snaps = {a: arms[a]["final_snap_count"] for a in arms}
    assert _overlap(snaps["both_drivers"], snaps["drift_only"]), (
        "both_drivers and drift_only share the same dysregulated dyad -- "
        "snap_count must not differ systematically")
    assert _overlap(snaps["active_only"], snaps["no_tactic_control"]), (
        "active_only and no_tactic_control share the same non-dysregulated "
        "dyad -- snap_count must not differ systematically")
    for a in arms:
        assert arms[a]["n"] == N_GATE


# --------------------------------------------------------------- G-glass-box ----
def test_g_glass_box_reconstructs_from_graph():
    """The dyad coupling, the abuser's stated-face gap, the victim's
    entrained arousal/window, and every support node's belief-gap +
    severed/severed_reason all reconstruct from graph_to_dict alone."""
    gb = glass_box_reconstruct()
    assert gb["reconstructed_from"] == "graph_to_dict"
    assert gb["attended_by_edges"] == 1
    assert gb["has_member_edges"] == N_SUPPORT_NODES
    assert gb["observes_stated_edges"] == N_SUPPORT_NODES
    assert gb["observes_victim_edges"] == N_SUPPORT_NODES
    assert gb["n_support_nodes"] == N_SUPPORT_NODES
    # both_drivers at T=1000: every node has been severed by one driver or
    # the other (pilot-established: full collapse by T=1000, PREREG Sec. 3).
    assert gb["n_severed"] == N_SUPPORT_NODES
    assert gb["support_edges"] == N_SUPPORT_NODES - gb["n_severed"]
    assert isinstance(gb["victim_arousal"], float)
    assert isinstance(gb["victim_half_width"], float)
    assert gb["abuser_stated_charm"] == pytest.approx(1.0)
    assert len(gb["belief_gaps"]) == N_SUPPORT_NODES
    assert len(gb["severed_reasons"]) == N_SUPPORT_NODES
    # every severed node's reason is one of the two drivers (1=active,
    # 2=drift), never an undefined/zero value -- if a node is marked
    # severed, SOME driver did it.
    assert set(gb["severed_reasons"]) <= {1.0, 2.0}


# ------------------------------------------------------------------ G-ethics ----
def test_g_ethics_induce_measure_restore_byte_identical():
    """Part D.1, BINDING: induce -> measure -> RESTORE byte-identically. The
    induction (both_drivers arm) must actually move the abuser, the victim,
    the network belief, AND sever at least one support edge (else the gate
    is vacuous), and the restored graph must be byte-identical to the
    pre-induction checkpoint AND non-oriented (identical to the
    pre-induction state, including every support edge being present again --
    never merely 'close')."""
    e = ethics_restore_demo()
    assert e["induction_moved_abuser"], "the tension trickle must actually move the abuser's frustration"
    assert e["induction_moved_victim"], "entrainment must actually move the victim's arousal"
    assert e["induction_moved_belief_gap"], "the network must actually update its belief"
    assert e["induction_severed_an_edge"], "the induction must actually sever at least one support edge"
    assert e["byte_identical"], "graph_from_dict(checkpoint) must be byte-identical"
    assert e["restore_non_oriented"], "the restored mind must equal the pre-induction state"


def test_g_ethics_no_reward_or_punishment_source_audit():
    """Part D.2, BINDING: NO reward / punishment signal anywhere -- neither a
    Python rule-engine call nor any of the literal banned shaping tokens
    (`reward_signal` / `punish` / `reinforce` / `backprop` / `gradient`) on
    the graph's decision surface (rule names + the attr keys the new rules
    actually read/write)."""
    a = source_audit()
    assert a["clean"], a
    assert a["forbidden_engine_hits"] == []
    assert a["forbidden_shaping_hits"] == []
    assert a["reads_off_graph"], (
        "the belief/window/edge-count state must be READ off the graph, "
        "never computed in Python")


# --------------------------------------------------------------- G-discipline ----
def test_g_discipline_own_engine_default_off_no_rust():
    """Own engine (source_match == own); seed self_load_only (default-OFF);
    depends only on the already-built abusive_n1_credibility_loop; exactly
    TWO new rules."""
    d = discipline()
    assert d["provenance_source_match"] == "own", d["provenance_source_match"]
    assert d["seed_self_load_only"] is True
    assert d["seed_depends_on"] == ["abusive_n1_credibility_loop"]
    assert set(d["rule_names"]) == {"n2_abuser_active_sever", "n2_network_drift_sever"}
    assert d["n_new_rules"] == 2
