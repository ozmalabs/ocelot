#!/usr/bin/env python3
"""Recompute ID-reference-aware graph fingerprints from retained final snapshots."""
from __future__ import annotations
import base64, collections, gzip, hashlib, json, re, zlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CAPTURES={
    "fixed_seed_global": ROOT/"evaluation/reports/area_settlement_fixed_seed_repeatability_v1_20261006/capture.json.gz",
    "original_three_arms": ROOT/"evaluation/reports/held_topic_area_settlement_parity_v1_1_20261005/capture.json.gz",
}
OUT=ROOT/"evaluation/reports/settlement_snapshot_semantic_fingerprint_v1_analysis_20261006.json"

def sha(v): return hashlib.sha256(v).hexdigest()
def encoded_graph(run, mode):
    if mode=="fixed_seed_global": return run["turns"][-1]["final_snapshot_zlib_b64"]
    return run["turns"][-1]["settlement_parity"]["graph_snapshot_zlib_b64"]

def semantic_wl(blob, rounds=4):
    graph=json.loads(zlib.decompress(base64.b64decode(blob)))
    nodes={int(n["id"]):n for n in graph["nodes"]}
    ref_edges=collections.defaultdict(list)

    def walk(value,path=()):
        if isinstance(value,dict):
            if set(value)=={"__nid__"}:
                try: yield path,int(value["__nid__"])
                except (TypeError,ValueError): pass
            else:
                for key,item in value.items(): yield from walk(item,path+(str(key),))
        elif isinstance(value,list):
            for index,item in enumerate(value): yield from walk(item,path+(str(index),))

    def ref_target(value):
        match=re.search(r"(?:#)?(\d+)$",str(value))
        if match:
            target=int(match.group(1))
            if target in nodes: return target
        return None

    def core(node_id,node):
        attrs={k:v for k,v in node.get("attrs",{}).items()
               if not (node.get("type")=="SystemModel" and k in ("ts","runtime_s"))}
        for path,target in walk(attrs):
            if target in nodes: ref_edges[node_id].append(("attrref:"+".".join(path),target))
        for key,value in attrs.items():
            if "foreign" in key.lower() or not (key.lower().endswith("_id") or key.lower().endswith("_ids")):
                continue
            values=value.get("__list__",[]) if isinstance(value,dict) and "__list__" in value else (value if isinstance(value,list) else [value])
            for index,item in enumerate(values):
                target=ref_target(item)
                if target is not None: ref_edges[node_id].append((f"attrref:{key}[{index}]",target))
        def clean(value,key=""):
            if isinstance(value,dict):
                if set(value)=={"__nid__"}: return {"__nref__":True}
                return {k:clean(v,k) for k,v in value.items()}
            if isinstance(value,list): return [clean(v,key) for v in value]
            if (key.lower().endswith("_id") or key.lower().endswith("_ids")) and "foreign" not in key.lower():
                if ref_target(value) is not None: return {"__nref__":True}
            return value
        return json.dumps({"type":node.get("type"),"attrs":clean(attrs)},sort_keys=True,separators=(",",":"),default=str)

    cores={nid:core(nid,node) for nid,node in nodes.items()}
    colors={nid:sha(label.encode()) for nid,label in cores.items()}
    edges=[(int(e["src"]),int(e["tgt"]),str(e["type"]),
            json.dumps(e.get("attrs",{}),sort_keys=True,separators=(",",":"),default=str))
           for e in graph["edges"]]
    for _ in range(rounds):
        neighborhoods={nid:[] for nid in nodes}
        for src,tgt,kind,attrs in edges:
            neighborhoods[src].append(("out",kind,attrs,colors[tgt]))
            neighborhoods[tgt].append(("in",kind,attrs,colors[src]))
        for src,refs in ref_edges.items():
            for kind,tgt in refs: neighborhoods[src].append(("ref",kind,"",colors[tgt]))
        colors={nid:sha((cores[nid]+"|"+json.dumps(sorted(neighborhoods[nid]),separators=(",",":"))).encode())
                for nid in nodes}
    payload={"nodes":sorted(colors.values()),
             "edges":sorted((colors[s],k,colors[t],a) for s,t,k,a in edges),
             "attr_refs":sorted((colors[s],k,colors[t]) for s,refs in ref_edges.items() for k,t in refs)}
    return sha(json.dumps(payload,separators=(",",":")).encode()),{
        "node_count":len(nodes),"edge_count":len(edges),
        "volatile_system_model_nodes":sum(n.get("type")=="SystemModel" and ("ts" in n.get("attrs",{}) or "runtime_s" in n.get("attrs",{})) for n in nodes.values()),
        "attribute_id_refs":sum(len(refs) for refs in ref_edges.values())}

rows=[]
for mode,path in CAPTURES.items():
    capture=json.loads(gzip.decompress(path.read_bytes()))
    for run in capture["runs"]:
        digest,counts=semantic_wl(encoded_graph(run,mode))
        rows.append({"capture":mode,"arm":run["arm"],"replicate":run["replicate"],"semantic_wl_sha256":digest,**counts})
groups=collections.defaultdict(list)
for row in rows: groups[(row["capture"],row["arm"])].append(row["semantic_wl_sha256"])
summary={f"{capture}/{arm}":{"runs":len(values),"distinct_fingerprints":len(set(values)),"fingerprints":values}
         for (capture,arm),values in groups.items()}
analysis={"schema_version":1,"rows":rows,"group_summary":summary,
 "fixed_seed_global_repeatable":len(set(groups[("fixed_seed_global","global")]))==1,
 "original_global_repeatable":len(set(groups[("original_three_arms","global")]))==1,
 "original_barrier_repeatable":len(set(groups[("original_three_arms","barrier")]))==1,
 "original_async_repeatable":len(set(groups[("original_three_arms","async")]))==1,
 "original_all_arms_semantic_final_equal":len({values[0] for (capture,_),values in groups.items() if capture=="original_three_arms"})==1,
 "excluded_fields":"SystemModel.ts and SystemModel.runtime_s; graph reference attributes are normalized into labeled directed edges. WL equality is not a complete graph isomorphism proof."}
OUT.write_text(json.dumps(analysis,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:v for k,v in analysis.items() if k not in ("rows","group_summary")},indent=2))
