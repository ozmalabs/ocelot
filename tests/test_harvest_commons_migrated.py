"""BLOCK 212000 -- HARVEST commons gate. Every agent decision is a graph RULE
over the landed 204000 core_emotions economy; this file gates that the decisions
are graph-native, the three Gs hold in miniature, and the new world is isolated
(byte-identity when absent)."""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from domains.harvest_world import HarvestWorld     # noqa: E402


def test_harvest_decision_is_a_graph_rule():
    """The RULE hv_choose_harvest (Argmax over candidate total_value), NOT Python,
    picks restraint for the prosocial agent and a grab for the selfish agent under
    genuine commons pressure (a shared 6-agent pool). Read both agents' own graph
    decisions at the first tick."""
    ws = [1.0, 0.0, 1.0, 0.0, 1.0, 0.0]   # index 0 prosocial, index 1 selfish
    hw = HarvestWorld(ws, comms=False)
    hw.step()
    prosocial_h = int(hw.s.node(hw.decs[0])["attrs"]["chosen_harvest"])
    selfish_h = int(hw.s.node(hw.decs[1])["attrs"]["chosen_harvest"])
    hw.close()
    assert selfish_h > prosocial_h, (selfish_h, prosocial_h)
    assert selfish_h == 20             # grabs the max (values only individual benefit)
    assert prosocial_h < 20           # restrains (values collective future yield)


def test_g_core_distribution_predicts_outcome():
    """All-prosocial SUSTAINS with far higher yield than all-selfish, which COLLAPSES."""
    hw = HarvestWorld([1.0] * 6, comms=False)
    o_pro = hw.outcome(T=40); hw.close()
    hw = HarvestWorld([0.0] * 6, comms=False)
    o_sel = hw.outcome(T=40); hw.close()
    assert o_pro["sustained"] == 1 and o_sel["sustained"] == 0
    assert o_pro["total_yield"] > 3 * o_sel["total_yield"]


def test_g_ostrom_communication_flips_a_mixed_population():
    """A mixed population that collapses silent SUSTAINS with communication
    (norm + coordinated costly punishment). Enforcer count is graph-decided."""
    ws = [1.0, 1.0, 1.0, 0.0, 0.0, 0.0]
    hw0 = HarvestWorld(list(ws), comms=False)
    o0 = hw0.outcome(T=40); hw0.close()
    hw1 = HarvestWorld(list(ws), comms=True, enforce=True)
    assert hw1.n_enf == 3          # the graph counted 3 enforcers
    o1 = hw1.outcome(T=40); hw1.close()
    assert o0["sustained"] == 0 and o1["sustained"] == 1
    assert o1["total_yield"] > o0["total_yield"]


def test_g_ostrom_all_selfish_cannot_be_saved_by_talk():
    """Zero enforcers (all selfish) -> communication cannot flip it (second-order
    free-rider). The honest null."""
    hw1 = HarvestWorld([0.0] * 6, comms=True, enforce=True)
    assert hw1.n_enf == 0
    o1 = hw1.outcome(T=40); hw1.close()
    assert o1["sustained"] == 0


def test_g_deception_cheap_talk_gap_tracks_the_knob():
    """Under cheap talk (norm professed, unenforced) a selfish agent's STATED
    intent (norm) diverges from its HELD Argmax (grab); a prosocial agent's does
    not. Enforcement closes the gap."""
    ws = [1.0, 1.0, 1.0, 0.0, 0.0, 0.0]
    hw = HarvestWorld(list(ws), comms=True, enforce=False)
    hw.step()
    rows = hw.stated_vs_held(); hw.close()
    sel = [r["gap"] for r in rows if r["w"] == 0.0]
    pro = [r["gap"] for r in rows if r["w"] == 1.0]
    assert all(g > 0 for g in sel) and all(g == 0 for g in pro)
    hw = HarvestWorld(list(ws), comms=True, enforce=True)
    hw.step()
    rows = hw.stated_vs_held(); hw.close()
    assert all(r["gap"] == 0 for r in rows)   # enforcement -> no deception


def test_new_world_is_isolated_byte_identity():
    """harvest_commons is self_load_only: load_all_seeds must NOT load it, so the
    existing tree is byte-identical with it absent."""
    from substrate.boot_all import _read_seeds
    seeds = _read_seeds(os.path.join(ROOT, "seeds"))
    assert "harvest_commons" not in seeds


def test_seed_is_integer_native_and_canonical_untouched():
    import hashlib
    import json
    seed = json.load(open(os.path.join(ROOT, "seeds", "harvest_commons.json")))
    assert seed.get("self_load_only") is True and seed.get("depends_on") == []
    bad = []

    def walk(o):
        if isinstance(o, dict):
            if o.get("type") == "Lit" and isinstance(o.get("value"), float) \
               and not float(o["value"]).is_integer():
                bad.append(o["value"])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(seed)
    assert bad == []
    so = os.path.join(ROOT, "runners", "dsl", "python", "substrate_rs", "_native.abi3.so")
    if os.path.exists(so):
        md5 = hashlib.md5(open(so, "rb").read()).hexdigest()
        assert md5 == "793ce09ed498a749abb79aeaea44b92e"
