#!/usr/bin/env python3
"""Fresh-process scaling and audit-overhead sweep for two-sheet vision closure."""
from __future__ import annotations
import copy,hashlib,json,os,platform,resource,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_VISION_TWO_SHEET_CURRENT_SOURCE_SCALE_V2_3_PREREG_20260927.md'
LOCK=ROOT/'evaluation/substrate_capability/vision_two_sheet_current_source_scale_v2_4_lock_20260927.json'
OUT=ROOT/'evaluation/reports/vision_two_sheet_current_source_scale_v2_4_20260927.json'
CELLDIR=ROOT/'evaluation/reports/vision_two_sheet_current_source_scale_v2_4_cells'
SEED_DOC=ROOT/'seeds/vision_settle.json';SEEDS=(4101,7301,10703);SIZES=(2,4,8,16,32,64);SCOPES=('global','scoped');B_STATES=(0.0,1.0);MODES=('plain','audit');CAP=10_000
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def source_inputs():
 from domains.engine_provenance import engine_provenance
 from substrate_rs import _native
 sources=('runners/dsl/python/substrate_rs/__init__.py','runners/dsl/python/substrate_rs/ext.py','runners/dsl/python/substrate_rs/_native.build.json','runners/dsl/src/py.rs','runners/dsl/src/scale_audit.rs','runners/dsl/src/rewrite.rs','runners/dsl/src/substrate.rs','runners/dsl/src/term.rs','substrate/seed_loader.py','scripts/settle_lib.py','scripts/rung8_lib.py')
 return {'protocol_sha256':sha(PROTOCOL),'runner_sha256':sha(__file__),'v2_3_protocol_sha256':sha(ROOT/'docs/research/engine_substrate/SUBSTRATE_VISION_TWO_SHEET_CURRENT_SOURCE_SCALE_V2_3_PREREG_20260927.md'),'v2_3_runner_sha256':sha(ROOT/'scripts/substrate_vision_two_sheet_current_source_scale_v2_3.py'),'v2_3_result_sha256':sha(ROOT/'docs/research/engine_substrate/SUBSTRATE_VISION_TWO_SHEET_CURRENT_SOURCE_SCALE_V2_3_RESULTS_20260927.md'),'v2_3_lock_sha256':sha(ROOT/'evaluation/substrate_capability/vision_two_sheet_current_source_scale_v2_3_lock_20260927.json'),'v2_3_analysis_sha256':sha(ROOT/'evaluation/reports/vision_two_sheet_current_source_scale_v2_3_analysis_20260927.json'),'seed_sha256':sha(SEED_DOC),'source_sha256':{x:sha(ROOT/x) for x in sources},'native_extension_sha256':sha(Path(_native.__file__).resolve()),'engine_provenance':engine_provenance(),'python':platform.python_version(),'platform':platform.platform(),'seeds':list(SEEDS),'sizes':list(SIZES),'scopes':list(SCOPES),'b_states':list(B_STATES),'modes':list(MODES),'progress_cap':CAP}
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
 if found!=2:raise RuntimeError(f'expected two global SUnit fold sources, got {found}')
 return m
def rss_bytes():
 try:return int(Path('/proc/self/statm').read_text().split()[1])*os.sysconf('SC_PAGE_SIZE')
 except (OSError,ValueError,IndexError):return None
def peak_rss_bytes():
 x=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss;return int(x*(1024 if sys.platform.startswith('linux') else 1))
def predict(n,aff_a,aff_b,b_state,scoped):
 import numpy as np
 all_acts=np.concatenate((np.ones(n*n),np.full(n*n,b_state)));out=[]
 for aff,initial in ((np.asarray(aff_a),np.ones(n*n)),(np.asarray(aff_b),np.full(n*n,b_state))):
  grid=initial.reshape(n,n);vals=[]
  for r in range(n):
   for c in range(n):
    neigh=[grid[rr,cc] for rr in range(max(0,r-1),min(n,r+2)) for cc in range(max(0,c-1),min(n,c+2)) if (rr,cc)!=(r,c)]
    local=float(np.mean(neigh)) if neigh else 0.0;pool=initial if scoped else all_acts
    vals.append(max(float(aff[r*n+c])+local-float(np.mean(pool)),0.0))
  out.append(vals)
 return out
def run_cell(seed,n,scope,b_state,mode):
 import numpy as np
 import substrate_rs as sr
 from substrate.seed_loader import engine_rules_only
 doc=json.loads(SEED_DOC.read_text());manifest=engine_rules_only(doc);manifest['rules']=[r for r in manifest.get('rules',[]) if r.get('name')=='st_settle']
 if scope=='scoped':manifest=clone_scoped(manifest)
 if len(manifest['rules'])!=1:raise RuntimeError('expected one st_settle rule')
 np.random.seed(seed+31*n);rng=np.random.Generator(np.random.PCG64(seed+31*n))
 rss0=rss_bytes();outer=sr.Substrate();inner=outer._inner;inner.load_seed_manifest(manifest);pp=inner.nodes('SettleParams')
 if len(pp)!=1:raise RuntimeError(f'expected one SettleParams, found {len(pp)}')
 inner.set_attr(pp[0],'settle',1.0);roots=[];sheets=[];affs=[]
 for label,state in (('A',1.0),('B',b_state)):
  root=inner.add_node('World',{'name':label,'step':0.0});units=[];aff=(rng.random(n*n)*.2).tolist() if label=='A' else [0.0]*(n*n)
  for i in range(n*n):units.append(inner.add_node('SUnit',{'act':state,'aff':float(aff[i]),'aff_step':0.0,'act_next':-1.0}))
  for r in range(n):
   for c in range(n):
    u=units[r*n+c];inner.add_edge_unchecked(root,'has_sunit',u,{})
    for dr in (-1,0,1):
     for dc in (-1,0,1):
      rr,cc=r+dr,c+dc
      if (dr or dc) and 0<=rr<n and 0<=cc<n:inner.add_edge_unchecked(u,'sunit_neighbour',units[rr*n+cc],{})
  roots.append(root);sheets.append(units);affs.append(aff)
 members=[list(inner.neighbours(r,'has_sunit')) for r in roots]
 if any(set(a)!=set(b) for a,b in zip(members,sheets)) or set(members[0])&set(members[1]):raise RuntimeError('root ownership mismatch')
 if mode=='audit':
  inner.scale_audit_set_enabled(False);inner.scale_audit_set_per_rule_enabled(False);inner.scale_audit_reset();inner.scale_audit_per_rule_reset();inner.scale_audit_set_enabled(True);inner.scale_audit_set_per_rule_enabled(True)
 rss_build=rss_bytes();wall0=time.perf_counter();cpu0=time.process_time();progress=int(inner.run_rules(CAP));cpu=time.process_time()-cpu0;wall=time.perf_counter()-wall0;rss_done=rss_bytes()
 out=[[float(inner.node(u)['attrs'].get('act_next',0.0)) for u in units] for units in sheets];pred=predict(n,affs[0],affs[1],b_state,scope=='scoped')
 residual=max(float(np.max(np.abs(np.asarray(out[i])-np.asarray(pred[i])))) for i in (0,1))
 if mode=='audit':
  global_counts=dict(inner.scale_audit_snapshot());names={int(x[0]):str(x[1]) for x in inner.rule_access_sets()};per=[{'rule_index':int(i),'rule_name':names.get(int(i),f'rule_{i}'),'metric':str(mt),'count':int(v)} for i,mt,v in inner.scale_audit_per_rule_snapshot()]
 else:global_counts={};per=[]
 graph=inner.graph_to_dict();rss_snapshot=rss_bytes()
 return {'seed':seed,'n_side':n,'units_per_sheet':n*n,'total_sunits':2*n*n,'scope':scope,'b_initial_act':b_state,'mode':mode,'progress':progress,'budget':CAP,'budget_exit':progress>=CAP,'members_per_root':[len(x) for x in members],'graph_nodes':len(graph['nodes']),'graph_edges':len(graph['edges']),'aff_A':affs[0],'aff_B':affs[1],'act_next_A':out[0],'act_next_B':out[1],'max_equation_residual':residual,'global_counters':global_counts,'per_rule_counters':per,'closure_wall_seconds':wall,'closure_process_cpu_seconds':cpu,'rss_before_build_bytes':rss0,'rss_after_build_bytes':rss_build,'rss_after_closure_bytes':rss_done,'rss_after_graph_snapshot_bytes':rss_snapshot,'process_peak_rss_bytes':peak_rss_bytes()}
def cell_id(seed,n,scope,b,mode):return f's{seed}_n{n}_{scope}_b{int(b)}_{mode}'
def main():
 if sys.argv[1:]==['--lock']:
  LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps({'locked_inputs':source_inputs()},indent=2,sort_keys=True)+'\n');print(LOCK);return
 locked=source_inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text())['locked_inputs']!=locked:raise SystemExit('missing/stale source lock')
 CELLDIR.mkdir(parents=True,exist_ok=True)
 if len(sys.argv)==7 and sys.argv[1]=='--cell':
  _,_,ss,nn,scope,bb,mode=sys.argv;seed=int(ss);n=int(nn);b=float(bb)
  if seed not in SEEDS or n not in SIZES or scope not in SCOPES or b not in B_STATES or mode not in MODES:raise SystemExit('unregistered cell')
  row=run_cell(seed,n,scope,b,mode);row['cell_id']=cell_id(seed,n,scope,b,mode);row['source_lock_sha256']=sha(LOCK);row['source_stable']=source_inputs()==locked
  p=CELLDIR/f'{row["cell_id"]}.json';p.write_text(json.dumps(row,separators=(',',':'),sort_keys=True)+'\n')
  if not row['source_stable']:raise SystemExit('source drift')
  print(f'cell={row["cell_id"]} progress={row["progress"]} wall={row["closure_wall_seconds"]:.6f}s rss_peak={row["process_peak_rss_bytes"]}',flush=True);return
 if len(sys.argv)!=1:raise SystemExit('usage: runner [--lock | --cell seed n scope bstate mode]')
 cells=[]
 for seed in SEEDS:
  for n in SIZES:
   for scope in SCOPES:
    for b in B_STATES:
     order=MODES if (seed+n+int(b))%2==0 else tuple(reversed(MODES))
     for mode in order:
      cid=cell_id(seed,n,scope,b,mode);path=CELLDIR/f'{cid}.json'
      if not path.exists():subprocess.run([sys.executable,__file__,'--cell',str(seed),str(n),scope,str(b),mode],cwd=ROOT,check=True)
      cells.append(json.loads(path.read_text()))
      print(f'progress_cells={len(cells)}/96 last={cid}',flush=True)
 data={'run_id':'vision-two-sheet-current-source-scale-v2.4-20260927','locked_inputs':locked,'cells':cells,'source_stable':source_inputs()==locked,'complete':len(cells)==96}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
 if not data['source_stable'] or not data['complete']:raise SystemExit('incomplete or source drift')
 print(json.dumps({'output':str(OUT.relative_to(ROOT)),'cells':len(cells),'source_stable':data['source_stable']},indent=2))
if __name__=='__main__':main()
