#!/usr/bin/env python3
"""Full-seed mint/reuse probe for repeated-predicate residual ambiguity."""
from __future__ import annotations
import hashlib,json,platform,random,subprocess,sys,time
from pathlib import Path
from domains.engine_provenance import engine_preamble,provenance_line
engine_preamble()
from substrate.boot_core import boot_core
from domains import reflective_faculty as rf
from substrate_rs import _native
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"evaluation/reports/substrate_genmint_residual_robustness_v1_20260926.json"
M=[1,1,0,2];LAYOUTS={"original":[(0,0),(1,0),(2,0),(0,2)],"orthogonal_pairs":[(0,0),(0,1),(1,0),(1,1)],"paired_square":[(0,0),(1,0),(0,1),(1,1)]};PREDS=["p0","p0","p1","p1"]
CONDS=["positive","corrupt_p0_r_1","corrupt_p0_r_2","corrupt_p0_r_3"];MODES=["no_identity","stable_identity"];FIELDS=["status","residual","transform_checked","transform_explained","dim_checked","dim_explained","gen_checked","gen_explained","decoded_epoch"]
REPS=5;SEED=20260926
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def mapped(rows,slots,matrix):
 mins=[min(row[i] for row in rows) for i in slots];out=[]
 for row in rows:
  rr=list(row)
  for i,slot in enumerate(slots):rr[slot]=sum(matrix[2*i+j]*(row[slots[j]]-mins[j]) for j in range(2))
  out.append(rr)
 return out
def linear_generators(s):
 result=[]
 for node in s.nodes("DimensionGenerator"):
  attrs=s.node(node)["attrs"]
  if attrs.get("kind")=="linear":result.append({"node":str(node),"name":attrs.get("name"),"matrix":list(attrs.get("matrix") or []),"coord_dims":list(attrs.get("coord_dims") or [])})
 return result
def observe(s,ag,goal,dim_types,key):
 epoch=s.node(ag)["attrs"].get("codebook_epoch") or 0.0
 node=s.add_node("Observation",{"signature":goal,"key":["mint_robustness",*key],"status":"decoded","residual":goal,"decoded_epoch":epoch,"dim_types":dim_types})
 s.add_edge(ag,"observed",node)
 return node
def run_sequence(layout,mode,condition,enabled,repetition):
 points=LAYOUTS[layout];stable=(mode=="stable_identity");slots=[2,3] if stable else [1,2]
 dim_types=["pred","id","coord:r","coord:c","val"] if stable else ["pred","coord:r","coord:c","val"]
 base=[]
 for i,(pred,(r,c)) in enumerate(zip(PREDS,points)):
  base.append([pred,f"rel{i}",r,c,"red"] if stable else [pred,r,c,"red"])
 first=mapped(base,slots,M);second=mapped(first,slots,M)
 if condition!="positive":first[0][slots[0]]+=int(condition.rsplit("_",1)[1])
 s,ag=boot_core();native=rf._native_eval2(s);rf._ensure_shape_decode_loop(s,native,ag)
 if enabled:s.set_attr(ag,"gen_infer_enabled",1.0)
 s.add_node("ShapeSignature",{"name":layout,"signature":json.dumps(base),"kind":"faculty","faculty":layout,"dim_types":dim_types})
 axis_start=len(list(s.nodes("CapabilityAxis")));initial_generators=linear_generators(s);steps=[]
 for stage,goal in (("first_member",first),("clean_M2",second)):
  obs=observe(s,ag,goal,dim_types,[layout,mode,condition,str(enabled),str(repetition),stage])
  before_axis=len(list(s.nodes("CapabilityAxis")));start=time.perf_counter();native.run_rules();elapsed=time.perf_counter()-start
  attrs=s.node(obs)["attrs"];transforms=[]
  for tnode in s.neighbours(obs,"has_transform"):
   ta=s.node(tnode)["attrs"];transforms.append({k:ta.get(k) for k in ("kind","dim","delta","pred") if k in ta})
  steps.append({"stage":stage,"goal":goal,"observation":{"attrs":{k:attrs.get(k) for k in FIELDS},"transforms":transforms},"axis_count":len(list(s.nodes("CapabilityAxis"))),"quanta_added":len(list(s.nodes("CapabilityAxis")))-before_axis,"linear_generators":linear_generators(s),"closure_seconds":elapsed,"graph_nodes":len(list(s.nodes()))})
 return {"layout":layout,"mode":mode,"condition":condition,"gen_infer_enabled":enabled,"repetition":repetition,"base":base,"dim_types":dim_types,"initial_linear_generators":initial_generators,"steps":steps,"total_quanta":len(list(s.nodes("CapabilityAxis")))-axis_start,"final_linear_generators":linear_generators(s)}
def boot(enabled):
 s,ag=boot_core();native=rf._native_eval2(s);rf._ensure_shape_decode_loop(s,native,ag)
 if enabled:s.set_attr(ag,"gen_infer_enabled",1.0)
 return s,ag,native
def main():
 started=time.perf_counter();cells=[(l,m,c,e) for l in LAYOUTS for m in MODES for c in CONDS for e in (False,True)];rng=random.Random(SEED);schedules={};samples=[]
 for rep in range(1,REPS+1):
  order=cells.copy();rng.shuffle(order);schedules[str(rep)]=[list(x) for x in order]
  for layout,mode,condition,enabled in order:samples.append(run_sequence(layout,mode,condition,enabled,rep))
 native_path=Path(_native.__file__).resolve();paths=["scripts/genmint_residual_robustness_probe_v1.py","scripts/analyze_substrate_genmint_residual_robustness_probe_v1.py","docs/research/engine_substrate/SUBSTRATE_GENMINT_RESIDUAL_ROBUSTNESS_PREREG_20260926.md","seeds/shape_decode_loop.json","domains/reflective_faculty.py","domains/engine_provenance.py","substrate/boot_core.py","runners/dsl/src/shape_decode.rs","runners/dsl/src/term.rs","runners/dsl/python/substrate_rs/_native.build.json"]
 report={"schema_version":1,"run_id":"substrate-genmint-residual-robustness-v1-20260926","engine":provenance_line(),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),"environment":{"python":sys.version,"platform":platform.platform()},"protocol":{"matrix":M,"layouts":{k:[list(p) for p in v] for k,v in LAYOUTS.items()},"predicates":PREDS,"conditions":CONDS,"modes":MODES,"enabled_arms":[False,True],"stages":["first_member","clean_M2"],"fields":FIELDS,"repetitions":REPS,"schedule_seed":SEED,"schedule_by_repetition":schedules,"timed_region":"native.run_rules() only for each observation"},"samples":samples,"runtime_seconds":time.perf_counter()-started,"provenance":{"source_sha256":{p:sha(ROOT/p) for p in paths},"native_extension_path":str(native_path),"native_extension_sha256":sha(native_path)},"claim_boundary":"End-to-end production seed on three small repeated-predicate layouts, one 2-D map, and three localized coordinate perturbations; not a natural-noise or general learning claim."}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True,default=str)+"\n");print(json.dumps({"output":str(OUT),"samples":len(samples),"runtime_seconds":report["runtime_seconds"]},indent=2))
if __name__=="__main__":main()
