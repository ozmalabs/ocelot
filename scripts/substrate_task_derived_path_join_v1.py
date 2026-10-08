#!/usr/bin/env python3
"""Measure a task-authored three-edge path rule under native order permutations."""
from __future__ import annotations
import hashlib,itertools,json,os,random,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'scripts')]
from substrate_rs import Substrate,_native
from domains.engine_provenance import assert_measuring_engine
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_TASK_DERIVED_PATH_JOIN_V1_PREREG_20260927.md'
LOCK=ROOT/'evaluation/substrate_capability/task_derived_path_join_v1_lock_20260927.json'
RAW=ROOT/'evaluation/reports/substrate_task_derived_path_join_v1_workers_raw_20260927.json'
OUT=ROOT/'evaluation/reports/substrate_task_derived_path_join_v1_20260927.json'
ANALYZER=ROOT/'scripts/analyze_substrate_task_derived_path_join_v1.py'
SEED=ROOT/'seeds/self_change_reasoning.json'
SOURCES=('runners/dsl/src/rewrite.rs','runners/dsl/src/py.rs','runners/dsl/src/scale_audit.rs','runners/dsl/src/substrate.rs','runners/dsl/python/substrate_rs/_native.build.json')
ORDERS=tuple(itertools.permutations(range(3)))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fingerprint():
 paths=(str(PROTOCOL.relative_to(ROOT)),str(Path(__file__).relative_to(ROOT)),str(ANALYZER.relative_to(ROOT)),str(SEED.relative_to(ROOT)),*SOURCES)
 return {'files':{p:sha(ROOT/p) for p in paths},'native_sha256':sha(Path(_native.__file__).resolve()),'native_path':str(Path(_native.__file__).resolve()),'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()}
def normalized_graph(s):
 g=s.graph_to_dict();nodes=g['nodes'];edges=g['edges']
 keys={}
 for n in nodes:
  key=json.dumps({'type':n['type'],'attrs':n.get('attrs',{})},sort_keys=True,separators=(',',':'))
  if key in keys:raise RuntimeError(f'non-unique normalization key: {key}')
  keys[key]=n['id']
 by_id={v:k for k,v in keys.items()}
 return {'nodes':sorted(keys),'edges':sorted((by_id[e['src']],e['type'],by_id[e['tgt']]) for e in edges)}
def make_substrate(m,q,order,audit):
 data=json.loads(SEED.read_text());rule=next(r for r in data['rules'] if r.get('name')=='sc_canary_requests_commit')
 rule=json.loads(json.dumps(rule));rule['name']='sc_canary_requests_commit_path_order_v1';rule['match']=[rule['match'][i] for i in order]
 s=Substrate();inner=s._inner;sc=s.add_node('SelfChange',{'status':'awaiting_canary','ordinal':0})
 positives=[];d=q*m
 for i in range(m):
  p=s.add_node('RulePatch',{'target_uid':f'probe-target-{i}','expected_revision':0,'state':'ready','role':'positive','ordinal':i})
  c=s.add_node('Canary',{'status':'pending','role':'positive','ordinal':i})
  e=s.add_node('CanaryEvidence',{'replicated_gain':5,'protected_regressions':0,'replications':2,'role':'positive','ordinal':i})
  inner.add_edge_unchecked(sc,'selected_patch',p);inner.add_edge_unchecked(p,'has_canary',c);inner.add_edge_unchecked(c,'has_canary_evidence',e)
  positives.append((p,c,e))
 # D false joins per relation, all relation populations remain M+D.
 for i in range(d):
  p=s.add_node('RulePatch',{'target_uid':f'decoy-selected-{i}','expected_revision':0,'state':'ready','role':'selected_decoy','ordinal':i});inner.add_edge_unchecked(sc,'selected_patch',p)
 for i in range(d):
  p=s.add_node('RulePatch',{'target_uid':f'decoy-canary-{i}','expected_revision':0,'state':'ready','role':'canary_decoy','ordinal':i})
  c=s.add_node('Canary',{'status':'pending','role':'canary_decoy','ordinal':i});inner.add_edge_unchecked(p,'has_canary',c)
 for i in range(d):
  c=s.add_node('Canary',{'status':'pending','role':'evidence_decoy','ordinal':i})
  e=s.add_node('CanaryEvidence',{'replicated_gain':5,'protected_regressions':0,'replications':2,'role':'evidence_decoy','ordinal':i})
  inner.add_edge_unchecked(c,'has_canary_evidence',e)
 idx=int(inner.add_rule(rule));installed=[list(e) for e in inner.export_rules()[idx]['match']]
 if audit:
  _native.Substrate.scale_audit_set_enabled(False);_native.Substrate.scale_audit_set_per_rule_enabled(False)
  _native.Substrate.scale_audit_reset();_native.Substrate.scale_audit_per_rule_reset()
  _native.Substrate.scale_audit_set_per_rule_enabled(True);_native.Substrate.scale_audit_set_enabled(True)
 report=dict(inner.run_rules_report(1000000,False))
 counters=dict(_native.Substrate.scale_audit_snapshot()) if audit else {}
 per=[list(x) for x in _native.Substrate.scale_audit_per_rule_snapshot()] if audit else []
 clauses=[list(x) for x in _native.Substrate.scale_audit_match_clause_snapshot()] if audit else []
 _native.Substrate.scale_audit_set_enabled(False);_native.Substrate.scale_audit_set_per_rule_enabled(False)
 graph=normalized_graph(s)
 nodes=inner.graph_to_dict()['nodes'];attrs={(n['type'],n.get('attrs',{}).get('role'),n.get('attrs',{}).get('ordinal')):n.get('attrs',{}) for n in nodes}
 commit_count=sum(n['type']=='Commit' for n in nodes)
 positive_passed=sum(attrs.get(('Canary','positive',i),{}).get('status')=='passed' for i in range(m))
 positive_patches_queued=sum(attrs.get(('RulePatch','positive',i),{}).get('state')=='transaction_queued' for i in range(m))
 decoy_statuses=[a.get('status') for (t,role,i),a in attrs.items() if t=='Canary' and role in {'canary_decoy','evidence_decoy'}]
 decoy_patch_states=[a.get('state') for (t,role,i),a in attrs.items() if t=='RulePatch' and role in {'selected_decoy','canary_decoy'}]
 source_status=inner.node(sc)['attrs'].get('status')
 commit_edges=sum(e['type']=='has_commit' for e in inner.graph_to_dict()['edges'])
 candidate_total=sum(int(n) for i,name,n in per if int(i)==idx and name=='candidate_tests') if audit else 0
 clause_counts=[0]*len(installed)
 for i,j,n in clauses:
  if int(i)==idx and 0<=int(j)<len(clause_counts):clause_counts[int(j)]+=int(n)
 return {'graph':graph,'report':report,'rule_index':idx,'authored_indices':list(order),'installed_order':[e[1] for e in installed],
  'audit':audit,'counters':counters,'per_rule':per,'clause_candidates':clauses,'target_candidate_tests':candidate_total,
  'target_candidate_tests_by_clause':clause_counts,'commit_count':commit_count,'commit_edges':commit_edges,
  'positive_canaries_passed':positive_passed,'positive_patches_queued':positive_patches_queued,
  'decoy_canary_statuses':decoy_statuses,'decoy_patch_states':decoy_patch_states,'source_status':source_status,
 'relation_counts':{t:sum(e['type']==t for e in inner.graph_to_dict()['edges']) for t in ('selected_patch','has_canary','has_canary_evidence')}}
def worker(m,q,label,rep):
 order=tuple(int(c) for c in label)
 assert set(order)==set(range(3))
 before=fingerprint();plain=make_substrate(m,q,order,False);audited=make_substrate(m,q,order,True);after=fingerprint()
 return {'multiplicity':m,'decoy_ratio':q,'permutation':label,'replicate':rep,'pid':os.getpid(),'before':before,'after':after,'plain':plain,'audit':audited}
def cells():
 for m in (1,8,32):
  for q in (0,4):
   for order in ORDERS:
    label=''.join(map(str,order))
    for rep in range(3):yield m,q,label,rep
def main():
 assert_measuring_engine()
 if sys.argv[1:]==['--lock']:
  LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps(fingerprint(),indent=2,sort_keys=True)+'\n');print(LOCK);return
 if len(sys.argv)==6 and sys.argv[1]=='--worker':
  print(json.dumps(worker(int(sys.argv[2]),int(sys.argv[3]),sys.argv[4],int(sys.argv[5])),sort_keys=True));return
 locked=fingerprint()
 if not LOCK.exists() or json.loads(LOCK.read_text())!=locked:raise SystemExit('missing or stale source/native lock')
 jobs=list(cells());random.Random(20260927).shuffle(jobs);env=dict(os.environ);env['PYTHONHASHSEED']='0';env['PYTHONPATH']=os.pathsep.join((str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'scripts'),env.get('PYTHONPATH','')))
 runs=[]
 for m,q,label,rep in jobs:
  cp=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',str(m),str(q),label,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
  runs.append(json.loads(cp.stdout))
 post=fingerprint();RAW.write_text(json.dumps({'schema_version':1,'run_id':'substrate-task-derived-path-join-v1-20260927','locked_inputs':locked,'post_run_inputs':post,'runs':runs},indent=2,sort_keys=True)+'\n')
 print(json.dumps({'worker_count':len(runs),'stable':post==locked and all(x['before']==locked==x['after'] for x in runs),'raw':str(RAW.relative_to(ROOT))},indent=2))
if __name__=='__main__':main()
