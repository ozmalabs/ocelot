"""jabberwock_running_session_acts — the RUNNING loop FIXES a reopened deferred gap.

The demo: the jabberwock defers a gap by sufficiency, re-measures its salience high,
REOPENS it (pass-through into the live session), and then the RUNNING loop's
fire_reflexes trips the seeded `reopened_concern_pursue` reflex whose executor RUNS
THE REAL REPAIR — the DEFECT IS CLEANED in the live loop, not the batch queue:

  · a reopened UNDERSTANDING gap has its clause fragment DROPPED (nominal_filter
    authored + applied), and
  · a reopened EFFICIENCY gap has warm_once APPLIED (WordNet resident),

and the concern is RESOLVED (closed) IFF the driver's fix #2-verifies. The executor
mirrors _question_pursue_advance: it recovers the gap the concern targets, dispatches
it to the kind-keyed driver (gap_prioritization._DRIVER_REGISTRY), and reads the #2
boolean — no Python branch decides the repair.

Run:  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_running_session_acts.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _agent():
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    from domains import load_timing as lt
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    t = lt.LoadTimer(a)
    t.record("read_source", 40.0, article="A1")
    t.record("ground_lexeme", 1400.0, article="A1", n_items=20, phase="cold")
    t.record("ground_lexeme", 0.4 * 20, article="A2", n_items=20, phase="warm")
    return a


def _rule(title):
    print("\n" + title)
    print("-" * len(title))


def understanding_demo():
    from domains import gap_prioritization as gp
    from domains import stopping_policy as sp
    from domains import issue_reopen as ir
    from domains import understanding_self_improvement as usi
    from domains import consumption_quality as cq

    _rule("UNDERSTANDING — a deferred fragment gap is REOPENED and CLEANED in the live loop")
    a = _agent()
    agenda = gp.perceive_gaps(a)
    gp.normalize_all(a, agenda)
    for g in [x for x in agenda if gp.gap_salience(a, x)[0] == "understanding"]:
        a.s.set_attr(g, "salience", 0.2)
    gp.normalize_all(a, agenda)
    sp.set_sufficiency_threshold(a, 0.5)
    ir.set_reopen_threshold(a, 0.7)
    _led, left = gp.enact_in_order_with_stopping(a, gp.prioritize(a, agenda))
    print(f"  scheduling STOPPED by sufficiency -> {len(left)} gaps DEFERRED (unfixed)")

    g = next(x for x in left if usi.gap_error_features(a, x) == (0.0, 1.0))
    print(f"  deferred understanding gap: features(head_is_nominal, sense_fits)="
          f"{usi.gap_error_features(a, g)} — a non-nominal fragment leak")

    a.s.set_attr(g, "salience", 0.9)
    ir.remeasure_salience(a, g)
    print(f"  re-measured norm_salience={round(a.s.node(g)['attrs']['norm_salience'], 3)}"
          f" > reopen bar {ir.reopen_threshold(a)} -> should_reopen={ir.should_reopen(a, g)}")

    concern = ir.reopen_deferred(a, left)["concerns"][0]
    print(f"  PASS-THROUGH: open concerns before firing = {len(ir.open_concerns(a))}")

    print("  >> RUNNING LOOP: a.fire_reflexes() ...")
    fired = a.fire_reflexes()
    print(f"     fired: {fired}")
    print(f"     concern pursued={a.s.node(concern)['attrs'].get('pursued')} "
          f"resolved={a.s.node(concern)['attrs'].get('resolved')} "
          f"| gap fixed={a.s.node(g)['attrs'].get('fixed')}")

    kept, dropped = cq.nominal_filter(
        [{"surface": usi.FRAGMENT_SURFACE}, {"surface": usi.NOMINAL_SURFACE}], agent=a)
    ks = [c.get("surface") if isinstance(c, dict) else c for c in kept]
    ds = [c.get("surface") if isinstance(c, dict) else c for c in dropped]
    print(f"     REAL DEFECT-CLEANING: dropped={ds}  kept={ks}")
    print(f"     inbox: open={len(ir.open_concerns(a))} resolved={len(ir.resolved_concerns(a))}")
    ok = (usi.FRAGMENT_SURFACE in ds and usi.FRAGMENT_SURFACE not in ks
          and a.s.node(concern)["attrs"].get("resolved") == 1.0)
    print(f"     => deferred -> reopened -> FIXED via the running loop: {ok}")
    return ok


def efficiency_demo():
    from domains import gap_prioritization as gp
    from domains import issue_reopen as ir
    from domains import performance_self_improvement as psi
    from domains import dictionary_lexicon as dl

    _rule("EFFICIENCY — a reopened one-time-init gap has warm_once APPLIED in the live loop")
    a = _agent()
    pg = psi.perceive_performance_gap(a)["gap"]
    gp.normalize_salience(a, pg)
    print(f"  perf gap kind={a.s.node(pg)['attrs'].get('kind')} | WordNet warm before={dl.is_wordnet_warm()}")
    concern = ir.reopen(a, pg)
    print(f"  PASS-THROUGH: open concerns before firing = {len(ir.open_concerns(a))}")

    print("  >> RUNNING LOOP: a.fire_reflexes() ...")
    fired = a.fire_reflexes()
    print(f"     fired: {fired}")
    print(f"     concern resolved={a.s.node(concern)['attrs'].get('resolved')} "
          f"| gap fixed={a.s.node(pg)['attrs'].get('fixed')} "
          f"| WordNet warm after={dl.is_wordnet_warm()}")
    ok = dl.is_wordnet_warm() and a.s.node(concern)["attrs"].get("resolved") == 1.0
    print(f"     => reopened EFFICIENCY gap warm_once APPLIED (WordNet resident): {ok}")
    return ok


def discriminative_demo():
    from domains import issue_reopen as ir

    _rule("DISCRIMINATIVE — still-deferred is NOT fixed; a failed-#2 fix does NOT resolve")
    # (1) still-deferred: never reopened -> no concern -> the running loop does nothing.
    a = _agent()
    from domains import gap_prioritization as gp
    from domains import stopping_policy as sp
    agenda = gp.perceive_gaps(a)
    gp.normalize_all(a, agenda)
    for g in [x for x in agenda if gp.gap_salience(a, x)[0] == "understanding"]:
        a.s.set_attr(g, "salience", 0.2)
    gp.normalize_all(a, agenda)
    sp.set_sufficiency_threshold(a, 0.5)
    ir.set_reopen_threshold(a, 0.7)
    _led, left = gp.enact_in_order_with_stopping(a, gp.prioritize(a, agenda))
    h = left[0]
    fired = a.fire_reflexes()
    print(f"  still-deferred gap (salience 0.2 < reopen bar): fired={fired} "
          f"active_concerns={len(ir.active_concerns(a))} gap fixed={a.s.node(h)['attrs'].get('fixed', 0.0)}")
    c1 = (ir.REOPEN_REFLEX not in fired and float(a.s.node(h)["attrs"].get("fixed", 0.0)) == 0.0)

    # (2) failed-#2: a reopened clean gap (no defect) -> fix not accepted -> stays OPEN.
    b = _agent()
    clean = b.s.add_node("CapabilityGap", {
        "kind": "understanding", "faculty": "clean_faculty",
        "head_is_nominal": 1.0, "sense_fits_context": 1.0,
        "salience": 0.9, "norm_salience": 0.9})
    concern = ir.reopen(b, clean)
    fired2 = b.fire_reflexes()
    print(f"  reopened CLEAN gap (no defect): fired={fired2} "
          f"resolved={b.s.node(concern)['attrs'].get('resolved')} "
          f"stays open={concern in ir.open_concerns(b)}")
    c2 = (b.s.node(concern)["attrs"].get("resolved") is None and concern in ir.open_concerns(b))
    print(f"     => still-deferred not fixed: {c1} | failed-#2 stays open: {c2}")
    return c1 and c2


def main():
    try:
        import substrate_rs  # noqa: F401
    except Exception:
        print("substrate_rs not available — skipping demo")
        return
    print("=" * 74)
    print("THE RUNNING SESSION ACTS — reopened deferred gaps are FIXED in the live loop")
    print("=" * 74)
    r1 = understanding_demo()
    r2 = efficiency_demo()
    r3 = discriminative_demo()
    _rule("LEDGER")
    print(f"  understanding reopened-gap CLEANED in the live loop : {r1}")
    print(f"  efficiency   reopened-gap warm_once in the live loop: {r2}")
    print(f"  discriminative controls (deferred/failed-#2) hold   : {r3}")
    print(f"\n  ALL: {r1 and r2 and r3}")


if __name__ == "__main__":
    main()
