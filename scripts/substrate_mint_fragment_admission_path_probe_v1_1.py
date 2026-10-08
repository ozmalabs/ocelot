#!/usr/bin/env python3
"""Probe whether live rule admission routes enforce the finite-key fragment."""
from __future__ import annotations
import hashlib, json, os, platform, resource, subprocess, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'scripts')]
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_MINT_FRAGMENT_ADMISSION_PATH_PROBE_V1_1_AMENDMENT_20260928.md'
LOCK=ROOT/'evaluation/substrate_capability/mint_fragment_admission_path_probe_v1_1_lock_20260928.json'
OUT=ROOT/'evaluation/reports/substrate_mint_fragment_admission_path_probe_v1_1_20260928.json'
ANALYZER=ROOT/'scripts/analyze_substrate_mint_fragment_admission_path_probe_v1_1.py'
SOURCES=('scripts/substrate_mint_fragment_admission_path_probe_v1_1.py','scripts/analyze_substrate_mint_fragment_admission_path_probe_v1_1.py','scripts/analyze_mint_termination_fragment.py','domains/engine_provenance.py','substrate/world_adapter.py','substrate/boot_core.py','substrate/seed_loader.py','docs/research/engine_substrate/SUBSTRATE_MINT_FRAGMENT_ADMISSION_PATH_PROBE_V1_1_AMENDMENT_20260928.md','runners/dsl/src/cognitive_cycle.rs','runners/dsl/src/graph_rules.rs','runners/dsl/src/py.rs','runners/dsl/src/rewrite.rs','runners/dsl/src/substrate.rs','runners/dsl/src/term.rs','runners/dsl/python/substrate_rs/_native.build.json')
WORKERS=(0,1,2)
NEGATIVE={'name':'finite_key_admission_negative','match':[['x','admission_trigger','y']],'where':None,'effects':[['add_node','fresh','AdmissionWitness',{'tag':'fresh'}]]}
SAFE={'name':'finite_key_patch_seed','match':[['x','admission_trigger','y']],'where':None,'effects':[['add_node_if_absent','w','AdmissionWitness',{'tag':'fixed'}]]}
INITIAL_NODES=['n0','n1'];INITIAL_EDGES=[['n0','admission_trigger','n1']]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inputs():
 from substrate_rs import _native
 return {'files':{p:sha(ROOT/p) for p in SOURCES},'native_extension_sha256':sha(Path(_native.__file__).resolve()),'native_build_stale':__import__('domains.engine_provenance',fromlist=['build_is_stale']).build_is_stale(str(ROOT)),'negative_rule':NEGATIVE,'safe_rule':SAFE,'initial_node_ids':INITIAL_NODES,'initial_edges':INITIAL_EDGES,'workers':list(WORKERS)}
def checker_result():
 from analyze_mint_termination_fragment import analyze
 return analyze([{'name':NEGATIVE['name'],'match':NEGATIVE['match'],'effects':NEGATIVE['effects']}],INITIAL_NODES,INITIAL_EDGES)
def direct_route():
 from substrate_rs import _native
 s=_native.Substrate();err=None;idx=None
 try:idx=s.add_rule(NEGATIVE)
 except BaseException as e:err=f'{type(e).__name__}: {e}'
 return {'route':'direct_add_rule','accepted':err is None,'error':err,'rule_count':s.rule_count(),'rule':s.export_rules()[0] if idx is not None else None}
def import_route():
 from substrate_rs import _native
 s=_native.Substrate();err=None;count=None
 try:count=s.import_rules([NEGATIVE])
 except BaseException as e:err=f'{type(e).__name__}: {e}'
 return {'route':'checkpoint_import','accepted':err is None,'error':err,'imported_count':count,'rule_count':s.rule_count(),'rule':s.export_rules()[0] if count else None}
def patch_route():
 from substrate_rs import _native
 s=_native.Substrate();idx=s.add_rule(SAFE);before=s.rule_metadata(idx);err=None;receipt=None
 try:receipt=s.apply_rule_patch(before['rule_uid'],before['revision'],before['content_hash'],'effects',NEGATIVE['effects'])
 except BaseException as e:err=f'{type(e).__name__}: {e}'
 after=s.rule_metadata(idx)
 return {'route':'rule_patch_revision','accepted':err is None,'error':err,'before':before,'after':after,'receipt':receipt,'rule':s.export_rules()[idx]}
def graph_self_mint_route():
 from substrate.world_adapter import WorldAdapter
 a=WorldAdapter(seeds=(),shadow_read=False,deep_ingest=False)
 anchor=a.s.add_node('AdmissionAnchor',{});trigger=a.s.add_node('AdmissionTrigger',{});a.inner.add_edge_unchecked(anchor,'wants_mint',trigger)
 target=a.s.add_node('Rule',{'id':'minted_out_of_fragment','match':[['x','never_fire_admission','y']],'where':{'type':'Lit','value':True},'effect':[['add_node','fresh','AdmissionWitness',{'tag':'fresh'}]],'minted':0.0})
 a.inner.add_edge_unchecked(anchor,'owns_rule',target)
 mint=a.s.add_node('Rule',{'id':'mint_out_of_fragment_once','match':[['a','wants_mint','t'],['a','owns_rule','rn']],'where':{'type':'Lt','a':{'type':'Attr','node':{'type':'Var','name':'rn'},'key':'minted'},'b':{'type':'Lit','value':0.5}},'effect':[['set_rule_clause',{'__term__':{'type':'Attr','node':{'type':'Var','name':'rn'},'key':'id'}},'__mint__',{'__term__':{'type':'Var','name':'rn'} }],['set_attr','rn','minted',{'__term__':{'type':'Lit','value':1.0}}]]})
 before=a.inner.rule_count();err=None
 cycle_report=None
 try:cycle_report=a.inner.run_cycle('graph_then_struct',100)
 except BaseException as e:err=f'{type(e).__name__}: {e}'
 after=a.inner.rule_count();rules=a.inner.export_rules();new=[r for r in rules if r.get('name')=='minted_out_of_fragment']
 return {'route':'graph_rule_self_mint','accepted':len(new)==1,'error':err,'cycle_report':cycle_report,'rule_count_before':before,'rule_count_after':after,'minted_rule_count':len(new),'minted_rule':new[0] if new else None,'trigger_edge_absent':len(a.inner.neighbours(trigger,'never_fire_admission'))==0,'rule_node_ids':[int(target.value if hasattr(target,'value') else target),int(mint.value if hasattr(mint,'value') else mint)]}
def worker(rep):
 before=inputs();started=time.perf_counter_ns();checker=checker_result();rows=[direct_route(),import_route(),patch_route(),graph_self_mint_route()];elapsed=time.perf_counter_ns()-started;after=inputs()
 return {'replicate':rep,'pid':os.getpid(),'before':before,'after':after,'checker':checker,'routes':rows,'elapsed_wall_ns':elapsed,'peak_rss_bytes':int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024),'environment':{'python':sys.version,'platform':platform.platform()}}
def main():
 if sys.argv[1:]==['--lock']:
  print(json.dumps({'locked_inputs':inputs()},indent=2,sort_keys=True));return
 if len(sys.argv)==2 and sys.argv[1]=='--worker':
  print(json.dumps(worker(int(os.environ['OCEL0_ADMISSION_REP'])),sort_keys=True));return
 locked=json.loads(LOCK.read_text())
 if locked.get('locked_inputs')!=inputs():raise SystemExit('locked inputs changed')
 started=time.time();runs=[];env={**os.environ,'PYTHONPATH':f'{ROOT}:{ROOT/"runners/dsl/python"}:{ROOT/"scripts"}','OZMA_SEED_PERSIST_DISABLED':'1'}
 for rep in WORKERS:
  cp=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker'],cwd=ROOT,env={**env,'OCEL0_ADMISSION_REP':str(rep)},text=True,capture_output=True,timeout=300)
  try:row=json.loads(cp.stdout)
  except Exception:row={'replicate':rep,'worker_error':cp.stderr or cp.stdout}
  row.update({'worker_returncode':cp.returncode,'worker_stderr':cp.stderr});runs.append(row)
 post=inputs();checks={'three_fresh_workers':len(runs)==3 and len({r.get('pid') for r in runs})==3,'parent_lock_stable':post==locked['locked_inputs'],'workers_source_stable':all(r.get('before')==locked['locked_inputs']==r.get('after') for r in runs),'each_worker_has_four_routes':all(len(r.get('routes',[]))==4 for r in runs),'worker_success':all(r.get('worker_returncode')==0 and not r.get('worker_error') for r in runs)}
 raw={'schema_version':1,'run_id':'substrate-mint-fragment-admission-path-probe-v1-1-20260928','started_epoch_s':started,'locked_inputs':locked['locked_inputs'],'post_run_inputs':post,'checks':checks,'all_checks_pass':all(checks.values()),'runs':runs,'claim_boundary':'Three-worker probe of four exact rule admission/revision routes; rejected finite-key syntax is installed but never closed. Not an exhaustive admission inventory or termination experiment.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(raw,indent=2,sort_keys=True)+'\n');print(json.dumps({'raw':str(OUT.relative_to(ROOT)),'checks':checks,'all_checks_pass':raw['all_checks_pass']},indent=2))
 if not raw['all_checks_pass']:raise SystemExit('runner gates failed; raw result preserved')
if __name__=='__main__':main()
