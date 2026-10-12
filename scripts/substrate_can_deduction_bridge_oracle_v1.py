#!/usr/bin/env python3
"""Exhaustive five-topic CAN-to-deduction translation oracle panel."""
from __future__ import annotations
import hashlib, itertools, json, os, platform, resource, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_CAN_DEDUCTION_BRIDGE_ORACLE_V1_PREREG_20260927.md"
ANALYZER = ROOT / "scripts/analyze_substrate_can_deduction_bridge_oracle_v1.py"
LOCK = ROOT / "evaluation/substrate_capability/can_deduction_bridge_oracle_v1_lock_20260927.json"
OUT = ROOT / "evaluation/reports/can_deduction_bridge_oracle_v1_20260927.json"
TOPICS = ["trust_mayor", "claim_credible", "world_safe", "self_worth", "debtor_trustworthy"]
WORKERS = [0, 1]

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def tree(folder, suffixes):
    out = {}
    for p in sorted(folder.rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts and p.suffix in suffixes:
            out[p.relative_to(ROOT).as_posix()] = sha(p)
    return out

def inputs():
    from substrate_rs import _native
    return {
        "prereg_sha256": sha(PREREG), "runner_sha256": sha(__file__),
        "analyzer_sha256": sha(ANALYZER),
        "source_trees": {
            "domains": tree(ROOT / "domains", {".py"}),
            "substrate": tree(ROOT / "substrate", {".py"}),
            "seeds": tree(ROOT / "seeds", {".json"}),
            "native_python": tree(ROOT / "runners/dsl/python", {".py"}),
            "rust": tree(ROOT / "runners/dsl/src", {".rs"}),
        },
        "native_extension_sha256": sha(Path(_native.__file__).resolve()),
        "topics": TOPICS,
    }

def worker(rep):
    from substrate.world_adapter import WorldAdapter
    from domains import reasoning_can_bridge as bridge
    from substrate_rs import _native
    start_wall, start_cpu = time.perf_counter_ns(), time.process_time_ns()
    adapter = WorldAdapter(seeds=())
    sub, native = adapter.s, adapter.inner
    cases = []
    for ci, vector in enumerate(itertools.product((-1, 0, 1), repeat=len(TOPICS))):
        name = f"bridge_oracle_case_{ci:03d}"
        resident = native.add_node("Resident", {"name": name})
        mt = native.add_node("Microtheory", {"name": name + "_beliefs"})
        native.add_edge_unchecked(resident, "has_belief_mt", mt)
        concepts = []
        for topic, state in zip(TOPICS, vector):
            concept = native.add_node("Concept", {"name": topic, "state": state})
            native.add_edge_unchecked(mt, "has_concept", concept)
            concepts.append(concept)
        # Frozen oracle input is kept separate from the bridge result.
        expected = sorted((name, topic if state > 0 else "not_" + topic)
                          for topic, state in zip(TOPICS, vector) if state != 0)
        cases.append({"case_id": ci, "entity": name, "mt": int(mt.value),
                      "states": dict(zip(TOPICS, vector)), "expected": expected,
                      "concept_ids": [int(n.value) for n in concepts]})

    Native = _native.Substrate
    Native.scale_audit_set_enabled(True)
    Native.scale_audit_set_per_rule_enabled(True)
    Native.scale_audit_reset()
    fixture_wall_ns = time.perf_counter_ns() - start_wall
    results = []
    for case in cases:
        mt = _native.NodeID(case["mt"])
        before = time.perf_counter_ns()
        cpu_before = time.process_time_ns()
        rows = bridge.can_state_as_predications(adapter, mt, t=case["case_id"])
        elapsed = time.perf_counter_ns() - before
        cpu_elapsed = time.process_time_ns() - cpu_before
        entity_node = next((n for n in sub.nodes("SmEntity")
                            if sub.node(n)["attrs"].get("name") == case["entity"]), None)
        attrs = sub.node(entity_node)["attrs"] if entity_node is not None else {"name": case["entity"]}
        observed = sorted((case["entity"], key) for key, value in attrs.items()
                          if key not in ("name", "unit", "coref_number") and value == 1
                          and (key in TOPICS or key.startswith("not_") and key[4:] in TOPICS))
        results.append({"case_id": case["case_id"], "entity": case["entity"],
                        "states": case["states"], "expected": case["expected"],
                        "observed": observed, "bridge_result_count": len(rows),
                        "bridge_call_wall_ns": elapsed, "bridge_call_cpu_ns": cpu_elapsed,
                        "entity_attrs": {k: v for k, v in attrs.items()
                                         if k in TOPICS or k.startswith("not_")}})
    aggregate_expected = sorted(fact for case in cases for fact in case["expected"])
    aggregate_observed = []
    for enode in sub.nodes("SmEntity"):
        eat = sub.node(enode)["attrs"]
        entity_name = eat.get("name")
        aggregate_observed.extend([entity_name, key] for key, value in eat.items()
                                   if value == 1 and (key in TOPICS or
                                   key.startswith("not_") and key[4:] in TOPICS))
    aggregate_observed.sort()
    audit_counters = dict(Native.scale_audit_snapshot())
    per_rule_counters = [list(row) for row in Native.scale_audit_per_rule_snapshot()]
    # Re-entry and isolation controls use distinct owner/Microtheory identities.
    first = cases[0]
    first_mt = _native.NodeID(first["mt"])
    first_entity = next(n for n in sub.nodes("SmEntity")
                        if sub.node(n)["attrs"].get("name") == first["entity"])
    attrs_before = {k: v for k, v in sub.node(first_entity)["attrs"].items()
                    if k in TOPICS or k.startswith("not_")}
    bridge.can_state_as_predications(adapter, first_mt, t=999)
    attrs_after = {k: v for k, v in sub.node(first_entity)["attrs"].items()
                   if k in TOPICS or k.startswith("not_")}
    duplicate_control = {"before": attrs_before, "after": attrs_after,
                         "semantic_delta_empty": attrs_before == attrs_after}

    isolated_name = "bridge_oracle_unrelated"
    isolated_resident = native.add_node("Resident", {"name": isolated_name})
    isolated_mt = native.add_node("Microtheory", {"name": isolated_name + "_beliefs"})
    native.add_edge_unchecked(isolated_resident, "has_belief_mt", isolated_mt)
    for topic in TOPICS:
        cn = native.add_node("Concept", {"name": topic, "state": 0})
        native.add_edge_unchecked(isolated_mt, "has_concept", cn)
    isolated_rows = bridge.can_state_as_predications(adapter, isolated_mt, t=1000)
    isolated_entity = next((n for n in sub.nodes("SmEntity")
                            if sub.node(n)["attrs"].get("name") == isolated_name), None)
    isolated_graph_attrs = sub.node(isolated_entity)["attrs"] if isolated_entity is not None else {}
    isolated_attrs = {k: v for k, v in isolated_graph_attrs.items()
                      if k in TOPICS or k.startswith("not_")}
    isolation_control = {"result_count": len(isolated_rows),
                         "semantic_attrs": isolated_attrs,
                         "no_cross_target_facts": not isolated_attrs}

    absent_name = "bridge_oracle_absent"
    absent_resident = native.add_node("Resident", {"name": absent_name})
    absent_mt = native.add_node("Microtheory", {"name": absent_name + "_beliefs"})
    native.add_edge_unchecked(absent_resident, "has_belief_mt", absent_mt)
    absent_concept = native.add_node("Concept", {"name": "world_safe"})
    native.add_edge_unchecked(absent_mt, "has_concept", absent_concept)
    absent_rows = bridge.can_state_as_predications(adapter, absent_mt, t=1001)
    absent_entity_exists = any(sub.node(n)["attrs"].get("name") == absent_name
                               for n in sub.nodes("SmEntity"))
    absent_control = {"result_count": len(absent_rows),
                      "entity_created": absent_entity_exists,
                      "no_fact_for_missing_state": len(absent_rows) == 0 and not absent_entity_exists}

    # Ambiguous token containment must not mint a denotation edge. The public
    # bridge may still use the explicit legacy Resident->Microtheory owner path;
    # record that outcome separately instead of conflating it with ambiguity.
    from domains import situation_model_reader as smr
    ambiguous_entity = smr._entity(adapter, "Ambiguous")
    amb_mts = []
    for owner in ("Ambiguous One", "Ambiguous Two"):
        rr = native.add_node("Resident", {"name": owner})
        mm = native.add_node("Microtheory", {"name": owner.replace(" ", "_") + "_beliefs"})
        native.add_edge_unchecked(rr, "has_belief_mt", mm)
        cc = native.add_node("Concept", {"name": "world_safe", "state": 1})
        native.add_edge_unchecked(mm, "has_concept", cc)
        amb_mts.append(mm)
    native.set_attr(ambiguous_entity, "name_tokens", frozenset({"ambiguous"}))
    for rr in sub.nodes("Resident"):
        nm = sub.node(rr)["attrs"].get("name")
        if nm in ("Ambiguous One", "Ambiguous Two"):
            native.set_attr(rr, "name_tokens", frozenset({"ambiguous", nm.split()[-1].lower()}))
    # The bridge call runs the correspondence Rules, after which we inspect the
    # graph-native outcome and the documented owner fallback result.
    amb_rows = bridge.can_state_as_predications(adapter, amb_mts[0], t=2000)
    denoted = [int(n.value) for n in native.neighbours(ambiguous_entity, "denotes")]
    owner_name = "Ambiguous One"
    owner_sm = next((n for n in sub.nodes("SmEntity")
                     if sub.node(n)["attrs"].get("name") == owner_name), None)
    ambiguity_control = {"ambiguous_entity_id": int(ambiguous_entity.value),
                         "ambiguous_denotes_edges": denoted,
                         "expected_no_denotes": True,
                         "legacy_owner_fallback": owner_sm is not None and
                         sub.node(owner_sm)["attrs"].get("world_safe") == 1,
                         "bridge_result_count": len(amb_rows)}
    Native.scale_audit_set_enabled(False)
    Native.scale_audit_set_per_rule_enabled(False)
    wall_ns, cpu_ns = time.perf_counter_ns() - start_wall, time.process_time_ns() - start_cpu
    return {"replicate": rep, "pid": os.getpid(), "cases": results,
            "aggregate_expected": aggregate_expected,
            "aggregate_observed": aggregate_observed,
            "native_audit_counters": audit_counters,
            "native_per_rule_counter_rows": len(per_rule_counters),
            "controls": {"duplicate_invocation": duplicate_control,
                         "unrelated_target": isolation_control,
                         "missing_state": absent_control,
                         "ambiguous_tokens": ambiguity_control},
            "runtime": {"wall_ns_including_fixture_build": wall_ns,
                        "cpu_ns_including_fixture_build": cpu_ns,
                        "fixture_build_wall_ns": fixture_wall_ns,
                        "bridge_panel_wall_ns": sum(r["bridge_call_wall_ns"] for r in results),
                        "bridge_panel_cpu_ns": sum(r["bridge_call_cpu_ns"] for r in results),
                        "peak_rss_bytes": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1024 if sys.platform.startswith("linux") else 1)),
                        "final_node_count": native.node_count(),
                        "final_edge_count": native.edge_count(),
                        "python": sys.version, "platform": platform.platform()}}

def main():
    if sys.argv[1:] == ["--lock"]:
        print(json.dumps({"locked_inputs": inputs()}, indent=2, sort_keys=True)); return
    if sys.argv[1:] == ["--worker"]:
        rep = int(os.environ["OCEL0_CAN_BRIDGE_REP"])
        before = inputs(); result = worker(rep); after = inputs()
        result.update({"locked_inputs_before": before, "locked_inputs_after": after,
                       "source_stable": before == after})
        print(json.dumps(result, sort_keys=True)); return
    locked = inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs") != locked:
        raise SystemExit("missing or stale bridge-oracle lock; capture --lock then freeze it")
    env = {**os.environ, "PYTHONPATH": f"{ROOT}:{ROOT / 'runners/dsl/python'}",
           "OZMA_SEED_PERSIST_DISABLED": "1"}
    runs = []
    for rep in WORKERS:
        e = {**env, "OCEL0_CAN_BRIDGE_REP": str(rep)}
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker"],
                              cwd=ROOT, env=e, text=True, capture_output=True, timeout=900)
        try: row = json.loads(proc.stdout)
        except Exception: row = {"worker_error": proc.stderr or proc.stdout}
        row.update({"worker_returncode": proc.returncode, "worker_stderr": proc.stderr})
        runs.append(row)
    post = inputs()
    checks = {
        "two_fresh_processes": len(runs) == 2 and len({r.get("pid") for r in runs}) == 2,
        "source_stable": post == locked and all(r.get("source_stable") and r.get("locked_inputs_before") == locked == r.get("locked_inputs_after") for r in runs),
        "all_243_cases": all(len(r.get("cases", [])) == 243 for r in runs),
        "worker_success": all(r.get("worker_returncode") == 0 for r in runs),
    }
    report = {"schema_version": 1, "run_id": "can-deduction-bridge-oracle-v1-20260927",
              "locked_inputs": locked, "post_run_inputs": post,
              "integrity_checks": checks, "integrity_pass": all(checks.values()),
              "runs": runs, "claim_boundary": "Five-topic exhaustive ternary state translation and attribute attribution only; not CAN belief truth, utility, natural frequency, or induction capability."}
    OUT.parent.mkdir(parents=True, exist_ok=True); OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"report": str(OUT.relative_to(ROOT)), "integrity_checks": checks}, indent=2))
    if not report["integrity_pass"]: raise SystemExit("integrity gates failed")

if __name__ == "__main__": main()
