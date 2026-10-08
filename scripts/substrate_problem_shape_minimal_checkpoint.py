#!/usr/bin/env python3
"""Measure a minimal ProblemShape-only checkpoint and exact continuation."""
from __future__ import annotations
import argparse,json,os,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'scripts')]
from substrate_problem_shape_induction_economics import pump,sha,rss_bytes
from substrate_problem_shape_population_scale import STATEMENTS
from substrate_problem_shape_event_index_recovery import prepare,observe,wire,PS_RULES,SEEDS
PREREG=ROOT/'docs/research/engine_substrate/SUBSTRATE_PROBLEM_SHAPE_MINIMAL_CHECKPOINT_HARDENING_PREREG_20260925.md'
LOCK=ROOT/'evaluation/substrate_capability/problem_shape_minimal_checkpoint_hardening_lock_20260925.json'
SCHEMA_FILE=ROOT/'evaluation/substrate_capability/problem_shape_checkpoint.schema.v1.json'
CANDIDATE=ROOT/'scripts/substrate_problem_shape_all_transitions.py'
FULL_SCALE_RAW=ROOT/'evaluation/reports/substrate_problem_shape_event_index_checkpoint_scale_20260925.json'
EDGE_TYPES={'observed_problem','about_goal','minted_problem_shape','indexed_problem_shape','indexed_problem_shape_observation','problem_shape_pending_decode','problem_shape_decoded','problem_shape_residual_candidate'}
NODE_TYPES={'Agent','Goal','ProblemShapeObservation','ProblemShape','ProblemShapeKeyIndex'}
REQUIRED_PRODUCTIONS={
 ('Agent','observed_problem','ProblemShapeObservation'),
 ('ProblemShapeObservation','about_goal','Goal'),
 ('ProblemShapeObservation','minted_problem_shape','ProblemShape'),
 ('ProblemShapeObservation','indexed_problem_shape','ProblemShapeKeyIndex'),
 ('ProblemShapeKeyIndex','indexed_problem_shape_observation','ProblemShapeObservation'),
 ('Agent','problem_shape_pending_decode','ProblemShapeObservation'),
 ('Agent','problem_shape_decoded','ProblemShapeObservation'),
 ('Agent','problem_shape_residual_candidate','ProblemShapeObservation'),
}
REQUIRED_GRAPH_TRIPLES={
 ('Agent','observed_problem','ProblemShapeObservation'),
 ('ProblemShapeObservation','about_goal','Goal'),
 ('ProblemShapeObservation','indexed_problem_shape','ProblemShapeKeyIndex'),
 ('ProblemShapeKeyIndex','indexed_problem_shape_observation','ProblemShapeObservation'),
}

class BundleError(ValueError):
 def __init__(self,code):self.code=code;super().__init__(code)

def validate_bundle(bundle):
 """Reject malformed or incomplete bundles before native graph/rule import."""
 if not isinstance(bundle,dict) or bundle.get('schema_version')!=1 or bundle.get('contract')!='prepared_goal_problem_shape_continuation_v1':raise BundleError('schema_version_or_contract')
 if set(bundle)!={'schema_version','contract','agent_id','graph','productions','rules','goal_ids'}:raise BundleError('root_fields')
 graph=bundle.get('graph')
 if not isinstance(graph,dict) or set(graph)!={'next_id','nodes','edges'}:raise BundleError('graph_shape')
 if not isinstance(bundle['agent_id'],int) or not isinstance(bundle['goal_ids'],list) or not bundle['goal_ids'] or len(set(bundle['goal_ids']))!=len(bundle['goal_ids']):raise BundleError('identity_fields')
 nodes=graph['nodes'];edges=graph['edges']
 if not isinstance(nodes,list) or not isinstance(edges,list):raise BundleError('graph_collections')
 by_id={}
 for n in nodes:
  if not isinstance(n,dict) or set(n)!={'id','type','attrs'} or not isinstance(n['id'],int) or n['type'] not in NODE_TYPES or not isinstance(n['attrs'],dict) or n['id'] in by_id:raise BundleError('node_record')
  by_id[n['id']]=n
 if by_id.get(bundle['agent_id'],{}).get('type')!='Agent' or not isinstance(by_id[bundle['agent_id']]['attrs'].get('problem_codebook_epoch'),int):raise BundleError('agent_node')
 goals={n['id'] for n in nodes if n['type']=='Goal'}
 observations={n['id']:n for n in nodes if n['type']=='ProblemShapeObservation'}
 index_nodes={n['id']:n for n in nodes if n['type']=='ProblemShapeKeyIndex'}
 shapes=[n for n in nodes if n['type']=='ProblemShape']
 if goals!=set(bundle['goal_ids']) or not observations or not index_nodes:raise BundleError('required_nodes')
 triples=[];by_type={}
 for e in edges:
  if not isinstance(e,dict) or set(e)!={'src','type','tgt','attrs'} or not isinstance(e['src'],int) or not isinstance(e['tgt'],int) or not isinstance(e['attrs'],dict):raise BundleError('edge_record')
  if e['src'] not in by_id or e['tgt'] not in by_id:raise BundleError('dangling_edge')
  st,tt=by_id[e['src']]['type'],by_id[e['tgt']]['type'];triple=(st,e['type'],tt)
  if e['type'] not in EDGE_TYPES:raise BundleError('unknown_edge')
  triples.append(triple);by_type.setdefault(e['type'],[]).append(e)
 if not REQUIRED_GRAPH_TRIPLES.issubset(set(triples)):raise BundleError('required_edges')
 for obs_id,node in observations.items():
  a=node['attrs'];key=a.get('key')
  signature=a.get('signature');signature=signature.get('__list__') if isinstance(signature,dict) and set(signature)=={'__list__'} else signature
  if not isinstance(key,str) or not isinstance(signature,list) or a.get('status') not in {'pending','decoded','recognized','residual','minted'}:raise BundleError('observation_attrs')
  if sum(e['src']==bundle['agent_id'] and e['tgt']==obs_id for e in by_type.get('observed_problem',[]))!=1:raise BundleError('observation_membership')
  about=[e for e in by_type.get('about_goal',[]) if e['src']==obs_id]
  if len(about)!=1 or about[0]['tgt'] not in goals:raise BundleError('goal_link')
  idx=[e for e in by_type.get('indexed_problem_shape',[]) if e['src']==obs_id]
  if len(idx)!=1 or by_id[idx[0]['tgt']]['type']!='ProblemShapeKeyIndex':raise BundleError('index_link')
  reverse=[e for e in by_type.get('indexed_problem_shape_observation',[]) if e['tgt']==obs_id and e['src']==idx[0]['tgt']]
  if len(reverse)!=1:raise BundleError('index_reverse_link')
  for et,status in [('problem_shape_pending_decode','pending'),('problem_shape_decoded','decoded'),('problem_shape_residual_candidate','residual')]:
   count=sum(e['tgt']==obs_id for e in by_type.get(et,[]))
   if (count and a['status']!=status) or (a['status']==status and count!=1):raise BundleError('event_status')
 for ix_id,node in index_nodes.items():
  a=node['attrs'];key=a.get('key');count=a.get('support_count')
  if not isinstance(key,str) or not isinstance(count,int) or count<1:raise BundleError('index_attrs')
  members=[e['src'] for e in by_type.get('indexed_problem_shape',[]) if e['tgt']==ix_id]
  if len(members)!=count or any(observations[m]['attrs'].get('key')!=key for m in members):raise BundleError('index_support')
 if any(n['type']=='ProblemShape' and not {'name','signature','support','minted'}.issubset(n['attrs']) for n in shapes):raise BundleError('shape_attrs')
 productions=bundle.get('productions');prod_triples=set()
 for p in productions if isinstance(productions,list) else []:
  try:prod_triples.add((p['src']['type'],p['edge_type'],p['tgt']['type']))
  except (KeyError,TypeError):raise BundleError('production_record')
 if prod_triples!=REQUIRED_PRODUCTIONS:raise BundleError('production_set')
 rules=bundle.get('rules');names={r.get('name') for r in rules if isinstance(r,dict)} if isinstance(rules,list) else set()
 if names!=PS_RULES or len(rules)!=len(PS_RULES):raise BundleError('rule_set')
 for r in rules:
  for m in r.get('match',[]):
   if not isinstance(m,list) or len(m)!=3 or m[1] not in EDGE_TYPES:raise BundleError('rule_match_edge')
 return {'nodes':len(nodes),'edges':len(edges),'rules':len(rules),'productions':len(productions),'observations':len(observations)}

def read_bundle_bytes(raw):
 try:bundle=json.loads(raw)
 except (json.JSONDecodeError,UnicodeDecodeError):raise BundleError('invalid_json')
 validate_bundle(bundle);return bundle

def atomic_write(path,raw,fail_before_replace=False):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);fd,tmp=tempfile.mkstemp(prefix=f'.{path.name}.',suffix='.tmp',dir=path.parent)
 try:
  with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
  if fail_before_replace:raise OSError('injected_before_replace')
  os.replace(tmp,path)
  dfd=os.open(path.parent,os.O_RDONLY)
  try:os.fsync(dfd)
  finally:os.close(dfd)
 except Exception:
  try:os.unlink(tmp)
  except FileNotFoundError:pass
  raise
 return path.stat().st_size

def snapshot(agent,records):
 from substrate_rs import _native
 s,native=agent.s,agent.inner;obs=[]
 for r in records:
  nid=_native.NodeID(int(r['observation_id']));a=s.node(nid)['attrs'];links=sorted(int(x.value) for x in s.neighbours(nid,'about_goal'))
  obs.append({'goal_id':int(r['goal_id']),'about_goal_ids':links,'key':a.get('key'),'status':a.get('status'),'covered_by':a.get('covered_by'),'decoded_epoch':a.get('decoded_epoch')})
 obs.sort(key=lambda x:x['goal_id'])
 shapes=sorted([{'name':s.node(n)['attrs'].get('name'),'support':s.node(n)['attrs'].get('support'),'minted':s.node(n)['attrs'].get('minted')} for n in s.nodes('ProblemShape') if float(s.node(n)['attrs'].get('minted',0))>0],key=lambda x:x['name'])
 indexes=sorted([{'key':s.node(n)['attrs']['key'],'support_count':int(s.node(n)['attrs']['support_count'])} for n in s.nodes('ProblemShapeKeyIndex')],key=lambda x:x['key'])
 edges=s.graph_to_dict()['edges'];events={et:sum(1 for e in edges if e.get('type')==et) for et in ('problem_shape_pending_decode','problem_shape_decoded','problem_shape_residual_candidate')}
 rules=sorted(row[1] for row in native.rule_access_sets() if row[2] and row[1] in PS_RULES)
 groups={}
 for n in s.nodes('ProblemShapeObservation'):
  k=str(s.node(n)['attrs']['key']);groups[k]=groups.get(k,0)+1
 support={x['key']:x['support_count'] for x in indexes}
 return {'observations':obs,'shapes':shapes,'indexes':indexes,'events':events,'active_rules':rules,'epoch':int(s.node(agent.agent)['attrs'].get('problem_codebook_epoch',0)),'fixed_point':native.run_rules_report(100000,False)['status']=='fixed_point','support_exact':support==groups,'index_links_exact':all(len(s.neighbours(n,'indexed_problem_shape'))==1 for n in s.nodes('ProblemShapeObservation'))}

def minimal_bundle(agent,tasks,records):
 s,native=agent.s,agent.inner;dump=s.graph_to_dict();all_nodes={int(n['id']):n for n in dump['nodes']}
 keep={int(agent.agent.value)}|{int(g.value) for g in tasks}|{int(r['observation_id']) for r in records}
 keep|={nid for nid,n in all_nodes.items() if n['type'] in ('ProblemShape','ProblemShapeKeyIndex')}
 # Preserve only the agent epoch; keep complete prepared Goal/observation/codebook/index attrs.
 nodes=[]
 for nid in sorted(keep):
  n=all_nodes[nid]
  if n['type']=='Agent':n={**n,'attrs':{'problem_codebook_epoch':int(n['attrs'].get('problem_codebook_epoch',0))}}
  nodes.append(n)
 edges=[e for e in dump['edges'] if e['type'] in EDGE_TYPES and int(e['src']) in keep and int(e['tgt']) in keep]
 graph={'next_id':dump['next_id'],'nodes':nodes,'edges':edges}
 grammar=native.grammar_to_json()['productions'];productions=[p for p in grammar if (p.get('src',{}).get('type'),p.get('edge_type'),p.get('tgt',{}).get('type')) in REQUIRED_PRODUCTIONS]
 exported=native.export_rules_prefix('ps_');rules=[r for r in exported if r.get('name') in PS_RULES]
 if {r.get('name') for r in rules}!=PS_RULES:raise RuntimeError('minimal export did not contain exactly all five active ProblemShape rules')
 bundle={'schema_version':1,'contract':'prepared_goal_problem_shape_continuation_v1','agent_id':int(agent.agent.value),'graph':graph,'productions':productions,'rules':rules,'goal_ids':[int(g.value) for g in tasks]}
 validate_bundle(bundle)
 return bundle

def make_min_adapter(bundle):
 import substrate_rs as srs
 validate_bundle(bundle)
 sub=srs.Substrate();sub.graph_from_dict(bundle['graph'])
 for p in bundle['productions']:sub._inner.add_production_no_mirror(p)
 sub._inner.import_rules(bundle['rules'])
 from types import SimpleNamespace
 return SimpleNamespace(s=sub,inner=sub._inner,agent=srs.NodeID(bundle['agent_id']))

def worker_control():
 agent,tasks,_=prepare(8);idx={};records=[]
 for i,g in enumerate(tasks):
  if i:pump(agent,g)
  records.append(observe(agent,g,f'decompose_{i+1}',idx))
 st=snapshot(agent,records)
 return {'arm':'full_adapter_control','process_id':os.getpid(),'state':st,'records':records,'rss_peak_bytes':rss_bytes()}

def worker_compact_write(path):
 agent,tasks,_=prepare(8);idx={}
 for g in tasks:pump(agent,g)
 first=observe(agent,tasks[0],'decompose_1',idx);bundle=minimal_bundle(agent,tasks,[first])
 payload=json.dumps(bundle,separators=(',',':')).encode('utf-8')
 before=time.perf_counter_ns();atomic_write(path,payload);write_ns=time.perf_counter_ns()-before
 full_bytes=len(json.dumps(agent.s.graph_to_dict()).encode('utf-8'))
 return {'arm':'compact_writer','process_id':os.getpid(),'first_record':first,'checkpoint_bytes':Path(path).stat().st_size,'write_wall_ns':write_ns,'checkpoint_nodes':len(bundle['graph']['nodes']),'checkpoint_edges':len(bundle['graph']['edges']),'selected_rules':len(bundle['rules']),'selected_productions':len(bundle['productions']),'full_graph_json_bytes':full_bytes,'rss_peak_bytes':rss_bytes(),'bundle_goal_ids':bundle['goal_ids']}

def worker_compact_read(path):
 from substrate_rs import _native
 from domains import problem_shape as ps
 start=time.perf_counter_ns();bundle=read_bundle_bytes(Path(path).read_bytes());agent=make_min_adapter(bundle);load_ns=time.perf_counter_ns()-start
 s=agent.s;idx={str(s.node(n)['attrs']['key']):n for n in s.nodes('ProblemShapeKeyIndex')}
 first={'goal_id':None,'observation_id':None}
 # identify first existing observation and its associated goal from checkpoint
 obs0=s.nodes('ProblemShapeObservation')[0];goal0=s.neighbours(obs0,'about_goal')[0]
 first={'goal_id':int(goal0.value),'observation_id':int(obs0.value)}
 records=[first]
 for i,gid in enumerate(bundle['goal_ids'][1:],1):
  goal=_native.NodeID(int(gid));ob=ps.observe(agent,goal,run=False)
  if ob is None:raise RuntimeError('minimal observer refused prepared goal')
  key=str(s.node(ob)['attrs']['key']);ix=idx.get(key)
  if ix is None:ix=s.add_node('ProblemShapeKeyIndex',{'key':key,'support_count':0});idx[key]=ix
  count=int(s.node(ix)['attrs']['support_count'])+1;s.set_attr(ix,'support_count',count);s.add_edge(ob,'indexed_problem_shape',ix);s.add_edge(ix,'indexed_problem_shape_observation',ob);s.add_edge(agent.agent,'problem_shape_pending_decode',ob)
  agent.inner.run_rules();records.append({'goal_id':int(gid),'observation_id':int(ob.value)})
 st=snapshot(agent,records)
 return {'arm':'compact_reader','process_id':os.getpid(),'state':st,'records':records,'checkpoint_bytes':Path(path).stat().st_size,'load_wall_ns':load_ns,'loaded_nodes':s.node_count(),'loaded_edges':s.edge_count(),'loaded_rules':len(agent.inner.rule_access_sets()),'rss_peak_bytes':rss_bytes()}

def corruption_and_atomic_probes(path):
 raw=Path(path).read_bytes();base=json.loads(raw);cases={}
 mutations={
  'unsupported_version':lambda b:b.__setitem__('schema_version',99),
  'missing_rule':lambda b:b.__setitem__('rules',[r for r in b['rules'] if r.get('name')!='ps_mint']),
  'missing_production':lambda b:b.__setitem__('productions',[p for p in b['productions'] if not (p.get('edge_type')=='problem_shape_pending_decode' and p.get('src',{}).get('type')=='Agent')]),
  'dangling_edge':lambda b:b['graph']['edges'][0].__setitem__('tgt',99999999),
  'bad_index_count':lambda b:next(n for n in b['graph']['nodes'] if n['type']=='ProblemShapeKeyIndex')['attrs'].__setitem__('support_count',99),
  'missing_residual_event':lambda b:b['graph'].__setitem__('edges',[e for e in b['graph']['edges'] if e['type']!='problem_shape_residual_candidate']),
  'event_status_mismatch':lambda b:next(n for n in b['graph']['nodes'] if n['type']=='ProblemShapeObservation')['attrs'].__setitem__('status','recognized'),
  'missing_index_link':lambda b:b['graph'].__setitem__('edges',[e for e in b['graph']['edges'] if e['type']!='indexed_problem_shape']),
 }
 for name,mutate in mutations.items():
  candidate=json.loads(json.dumps(base));mutate(candidate)
  try:validate_bundle(candidate);cases[name]={'rejected':False,'error':None}
  except BundleError as ex:cases[name]={'rejected':True,'error':ex.code}
 try:read_bundle_bytes(raw[:-1]);cases['truncated_json']={'rejected':False,'error':None}
 except BundleError as ex:cases['truncated_json']={'rejected':True,'error':ex.code}
 # Simulate a write failure after fsync but before atomic replacement.
 prior=Path(path).read_bytes();new_bytes=(prior+b' ');failure=None
 try:atomic_write(path,new_bytes,fail_before_replace=True)
 except OSError as ex:failure=str(ex)
 target_preserved=Path(path).read_bytes()==prior
 temp_files=list(Path(path).parent.glob(f'.{Path(path).name}.*.tmp'))
 # Exercise the successful replacement path and revalidate its output.
 atomic_write(path,prior);success_valid=read_bundle_bytes(Path(path).read_bytes())==base
 return {'schema_rejection_cases':cases,'all_corruptions_rejected':all(v['rejected'] for v in cases.values()),'atomic_failure_injected':failure=='injected_before_replace','atomic_failure_preserved_previous_target':target_preserved,'temporary_files_cleaned':not temp_files,'atomic_success_replaces_with_valid_bundle':success_valid}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path);ap.add_argument('--arm',choices=['control','compact_write','compact_read']);ap.add_argument('--checkpoint',type=Path);a=ap.parse_args()
 if a.arm=='control':print(json.dumps(worker_control(),sort_keys=True));return 0
 if a.arm=='compact_write':print(json.dumps(worker_compact_write(a.checkpoint),sort_keys=True));return 0
 if a.arm=='compact_read':print(json.dumps(worker_compact_read(a.checkpoint),sort_keys=True));return 0
 if not a.output:ap.error('--output required')
 lock=json.loads(LOCK.read_text());want={'preregistration_sha256':sha(PREREG),'runner_sha256':sha(Path(__file__)),'candidate_runner_sha256':sha(CANDIDATE),'native_sha256':sha(ROOT/'runners/dsl/python/substrate_rs/_native.abi3.so'),'seed_hashes':{p.name:sha(p) for p in SEEDS},'full_scale_checkpoint_raw_sha256':sha(FULL_SCALE_RAW),'schema_sha256':sha(SCHEMA_FILE)}
 if any(lock.get(k)!=v for k,v in want.items()):raise SystemExit('minimal checkpoint lock mismatch')
 full_scale=json.loads(FULL_SCALE_RAW.read_text());full_bytes=next(x['writer']['checkpoint_bytes'] for x in full_scale['records'] if x['size']==8)
 stale=subprocess.check_output([sys.executable,'-c',"from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')))"],cwd=ROOT,text=True).strip()
 if stale:raise SystemExit(f'native build stale:\n{stale}')
 env={**os.environ,'PYTHONPATH':f'{ROOT}:{ROOT/"runners/dsl/python"}:{ROOT/"scripts"}'}
 with tempfile.TemporaryDirectory(prefix='ps-min-checkpoint-') as td:
  cp=Path(td)/'minimal.json'
  outputs={}
  for arm in ('control','compact_write'):
   cmd=[sys.executable,str(Path(__file__).resolve()),'--arm',arm]
   if arm!='control':cmd+=['--checkpoint',str(cp)]
   p=subprocess.run(cmd,cwd=ROOT,env=env,text=True,capture_output=True,timeout=180)
   if p.returncode:raise RuntimeError(f'{arm} failed:\n{p.stdout}\n{p.stderr}')
   outputs[arm]=json.loads(p.stdout);print(json.dumps({'arm':arm,'pid':outputs[arm]['process_id']}),flush=True)
  probes=corruption_and_atomic_probes(cp)
  cmd=[sys.executable,str(Path(__file__).resolve()),'--arm','compact_read','--checkpoint',str(cp)]
  p=subprocess.run(cmd,cwd=ROOT,env=env,text=True,capture_output=True,timeout=180)
  if p.returncode:raise RuntimeError(f'compact_read failed:\n{p.stdout}\n{p.stderr}')
  outputs['compact_read']=json.loads(p.stdout);print(json.dumps({'arm':'compact_read','pid':outputs['compact_read']['process_id']}),flush=True)
 control,writer,reader=(outputs[x] for x in ('control','compact_write','compact_read'))
 state_equal=control['state']==reader['state']; ids=[control['process_id'],writer['process_id'],reader['process_id']]
 state=reader['state']; checks={'all_eight_recognized':len(state['observations'])==8 and all(o['status']=='recognized' for o in state['observations']),'same_state_as_full_control':state_equal,'minted_shape_exact':state['shapes']==[{'name':'ps_has_bound=yes','support':2,'minted':1.0}],'final_index_support_eight':state['indexes']==[{'key':'ps_has_bound=yes','support_count':8}],'events_consumed':all(v==0 for v in state['events'].values()),'epoch_one':state['epoch']==1,'all_five_rules_restored':set(state['active_rules'])==PS_RULES,'fixed_point':state['fixed_point'],'support_and_links_exact':state['support_exact'] and state['index_links_exact'],'compact_below_five_percent_full_adapter':writer['checkpoint_bytes']<0.05*full_bytes}
 probes_pass=probes['all_corruptions_rejected'] and probes['atomic_failure_preserved_previous_target'] and probes['temporary_files_cleaned'] and probes['atomic_success_replaces_with_valid_bundle']
 result={'schema_version':1,'run_id':f'problem-shape-minimal-checkpoint-{time.strftime("%Y%m%dT%H%M%SZ",time.gmtime())}','preregistration':{'path':str(PREREG.relative_to(ROOT)),'sha256':sha(PREREG)},'lock':{'path':str(LOCK.relative_to(ROOT)),'sha256':sha(LOCK)},'runner_sha256':sha(Path(__file__)),'candidate_runner_sha256':sha(CANDIDATE),'native_sha256':sha(ROOT/'runners/dsl/python/substrate_rs/_native.abi3.so'),'schema_sha256':sha(SCHEMA_FILE),'seed_hashes':{p.name:sha(p) for p in SEEDS},'arms':outputs,'full_adapter_n8_checkpoint_bytes':full_bytes,'validation_and_atomic_probes':probes,'checks':checks,'distinct_process_ids':len(set(ids))==3,'all_checks_pass':all(checks.values()) and len(set(ids))==3 and probes_pass}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'checks':checks,'all_checks_pass':result['all_checks_pass']}));return 0 if result['all_checks_pass'] else 2
if __name__=='__main__':raise SystemExit(main())
