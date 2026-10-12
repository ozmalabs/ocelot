#!/usr/bin/env python3
"""Fresh-process episodic graph-checkpoint and corruption-recovery probe."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import resource
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_episodic_checkpoint_recovery_postfix_v5_20260925.json"
TARGETS = 6


def edge(agent, src, rel, tgt):
    agent.inner.add_edge_unchecked(src, rel, tgt, {})


def specs():
    return [{"i": i, "cue": f"checkpoint-cue-{i}", "summary": f"checkpoint-route-{i}-north"}
            for i in range(TARGETS)]


def writer(path):
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("episodic_working_memory_core",))
    for x in specs():
        ctx = agent.s.add_node("MemoryContext", {"context_key": f"checkpoint-context-{x['i']}"})
        schema = agent.s.add_node("MemorySchema", {"name": "route_state"})
        event = agent.s.add_node("EpisodicEvent", {
            "event_key": f"checkpoint-event-{x['i']}", "cue_key": x["cue"],
            "epoch": 1.0, "salience": 0.8, "surprise": 0.7, "value": 0.9,
            "observation_status": "observed", "provenance_kind": "perceived",
            "state_kind": "route", "state_summary": x["summary"],
        })
        edge(agent, agent.agent, "experienced_event", event)
        edge(agent, event, "in_context", ctx)
        edge(agent, event, "instantiates_schema", schema)
    closure_t0 = time.perf_counter_ns()
    closure_progress = int(agent.tick())
    closure_ns = time.perf_counter_ns() - closure_t0
    save_t0 = time.perf_counter_ns()
    agent.save(path)
    save_ns = time.perf_counter_ns() - save_t0
    result = {"mode": "writer", "pid": os.getpid(), "closure_progress": closure_progress,
              "closure_ns": closure_ns, "save_ns": save_ns,
              "node_count": agent.s.node_count(), "episode_count": len([
                  n for n in agent.s.nodes() if agent.s.node(n)["type"] == "Episode"])}
    try:
        agent.close()
        result["close_status"] = "closed"
    except Exception as exc:
        result["close_status"] = "error"
        result["close_exception_type"] = type(exc).__name__
        result["close_exception_message"] = str(exc)[:300]
    print(json.dumps(result, sort_keys=True))


def reader(path, variant):
    result = {"mode": "reader", "variant": variant, "pid": os.getpid()}
    try:
        from substrate.world_adapter import WorldAdapter
        t0 = time.perf_counter_ns()
        agent = WorldAdapter.load(path)
        result["load_ns"] = time.perf_counter_ns() - t0
    except Exception as exc:
        result.update({"load_status": "error", "exception_type": type(exc).__name__,
                       "exception_message": str(exc)[:300], "rss_peak_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})
        print(json.dumps(result, sort_keys=True)); return
    result["load_status"] = "loaded"
    result["node_count"] = agent.s.node_count()
    result["episode_count"] = sum(1 for n in agent.s.nodes() if agent.s.node(n)["type"] == "Episode")
    result["memory_rule_count"] = sum(1 for r in agent.inner.export_rules()
                                      if "episodic_" in str(r.get("name", "")) or
                                      "working_memory_" in str(r.get("name", "")))
    integrity = []
    for ep in [n for n in agent.s.nodes() if agent.s.node(n)["type"] == "Episode"]:
        bound = list(agent.inner.neighbours(ep, "bound_event"))
        contexts = list(agent.inner.neighbours(ep, "in_context"))
        schemas = list(agent.inner.neighbours(ep, "instantiates_schema"))
        integrity.append({"bound_event_count": len(bound), "context_count": len(contexts),
                          "schema_count": len(schemas)})
    result["episode_relation_counts"] = integrity
    rows = []
    for x in specs():
        req = agent.s.add_node("MemoryRetrievalRequest", {
            "status": "pending", "cue_key": x["cue"], "epoch": 4.0,
        })
        edge(agent, agent.agent, "has_memory_retrieval_request", req)
        t0 = time.perf_counter_ns(); progress = int(agent.tick()); tick_ns = time.perf_counter_ns() - t0
        cand = list(agent.inner.neighbours(req, "has_recall_candidate"))
        outcomes = list(agent.inner.neighbours(req, "has_recall_outcome"))
        row = {"cue": x["cue"], "expected_summary": x["summary"], "progress": progress,
               "tick_ns": tick_ns, "candidate_count": len(cand), "outcome_count": len(outcomes)}
        if len(cand) == 1:
            ca = agent.s.node(cand[0])["attrs"]
            ev = list(agent.inner.neighbours(cand[0], "reconstructs_event"))
            ea = agent.s.node(ev[0])["attrs"] if len(ev) == 1 else {}
            row.update({"status": ca.get("status"), "confidence": ca.get("confidence"),
                        "provenance_kind": ca.get("provenance_kind"),
                        "observation_status": ca.get("observation_status"),
                        "state_summary": ea.get("state_summary"),
                        "reconstructed_event_count": len(ev)})
        elif len(outcomes) == 1:
            oa = agent.s.node(outcomes[0])["attrs"]
            row.update({"status": oa.get("status"), "confidence": oa.get("confidence")})
        else:
            row["status"] = "no_response"
        rows.append(row)
    result["queries"] = rows
    result["rss_peak_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    try:
        agent.close()
        result["close_status"] = "closed"
    except Exception as exc:
        result["close_status"] = "error"
        result["close_exception_type"] = type(exc).__name__
        result["close_exception_message"] = str(exc)[:300]
    print(json.dumps(result, sort_keys=True))


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--write":
        writer(sys.argv[2]); return
    if len(sys.argv) == 4 and sys.argv[1] == "--read":
        reader(sys.argv[3], sys.argv[2]); return
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{ROOT / 'runners/dsl/python'}:{ROOT}:{env.get('PYTHONPATH', '')}"
    with tempfile.TemporaryDirectory(prefix="episodic-checkpoint-") as td:
        base = Path(td) / "intact.json"
        wp = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--write", str(base)],
                            cwd=ROOT, env=env, text=True, capture_output=True, check=True)
        writer_record = json.loads(wp.stdout.strip())
        checkpoint_bytes = base.stat().st_size
        data = json.loads(base.read_text())
        graph = data["graph"]
        changed = json.loads(json.dumps(data))
        event = next(n for n in changed["graph"]["nodes"]
                     if n["type"] == "EpisodicEvent" and n["attrs"].get("cue_key") == "checkpoint-cue-0")
        event["attrs"]["state_summary"] = "CORRUPTION-MARKER"
        changed_path = Path(td) / "changed-summary.json"
        changed_path.write_text(json.dumps(changed))
        missing = json.loads(json.dumps(data))
        ep = next(n for n in missing["graph"]["nodes"] if n["type"] == "Episode" and n["attrs"].get("cue_key") == "checkpoint-cue-1")
        missing["graph"]["edges"] = [e for e in missing["graph"]["edges"]
                                       if not (e["type"] == "recorded_episode" and e["tgt"] == ep["id"])]
        missing_path = Path(td) / "missing-recorded-edge.json"
        missing_path.write_text(json.dumps(missing))
        malformed_path = Path(td) / "malformed.json"
        malformed_path.write_text('{"graph":')
        readers = []
        for variant, path in (("intact", base), ("altered_summary", changed_path),
                              ("missing_recorded_edge", missing_path), ("malformed_json", malformed_path)):
            p = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--read", variant, str(path)],
                               cwd=ROOT, env=env, text=True, capture_output=True, check=True)
            readers.append(json.loads(p.stdout.strip()))
        by = {r["variant"]: r for r in readers}
    intact = by["intact"]
    changed_reader = by["altered_summary"]
    missing_reader = by["missing_recorded_edge"]
    malformed_reader = by["malformed_json"]
    checks = {
        "writer_bound_six_episodes": writer_record["episode_count"] == 6,
        "all_processes_are_distinct": len({writer_record["pid"], *(r["pid"] for r in readers)}) == 5,
        "intact_checkpoint_recalls_all_six": intact["load_status"] == "loaded" and intact["episode_count"] == 6 and all(
            q["candidate_count"] == 1 and q["state_summary"] == q["expected_summary"] and
            q["provenance_kind"] == "recalled" and q["observation_status"] == "not_observed" for q in intact["queries"]),
        "intact_checkpoint_restores_episode_relations_and_rules": (
            all(x == {"bound_event_count": 1, "context_count": 1, "schema_count": 1}
                for x in intact["episode_relation_counts"]) and intact["memory_rule_count"] >= 1),
        "altered_content_is_exposed_as_recalled_without_integrity_warning": (
            changed_reader["queries"][0].get("state_summary") == "CORRUPTION-MARKER" and
            changed_reader["queries"][0].get("provenance_kind") == "recalled" and
            changed_reader["queries"][0].get("observation_status") == "not_observed"),
        "missing_episode_link_degrades_to_insufficient_information": (
            missing_reader["queries"][1]["candidate_count"] == 0 and
            missing_reader["queries"][1].get("status") == "insufficient_information" and
            all(q["state_summary"] == q["expected_summary"] for i, q in enumerate(missing_reader["queries"]) if i != 1)),
        "malformed_json_is_rejected": malformed_reader["load_status"] == "error" and malformed_reader["exception_type"] == "JSONDecodeError",
        "restored_adapters_close_cleanly": all(
            by[name].get("close_status") == "closed"
            for name in ("intact", "altered_summary", "missing_recorded_edge")),
    }
    paths = {
        "harness": Path(__file__).resolve(),
        "preregistration": ROOT / "docs/research/engine_substrate/SUBSTRATE_EPISODIC_CHECKPOINT_RECOVERY_PREREG_20260925.md",
        "world_adapter": ROOT / "substrate/world_adapter.py",
        "episodic_seed": ROOT / "seeds/episodic_working_memory_core.json",
        "memory_seed": ROOT / "seeds/memory_core.json",
        "native_extension": ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so",
        "native_build_manifest": ROOT / "runners/dsl/python/substrate_rs/_native.build.json",
    }
    payload = {"schema_version": 1, "run_id": "substrate-episodic-checkpoint-recovery-20260925-v5",
               "scope": "fresh-process WorldAdapter episodic graph checkpoint and three corruption variants",
               "claim_boundary": "Tiny authored graph checkpoint probe; not MemoryFaculty durability or security claim.",
               "source_sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths.values()},
               "environment": {"python": platform.python_version(), "platform": platform.platform()},
               "writer": writer_record, "checks": checks,
               "readers": readers,
               "checkpoint_bytes": checkpoint_bytes,
               "summary": {"all_checks_pass": all(checks.values()),
                           "load_ms": {r["variant"]: (r.get("load_ns", 0) / 1e6) for r in readers},
                           "peak_rss_kib": {r["variant"]: r.get("rss_peak_kib") for r in readers}}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "summary": payload["summary"], "output": str(OUT)}, indent=2))
    if not all(checks.values()):
        raise SystemExit("episodic checkpoint recovery pilot failed")


if __name__ == "__main__":
    main()
