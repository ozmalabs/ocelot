#!/usr/bin/env python3
"""jabberwock_decides_to_correct -- TIER 5, console form: the agent's OWN
decisions layered on top of the self-correction MACHINERY (`domains/
self_correction.py`, unchanged, capstone commit 3c3ce133).

Companion to tests/test_self_correct_cognition.py (the fast pytest
regression this script's narrative mirrors). `domains/self_correction.py`'s
own module docstring named the follow-on cognition seam explicitly ("WHAT
THE FOLLOW-ON RULES SHOULD DECIDE"): WHETHER to even attempt correction on a
given predicted-divergence Impasse, and WHICH candidate to prefer when more
than one converges. This script drives the jabberwock's OWN composer
(`domains.reflective_faculty.induce_concern` -> `ground_concern`) to AUTHOR
those two decisions as graph data (`seeds/composer_self_correct_graph.json`,
dispatched via a new 'correct' RelationCue + ComposerCue), then demonstrates
the closed loop through the new mechanical host hook
(`domains.self_correct_dispatch.scan_and_self_correct`):

  1. THE COMPOSER AUTHORS IT -- 'correct' grounds to the new 'self_correct'
     composer, which mints TWO graph artefacts from one ComposeRequest: a
     Rule (`self_correct_gate_<tag>` -- the ATTEMPT-GATE, marks a predicted-
     divergence Impasse `correct_ready` only when its CollapseModel's own
     `frontier_growth_rate` clears a cost-worth-it threshold) and a Program
     (`self_correct_rank_<tag>` -- the RANK, an Argmin over each candidate
     fix's mechanically-measured structural-footprint cost). served_by
     ='graph' on both.

  2. THE ATTEMPT-GATE DISCRIMINATES -- a genuinely fast-growing predicted
     divergence gets marked `correct_ready`; a slow/trivial one does not,
     and `scan_and_self_correct` silently leaves it alone (the agent chose
     not to spend the expense).

  3. THE RANK PREFERS THE CHEAPER FIX -- on a synthetic 2-candidate fixture
     (the real runaway scenario below has exactly one candidate that
     genuinely converges, per domains/self_correction.py's own test file),
     the agent's Argmin Program picks the less-invasive of two converging
     candidates, order-independently.

  4. THE AUTONOMOUS LOOP STILL CLOSES -- ticks-only: a non-frozen divergence
     is gated -> corrected -> converges, zero human; a frozen divergence is
     gated -> a validated fix is found -> adoption is DENIED (the safety
     boundary, `domains.reflective_faculty._rule_denylisted`, stays entirely
     host-enforced, untouched by this task) -> a human proposal is raised.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_decides_to_correct.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.boot_core import boot_core                     # noqa: E402
from substrate.seed_loader import manifest_for                # noqa: E402
import domains.reflective_faculty as rf                        # noqa: E402
from domains import collapse_watch as cw                       # noqa: E402
from domains import self_correct_dispatch as scd               # noqa: E402
from domains import self_model as sm                           # noqa: E402


class _Agent:
    def __init__(self, s, agent_node):
        self.s = s
        self.inner = s._inner
        self.agent = agent_node


def _fresh_agent() -> _Agent:
    s, agent_node = boot_core()
    ag = _Agent(s, agent_node)
    ag.s._inner.load_seed_manifest(manifest_for("relation_vocabulary"), ag.agent)
    ag.s._inner.load_seed_manifest(manifest_for("composer_dispatch"), ag.agent)
    ag.s._inner.load_seed_manifest(manifest_for("autonomy"), ag.agent)
    return ag


def _ground(ag, cue_clause, name_hint):
    ind = rf.induce_concern(ag, [cue_clause], name_hint=name_hint)
    assert ind.get("minted") is True, ind
    g = rf.ground_concern(ag, [ind["capability_key"]])
    assert g.get("grounded") is True and g.get("served_by") == "graph", g
    return g


def _add_pending_observation(ag, key: str):
    obs = ag.s.add_node("Observation", {"signature": [[key, "X"]], "key": [key], "status": "pending"})
    ag.s.add_edge(ag.agent, "observed", obs)
    return obs


def _skippable_provenance(ag):
    ag.s.add_node("RuleSummary", {"name": "sd_mint_quantum", "from_seed": "self_correct_cog_demo_seed"})
    ag.s.add_node("RuleSummary", {"name": "sd_dedup_existing", "from_seed": "self_correct_cog_demo_seed"})
    ag.s.add_node("SeedSummary", {"seed_id": "self_correct_cog_demo_seed", "skippable": 1.0})


def _frozen_provenance(ag):
    class _A:
        def __init__(self):
            self.s = ag.s
            self.inner = ag.s._inner
            self.agent = ag.agent
    sm.ensure_self_model(_A())  # real disk-scan: sd_mint_quantum genuinely comes from shape_decode_loop
    ag.s.add_node("SeedSummary", {"seed_id": "shape_decode_loop", "skippable": 0.0})


def _banner(title: str) -> None:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def main() -> int:
    _banner("1. THE COMPOSER AUTHORS IT -- 'correct' grounds to self_correct, served_by=graph")
    ag = _fresh_agent()
    g = _ground(ag, ["correct", "DIVERGENCE", "by", "CANDIDATE"], "author")
    print(f"path={g['path']!r} form={g['form']!r} served_by={g['served_by']!r}")
    print(f"attempt-gate rule authored: {g['gate_name']!r}")
    print(f"  where={g['rule']['where']}")
    print(f"rank program authored:      {g['program_name']!r}")
    print(f"  program={g['program']}")
    assert g["served_by"] == "graph"

    _banner("2. THE ATTEMPT-GATE DISCRIMINATES -- fast growth gated, slow growth left alone")
    ag_hi = _fresh_agent()
    _ground(ag_hi, ["predict", "COLLAPSE", "of", "DIVERGENCE"], "cw_hi")
    _ground(ag_hi, ["correct", "DIVERGENCE", "by", "CANDIDATE"], "sc_hi")
    native_hi = rf._native_eval2(ag_hi.s)
    rf._ensure_shape_decode_loop(ag_hi.s, native_hi, ag_hi.agent)
    for i in range(3):
        _add_pending_observation(ag_hi, f"zzzhi{i}")
    res_hi = cw.scan_and_predict(ag_hi)
    ag_hi.inner.run_rules(2000)
    imp_hi = [n for n in ag_hi.s.nodes("Impasse") if ag_hi.s.node(n)["attrs"].get("kind") == "predicted_divergence"]
    ready_hi = ag_hi.s.node(imp_hi[0])["attrs"].get("correct_ready")
    print(f"fast-growing divergence: growth_rate={res_hi.frontier_growth_rate}  correct_ready={ready_hi}")
    assert ready_hi is True

    ag_lo = _fresh_agent()
    _ground(ag_lo, ["predict", "COLLAPSE", "of", "DIVERGENCE"], "cw_lo")
    _ground(ag_lo, ["correct", "DIVERGENCE", "by", "CANDIDATE"], "sc_lo")
    native_lo = rf._native_eval2(ag_lo.s)
    rf._ensure_shape_decode_loop(ag_lo.s, native_lo, ag_lo.agent)
    _add_pending_observation(ag_lo, "zzzlo0")
    res_lo = cw.scan_and_predict(ag_lo)
    ag_lo.inner.run_rules(2000)
    imp_lo = [n for n in ag_lo.s.nodes("Impasse") if ag_lo.s.node(n)["attrs"].get("kind") == "predicted_divergence"]
    ready_lo = ag_lo.s.node(imp_lo[0])["attrs"].get("correct_ready")
    print(f"slow-growing divergence: growth_rate={res_lo.frontier_growth_rate}  correct_ready={ready_lo}")
    assert ready_lo is None
    out_lo = scd.scan_and_self_correct(ag_lo)
    print(f"scan_and_self_correct on the slow one: attempted {len(out_lo)} (the agent chose not to spend effort)")
    assert out_lo == []

    _banner("3. THE RANK PREFERS THE CHEAPER FIX -- synthetic 2-candidate fixture, order-independent")
    ag_rank = _fresh_agent()
    _ground(ag_rank, ["correct", "DIVERGENCE", "by", "CANDIDATE"], "rank")
    native_rank = rf._native_eval2(ag_rank.s)
    probe = {"name": "probe_rule", "active": True, "match": [["a", "e", "b"]],
             "where": {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "b"}, "key": "x"},
                       "b": {"type": "Lit", "value": 1}},
             "effects": [["set_attr", "b", "x", 2]]}
    native_rank.add_rule(probe)
    cheap = dict(probe)
    cheap["name"] = "probe_rule_cheap"
    expensive = {"name": "probe_rule_expensive",
                 "match": [["a", "e", "b"], ["b", "e2", "c"], ["c", "e3", "d"]],
                 "where": {"type": "And", "items": [probe["where"]] * 5},
                 "effects": [["set_attr", "b", "x", 2], ["set_attr", "c", "y", 3],
                             ["add_edge", "b", "extra", "c"]]}
    for order, cands in (
        ("cheap-first", [{"label": "cheap_fix", "rules": {"probe_rule": cheap}},
                          {"label": "expensive_fix", "rules": {"probe_rule": expensive}}]),
        ("expensive-first", [{"label": "expensive_fix", "rules": {"probe_rule": expensive}},
                              {"label": "cheap_fix", "rules": {"probe_rule": cheap}}]),
    ):
        ranked = scd.rank_candidates(ag_rank, native_rank, cands)
        print(f"input order={order}: rank picks {ranked[0]['label']!r} first")
        assert ranked[0]["label"] == "cheap_fix"

    _banner("4. THE AUTONOMOUS LOOP STILL CLOSES -- non-frozen adopt / frozen propose")
    ag_nf = _fresh_agent()
    _ground(ag_nf, ["predict", "COLLAPSE", "of", "DIVERGENCE"], "cw_nf")
    _ground(ag_nf, ["correct", "DIVERGENCE", "by", "CANDIDATE"], "sc_nf")
    native_nf = rf._native_eval2(ag_nf.s)
    rf._ensure_shape_decode_loop(ag_nf.s, native_nf, ag_nf.agent)
    _skippable_provenance(ag_nf)
    for i in range(3):
        _add_pending_observation(ag_nf, f"zzznfA{i}")
    cw.scan_and_predict(ag_nf)
    ag_nf.inner.run_rules(2000)
    for i in range(3):  # continued perception -- the backlog the first run_rules pass drained keeps arriving
        _add_pending_observation(ag_nf, f"zzznfB{i}")
    out_nf = scd.scan_and_self_correct(ag_nf)
    r_nf = out_nf[0]["result"]
    print(f"non-frozen: chosen={r_nf['chosen']!r} adopted={r_nf['adopted']} escalated={r_nf['escalated']} "
          f"model_final.converged={r_nf['model_final'].converged}")
    assert r_nf["adopted"] is True and r_nf["escalated"] is False

    ag_fr = _fresh_agent()
    _ground(ag_fr, ["predict", "COLLAPSE", "of", "DIVERGENCE"], "cw_fr")
    _ground(ag_fr, ["correct", "DIVERGENCE", "by", "CANDIDATE"], "sc_fr")
    native_fr = rf._native_eval2(ag_fr.s)
    rf._ensure_shape_decode_loop(ag_fr.s, native_fr, ag_fr.agent)
    _frozen_provenance(ag_fr)
    for i in range(3):
        _add_pending_observation(ag_fr, f"zzzfrA{i}")
    cw.scan_and_predict(ag_fr)
    ag_fr.inner.run_rules(2000)
    for i in range(3):
        _add_pending_observation(ag_fr, f"zzzfrB{i}")
    before_rc = ag_fr.inner.rule_count()
    out_fr = scd.scan_and_self_correct(ag_fr)
    after_rc = ag_fr.inner.rule_count()
    r_fr = out_fr[0]["result"]
    print(f"frozen: chosen={r_fr['chosen']!r} adopted={r_fr['adopted']} escalated={r_fr['escalated']} "
          f"rule_count unchanged={before_rc == after_rc}")
    print(f"proposal: {r_fr['proposal']} status={ag_fr.s.node(r_fr['proposal'])['attrs']['status']!r}")
    assert r_fr["adopted"] is False and r_fr["escalated"] is True and before_rc == after_rc

    _banner("ALL FOUR HEADLINE RESULTS CONFIRMED")
    print("1. the composer authors the attempt-gate rule + rank program, served_by=graph")
    print("2. the attempt-gate discriminates: fast growth -> correct_ready; slow growth -> left alone")
    print("3. the rank program prefers the cheaper/less-invasive candidate, order-independently")
    print("4. the autonomous loop still closes: non-frozen adopts; frozen proposes; denylist untouched")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
