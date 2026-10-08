#!/usr/bin/env python3
"""Bounded-sample prefix-order selector evaluation on captured and held-out data."""
from __future__ import annotations
import copy,hashlib,itertools,json,os,statistics,subprocess,sys,time
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
import substrate_rs as sr
from substrate.seed_loader import engine_rules_only
PROTOCOL=ROOT/"docs/research/engine_substrate/PREFIX_COST_SELECTOR_V1_PREREG_20261001.md"
RUNNER=Path(__file__).resolve();ANALYZER=ROOT/"scripts/analyze_prefix_cost_selector_v1.py"
LOCK=ROOT/"evaluation/substrate_capability/prefix_cost_selector_v1_lock_20261001.json"
RAW=ROOT/"evaluation/reports/prefix_cost_selector_v1_workers_20261001.json"
OUT=ROOT/"evaluation/reports/prefix_cost_selector_v1_20261001.json"
PHOTON_SEED=ROOT/"seeds/photon_retina_per_sensor.json";CAN_SEED=ROOT/"seeds/can_native_reimplementation.json"
PHOTON_CAPTURE=ROOT/"evaluation/reports/photon_retinal_join_order_v1_1_workers_20261001.json"
CAN_CAPTURE=ROOT/"evaluation/reports/can_productive_join_topology_v1_1_workers_20261001.json"
CAN_SCALE_CAPTURE=ROOT/"evaluation/reports/can_productive_join_order_v2_workers_20261001.json"
PHOTON_TARGET="photon_column_synthesizes_retinal_percept";CAN_TARGETS=("can_native_hebbian_mint","can_native_hebbian_reweight")
BEAM=8;SAMPLE_CAP=128;HELDOUT_N=16;REPS=3
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def fingerprint():
 from substrate_rs import _native
 files=(str(RUNNER.relative_to(ROOT)),str(ANALYZER.relative_to(ROOT)),str(PROTOCOL.relative_to(ROOT)),str(PHOTON_SEED.relative_to(ROOT)),str(CAN_SEED.relative_to(ROOT)),str(PHOTON_CAPTURE.relative_to(ROOT)),str(CAN_CAPTURE.relative_to(ROOT)),str(CAN_SCALE_CAPTURE.relative_to(ROOT)),"evaluation/substrate_capability/photon_retinal_join_order_v1_1_lock_20261001.json","evaluation/substrate_capability/can_productive_join_topology_v1_1_lock_20261001.json","evaluation/substrate_capability/can_productive_join_order_v2_lock_20261001.json","substrate/seed_loader.py","runners/dsl/src/rewrite.rs","runners/dsl/src/substrate.rs","runners/dsl/src/scale_audit.rs","runners/dsl/src/py.rs","runners/dsl/src/graph.rs","runners/dsl/python/substrate_rs/_native.build.json")
 return {"files":{p:sha(ROOT/p) for p in files},"native_path":str(Path(_native.__file__).resolve()),"native_sha256":sha(_native.__file__),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}
def build_indexes(edges):
 out=defaultdict(list);inc=defaultdict(list);byrel=defaultdict(list)
 for s,r,t in edges:out[(s,r)].append(t);inc[(t,r)].append(s);byrel[r].append((s,t))
 return out,inc,byrel
def expand(binding,edge,indexes):
 out,inc,byrel=indexes;sv,rel,tv=edge;s=binding.get(sv);t=binding.get(tv);rows=[]
 if s is not None:
  candidates=out.get((s,rel),[])
  for target in candidates:
   if t is not None and target!=t:continue
   updated=dict(binding);updated[tv]=target;rows.append(updated)
  return rows,len(candidates)
 if t is not None:
  candidates=inc.get((t,rel),[])
  for source in candidates:
   updated=dict(binding);updated[sv]=source;rows.append(updated)
  return rows,len(candidates)
 candidates=byrel[rel]
 for source,target in candidates:
  updated=dict(binding);updated[sv]=source;updated[tv]=target;rows.append(updated)
 return rows,len(candidates)
def bounded_sample(rows):
 if len(rows)<=SAMPLE_CAP:return rows
 return [rows[(i*len(rows))//SAMPLE_CAP] for i in range(SAMPLE_CAP)]
def choose_order(pattern,indexes,beam_width=BEAM):
 _,_,byrel=indexes
 first=min(range(len(pattern)),key=lambda i:(len(byrel[pattern[i][1]]),i))
 sv,rel,tv=pattern[first];base=[{sv:s,tv:t} for s,t in byrel[rel]]
 beam=[{"order":[first],"population":float(len(base)),"samples":bounded_sample(base),"estimate":float(len(base))}]
 while len(beam[0]["order"])<len(pattern):
  expanded_beam=[]
  for prefix in beam:
   for i,edge in enumerate(pattern):
    if i in prefix["order"]:continue
    rows=[];attempts=0
    for binding in prefix["samples"]:
     children,cost=expand(binding,edge,indexes);rows.extend(children);attempts+=cost
    scale=prefix["population"]/max(1,len(prefix["samples"]))
    estimated_cost=attempts*scale;estimated_population=len(rows)*scale
    expanded_beam.append({"order":prefix["order"]+[i],"population":estimated_population,"samples":bounded_sample(rows),"estimate":prefix["estimate"]+estimated_cost})
  beam=sorted(expanded_beam,key=lambda p:(p["estimate"],p["order"]))[:beam_width]
 winner=min(beam,key=lambda p:(p["estimate"],p["order"]))
 return winner["order"],winner["estimate"]
def photon_counts(profile,n):
 if profile in ("uniform","correlated","rotated"):
  rows=[]
  for r in range(4):
   if profile=="uniform":rows.append([2]*n)
   elif profile=="correlated":rows.append([1+(i%4) for i in range(n)])
   else:rows.append([1+((i+r)%4) for i in range(n)])
  return rows
 if profile=="heldout_latin":return [[1+((5*i+3*r+i//4+1)%4) for i in range(n)] for r in range(4)]
 raise ValueError(profile)
def photon_edges(n,counts):
 rels=("rod_receptor","l_receptor","m_receptor","s_receptor","has_retinal_percept");edges=[]
 for i in range(n):
  for r,rel in enumerate(rels[:4]):
   for j in range(counts[r][i]):edges.append((i,rel,(r,i,j)))
  edges.append((i,"has_retinal_percept",("percept",i)))
 return edges
def can_pairs(n,q,layout):
 cyclic=[(i,(i+off)%n) for off in range(1,n) for i in range(n)]
 if layout=="cyclic":ordered=cyclic
 elif layout=="hub":
  head=[]
  for i in range(1,n):head.extend(((0,i),(i,0)))
  used=set(head);ordered=head+[p for p in cyclic if p not in used]
 elif layout=="clustered":
  width=max(4,round(n**0.5));head=[(i,j) for i in range(n) for j in range(n) if i!=j and i//width==j//width]
  used=set(head);ordered=head+[p for p in cyclic if p not in used]
 else:raise ValueError(layout)
 return ordered[:q]
def can_edges(n,q,layout):
 edges=[("mt","has_concept",("concept",i)) for i in range(n)]
 for j,(a,b) in enumerate(can_pairs(n,q,layout)):
  edges.extend(((('concept',a),"coactivated_with",('coact',j)),(('coact',j),"coactivation_of",('concept',b))))
 return edges
def native_photon_arm(n,counts,order=None,audit=True):
 inner=sr.Substrate()._inner;manifest=json.loads(PHOTON_SEED.read_text());rule=next(x for x in manifest["rules"] if x.get("name")==PHOTON_TARGET);manifest["rules"]=[];inner.load_seed_manifest(engine_rules_only(manifest))
 activations={"rod_receptor":0.25,"l_receptor":0.75,"m_receptor":0.5,"s_receptor":0.125}
 for i in range(n):
  col=inner.add_node("RetinalColumn",{"fixture_id":f"column:{i}","column_index":i,"column_epoch":1})
  for r,rel in enumerate(("rod_receptor","l_receptor","m_receptor","s_receptor")):
   for j in range(counts[r][i]):
    rec=inner.add_node("Photoreceptor",{"fixture_id":f"{rel}:{i}:{j}","rod_epoch":1,"activation":activations[rel]});inner.add_edge(col,rel,rec,{})
  epoch=0 if i==n-1 else 1;per=inner.add_node("RetinalPercept",{"fixture_id":f"percept:{i}","percept_index":i,"percept_epoch":epoch,"intensity":0.0,"red_green":0.0,"blue_yellow":0.0,"salience":0.0});inner.add_edge(col,"has_retinal_percept",per,{})
 if order is None:inner.add_rule(copy.deepcopy(rule))
 else:
  edited=copy.deepcopy(rule);edited["match"]=[rule["match"][i] for i in order];inner.add_rule_preserving_match_order(edited)
 if audit:
  inner.scale_audit_set_enabled(False);inner.scale_audit_reset();inner.scale_audit_set_per_rule_enabled(True);inner.scale_audit_per_rule_reset();inner.scale_audit_set_enabled(True)
 progress=int(inner.run_rules(100))
 if audit:
  counts_audit={str(k):int(v) for k,v in dict(inner.scale_audit_snapshot()).items()};inner.scale_audit_set_enabled(False);inner.scale_audit_set_per_rule_enabled(False)
 else:counts_audit={}
 terminal=int(inner.run_rules(1));g=inner.graph_to_dict();nodes={x["id"]:x for x in g["nodes"]};tokens={i:nodes[i]["attrs"].get("fixture_id",f"{nodes[i]['type']}:{i}") for i in nodes}
 ns=sorted(((x["type"],x["attrs"]) for x in g["nodes"]),key=lambda x:json.dumps(x,sort_keys=True,default=str));es=sorted((tokens[e["src"]],e["type"],tokens[e["tgt"]],e.get("attrs",{})) for e in g["edges"]);raw=json.dumps({"nodes":ns,"edges":es},sort_keys=True,separators=(",",":"),default=str);digest=hashlib.sha256(raw.encode()).hexdigest()
 percepts={x["attrs"]["fixture_id"]:x["attrs"] for x in g["nodes"] if x["type"]=="RetinalPercept"}
 return {"candidate_tests":int(counts_audit.get("cand_tested",0)),"progress":progress,"terminal":terminal,"digest":digest,"percepts":percepts}
def worker(rep):
 start=fingerprint();n=HELDOUT_N;counts=photon_counts("heldout_latin",n);edges=photon_edges(n,counts);pattern=[tuple(x) for x in next(x for x in json.loads(PHOTON_SEED.read_text())["rules"] if x.get("name")==PHOTON_TARGET)["match"]]
 ix=build_indexes(edges);timings=[];decisions=[]
 for _ in range(21):
  t=time.perf_counter_ns();local_ix=build_indexes(edges);index_ns=time.perf_counter_ns()-t
  t=time.perf_counter_ns();order,estimate=choose_order(pattern,local_ix);search_ns=time.perf_counter_ns()-t
  timings.append({"index_ns":index_ns,"search_ns":search_ns});decisions.append((order,estimate))
 selector_order,estimated=choose_order(pattern,ix)
 default=native_photon_arm(n,counts,None,True)
 permutations=[]
 for order in itertools.permutations(range(len(pattern))):permutations.append({"order":list(order),**native_photon_arm(n,counts,order,True)})
 best=min(permutations,key=lambda x:(x["candidate_tests"],x["order"]))
 selected=next(x for x in permutations if x["order"]==selector_order)
 default_plain=native_photon_arm(n,counts,None,False);selected_plain=native_photon_arm(n,counts,selector_order,False)
 end=fingerprint()
 return {"profile":"heldout_latin","n":n,"replicate":rep,"pid":os.getpid(),"count_matrix":counts,"pair_edge_digest":hashlib.sha256(json.dumps(edges,separators=(",",":")).encode()).hexdigest(),"start":start,"end":end,"selector_order":selector_order,"estimated_work":estimated,"repeat_decisions":[{"order":o,"estimate":e} for o,e in decisions],"timings":timings,"default":default,"permutations":permutations,"best":best,"selected":selected,"default_plain":default_plain,"selected_plain":selected_plain}
def validate_prior_capture(raw_path,lock_path):
 capture=json.loads(raw_path.read_text());prior_lock=json.loads(lock_path.read_text())
 return {"raw":str(raw_path.relative_to(ROOT)),"valid_source_lock":capture["locked_inputs"]==prior_lock==capture["post_run_inputs"] and all(x["start"]==prior_lock==x["end"] for x in capture["runs"])}
def main():
 if sys.argv[1:]==["--lock"]:LOCK.write_text(json.dumps(fingerprint(),indent=2,sort_keys=True)+"\n");print(LOCK);return
 if len(sys.argv)>1 and sys.argv[1]=="--worker":print(json.dumps(worker(int(sys.argv[2])),sort_keys=True));return
 from domains.engine_provenance import build_is_stale
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit("native build stale: "+"; ".join(stale))
 lock=fingerprint()
 if not LOCK.is_file() or json.loads(LOCK.read_text())!=lock:raise SystemExit("source lock missing or stale")
 env=dict(os.environ);env["PYTHONPATH"]=os.pathsep.join((str(ROOT),str(ROOT/"runners/dsl/python"),env.get("PYTHONPATH","")));runs=[]
 for rep in range(REPS):
  p=subprocess.run([sys.executable,str(RUNNER),"--worker",str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True,timeout=600);row=json.loads(p.stdout);runs.append(row);print(f"rep={rep} selector={row['selector_order']} work={row['selected']['candidate_tests']}/{row['best']['candidate_tests']} ns={statistics.median(x['index_ns']+x['search_ns'] for x in row['timings'])}",flush=True)
 historical={"can":historical_can_eval(),"photon":historical_photon_eval()}
 validations=[validate_prior_capture(PHOTON_CAPTURE,ROOT/"evaluation/substrate_capability/photon_retinal_join_order_v1_1_lock_20261001.json"),validate_prior_capture(CAN_CAPTURE,ROOT/"evaluation/substrate_capability/can_productive_join_topology_v1_1_lock_20261001.json"),validate_prior_capture(CAN_SCALE_CAPTURE,ROOT/"evaluation/substrate_capability/can_productive_join_order_v2_lock_20261001.json")]
 post=fingerprint();raw={"locked_inputs":lock,"post_run_inputs":post,"runs":runs,"historical":historical,"historical_capture_validation":validations};RAW.write_text(json.dumps(raw,indent=2,sort_keys=True)+"\n")
 subprocess.run([sys.executable,str(ANALYZER)],cwd=ROOT,env=env,check=True)
 print(json.dumps({"workers":len(runs),"source_stable":lock==post,"raw":str(RAW.relative_to(ROOT))},indent=2))
def historical_photon_eval():
 data=json.loads(PHOTON_CAPTURE.read_text());result=[]
 for profile in ("uniform","correlated","rotated"):
  row=next(x for x in data["runs"] if x["profile"]==profile);edges=photon_edges(12,photon_counts(profile,12));pattern=[tuple(x) for x in next(x for x in json.loads(PHOTON_SEED.read_text())["rules"] if x.get("name")==PHOTON_TARGET)["match"]];order,estimate=choose_order(pattern,build_indexes(edges));selected=next(x for x in row["permutations"] if x["order_indices"]==order);best=row["best"]
  result.append({"profile":profile,"order":order,"estimate":estimate,"selected_work":int(selected["global"].get("cand_tested",0)),"best_order":best["order_indices"],"best_work":int(best["global"].get("cand_tested",0))})
 return result
def historical_can_eval():
 top=json.loads(CAN_CAPTURE.read_text());scale=json.loads(CAN_SCALE_CAPTURE.read_text());seen=set();rows=[]
 for r in top["runs"]:
  key=(r["layout"],r["n"],r["q"])
  if key in seen:continue
  seen.add(key);edges=can_edges(*key[1:],key[0]);data=next(x for x in json.loads(CAN_SEED.read_text())["rules"] if x.get("name")==CAN_TARGETS[0]);pattern=[tuple(x) for x in data["match"]];order,estimate=choose_order(pattern,build_indexes(edges));actual=r["best"];rows.append({"layout":key[0],"n":key[1],"q":key[2],"order":order,"estimate":estimate,"best_order":[0,2,3,1],"selected_work_if_measured_best":int(actual["global"].get("cand_tested",0)),"best_work":int(actual["global"].get("cand_tested",0))})
 for r in scale["runs"]:
  if r["n"]!=128 or r["q"]==0:continue
  key=("cyclic",r["n"],r["q"])
  if key in seen:continue
  seen.add(key);edges=can_edges(key[1],key[2],key[0]);data=next(x for x in json.loads(CAN_SEED.read_text())["rules"] if x.get("name")==CAN_TARGETS[0]);pattern=[tuple(x) for x in data["match"]];order,estimate=choose_order(pattern,build_indexes(edges));actual=r["best"];rows.append({"layout":key[0],"n":key[1],"q":key[2],"order":order,"estimate":estimate,"best_order":[0,2,3,1],"selected_work_if_measured_best":int(actual["global"].get("cand_tested",0)),"best_work":int(actual["global"].get("cand_tested",0))})
 return rows
if __name__=="__main__":main()
