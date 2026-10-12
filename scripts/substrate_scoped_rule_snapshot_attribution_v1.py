#!/usr/bin/env python3
"""Attribute scoped no-op setup sensitivity to active slots and rule body size."""
from __future__ import annotations

import hashlib, json, random, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "runners/dsl/python"), str(ROOT)]
from domains.engine_provenance import build_is_stale, rust_source_fingerprint
from substrate_rs import Substrate
from substrate_rs.ext import add_rule

LOCK = ROOT / "docs/research/engine_substrate/SUBSTRATE_SCOPED_RULE_SNAPSHOT_ATTRIBUTION_PREREG_20260926.md"
OUT = ROOT / "evaluation/reports/substrate_scoped_rule_snapshot_attribution_v1_20260926.json"
NATIVE = ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so"
ACTIVE_COUNTS, REPEATS, CALLS = (64, 256, 512), 5, 30

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def fixture(active, tombstones, shape):
    s = Substrate(); mt = s.add_node("Microtheory", {"fixed": True}); c = s.add_node("Concept", {"fixed": True})
    s.add_edge_unchecked(mt, "has_concept", c)
    edges_n, effects_n = (1, 1) if shape == "small" else (8, 8)
    def install(i):
        edges = [(f"x{j}", f"absent_{i}_{j}", f"y{j}") for j in range(edges_n)]
        effects = [["set_attr", f"y{j}", f"unused_{j}", True] for j in range(effects_n)]
        return add_rule(s._inner, f"snapshot_{i}", edges, effects)
    dead = [install(i) for i in range(tombstones)]
    for i in dead: assert s._inner.remove_rule(i)
    for i in range(active): install(tombstones + i)
    return s, mt, c

def project(s, mt, c):
    a, b = s.node(mt), s.node(c)
    exported=s._inner.export_rules()
    return (s.node_count(), s.edge_count(), a["type"], a["attrs"], b["type"], b["attrs"],
            s.has_edge(mt, "has_concept", c), s._inner.rule_count(), sum(bool(r["active"]) for r in exported))

def one(active, tombstones, shape, repeat):
    s, mt, c = fixture(active, tombstones, shape); inner=s._inner
    inner.scale_audit_set_per_rule_enabled(False); inner.scale_audit_set_enabled(False)
    assert int(inner.run_rules_scoped(100_000, False, mt)) == 0
    before=project(s,mt,c); inner.scale_audit_reset()
    wall0,cpu0=time.perf_counter_ns(),time.process_time_ns()
    results=[int(inner.run_rules_scoped(100_000,False,mt)) for _ in range(CALLS)]
    wall,cpu=time.perf_counter_ns()-wall0,time.process_time_ns()-cpu0
    counts=dict(inner.scale_audit_snapshot()); after=project(s,mt,c)
    return {"active":active,"tombstones":tombstones,"shape":shape,"repeat":repeat,"calls":CALLS,
            "results":results,"before":before,"after":after,"wall_ns":wall,"cpu_ns":cpu,
            "ns_per_call":wall/CALLS,"counters":counts}

def main():
    if build_is_stale(str(ROOT)): raise SystemExit("stale native build")
    rows=[]
    for rep in range(REPEATS):
        cells=[(n,t,sh) for n in ACTIVE_COUNTS for t in (0,n) for sh in ("small","large")]
        random.Random(99173+rep).shuffle(cells)
        for n,t,sh in cells: rows.append(one(n,t,sh,rep))
    inputs={"protocol":sha(LOCK),"runner":sha(Path(__file__)),
            **{k:sha(ROOT/p) for k,p in {"graph_rs":"runners/dsl/src/graph.rs","substrate_rs":"runners/dsl/src/substrate.rs",
                "rewrite_rs":"runners/dsl/src/rewrite.rs","py_rs":"runners/dsl/src/py.rs","scale_audit_rs":"runners/dsl/src/scale_audit.rs"}.items()},
            "native":sha(NATIVE),"rust_source_fingerprint":rust_source_fingerprint(str(ROOT))}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps({"protocol_id":"SUBSTRATE_SCOPED_RULE_SNAPSHOT_ATTRIBUTION_20260926","active_counts":ACTIVE_COUNTS,
        "repeats":REPEATS,"calls_per_cell":CALLS,"inputs":inputs,"rows":rows},indent=2,sort_keys=True)+"\n")
    print(json.dumps({"output":str(OUT),"cells":len(rows),"stable_zero_progress":all(not any(r["results"]) and r["before"]==r["after"] for r in rows)},indent=2))

if __name__=="__main__": main()
