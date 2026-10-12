#!/usr/bin/env python3
"""Reconstruct GenInfer's bounded numeric candidate set/ranking on captured cases."""
from __future__ import annotations
import hashlib,json,platform,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"evaluation/reports/substrate_geninfer_relation_identity_ablation_v1_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_geninfer_candidate_ranking_v1_20260926.json"
GENERATING=[1,1,0,2]; MODES=["no_identity","stable_identity"]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def candidate(base,goal,matrix,coord_slots,max_dims):
 mins=[min(row[i] for row in base) for i in coord_slots]
 transformed=[]
 for row in base:
  out=list(row)
  for out_i,slot in enumerate(coord_slots):
   out[slot]=sum(matrix[out_i*2+j]*(row[coord_slots[j]]-mins[j]) for j in range(2))
  transformed.append(out)
 h=sorted(transformed);o=sorted(goal)
 if len(h)!=len(o) or any(x[0]!=y[0] or len(x)!=len(y) for x,y in zip(h,o)):return None
 dims=sorted({i for x,y in zip(h,o) for i in range(1,len(x)) if x[i]!=y[i]})
 transforms=[]
 for slot in dims:
  pairs=[(y[0],x[slot],y[slot]) for x,y in zip(h,o)]
  if all(isinstance(a,(int,float)) and isinstance(b,(int,float)) for _,a,b in pairs):
   deltas=[b-a for _,a,b in pairs]
   if all(d==deltas[0] for d in deltas):
    transforms.append({"dim":slot,"kind":"shift","delta":deltas[0]});continue
   groups=[];seen=set()
   for pred,_,_ in pairs:
    if pred not in seen:seen.add(pred);groups.append(pred)
   for pred in groups:
    gd=[b-a for p,a,b in pairs if p==pred]
    if not all(d==gd[0] for d in gd):return None
    if gd[0]!=0:transforms.append({"dim":slot,"kind":"shift","delta":gd[0],"pred":pred})
  else:
   mapping={}
   for _,a,b in pairs:
    if a in mapping and mapping[a]!=b:return None
    mapping[a]=b
   changed=[[a,b] for a,b in mapping.items() if a!=b]
   if changed:transforms.append({"dim":slot,"kind":"subst","delta":changed})
 if len(transforms)>max_dims:return None
 return {"matrix":matrix,"residual_dims":len(transforms),"transforms":transforms,"dims":[x["dim"] for x in transforms],"score":[len(transforms),sum(abs(x) for x in matrix),matrix]}
def solve(sample):
 base=sample["base"];goal=sample["goal"];coord_slots=[i for i,t in enumerate(sample["dim_types"]) if t.startswith("coord:")]
 extents=[]
 for rows in (base,goal):
  for slot in coord_slots:
   vals=[r[slot] for r in rows];extents.append(max(vals)-min(vals))
 b=max(extents);viable=[];checked=0
 for a in range(-b,b+1):
  for bb in range(-b,b+1):
   for c in range(-b,b+1):
    for d in range(-b,b+1):
     if [a,bb,c,d]==[1,0,0,1]:continue
     checked+=1;att=candidate(base,goal,[a,bb,c,d],coord_slots,2)
     if att is not None:viable.append(att)
 viable.sort(key=lambda x:(x["score"][0],x["score"][1],x["score"][2]))
 expected=sample["observation"]
 winner=viable[0] if viable else None
 fields={"explained":winner is not None,"matrix":winner["matrix"] if winner else [],"residual_dims":winner["residual_dims"] if winner else 0,"transforms":winner["transforms"] if winner else [],"dims":winner["dims"] if winner else [],"checked":checked}
 fields_match=all(fields[k]==expected[k] for k in fields)
 gen=next((x for x in viable if x["matrix"]==GENERATING),None)
 return {"layout":sample["layout"],"mode":sample["mode"],"condition":sample["condition"],"B":b,"checked":checked,"eligible_candidate_count":len(viable),"native_repeat_count":5,"native_repeats_identical":True,"native_fields_match":fields_match,"native_fields":expected,"reconstructed_fields":fields,"winner_score":winner["score"] if winner else None,"generating_matrix_eligible":gen is not None,"generating_matrix_score":gen["score"] if gen else None,"top_candidates":viable[:10]}
def main():
 raw=json.loads(SOURCE.read_text());keys={}
 for s in raw["samples"]:
  if s["condition"]=="positive":continue
  key=(s["layout"],s["mode"],s["condition"]);keys.setdefault(key,[]).append(s)
 cases=[]
 for key,replicates in sorted(keys.items()):
  replicates.sort(key=lambda s:s["repetition"]);first=replicates[0]
  case=solve(first);case["native_repeats_identical"]=all(s["observation"]==first["observation"] for s in replicates)
  cases.append(case)
 native_path=Path(raw["provenance"]["native_extension_path"])
 paths=["scripts/reconstruct_geninfer_candidate_ranking_v1.py","scripts/analyze_geninfer_candidate_ranking_v1.py","docs/research/engine_substrate/SUBSTRATE_GENINFER_CANDIDATE_RANKING_RECONSTRUCTION_PREREG_20260926.md","runners/dsl/src/shape_decode.rs","runners/dsl/src/value.rs"]
 report={"schema_version":1,"run_id":"substrate-geninfer-candidate-ranking-v1-20260926","engine":raw["engine"],"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),"environment":{"python":sys.version,"platform":platform.platform()},"input":{"path":str(SOURCE.relative_to(ROOT)),"sha256":sha(SOURCE)},"protocol":{"matrix_domain":"all non-identity 2x2 integer matrices in [-B,B]^4","B":"max normalized extent from base and observation","acceptance":"numeric residual grouping and max_dims=2; score=(residual_entries, matrix L1, lexicographic matrix)","cases":len(cases)},"cases":cases,"provenance":{"source_sha256":{p:sha(ROOT/p) for p in paths},"native_extension_path":str(native_path),"native_extension_sha256":sha(native_path)},"claim_boundary":"A source-derived Python reconstruction checked against captured native outputs for 18 corrupted cells; not an internal native trace and not a proof beyond these fixtures."}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");print(json.dumps({"output":str(OUT),"cases":len(cases),"all_native_matches":all(c["native_fields_match"] and c["native_repeats_identical"] for c in cases),"mismatches":[{k:c[k] for k in ("layout","mode","condition","native_fields","reconstructed_fields")} for c in cases if not c["native_fields_match"]],"selected_cases":[{k:c[k] for k in ("layout","mode","condition","B","eligible_candidate_count","winner_score","generating_matrix_eligible","generating_matrix_score","native_fields_match","top_candidates")} for c in cases if c["mode"]=="stable_identity" and (c["layout"]=="original" or c["layout"]=="paired_square" and c["condition"].endswith("_2"))]},indent=2))
if __name__=="__main__":main()
