"""ORDER-N ESCALATION IS DOMAIN-AGNOSTIC + CONFIDENCE-DRIVEN — proof on TOY abstract worlds.

Boots ONLY the generic cognition stack (autonomy + investigation_loop + investigation_teacher
+ impasse_escalation) over ABSTRACT domains (nonsense-key axes, no-op operators). NO speech /
chess / vision code. Two scenarios:

  A. NOTHING WORKS (a FakeWorld that always measures 0.0): the agent climbs the ladder under
     sustained low confidence — order2 change-method, order3 reframe, order4 AUTHOR A NEW TOOL
     (the self-extend reflex), order5 re-prioritise, order6 RETHINK THE SELF APPROACH.

  B. A REVISION WORKS (method_two measures well): the agent changes method at order2, sees
     confidence rise (saturation), and STOPS — it does NOT climb further. The climb is driven
     by CONFIDENCE (saturation), not a timer.

If this runs on toy worlds, the ladder applies to everything.

Run:
  cd experiments/gamma-substrate
  ulimit -v 12582912
  PYTHONPATH=.:runners/dsl/python \\
    /home/matt/ozma/internal/research/.venv/bin/python -m scripts.escalation_domain_agnostic
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from substrate.world_adapter import WorldAdapter
from substrate.seed_loader import manifest_for
from domains.gap_prioritiser import record_measured_capability

SEP = "=" * 80
SEEDS = ["enact", "discourse", "autonomy", "investigation_loop",
         "investigation_teacher", "impasse_escalation"]


class ToyWorld:
    """Domain-agnostic stand-in executor. `winners` = runner names that measure well; every
    other runner measures 0.0 (stalls). With winners=() nothing ever works."""

    def __init__(self, substrate, winners=()):
        self.s = substrate
        self.winners = set(winners)

    def execute(self, req):
        m = 0.9 if req.get("operator") in self.winners else 0.0
        return record_measured_capability(
            self.s, req.get("capability_keys", ["toy"]),
            measured=m, target=req.get("target", 0.6),
            metric=req.get("measurement_key", "toy_metric"), note=f"toy runner={req.get('operator')}")


def _prod(s, a, e, b):
    try:
        s.add_production({"src": {"type": a, "var": "x"}, "edge_type": e,
                          "tgt": {"type": b, "var": "y"}, "where": None,
                          "weight": {"type": "Lit", "value": 1.0}, "provenance": "toy"})
    except Exception:
        pass


def build(winners=()):
    adapter = WorldAdapter()
    for sid in SEEDS:
        adapter.inner.load_seed_manifest(manifest_for(sid), adapter.agent)
    s = adapter.s
    _prod(s, "Operator", "applies_in", "Microtheory")
    _prod(s, "CapabilityAxis", "investigated_by", "Operator")
    mt = s.add_node("Microtheory", {"name": "toy_world", "domain": "abstract"})
    op1 = s.add_node("Operator", {"name": "method_one", "runner": "m1", "metric": "toy_metric", "target": 0.6})
    op2 = s.add_node("Operator", {"name": "method_two", "runner": "m2", "metric": "toy_metric", "target": 0.6})
    s.add_edge(op1, "applies_in", mt)
    s.add_edge(op2, "applies_in", mt)
    ax = s.add_node("CapabilityAxis", {"is_axis": 1.0, "capability_keys": ["alpha"],
                                       "saturation": 0.0, "shortfall": 0.7, "min_order": 1.0,
                                       "investigated_count": 0, "mf_stall": 0})
    s.add_edge(ax, "investigated_by", op1)
    s.add_edge(adapter.agent, "operates_in", mt)
    world = ToyWorld(s, winners=winners)
    adapter.wire_autonomy_faculty(); adapter.wire_enact_faculty()
    adapter.wire_investigation_faculty(world)
    adapter.wire_teacher_resolution()
    adapter.wire_escalation_faculties()
    adapter.set_self_teacher(lambda q: "a contrastive sub-band onset detector")
    return adapter, ax


def _order(adapter):
    o = 0
    for mi in adapter.s.nodes("Impasse"):
        a = adapter.s.node(mi)["attrs"]
        if a.get("kind") in ("escalation", "self_extend", "self_rethink") and a.get("order"):
            o = max(o, int(a["order"]))
    return o


def scenario_climb():
    print("  SCENARIO A — nothing works: climb the whole ladder under low confidence.")
    adapter, ax = build(winners=())
    seen, reached6 = set(), None
    for t in range(1, 161):
        adapter.master_tick(); adapter.tick()
        o = _order(adapter)
        if o and o not in seen:
            seen.add(o)
            label = {2: "change METHOD", 3: "reframe (decompose)", 4: "author a TOOL",
                     5: "re-prioritise", 6: "RETHINK SELF"}.get(o, "")
            print(f"    [tick {t:3d}] reached ORDER {o} — {label}")
        if o >= 6 and reached6 is None:
            reached6 = t
        if reached6 is not None and t >= reached6 + 8:   # let order-6 act + the rethink reflex fire
            break
    authored = [n for n in adapter.s.nodes("Operator")
                if adapter.s.node(n)["attrs"].get("authored_by_escalation") == 1.0]
    reassessed = adapter.inner.neighbours(adapter.agent, "reassessed")
    rethink = adapter.s.node(adapter.agent)["attrs"].get("rethink_self") == 1.0
    print(f"    -> tools authored by escalation: {len(authored)}; self-reassessments: {len(reassessed)}; "
          f"rethink_self flag: {rethink}")
    return {"max_order": max(seen) if seen else 0, "authored": len(authored),
            "rethink": rethink and len(reassessed) >= 1}


def scenario_confidence():
    print("\n  SCENARIO B — method_two works: change method, confidence rises, STOP (no further climb).")
    adapter, ax = build(winners=("m2",))
    settled, max_order = None, 0
    for t in range(1, 61):
        adapter.master_tick(); adapter.tick()
        max_order = max(max_order, _order(adapter))
        resolved = [n for n in adapter.s.nodes("Impasse")
                    if adapter.s.node(n)["attrs"].get("kind") == "escalation"
                    and adapter.s.node(n)["attrs"].get("resolved") is True
                    and adapter.s.node(n)["attrs"].get("outcome") == "approach_changed_and_worked"]
        if resolved and settled is None:
            settled = t
            sat = adapter.s.node(ax)["attrs"].get("saturation")
            print(f"    [tick {t:2d}] escalation RESOLVED at order {max_order} "
                  f"(saturation={sat}) — the change of method worked; did NOT climb further.")
            break
    return {"resolved": settled is not None, "max_order": max_order}


def scenario_authored_works():
    print("\n  SCENARIO C — only an AUTHORED tool works: climb to order-4, author it, it RUNS and resolves.")
    adapter, ax = build(winners=("authored",))   # m1/m2 fail; the order-4 authored tool succeeds
    settled, max_order = None, 0
    for t in range(1, 81):
        adapter.master_tick(); adapter.tick()
        max_order = max(max_order, _order(adapter))
        resolved = [n for n in adapter.s.nodes("Impasse")
                    if adapter.s.node(n)["attrs"].get("outcome") == "approach_changed_and_worked"]
        authored = [n for n in adapter.s.nodes("Operator")
                    if adapter.s.node(n)["attrs"].get("authored_by_escalation") == 1.0]
        if resolved and authored and settled is None:
            settled = t
            print(f"    [tick {t:2d}] authored tool ran and WORKED -> escalation resolved at order {max_order}")
            break
    bound_authored = any(adapter.s.node(o)["attrs"].get("authored_by_escalation") == 1.0
                         for o in adapter.inner.neighbours(ax, "investigated_by"))
    return {"resolved": settled is not None, "max_order": max_order, "bound_authored": bound_authored}


def main():
    print(SEP)
    print("ORDER-N ESCALATION — domain-agnostic + confidence-driven (toy worlds, NO domain code).")
    print(SEP)
    a = scenario_climb()
    b = scenario_confidence()
    c = scenario_authored_works()
    print(f"\n{SEP}")
    ok_climb = a["max_order"] >= 6 and a["authored"] >= 1 and a["rethink"]
    ok_conf = b["resolved"] and b["max_order"] == 2
    ok_auth = c["resolved"] and c["max_order"] == 4 and c["bound_authored"]
    print(f"  A climb-to-self-rethink   : max_order={a['max_order']} (want 6), tools={a['authored']}, "
          f"rethink={a['rethink']}  -> {ok_climb}")
    print(f"  B confidence-stop         : resolved={b['resolved']}, max_order={b['max_order']} (want 2)  -> {ok_conf}")
    print(f"  C authored-tool-works     : resolved={c['resolved']}, max_order={c['max_order']} (want 4), "
          f"bound_to_authored={c['bound_authored']}  -> {ok_auth}")
    ok = ok_climb and ok_conf and ok_auth
    print(f"  {'PASS' if ok else 'FAIL'} — the ladder climbs to rethinking-self when nothing works, STOPS when a "
          f"revision works, and an AUTHORED order-4 tool actually RUNS and resolves. Domain-agnostic.")
    print(SEP)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
