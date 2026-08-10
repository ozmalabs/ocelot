"""Effect-gate + deeper-wall meta-monitor — the invention-treadmill fix.

Locks the load-bearing properties the brief requires:
  (1) a NON-LIFTING invented cue is DROPPED (front end does not balloon);
  (2) a LIFTING cue is KEPT;
  (3) on a deeper-wall cell, after N consecutive non-lifting mods the cell is
      FLAGGED deeper_wall, front-end mods STOP on it, and the curriculum redirects.
All decisions are graph Rules; the adapter only measures held-out + reverts.
"""
from __future__ import annotations

import pytest

srs = pytest.importorskip("substrate_rs")

from substrate_rs import Substrate
import domains.self_directed_speech_world as W
import domains.agent_frontend as FE


def _world():
    s = Substrate()
    info = W.install_speech_world_rules(s)
    c = W.install_cell(s, "digit", "fsdd", "en")
    return s, info, c


def _n_active(s):
    return FE.n_active(s)


def test_non_lifting_cue_is_dropped():
    s, info, c = _world()
    n0 = _n_active(s)
    # the agent adds a cue FOR this cell at baseline held-out 0.40
    s.set_attr(c, "held_cookie_rate", 0.40)
    mod = FE.modify_frontend(s)
    W.note_frontend_mod(s, c, mod["cue"])
    assert _n_active(s) == n0 + 1
    # next report: held-out did NOT lift (still 0.40) -> the gate must REVERT it.
    s.set_attr(c, "held_cookie_rate", 0.40)
    s.set_attr(c, "mod_eval_pending", 1)
    W.run_effect_gate(s, info)
    assert _n_active(s) == n0, "non-lifting cue should be reverted (no balloon)"
    assert s.node(c)["attrs"]["nonlift_streak"] == 1.0


def test_lifting_cue_is_kept():
    s, info, c = _world()
    n0 = _n_active(s)
    s.set_attr(c, "held_cookie_rate", 0.40)
    mod = FE.modify_frontend(s)
    W.note_frontend_mod(s, c, mod["cue"])
    # next report: held-out LIFTED 0.40 -> 0.53 (beyond lift_band) -> KEEP it.
    s.set_attr(c, "held_cookie_rate", 0.53)
    s.set_attr(c, "mod_eval_pending", 1)
    W.run_effect_gate(s, info)
    assert _n_active(s) == n0 + 1, "lifting cue should be kept"
    assert s.node(c)["attrs"]["nonlift_streak"] == 0.0


def test_deeper_wall_flag_after_N_non_lifts_and_mods_stop():
    s, info, c = _world()
    n0 = _n_active(s)
    s.set_attr(c, "held_cookie_rate", 0.40)
    # plateau condition for the PLATEAU_TERM: hard + stalled + had effort.
    s.set_attr(c, "held_delta", 0.0)
    s.set_attr(c, "n_probes", 20.0)
    dw_n = int(s.node(c)["attrs"]["deeper_wall_n"])
    for i in range(dw_n):
        # the cell is still front-end-modifiable (not yet walled, no pending judge)
        assert W.cell_plateaued(s, c), f"cell should plateau before iter {i}"
        mod = FE.modify_frontend(s)
        if mod is None:
            inv = W.invent_frontend_cue(s, s.node(c)["attrs"]["name"], seed=i)
            # synthetic cell may have no banked clips to invent from; mint a stub
            if inv is None:
                # mimic a mint so the gate has a cue to revert (still a real Cue node)
                fe = next(n for n in s.nodes("FrontEnd"))
                stub = s.add_node("Cue", {"name": f"stub{i}", "extractor": "invented",
                                          "active": 1.0, "origin": "agent_frontend"})
                s.add_edge(fe, "has_cue", stub)
                cue = stub
            else:
                cue = inv["cue"]
        else:
            cue = mod["cue"]
        W.note_frontend_mod(s, c, cue)
        # next report: NO lift -> gate reverts + streak grows; deeper-wall after dw_n
        s.set_attr(c, "mod_eval_pending", 1)
        W.run_effect_gate(s, info)
    a = s.node(c)["attrs"]
    assert a["deeper_wall"] == 1, "cell should be flagged deeper-wall after N non-lifts"
    assert _n_active(s) == n0, "all non-lifting mods reverted -> front end bounded"
    # mods STOP on a deeper-wall cell: PLATEAU_TERM now excludes it.
    assert not W.cell_plateaued(s, c), "deeper-wall cell must no longer plateau-for-mods"


def test_front_end_stays_bounded_across_many_non_lifting_plateaus():
    # the treadmill regression: before the fix, repeated plateaus ballooned the front
    # end. Now non-lifting mods revert + the cell walls, so n_active never balloons.
    s, info, c = _world()
    n0 = _n_active(s)
    s.set_attr(c, "held_cookie_rate", 0.40)
    s.set_attr(c, "held_delta", 0.0)
    s.set_attr(c, "n_probes", 20.0)
    for i in range(10):
        if not W.cell_plateaued(s, c):
            break
        mod = FE.modify_frontend(s)
        if mod is None:
            fe = next(n for n in s.nodes("FrontEnd"))
            stub = s.add_node("Cue", {"name": f"st{i}", "extractor": "invented",
                                      "active": 1.0, "origin": "agent_frontend"})
            s.add_edge(fe, "has_cue", stub)
            cue = stub
        else:
            cue = mod["cue"]
        W.note_frontend_mod(s, c, cue)
        s.set_attr(c, "mod_eval_pending", 1)
        W.run_effect_gate(s, info)
    assert _n_active(s) == n0, "front end stays bounded (no balloon)"
    assert s.node(c)["attrs"]["deeper_wall"] == 1
