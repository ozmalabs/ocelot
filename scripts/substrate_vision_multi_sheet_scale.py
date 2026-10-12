#!/usr/bin/env python3
"""Repeated two-root semantic and work probe for vision settlement scope."""
from __future__ import annotations
import copy,hashlib,json,platform,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
SEED_DOC=ROOT/'seeds/vision_settle.json';PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_VISION_MULTI_SHEET_SCALE_PREREG_20260925.md';OUT=ROOT/'evaluation/reports/substrate_vision_multi_sheet_scale_20260925.json';LOCK=ROOT/'evaluation/substrate_capability/vision_multi_sheet_scale_lock_20260925.json';CAP=10000
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def clone_scoped(doc):
 m=copy.deepcopy(doc);found=0
 def visit(x):
  nonlocal found
  if isinstance(x,dict):
   if x.get('type')=='NodesOfType' and x.get('node_type')=='SUnit':found+=1;return {'type':'Neighbours','node':{'type':'Var','name':'r'},'edge_type':'has_sunit','any_type':False}
   return {k:visit(v) for k,v in x.items()}
  if isinstance(x,list):return [visit(v) for v in x]
  return x
 for r in m.get('rules',[]):
  if r.get('name')=='st_settle':r['name']='st_settle_root_scoped_benchmark';r['where']=visit(r.get('where'));r['effects']=visit(r.get('effects'))
 if found!=2:raise RuntimeError(f'expected exactly two global SUnit sources, got {found}')
 return m
def one_arm(sr,doc,seed,n,scoped,b_state):
 from substrate.seed_loader import engine_rules_only
 base=engine_rules_only(doc);manifest=dict(base);manifest['rules']=[r for r in base.get('rules',[]) if r.get('name')=='st_settle']
 if scoped:manifest=clone_scoped(manifest)
 if len(manifest['rules'])!=1:raise RuntimeError('expected exactly one st_settle rule')
 outer=sr.Substrate();inner=outer._inner;inner.load_seed_manifest(manifest)
 params=inner.nodes('SettleParams')
 if len(params)!=1:raise RuntimeError(f'expected singleton SettleParams, got {len(params)}')
 inner.set_attr(params[0],'settle',1.0);roots=[];sheets=[];affs=[];rng=np.random.Generator(np.random.PCG64(seed+31*n))
 for label,state in (('A',1.0),('B',float(b_state))):
  root=inner.add_node('World',{'name':label,'step':0.0});nodes=[];aff=(rng.random(n*n)*0.2).tolist() if label=='A' else [0.0]*(n*n)
  for i in range(n*n):nodes.append(inner.add_node('SUnit',{'act':state,'aff':float(aff[i]),'aff_step':0.0,'act_next':-1.0}))
  for r in range(n):
   for c in range(n):
    u=nodes[r*n+c];inner.add_edge_unchecked(root,'has_sunit',u,{})
    for dr in (-1,0,1):
     for dc in (-1,0,1):
      rr,cc=r+dr,c+dc
      if (dr or dc) and 0<=rr<n and 0<=cc<n:inner.add_edge_unchecked(u,'sunit_neighbour',nodes[rr*n+cc],{})
  roots.append(root);sheets.append(nodes);affs.append(aff)
 memberships=[list(inner.neighbours(r,'has_sunit')) for r in roots]
 if any(set(m)!=set(ns) for m,ns in zip(memberships,sheets)) or set(memberships[0])&set(memberships[1]):raise RuntimeError('root membership overlap or mismatch')
 inner.scale_audit_set_enabled(False);inner.scale_audit_set_per_rule_enabled(False);inner.scale_audit_reset();inner.scale_audit_per_rule_reset();inner.scale_audit_set_enabled(True);inner.scale_audit_set_per_rule_enabled(True)
 progress=int(inner.run_rules(CAP));global_counts=dict(inner.scale_audit_snapshot());names={int(x[0]):str(x[1]) for x in inner.rule_access_sets()};per=[{'rule_index':int(i),'rule_name':names.get(int(i),f'rule_{i}'),'metric':str(mt),'count':int(v)} for i,mt,v in inner.scale_audit_per_rule_snapshot()]
 inner.scale_audit_set_per_rule_enabled(False);inner.scale_audit_set_enabled(False)
 out=[[float(inner.node(u)['attrs'].get('act_next',0.0)) for u in ns] for ns in sheets]
 return {'seed':seed,'n_side':n,'units_per_sheet':n*n,'total_sunits':2*n*n,'variant':'scoped' if scoped else 'global','b_initial_act':float(b_state),'progress':progress,'budget':CAP,'budget_exit':progress>=CAP,'members_per_root':[len(m) for m in memberships],'graph_nodes':len(inner.nodes()),'aff_A':affs[0],'aff_B':affs[1],'act_next_A':out[0],'act_next_B':out[1],'global_counters':global_counts,'per_rule_counters':per,'rule_name':'st_settle_root_scoped_benchmark' if scoped else 'st_settle'}
def predict(row,scoped):
 n=row['n_side'];a=np.ones(n*n);b=np.full(n*n,row['b_initial_act']);affs=(np.asarray(row['aff_A']),np.asarray(row['aff_B']));all_acts=np.concatenate((a,b));outputs=[]
 for sheet,acts in enumerate((a,b)):
  grid=acts.reshape(n,n);vals=[]
  for r in range(n):
   for c in range(n):
    neigh=[grid[rr,cc] for rr in range(max(0,r-1),min(n,r+2)) for cc in range(max(0,c-1),min(n,c+2)) if (rr,cc)!=(r,c)]
    local=float(np.mean(neigh)) if neigh else 0.0;pool=acts if scoped else all_acts
    vals.append(max(float(affs[sheet][r*n+c])+local-float(np.mean(pool)),0.0))
  outputs.append(vals)
 return outputs
def main():
 from domains.engine_provenance import engine_preamble,engine_provenance
 engine_preamble()
 import substrate_rs as sr
 from substrate_rs import _native
 doc=json.loads(SEED_DOC.read_text());engine=engine_provenance();lock={'run_id':'vision-multi-sheet-scale-20260925','hashes':{'runner':sha(Path(__file__)),'protocol':sha(PROTOCOL),'seed':sha(SEED_DOC)},'native_extension_sha256':sha(Path(_native.__file__).resolve()),'engine_provenance':engine};LOCK.write_text(json.dumps(lock,indent=2,sort_keys=True)+'\n')
 arms=[];conditions=((False,0.0),(False,1.0),(True,0.0),(True,1.0))
 for ix,seed in enumerate((4101,7301,10703)):
  for n in (2,4,8,16):
   order=conditions if ix%2==0 else tuple(reversed(conditions))
   for scoped,b in order:
    row=one_arm(sr,doc,seed,n,scoped,b);row['predicted']=predict(row,scoped);row['max_equation_residual']=max(float(np.max(np.abs(np.asarray(row['act_next_A'])-row['predicted'][0]))),float(np.max(np.abs(np.asarray(row['act_next_B'])-row['predicted'][1]))));row['exact_prediction']=row['act_next_A']==row['predicted'][0] and row['act_next_B']==row['predicted'][1];arms.append(row)
   print(f'DONE seed={seed} n={n} arms=4',flush=True)
 pairs=[]
 for seed in (4101,7301,10703):
  for n in (2,4,8,16):
   get=lambda v,b:next(a for a in arms if a['seed']==seed and a['n_side']==n and a['variant']==v and a['b_initial_act']==b)
   g0,g1,s0,s1=get('global',0.0),get('global',1.0),get('scoped',0.0),get('scoped',1.0)
   pairs.append({'seed':seed,'n_side':n,'global_a_change_max':float(np.max(np.abs(np.asarray(g0['act_next_A'])-np.asarray(g1['act_next_A'])))),'scoped_a_change_max':float(np.max(np.abs(np.asarray(s0['act_next_A'])-np.asarray(s1['act_next_A'])))),'global_nodesoftype_units_b0':g0['global_counters'].get('term_unit:NodesOfType',0),'global_nodesoftype_units_b1':g1['global_counters'].get('term_unit:NodesOfType',0),'scoped_nodesoftype_units_b0':s0['global_counters'].get('term_unit:NodesOfType',0),'scoped_nodesoftype_units_b1':s1['global_counters'].get('term_unit:NodesOfType',0)})
 result={'run_id':'vision-multi-sheet-scale-20260925-v1','arms':arms,'pairs':pairs,'lock_sha256':sha(LOCK),'checks':{'48_arms':len(arms)==48,'correct_root_membership':all(a['members_per_root']==[a['units_per_sheet']]*2 for a in arms),'equation_residual_le_1e12':all(a['max_equation_residual']<=1e-12 for a in arms),'global_cross_root_coupling':all(x['global_a_change_max']>0 for x in pairs),'scoped_cross_root_independence':all(x['scoped_a_change_max']==0 for x in pairs),'positive_progress_below_budget':all(0<a['progress']<CAP for a in arms),'counter_integers':all(all(isinstance(v,int) and v>=0 for v in a['global_counters'].values()) for a in arms)},'provenance':{'python':sys.version,'platform':platform.platform(),'runner_sha256':sha(Path(__file__)),'protocol_sha256':sha(PROTOCOL),'seed_sha256':sha(SEED_DOC),'native_extension_path':str(Path(_native.__file__).resolve()),'native_extension_sha256':sha(Path(_native.__file__).resolve()),'engine_provenance':engine,'source_sha256':{n:sha(ROOT/'runners/dsl/src'/n) for n in ('rewrite.rs','substrate.rs','term.rs','py.rs','scale_audit.rs')}}}
 result['pass']=all(result['checks'].values());OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':result['checks'],'pairs':pairs,'pass':result['pass']},indent=2))
 if not result['pass']:raise SystemExit('multi-sheet locality gate failed')
if __name__=='__main__':main()
