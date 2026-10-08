#!/usr/bin/env python3
"""Held-out prediction probe for GenInfer matrix plus predicate residuals."""
import hashlib,json,platform,subprocess,sys
from pathlib import Path
from domains.engine_provenance import engine_preamble,provenance_line
engine_preamble()
from substrate_rs import _native
ROOT=Path(__file__).resolve().parents[1]
LOCK=ROOT/"docs/research/engine_substrate/SUBSTRATE_GENINFER_HELDOUT_RELATION_PREREG_20260926.md"
OUT=ROOT/"evaluation/reports/substrate_geninfer_heldout_relation_v1_20260926.json"
M=[1,1,0,2];PTS=[(0,0),(1,0),(0,1),(1,1),(2,0),(0,2),(2,1),(1,2)]
GROUPS={"adjacent_01":{"p0":[0,1,4,6],"heldout":[6,7]},"opposite_03":{"p0":[0,3,4,7],"heldout":[7,6]},"adjacent_12":{"p0":[1,2,5,6],"heldout":[6,7]}}
TRAIN_CONDS=("clean","uniform_p0_plus1","inconsistent_p0_plus1_plus2")
HELDOUT_CONDS=("clean","uniform_p0_plus1")
FIELDS=("explained","matrix","residual_dims","transforms","dims","checked")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def build(group,train_cond,hold_cond,rep):
 p0=GROUPS[group]["p0"]; test=GROUPS[group]["heldout"]; tr=[i for i in range(8) if i not in test]
 base=[];train_target=[];held_base=[];held_target=[];a,b,c,d=M
 for i,(r,q) in enumerate(PTS):
  pred="p0" if i in p0 else "p1"; row=[pred,r,q,"red"]; y=[pred,a*r+b*q,c*r+d*q,"red"]
  if i in tr:
   bump=0
   if train_cond=="uniform_p0_plus1" and pred=="p0":bump=1
   if train_cond=="inconsistent_p0_plus1_plus2" and pred=="p0" and i in [j for j in tr if j in p0][:2]:bump=1 if i==[j for j in tr if j in p0][0] else 2
   y[1]+=bump;base.append(row);train_target.append(y)
  else:
   if hold_cond=="uniform_p0_plus1" and pred=="p0":y[1]+=1
   held_base.append(row);held_target.append(y)
 sub=_native.Substrate();sub.add_node("ShapeSignature",{"name":group,"signature":json.dumps(base),"kind":"faculty","faculty":group,"dim_types":["pred","coord:r","coord:c","val"]})
 term={"type":"GenInfer","goal":{"type":"Lit","value":train_target},"codebook_type":"ShapeSignature","max_dims":2,"field":"explained"}
 obs={f:sub.evaluate({**term,"field":f},{}) for f in FIELDS}
 predictions=[];matrix=obs["matrix"]
 for row in held_base:
  pred,r,q,val=row
  if len(matrix)!=4: out=None
  else:
   out=[pred,matrix[0]*r+matrix[1]*q,matrix[2]*r+matrix[3]*q,val]
   for t in obs["transforms"]:
    if t.get("pred") not in (None,pred):continue
    if t.get("kind")=="shift":
     dim=t.get("dim");slot=dim if isinstance(dim,int) else None
     if slot in (1,2):out[slot]+=t.get("delta",0)
    elif t.get("kind")=="subst" and out[3]==t.get("from"):out[3]=t.get("to")
  predictions.append(out)
 return {"group":group,"training_condition":train_cond,"heldout_condition":hold_cond,"repetition":rep,"training_indices":tr,"heldout_indices":test,"training_base":base,"training_target":train_target,"heldout_base":held_base,"heldout_target":held_target,"observation":obs,"predictions":predictions,"heldout_row_correct":[x==y for x,y in zip(predictions,held_target)]}
def main():
 rows=[build(g,t,h,r) for g in GROUPS for t in TRAIN_CONDS for h in HELDOUT_CONDS for r in range(1,6)]
 paths=["scripts/geninfer_heldout_relation_probe_v1.py","scripts/analyze_geninfer_heldout_relation_probe_v1.py","docs/research/engine_substrate/SUBSTRATE_GENINFER_HELDOUT_RELATION_PREREG_20260926.md","runners/dsl/src/shape_decode.rs","runners/dsl/src/term.rs","runners/dsl/python/substrate_rs/_native.build.json"]
 native=Path(_native.__file__).resolve();payload={"schema_version":1,"protocol":"SUBSTRATE_GENINFER_HELDOUT_RELATION_V1","engine":provenance_line(),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),"environment":{"python":sys.version,"platform":platform.platform()},"inputs":{"matrix":M,"points":[list(p) for p in PTS],"groups":GROUPS,"training_conditions":TRAIN_CONDS,"heldout_conditions":HELDOUT_CONDS,"repetitions":5,"fields":FIELDS},"samples":rows,"source_sha256":{p:sha(ROOT/p) for p in paths},"native":{"path":str(native),"sha256":sha(native)},"claim_boundary":"controlled 2-D matrix and residual generalization diagnostic; not natural task accuracy"}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(json.dumps({"output":str(OUT),"samples":len(rows)},indent=2))
if __name__=="__main__":main()
