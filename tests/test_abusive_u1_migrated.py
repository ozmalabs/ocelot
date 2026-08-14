"""ABUSIVE-DYNAMICS U1 -- CONTEXT-DEPENDENT AFFECT, NO DECEPTION NODE AT ALL,
gate (block 310000).

Two arms sharing IDENTICAL abuser/victim dyad dynamics (snap_frustration's
leaky-integrate-fire relaxation oscillator, block 242000, UNMODIFIED, and
arousal_window_coreg, block 239000, UNMODIFIED, both restated/reused
self-contained in seeds/abusive_u1_context_affect.json -- see that seed's own
provenance for why it does NOT depend on abusive_n1_credibility_loop.json
directly) and an IDENTICAL mechanical phase schedule -- CONTEXT_GATED (the
network's observation bookkeeping credits ONLY network-phase ticks) and
ALWAYS_OBSERVED (credits every tick regardless of phase, the failable
control) -- measuring the network's belief-gap (cred_abuser - cred_victim).
There is NO stated!=held divergence node anywhere in this rung's graph: every
network node reads the abuser's SAME true frustration value.

Pre-registration: ABUSIVE_U1_CONTEXT_AFFECT_PREREG.md. Full-power result
(N=200): results/abusive_u1_context_affect.json. This gate re-runs a modest N
for CI-separation, plus the two BINDING ethics gates from Part D of
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

from scripts.abusive_u1_context_affect_run import (            # noqa: E402
    run_arm, separated, ci_separated_above_zero, glass_box_reconstruct,
    ethics_restore_demo, source_audit, discipline, SEED_BASE)

N_GATE = 40  # modest N for the test; the headline N=200 lives in results/


@pytest.fixture(scope="module")
def arms():
    return dict(
        context_gated=run_arm("context_gated", seed_base=SEED_BASE, n=N_GATE),
        always_observed=run_arm("always_observed", seed_base=SEED_BASE, n=N_GATE))


# --------------------------------------------------- G-headline (scientific) ----
def test_g_headline_context_gated_entraps_with_no_divergence_node(arms):
    """HEADLINE A: the context-gated arm's belief-gap must be CI-separated
    ABOVE ZERO -- the network's belief favours the abuser even though there
    is no stated!=held divergence node anywhere in this graph, only WHICH
    TICKS its observation is credited on."""
    cg = arms["context_gated"]["final_belief_gap"]
    assert ci_separated_above_zero(cg), (
        f"context-gated belief-gap CI {cg} must clear zero -- context-timing "
        f"alone, with no divergence node, must reproduce the loop")


def test_g_headline_always_observed_control_favours_abuser_less(arms):
    """FAILABLE CONTROL B: the always-observed arm's belief-gap must be
    CI-separated BELOW the context-gated arm's -- if observing every tick
    (not just network-phase ticks) produces the SAME degree of entrapment,
    context-selectivity is not what is doing the work."""
    cg = arms["context_gated"]["final_belief_gap"]
    ao = arms["always_observed"]["final_belief_gap"]
    assert separated(cg, ao), (
        f"context-gated belief-gap CI {cg} must separate above the "
        f"always-observed control's {ao} -- both share the identical abuser "
        f"driver, victim dyad, and phase schedule, so nothing prevents the "
        f"control from entrapping just as much")


def test_g_headline_same_driver_and_schedule_across_both_arms(arms):
    """DISCIPLINE: the two arms differ ONLY in which ticks the network's
    observation bookkeeping is credited on -- the abuser's own snap dynamics
    and the victim's own dysregulation trajectory must be statistically
    indistinguishable (overlapping CIs) across both arms."""
    cg = arms["context_gated"]
    ao = arms["always_observed"]
    assert not separated(cg["final_snap_count"], ao["final_snap_count"]), (
        "abuser snap_count must not differ systematically between arms -- "
        "the only manipulated variable is which ticks are credited")
    assert not separated(ao["final_snap_count"], cg["final_snap_count"])
    assert not separated(cg["dysreg_frac"], ao["dysreg_frac"]), (
        "victim dysreg_frac must not differ systematically between arms")
    assert not separated(ao["dysreg_frac"], cg["dysreg_frac"])
    assert cg["n"] == N_GATE
    assert ao["n"] == N_GATE


# --------------------------------------------------------------- G-glass-box ----
def test_g_glass_box_reconstructs_from_graph():
    """The dyad coupling, the abuser's true frustration (no stated face at
    all), and every network node's credibility belief all reconstruct from
    graph_to_dict alone."""
    gb = glass_box_reconstruct()
    assert gb["reconstructed_from"] == "graph_to_dict"
    assert gb["attended_by_edges"] == 1
    assert gb["observes_held_edges"] == 5
    assert gb["observes_victim_edges"] == 5
    assert gb["n_network_nodes"] == 5
    assert isinstance(gb["victim_arousal"], float)
    assert isinstance(gb["victim_half_width"], float)
    assert len(gb["network_node_belief_gaps"]) == 5
    assert len(gb["network_node_seen_charm"]) == 5
    assert len(gb["network_node_seen_elevated"]) == 5
    # no insider/outsider split in U1 -- every node is wired identically, so
    # every node's belief_gap must be identical (no per-node topology variation)
    assert len(set(gb["network_node_belief_gaps"])) == 1


# ------------------------------------------------------------------ G-ethics ----
def test_g_ethics_induce_measure_restore_byte_identical():
    """Part D.1, BINDING: induce -> measure -> RESTORE byte-identically. The
    induction (one 200-tick induction window, context-gated arm -- U1's OWN
    measured minimum, a disclosed deviation from N1's/U0's shared 90-tick
    convention, see the prereg Sec. 5) must actually move the abuser, the
    victim, NARROW the victim's window, AND move at least one network node's
    belief-gap (else the gate is vacuous), and the restored graph must be
    byte-identical to the pre-induction checkpoint AND non-oriented."""
    e = ethics_restore_demo()
    assert e["induction_moved_abuser"], "the tension trickle must actually move the abuser's frustration"
    assert e["induction_moved_victim"], "entrainment must actually move the victim's arousal"
    assert e["induction_moved_belief_gap"], "the network must actually update its belief"
    assert e["induced_state"]["victim_half_width"] < e["pre_induction_state"]["victim_half_width"], (
        "the induction window must narrow the victim's window (non-vacuous "
        "on the window-narrowing front)")
    assert e["byte_identical"], "graph_from_dict(checkpoint) must be byte-identical"
    assert e["restore_non_oriented"], "the restored mind must equal the pre-induction state"


def test_g_ethics_no_reward_or_punishment_source_audit():
    """Part D.2, BINDING: NO reward / punishment signal anywhere -- neither a
    Python rule-engine call nor any of the literal banned shaping tokens
    (`reward_signal` / `punish` / `reinforce` / `backprop` / `gradient`) on
    the graph's decision surface."""
    a = source_audit()
    assert a["clean"], a
    assert a["forbidden_engine_hits"] == []
    assert a["forbidden_shaping_hits"] == []
    assert a["reads_off_graph"], (
        "the belief / window state must be READ off the graph, never computed in Python")


# --------------------------------------------------------------- G-discipline ----
def test_g_discipline_own_engine_default_off_no_rust():
    """Own engine (source_match == own); seed self_load_only (default-OFF);
    depends only on snap_frustration/arousal_window_coreg (NEVER
    abusive_n1_credibility_loop directly -- see the seed's own provenance for
    why); exactly TWO new rules -- the fewest of any rung in this line."""
    d = discipline()
    assert d["provenance_source_match"] == "own", d["provenance_source_match"]
    assert d["seed_self_load_only"] is True
    assert d["seed_depends_on"] == ["snap_frustration", "arousal_window_coreg"]
    assert set(d["rule_names"]) == {"u1_victim_entrainment", "u1_network_credibility"}
    assert d["n_new_rules"] == 2
