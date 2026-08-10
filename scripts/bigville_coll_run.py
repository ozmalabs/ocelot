#!/usr/bin/env python3
"""bigville R16 (block 264000) -- GLASS-BOX demonstration of COLLECTION + EVICTION-
AS-ENFORCEMENT + the MORAL INJURY of eviction.

Runs the pre-registered gates end to end and dumps every number to
results/bigville_coll/summary.json (read straight off the graph -- no narration).
Story: rent doesn't move until someone knocks (and can pocket it); nobody is
evicted until a doer reaches the door; the doer FEELS it iff he has empathy; and an
empathic owner offloads the dirty work to hands that feel it less -- so the actual
evictor is systematically low-empathy (the banality of eviction). Every decision is
a seed RULE; this script only wires edges, places movers, arms one-shots, ticks and
reads. Ethics: induce -> measure -> RESTORE.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_coll_world import BigvilleCollWorld    # noqa: E402
from worlds.bigville_time_world import DAY                  # noqa: E402

OUT = os.path.join(_ROOT, "results", "bigville_coll")


def _pool(w):
    return sorted(w._cell_at.keys())


def _world():
    w = BigvilleCollWorld(day_range=16)
    w.set_phase(DAY)
    w.add_bank("scrooge", _pool(w)[0], reserves=100000, salary=0, fair_rate_bp=1000)
    return w


def collection_is_an_act():
    w = _world(); P = _pool(w)
    w.make_agent("ll", P[10], coin=0)
    w.make_agent("tenant", P[10], coin=100)
    w.add_house("h", 200); w.place_house("h", P[10])
    w.rent("tenant", "ll", "h", rent=5, term=3)
    w.setup_rental_r16("tenant", hired=0, wage=0)
    w.hire_collector("ll", "tenant")
    before = (w.coin_of("ll"), w.coin_of("tenant"))
    w.collect("ll")
    after = (w.coin_of("ll"), w.coin_of("tenant"))
    # ablation
    a = _world(); Pa = _pool(a)
    a.make_agent("ll", Pa[20], coin=0)
    a.make_agent("tenant", Pa[10], coin=100)
    a.add_house("h", 200); a.place_house("h", Pa[10])
    a.rent("tenant", "ll", "h", rent=5, term=3)
    a.setup_rental_r16("tenant", hired=0, wage=0)
    a.hire_collector("ll", "tenant")
    a.collect("ll")
    return dict(before=before, after=after,
                ablate_owner=a.coin_of("ll"), ablate_tenant=a.coin_of("tenant"),
                act=(after == (5, 95) and a.coin_of("ll") == 0))


def hired_and_sabotage(deliver_bp):
    w = _world(); P = _pool(w)
    w.make_agent("ll", P[30], coin=1000)
    w.make_agent("agent", P[10], coin=0, deliver_bp=deliver_bp)
    w.make_agent("tenant", P[10], coin=100)
    w.add_house("h", 200); w.place_house("h", P[10])
    w.rent("tenant", "ll", "h", rent=10, term=3)
    w.setup_rental_r16("tenant", hired=1, wage=3)
    w.hire_collector("agent", "tenant")
    w.collect("agent"); w.deliver("agent"); w.pay_wage("agent")
    return dict(deliver_bp=deliver_bp, stated=w.stated_collected_of("agent"),
                held=w.held_delivered_of("agent"), owner_net=w.coin_of("ll") - 1000,
                collector_take=w.coin_of("agent"), tenant_paid=100 - w.coin_of("tenant"))


def _arrears_world(w_super):
    w = _world(); P = _pool(w)
    w.make_agent("ll", P[10], coin=0)
    w.make_agent("tenant", P[10], coin=0)
    w.attach_affect("tenant", concern_mag=4.0, concern_drop=3.0, arousal=0.0, valence=5.0)
    w.make_agent("doer", P[15], coin=0, w_supergraph=w_super, injury_mag=4.0, injury_drop=3.0)
    w.attach_affect("doer", concern_mag=0.0, concern_drop=0.0, arousal=0.0, valence=5.0)
    w.add_house("h", 200); w.place_house("h", P[15])
    w.rent("tenant", "ll", "h", rent=5, term=2)
    w.setup_rental_r16("tenant", hired=0, wage=0)
    w.hire_collector("ll", "tenant")
    for _ in range(3):
        w.place("ll", P[10]); w.collect("ll")
    return w, P


def eviction_needs_a_doer():
    wd, P = _arrears_world(4.0)
    wd.hire_enforcer("doer", "tenant"); wd.evict("doer")
    present = dict(arr=wd.arr_of("tenant"), evicted=wd.r16_evicted_of("tenant"),
                   homeless=wd.homeless_of("tenant"),
                   victim_valence=wd.affect_state("tenant")["valence"])
    wn, _ = _arrears_world(4.0)
    wn.evict("doer")   # no enforcer wired
    absent = dict(arr=wn.arr_of("tenant"), evicted=wn.r16_evicted_of("tenant"),
                  homeless=wn.homeless_of("tenant"),
                  victim_valence=wn.affect_state("tenant")["valence"])
    return dict(doer_present=present, no_doer_control=absent,
                needs_doer=(present["evicted"] == 1 and absent["evicted"] == 0))


def moral_injury(w_super):
    w, P = _arrears_world(w_super)
    before = w.affect_state("doer")
    w.hire_enforcer("doer", "tenant"); w.evict("doer")
    after = w.affect_state("doer")
    return dict(w_supergraph=w_super, arousal_before=before["arousal"],
                arousal_after=after["arousal"], valence_before=before["valence"],
                valence_after=after["valence"], moral_injury=w.moral_injury_of("doer"),
                injury_total=w.injury_total_of("doer"),
                zero_injury=w.zero_injury_of("doer"))


def dirty_work_offload():
    # conservation cases
    a, _ = _arrears_world(4.0)
    a.hire_enforcer("doer", "tenant"); a.evict("doer")
    self_case = a.injury_total_of("doer")

    b, P = _arrears_world(4.0)
    b.make_agent("bailiff", P[15], coin=0, w_supergraph=1.0, injury_mag=4.0, injury_drop=3.0)
    b.attach_affect("bailiff", concern_mag=0.0, concern_drop=0.0, arousal=0.0, valence=5.0)
    b.hire_enforcer("bailiff", "tenant"); b.evict("bailiff")
    move_case = dict(bailiff=b.injury_total_of("bailiff"), owner=b.injury_total_of("doer"))

    c, P = _arrears_world(4.0)
    c.make_agent("bailiff", P[15], coin=0, w_supergraph=0.0, injury_mag=4.0, injury_drop=3.0)
    c.attach_affect("bailiff", concern_mag=0.0, concern_drop=0.0, arousal=0.0, valence=5.0)
    c.hire_enforcer("bailiff", "tenant"); c.evict("bailiff")
    erase_case = dict(bailiff_injury=c.injury_total_of("bailiff"),
                      bailiff_zero=c.zero_injury_of("bailiff"))

    # emergent market pick
    w = _world(); P = _pool(w)
    w.make_agent("bailiff_psych", P[40], w_supergraph=0.0, injury_mag=4.0, ask_wage=2.0)
    w.make_agent("bailiff_emp", P[41], w_supergraph=1.0, injury_mag=4.0, ask_wage=2.0)
    picks = {}
    for i, (nm, w_own) in enumerate([("empathic_owner", 1.0), ("psychopath_owner", 0.0)]):
        w.make_agent(nm, P[10 + i], coin=0, w_supergraph=w_own, injury_mag=4.0, ask_wage=0.0)
        w.make_agent("t%d" % i, P[20 + i], coin=0)
        w.add_house("h%d" % i, 200); w.place_house("h%d" % i, P[20 + i])
        w.rent("t%d" % i, nm, "h%d" % i, rent=5, term=2)
        w.setup_rental_r16("t%d" % i, hired=0, wage=0)
        w.add_candidate("t%d" % i, nm)
        w.add_candidate("t%d" % i, "bailiff_psych")
        w.add_candidate("t%d" % i, "bailiff_emp")
        w.pick_cheapest("t%d" % i)
        picks[nm] = dict(owner_empathy=w_own, picked_evictor_empathy=w.picked_w_of("t%d" % i),
                         picked_ask_wage=w.picked_wage_of("t%d" % i))
    return dict(self_case_owner_injury=self_case, hire_empathic_MOVED=move_case,
                hire_psychopath_ERASED=erase_case, market_pick=picks,
                banality=(max(p["picked_evictor_empathy"] for p in picks.values()) == 0.0))


def ethics_restore():
    w, P = _arrears_world(4.0)
    w.hire_enforcer("doer", "tenant"); w.evict("doer")
    induced = dict(tenant_homeless=w.homeless_of("tenant"),
                   doer_injury=w.moral_injury_of("doer"),
                   doer_valence=w.affect_state("doer")["valence"])
    w.restore("tenant", "doer", tenants=("tenant",))
    restored = dict(tenant_affect=w.affect_state("tenant"),
                    doer_affect=w.affect_state("doer"),
                    tenant_homeless=w.homeless_of("tenant"),
                    evicted=w.r16_evicted_of("tenant"))
    return dict(induced=induced, restored=restored,
                clean=(restored["tenant_homeless"] == 0 and restored["evicted"] == 0
                       and restored["doer_affect"]["valence"] == 5.0))


def main():
    os.makedirs(OUT, exist_ok=True)
    R = {}
    R["G_collection_is_an_act"] = collection_is_an_act()
    R["G_collection_refusable"] = dict(honest=hired_and_sabotage(10000),
                                       saboteur=hired_and_sabotage(6000))
    R["G_eviction_needs_a_doer"] = eviction_needs_a_doer()
    R["G_moral_injury"] = dict(empathic=moral_injury(4.0), psychopath=moral_injury(0.0))
    R["G_dirty_work_offload"] = dirty_work_offload()
    R["G_ethics_restore"] = ethics_restore()

    with open(os.path.join(OUT, "summary.json"), "w") as f:
        json.dump(R, f, indent=2)

    # glass-box console read-off
    print("=== BIGVILLE R16 — COLLECTION / EVICTION / MORAL INJURY (glass-box) ===")
    a = R["G_collection_is_an_act"]
    print("COLLECT  before(ll,tenant)=%s -> after=%s | ablate(not proximate) owner=%s (act=%s)"
          % (a["before"], a["after"], a["ablate_owner"], a["act"]))
    h, s = R["G_collection_refusable"]["honest"], R["G_collection_refusable"]["saboteur"]
    print("REFUSE   honest: stated=%d held=%d owner_net=%d | saboteur: stated=%d held=%d owner_net=%d take=%d (234 gap=%s)"
          % (h["stated"], h["held"], h["owner_net"], s["stated"], s["held"],
             s["owner_net"], s["collector_take"], s["stated"] > s["held"]))
    e = R["G_eviction_needs_a_doer"]
    print("EVICT    doer-present evicted=%d homeless=%d | no-doer evicted=%d (needs_doer=%s)"
          % (e["doer_present"]["evicted"], e["doer_present"]["homeless"],
             e["no_doer_control"]["evicted"], e["needs_doer"]))
    em, ps = R["G_moral_injury"]["empathic"], R["G_moral_injury"]["psychopath"]
    print("INJURY   empathic evictor: valence %.0f->%.0f arousal %.0f->%.0f injury=%d | psychopath: valence %.0f->%.0f injury=%d"
          % (em["valence_before"], em["valence_after"], em["arousal_before"], em["arousal_after"],
             em["moral_injury"], ps["valence_before"], ps["valence_after"], ps["moral_injury"]))
    d = R["G_dirty_work_offload"]
    print("OFFLOAD  self-evict owner injury=%.0f | hire-empathic MOVED bailiff=%.0f owner=%.0f | hire-psychopath ERASED bailiff=%.0f"
          % (d["self_case_owner_injury"], d["hire_empathic_MOVED"]["bailiff"],
             d["hire_empathic_MOVED"]["owner"], d["hire_psychopath_ERASED"]["bailiff_injury"]))
    for nm, p in d["market_pick"].items():
        print("         market: %-16s (empathy %.0f) picks evictor empathy=%.0f wage=%.0f"
              % (nm, p["owner_empathy"], p["picked_evictor_empathy"], p["picked_ask_wage"]))
    print("         BANALITY (every eviction lands on w=0 hands)=%s" % d["banality"])
    r = R["G_ethics_restore"]
    print("ETHICS   induced homeless=%d injury=%d -> RESTORED homeless=%d evicted=%d (clean=%s)"
          % (r["induced"]["tenant_homeless"], r["induced"]["doer_injury"],
             r["restored"]["tenant_homeless"], r["restored"]["evicted"], r["clean"]))
    print("\nwrote", os.path.join(OUT, "summary.json"))
    return R


if __name__ == "__main__":
    main()
