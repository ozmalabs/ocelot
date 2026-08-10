"""THE DISORDER GLASS-BOX gate (seed block 199000) — mental illness as a mis-set
decay/demotion knob. Built on 196000's staleness_decay atom + 198000's
demotion_hierarchy.

FRAMING (standing project rule): understanding, not judgment. Each disorder is a
state that makes sense given a broken parameter — a mechanistic DEMO of the
aberrant-precision / aberrant-salience account (Kapur; Friston/Corlett;
extinction-failure PTSD), never a moral claim.

Reads the measured criteria and pins the mechanism-level claims:
  * G1  OBSESSION / RUMINATION = a SELF-REFRESHING LOOP. With the `ruminates_on`
        edge present, the obsessive trace is pinned FRESH and NEVER demotes,
        while a background trace demotes 2->1->0. Snip the edge -> it demotes
        (reversible). The stuck FRESH slot CROWDS OUT background capacity at a
        matched bit budget; restoring health frees the slot.
  * G2  PTSD / non-extinction = a held THREAT-SURFACE that WON'T DEMOTE. A
        pathologically long half_life pins the threat FRESH so the graph-native
        present/past readout stays 'present'; a normal control decays to 'past'.
        Restore a normal half_life (PURE KNOB) -> it demotes to 'past'
        (reversible).
  * G3  THE KNOB IS EXPLICIT + GRAPH-RESIDENT + PURE. The disorder is produced by
        NAMED graph-resident parameters (the `ruminates_on` EDGE; the `half_life`
        ATTRIBUTE) read by RULES; the adapter runs no Python rule engine. Turning
        the knob back restores health byte-identically to a never-sick trace.
  * integer-native disorder rules; default-OFF byte-identity.

The test RUNS the measure (able to fail if the obsession demotes with the loop
on, does not demote after the edge is cut, does not crowd capacity; if the PTSD
threat ever reads 'past' within the horizon or does not flip on cure; if a cure
leaves residue; if a float enters the disorder rules; or if default-off is not
byte-identical). Prereg: VISION_DISORDER_GLASSBOX_PREREG.md.
"""
import importlib

import pytest

M = importlib.import_module("scripts.disorder_glassbox_measure")


@pytest.fixture(scope="module")
def res():
    return M.main()


def test_G1_obsession_self_refresh_pins_fresh(res):
    c = res["criteria"]
    # emerge: the obsessive (ruminated) trace never demotes; background does
    assert c["g1_obsession_stuck_fresh"], res["g1_tier"]["emerge"]
    assert c["g1_background_demotes"], res["g1_tier"]["emerge"]
    obs_on = [r["obs_tier"] for r in res["g1_tier"]["emerge"]]
    assert all(t == 2 for t in obs_on)


def test_G1_obsession_reverses_when_edge_snipped(res):
    c = res["criteria"]
    assert c["g1_edge_removed"]
    assert c["g1_reverse_demotes"], res["g1_tier"]["reverse"]
    assert c["g1_reversible"]
    obs_off = [r["obs_tier"] for r in res["g1_tier"]["reverse"]]
    # once the self-refresh coupling is cut, surprise-gated decay resumes
    assert obs_off[0] == 2 and obs_off[-1] == 0 and set(obs_off) == {0, 1, 2}


def test_G1_obsession_crowds_out_capacity(res):
    c = res["criteria"]
    assert c["g1cap_obsessive_holds_fresh_slot"], res["g1_capacity"]["headline"]
    assert c["g1cap_healthy_obsessive_is_latent"], res["g1_capacity"]["headline"]
    assert c["g1cap_obsession_crowds_out"], res["g1_capacity"]["headline"]
    assert c["g1cap_health_dominates_sweep"], res["g1_capacity"]["sweep"]
    assert c["g1cap_strict_somewhere"]
    h = res["g1_capacity"]["headline"]
    assert h["bg_retained_healthy"] > h["bg_retained_obsession"]


def test_G2_ptsd_stuck_present(res):
    c = res["criteria"]
    assert c["g2_threat_stuck_present"], res["g2"]["emerge"]
    assert c["g2_threat_stuck_fresh"], res["g2"]["emerge"]
    assert c["g2_control_reaches_past"], res["g2"]["emerge"]
    threat_on = [r["threat_present"] for r in res["g2"]["emerge"]]
    assert all(p == 1 for p in threat_on)


def test_G2_ptsd_reverses_on_restored_half_life(res):
    c = res["criteria"]
    assert c["g2_reverse_to_past"], res["g2"]["reverse"]
    assert c["g2_reverse_demotes"], res["g2"]["reverse"]
    assert c["g2_reversible"]
    threat_off = [r["threat_present"] for r in res["g2"]["reverse"]]
    # restoring a normal half_life (the pure knob) files the threat as 'past'
    assert all(p == 0 for p in threat_off)


def test_G3_knob_is_explicit_graph_resident(res):
    a = res["g3_source_audit"]
    assert a["obsession_knob_is_edge"], a
    assert a["obsession_rule_self_refreshes"], a
    assert a["readout_rule_exposes_present"], a
    assert a["no_del_node_in_disorder_seed"], a
    # the disorder is a decay fault, produced by rules over named graph params
    assert a["adapter_runs_no_python_rule_engine"], a
    assert a["knob_names"]["obsession"].startswith("ruminates_on")
    assert a["knob_names"]["ptsd"].startswith("half_life")


def test_G3_cure_is_a_pure_knob(res):
    c = res["criteria"]
    # made-sick-then-cured is byte-identical to never-sick on the trace readout
    assert c["g3_obsession_cure_is_pure"], (res["g3_pure_knob"]["obs_never"],
                                            res["g3_pure_knob"]["obs_cured"])
    assert c["g3_ptsd_cure_is_pure"], (res["g3_pure_knob"]["ptsd_never"],
                                       res["g3_pure_knob"]["ptsd_cured"])


def test_integer_native(res):
    ia = res["integer_audit"]
    assert res["criteria"]["integer_native"], ia["offenders"]
    assert ia["offender_count"] == 0
    # the readout rule uses Gte/IfThenElse (integer), no Div/Times
    assert "IfThenElse" in ia["report"]["dis_present_readout"]


def test_default_off_byte_identical(res):
    c = res["criteria"]
    assert c["default_off_byte_identical"], res["default_off"]
    assert c["default_off_no_params_created"]
