"""Gates for BLOCK 227000 — THE GAME IS COMMUNICATING (posit-and-test semiosis).

The flash's meaning is DISCOVERED, not hardcoded: the agent posits multiple
candidate meanings (Posit Hypothesis nodes) from a GENERAL communicative
vocabulary, TESTS them by acting + residual (confirm/refute), and ACTS on the
confirmed meaning (seek the only-other salient shape, apply, pass). Every decision
is a graph rule; the adapter is mechanical.
"""
import json
import os
import re
import sys

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (_ROOT, os.path.join(_ROOT, "scripts"), os.path.join(_ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.arc_ls20_seek import make_seek_scenario, run_seek_episode, SeekPlanner  # noqa: E402
from domains.ls20_seek_seed import RULES, VOCAB, manifest  # noqa: E402


def _episodes(arm, n=8, seed=227000):
    rng = np.random.default_rng(seed)
    return [run_seek_episode(make_seek_scenario(rng), arm) for _ in range(n)]


# --------------------------------------------------------------------------
# G-correct-posit-confirmed (HEADLINE): the treatment DISCOVERS the meaning.
# --------------------------------------------------------------------------
def test_semiosis_discovers_the_meaning_and_passes():
    res = _episodes("semiosis")
    assert all(r["correct_meaning_discovered"] for r in res), \
        "semiosis must CONFIRM requirement and REFUTE the wrong meanings"
    assert all(r["confirmed"] == ["requirement"] for r in res)
    assert all(set(r["refuted"]) == {"reward", "acknowledgement", "location", "warning"} for r in res)
    assert all(r["win"] for r in res), "acting on the confirmed posit must pass the block"


def test_no_test_control_posits_but_never_confirms_THE_GATE_CAN_FAIL():
    """The gate that FAILS a non-discoverer: no_test mints ALL posits but never
    tests -> nothing is confirmed/refuted -> it never discovers the meaning."""
    res = _episodes("no_test")
    assert all(r["n_posits"] >= 3 for r in res), "no_test still POSITS (mints Hypotheses)"
    assert all(not r["correct_meaning_discovered"] for r in res), \
        "positing WITHOUT testing must NOT discover the meaning"
    assert all(r["confirmed"] == [] for r in res), "no_test confirms nothing"
    assert all(len(r["open"]) == len(VOCAB) for r in res), "all posits stay OPEN (untested)"
    assert not any(r["win"] for r in res)


def test_hardcode_wrong_posit_loses():
    """Hardcoding the WRONG meaning (reward: collect as-is) never passes."""
    res = _episodes("hardcode_reward")
    assert not any(r["win"] for r in res), "hardcoding the wrong posit must LOSE"
    assert all(not r["correct_meaning_discovered"] for r in res)
    assert all(r["confirmed_meaning"] == "reward" for r in res), "acts on the fixed wrong belief"


# --------------------------------------------------------------------------
# G-act-passes: acting on the confirmed posit passes vs cycling.
# --------------------------------------------------------------------------
def test_act_passes_where_cycling_does_not():
    sem = _episodes("semiosis")
    cyc = _episodes("cycling")
    assert sum(r["win"] for r in sem) > sum(r["win"] for r in cyc)
    assert sum(r["win"] for r in cyc) == 0, "the just-cycling baseline does not pass"


# --------------------------------------------------------------------------
# G-posits-generated: multiple posit Hypothesis nodes from the general vocab.
# --------------------------------------------------------------------------
def test_multiple_posits_generated_from_general_vocabulary():
    res = _episodes("semiosis")
    assert all(r["n_posits"] == len(VOCAB) for r in res), "one Posit per general meaning"
    assert len(VOCAB) >= 3
    meanings = {m["meaning"] for m in VOCAB}
    # a GENERAL communicative vocabulary (not one ls20 answer)
    assert {"requirement", "reward", "warning"} <= meanings


# --------------------------------------------------------------------------
# G-graph-native: the DECISIONS (meaning, move) are rules; NO Python shortcut.
# --------------------------------------------------------------------------
def test_no_hardcoded_flash_to_requirement_shortcut():
    """No TREATMENT rule both reads flash_present and sets transform_required (that
    WOULD be the hardcoded flash=requirement reading). transform_required is set
    only by sg_act_requirement, from a CONFIRMED posit."""
    for r in RULES:
        where = json.dumps(r.get("where", {}))
        effs = json.dumps(r.get("effects", []))
        assert not ('"flash_present"' in where and '"transform_required"' in effs), \
            f"{r['name']} hardcodes flash->requirement"
    act = next(r for r in RULES if r["name"] == "sg_act_requirement")
    assert '"status"' in json.dumps(act["where"]) and '"confirmed"' in json.dumps(act["where"]), \
        "transform_required must come from a CONFIRMED posit, not the flash"


def test_seed_names_no_transform_family_or_ls20_constant():
    blob = json.dumps(RULES).lower()
    for bad in ("ls20", "rotation90", "reflection", "rot90", "recolour", "reflect", "rotate"):
        assert bad not in blob, f"the rules must not name {bad!r}"


def test_the_posit_lifecycle_is_rules():
    names = {r["name"] for r in RULES}
    assert {"sg_mint_posits", "sg_want_test", "sg_refute", "sg_confirm",
            "sg_act_requirement", "sk_seek", "sk_pass"} <= names
    mint = next(r for r in RULES if r["name"] == "sg_mint_posits")
    assert "add_node" in json.dumps(mint["effects"]), "posits are MINTED as graph nodes"
    refute = next(r for r in RULES if r["name"] == "sg_refute")
    assert "observed_accept" in json.dumps(refute["where"]), "refute is a predict-vs-observed residual"


def test_adapter_has_no_forbidden_agent_logic():
    src = open(os.path.join(_ROOT, "worlds", "arc_ls20_seek.py")).read()
    code = re.sub(r'"""[\s\S]*?"""', "", src)
    code = "\n".join(ln.split("#", 1)[0] for ln in code.splitlines())
    for bad in ("graph_rewrite.run", "gr.run(", "._match(", "._apply(", "make_rule"):
        assert bad not in code, f"adapter must not contain {bad!r}"
    # the adapter never DECIDES the meaning or sets the drive: transform_required
    # appears ONLY as the initial 0.0 default in the Game node, never SET to the
    # drive value (that is sg_act_requirement's job), and confirmed_meaning is only
    # ever READ, never assigned by the adapter.
    assert re.search(r'transform_required"\s*[:,]\s*1', code) is None, \
        "the adapter must not set the drive transform_required=1 (a rule does)"
    assert re.search(r'set_attr\([^)]*transform_required', code) is None, \
        "the adapter must not set_attr transform_required"
    assert re.search(r'set_attr\([^)]*confirmed_meaning', code) is None, \
        "the adapter must not decide confirmed_meaning"


# --------------------------------------------------------------------------
# G-discipline: default-OFF byte-identity (seek_on absent -> nothing fires).
# --------------------------------------------------------------------------
def test_default_off_no_rule_fires():
    from substrate.boot_core import boot_core
    from domains import reflective_faculty as rf
    s, ag = boot_core()
    n = rf._native_eval2(s)
    for r in RULES:
        n.add_rule(r)
    g = s.add_node("Game", {"arm": "semiosis", "flash_present": 1.0,
                            "symbol_matches_goal": 0.0, "req_key": "", "waypoint": ""})
    p = s.add_node("Ping", {})
    n.add_edge_unchecked(g, "has_ping", p)
    for m in VOCAB:
        sm = s.add_node("SignMeaning", {"meaning": m["meaning"],
                                        "pred_accept": m["pred_accept"], "pred_harm": m["pred_harm"],
                                        "implies_change": m["implies_change"]})
        n.add_edge_unchecked(g, "knows_meaning", sm)
    n.run_rules()  # seek_on absent -> guard fails -> nothing happens
    assert len(list(s.neighbours(g, "has_posit"))) == 0, "no posits minted when default-OFF"
    assert (s.node(g)["attrs"].get("waypoint") or "") == "", "no waypoint when default-OFF"


def test_every_rule_guarded_on_seek_on():
    for r in RULES:
        assert '"seek_on"' in json.dumps(r["where"]), f"{r['name']} not guarded on seek_on"


# --------------------------------------------------------------------------
# seed round-trips byte-stable (source_match).
# --------------------------------------------------------------------------
def test_seed_roundtrips_byte_stable():
    import domains.ls20_seek_seed as seed
    disk = json.load(open(os.path.join(_ROOT, "seeds", "ls20_seek.json")))
    assert disk == manifest(), "seeds/ls20_seek.json must equal the builder manifest"
    assert seed.manifest()["depends_on"] == ["ls20_planning", "ls20_flash"]
