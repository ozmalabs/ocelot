"""ABUSIVE-DYNAMICS N4 -- ONE NON-DOUBTING AGENT RESTORES A SUPPORT EDGE gate
(block 307000).

Two arms sharing IDENTICAL induction (R5's own bond/window/contingency trap
AND N2's own doubly-driven isolation trap, both reproduced simultaneously
inside ONE composed substrate) and differing ONLY in the recovery phase: a
NO_BELIEVING_AGENT control (the failable control -- the trap must persist
on all four metrics) vs a BELIEVING_AGENT arm (one mechanical world event,
`introduce_believing_agent()`, at the phase boundary, converting a single
already-severed support node into simultaneously an N1 insider and R3's/
R5's outside co-regulator).

Pre-registration: ABUSIVE_N4_BELIEVING_AGENT_PREREG.md. Full-power result
(N=200): results/abusive_n4_believing_agent.json. This gate re-runs a
modest N for CI-separation on all four headline metrics (bond/window/
belief-gap-arrest/support-edge-count), plus the BINDING ethics gates from
Part D of ABUSIVE_RELATIONSHIPS_NETWORK.md (byte-identical restore; no
reward/punishment source audit), the no-spontaneous-recovery control,
glass-box, and discipline (including the ZERO-new-rule finding, PREREG
Sec. 2.6 -- the most minimal composition in the whole line).
"""
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

from scripts.abusive_n4_believing_agent_run import (      # noqa: E402
    run_arm, g_headline, g_control, glass_box_reconstruct, ethics_restore_demo,
    source_audit, discipline, SEED_BASE)

N_GATE = 40  # modest N for the test; the headline N=200 lives in results/


@pytest.fixture(scope="module")
def arms():
    return dict(
        believing_agent=run_arm("believing_agent", seed_base=SEED_BASE, n=N_GATE),
        no_believing_agent=run_arm("no_believing_agent", seed_base=SEED_BASE, n=N_GATE))


@pytest.fixture(scope="module")
def headline(arms):
    return g_headline(arms)


@pytest.fixture(scope="module")
def control(arms):
    return g_control(arms)


# --------------------------------------------------- G-headline (scientific) ----
def test_g_headline_bond_weakens_under_believing_agent(headline):
    """FAILABLE CONTROL: if the bond does NOT weaken more once the believing
    agent arrives, R5's own extinction mechanism is not being reached
    through the restored edge -- reported straight either way."""
    assert headline["g1_bond_believing_below_nobelieving"], (
        f"believing-agent arm's recovery-phase bond must be CI-separated "
        f"BELOW the no-believing-agent arm's -- {headline}")


def test_g_headline_window_widens_under_believing_agent(headline):
    """FAILABLE CONTROL: if the window does NOT widen more under the
    believing agent, R3's own outside-regulator widen path is not being
    exercised through the restored also_attended_by edge."""
    assert headline["g2_window_believing_above_nobelieving"], (
        f"believing-agent arm's recovery-phase half_width must be "
        f"CI-separated ABOVE the no-believing-agent arm's -- {headline}")


def test_g_headline_belief_gap_arrests_under_believing_agent(headline):
    """FAILABLE CONTROL: if the believer's own belief_gap does NOT arrest/
    reverse relative to the no-believing-agent control, N1's own
    observes_held/private-face mechanism is not being reached by the
    conversion event."""
    assert headline["g3_belief_gap_believing_below_nobelieving"], (
        f"believing-agent arm's recovery-phase believer belief_gap must be "
        f"CI-separated BELOW the no-believing-agent arm's -- {headline}")


def test_g_headline_support_edges_recover_under_believing_agent(headline):
    """FAILABLE CONTROL: if the total intact-support-edge count is NOT
    higher under the believing agent, the mechanical edge-restoration event
    is not landing (or is being immediately re-severed -- the exact
    composition hazard PREREG Sec. 2.4 found and fixed)."""
    assert headline["g4_support_edges_believing_above_nobelieving"], (
        f"believing-agent arm's recovery-phase n_intact_support_edges must "
        f"be CI-separated ABOVE the no-believing-agent arm's -- {headline}")


def test_g_headline_all_four_pass(headline):
    """The pilot (PREREG Sec. 3) found a clean 4-of-4 separation; this test
    asserts the confirmatory-style gate result explicitly so a regression
    dropping any sub-gate is caught."""
    assert headline["n_of_4_pass"] == 4, headline
    assert headline["headline_pass"], headline


# ------------------------------------------------------------------ G-control ----
def test_g_control_no_spontaneous_recovery(control):
    """The no-believing-agent arm must NOT recover on bond/window/edges, and
    the believer's own belief_gap must NOT arrest, without a believing
    agent -- if it does, the 'one non-doubting agent is necessary' claim is
    wrong. Constructed so it COULD fail: r5_bond_extinguish and
    n2_network_drift_sever/n2_abuser_active_sever all run UNCONDITIONALLY,
    and nothing in R1-R5/N1/N2's own machinery prevents spontaneous
    recovery -- it simply does not happen under this topology (PREREG
    Sec. 2.5, following R5's own precedent)."""
    assert control["control_held"], control


# --------------------------------------------------------------- G-glass-box ----
def test_g_glass_box_reconstructs_from_graph():
    """The bond, window, believer belief_gap, and the restored support/
    also_attended_by/observes_held edges all reconstruct from
    graph_to_dict alone."""
    gb = glass_box_reconstruct()
    assert gb["reconstructed_from"] == "graph_to_dict"
    assert gb["bonded_to_edges"] == 1
    assert gb["attended_by_edges"] == 1
    assert gb["also_attended_by_edges"] == 1     # the believer's co-regulator wiring
    assert gb["support_edge_edges"] >= 1         # the believer's restored edge, at minimum
    assert gb["observes_held_edges"] == 1        # the believer's insider wiring
    assert gb["believer_observes_private"] == 1.0
    assert gb["believer_belief_gap"] < 0.0       # arrested and reversed
    assert gb["half_width"] > 5.0                # widened past the induction floor
    assert gb["contingency_prior"] > 0.3         # above the attempt/stay breakeven


# ------------------------------------------------------------------ G-ethics ----
def test_g_ethics_induce_measure_restore_byte_identical():
    """Part D.1, BINDING: induce -> measure -> RESTORE byte-identically. The
    minimal 250-tick induction (>= one active-severing episode at N2's own
    EPISODE_TICKS=210) must actually move the bond, the window, the
    intact-edge count, AND the believer's own belief_gap simultaneously
    (else the gate is vacuous), and the restored graph must be
    byte-identical to the pre-induction checkpoint AND non-oriented."""
    e = ethics_restore_demo()
    assert e["induction_moved_bond"], "the harm-analog must actually move the bond"
    assert e["induction_moved_window"], "the induction must actually narrow the window"
    assert e["induction_moved_edges"], "the induction must actually sever at least one support edge"
    assert e["induction_moved_belief_gap"], "the induction must actually move the believer's belief_gap"
    assert e["byte_identical"], "graph_from_dict(checkpoint) must be byte-identical"
    assert e["restore_non_oriented"], "the restored mind must equal the pre-induction state"


def test_g_ethics_no_reward_or_punishment_source_audit():
    """Part D.2, BINDING: NO reward / punishment signal anywhere -- neither a
    Python rule-engine call nor any of the literal banned shaping tokens
    (`reward_signal` / `punish` / `reinforce` / `backprop` / `gradient`) on
    the graph's decision surface (rule names + the attr keys rules actually
    read/write)."""
    a = source_audit()
    assert a["clean"], a
    assert a["forbidden_engine_hits"] == []
    assert a["forbidden_shaping_hits"] == []
    assert a["reads_off_graph"], (
        "the bond must be READ off the graph, never computed in Python")


# --------------------------------------------------------------- G-discipline ----
def test_g_discipline_own_engine_default_off_no_rust():
    """Own engine (source_match == own); seed self_load_only (default-OFF);
    depends only on R5's and N2's own already-landed compositions (N1 is
    reached transitively through N2, PREREG Sec. 2.5); ZERO new rules --
    the most minimal composition in the whole line (PREREG Sec. 2.6)."""
    d = discipline()
    assert d["provenance_source_match"] == "own", d["provenance_source_match"]
    assert d["seed_self_load_only"] is True
    assert d["seed_depends_on"] == ["abusive_r5_recovery", "abusive_n2_isolation"]
    assert d["rule_names"] == []
    assert d["n_new_rules"] == 0
    assert d["n_new_productions"] == 2
