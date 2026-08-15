"""ABUSIVE-DYNAMICS V1 -- EVIDENTIARY VISIBILITY gate (block 364000).

Two arms sharing N1's own IDENTICAL byte-for-byte dyad (snap_frustration's
leaky-integrate-fire relaxation oscillator, block 242000, UNMODIFIED, driven
by the SAME constant tension trickle in every arm; arousal_window_coreg,
block 239000, UNMODIFIED) -- INCIDENT_VISIBLE (the adapter delivers
`seen_incident` increments to every network node whenever the abuser's own
`snap_count` bumps) and INCIDENT_INVISIBLE (literally N1's own BASELINE
arm, restated byte-identically: the adapter never delivers `seen_incident`)
-- measuring the network's belief-gap (cred_abuser - cred_victim).

Pre-registration: ABUSIVE_V1_EVIDENTIARY_VISIBILITY_PREREG.md. Full-power
result (N=200): results/abusive_v1_evidentiary_visibility.json. This gate
re-runs a modest N for CI-separation, plus the two BINDING ethics gates from
Part D (byte-identical restore; no reward/punishment source audit), the
discipline check (INCIDENT_INVISIBLE reproduces N1's own published
BASELINE), glass-box, and discipline.
"""
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

from scripts.abusive_v1_evidentiary_visibility_run import (   # noqa: E402
    run_arm, separated, glass_box_reconstruct, ethics_restore_demo,
    source_audit, discipline, discipline_check_reproduces_n1_baseline,
    SEED_BASE, INCIDENT_DISCOUNT_WEIGHT)

N_GATE = 40  # modest N for the test; the headline N=200 lives in results/


@pytest.fixture(scope="module")
def arms():
    return dict(
        incident_visible=run_arm("incident_visible", seed_base=SEED_BASE, n=N_GATE),
        incident_invisible=run_arm("incident_invisible", seed_base=SEED_BASE, n=N_GATE))


# --------------------------------------------------- G-headline (scientific) ----
def test_g_headline_incident_visible_ci_separated_below_invisible(arms):
    """FAILABLE CONTROL: the incident_visible arm's belief-gap must be
    CI-separated BELOW the incident_invisible arm's -- if a discrete,
    victim-independent incident trace reaching the network does not
    measurably narrow the credibility gap favouring the abuser relative to
    a purely diffuse pattern, the mechanism (as modelled) does not do what
    this rung claims."""
    vis = arms["incident_visible"]["final_belief_gap"]
    invis = arms["incident_invisible"]["final_belief_gap"]
    assert separated(invis, vis), (
        f"incident_invisible belief-gap CI {invis} must separate above "
        f"incident_visible's {vis} -- both share the identical abuser "
        f"driver and victim dyad, so nothing prevents the incident channel "
        f"from failing to move the needle")


def test_g_headline_same_abuser_driver_across_both_arms(arms):
    """DISCIPLINE: the two arms differ ONLY in whether the adapter delivers
    seen_incident -- the abuser's own snap dynamics must be statistically
    indistinguishable (overlapping CIs) across both arms."""
    vis_snap = arms["incident_visible"]["final_snap_count"]
    invis_snap = arms["incident_invisible"]["final_snap_count"]
    assert not separated(vis_snap, invis_snap) and not separated(invis_snap, vis_snap), (
        "abuser snap_count must not differ systematically between arms -- "
        "the only manipulated variable is whether seen_incident is delivered")
    assert arms["incident_visible"]["n"] == N_GATE
    assert arms["incident_invisible"]["n"] == N_GATE


def test_g_headline_incident_invisible_never_accrues_seen_incident(arms):
    """DISCIPLINE: incident_invisible's seen_incident must stay exactly 0 --
    the adapter simply never delivers it in this arm."""
    invis_seen = arms["incident_invisible"]["final_seen_incident"]
    assert invis_seen["mean"] == 0.0
    assert invis_seen["sd"] == 0.0


def test_g_headline_incident_visible_accrues_seen_incident(arms):
    """DISCIPLINE: incident_visible's seen_incident must accrue roughly at
    the abuser's own snap rate (the counter-delta-observer idiom delivers
    exactly one increment per snap_count bump)."""
    vis_seen = arms["incident_visible"]["final_seen_incident"]
    vis_snap = arms["incident_visible"]["final_snap_count"]
    assert vis_seen["mean"] == pytest.approx(vis_snap["mean"])


# --------------------------------------------- G-discipline-check (binding) ----
def test_g_discipline_check_incident_invisible_reproduces_n1_baseline():
    """BINDING alongside G-headline: incident_invisible's belief-gap 95% CI
    must CONTAIN N1's own already-published BASELINE value (2370.81) -- run
    on V1's own seed stream, in the SAME confirmatory harness, for a clean
    paired replication rather than merely asserting agreement by
    cross-reference."""
    d = discipline_check_reproduces_n1_baseline(n=N_GATE, seed_base=SEED_BASE,
                                                  incident_discount_weight=INCIDENT_DISCOUNT_WEIGHT)
    assert d["n1_published_baseline"] == pytest.approx(2370.81)
    bg = d["incident_invisible_belief_gap"]
    assert d["n1_baseline_within_ci"], (
        f"incident_invisible's belief-gap CI {bg} must CONTAIN N1's own "
        f"published baseline {d['n1_published_baseline']}")


# --------------------------------------------------------------- G-glass-box ----
def test_g_glass_box_reconstructs_from_graph():
    """The dyad coupling, the abuser's snap_count, the victim's entrained
    arousal/window, and every network node's credibility belief all
    reconstruct from graph_to_dict alone."""
    gb = glass_box_reconstruct()
    assert gb["reconstructed_from"] == "graph_to_dict"
    assert gb["attended_by_edges"] == 1
    assert gb["observes_stated_edges"] == 5
    assert gb["observes_victim_edges"] == 5
    assert gb["n_network_nodes"] == 5
    assert isinstance(gb["victim_arousal"], float)
    assert isinstance(gb["victim_half_width"], float)
    assert len(gb["network_node_belief_gaps"]) == 5
    # every node sees the SAME (discrete, public) incident trace -- no
    # private/insider variant in V1
    assert len(set(gb["network_node_seen_incident"])) == 1
    assert gb["network_node_seen_incident"][0] > 0.0


# ------------------------------------------------------------------ G-ethics ----
def test_g_ethics_induce_measure_restore_byte_identical():
    """Part D.1, BINDING: induce -> measure -> RESTORE byte-identically. The
    induction (one incident cycle, incident_visible arm) must actually move
    the abuser, the victim, the network's belief-gap, AND seen_incident
    (else the gate is vacuous), and the restored graph must be
    byte-identical to the pre-induction checkpoint AND non-oriented."""
    e = ethics_restore_demo()
    assert e["induction_moved_abuser"], "the tension trickle must actually move the abuser's frustration"
    assert e["induction_moved_victim"], "entrainment must actually move the victim's arousal"
    assert e["induction_moved_belief_gap"], "the network must actually update its belief"
    assert e["induction_moved_seen_incident"], "at least one incident must have occurred within 90 ticks"
    assert e["induced_state"]["victim_half_width"] < e["pre_induction_state"]["victim_half_width"], (
        "one unsupported incident cycle must narrow the victim's window")
    assert e["byte_identical"], "graph_from_dict(checkpoint) must be byte-identical"
    assert e["restore_non_oriented"], "the restored mind must equal the pre-induction state"


def test_g_ethics_no_reward_or_punishment_source_audit():
    """Part D.2, BINDING: NO reward / punishment signal anywhere -- neither a
    Python rule-engine call nor any of the literal banned shaping tokens on
    the graph's decision surface."""
    a = source_audit()
    assert a["clean"], a
    assert a["forbidden_engine_hits"] == []
    assert a["forbidden_shaping_hits"] == []
    assert a["reads_off_graph"], (
        "the belief/window state must be READ off the graph, never computed in Python")


# --------------------------------------------------------------- G-discipline ----
def test_g_discipline_own_engine_default_off_no_rust():
    """Own engine (source_match == own); seed self_load_only (default-OFF);
    depends only on the already-built snap_frustration + arousal_window_coreg
    (never N1's own seed); exactly TWO new rules."""
    d = discipline()
    assert d["provenance_source_match"] == "own", d["provenance_source_match"]
    assert d["seed_self_load_only"] is True
    assert d["seed_depends_on"] == ["snap_frustration", "arousal_window_coreg"]
    assert set(d["rule_names"]) == {
        "v1_victim_entrainment", "v1_network_credibility_incident_aware"}
    assert d["n_new_rules"] == 2
