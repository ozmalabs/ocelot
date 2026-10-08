#!/usr/bin/env python3
"""Capture active rule static access metadata for the five-route locality panel."""
from __future__ import annotations
import hashlib,importlib.util,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'scripts')]
HARVEST=ROOT/'evaluation/substrate_capability/live_conversation_task_graph_harvest_v2.py'
FRAME_LOCK=ROOT/'evaluation/substrate_capability/multiroute_frame_access_v1_20261006_lock.json'
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_MULTIROUTE_STATIC_DEPENDENCY_METADATA_V1_PREREG_20261006.md'
RUNNER=Path(__file__).resolve();LOCK=ROOT/'evaluation/substrate_capability/multiroute_static_dependency_metadata_v1_20261006_lock.json'
OUT=ROOT/'evaluation/reports/multiroute_frame_access_v1_20261006/static_rule_metadata.json'
ROUTES=['scene_description','held_self_knowledge_answer','self_report_action','unknown_word_clarification','concern_authoring']
def sha(p):return 'sha256:'+hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load():
 s=importlib.util.spec_from_file_location('harvest_static_metadata',HARVEST);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def inputs():
 from substrate_rs import _native
 h=load();return {'protocol_sha256':sha(PROTOCOL),'runner_sha256':sha(RUNNER),'harvest_runner_sha256':sha(HARVEST),'harvest_inputs':h.inputs(),'frame_lock_sha256':sha(FRAME_LOCK),'native_extension_sha256':sha(Path(_native.__file__).resolve()),'routes':ROUTES}
def worker(route):
 h=load();from substrate.world_adapter import WorldAdapter
 original=WorldAdapter.converse;captured=[]
 def wrap(self,*args,**kwargs):
  try:return original(self,*args,**kwargs)
  finally:
   rows=[]
   for row in self.inner.rule_access_sets():
    slot=int(row[0]);m=self.inner.rule_metadata(slot);uid=int(m['rule_uid'])
    rows.append({'rule_uid':uid,'rule_index':slot,'rule_name':str(row[1]),'active':bool(row[2]),'reads':list(row[3]),'term_edge_reads':list(row[4]),'writes':list(row[5]),'reads_any':bool(row[6]),'writes_any':bool(row[7])})
   captured.append(rows)
 WorldAdapter.converse=wrap
 try:r=h.worker(route,0)
 finally:WorldAdapter.converse=original
 if len(captured)!=1:raise RuntimeError(f'expected one converse metadata table; got {len(captured)}')
 return {'condition':route,'replicate':0,'locked_inputs':r['locked_inputs'],'post_run_inputs':r['post_run_inputs'],'source_stable':r['source_stable'],'rule_access_table':captured[0]}
def main():
 if sys.argv[1:]==['--lock']:
  LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps({'schema':'MultiRouteStaticDependencyMetadataV1Lock','locked_inputs':inputs()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return
 locked=inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing/stale metadata source lock')
 if OUT.exists():raise SystemExit(f'refusing overwrite: {OUT}')
 OUT.parent.mkdir(parents=True,exist_ok=True);env=os.environ.copy();env.setdefault('OZMA_NO_LLM','1');env.setdefault('OZMA_SEED_PERSIST_DISABLED','1');env['PYTHONPATH']=os.pathsep.join([str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'scripts'),env.get('PYTHONPATH','')])
 runs=[]
 for route in ROUTES:
  e=env.copy();e['OCEL0_TASK_CONDITION']=route;e['OCEL0_TASK_REP']='0';p=subprocess.run([sys.executable,str(RUNNER),'--worker',route],cwd=ROOT,env=e,text=True,capture_output=True,check=True,timeout=300);runs.append(json.loads(p.stdout));print(f'metadata={route}',file=sys.stderr,flush=True)
 post=inputs();payload={'schema':'MultiRouteStaticDependencyMetadataV1','locked_inputs':locked,'post_run_inputs':post,'runs':runs};OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
 ok=locked==post and all(r['source_stable'] and r['locked_inputs']==r['post_run_inputs'] for r in runs)
 print(json.dumps({'output':str(OUT.relative_to(ROOT)),'routes':len(runs),'source_stable':ok,'rule_rows':sum(len(r['rule_access_table']) for r in runs)},indent=2))
 if not ok:raise SystemExit('metadata capture integrity failed')
if __name__=='__main__':
 if len(sys.argv)==3 and sys.argv[1]=='--worker':print(json.dumps(worker(sys.argv[2]),sort_keys=True,separators=(',',':')))
 else:main()
