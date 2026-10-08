#!/usr/bin/env python3
"""Fresh-process save/load scale for eventized ProblemShape state."""
from __future__ import annotations
import argparse,json,os,platform,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'scripts')]
from substrate_problem_shape_induction_economics import sha,rss_bytes
from substrate_problem_shape_event_index_recovery import prepare,observe,wire,PS_RULES,SEEDS
PREREG=ROOT/'docs/research/engine_substrate/SUBSTRATE_PROBLEM_SHAPE_EVENT_INDEX_CHECKPOINT_SCALE_PREREG_20260925.md'
LOCK=ROOT/'evaluation/substrate_capability/problem_shape_event_index_checkpoint_scale_lock_20260925.json'
CANDIDATE=ROOT/'scripts/substrate_problem_shape_all_transitions.py'
SIZES=[2,8,16,32]

def projection(agent,records):
 from substrate_rs import _native
 s,native=agent.s,agent.inner
 observations=[]
 for r in records:
  oid=_native.NodeID(int(r['observation_id']));a=s.node(oid)['attrs']; links=sorted(int(x.value) for x in s.neighbours(oid,'about_goal'))
  observations.append({'goal_id':int(r['goal_id']),'about_goal_ids':links,'key':a.get('key'),'status':a.get('status'),'covered_by':a.get('covered_by'),'decoded_epoch':a.get('decoded_epoch')})
 observations.sort(key=lambda x:x['goal_id'])
 shapes=sorted([{'name':s.node(n)['attrs'].get('name'),'support':s.node(n)['attrs'].get('support'),'minted':s.node(n)['attrs'].get('minted')} for n in s.nodes('ProblemShape') if float(s.node(n)['attrs'].get('minted',0))>0],key=lambda z:z['name'])
 indexes=sorted([{'key':s.node(n)['attrs']['key'],'support_count':int(s.node(n)['attrs']['support_count'])} for n in s.nodes('ProblemShapeKeyIndex')],key=lambda z:z['key'])
 edges=s.graph_to_dict()['edges'];event_types=['problem_shape_pending_decode','problem_shape_decoded','problem_shape_residual_candidate']
 events={et:sum(1 for e in edges if e.get('type')==et) for et in event_types}
 active=sorted(row[1] for row in native.rule_access_sets() if row[2] and row[1] in PS_RULES)
 epoch=int(s.node(agent.agent)['attrs'].get('problem_codebook_epoch',0))
 fixed=native.run_rules_report(100000,False)['status']=='fixed_point'
 grouped={}
 for n in s.nodes('ProblemShapeObservation'):
  k=str(s.node(n)['attrs']['key']);grouped[k]=grouped.get(k,0)+1
 support={x['key']:x['support_count'] for x in indexes}
 return {'observations':observations,'shapes':shapes,'indexes':indexes,'events':events,'active_rules':active,'epoch':epoch,'fixed_point':fixed,'support_exact':support==grouped,'index_links_exact':all(len(s.neighbours(n,'indexed_problem_shape'))==1 for n in s.nodes('ProblemShapeObservation'))}

def writer(n,path):
 import domains.problem_decomposition as pdec
 from substrate_problem_shape_induction_economics import pump
 agent,tasks,_=prepare(n);idx={};records=[]
 for i,g in enumerate(tasks):
  if i:
   status=pump(agent,g)['status']
   if status not in ('resolved','walled'):raise RuntimeError(f'goal {i+1} failed')
  records.append(observe(agent,g,f'decompose_{i+1}',idx))
 state=projection(agent,records)
 if not state['fixed_point']:raise RuntimeError('writer did not settle')
 start=time.perf_counter_ns();agent.save(path);save_ns=time.perf_counter_ns()-start
 return {'arm':'writer','size':n,'process_id':os.getpid(),'records':records,'state':state,'node_count':agent.s.node_count(),'edge_count':agent.s.edge_count(),'checkpoint_bytes':Path(path).stat().st_size,'save_wall_ns':save_ns,'rss_peak_bytes':rss_bytes()}

def reader(path,expected_path,n):
 from substrate import world_adapter as wa
 load0=time.perf_counter_ns();agent=wa.WorldAdapter.load(path);load_ns=time.perf_counter_ns()-load0;expected=json.loads(Path(expected_path).read_text())
 # Use persisted observation/goal IDs; the graph checkpoint preserves them exactly.
 start=time.perf_counter_ns();loaded=projection(agent,expected['records']);projection_ns=time.perf_counter_ns()-start
 equal=loaded==expected['state']
 all_status=all(x['status']=='recognized' for x in loaded['observations']) and len(loaded['observations'])==n
 return {'arm':'reader','size':n,'process_id':os.getpid(),'state':loaded,'load_wall_ns':load_ns,'projection_check_wall_ns':projection_ns,'rss_peak_bytes':rss_bytes(),'projection_matches_writer':equal,'all_recognized':all_status,'checks':{'state_matches_writer':equal,'all_recognized':all_status,'shape_count_one_support_two':loaded['shapes']==[{'name':'ps_has_bound=yes','support':2,'minted':1.0}],'index_support_n':loaded['indexes']==[{'key':'ps_has_bound=yes','support_count':n}],'events_empty':all(v==0 for v in loaded['events'].values()),'epoch_one':loaded['epoch']==1,'fixed_point':loaded['fixed_point'],'support_exact':loaded['support_exact'],'links_exact':loaded['index_links_exact']}}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path);ap.add_argument('--worker',choices=['writer','reader']);ap.add_argument('--size',type=int,choices=SIZES);ap.add_argument('--checkpoint',type=Path);ap.add_argument('--expected',type=Path);a=ap.parse_args()
 if a.worker=='writer':
  print(json.dumps(writer(a.size,a.checkpoint),sort_keys=True));return 0
 if a.worker=='reader':
  r=reader(a.checkpoint,a.expected,a.size);r['all_checks_pass']=all(r['checks'].values());print(json.dumps(r,sort_keys=True));return 0 if r['all_checks_pass'] else 2
 if not a.output:ap.error('--output required')
 stale=subprocess.check_output([sys.executable,'-c',"from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')))"],cwd=ROOT,text=True).strip()
 if stale:raise SystemExit(f'native build stale:\n{stale}')
 import hashlib
 lock=json.loads(LOCK.read_text());want={'preregistration_sha256':sha(PREREG),'runner_sha256':sha(Path(__file__)),'candidate_runner_sha256':sha(CANDIDATE),'native_sha256':sha(ROOT/'runners/dsl/python/substrate_rs/_native.abi3.so'),'seed_hashes':{p.name:sha(p) for p in SEEDS}}
 if any(lock.get(k)!=v for k,v in want.items()):raise SystemExit('checkpoint scale lock mismatch')
 env={**os.environ,'PYTHONPATH':f'{ROOT}:{ROOT/"runners/dsl/python"}:{ROOT/"scripts"}'};records=[]
 with tempfile.TemporaryDirectory(prefix='ps-event-checkpoint-scale-') as td:
  for n in SIZES:
   cp=Path(td)/f'n{n}.json';spec=Path(td)/f'n{n}-state.json'
   wp=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker','writer','--size',str(n),'--checkpoint',str(cp)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=240)
   if wp.returncode:raise RuntimeError(f'writer N={n} failed:\n{wp.stdout}\n{wp.stderr}')
   w=json.loads(wp.stdout);spec.write_text(json.dumps({'records':w['records'],'state':w['state']}))
   rp=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker','reader','--size',str(n),'--checkpoint',str(cp),'--expected',str(spec)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=180)
   if rp.returncode:raise RuntimeError(f'reader N={n} failed:\n{rp.stdout}\n{rp.stderr}')
   r=json.loads(rp.stdout);records.append({'size':n,'writer':w,'reader':r});print(json.dumps({'size':n,'writer_pid':w['process_id'],'reader_pid':r['process_id'],'checks':r['checks']}),flush=True)
 pids=[z[arm]['process_id'] for z in records for arm in ('writer','reader')]
 result={'schema_version':1,'run_id':f'problem-shape-event-index-checkpoint-scale-{time.strftime("%Y%m%dT%H%M%SZ",time.gmtime())}','preregistration':{'path':str(PREREG.relative_to(ROOT)),'sha256':sha(PREREG)},'lock':{'path':str(LOCK.relative_to(ROOT)),'sha256':sha(LOCK)},'runner_sha256':sha(Path(__file__)),'candidate_runner_sha256':sha(CANDIDATE),'native_sha256':sha(ROOT/'runners/dsl/python/substrate_rs/_native.abi3.so'),'seed_hashes':{p.name:sha(p) for p in SEEDS},'fresh_processes_per_size':True,'unique_process_ids':len(pids)==len(set(pids)),'records':records,'all_checks_pass':len(records)==len(SIZES) and len(pids)==2*len(SIZES) and len(pids)==len(set(pids)) and all(all(x['reader']['checks'].values()) for x in records)}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'all_checks_pass':result['all_checks_pass'],'sizes':len(records)}));return 0 if result['all_checks_pass'] else 2
if __name__=='__main__':raise SystemExit(main())
