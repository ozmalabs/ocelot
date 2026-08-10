#!/usr/bin/env python3
"""DEMO RUNNER for bigville R18 (block 266000) -- THE SCHOOL. Prints the glass-box
findings behind the gates: council funds the schoolmaster, the affect-gated
classroom (with/without co-regulation), the heterogeneous-classroom outcome
distribution + WHY each child did or did not learn, the generational hinge
(school-derived capability), and the schoolmaster's inner life (willing vs
sabotage). Emits results/bigville_school/summary.json.

Pure world I/O + read-off: every DECISION is a seed rule (bigville_school_fund /
_learn / _life). NOT agent runtime; deletable.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from worlds.bigville_school_world import BigvilleSchoolWorld       # noqa: E402
from worlds.bigville_time_world import DAY                         # noqa: E402

REASON = {0: "learned", 1: "dysregulated", 2: "missing-prereq",
          3: "school-closed", 4: "low-safety-prior", -1: "n/a"}


def _pool(w):
    return sorted(w._cell_at.keys())


def _world(*, base_rate_bp=2000, collect=True, safe=True, salary=20,
           fair_salary=20, coerced=0.0):
    w = BigvilleSchoolWorld(day_range=16)
    w.set_phase(DAY)
    P = _pool(w)
    w.add_council(base_rate_bp=base_rate_bp)
    w.add_treasury(funds=0)
    w.add_schoolmaster("master", P[5], salary=salary, fair_salary=fair_salary,
                       coerced=coerced, safe=safe)
    w.add_school(master="master")
    w.add_payer("land", P[10], taxable=1000, coin=9000)
    w.set_tax()
    if collect:
        w.collect_taxes()
    w.pay_salaries()
    w._refresh_school()
    return w, P


def main():
    out = {}

    # --- G-council-funds-the-schoolmaster ---
    on, _ = _world(collect=True)
    off, _ = _world(collect=False)
    cut, _ = _world(base_rate_bp=0)
    out["council_funds"] = {
        "funded_open": on.school_open(), "funded_master_coin": on.coin_of("master"),
        "ablate_revenue_closed": off.school_closed(),
        "tax_cutting_council_closed": cut.school_closed()}

    # --- G-affect-gated (headline) + control ---
    w, P = _world()
    w.add_child("coreg", P[11]); w.enrol("coreg", coregulated=True); w.stress("coreg")
    w.hold_lesson("coreg")
    w2, P2 = _world()
    w2.add_child("noco", P2[11]); w2.enrol("noco", coregulated=False); w2.stress("noco")
    w2.hold_lesson("noco")
    out["affect_gated"] = {
        "coregulated_learned_skill": w.skill_level("coreg"),
        "coregulated_window_widened": w.window_of("coreg")["widen_count"],
        "ablate_coreg_skill": w2.skill_level("noco"),
        "ablate_coreg_reason": REASON[w2.fail_reason_of("noco")]}

    # --- G-heterogeneous-classroom ---
    w, P = _world()
    spec = {"reg": (True, False, True, 0.5), "noprq": (True, False, False, 0.5),
            "dys": (False, True, True, 0.5), "lowsf": (False, True, True, 0.2)}
    for nm, (co, st, pr, sp) in spec.items():
        w.add_child(nm, P[11], prereq_met=pr, safety_prior=sp)
        w.enrol(nm, coregulated=co)
        if st:
            w.stress(nm)
        w.hold_lesson(nm)
    out["heterogeneous"] = {nm: {"skill": w.skill_level(nm),
                                 "why": REASON[w.fail_reason_of(nm)]} for nm in spec}

    # --- G-generational-hinge ---
    def coa(n, collect=True):
        ww, PP = _world(collect=collect)
        ww.add_child("k", PP[11], base_capability=0.3)
        ww.enrol("k", coregulated=True)
        for _ in range(n):
            ww.hold_lesson("k")
        ww.come_of_age("k")
        return ww.capability_of("k"), ww.skill_level("k")
    sc_cap, sc_sk = coa(5, True)
    un_cap, un_sk = coa(0, True)
    df_cap, df_sk = coa(5, False)     # defunded: closed school
    out["generational_hinge"] = {
        "schooled_capability": sc_cap, "schooled_skill": sc_sk,
        "unschooled_capability": un_cap,
        "defunded_capability": df_cap, "defunded_skill": df_sk}

    # --- G-schoolmaster-inner-life ---
    rows = {}
    for tag, kw in (("willing", {}), ("underpaid", dict(salary=5, fair_salary=20)),
                    ("coerced", dict(coerced=1.0))):
        w, P = _world(**kw)
        w.add_child("k", P[11]); w.enrol("k"); w.hold_lesson("k")
        rows[tag] = {"held_rate": w.master_attr("held_rate"),
                     "sabotaged": w.master_attr("sabotaged"),
                     "stated_minus_held": w.stated_minus_held(),
                     "child_gain": w.skill_level("k")}
    out["inner_life"] = rows

    # --- ETHICS: induce -> restore ---
    w, P = _world()
    w.add_child("e", P[11]); w.enrol("e", coregulated=False)
    w.stress("e"); w.hold_lesson("e")
    induced = {"skill": w.skill_level("e"), "why": REASON[w.fail_reason_of("e")]}
    w.eng.add_edge_unchecked(w._movers["e"], "attended_by", w._movers["master"])
    w.stress("e"); w.hold_lesson("e")
    out["ethics"] = {"induced": induced,
                     "restored_skill": w.skill_level("e"),
                     "restored_reason": REASON[w.fail_reason_of("e")]}

    dest = os.path.join(_ROOT, "results", "bigville_school")
    os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, "summary.json"), "w") as f:
        json.dump(out, f, indent=1)
        f.write("\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
