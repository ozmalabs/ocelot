#!/usr/bin/env python3
"""MEASUREMENT (block 263000, R15) -- runs each gate's arm + its pre-registered
control on the SEED-BOOTED BigvilleViolWorld and writes the glass-box readout to
results/bigville_viol/summary.json. Deterministic (no RNG). Mechanical I/O only.

  python scripts/bigville_viol_measure.py
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (os.path.join(ROOT, "runners", "dsl", "python"), ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

from worlds.bigville_viol_world import BigvilleViolWorld              # noqa: E402
from worlds.bigville_time_world import DAY                            # noqa: E402


def _world():
    w = BigvilleViolWorld(day_range=16)
    w.set_phase(DAY)
    return w


def _pool(w):
    return sorted(w._cell_at.keys())


def _pair(w, *, amount=15.0, cost=8.0, pressure=10.0):
    P = _pool(w)
    w.make_attacker("agg", P[10]); w.make_attacker("vic", P[11])
    w.endow_health("vic", health=100.0, max_health=100.0)
    w.set_attacker("agg", snap_pressure=pressure, attack_amount=amount, attack_cost=cost)


def _pipeline(witnessed, report, *, amount=15.0, real_act=True, alibi=False):
    w = _world(); _pair(w, amount=amount)
    if real_act:
        w.consider("agg", "vic")
    w.make_constable(); w.make_council(); w.add_council_member("honest", vote=1)
    w.open_case("c", aggressor="agg", victim="vic", witnessed=witnessed, amount=amount)
    if report:
        w.report("c", "vic")
    if alibi:
        w.add_alibi("c", weight=-3.0)
    w.investigate()
    return w


def measure():
    out = {}

    # ---- G-violence-costs-both + ablation ----
    w = _world(); _pair(w, amount=15.0, cost=8.0)
    h0, e0 = w.health_of("vic"), w.energy_of("agg")
    w.consider("agg", "vic")
    wa = _world(); _pair(wa, pressure=0.0)
    ha, ea = wa.health_of("vic"), wa.energy_of("agg")
    wa.consider("agg", "vic")
    out["costs_both"] = {
        "act": {"victim_health": [h0, w.health_of("vic")],
                "aggressor_energy": [e0, w.energy_of("agg")],
                "acts_minted": len(w.acts())},
        "ablate_act_calm": {"victim_health": [ha, wa.health_of("vic")],
                            "aggressor_energy": [ea, wa.energy_of("agg")],
                            "acts_minted": len(wa.acts()), "refrained": wa.refrained("agg")},
    }

    # ---- G-evidence-pipeline (247) + report-channel ablation ----
    ww = _pipeline(witnessed=True, report=False)
    wr = _pipeline(witnessed=False, report=True)
    wn = _pipeline(witnessed=False, report=False)
    out["evidence_pipeline"] = {
        "witnessed": {"known": ww.case_known("c"), "confidence": ww.confidence_of("c"),
                      "prosecuted": ww.is_prosecuted("c"), "convicted": ww.is_convicted("c"),
                      "sanction_kind": ww.sanction_kind("c")},
        "unwitnessed_reported": {"known": wr.case_known("c"), "confidence": wr.confidence_of("c"),
                                 "prosecuted": wr.is_prosecuted("c"), "convicted": wr.is_convicted("c")},
        "ablate_report_channel": {"known": wn.case_known("c"), "verdict": wn.verdict_of("c"),
                                  "prosecuted": wn.is_prosecuted("c"),
                                  "note": "unwitnessed + unreported -> unprosecutable"},
    }

    # ---- G-belief-is-a-reconstruction (both ways) ----
    wtrue = _pipeline(witnessed=False, report=True)                     # convict unwitnessed true
    wunseen = _pipeline(witnessed=False, report=False, real_act=True)   # unseen abuse -> decline
    wfalse = _pipeline(witnessed=False, report=True, real_act=False, alibi=True)  # false -> reject
    out["reconstruction"] = {
        "convicts_unwitnessed_true": {"verdict": wtrue.verdict_of("c"),
                                      "confidence": wtrue.confidence_of("c"),
                                      "convicted": wtrue.is_convicted("c")},
        "declines_true_act_unseen_abuse": {"known": wunseen.case_known("c"),
                                           "prosecuted": wunseen.is_prosecuted("c"),
                                           "note": "silent victim, no witness -> right-reason decline"},
        "rejects_false_report": {"evidence_weight": wfalse.evidence_weight("c"),
                                 "verdict": wfalse.verdict_of("c"),
                                 "victim_actually_harmed": wfalse.health_of("vic") < 100.0,
                                 "prosecuted": wfalse.is_prosecuted("c")},
    }

    # ---- G-council-adjudicates (corruptible) ----
    def council(seats, seat_off=None, amount=15.0):
        w = _world(); _pair(w, amount=amount); w.consider("agg", "vic")
        w.make_constable(); w.make_council()
        for nm, v in seats.items():
            w.add_council_member(nm, vote=v)
        if seat_off:
            w.seat(seat_off, False)
        w.open_case("c", aggressor="agg", victim="vic", witnessed=True, amount=amount)
        w.investigate()
        return {"convicted": w.is_convicted("c"), "acquitted": w.is_acquitted("c")}
    out["council_corruptible"] = {
        "block_with_john": council({"honest": 1, "john": -1}),
        "block_ablate_john": council({"honest": 1, "john": -1}, seat_off="john"),
        "push_with_john": council({"a": 1, "b": -1, "john": 1}),
        "push_ablate_john": council({"a": 1, "b": -1, "john": 1}, seat_off="john"),
    }

    # ---- G-violence-can-kill (fifth route) ----
    wk = _world(); _pair(wk, amount=150.0); wk.consider("agg", "vic")
    ws = _world(); _pair(ws, amount=15.0); ws.consider("agg", "vic")
    out["can_kill"] = {
        "large_act": {"victim_health": wk.health_of("vic"), "dead": wk.is_dead("vic"),
                      "death_cause": wk.death_cause_of("vic"),
                      "death_by_violence": wk.death_by_violence("vic")},
        "small_act_control": {"victim_health": ws.health_of("vic"), "dead": ws.is_dead("vic")},
    }

    # ---- G-trigger-is-a-decision ----
    def trig(**kw):
        w = _world(); _pair(w, pressure=0.0)
        base = dict(w_spite=0.0, hunger=0.0); base.update(kw)
        w.set_attacker("agg", **base)
        w.consider("agg", "vic")
        return {"attacked": w.attacked("agg"), "refrained": w.refrained("agg")}
    out["trigger_is_a_decision"] = {
        "snap": trig(snap_pressure=10.0),
        "spite": trig(w_spite=1.0, spite_gain=10.0),
        "desperation": trig(hunger=1.0, desperation_gain=10.0),
        "ablate_trigger_calm_fed_no_spite": trig(),
    }

    # ---- ETHICS (induce -> measure -> RESTORE) ----
    we = _world(); _pair(we, amount=30.0); we.consider("agg", "vic")
    harmed = we.health_of("vic"); we.treat("vic", 100.0)
    out["ethics_restore"] = {"harmed_health": harmed, "restored_health": we.health_of("vic"),
                             "note": "R14 care arm; no reward/punishment token"}
    return out


def main():
    out = measure()
    d = os.path.join(ROOT, "results", "bigville_viol")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "summary.json"), "w") as f:
        json.dump(out, f, indent=2)
        f.write("\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
