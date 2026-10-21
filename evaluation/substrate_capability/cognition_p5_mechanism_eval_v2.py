#!/usr/bin/env python3
"""Second, adapter-backed P5 evaluation protocol; all outcomes come from mechanisms."""
from __future__ import annotations

import hashlib
import json
import os
import random
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for entry in (ROOT, ROOT / "runners" / "dsl" / "python"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

PROTOCOL = "cognition_p5_mechanism_eval_v2"
N_PRIMARY, N_CONTROL = 200, 100
ITEM_ARMS = {
    "F1": ("shared_view_on", "shared_view_off"),
    "F2": ("recursive_rules_on", "recursive_rules_off"),
    "G2": ("reappraisal_on", "reappraisal_off"),
    "G3": ("inhibition_on", "inhibition_off"),
    "E3": ("scm_do_query", "conditioning_only"),
    "E4": ("planner", "one_step"),
    "A2": ("completion_on", "completion_off"),
    "D6": ("buffered_incremental", "direct_exact"),
}
FROZEN = (
    "docs/research/engine_substrate/COGNITION_BUILD_P5_ADAPTERS_PREREG.md",
    "docs/research/engine_substrate/COGNITION_BUILD_P5_PREREG.md",
    "docs/research/engine_substrate/COGNITION_BUILD_P5_FACULTY_DEPTH_PLAN.md",
    "evaluation/substrate_capability/cognition_p5_mechanism_eval_v2.py",
    "evaluation/substrate_capability/cognition_p5_mechanism_analysis_v2.py",
    "evaluation/substrate_capability/cognition_p5_heldout_v1.py",
    "evaluation/substrate_capability/cognition_p5_analysis_v1.py",
    "scripts/gen_tom_unified_view_seed.py", "seeds/tom_unified_view.json",
    "scripts/gen_recursive_tom_seed.py", "seeds/recursive_tom.json",
    "scripts/gen_reappraisal_seed.py", "seeds/reappraisal.json",
    "scripts/gen_response_inhibition_seed.py", "seeds/response_inhibition.json",
    "scripts/gen_scm_reasoning_seed.py", "seeds/scm_reasoning.json",
    "scripts/gen_cognition_planner_seed.py", "seeds/cognition_planner.json",
    "scripts/gen_decomposition_completion_seed.py", "seeds/decomposition_completion.json",
    "scripts/gen_analog_imagery_seed.py", "seeds/analog_imagery.json",
    "tests/test_tom_unified_view_migrated.py", "tests/test_recursive_tom_migrated.py",
    "tests/test_reappraisal_migrated.py", "tests/test_response_inhibition_migrated.py",
    "tests/test_scm_intervention_migrated.py", "tests/test_cognition_multistep_planner_migrated.py",
    "tests/test_decomposition_completion_migrated.py", "tests/test_analog_imagery_migrated.py",
    "runners/dsl/python/substrate_rs/_native.abi3.so",
    "runners/dsl/python/substrate_rs/_native.build.json",
)


def _git(*args):
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    if result.returncode:
        raise ValueError(result.stderr.strip() or "git check failed")
    return result.stdout.strip()


def _hashes():
    return {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in FROZEN}


def _verify_freeze(commit):
    if _git("rev-parse", "HEAD") != commit:
        raise ValueError("registered draw requires its preregistration-only commit at HEAD")
    if os.environ.get("COGNITION_PREREG_HASH", "") != commit:
        raise ValueError("COGNITION_PREREG_HASH mismatch")
    for p in FROZEN:
        _git("cat-file", "-e", f"{commit}:{p}")
        if _git("status", "--porcelain", "--", p):
            raise ValueError(f"frozen artifact changed: {p}")


def _case(seed, item, index, control=False):
    rng = random.Random(seed ^ (index * 7919) ^ sum(map(ord, item)) ^ (0xA51 if control else 0))
    cid = f"{item}-{'c' if control else 'p'}-{index:04d}"
    if item == "F1":
        values = [f"belief-{index % 7}", f"belief-{(index + int(control)) % 7}"]
        inp = {"source_key": cid, "content_values": values, "owner_permutation": rng.sample(range(4), 4)}
        oracle = {"preserve_sources": True, "expected_rows": 4}
    elif item == "F2":
        belief = bool(index % 2)
        belief_value = "drawer" if belief else "shelf"
        query_status = "true" if belief else "false"
        if control:
            query_status = "unknown"
        inp = {"holder_path": [f"holder-{index}", f"observer-{index}"],
               "referent": "key", "belief_value": belief_value, "query_value": "drawer",
               "actual_value": "shelf" if belief else "drawer", "accessible": not control,
               "cycle": False, "depth": 2}
        oracle = {"query_status": query_status,
                  "actual_value": inp["actual_value"], "expected_belief": inp["belief_value"]}
    elif item == "G2":
        supported = not control and bool(index % 2)
        inp = {"supported": supported, "arousal": 0.8,
               "alternative_has_evidence": supported, "forced_constraints_preserved": True}
        oracle = {"view_expected": supported, "source_unchanged": True}
    elif item == "G3":
        schedule = "stop_before" if (control or index % 3 == 0) else "go"
        if not control and index % 3 == 1:
            schedule = "late_stop"
        inp = {"schedule": schedule, "action": "advance", "epoch": 4}
        oracle = {"expected_status": "withheld" if schedule == "stop_before" else "emitted",
                  "late_stop_is_separate": schedule == "late_stop"}
    elif item == "E3":
        kind = ("confounder", "collider", "chain", "nonidentified")[index % 4]
        inp = {"model_kind": kind, "intervention": {"X": 1}, "outcome": "Y"}
        if kind == "confounder":
            model = {"variables": [{"id": "X", "domain": [0, 1]}, {"id": "Y", "domain": [0, 1]}],
                     "exogenous": [{"id": "U", "domain": [0, 1]}],
                     "equations": [{"target": name, "parents": [], "exogenous": ["U"],
                                    "rows": [{"inputs": {"U": 0}, "value": 0}, {"inputs": {"U": 1}, "value": 1}]}
                                   for name in ("X", "Y")],
                     "source_ids": ["mechanism-confounder"], "source_epoch": 7}
            effect = [0, 1]
        elif kind == "collider":
            model = {"variables": [{"id": name, "domain": [0, 1]} for name in ("X", "Y", "C")],
                     "exogenous": [{"id": name, "domain": [0, 1]} for name in ("Ux", "Uy")],
                     "equations": [
                         {"target": "X", "parents": [], "exogenous": ["Ux"], "rows": [
                             {"inputs": {"Ux": 0}, "value": 0}, {"inputs": {"Ux": 1}, "value": 1}]},
                         {"target": "Y", "parents": [], "exogenous": ["Uy"], "rows": [
                             {"inputs": {"Uy": 0}, "value": 0}, {"inputs": {"Uy": 1}, "value": 1}]},
                         {"target": "C", "parents": ["X", "Y"], "exogenous": [], "rows": [
                             {"inputs": {"X": x, "Y": y}, "value": x * y} for x in (0, 1) for y in (0, 1)]}],
                     "source_ids": ["mechanism-collider"], "source_epoch": 7}
            effect = [0, 1]
        elif kind == "chain":
            model = {"variables": [{"id": name, "domain": [0, 1]} for name in ("X", "Z", "Y")],
                     "exogenous": [{"id": "U", "domain": [0, 1]}],
                     "equations": [
                         {"target": "X", "parents": [], "exogenous": ["U"], "rows": [
                             {"inputs": {"U": 0}, "value": 0}, {"inputs": {"U": 1}, "value": 1}]},
                         {"target": "Z", "parents": ["X"], "exogenous": [], "rows": [
                             {"inputs": {"X": 0}, "value": 0}, {"inputs": {"X": 1}, "value": 1}]},
                         {"target": "Y", "parents": ["Z"], "exogenous": [], "rows": [
                             {"inputs": {"Z": 0}, "value": 0}, {"inputs": {"Z": 1}, "value": 1}]}],
                     "source_ids": ["mechanism-chain"], "source_epoch": 7}
            effect = [1, 1]
        else:
            model = {"variables": [{"id": "X", "domain": [0, 1]}, {"id": "Y", "domain": [0, 1]}],
                     "exogenous": [], "equations": [], "source_ids": [], "source_epoch": 7}
            effect = None
        inp["model"] = model
        oracle = {"identified": kind != "nonidentified", "effect_values": effect}
    elif item == "E4":
        depth = 2 + index % 7
        inp = {"depth": depth, "missing_final_edge": control,
               "depth_limit": 8, "expansion_limit": 256, "trap": f"trap-{index}"}
        oracle = {"reachable": not control, "optimal_depth": depth if not control else None}
    elif item == "A2":
        inp = {"required": ["alpha", "beta", "gamma"],
               "completed_count": 3 if control or index % 4 == 0 else index % 3,
               "stale_epoch": control}
        oracle = {"complete": inp["completed_count"] == 3 and not control}
    else:
        inp = {"shape": [list(point) for point in rng.sample(
                   [(x, y) for x in range(4) for y in range(4)], 4)],
               "angle": (0, 90, 180, 270)[index % 4], "shape_index": index}
        oracle = {"exact_transform": True, "work": inp["angle"] // 90, "grounded": False}
    return {"case_id": cid, "kind": "control" if control else "primary",
            "agent_input": inp, "scoring_oracle": oracle}


def _f1_arm(row, enabled):
    from substrate.world_adapter import WorldAdapter
    w = WorldAdapter(seeds=["tom_unified_view"])
    policy = w.s.nodes("TomViewPolicy")[0]
    w.s.set_attr(policy, "enabled", 1.0 if enabled else 0.0)
    source_specs = [("character_tom", "belief", "attributed", row["agent_input"]["content_values"][0]),
                    ("interlocutor_estimate", "estimate", "estimate", "feature=formal"),
                    ("interlocutor_assertion", "asserted", "world_assertion", row["agent_input"]["content_values"][1]),
                    ("bigville_tom", "attributed", "attributed", "controllability=low")]
    nodes = []
    owners = row["agent_input"]["owner_permutation"]
    for i, (kind, modality, epistemic, content) in enumerate(source_specs):
        node = w.s.add_node("TomAttributedStateSource", {
            "schema_version": 1, "source_key": f"{row['case_id']}:{i}",
            "source_is_current": True, "source_kind": kind,
            "source_node": f"source:{row['case_id']}:{i}", "source_epoch": i,
            "owner_id": f"owner-{owners[i]}", "holder": f"holder-{owners[i]}",
            "target": "room", "content_ref": content,
            "modality": modality, "epistemic_kind": epistemic,
        })
        nodes.append(node)
        w.inner.add_edge_unchecked(w.agent, "has_tom_attributed_source", node)
    before = [dict(w.s.node(n)["attrs"]) for n in nodes]
    w.tick()
    views = [w.s.node(n)["attrs"] for n in w.s.nodes("TomAttributedStateView")]
    source_unchanged = before == [w.s.node(n)["attrs"] for n in nodes]
    leak = any(v.get("epistemic_kind") == "world_assertion" and v.get("modality") == "belief"
               for v in views)
    result = {"views": views, "view_count": len(views), "source_unchanged": source_unchanged,
              "belief_truth_leak": leak, "expected_view_count": 4 if enabled else 0,
              "conformance": len(views) == (4 if enabled else 0)}
    w.close()
    return result


def _f2_arm(row, enabled):
    from substrate.world_adapter import WorldAdapter
    w = WorldAdapter(seeds=["recursive_tom"])
    policy = w.s.nodes("RecursiveTomPolicy")[0]
    w.s.set_attr(policy, "enabled", 1.0 if enabled else 0.0)
    inp = row["agent_input"]
    path = inp["holder_path"]
    event = w.s.add_node("RecursiveTomEvent", {
        "schema_version": 1, "event_id": row["case_id"], "holder_path": path,
        "holder_path_key": "/".join(path), "depth": 2, "referent": inp["referent"],
        "content_ref": f"key={inp['belief_value']}", "value": inp["belief_value"],
        "actual_world_version": 1, "accessible": inp["accessible"], "has_cycle": False,
    })
    w.inner.add_edge_unchecked(w.agent, "has_recursive_tom_event", event)
    actual = w.s.add_node("ActualWorldFact", {"referent": "key", "value": inp["actual_value"], "version": 1})
    query = w.s.add_node("RecursiveTomQuery", {
        "query_id": row["case_id"], "holder_path_key": "/".join(path),
        "referent": "key", "content_ref": f"key={inp['belief_value']}",
        "expected_value": inp["query_value"], "actual_world_version": 1,
    })
    w.inner.add_edge_unchecked(w.agent, "has_recursive_tom_query", query)
    w.tick()
    answers = [w.s.node(n)["attrs"] for n in w.s.nodes("RecursiveTomAnswer")]
    answer = answers[0].get("status") if answers else "unknown"
    result = {"answer": answer, "actual_world_unchanged": w.s.node(actual)["attrs"]["value"] == inp["actual_value"],
              "expected": row["scoring_oracle"]["query_status"], "belief_value": inp["belief_value"]}
    w.close()
    return result


def _g2_arm(row, enabled):
    from tests.test_reappraisal_migrated import _funded_event_case, _tick_native
    inp = row["agent_input"]
    s, ag, _mode, _budget, event, app, frame, claim, evidence = _funded_event_case(enabled=enabled)
    if not inp["supported"]:
        s.remove_edge(claim, "supported_by", evidence)
    before_event = dict(s.node(event)["attrs"])
    _tick_native(s)
    views = s.neighbours(ag, "has_reappraisal_view")
    result = {"view_count": len(views), "source_unchanged": s.node(event)["attrs"] == before_event,
              "selected_frame": s.node(frame)["attrs"]["frame_id"] if views else None,
              "unsupported_accepted": bool(views and not inp["supported"]),
              "appraisal_count": len(s.nodes("Appraisal"))}
    return result


def _g3_arm(row, enabled):
    from tests.test_response_inhibition_migrated import _world_case
    schedule = row["agent_input"]["schedule"]
    stopped = schedule == "stop_before" and enabled
    adapter, request, authorization, stop, _reflex, calls = _world_case(stopped=stopped)
    if not enabled and stopped:
        adapter.s.set_attr(stop, "source_epoch", -1.0)
    adapter.fire_reflexes()
    if schedule == "late_stop" and enabled:
        late = adapter.s.add_node("ActionStopEvent", {"request_id": adapter.s.node(request)["attrs"]["request_id"],
            "source_epoch": 4.0, "status": "pending"})
        adapter.inner.add_edge_unchecked(request, "has_action_stop", late)
        adapter.tick()
    attrs = adapter.s.node(request)["attrs"]
    result = {"status": attrs["status"], "emissions": len(calls),
              "authorization_status": adapter.s.node(authorization)["attrs"]["status"],
              "sink_receipt": attrs.get("sink_receipt_id"),
              "timely_stop_withheld": schedule != "stop_before" or attrs["status"] == "withheld",
              "valid_go_emitted": schedule != "go" or (attrs["status"] == "emitted" and len(calls) == 1),
              "late_stop_status": adapter.s.node(late)["attrs"]["status"] if schedule == "late_stop" and enabled else None}
    adapter.close()
    return result


def _e3_arm(row, use_scm):
    from tests.test_scm_intervention_migrated import _native
    model = row["agent_input"]["model"]
    query = {"kind": "effect" if use_scm else "condition", "outcome": "Y"}
    exogenous = model.get("exogenous", [])
    assignments = [{node["id"]: value for node, value in zip(exogenous, values)}
                   for values in ([0] * len(exogenous), [1] * len(exogenous))]
    before = json.dumps(model, sort_keys=True)
    result = _native(model, query, {"X": 1}, assignments)
    return {"status": result.get("status"), "values": result.get("values"),
            "source_ids": result.get("source_ids"), "source_epoch": result.get("source_epoch"),
            "truth_entered_graph": False, "live_model_unchanged": json.dumps(model, sort_keys=True) == before}


def _e4_arm(row, planner):
    if not planner:
        reachable = row["agent_input"]["depth"] == 1
        return {"predicted_reachable": reachable, "observed_success": reachable,
                "observed_depth": 1 if reachable else None, "expanded": 1}
    from tests.test_cognition_multistep_planner_migrated import _graph_planner, _run_to_fixpoint
    depth = row["agent_input"]["depth"]
    edges = [(f"s{i}", f"advance-{i}", f"s{i+1}" if i + 1 < depth else "goal", 2)
             for i in range(depth)]
    if row["agent_input"]["missing_final_edge"]:
        edges = edges[:-1]
    # A trap branch competes for frontier work but never reaches the goal.
    edges.extend([("s0", "trap", "trap-state", 2),
                  ("trap-state", "trap-loop", "trap-state", 2)])
    a, request, budget = _graph_planner(edges, required_horizon=max(1.0, float(depth)), remaining=256.0)
    _run_to_fixpoint(a)
    attrs = a.s.node(request)["attrs"]
    candidates = a.inner.neighbours(request, "has_imagined_plan_candidate")
    successful_path = None
    if candidates:
        arrival = a.inner.neighbours(candidates[0], "has_terminal_path_arrival")[0]
        actions = []
        while a.s.node(arrival)["attrs"].get("path_kind") != "origin":
            actions.append(a.s.node(arrival)["attrs"]["action_key"])
            arrival = a.inner.neighbours(arrival, "parent_path_arrival")[0]
        actions.reverse()
        state = "s0"
        for action in actions:
            move = next((edge for edge in edges if edge[0] == state and edge[1] == action), None)
            if move is None:
                break
            state = move[2]
        successful_path = state == "goal"
    result = {"predicted_reachable": bool(candidates), "observed_success": bool(successful_path),
              "observed_depth": len(actions) if candidates else None,
              "expanded": attrs.get("expanded_count"), "budget_remaining": a.s.node(budget)["attrs"]["remaining"],
              "terminal_status": attrs.get("status"), "imagined_only": True}
    a.close()
    return result


def _a2_arm(row, enabled):
    from substrate.world_adapter import WorldAdapter
    from tests.test_decomposition_completion_migrated import _edge
    agent = WorldAdapter(seeds=["decomposition_completion"])
    policy = agent.s.nodes("DecompositionCompletionPolicy")[0]
    agent.s.set_attr(policy, "enabled", 1.0 if enabled else 0.0)
    axis = agent.s.add_node("CapabilityAxis", {"saturation": 0.35, "model_epoch": 4,
        "decomposition_epoch": 7})
    impasse = agent.s.add_node("Impasse", {"kind": "escalation", "resolved": False})
    _edge(agent, impasse, "needs_decomposition", axis)
    _edge(agent, impasse, "about_axis", axis)
    inp = row["agent_input"]
    for i, key in enumerate(inp["required"]):
        key_node = agent.s.add_node("CapKey", {"name": key})
        _edge(agent, axis, "requires_key", key_node)
        if i < inp["completed_count"]:
            child = agent.s.add_node("CapabilityAxis", {
                "completion_status": "completed", "completion_verified": 1,
                "model_epoch": 3 if inp["stale_epoch"] and i == 2 else 4,
                "decomposition_epoch": 7,
            })
            _edge(agent, axis, "decomposes_into", child)
            _edge(agent, child, "requires_key", key_node)
    agent.tick()
    ia = agent.s.node(impasse)["attrs"]
    aa = agent.s.node(axis)["attrs"]
    result = {"resolved": ia.get("resolved", False), "witness": ia.get("completion_witness", 0) == 1,
              "saturation": aa["saturation"], "expected_complete": row["scoring_oracle"]["complete"],
              "premature_settlement": bool(ia.get("resolved", False) and not row["scoring_oracle"]["complete"])}
    agent.close()
    return result


def _d6_arm(row, buffered):
    inp = row["agent_input"]
    points = frozenset(tuple(point) for point in inp["shape"])
    from tests.test_analog_imagery_migrated import shortest_rotation
    steps = shortest_rotation(0, inp["angle"])
    if not buffered:
        current = sorted(points)
        from tests.test_analog_imagery_migrated import rotate_ordered
        for step in steps:
            current = rotate_ordered(current, step)
        return {"shape": current, "work": len(steps), "grounded": False, "exact": True}
    from tests.test_analog_imagery_migrated import _runtime, rotate_ordered, _verification_receipt
    agent, observation, request, _budget = _runtime(points, steps, budget=8)
    agent.tick()
    attrs = agent.s.node(request)["attrs"]
    expected = sorted(points)
    for step in steps:
        expected = rotate_ordered(expected, step)
    actual = [tuple(point) for point in attrs["current_shape"]]
    exact = actual == [tuple(point) for point in expected]
    _verification_receipt(agent, request, observation, "verified" if exact else "mismatch")
    agent.tick()
    final = agent.s.node(request)["attrs"]
    result = {"shape": final["current_shape"], "work": final.get("cost", 0),
              "grounded": bool(final.get("grounded", 0)),
              "exact": exact, "shape_verified": bool(final.get("shape_verified", False)),
              "buffer_size": final.get("buffer_size"),
              "witnesses": len(agent.s.neighbours(request, "has_imagery_witness")),
              "status": final["status"]}
    agent.close()
    return result


def _run_arm(item, row, arm):
    enabled = arm.endswith("_on") or arm in {"planner", "scm_do_query", "completion_on", "buffered_incremental"}
    if item == "F1": return _f1_arm(row, enabled)
    if item == "F2": return _f2_arm(row, enabled)
    if item == "G2": return _g2_arm(row, enabled)
    if item == "G3": return _g3_arm(row, enabled)
    if item == "E3": return _e3_arm(row, arm == "scm_do_query")
    if item == "E4": return _e4_arm(row, arm == "planner")
    if item == "A2": return _a2_arm(row, arm == "completion_on")
    return _d6_arm(row, arm == "buffered_incremental")


def run(prereg_hash, first, end, *, development=False):
    if not development:
        _verify_freeze(prereg_hash)
    if first < 0 or end < first or (not development and end > N_PRIMARY):
        raise ValueError("draw range must be within registered 0..200 indices")
    seed = int(hashlib.sha256(prereg_hash.encode()).hexdigest()[:16], 16)
    result = {"protocol": PROTOCOL, "prereg_hash": prereg_hash,
              "first": first, "end": end, "development_only": development,
              "limits": {"max_epochs": 64, "planner_depth": 8, "planner_expansions": 256},
              "artifact_sha256": _hashes(), "items": {}}
    for item, arms in ITEM_ARMS.items():
        primary = []
        controls = []
        for ix in range(first, end):
            row = _case(seed, item, ix)
            row["arms"] = {arm: _run_arm(item, row, arm) for arm in arms}
            primary.append(row)
        for ix in range(N_CONTROL):
            row = _case(seed, item, ix, control=True)
            row["arms"] = {arm: _run_arm(item, row, arm) for arm in arms}
            controls.append(row)
        result["items"][item] = {"arms": arms, "primary": primary, "controls": controls}
    return result


def _self_check():
    small = run("development-v2", 0, 2, development=True)
    assert set(small["items"]) == set(ITEM_ARMS)
    assert all(len(item["primary"]) == 2 and len(item["controls"]) == N_CONTROL
               for item in small["items"].values())
    assert all(all(isinstance(outcome, dict) for outcome in row["arms"].values())
               for item in small["items"].values() for row in item["primary"] + item["controls"])
    assert all("scoring_oracle" not in row.get("agent_input", {})
               for item in small["items"].values() for row in item["primary"] + item["controls"])
    bad = dict(small["artifact_sha256"]); bad[next(iter(bad))] = "0" * 64
    assert bad != _hashes()
    try:
        _verify_freeze("0" * 40)
    except ValueError:
        pass
    else:
        raise AssertionError("freeze guard accepted an invalid preregistration")


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--self-check"]:
        _self_check(); print("cognition_p5_mechanism_eval_v2 self-check passed"); return
    if len(args) != 3:
        raise SystemExit("usage: cognition_p5_mechanism_eval_v2.py <prereg_hash> <first> <end> | --self-check")
    report = run(args[0], int(args[1]), int(args[2]))
    out = ROOT / "evaluation" / "reports" / f"cognition_p5_mechanism_eval_v2_{args[0][:8]}_d{args[1]}-{args[2]}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
