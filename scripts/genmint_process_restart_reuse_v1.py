#!/usr/bin/env python3
"""Measure full-seed GenMint acquisition and selected reuse after process restart."""
from __future__ import annotations
import argparse, hashlib, json, os, platform, random, resource, subprocess, sys, tempfile, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
from domains.engine_provenance import build_is_stale, engine_preamble, rust_source_fingerprint
engine_preamble()
from substrate.boot_core import boot_core
from domains import reflective_faculty as rf
from substrate_rs import _native
import genmint_matrix_family_reuse_probe_v3 as fixtures
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_GENMINT_PROCESS_RESTART_REUSE_V1_PREREG_20260930.md'
LOCK=ROOT/'evaluation/substrate_capability/genmint_process_restart_reuse_v1_lock_20260930.json'
RAW=ROOT/'evaluation/reports/genmint_process_restart_reuse_v1_20260930.json'
MATRICES=('prior_matrix','shearA','shearB');LAYOUTS=('adjacent_01','opposite_03');ARMS=('continuous_enabled','restart_enabled','restart_disabled');REPS=5;K=16;SEED=20260930
SOURCES=('scripts/genmint_process_restart_reuse_v1.py','scripts/analyze_genmint_process_restart_reuse_v1.py','scripts/genmint_matrix_family_reuse_probe_v3.py','scripts/analyze_genmint_matrix_family_reuse_probe_v3.py','docs/research/engine_substrate/SUBSTRATE_GENMINT_PROCESS_RESTART_REUSE_V1_PREREG_20260930.md','seeds/shape_decode_loop.json','domains/reflective_faculty.py','domains/engine_provenance.py','substrate/boot_core.py','runners/dsl/src/shape_decode.rs','runners/dsl/src/term.rs','runners/dsl/src/py.rs','runners/dsl/src/substrate.rs','runners/dsl/src/persist.rs','runners/dsl/python/substrate_rs/__init__.py','runners/dsl/python/substrate_rs/_native.build.json')
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def input_lock():
 ext=Path(_native.__file__).resolve()
 return {'source_sha256':{x:sha(ROOT/x) for x in SOURCES},'native_path':str(ext),'native_sha256':sha(ext),'native_build_manifest_sha256':sha(ROOT/'runners/dsl/python/substrate_rs/_native.build.json'),'rust_source_fingerprint':rust_source_fingerprint(str(ROOT)),'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()}
def training_input(matrix,layout):
 m=fixtures.MAPS[matrix];p0=set(fixtures.LAYOUTS[layout]);base=[];target=[]
 for i,(r,c) in enumerate(fixtures.POINTS):
  b,y=fixtures.make_row('p0' if i in p0 else 'p1',r,c,m);base.append(b);target.append(y)
 return m,sorted(p0),base,target
def train(matrix,layout,enabled,rep):
 start=time.perf_counter();cpu=time.process_time();s,agent=boot_core();native=rf._native_eval2(s);rf._ensure_shape_decode_loop(s,native,agent);boot_wall=time.perf_counter()-start;boot_cpu=time.process_time()-cpu
 if enabled:s.set_attr(agent,'gen_infer_enabled',1.0)
 m,p0,base,target=training_input(matrix,layout);dt=fixtures.DT
 s.add_node('ShapeSignature',{'name':f'training_{matrix}_{layout}','signature':json.dumps(base),'kind':'faculty','faculty':f'training_{matrix}_{layout}','dim_types':dt})
 epoch=s.node(agent)['attrs'].get('codebook_epoch') or 0.0
 obs=s.add_node('Observation',{'signature':target,'key':['matrix_restart',matrix,layout,str(enabled),str(rep),'train'],'status':'decoded','residual':target,'decoded_epoch':epoch,'dim_types':dt});s.add_edge(agent,'observed',obs)
 before_gens=fixtures.linear_gens(s);train_wall=time.perf_counter();train_cpu=time.process_time();native.run_rules();train_wall=time.perf_counter()-train_wall;train_cpu=time.process_time()-train_cpu
 after_gens=fixtures.linear_gens(s);attrs=s.node(obs)['attrs'];expected=[g for g in after_gens if g['matrix']==m and g['name'] not in {x['name'] for x in before_gens}]
 return s,agent,native,{'matrix_name':matrix,'layout':layout,'enabled':enabled,'replicate':rep,'matrix':m,'p0_indices':p0,'training_base':base,'training_target':target,'train_status':attrs.get('status'),'train_residual':attrs.get('residual'),'train_transforms':fixtures.transform_records(s,obs),'generators_before':before_gens,'generators_after':after_gens,'acquired_expected_generator':expected[0] if len(expected)==1 else None,'boot_wall_s':boot_wall,'boot_cpu_s':boot_cpu,'train_closure_wall_s':train_wall,'train_closure_cpu_s':train_cpu,'train_graph_nodes':s.node_count(),'train_graph_edges':s.edge_count()}
def apply(s,agent,native,matrix,layout,rep,enabled,expected_gen):
 results=[];cost_wall=cost_cpu=0.0;m=fixtures.MAPS[matrix]
 for ti,coords in enumerate(fixtures.HELDOUT):
  base=[];target=[]
  for j,(r,c) in enumerate(coords):
   b,y=fixtures.make_row('p0' if j%2==0 else 'p1',r,c,m);base.append(b);target.append(y)
  name=f'held_{ti}_{matrix}_{layout}'
  s.add_node('ShapeSignature',{'name':name,'signature':json.dumps(base),'kind':'faculty','faculty':name,'dim_types':fixtures.DT})
  epoch=s.node(agent)['attrs'].get('codebook_epoch') or 0.0
  obs=s.add_node('Observation',{'signature':target,'key':['matrix_restart',matrix,layout,str(enabled),str(rep),str(ti)],'status':'decoded','residual':target,'decoded_epoch':epoch,'dim_types':fixtures.DT});s.add_edge(agent,'observed',obs)
  before=fixtures.linear_gens(s);st=time.perf_counter();ct=time.process_time();native.run_rules();elapsed=time.perf_counter()-st;cpu=time.process_time()-ct;cost_wall+=elapsed;cost_cpu+=cpu
  at=s.node(obs)['attrs'];trans=fixtures.transform_records(s,obs);gen_name=next((t.get('generator') for t in trans if t.get('generator')),None);gen=next((g for g in fixtures.linear_gens(s) if g['name']==gen_name),None)
  route='no_generator' if gen is None else ('training_acquired' if expected_gen and gen_name==expected_gen['name'] else ('expected_matrix_other_generator' if gen['matrix']==m else 'other_generator'))
  independent=[]
  if gen is not None:
   a,b,c,d=gen['matrix'];mins=[min(row[q] for row in base) for q in (1,2)]
   predicted=[[row[0],a*(row[1]-mins[0])+b*(row[2]-mins[1]),c*(row[1]-mins[0])+d*(row[2]-mins[1]),row[3]] for row in base]
   for residual in (trans[0].get('transforms') if trans else []) or []:
    for row in predicted:
     if residual.get('pred') is not None and residual['pred']!=row[0]:continue
     dim=residual.get('dim')
     if residual.get('kind')=='shift' and dim in (1,2):row[dim]+=residual.get('delta',0)
     elif residual.get('kind')=='subst' and row[3]==residual.get('from'):row[3]=residual.get('to')
   independent=predicted
  results.append({'task_index':ti,'base':base,'target':target,'status':at.get('status'),'residual':at.get('residual'),'transforms':trans,'selected_generator':gen_name,'selected_matrix':gen.get('matrix') if gen else None,'route':route,'independent_predictions':independent,'exact_target_match':independent==target if gen else False,'closure_wall_s':elapsed,'closure_cpu_s':cpu,'generators_before':before,'generators_after':fixtures.linear_gens(s)})
 return results,cost_wall,cost_cpu

def restore_bundle(path):
 from substrate_rs import Substrate
 raw=Path(path).read_bytes();b=json.loads(raw);s=Substrate();g=s._inner;g.graph_from_dict(b['graph'])
 for prod in b['grammar'].get('productions',[]):g.add_production_no_mirror(prod)
 g.import_rules(b['rules'])
 def canonical_rules(rows):
  out=[]
  for row in rows:
   item=dict(row);item.pop('content_hash',None);item['match']=sorted(item.get('match',[]),key=lambda clause:tuple(clause));out.append(item)
  return out
 checks={'graph_exact':s.graph_to_dict()==b['graph'],'grammar_exact':s.grammar_to_json()==b['grammar'],'rules_semantically_exact':canonical_rules(g.export_rules())==canonical_rules(b['rules'])}
 checks['checkpoint_bytes']=len(raw);checks['checkpoint_sha256']=hashlib.sha256(raw).hexdigest()
 return s,b,checks

def child(mode,matrix,layout,arm,rep,path=None):
 start=time.perf_counter();cpu=time.process_time()
 enabled=arm!='restart_disabled'
 if mode=='apply':
  s,b,checks=restore_bundle(path);native=rf._native_eval2(s);agent=__import__('substrate_rs').NodeID(int(b['agent_id']));tasks,wall,appcpu=apply(s,agent,native,matrix,layout,rep,enabled,b.get('expected_generator'))
  result={'role':'consumer','pid':os.getpid(),'restore_checks':checks,'restore_wall_s':time.perf_counter()-start,'restore_cpu_s':time.process_time()-cpu,'applications':tasks,'application_closure_wall_s':wall,'application_closure_cpu_s':appcpu,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'final_graph_nodes':s.node_count(),'final_graph_edges':s.edge_count()}
 else:
  s,agent,native,meta=train(matrix,layout,enabled,rep)
  if arm=='continuous_enabled':
   tasks,wall,appcpu=apply(s,agent,native,matrix,layout,rep,True,meta['acquired_expected_generator']);result={'role':'continuous','producer_pid':os.getpid(),'consumer_pid':os.getpid(),'train':meta,'restore_checks':{'not_applicable':True},'restore_wall_s':0.0,'restore_cpu_s':0.0,'applications':tasks,'application_closure_wall_s':wall,'application_closure_cpu_s':appcpu,'checkpoint_write_wall_s':0.0,'checkpoint_read_wall_s':0.0,'checkpoint_bytes':0,'checkpoint_sha256':None,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'final_graph_nodes':s.node_count(),'final_graph_edges':s.edge_count()}
  else:
   bundle={'graph':s.graph_to_dict(),'grammar':s.grammar_to_json(),'rules':native.export_rules(),'agent_id':agent.value,'expected_generator':meta['acquired_expected_generator'],'matrix':meta['matrix'],'layout':layout,'enabled':enabled,'replicate':rep}
   blob=json.dumps(bundle,sort_keys=True,separators=(',',':')).encode();st=time.perf_counter();
   with open(path,'wb') as f:f.write(blob);f.flush();os.fsync(f.fileno())
   meta['checkpoint_write_wall_s']=time.perf_counter()-st;meta['checkpoint_bytes']=len(blob);meta['checkpoint_sha256']=hashlib.sha256(blob).hexdigest()
   env=dict(os.environ);env['PYTHONPATH']=f"{ROOT}:{ROOT/'runners/dsl/python'}:{env.get('PYTHONPATH','')}"
   st=time.perf_counter();proc=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--child','apply','--matrix',matrix,'--layout',layout,'--arm',arm,'--replicate',str(rep),'--path',str(path)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=120)
   meta['consumer_process_wall_s']=time.perf_counter()-st
   if proc.returncode:raise RuntimeError(f"consumer subprocess failed: {proc.stderr[-2000:]}")
   consumer=json.loads(proc.stdout.strip().splitlines()[-1]);meta['checkpoint_read_wall_s']=consumer['restore_wall_s'];meta['checkpoint_restore_checks']=consumer['restore_checks']
   ckread=consumer['restore_checks']
   result={'role':'restart','producer_pid':os.getpid(),'consumer_pid':consumer['pid'],'train':meta,'restore_checks':ckread,'checkpoint_io_matches':ckread.get('checkpoint_bytes')==meta['checkpoint_bytes'] and ckread.get('checkpoint_sha256')==meta['checkpoint_sha256'],'restore_wall_s':consumer['restore_wall_s'],'restore_cpu_s':consumer['restore_cpu_s'],'applications':consumer['applications'],'application_closure_wall_s':consumer['application_closure_wall_s'],'application_closure_cpu_s':consumer['application_closure_cpu_s'],'consumer_process_wall_s':meta['consumer_process_wall_s'],'checkpoint_write_wall_s':meta['checkpoint_write_wall_s'],'checkpoint_read_wall_s':meta['checkpoint_read_wall_s'],'checkpoint_bytes':meta['checkpoint_bytes'],'checkpoint_sha256':meta['checkpoint_sha256'],'peak_rss_kib':max(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,consumer['peak_rss_kib']),'final_graph_nodes':consumer['final_graph_nodes'],'final_graph_edges':consumer['final_graph_edges']}
 return result

def worker(cell):
 matrix,layout,arm,rep=cell;tmp=tempfile.TemporaryDirectory(prefix='genmint_restart_');path=Path(tmp.name)/'checkpoint.json'
 result=child('train',matrix,layout,arm,rep,str(path) if arm!='continuous_enabled' else None);result.update({'matrix_name':matrix,'layout':layout,'arm':arm,'replicate':rep,'worker_pid':os.getpid(),'worker_elapsed_s':time.perf_counter()});return result

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--child',choices=('train','apply'));ap.add_argument('--matrix');ap.add_argument('--layout');ap.add_argument('--arm',choices=ARMS);ap.add_argument('--replicate',type=int);ap.add_argument('--path');ap.add_argument('--write-lock',action='store_true');a=ap.parse_args()
 if a.child:
  env=dict(os.environ);env['PYTHONPATH']=f"{ROOT}:{ROOT/'runners/dsl/python'}:{env.get('PYTHONPATH','')}"
  try:r=child(a.child,a.matrix,a.layout,a.arm,a.replicate,a.path)
  except Exception as e: print(json.dumps({'worker_failure':repr(e),'pid':os.getpid()}));raise
  print(json.dumps(r,sort_keys=True,default=str));return
 if a.write_lock:
  lock={'schema':'GenMintProcessRestartReuseLockV1','inputs':input_lock(),'design':{'matrices':MATRICES,'layouts':LAYOUTS,'arms':ARMS,'repeats':REPS,'heldout_bases':fixtures.HELDOUT,'K':K,'schedule_seed':SEED}}
  print(json.dumps(lock,indent=2,sort_keys=True));return
 if RAW.exists():raise SystemExit(f'refusing to overwrite existing capture: {RAW}')
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit(f'stale native engine: {stale}')
 lock=json.loads(LOCK.read_text())
 if lock.get('inputs')!=input_lock():raise SystemExit('source/native input lock mismatch')
 jobs=[(m,l,arm,r) for m in MATRICES for l in LAYOUTS for arm in ARMS for r in range(1,REPS+1)];rng=random.Random(SEED);rng.shuffle(jobs);rows=[];schedule=[];env=dict(os.environ);env['PYTHONPATH']=f"{ROOT}:{ROOT/'runners/dsl/python'}:{env.get('PYTHONPATH','')}"
 for ix,(m,l,arm,rep) in enumerate(jobs,1):
  schedule.append([m,l,arm,rep]);cmd=[sys.executable,str(Path(__file__).resolve()),'--child','train','--matrix',m,'--layout',l,'--arm',arm,'--replicate',str(rep)]
  outer_start=time.perf_counter()
  try:
   with tempfile.TemporaryDirectory(prefix=f'genmint_restart_{m}_{l}_{arm}_{rep}_') as td:
    if arm!='continuous_enabled':cmd.extend(['--path',str(Path(td)/'checkpoint.json')])
    cp=subprocess.run(cmd,cwd=ROOT,env=env,text=True,capture_output=True,timeout=180)
   if cp.returncode:raise RuntimeError(cp.stderr[-2500:])
   row=json.loads(cp.stdout.strip().splitlines()[-1]);row['outer_worker_wall_s']=time.perf_counter()-outer_start
  except Exception as exc:row={'matrix_name':m,'layout':l,'arm':arm,'replicate':rep,'worker_failure':repr(exc),'producer_pid':None}
  rows.append(row);print(f"{ix}/90 {m}/{l} {arm} r{rep}: {row.get('train',{}).get('train_status',row.get('worker_failure','failed'))}",flush=True)
 capture={'schema':'GenMintProcessRestartReuseV1','lock_sha256':sha(LOCK),'locked_inputs':lock['inputs'],'host':{'platform':platform.platform(),'python':sys.version},'engine_fingerprint':rust_source_fingerprint(str(ROOT)),'schedule':schedule,'workers':rows,'claim_boundary':'durable survival and selected reuse of bounded authored 2-D integer-linear generators; does not measure meta-learning or general capability'}
 RAW.parent.mkdir(parents=True,exist_ok=True);RAW.write_text(json.dumps(capture,indent=2,sort_keys=True,default=str)+'\n');print(json.dumps({'capture':str(RAW),'workers':len(rows),'failures':sum('worker_failure'in x for x in rows)},indent=2))
if __name__=='__main__':main()
