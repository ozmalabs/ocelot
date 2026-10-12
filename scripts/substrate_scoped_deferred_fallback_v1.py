#!/usr/bin/env python3
"""Measure explicit full-closure fallback when scoped deferred work is pending."""
from __future__ import annotations
import hashlib, json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_SCOPED_DEFERRED_FALLBACK_PREREG_20260926.md"
LOCK = ROOT / "evaluation/substrate_capability/scoped_deferred_fallback_v1_2_lock_20260926.json"
OUT = ROOT / "evaluation/reports/substrate_scoped_deferred_fallback_v1_2_20260926.json"
SIZES, REPS = (2, 4, 8), 2
CAP = 20_000

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def build(pair_count, arm):
    from substrate_rs import Substrate, Attr, Eq, Lit, Not, Var, _native
    from substrate_rs.ext import add_rule
    s = Substrate()
    controller = s.add_node("Microtheory", {"name": "identity_controller"})
    anchor = s.add_node("Anchor", {})
    s.add_edge_unchecked(controller, "has_concept", anchor)
    s.add_edge_unchecked(anchor, "has_anchor", anchor)
    prev, cur = [], []
    owners = []
    for i in range(pair_count):
        mt_prev = s.add_node("Microtheory", {"name": f"prev_frame_{i}"})
        mt_cur = s.add_node("Microtheory", {"name": f"cur_frame_{i}"})
        p = s.add_node("PrevPercept", {"feat": [float(i * 10), 0.0]})
        c = s.add_node("CurPercept", {"feat": [float(i * 10) + 0.05, 0.05]})
        s.add_edge_unchecked(mt_prev, "has_concept", p)
        s.add_edge_unchecked(mt_cur, "has_concept", c)
        prev.append(p); cur.append(c); owners.extend((mt_prev, mt_cur))
    add_rule(s._inner, "deferred_fallback_track_identity",
        [("mt", "has_concept", "a"), ("a", "has_anchor", "a")],
        [["track_identity",
          {"__term__": {"type": "NodesOfType", "node_type": "PrevPercept"}},
          {"__term__": {"type": "NodesOfType", "node_type": "CurPercept"}},
          "feat", None, None, "identity", 1.0],
         ["set_attr", "a", "tracking_done", True]],
        where=Not(Eq(Attr(Var("a"), "tracking_done"), Lit(True))))
    scoped = None
    global_report = None
    if arm == "full":
        global_report = s._inner.run_rules_report(CAP, False)
    else:
        scoped = s._inner.run_rules_scoped_delta_report(controller, 1, False)
        if arm == "scoped_fallback" and scoped["deferred_effects_pending"]:
            global_report = s._inner.run_rules_report(CAP, False)
    identities = {
        "previous": s._inner.get_attr_many(prev, "identity"),
        "current": s._inner.get_attr_many(cur, "identity"),
        "controller_done": s.node(anchor)["attrs"].get("tracking_done"),
    }
    if arm in ("full", "scoped_fallback"):
        terminal = s._inner.run_rules_report(CAP, False)
        terminal_progress = int(terminal["progress_steps"])
        terminal_status = terminal["status"]
    else:
        terminal_progress = None; terminal_status = None
    result = {"arm": arm, "pair_count": pair_count, "frame_count": pair_count * 2,
        "pid": os.getpid(), "identities": identities,
        "scoped_report": None if scoped is None else {
            "progress_steps": scoped["progress_steps"],
            "hit_progress_budget": scoped["hit_progress_budget"],
            "deferred_effects_pending": scoped["deferred_effects_pending"],
            "affected_microtheories": scoped["affected_microtheories"],
            "affected_nodes": scoped["affected_nodes"], "affected_edges": scoped["affected_edges"]},
        "global_report": None if global_report is None else global_report,
        "terminal_global_status": terminal_status, "terminal_global_progress": terminal_progress,
        "native_extension_sha256": sha(Path(_native.__file__).resolve())}
    return result

def inputs():
    ps={"protocol":PROTOCOL,"runner":Path(__file__).resolve(),
        "analyzer":ROOT/"scripts/analyze_substrate_scoped_deferred_fallback_v1.py",
        "rewrite":ROOT/"runners/dsl/src/rewrite.rs","substrate":ROOT/"runners/dsl/src/substrate.rs",
        "term":ROOT/"runners/dsl/src/term.rs","py_binding":ROOT/"runners/dsl/src/py.rs",
        "native_build_manifest":ROOT/"runners/dsl/python/substrate_rs/_native.build.json"}
    return {k:sha(v) for k,v in ps.items()}

def main():
    if sys.argv[1:]==["--lock"]: print(json.dumps(inputs(),indent=2,sort_keys=True)); return
    if len(sys.argv)==4 and sys.argv[1]=="--worker": print(json.dumps(build(int(sys.argv[2]),sys.argv[3]),sort_keys=True)); return
    locked=inputs()
    if json.loads(LOCK.read_text()) != locked: raise SystemExit("input lock mismatch")
    env=dict(os.environ); env["PYTHONPATH"]=f"{ROOT/'runners/dsl/python'}:{ROOT}:{env.get('PYTHONPATH','')}"
    runs=[]
    for count in (1,2,4):
      for rep in range(REPS):
       for arm in ("full","scoped_only","scoped_fallback"):
        cmd=[sys.executable,str(Path(__file__).resolve()),"--worker",str(count),arm]
        row=json.loads(subprocess.check_output(cmd,cwd=ROOT,env=env,text=True)); row["replicate"]=rep
        runs.append(row); print(f"pairs={count} rep={rep} arm={arm} pending={None if row['scoped_report'] is None else row['scoped_report']['deferred_effects_pending']}",flush=True)
    payload={"schema_version":1,"run_id":"substrate-scoped-deferred-fallback-v1_2-20260926",
      "claim_boundary":"one synthetic TrackIdentity deferred-effect family; explicit global fallback only",
      "locked_inputs":locked,"runs":runs}
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
    print(f"raw report: {OUT.relative_to(ROOT)} ({len(runs)} workers)")

if __name__=="__main__": main()
