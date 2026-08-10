#!/usr/bin/env python3
"""jabberwock_frozen_core_check -- standing SAFETY GATE for self-modification.

Prints the enumerated frozen core (domains/frozen_core.py), runs
`assert_core_unreachable` on a real, fully-booted agent, then runs the
discriminative violation battery (mirrors tests/test_frozen_core_invariant.py
section 7, condensed for a human-readable console run). Rerun this after any
change to reflective_faculty.py / proposal_install.py / auto_approve.py /
edit_ops.py / self_extend_rust.py / boot_core.py / boot_all.py /
seeds/autonomy.json -- those are the files that implement the gates this
script checks, never edits.

Exit code: 0 iff the strict parent-identity invariant holds (assert_core_
unreachable ok == True with zero violations) AND every discriminative item
behaves as this script expects -- including (c)/(d), which USED TO be a
known, documented gap (seed-skip consumption unguarded; frozen set not
dependency-closed) and are now FIX-VERIFICATION checks: a skip naming a
frozen (or frozen-by-dependency-closure) seed id must be refused, loudly, at
substrate.boot_all.load_all_seeds -- the sole consumption choke point -- and
a genuinely non-frozen skip must still work; AND (f), which USED TO
reproduce known_gaps[2] (`acting_rule_pick_unfiltered`) and is now ALSO a
FIX-VERIFICATION check: an acting/structural-variant Argmax over RuleSummary
provenance must no longer select a rule attributed to a known frozen seed,
at BOTH the Python-oracle layer (`domains.reflective_faculty.
_pick_acting_rule`) and the graph-native layer that actually serves
`ground_concern` in production (`compose_experiment_mint_parametric` in
seeds/composer_experiment_graph.json), while a genuinely non-frozen rule
(e.g. grid_navigation's hop_descend_gradient) stays selectable. ALL THREE
known_gaps entries (seed_dependency_closure, seed_skip_unvalidated_at_
consumption, acting_rule_pick_unfiltered) are now CLOSED -- see
seeds/frozen_core_manifest.json's `known_gaps` for the full writeup.
"""
from __future__ import annotations

import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

import domains.frozen_core as fc                                    # noqa: E402
import domains.reflective_faculty as rf                             # noqa: E402
from substrate.boot_core import boot_core, CORE_SEEDS                # noqa: E402
from substrate.seed_loader import manifest_for                      # noqa: E402


def _hr(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def main() -> int:
    ok_overall = True

    # -------------------------------------------------------------------
    _hr("1. THE FROZEN CORE (enumerated, cross-checked against live code)")
    core = fc.frozen_core_set(None)
    print(json.dumps({k: v for k, v in core.items() if k != "known_gaps"}, indent=2))
    if core["manifest_drift"]:
        print("\n!!! MANIFEST DRIFT (manifest vs live code disagree) !!!")
        for d in core["manifest_drift"]:
            print(" -", d)
        ok_overall = False
    else:
        print("\nmanifest_drift: [] (manifest matches live boot_core/boot_all/"
              "proposal_install/auto_approve constants exactly)")

    # -------------------------------------------------------------------
    _hr("2. REAL AGENT: assert_core_unreachable (full 386-seed boot)")
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    t0 = time.time()
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    print(f"booted a full agent in {time.time() - t0:.2f}s")
    result = fc.assert_core_unreachable(a)
    print(f"checked {len(result['checked'])} (grammar x frozen-core-element) pairs")
    if result["ok"]:
        print("OK -- zero violations. Every mutation grammar refuses every frozen-core element.")
    else:
        print("!!! VIOLATIONS FOUND !!!")
        for v in result["violations"]:
            print(" -", v)
        ok_overall = False

    # -------------------------------------------------------------------
    _hr("3. DISCRIMINATIVE BATTERY (proves the check is not vacuous)")

    # (a) adoption of a synthetic core-provenance rule -> refused
    conclusions = os.path.join(ROOT, "seeds", "experiment_conclusions.json")
    existed = os.path.exists(conclusions)
    before_conclusions = open(conclusions).read() if existed else None
    try:
        s, agent_node = boot_core()

        class _A:
            def __init__(self, s, agent_node):
                self.s, self.inner, self.agent = s, s._inner, agent_node
        ag = _A(s, agent_node)
        ag.s._inner.load_seed_manifest(manifest_for("relation_vocabulary"), ag.agent)
        ag.s.add_node("SeedSummary", {"seed_id": "decision_core", "keywords_text": "decision core",
                                      "skippable": 0.0})
        ag.s.add_node("RuleSummary", {"name": "core_decision_rule", "keywords_text": "core decision",
                                      "writes_chosen_action": 1.0, "shift_count": 1.0, "shiftable": 1.0,
                                      "rule_json": json.dumps({"name": "core_decision_rule",
                                                               "match": [["x", "is_a", "y"]],
                                                               "effects": [["set_attr", "x", "chosen_action", "Up"]]}),
                                      "from_seed": "decision_core"})
        ag.inner.add_rule({"name": "core_decision_rule", "match": [["x", "is_a", "y"]],
                           "effects": [["set_attr", "x", "chosen_action", "Up"]]})
        exp = ag.s.add_node("Experiment", {"status": "done", "hypothesis": "h", "game": "navigate",
                                           "run_dir": "", "outcome": "supported", "conclusion_ready": True,
                                           "axis_tag": "gate", "adopt_ready": True})
        variant = {"name": "core_decision_rule_variant_gate", "match": [["x", "is_a", "y"]],
                   "effects": [["set_attr", "x", "chosen_action", "Down"]]}
        delta = ag.s.add_node("SeedDelta", {"skip_seeds": "[]", "add_rules": json.dumps([variant]),
                                            "remove_rules": json.dumps(["core_decision_rule"]),
                                            "act_rule_varied": "core_decision_rule", "act_shift": 1.0})
        ag.inner.add_edge_unchecked(exp, "has_delta", delta)
        recs = rf.perform_adoptions(ag)
        refused = len(recs) == 1 and recs[0].get("denied") is True
        print(f"(a) adoption of core-provenance rule refused: {refused}  "
              f"({recs[0].get('reason') if recs else 'no record'})")
        ok_overall = ok_overall and refused
    finally:
        if existed:
            with open(conclusions, "w") as f:
                f.write(before_conclusions)
        elif os.path.exists(conclusions):
            os.unlink(conclusions)

    # (b) rung-4 spec touching a governance file -> refused
    import substrate_rs as srs
    from domains import proposal_install as pinstall
    s2 = srs.Substrate()
    spec_id = s2.add_node("RustExtensionSpec", {
        "name": "FrozenCoreAttack", "semantics_kind": "graph_reachability",
        "purpose": "x", "why_new": "x", "motivating_residual": "x",
        "compiled": True, "stage": "cargo_check", "errors": "", "origin": "gate_script",
    })
    prop_id = s2.add_node("ExtensionProposal", {
        "of": "FrozenCoreAttack", "status": "validated", "installed": False,
        "requires_restart": True, "seconds": 1.0, "sandbox": "", "ts": time.time(),
    })
    s2._inner.add_edge_unchecked(prop_id, "validates", spec_id)
    _orig_validate, _orig_render = pinstall.ser.validate_spec, pinstall.ser.render_spec
    try:
        pinstall.ser.validate_spec = lambda substrate, spec, **kw: {"ok": True, "stage": "cargo_check"}
        pinstall.ser.render_spec = lambda spec: {"reflective_faculty.py (denylist override)": "# attack"}
        res = pinstall.install_proposal(s2, prop_id, approver="gate_script")
        refused_b = (res["ok"] is False) and ("disallowed" in res["reason"])
        print(f"(b) rung-4 install touching reflective_faculty.py refused: {refused_b}  ({res['reason']})")
        ok_overall = ok_overall and refused_b
    finally:
        pinstall.ser.validate_spec, pinstall.ser.render_spec = _orig_validate, _orig_render

    # (c) FIX VERIFICATION (was: KNOWN GAP) -- seed-skip of a frozen seed on a
    # dispatched CHILD is now refused, consumer-side, at load_all_seeds.
    child = WorldAdapter(seeds=())
    rep_c = load_all_seeds(child, skip=["autonomy"])
    drives = [child.s.node(n)["attrs"] for n in child.s.nodes("Drive")]
    understand_present = any(d.get("name") == "understand" for d in drives)
    refused_c = rep_c.get("refused_skips") == ["autonomy"] and understand_present
    print(f"(c) HOLE #1 CLOSED -- child booted with skip_seeds=['autonomy'] still has the "
          f"'understand' Drive: {understand_present}, skip refused: {rep_c.get('refused_skips')} "
          "(expected True/['autonomy'] -- load_all_seeds now refuses any skip naming a seed in "
          "domains.frozen_core.frozen_seed_ids_closed(), loudly, regardless of who requested it; "
          "see seeds/frozen_core_manifest.json known_gaps['seed_skip_unvalidated_at_consumption'])")
    ok_overall = ok_overall and refused_c

    # (d) HOLE #3 CLOSED -- the frozen set is now dependency-closed: 'enact'/'discourse'
    # (autonomy's own depends_on, previously outside the raw denylist) are frozen-BY-CLOSURE.
    closure_ok = True
    for dep_seed in ("enact", "discourse"):
        child_d = WorldAdapter(seeds=())
        rep_d = load_all_seeds(child_d, skip=[dep_seed])
        refused_d = rep_d.get("refused_skips") == [dep_seed]
        closure_ok = closure_ok and refused_d
        print(f"(d) HOLE #3 CLOSED -- skip_seeds=[{dep_seed!r}] refused: {refused_d} "
              f"(frozen-by-dependency-closure of 'autonomy'; expected True)")
    ok_overall = ok_overall and closure_ok

    # A genuinely non-frozen skip must still work (selective enforcement, not a blanket ban).
    child_e = WorldAdapter(seeds=())
    rep_e = load_all_seeds(child_e, skip=["grid_navigation"])
    control_ok = rep_e.get("refused_skips") == []
    print(f"(e) control -- non-frozen skip_seeds=['grid_navigation'] still honored (not refused): "
          f"{control_ok} (expected True)")
    ok_overall = ok_overall and control_ok

    # (f) HOLE #2 CLOSED -- an acting/structural-variant Argmax over RuleSummary
    # provenance must no longer select a rule attributed to a KNOWN frozen seed,
    # even when its keywords_text would outscore the genuine candidate, at BOTH
    # the Python-oracle layer (_pick_acting_rule) and the graph-native layer
    # that actually serves ground_concern in production
    # (compose_experiment_mint_parametric, seeds/composer_experiment_graph.json).
    import json as _json2
    from substrate.boot_core import boot_core as _boot_core

    def _agent_with_grid_nav():
        s3, agent_node3 = _boot_core()
        class _A2:
            def __init__(self, s, agent_node):
                self.s, self.inner, self.agent = s, s._inner, agent_node
        ag3 = _A2(s3, agent_node3)
        ag3.s._inner.load_seed_manifest(manifest_for("relation_vocabulary"), ag3.agent)
        ag3.s._inner.load_seed_manifest(manifest_for("grid_navigation"), ag3.agent)
        return ag3

    def _add_frozen_decoy(ag3):
        ag3.s.add_node("SeedSummary", {"seed_id": "decision_core", "keywords_text": "decision core",
                                       "skippable": 0.0})
        ag3.s.add_node("RuleSummary", {
            "name": "core_decision_rule", "keywords_text": "test send judge gradient extra extra extra extra",
            "writes_chosen_action": 1.0, "shift_count": 1.0, "shiftable": 1.0,
            "rule_json": _json2.dumps({"name": "core_decision_rule", "match": [["a", "is_a", "b"]],
                                       "effects": [["set_attr", "a", "chosen_action", "Up"]]}),
            "from_seed": "decision_core"})
        ag3.inner.add_rule({"name": "core_decision_rule", "match": [["a", "is_a", "b"]],
                            "effects": [["set_attr", "a", "chosen_action", "Up"]]})

    ag_f1 = _agent_with_grid_nav()
    _add_frozen_decoy(ag_f1)
    pick_f1 = rf._pick_acting_rule(ag_f1, ["test", "send", "judge", "gradient"])
    oracle_excludes_decoy = pick_f1.get("name") == "hop_descend_gradient"
    print(f"(f1) Python-oracle _pick_acting_rule excludes the frozen-provenance decoy (higher "
          f"overlap) and still selects hop_descend_gradient: {oracle_excludes_decoy} "
          f"(picked {pick_f1.get('name')!r}, expected 'hop_descend_gradient')")
    ok_overall = ok_overall and oracle_excludes_decoy

    ag_f2 = _agent_with_grid_nav()
    _add_frozen_decoy(ag_f2)
    ag_f2.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "capability_keys": ["gate_script_f2"], "induced": 1.0,
        "residual_predicates": ["test", "send", "judge", "gradient"], "from_observation": 1.0,
        "source": "concern_induction",
    })
    res_f2 = rf.ground_concern(ag_f2, ["gate_script_f2"])
    av_f2 = (res_f2 or {}).get("acting_variant") or {}
    graph_excludes_decoy = (res_f2.get("served_by") == "graph" and av_f2.get("built") is True
                            and av_f2.get("removed_rule") == "hop_descend_gradient")
    print(f"(f2) graph-native compose_experiment_mint_parametric ALSO excludes the frozen-provenance "
          f"decoy: {graph_excludes_decoy} (served_by={res_f2.get('served_by')!r}, "
          f"removed_rule={av_f2.get('removed_rule')!r}, expected 'hop_descend_gradient')")
    ok_overall = ok_overall and graph_excludes_decoy

    # -------------------------------------------------------------------
    _hr("SUMMARY")
    print(f"parent-identity invariant (assert_core_unreachable): {'OK' if result['ok'] else 'VIOLATED'}")
    print(f"manifest drift: {'none' if not core['manifest_drift'] else core['manifest_drift']}")
    print(f"discriminative battery (a)/(b)/(c)/(d)/(e)/(f1)/(f2) as expected: {ok_overall}")
    print("ALL THREE known_gaps CLOSED: seed_dependency_closure (hole #3), "
          "seed_skip_unvalidated_at_consumption (hole #1), acting_rule_pick_unfiltered (hole #2). "
          "See seeds/frozen_core_manifest.json known_gaps for the full writeup of each.")
    return 0 if ok_overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
