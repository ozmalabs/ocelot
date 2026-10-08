#!/usr/bin/env python3
"""Generated-owner fanout sweep for scoped dependency notifications."""
from __future__ import annotations
import hashlib, json, sys, time
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "runners/dsl/python"), str(ROOT)]
from domains.engine_provenance import rust_source_fingerprint
from substrate_rs import And, Attr, Count, Eq, InNeighbours, Lit, NodeID, Not, Substrate, Var
from substrate_rs.ext import add_rule

OUT = ROOT / "evaluation/reports/substrate_scoped_multi_frame_fanout_v1_20260926.json"
LOCK = ROOT / "docs/research/engine_substrate/SUBSTRATE_SCOPED_MULTI_FRAME_FANOUT_PREREG_20260926.md"
NATIVE = ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so"

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def fixture(k):
    s = Substrate()
    roles = ["A"] + [f"T{i}" for i in range(k)]
    mts = [s.add_node("Microtheory", {"role": r}) for r in roles]
    src = s.add_node("Concept", {"trigger": True, "emitted": False})
    targets = [s.add_node("Concept", {"state": 0}) for _ in range(k)]
    for mt, c in zip(mts, [src] + targets): s.add_edge_unchecked(mt, "has_concept", c)
    match = [("ma", "has_concept", "x")] + [(f"m{i}", "has_concept", f"y{i}") for i in range(k)]
    effects = [["add_node", "bridge", "Concept", {"delete_request": False}],
               ["add_edge", "ma", "has_concept", "bridge"]]
    effects += [["add_edge", "bridge", "causal_influence", f"y{i}"] for i in range(k)]
    effects += [["set_attr", "x", "emitted", True]]
    where = [Eq(Attr(Var("x"), "trigger"), Lit(True)), Eq(Attr(Var("x"), "emitted"), Lit(False)),
             Eq(Attr(Var("ma"), "role"), Lit("A"))]
    where += [Eq(Attr(Var(f"m{i}"), "role"), Lit(f"T{i}")) for i in range(k)]
    add_rule(s._inner, "mint_fanout_bridge", match, effects, where=And(where))
    add_rule(s._inner, "consume_influence", [("mt", "has_concept", "target")], [["set_attr", "target", "state", 1]],
             where=And([Eq(Attr(Var("target"), "state"), Lit(0)), Not(Eq(Count(InNeighbours(Var("target"), "causal_influence")), Lit(0)))]))
    add_rule(s._inner, "retract_influence", [("mt", "has_concept", "target")], [["set_attr", "target", "state", 0]],
             where=And([Eq(Attr(Var("target"), "state"), Lit(1)), Eq(Count(InNeighbours(Var("target"), "causal_influence")), Lit(0))]))
    add_rule(s._inner, "delete_bridge", [("ma", "has_concept", "bridge"), ("mb", "has_concept", "target"), ("bridge", "causal_influence", "target")], [["del_node", "bridge"]],
             where=And([Eq(Attr(Var("bridge"), "delete_request"), Lit(True)), Eq(Attr(Var("mb"), "role"), Lit("T0"))]))
    return s, mts, src, targets

def projection(s, mts, src, targets):
    bridges = [n for n in s.nodes("Concept") if "delete_request" in s.node(n)["attrs"]]
    b = bridges[0] if bridges else None
    return {"emitted": s.node(src)["attrs"].get("emitted"),
            "states": [s.node(x)["attrs"].get("state") for x in targets],
            "bridge_id": int(b.value) if b else None,
            "owned": bool(b and s.has_edge(mts[0], "has_concept", b)),
            "dependencies": [bool(b and s.has_edge(b, "causal_influence", x)) for x in targets],
            "owners": [int(x.value) for x in mts]}

def settle(s, seeds, suppressed=()):
    q = deque(seeds); queued = {int(x.value) for x in q}; reports=[]; notified=set(); turns=0
    while q and turns < 1000:
        mt=q.popleft(); queued.remove(int(mt.value)); turns+=1
        r=s._inner.run_rules_scoped_delta_report(mt, 1000, False); reports.append(r)
        if r["hit_progress_budget"] or r["deferred_effects_pending"]: break
        if r["progress_steps"]:
            for owner0 in r["affected_microtheories"]:
                owner=int(owner0); notified.add(owner)
                if owner not in suppressed and owner not in queued:
                    q.append(NodeID(owner)); queued.add(owner)
    return {"complete": not q and turns < 1000 and all(not r["hit_progress_budget"] and not r["deferred_effects_pending"] for r in reports),
            "reports": reports, "notified": sorted(notified), "turns": turns}

def run_event(k, omit=()):
    s,mts,src,targets=fixture(k); birth=settle(s,[mts[0]],omit); born=projection(s,mts,src,targets)
    if born["bridge_id"] is not None:
        s.set_attr(NodeID(born["bridge_id"]),"delete_request",True); deletion=settle(s,[mts[0]])
    else: deletion={"complete":False,"reports":[],"notified":[],"turns":0}
    return {"birth":birth,"born":born,"deletion":deletion,"ended":projection(s,mts,src,targets)}

def run_full(k):
    s,mts,src,targets=fixture(k); birth=s._inner.run_rules_report(1000,False); born=projection(s,mts,src,targets)
    if born["bridge_id"] is not None:
        s.set_attr(NodeID(born["bridge_id"]),"delete_request",True); deletion=s._inner.run_rules_report(1000,False)
    else: deletion={"status":"no_bridge"}
    return {"birth":birth,"born":born,"deletion":deletion,"ended":projection(s,mts,src,targets)}

def main():
    cells=[]
    for k in (2,4,8,16):
        t=time.perf_counter(); event=run_event(k); elapsed=time.perf_counter()-t; oracle=run_full(k)
        owners=event["born"]["owners"]
        gates={"birth_owner_set_exact": sorted(set(event["birth"]["notified"]))==owners,
               "deletion_owner_set_exact": sorted(set(event["deletion"]["notified"]))==owners,
               "birth_queue_complete":event["birth"]["complete"],"deletion_queue_complete":event["deletion"]["complete"],
               "birth_matches_full":event["born"]==oracle["born"],"deletion_matches_full":event["ended"]==oracle["ended"],
               "full_fixpoints":oracle["birth"]["status"]==oracle["deletion"]["status"]=="fixed_point",
               "all_dependencies_created":all(event["born"]["dependencies"]),
               "all_dependencies_removed":not any(event["ended"]["dependencies"])}
        omissions=[]
        for omitted_owner in owners[1:]:
            control=run_event(k,(omitted_owner,))
            omissions.append({"owner":omitted_owner,"diverges":control["born"]!=oracle["born"]})
        gates["every_boundary_omission_detected"]=all(x["diverges"] for x in omissions)
        cells.append({"fanout":k,"gates":gates,"event":event,"omission_controls":omissions,"oracle":oracle,
                      "elapsed_seconds":elapsed,"birth_turns":event["birth"]["turns"],"deletion_turns":event["deletion"]["turns"]})
    inputs={"lock":sha(LOCK),"runner":sha(Path(__file__)),"graph_rs":sha(ROOT/"runners/dsl/src/graph.rs"),
            "substrate_rs":sha(ROOT/"runners/dsl/src/substrate.rs"),"rewrite_rs":sha(ROOT/"runners/dsl/src/rewrite.rs"),
            "py_rs":sha(ROOT/"runners/dsl/src/py.rs"),"native":sha(NATIVE),"source_fingerprint":rust_source_fingerprint(str(ROOT))}
    payload={"protocol":"SUBSTRATE_SCOPED_MULTI_FRAME_FANOUT_PREREG_20260926_V1","inputs":inputs,"cells":cells}
    OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"output":str(OUT),"all_gates_pass":all(all(c["gates"].values()) for c in cells),
                      "cells":[{"fanout":c["fanout"],"gates":c["gates"],"birth_turns":c["birth_turns"],"deletion_turns":c["deletion_turns"]} for c in cells]},indent=2))
    if not all(all(c["gates"].values()) for c in cells): raise SystemExit("gate failure")

if __name__=="__main__": main()
