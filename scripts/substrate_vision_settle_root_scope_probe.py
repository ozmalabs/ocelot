#!/usr/bin/env python3
"""Paired native probe for a benchmark-only World-rooted settle mean."""
from __future__ import annotations
import copy, hashlib, json, platform, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SEED = ROOT / "seeds/vision_settle.json"
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_VISION_SETTLE_ROOT_SCOPE_PROBE_V1_1_AMENDMENT_20260925.md"
OUT = ROOT / "evaluation/reports/substrate_vision_settle_root_scope_probe_v1_1_20260925.json"
CAP = 10_000

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def source(kind):
    return {"type":"Neighbours", "node":{"type":"Var","name":"r"}, "edge_type":"has_sunit", "any_type":False}

def run_arm(sr, doc, b_state, scoped):
    from substrate.seed_loader import engine_rules_only
    inner = sr.Substrate()._inner
    manifest = dict(engine_rules_only(doc))
    rules = [r for r in manifest.get("rules",[]) if r.get("name")=="st_settle"]
    if len(rules)!=1: raise RuntimeError(f"expected one st_settle, got {len(rules)}")
    rule = copy.deepcopy(rules[0])
    if scoped:
        # The two global SUnit sources occur in the mean numerator and denominator.
        def replace(x):
            if isinstance(x, dict):
                if x.get("type")=="NodesOfType" and x.get("node_type")=="SUnit":
                    return source("root")
                return {k:replace(v) for k,v in x.items()}
            if isinstance(x,list): return [replace(v) for v in x]
            return x
        rule = replace(rule); rule["name"]="st_settle_root_scoped_probe"
    manifest["rules"]=[rule]
    inner.load_seed_manifest(manifest)
    params=inner.nodes("SettleParams")
    if len(params)!=1: raise RuntimeError(f"expected singleton SettleParams, got {len(params)}")
    inner.set_attr(params[0],"settle",1.0)
    cells=[]
    for label,state in (("A",1.0),("B",b_state)):
        root=inner.add_node("World",{"name":label,"step":0.0})
        pair=[inner.add_node("SUnit",{"act":state,"aff":0.0,"aff_step":0.0,"act_next":-1.0}) for _ in range(2)]
        for u in pair: inner.add_edge_unchecked(root,"has_sunit",u,{})
        inner.add_edge_unchecked(pair[0],"sunit_neighbour",pair[1],{})
        inner.add_edge_unchecked(pair[1],"sunit_neighbour",pair[0],{})
        cells.append(pair)
    progress=inner.run_rules(CAP)
    outs=[[float(inner.node(u)["attrs"].get("act_next",0.0)) for u in pair] for pair in cells]
    return {"b_initial_act":b_state,"progress":progress,"complete":progress<CAP,"a_act_next":outs[0],"b_act_next":outs[1]}

def main():
    from domains.engine_provenance import engine_preamble
    engine_preamble()
    import substrate_rs as sr
    from substrate_rs import _native
    from domains.engine_provenance import engine_provenance
    doc=json.loads(SEED.read_text())
    arms=[]
    for scoped in (False,True):
        for b in (0.0,1.0): arms.append({"variant":"root_scoped" if scoped else "global","result":run_arm(sr,doc,b,scoped)})
    global_a=[a["result"]["a_act_next"] for a in arms if a["variant"]=="global"]
    scoped_a=[a["result"]["a_act_next"] for a in arms if a["variant"]=="root_scoped"]
    expected_global=[[0.5,0.5],[0.0,0.0]]; expected_scoped=[[0.0,0.0],[0.0,0.0]]
    result={"run_id":"vision-settle-root-scope-probe-20260925","arms":arms,
      "checks":{"all_progress_and_complete":all(a["result"]["progress"]>0 and a["result"]["complete"] for a in arms),
      "global_prediction":global_a==expected_global,"root_scoped_prediction":scoped_a==expected_scoped,
      "global_cross_world_effect":global_a[0]!=global_a[1],"scoped_invariant_to_other_world":scoped_a[0]==scoped_a[1]},
      "provenance":{"python":sys.version,"platform":platform.platform(),"runner_sha256":sha(Path(__file__)),"protocol_sha256":sha(PROTOCOL),"seed_sha256":sha(SEED),"native_extension_path":str(Path(_native.__file__).resolve()),"native_extension_sha256":sha(Path(_native.__file__).resolve()),"engine_provenance":engine_provenance(),"source_sha256":{n:sha(ROOT/"runners/dsl/src"/n) for n in ("rewrite.rs","substrate.rs","term.rs","py.rs")}}}
    result["pass"]=all(result["checks"].values())
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"output":str(OUT.relative_to(ROOT)),"checks":result["checks"],"arms":arms},indent=2))
    if not result["pass"]: raise SystemExit("root-scoped probe did not match preregistered predictions")
if __name__=="__main__": main()
