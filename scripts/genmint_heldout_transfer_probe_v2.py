#!/usr/bin/env python3
"""Full-seed recognition/mint/reuse with held-out relation transfer scoring."""
import hashlib,json,platform,random,subprocess,sys,time
from pathlib import Path
from domains.engine_provenance import engine_preamble,provenance_line
engine_preamble()
from substrate.boot_core import boot_core
from domains import reflective_faculty as rf
from substrate_rs import _native
ROOT=Path(__file__).resolve().parents[1];LOCK=ROOT/"docs/research/engine_substrate/SUBSTRATE_GENMINT_HELDOUT_TRANSFER_V2_PREREG_20260926.md";OUT=ROOT/"evaluation/reports/substrate_genmint_heldout_transfer_v2_20260926.json"
M=[1,1,0,2];PTS=[(0,0),(1,0),(0,1),(1,1),(2,0),(0,2),(2,1),(1,2),(3,1),(1,3)]
GROUPS={"adjacent_01":{"p0":[0,1,4,6,8],"heldout":[6,7,8,9]},"opposite_03":{"p0":[0,3,4,7,8],"heldout":[6,7,8,9]},"adjacent_12":{"p0":[1,2,5,6,8],"heldout":[6,7,8,9]}}
TRAIN_CONDS=("clean","uniform_p0_plus1","inconsistent_p0_plus1_plus2");HOLD_CONDS=("clean","uniform_p0_plus1");ARMS=(False,True);REPS=5;SEED=20260928
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def relation(i,p0,matrix=M):
 r,q=PTS[i];p="p0" if i in p0 else "p1";a,b,c,d=matrix;return [p,r,q,"red"],[p,a*r+b*q,c*r+d*q,"red"]
def linear_gens(s):
 out=[]
 for n in s.nodes("DimensionGenerator"):
  a=s.node(n)["attrs"]
  if a.get("kind")=="linear":out.append({"id":str(n),"name":a.get("name"),"matrix":list(a.get("matrix") or []),"coord_dims":list(a.get("coord_dims") or [])})
 return out
def transforms(s,obs):
 out=[]
 for n in s.neighbours(obs,"has_transform"):
  a=s.node(n)["attrs"];out.append({k:a.get(k) for k in ("source","generator","dim","k","ks","transforms","dims","deltas","delta","base","generators") if k in a})
 return out
def add_obs(s,ag,native,sig,dim_types,key):
 epoch=s.node(ag)["attrs"].get("codebook_epoch") or 0.0
 n=s.add_node("Observation",{"signature":sig,"key":["heldout_transfer",*key],"status":"decoded","residual":sig,"decoded_epoch":epoch,"dim_types":dim_types});s.add_edge(ag,"observed",n)
 t0=time.perf_counter();native.run_rules();dt=time.perf_counter()-t0;a=s.node(n)["attrs"]
 return n,{"status":a.get("status"),"residual":a.get("residual"),"covered_by":a.get("covered_by"),"decoded_epoch":a.get("decoded_epoch"),"transforms":transforms(s,n),"closure_seconds":dt,"graph_nodes":len(list(s.nodes())),"linear_generators":linear_gens(s),"capability_axes":len(list(s.nodes("CapabilityAxis")))}
def run_one(group,train_cond,hold_cond,enabled,rep):
 p0=GROUPS[group]["p0"];held=GROUPS[group]["heldout"];train=[i for i in range(len(PTS)) if i not in held];dt=["pred","coord:r","coord:c","val"]
 base=[];target=[];p0train=[i for i in train if i in p0]
 for i in train:
  b,y=relation(i,p0);b=list(b);y=list(y)
  if train_cond=="uniform_p0_plus1" and i in p0:y[1]+=1
  if train_cond=="inconsistent_p0_plus1_plus2" and i in p0train[:2]:y[1]+=1 if i==p0train[0] else 2
  base.append(b);target.append(y)
 s,ag=boot_core();native=rf._native_eval2(s);rf._ensure_shape_decode_loop(s,native,ag)
 if enabled:s.set_attr(ag,"gen_infer_enabled",1.0)
 initial_gens=linear_gens(s)
 s.add_node("ShapeSignature",{"name":f"train_{group}","signature":json.dumps(base),"kind":"faculty","faculty":f"train_{group}","dim_types":dt})
 axis0=len(list(s.nodes("CapabilityAxis")));n1,stage1=add_obs(s,ag,native,target,dt,[group,train_cond,str(enabled),str(rep),"train"]);stage1["observation"]=str(n1);stage1["quanta_added"]=len(list(s.nodes("CapabilityAxis")))-axis0
 hbase=[];htarget=[]
 for i in held:
  b,y=relation(i,p0);b=list(b);y=list(y)
  if hold_cond=="uniform_p0_plus1" and i in p0:y[1]+=1
  hbase.append(b);htarget.append(y)
 s.add_node("ShapeSignature",{"name":f"heldout_{group}","signature":json.dumps(hbase),"kind":"faculty","faculty":f"heldout_{group}","dim_types":dt})
 n2,stage2=add_obs(s,ag,native,htarget,dt,[group,train_cond,hold_cond,str(enabled),str(rep),"heldout"]);stage2["observation"]=str(n2);stage2["quanta_added"]=len(list(s.nodes("CapabilityAxis")))-axis0-stage1["quanta_added"]
 return {"group":group,"training_condition":train_cond,"heldout_condition":hold_cond,"gen_infer_enabled":enabled,"repetition":rep,"training_indices":train,"heldout_indices":held,"training_base":base,"training_target":target,"heldout_base":hbase,"heldout_target":htarget,"initial_linear_generators":initial_gens,"train":stage1,"heldout":stage2,"final_linear_generators":linear_gens(s)}
def main():
 t0=time.perf_counter();cells=[(g,t,h,e) for g in GROUPS for t in TRAIN_CONDS for h in HOLD_CONDS for e in ARMS];rng=random.Random(SEED);samples=[];schedule=[]
 for rep in range(1,REPS+1):
  order=cells.copy();rng.shuffle(order);schedule.append([[*x] for x in order])
  for g,t,h,e in order:samples.append(run_one(g,t,h,e,rep))
 native=Path(_native.__file__).resolve();paths=["scripts/genmint_heldout_transfer_probe_v2.py","scripts/analyze_genmint_heldout_transfer_probe_v2.py","docs/research/engine_substrate/SUBSTRATE_GENMINT_HELDOUT_TRANSFER_V2_PREREG_20260926.md","seeds/shape_decode_loop.json","domains/reflective_faculty.py","domains/engine_provenance.py","substrate/boot_core.py","runners/dsl/src/shape_decode.rs","runners/dsl/src/term.rs","runners/dsl/python/substrate_rs/_native.build.json"]
 report={"protocol":"SUBSTRATE_GENMINT_HELDOUT_TRANSFER_V2","engine":provenance_line(),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),"environment":{"python":sys.version,"platform":platform.platform()},"inputs":{"matrix":M,"points":[list(x) for x in PTS],"groups":GROUPS,"training_conditions":TRAIN_CONDS,"heldout_conditions":HOLD_CONDS,"arms":ARMS,"repeats":REPS,"schedule_seed":SEED,"schedule":schedule},"samples":samples,"runtime_seconds":time.perf_counter()-t0,"source_sha256":{p:sha(ROOT/p) for p in paths},"native":{"path":str(native),"sha256":sha(native)},"claim_boundary":"authored 2-D full-seed acquisition and four-relation held-out transfer; not natural task generalization"}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True,default=str)+"\n");print(json.dumps({"output":str(OUT),"samples":len(samples),"runtime_seconds":report["runtime_seconds"]},indent=2))
if __name__=="__main__":main()
