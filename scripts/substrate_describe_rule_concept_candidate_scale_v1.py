#!/usr/bin/env python3
"""Scale the three live describe recognition-rule motifs against distractor Concepts."""
from __future__ import annotations
import hashlib,json,os,platform,resource,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'scripts')]
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_DESCRIBE_RULE_CONCEPT_CANDIDATE_SCALE_V1_PREREG_20260927.md'
LOCK=ROOT/'evaluation/substrate_capability/describe_rule_concept_candidate_scale_v1_lock_20260927.json'
OUT=ROOT/'evaluation/reports/describe_rule_concept_candidate_scale_v1_20260927.json'
DISTRACTORS=[0,64,256,1024,4096];REPLICATES=3
LABELS=[('a_counter','meter'),('a_thing_that_stays_put','static'),('a_thing_that_moves_itself','mover')]
SOURCES={
 'arc_self_report':ROOT/'scripts/arc_self_report.py','world_adapter':ROOT/'substrate/world_adapter.py',
 'boot_core':ROOT/'substrate/boot_core.py','term_engine':ROOT/'runners/dsl/src/term.rs',
 'rewrite_engine':ROOT/'runners/dsl/src/rewrite.rs','native_py':ROOT/'runners/dsl/src/py.rs',
 'native_build_manifest':ROOT/'runners/dsl/python/substrate_rs/_native.build.json',
 'native_extension':ROOT/'runners/dsl/python/substrate_rs/_native.abi3.so'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inputs():return {'protocol_sha256':sha(PROTOCOL),'runner_sha256':sha(__file__),'source_sha256':{k:sha(v) for k,v in SOURCES.items()}}
def attr(node,key):return {'type':'Attr','node':{'type':'Var','name':node},'key':key}
def lit(v):return {'type':'Lit','value':v}
def var(name):return {'type':'Var','name':name}
def holds(label,node):return {'type':'Holds','concept':label,'node':var(node)}
def worker(distractors,rep):
 from substrate.world_adapter import WorldAdapter
 a=WorldAdapter(seeds=());s=a.s;n=a.inner
 mt=n.add_node('Microtheory',{'name':'candidate_scale_gmt'})
 scene=n.add_node('Scene',{'name':'fixed_scene'})
 percepts={}
 for kind in ('meter','static','mover'):
  p=n.add_node('Percept',{'kind':kind,'fixture':'fixed_three_percepts'})
  n.add_edge_unchecked(scene,'has_percept',p);percepts[kind]=p
 targets={}
 for label,kind in LABELS:
  c=n.add_node('Concept',{'name':label,'fixture_role':'positive_target'})
  n.add_edge_unchecked(mt,'has_concept',c);targets[label]=c
  n.define_concept(label,{'type':'Eq','a':attr('x','kind'),'b':lit(kind)})
 noise=[]
 for i in range(distractors):
  c=n.add_node('Concept',{'name':f'distractor_{i:05d}','fixture_role':'negative_distractor'})
  n.add_edge_unchecked(mt,'has_concept',c);noise.append(c)
 rule_ids=[]
 for label,_kind in LABELS:
  rule={'name':f'recognise_{label}','match':[['scene','has_percept','p'],['gmt','has_concept','con']],
   'match_type':'Concept','where':{'type':'And','items':[{'type':'Eq','a':attr('con','name'),'b':lit(label)},holds(label,'p')]},
   'effects':[['add_edge','p','is_a','con']]}
  rule_ids.append(int(n.add_rule(rule)))
 expected={int(percepts[kind].value):int(targets[label].value) for label,kind in LABELS}
 Native=__import__('substrate_rs')._native.Substrate
 Native.scale_audit_reset();Native.scale_audit_per_rule_reset();Native.scale_audit_set_enabled(True);Native.scale_audit_set_per_rule_enabled(True)
 wall0,cpu0=time.perf_counter_ns(),time.process_time_ns();settle=n.run_rules_report(100000,False);wall,cpu=time.perf_counter_ns()-wall0,time.process_time_ns()-cpu0
 scale=dict(Native.scale_audit_snapshot());raw_per=Native.scale_audit_per_rule_snapshot();names={int(x[0]):str(x[1]) for x in n.rule_access_sets()}
 per=[{'rule_index':int(i),'rule_name':names.get(int(i),'?'),'metric':str(metric),'count':int(v)} for i,metric,v in raw_per]
 Native.scale_audit_set_per_rule_enabled(False);Native.scale_audit_set_enabled(False)
 actual={}
 for p in percepts.values():
  for c in n.neighbours(p,'is_a'):
   if s.has_node(c):actual.setdefault(int(p.value),[]).append(int(c.value))
 actual={k:sorted(v) for k,v in actual.items()};expected={k:[v] for k,v in expected.items()}
 valid=all(actual.get(k,[])==v for k,v in expected.items()) and len(actual)==3
 return {'distractor_count':distractors,'concept_population':len(targets)+len(noise),'percept_count':len(percepts),'replicate':rep,'pid':os.getpid(),
  'rule_ids':rule_ids,'rule_count':len(n.rule_access_sets()),'settle_report':settle,'exact_positive_classification':valid,'expected_edges':expected,'actual_edges':actual,
  'scale_audit':scale,'per_rule_audit':per,'wall_ns':wall,'cpu_ns':cpu,'peak_rss_bytes':int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024),
  'environment':{'python':sys.version,'platform':platform.platform()}}
def worker_ok(r):return r['settle_report']['status']=='fixed_point' and r['exact_positive_classification'] and len(r['actual_edges'])==3
def main():
 if sys.argv[1:]==['--lock']:print(json.dumps({'locked_inputs':inputs()},indent=2,sort_keys=True));return
 if sys.argv[1:]==['--worker']:
  before=inputs();r=worker(int(os.environ['OCEL0_DESC_CANDIDATES']),int(os.environ['OCEL0_DESC_REP']));after=inputs();r.update({'worker_inputs_before':before,'worker_inputs_after':after,'source_stable':before==after});print(json.dumps(r,sort_keys=True));return
 locked=inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing/stale describe-rule candidate scale lock')
 env={**os.environ,'PYTHONPATH':f'{ROOT}:{ROOT / "runners/dsl/python"}:{ROOT / "scripts"}','OZMA_NO_LLM':'1','OZMA_SEED_PERSIST_DISABLED':'1'}
 stale=subprocess.check_output([sys.executable,'-c',"from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')) )"],cwd=ROOT,env=env,text=True).strip()
 if stale:raise SystemExit(f'native build stale: {stale}')
 runs=[]
 for d in DISTRACTORS:
  for rep in range(REPLICATES):
   e=env.copy();e.update(OCEL0_DESC_CANDIDATES=str(d),OCEL0_DESC_REP=str(rep));p=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker'],cwd=ROOT,env=e,text=True,capture_output=True,timeout=180)
   r=json.loads(p.stdout) if p.stdout.strip() else {'distractor_count':d,'replicate':rep,'worker_error':p.stderr};r['worker_returncode']=p.returncode;r['worker_stderr']=p.stderr;runs.append(r);print(f'completed=distractors{d}/{rep} rc={p.returncode}',file=sys.stderr,flush=True)
 after=inputs();checks={'fifteen_workers':len(runs)==15,'unique_pids':len({r.get('pid') for r in runs})==15,'three_replicates_per_size':all(sum(r.get('distractor_count')==d for r in runs)==3 for d in DISTRACTORS),'parent_source_stable':after==locked,'workers_source_stable':all(r.get('source_stable') and r.get('worker_inputs_before')==locked==r.get('worker_inputs_after') for r in runs),'all_workers_returned':all(r.get('worker_returncode')==0 for r in runs),'all_semantics_fixedpoint':all(worker_ok(r) for r in runs)}
 rows=[]
 for d in DISTRACTORS:
  group=[r for r in runs if r.get('distractor_count')==d]
  candidate=sum(x['count'] for r in group for x in r.get('per_rule_audit',[]) if x['metric']=='candidate_pairs')//max(1,len(group))
  terms=sum(x['count'] for r in group for x in r.get('per_rule_audit',[]) if x['metric']=='term_evaluations')//max(1,len(group))
  rows.append({'distractor_count':d,'concept_population':d+len(LABELS),'replicates':len(group),'candidate_pairs_median':candidate,'term_evaluations_median':terms,'wall_ms_median':sorted(r['wall_ns'] for r in group)[len(group)//2]/1e6 if group else None,'cpu_ms_median':sorted(r['cpu_ns'] for r in group)[len(group)//2]/1e6 if group else None})
 checks['work_counts_monotonic']=all(rows[i]['candidate_pairs_median']<=rows[i+1]['candidate_pairs_median'] and rows[i]['term_evaluations_median']<=rows[i+1]['term_evaluations_median'] for i in range(len(rows)-1))
 report={'schema_version':1,'run_id':'describe-rule-concept-candidate-scale-v1-20260927','locked_inputs':locked,'post_run_inputs':after,'checks':checks,'all_checks_pass':all(checks.values()),'summary_by_size':rows,'runs':runs,'claim_boundary':'Controlled scaling of three source-derived Scene/Percept × Microtheory/Concept recognition rules with exact kind-based Holds predicates and synthetic negative distractors; not the complete describe faculty or natural-task scaling.'}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':checks,'summary_by_size':rows},indent=2))
 if not all(checks.values()):raise SystemExit('describe-rule candidate scale gates failed')
if __name__=='__main__':main()
