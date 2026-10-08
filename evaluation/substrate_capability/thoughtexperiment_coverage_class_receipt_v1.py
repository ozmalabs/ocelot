#!/usr/bin/env python3
"""Return coverage-qualified class receipts from isolated CoW graph branches."""
from __future__ import annotations
import hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
HERE=Path(__file__).resolve()
PRE=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_COVERAGE_CLASS_RECEIPT_V1_PREREG_20261004.md'
AN=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_coverage_class_receipt_v1.py'
UPRUN=ROOT/'evaluation/substrate_capability/coverage_aware_class_return_v1.py'
UPLOCK=ROOT/'evaluation/substrate_capability/coverage_aware_class_return_v1_lock_20261003.json'
UPRAW=ROOT/'evaluation/reports/coverage_aware_class_return_v1_20261003.json'
UPAN=ROOT/'evaluation/substrate_capability/analyze_coverage_aware_class_return_v1_1.py'
UPREPORT=ROOT/'evaluation/reports/coverage_aware_class_return_v1_1_analysis_20261004.json'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_coverage_class_receipt_v1_lock_20261004.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_coverage_class_receipt_v1_20261004.json'
SOURCES=('docs/research/engine_substrate/THOUGHTEXPERIMENT_COVERAGE_CLASS_RECEIPT_V1_PREREG_20261004.md',
 'evaluation/substrate_capability/thoughtexperiment_coverage_class_receipt_v1.py',
 'evaluation/substrate_capability/analyze_thoughtexperiment_coverage_class_receipt_v1.py',
 'evaluation/substrate_capability/coverage_aware_class_return_v1.py',
 'evaluation/substrate_capability/coverage_aware_class_return_v1_lock_20261003.json',
 'evaluation/reports/coverage_aware_class_return_v1_20261003.json',
 'evaluation/substrate_capability/analyze_coverage_aware_class_return_v1_1.py',
 'evaluation/reports/coverage_aware_class_return_v1_1_analysis_20261004.json',
 'runners/dsl/python/substrate_rs/__init__.py','runners/dsl/python/substrate_rs/_native.build.json',
 'runners/dsl/src/graph.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs',
 'domains/engine_provenance.py')

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def nid(x):return int(x.value if hasattr(x,'value') else x)
def graph_canonical(g):
 return {'nodes':sorted(g['nodes'],key=lambda x:int(x['id'])),
  'edges':sorted(g['edges'],key=lambda x:(int(x['src']),x['type'],int(x['tgt']),json.dumps(x.get('attrs',{}),sort_keys=True,separators=(',',':'))))}
def source_map():
 from substrate_rs import _native
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 if build_is_stale(str(ROOT)):raise RuntimeError('native engine stale')
 return {'files':{x:sha(ROOT/x) for x in SOURCES},'binary':{'path':str(Path(_native.__file__).resolve()),'sha256':sha(Path(_native.__file__).resolve())},'rust_fingerprint':rust_source_fingerprint(str(ROOT)),'python':sys.version,'platform':platform.platform()}
def panels_from_upstream():
 lock=json.loads(UPLOCK.read_text());raw=json.loads(UPRAW.read_text());analysis=json.loads(UPREPORT.read_text())
 if not analysis.get('passed') or analysis.get('errors'):raise RuntimeError('upstream policy analysis did not pass')
 if raw.get('lock_sha256')!=sha(UPLOCK) or raw.get('sources')!=lock.get('sources'):raise RuntimeError('upstream capture provenance mismatch')
 if analysis.get('capture_sha256')!=sha(UPRAW) or analysis.get('lock_sha256')!=sha(UPLOCK):raise RuntimeError('upstream analysis hashes mismatch')
 panels={(p['task'],p['worker']):p for p in lock['panels']};workers={(w['task'],w['worker']):w for w in raw['workers']};chosen=[]
 for row in analysis['rows']:
  if row['decision']!='behavior_class':continue
  key=(row['task'],row['worker']);p=panels[key];w=workers[key];r=w['result']
  if not row['all_survivors_exact'] or not r.get('coverage',{}).get('adequate'):raise RuntimeError(f'unsafe upstream class {key}')
  ids=sorted(x['id'] for x in r['survivors']);part=r.get('behavior_partition') or {}
  if part.get('class_count')!=1 or sorted(part['classes'][0]['hypothesis_ids'])!=ids:raise RuntimeError(f'class partition mismatch {key}')
  initial={x['id']:x for x in p['initial_hypotheses']}
  if any(i not in initial for i in ids):raise RuntimeError(f'candidate outside frozen initial set {key}')
  chosen.append({'task':key[0],'worker':key[1],'labels':r['calls'],'probe_count':r['coverage']['probe_count'],'holdout_safe':True,
    'initial_hypotheses':p['initial_hypotheses'],'member_ids':ids,'returned_terms':{x['id']:x['term'] for x in r['survivors']}})
 if len(chosen)!=5:raise RuntimeError(f'expected five class-return panels, got {len(chosen)}')
 return chosen
def graph_digest(sub):return digest(sub.graph_to_dict())
def worker(panel):
 from substrate_rs import Substrate
 primary=Substrate();root=primary.add_node('ThoughtExperimentProposal',{'role':'hypothesis_pool','task':panel['task'],'worker':int(panel['worker'])})
 candidates={}
 for h in panel['initial_hypotheses']:
  candidate_node=primary.add_node('ThoughtExperimentProposal',{'role':'candidate','candidate_id':h['id'],'family':h['family'],'term_json':json.dumps(h['term'],sort_keys=True,separators=(',',':'))})
  primary.add_edge_unchecked(root,'contains_candidate',candidate_node,{})
  candidates[h['id']]=candidate_node
 rules_before_state=primary._inner.export_rules();rules_before=digest(rules_before_state);before=primary.graph_to_dict();revision=tuple(primary.experiment_graph_rule_revision())
 t=time.perf_counter_ns();snapshot=primary._snapshot_with_backend('shared_graph_pages');branch=snapshot.fork();fork_ns=time.perf_counter_ns()-t
 if graph_digest(primary)!=digest(before):raise RuntimeError('fork changed primary')
 branch.begin_experiment_delta_journal();branch.checkpoint_experiment_delta_journal()
 t=time.perf_counter_ns();receipt=branch.add_node('ThoughtExperimentProposal',{'role':'coverage_qualified_behavior_class','decision':'behavior_class',
  'task':panel['task'],'worker':int(panel['worker']),'oracle_labels':int(panel['labels']),'covered_probe_count':int(panel['probe_count']),
  'finite_holdout_safe':1.0,'member_count':len(panel['member_ids']),'candidate_ids_json':json.dumps(panel['member_ids'],separators=(',',':'))})
 for hid in panel['member_ids']:branch.add_edge_unchecked(receipt,'returns_member',candidates[hid],{})
 mutate_ns=time.perf_counter_ns()-t
 t=time.perf_counter_ns();branch_state=branch.graph_to_dict();journal=branch.finish_experiment_delta_journal();delta=journal['derived_only'];extract_ns=time.perf_counter_ns()-t
 primary_before_return=primary.graph_to_dict()
 unchanged_before_return=graph_digest(primary)==digest(before) and digest(primary._inner.export_rules())==rules_before and tuple(primary.experiment_graph_rule_revision())==revision
 if not unchanged_before_return:raise RuntimeError('branch work leaked before return')
 t=time.perf_counter_ns();primary.apply_experiment_graph_delta(revision,delta);apply_ns=time.perf_counter_ns()-t
 adopted=primary.graph_to_dict();rules_after_state=primary._inner.export_rules();rules_after=digest(rules_after_state)
 stale_before=digest(adopted);stale_rejected=False;stale_error=''
 try:primary.apply_experiment_graph_delta(revision,delta)
 except RuntimeError as e:stale_rejected=True;stale_error=str(e)
 stale_unchanged=digest(primary.graph_to_dict())==stale_before
 return {'pid':os.getpid(),'task':panel['task'],'worker':panel['worker'],'revision':list(revision),'branch_backend':'shared_graph_pages',
  'primary_before':before,'primary_before_return':primary_before_return,'branch_after':branch_state,'primary_after':adopted,'derived_delta':delta,'receipt_id':nid(receipt),
  'rules_before':rules_before_state,'rules_after':rules_after_state,
  'candidate_node_ids':{k:nid(v) for k,v in candidates.items()},'expected_member_ids':panel['member_ids'],'returned_terms':panel['returned_terms'],
  'holdout_safe':panel['holdout_safe'],'primary_unchanged_before_return':unchanged_before_return,
  'branch_primary_parity':graph_canonical(branch_state)==graph_canonical(adopted),'rules_preserved':rules_before==rules_after,
  'stale_retry_rejected':stale_rejected,'stale_retry_unchanged':stale_unchanged,'stale_error':stale_error,
  'timing_ns':{'fork':fork_ns,'receipt_mutation':mutate_ns,'delta_extract':extract_ns,'apply':apply_ns},'journal':journal}
def main():
 args=sys.argv[1:]
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  LOCK.write_text(json.dumps({'schema':'ThoughtexperimentCoverageClassReceiptV1Lock','sources':source_map(),'panels':panels_from_upstream(),'backend':'shared_graph_pages'},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if args==['--run']:
  lock=json.loads(LOCK.read_text())
  if source_map()!=lock['sources'] or panels_from_upstream()!=lock['panels']:raise SystemExit('source or panel drift')
  env={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}'};rows=[]
  for i,p in enumerate(lock['panels']):
   proc=subprocess.run([sys.executable,str(HERE),'--worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=60)
   if proc.returncode:raise RuntimeError(proc.stderr[-2000:])
   rows.append(json.loads(proc.stdout.strip().splitlines()[-1]))
  if source_map()!=lock['sources']:raise SystemExit('source drift during capture')
  OUT.write_text(json.dumps({'schema':'ThoughtexperimentCoverageClassReceiptV1Results','lock_sha256':sha(LOCK),'sources':source_map(),'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'workers':rows},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
 if len(args)==2 and args[0]=='--worker':print(json.dumps(worker(json.loads(LOCK.read_text())['panels'][int(args[1])]),sort_keys=True,separators=(',',':')));return 0
 raise SystemExit('usage: --lock | --run | --worker ID')
if __name__=='__main__':raise SystemExit(main())
