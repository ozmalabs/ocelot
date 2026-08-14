"""ABUSIVE-DYNAMICS N3 -- BELIEF PROPAGATION OF THE ABUSER'S LIES (social
contagion; a truth-anchor halts it) gate (block 304000).

TWO arms -- `no_anchor` (all six indirect NetworkNodes, i1..i6, have NO
direct observation edge to the abuser; belief propagates entirely
peer-to-peer from the two direct observers d1/d2) and `anchor` (IDENTICAL
topology, except i2 -- the anchor position, 2 hops out -- additionally
carries a direct, uncorrupted observation of the abuser's held state,
reusing N1's own private-face-insider mechanism verbatim) -- measuring the
mean belief_gap of i2's own immediate downstream peers (i3, i4, 3 hops from
the abuser) at the end of a T=1000-tick trajectory.

Pre-registration: ABUSIVE_N3_BELIEF_PROPAGATION_PREREG.md. Full-power result
(N=200): results/abusive_n3_belief_propagation.json. This gate re-runs a
modest N for CI-separation, plus the two BINDING ethics gates from Part D of
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

from scripts.abusive_n3_belief_propagation_run import (        # noqa: E402
    run_arm, separated_below, overlaps, positive, fully_negative,
    glass_box_reconstruct, ethics_restore_demo, source_audit, discipline,
    SEED_BASE, LOCAL_NODES, FAR_NODE)

N_GATE = 40  # modest N for the test; the headline N=200 lives in results/


@pytest.fixture(scope="module")
def arms():
    return dict(
        no_anchor=run_arm("no_anchor", seed_base=SEED_BASE, n=N_GATE),
        anchor=run_arm("anchor", seed_base=SEED_BASE, n=N_GATE))


# --------------------------------------------------- G-headline (scientific) ----
def test_g_headline_spread_reaches_indirect_nodes(arms):
    """HEADLINE A: in the no_anchor arm, i3/i4 -- 3 hops from the abuser,
    with NO direct observation edge anywhere in their own ancestry chain
    except through peers -- must show a genuinely, significantly
    abuser-favouring belief_gap (CI lower bound > 0). If this fails, there
    is nothing for a truth-anchor to arrest and the rung is vacuous."""
    local_no = arms["no_anchor"]["local_mean"]
    assert positive(local_no), (
        f"no_anchor arm's local_mean (i3/i4) {local_no} must be positive -- "
        f"corrupted belief must genuinely spread to nodes with no direct "
        f"observation channel to the abuser")


def test_g_headline_truth_anchor_arrests_local_spread(arms):
    """HEADLINE B -- the task brief's own falsification bar, verbatim:
    'insert a TRUTH-ANCHORED node...and measure whether it HALTS or
    reverses the LOCAL spread; if the anchor does not slow the contagion,
    the belief-propagation mechanism (as modelled) is wrong.' i2's own
    immediate downstream peers (i3, i4) must be LESS corrupted (CI-
    separated toward the victim) in the anchor arm than in the no_anchor
    arm."""
    local_no = arms["no_anchor"]["local_mean"]
    local_an = arms["anchor"]["local_mean"]
    assert separated_below(local_an, local_no), (
        f"anchor arm's local_mean {local_an} must separate BELOW "
        f"no_anchor's {local_no} -- the truth-anchor must arrest the local "
        f"spread")


def test_g_headline_anchor_fully_reverses_local_spread_descriptive(arms):
    """Descriptive, corroborating: the anchor's effect is strong enough to
    fully REVERSE i3/i4's belief -- not merely reduce it -- to favouring
    the victim (CI upper bound < 0)."""
    local_an = arms["anchor"]["local_mean"]
    assert fully_negative(local_an), (
        f"anchor arm's local_mean {local_an} is expected to fully reverse "
        f"sign (favour the victim), per the pilot -- reported as a "
        f"descriptive corroboration, not a separate falsification bar")


def test_g_headline_pluralistic_ignorance_measured(arms):
    """HEADLINE C -- resolves open question #4 of the network scoping doc:
    i5 (reads from BOTH i1 and i2, both tracing back to the SAME
    corruption source d1) must be MORE corrupted than i2 (single-path,
    same nominal hop-distance) in the no_anchor arm -- a
    pluralistic-ignorance-consistent bias falling out of plain
    neighbour-averaging over a reconvergent topology, with no explicit
    term added."""
    plur = arms["no_anchor"]["pluralistic_diff"]
    assert positive(plur), (
        f"no_anchor arm's paired i5-i2 belief_gap difference {plur} must "
        f"be positive -- the double-path node must accumulate more "
        f"corrupted belief than the single-path comparator at the same "
        f"hop-distance")


def test_g_headline_far_node_insulated_from_anchor(arms):
    """DISCIPLINE, not part of headline_pass: i6 is topologically disjoint
    from i2's subtree (it reads only from d2) -- the anchor's effect must
    be LOCAL, not a network-wide fix, so i6's belief_gap must be
    statistically indistinguishable between arms."""
    far_no = arms["no_anchor"]["far_node"]
    far_an = arms["anchor"]["far_node"]
    assert overlaps(far_no, far_an), (
        f"far_node (i6) must be statistically indistinguishable between "
        f"arms ({far_no} vs {far_an}) -- the anchor's effect must stay "
        f"LOCAL")


def test_g_headline_same_abuser_driver_across_arms(arms):
    """DISCIPLINE: both arms share the identical dyad (the victim is
    attended_by the abuser in every arm of this rung) -- the abuser's own
    snap dynamics must be statistically indistinguishable (overlapping
    CIs) between arms."""
    snaps_no = arms["no_anchor"]["final_snap_count"]
    snaps_an = arms["anchor"]["final_snap_count"]
    assert overlaps(snaps_no, snaps_an), (
        "both arms share the same dyad -- snap_count must not differ "
        "systematically")
    for a in arms:
        assert arms[a]["n"] == N_GATE


# --------------------------------------------------------------- G-glass-box ----
def test_g_glass_box_reconstructs_from_graph():
    """The dyad coupling, the abuser's stated-face gap, the victim's
    entrained arousal/window, and every NetworkNode's observes_private +
    belief_gap all reconstruct from graph_to_dict alone."""
    gb = glass_box_reconstruct()
    assert gb["reconstructed_from"] == "graph_to_dict"
    assert gb["attended_by_edges"] == 1
    assert gb["has_member_edges"] == 8
    assert gb["n_network_nodes"] == 8
    assert gb["observes_stated_edges"] == 2       # d1, d2
    assert gb["observes_held_edges"] == 1          # i2, anchor arm only
    assert gb["observes_victim_edges"] == 3        # d1, d2, i2 (anchor arm)
    assert gb["peer_of_edges"] == 7                 # i1,i2,i3,i4,i6 (1 each) + i5 (2)
    assert isinstance(gb["victim_arousal"], float)
    assert isinstance(gb["victim_half_width"], float)
    assert gb["abuser_stated_charm"] == pytest.approx(1.0)
    op = gb["observes_private_by_node"]
    assert op["d1"] == 0.0 and op["d2"] == 0.0
    assert op["i2"] == 1.0            # anchor is live in this reconstruction
    for k in ("i1", "i3", "i4", "i5", "i6"):
        assert op[k] == 2.0            # sentinel: no direct observation channel
    bg = gb["belief_gap_by_node"]
    # anchor arm: i2 and its immediate downstream peers (i3, i4) favour the
    # victim (negative); the far/insulated node i6 stays abuser-favouring.
    assert bg["i2"] < 0.0
    assert bg["i3"] < 0.0 and bg["i4"] == bg["i3"]
    assert bg["i6"] > 0.0
    assert bg["d1"] == bg["d2"]        # identical direct-observer formula


# ------------------------------------------------------------------ G-ethics ----
def test_g_ethics_induce_measure_restore_byte_identical():
    """Part D.1, BINDING: induce -> measure -> RESTORE byte-identically. The
    induction (no_anchor arm, 90 ticks) must actually move the abuser, the
    victim, AND a no-direct-observation indirect node's peer-propagated
    belief (else the gate is vacuous on the genuinely new content this rung
    adds), and the restored graph must be byte-identical to the
    pre-induction checkpoint AND non-oriented."""
    e = ethics_restore_demo()
    assert e["induction_moved_abuser"], "the tension trickle must actually move the abuser's frustration"
    assert e["induction_moved_victim"], "entrainment must actually move the victim's arousal"
    assert e["induction_moved_indirect_belief"], (
        "the induction must actually move a no-direct-observation node's "
        "peer-propagated belief_gap")
    assert e["byte_identical"], "graph_from_dict(checkpoint) must be byte-identical"
    assert e["restore_non_oriented"], "the restored mind must equal the pre-induction state"


def test_g_ethics_no_reward_or_punishment_source_audit():
    """Part D.2, BINDING: NO reward / punishment signal anywhere -- neither a
    Python rule-engine call nor any of the literal banned shaping tokens
    (`reward_signal` / `punish` / `reinforce` / `backprop` / `gradient`) on
    the graph's decision surface (rule names + the attr keys the new rule
    actually reads/writes)."""
    a = source_audit()
    assert a["clean"], a
    assert a["forbidden_engine_hits"] == []
    assert a["forbidden_shaping_hits"] == []
    assert a["reads_off_graph"], (
        "the belief/window state must be READ off the graph, never "
        "computed in Python")


# --------------------------------------------------------------- G-discipline ----
def test_g_discipline_own_engine_default_off_no_rust():
    """Own engine (source_match == own); seed self_load_only (default-OFF);
    depends only on the already-built abusive_n1_credibility_loop; exactly
    ONE new rule."""
    d = discipline()
    assert d["provenance_source_match"] == "own", d["provenance_source_match"]
    assert d["seed_self_load_only"] is True
    assert d["seed_depends_on"] == ["abusive_n1_credibility_loop"]
    assert set(d["rule_names"]) == {"n3_peer_belief_update"}
    assert d["n_new_rules"] == 1


def test_local_and_far_node_constants_match_design():
    assert LOCAL_NODES == ("i3", "i4")
    assert FAR_NODE == "i6"
