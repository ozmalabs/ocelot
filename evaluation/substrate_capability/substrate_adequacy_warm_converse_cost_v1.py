#!/usr/bin/env python3
"""Source-locked cold/warmed full-conversation cost panel."""
from __future__ import annotations
import hashlib,importlib.util,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'evaluation/substrate_capability')]
RUNNER=Path(__file__).resolve(); PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_ADEQUACY_WARM_CONVERSE_COST_V1_PREREG_20261002.md'; ANALYZER=ROOT/'evaluation/substrate_capability/analyze_substrate_adequacy_warm_converse_cost_v1.py'; LOCK=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_cost_v1_lock_20261002.json'; RAW=ROOT/'evaluation/reports/substrate_adequacy_warm_converse_cost_v1_raw_20261002.json'
BASE_RUNNER=ROOT/'evaluation/substrate_capability/substrate_independent_adequacy_codewrite_transfer_v1.py'; ORACLE=ROOT/'evaluation/substrate_capability/independent_codewrite_oracles.py'
SPEC=importlib.util.spec_from_file_location('codewrite_base',BASE_RUNNER); base=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(base)
TASKS=('parity','clamp','square'); CONDITIONS=('truthful_adoption','missing_evidence'); REPEATS=3; PROVIDER='audit:warmed-route-provider'; KEY=b'warmed-converse-provider-key-32-bytes'
SOURCES=('domains/code_reading.py','domains/code_write_growth.py','domains/independent_adequacy.py','domains/adequacy_provider_auth.py','domains/adequacy_probe_selection.py','domains/teach.py','substrate/world_adapter.py','substrate/boot_core.py','substrate/boot_all.py','substrate/seed_loader.py','runners/dsl/python/substrate_rs/__init__.py','runners/dsl/src/graph.rs','runners/dsl/src/py.rs')
FIXTURES={**base.FIXTURES,'square':{'name':'square','source':'def square(x):\n    return x * x\n','known':[{'inputs':{'x':0},'expected':0}],'domain':[{'x':x} for x in range(-5,6)],'heldout':[{'x':x} for x in range(-20,21)]}}
REQUESTS={**base.REQUESTS,'square':'Write a function that squares an integer.'}
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def tree_sha(root,suffix):
 rows=[(p.relative_to(ROOT).as_posix(),sha(p)) for p in (ROOT/root).rglob('*') if p.is_file() and p.suffix==suffix]; h=hashlib.sha256()
 for n,d in sorted(rows): h.update(n.encode()+b'\0'+d.encode()+b'\n')
 return h.hexdigest()
def active():
 import substrate_rs
 from domains.engine_provenance import rust_source_fingerprint
 return {'files':{p:sha(ROOT/p) for p in SOURCES},'native':sha(substrate_rs._native.__file__),'rust_fingerprint':rust_source_fingerprint(str(ROOT)),'oracle':sha(ORACLE),'domain_tree':tree_sha('domains','.py'),'substrate_tree':tree_sha('substrate','.py'),'rust_tree':tree_sha('runners/dsl/src','.rs')}
def frozen(): return {'schema':'SubstrateAdequacyWarmConverseCostV1Lock','files':{str(p.relative_to(ROOT)):sha(p) for p in (RUNNER,ANALYZER,PROTOCOL,BASE_RUNNER,ORACLE)},'active':active(),'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'design':{'tasks':list(TASKS),'conditions':list(CONDITIONS),'repeats':REPEATS,'fixtures':FIXTURES,'requests':REQUESTS,'provider':PROVIDER}}
def json_default(v):
 if isinstance(v,set): return sorted(v,key=repr)
 try:return int(v)
 except (TypeError,ValueError):pass
 raise TypeError(type(v).__name__)
def snapshot(sub):
 g=sub.graph_to_dict(); return {'nodes':sorted(g['nodes'],key=lambda x:x['id']),'edges':sorted(g['edges'],key=lambda x:(x['src'],x['type'],x['tgt'],json.dumps(x.get('attrs',{}),sort_keys=True))),'next_id':g['next_id']}
def shape_state(sub,ag): return {'shapes':sorted(str(n) for n in sub.nodes('ShapeSignature') if sub.node(n)['attrs'].get('kind')=='code_write_construction'),'epoch':sub.node(ag)['attrs'].get('write_codebook_epoch',0) or 0}
def worker(task,condition,rep,lock):
 if frozen()!=lock: raise RuntimeError('source lock drift')
 os.environ['OZMA_NO_LLM']='1'; os.environ['OZMA_SEED_PERSIST_DISABLED']='1'
 from substrate.world_adapter import WorldAdapter
 from domains import code_reading as cdr, independent_adequacy as ia
 from domains.adequacy_provider_auth import sign_label,verify_signed_audit_evidence
 from independent_codewrite_oracles import label as oracle_label
 fixture=FIXTURES[task]; request_text=REQUESTS[task]; adapter=WorldAdapter(shadow_read=False,deep_ingest=False,trusted_adequacy_provider_keys={PROVIDER:KEY},require_authenticated_code_examples=True)
 sub,native,ag=cdr._resolve(adapter); read=cdr.read_function(adapter,fixture['source'],fixture['name']); term=read['term']; args=list(read['args']); cid=ia.candidate_id_for_write_shape(fixture['source'],read['name'],args,term,None); source_ids=[f'acquisition:{task}:warmed-v1']
 warm_wall0=time.perf_counter_ns(); warm_cpu0=time.process_time_ns(); warm_reply=adapter.converse('hello'); warm_cpu=time.process_time_ns()-warm_cpu0; warm_wall=time.perf_counter_ns()-warm_wall0; warmed_graph=snapshot(sub)
 request=rows=receipt=auth=None
 if condition=='truthful_adoption':
  request=ia.propose_audit_request(cid,term,fixture['known'],fixture['domain'],acquisition_source_ids=source_ids,count=1,seed=f'warmed-route:{task}:{rep}'); probe=request['probes'][0]; expected=oracle_label(task,probe['inputs']); raw={'source_id':PROVIDER,'label_id':f'warm:{task}:{rep}','expected':expected,'oracle_sha256':sha(ORACLE)}; signed=sign_label(raw,request['request_id'],probe['probe_id'],probe['input_sha256'],KEY); rows=[{'probe_id':probe['probe_id'],'inputs':probe['inputs'],'labels':[signed]}]; receipt=ia.adjudicate_audit_receipt(request,cid,term,rows,lambda t,e:native.evaluate(t,e),acquisition_source_ids=source_ids); auth=verify_signed_audit_evidence(request,rows,receipt,{PROVIDER:KEY}); evidence={'request':request,'audit_rows':rows,'receipt':receipt}
 else: evidence=None
 pre_graph=snapshot(sub); before={'shapes':sorted(str(n) for n in sub.nodes('ShapeSignature') if sub.node(n)['attrs'].get('kind')=='code_write_construction'),'epoch':sub.node(ag)['attrs'].get('write_codebook_epoch',0) or 0}; t0=time.perf_counter_ns(); c0=time.process_time_ns(); reply=adapter.converse(fixture['source'],code_example_evidence=evidence); call_cpu=time.process_time_ns()-c0; call_wall=time.perf_counter_ns()-t0; after=shape_state(sub,ag); post_graph=snapshot(sub)
 held=[{'inputs':env,'prediction':native.evaluate(term,env),'expected':oracle_label(task,env)} for env in fixture['heldout']]
 return {'task':task,'condition':condition,'rep':rep,'pid':os.getpid(),'candidate_id':cid,'term':term,'request':request,'rows':rows,'receipt':receipt,'auth':auth,'warm_reply':str(warm_reply),'reply':str(reply),'warm_wall_ns':warm_wall,'warm_cpu_ns':warm_cpu,'warm_nodes':len(warmed_graph['nodes']),'warm_edges':len(warmed_graph['edges']),'pre_call_graph':pre_graph,'post_call_graph':post_graph,'state_before':before,'state_after':after,'shape_delta':len(set(after['shapes'])-set(before['shapes'])),'heldout':held,'timing_ns':{'target_wall':call_wall,'target_cpu':call_cpu},'active_after':active()}
def main():
 lock=frozen()
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or RAW.exists(): raise SystemExit('refusing overwrite')
  LOCK.write_text(json.dumps(lock,indent=2,sort_keys=True)+'\n'); print(LOCK.relative_to(ROOT)); return
 if not LOCK.is_file() or json.loads(LOCK.read_text())!=lock: raise SystemExit('missing/stale lock')
 if RAW.exists(): raise SystemExit('capture exists; refusing overwrite')
 env=dict(os.environ,OZMA_NO_LLM='1',OZMA_SEED_PERSIST_DISABLED='1'); env['PYTHONPATH']=str(ROOT)+':'+str(ROOT/'runners/dsl/python')+':'+str(ROOT/'evaluation/substrate_capability')
 workers=[]
 for task in TASKS:
  for condition in CONDITIONS:
   for rep in range(1,REPEATS+1):
    p=subprocess.run([sys.executable,str(RUNNER),'--worker',task,condition,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=180)
    if p.returncode: raise RuntimeError(p.stderr[-3000:])
    row=json.loads(p.stdout.strip().splitlines()[-1]); workers.append(row); print(f"{task}/{condition}/{rep}: shapes={row['shape_delta']} cold={row['warm_wall_ns']/1e6:.1f}ms target={row['timing_ns']['target_wall']/1e6:.1f}ms",flush=True)
 post=frozen(); cap={'schema':'SubstrateAdequacyWarmConverseCostV1Capture','lock':lock,'post_lock':post,'source_stable':post==lock,'workers':workers,'host':platform.platform(),'python':sys.version}; RAW.write_text(json.dumps(cap,indent=2,sort_keys=True,default=json_default)+'\n'); print(json.dumps({'workers':len(workers),'source_stable':cap['source_stable'],'raw':str(RAW.relative_to(ROOT))},indent=2))
if __name__=='__main__':
 if len(sys.argv)==5 and sys.argv[1]=='--worker': print(json.dumps(worker(sys.argv[2],sys.argv[3],int(sys.argv[4]),json.loads(LOCK.read_text())),sort_keys=True,default=json_default))
 else: main()
