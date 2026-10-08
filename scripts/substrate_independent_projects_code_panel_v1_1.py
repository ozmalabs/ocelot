#!/usr/bin/env python3
"""Source-locked independent-project code behavior panel v1.1."""
from __future__ import annotations
import ast, hashlib, json, os, platform, resource, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
SNAP=ROOT/'data/independent_python_projects_v1_1'
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_INDEPENDENT_PROJECT_CODE_PANEL_V1_1_PREREG_20260928.md'
SNAPSHOTTER=ROOT/'scripts/snapshot_independent_code_projects_v1_1.py'
SELECTOR=ROOT/'scripts/select_independent_projects_code_frame_v1_1.py'
FRAME=ROOT/'evaluation/substrate_capability/independent_projects_code_panel_v1_1_frame_20260928.json'
ANALYZER=ROOT/'scripts/analyze_independent_projects_code_panel_v1_1.py'
LOCK=ROOT/'evaluation/substrate_capability/independent_projects_code_panel_v1_1_lock_20260928.json'
OUT=ROOT/'evaluation/reports/independent_projects_code_panel_v1_1_20260928.json'
def sha(data):return hashlib.sha256(data).hexdigest()
def pathsha(p):return sha(Path(p).read_bytes())
def tree(folder,suffixes):return {p.relative_to(ROOT).as_posix():pathsha(p) for p in sorted(folder.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.suffix in suffixes}
def seeds(folder):
 ps=sorted(folder.glob('*.json'))+sorted((folder/'generated').glob('*.json'))
 return {p.relative_to(ROOT).as_posix():pathsha(p) for p in ps if p.is_file()}
def inputs():
 from substrate_rs import _native
 return {'protocol_sha256':pathsha(PROTOCOL),'snapshotter_sha256':pathsha(SNAPSHOTTER),'selector_sha256':pathsha(SELECTOR),'frame_sha256':pathsha(FRAME),'runner_sha256':pathsha(__file__),'analyzer_sha256':pathsha(ANALYZER),
 'source_trees':{'domains':tree(ROOT/'domains',{'.py'}),'substrate':tree(ROOT/'substrate',{'.py'}),'worlds':tree(ROOT/'worlds',{'.py'}),'scripts':tree(ROOT/'scripts',{'.py'}),'seeds':seeds(ROOT/'seeds'),'native_python':tree(ROOT/'runners/dsl/python',{'.py'}),'rust':tree(ROOT/'runners/dsl/src',{'.rs'}),'independent_projects':tree(SNAP,{'.py','.txt','.md','.json'})},'native_extension_sha256':pathsha(Path(_native.__file__).resolve())}
def nodeid(n):return int(n.value if hasattr(n,'value') else n)
def rows(agent,typ,fields):return [{'id':nodeid(n),**{k:agent.s.node(n)['attrs'].get(k) for k in fields}} for n in agent.s.nodes(typ)]
def receipts(agent):return [r for r in rows(agent,'NativeReflectiveFacultyReceipt',('cluster','native_steps','native_rule')) if r.get('cluster')=='reflective_faculty.concern_decode_settlement']
def worker(rep):
 before=inputs()
 from substrate.world_adapter import WorldAdapter
 from substrate.boot_all import load_all_seeds
 from domains import code_reading
 frame=json.loads(FRAME.read_text()); agent=WorldAdapter(seeds=(),shadow_read=False,deep_ingest=False)
 t0,c0=time.perf_counter_ns(),time.process_time_ns(); boot=load_all_seeds(agent); boot_wall,boot_cpu=time.perf_counter_ns()-t0,time.process_time_ns()-c0
 calls=[]
 for fi,row in enumerate(frame['selected']):
  srcpath=SNAP/row['project']/'source'/row['file']; source=srcpath.read_text(encoding='utf-8')
  for ci,args in enumerate(row['input_cases']):
   rb={r['id'] for r in receipts(agent)}; ob={x['id'] for x in rows(agent,'Observation',())}; ax={x['id'] for x in rows(agent,'CapabilityAxis',())}
   t0,c0=time.perf_counter_ns(),time.process_time_ns(); pred=None; error=None
   try:
    value=code_reading.predict_output(agent,source,row['function'],args)
    if value is None or type(value) in (bool,int,float,str):pred={'type':type(value).__name__,'value':value}
    else:error='NonPrimitivePrediction'
   except BaseException as exc:error=type(exc).__name__
   wall,cpu=time.perf_counter_ns()-t0,time.process_time_ns()-c0
   obs=[x for x in rows(agent,'Observation',('status','covered_by','key')) if x['id'] not in ob]
   for x in obs:x['minted_axis_ids']=[nodeid(n) for n in agent.inner.neighbours(__import__('substrate_rs')._native.NodeID(x['id']),'minted')]
   calls.append({'function_index':fi,'case_index':ci,'project':row['project'],'file':row['file'],'function':row['function'],'module_sha256_expected':row['module_sha256'],'function_sha256_expected':row['function_sha256'],'module_sha256_observed':pathsha(srcpath),'args':args,'prediction':pred,'error_type':error,'abstained':error is not None,'wall_ns':wall,'cpu_ns':cpu,'receipt_delta':len({x['id'] for x in receipts(agent)}-rb),'new_observations':obs,'new_axis_count':len({x['id'] for x in rows(agent,'CapabilityAxis',())}-ax)})
 after=inputs()
 return {'replicate':rep,'pid':os.getpid(),'source_stable':before==after,'locked_inputs_before':before,'locked_inputs_after':after,'boot':{'loaded':boot.get('loaded'),'total':boot.get('total'),'failed':boot.get('failed',[]),'wall_ns':boot_wall,'cpu_ns':boot_cpu},'runtime':{'peak_rss_bytes':int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024),'python':sys.version,'platform':platform.platform()},'calls':calls}
def main():
 if sys.argv[1:]==['--lock']:print(json.dumps({'locked_inputs':inputs()},indent=2,sort_keys=True));return
 if sys.argv[1:]==['--worker']:print(json.dumps(worker(int(os.environ['OCEL0_INDEPENDENT_CODE_PANEL_V1_1_REP'])),sort_keys=True));return
 frozen=inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=frozen:raise SystemExit('missing or stale independent-project code source lock')
 from scripts.substrate_run_manifest import start_console_capture,finish_console_capture,capture_run_manifest
 run_id='independent-projects-code-panel-v1-1-20260928';started,capstate=datetime.now(timezone.utc).isoformat(),start_console_capture(run_id)
 env={**os.environ,'PYTHONPATH':f'{ROOT}:{ROOT / "runners/dsl/python"}','OZMA_SEED_PERSIST_DISABLED':'1'};runs=[]
 for rep in (0,1):
  proc=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker'],cwd=ROOT,env={**env,'OCEL0_INDEPENDENT_CODE_PANEL_V1_1_REP':str(rep)},text=True,capture_output=True,timeout=3600)
  try:r=json.loads(proc.stdout)
  except Exception:r={'replicate':rep,'worker_error':proc.stderr or proc.stdout}
  r.update({'worker_returncode':proc.returncode,'worker_stderr':proc.stderr});runs.append(r);print(f'completed=worker{rep} rc={proc.returncode}',file=sys.stderr,flush=True)
 post=inputs(); expected=sum(len(r['input_cases']) for r in json.loads(FRAME.read_text())['selected'])
 checks={'parent_lock_stable':post==frozen,'two_fresh_workers':len(runs)==2 and len({r.get('pid') for r in runs})==2,'worker_source_stability':all(r.get('source_stable') and r.get('locked_inputs_before')==frozen==r.get('locked_inputs_after') for r in runs),'complete_schedules':all(len(r.get('calls',[]))==expected for r in runs),'workers_succeeded':all(r.get('worker_returncode')==0 and r.get('boot',{}).get('loaded',0)>0 for r in runs)}
 console=finish_console_capture(capstate);source_files=sorted({p for vals in frozen['source_trees'].values() for p in vals})
 manifest=capture_run_manifest(run_id=run_id,runner='scripts/substrate_independent_projects_code_panel_v1_1.py',protocol_files=[PROTOCOL.relative_to(ROOT).as_posix(),SNAPSHOTTER.relative_to(ROOT).as_posix(),SELECTOR.relative_to(ROOT).as_posix(),FRAME.relative_to(ROOT).as_posix()],source_files=source_files+[LOCK.relative_to(ROOT).as_posix()],data_files=[FRAME.relative_to(ROOT).as_posix()],analysis_files=[ANALYZER.relative_to(ROOT).as_posix()],started_utc=started,exit_status=0 if all(checks.values()) else 1,stdout_stderr_capture=console,child_processes=[{'replicate':r.get('replicate'),'pid':r.get('pid'),'returncode':r.get('worker_returncode'),'stderr':r.get('worker_stderr'),'structured_stdout_embedded_in_raw':True} for r in runs])
 report={'schema':'independent-projects-code-panel-raw-v1.1','run_id':run_id,'locked_inputs':frozen,'post_run_inputs':post,'integrity_checks':checks,'integrity_pass':all(checks.values()),'run_manifest':manifest,'runs':runs,'claim_boundary':'Hash-sampled licensed independent Python projects, per-project representative functions in a fixed safe AST fragment; not broad repository accuracy.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'report':OUT.relative_to(ROOT).as_posix(),'integrity_checks':checks},indent=2))
 if not report['integrity_pass']:raise SystemExit('independent-project source integrity failed')
if __name__=='__main__':main()
