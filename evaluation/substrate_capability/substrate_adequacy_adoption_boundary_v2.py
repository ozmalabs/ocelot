#!/usr/bin/env python3
"""Cross-family source-locked full-graph audit at code adoption boundary."""
from __future__ import annotations
import hashlib, importlib.util, json, os, platform, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'evaluation/substrate_capability')]
RUNNER=Path(__file__).resolve(); PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_ADEQUACY_ADOPTION_BOUNDARY_V2_PREREG_20261002.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_substrate_adequacy_adoption_boundary_v2.py'
LOCK=ROOT/'evaluation/substrate_capability/substrate_adequacy_adoption_boundary_v2_lock_20261002.json'
RAW=ROOT/'evaluation/reports/substrate_adequacy_adoption_boundary_v2_raw_20261002.json'
ORACLE=ROOT/'evaluation/substrate_capability/independent_codewrite_oracles.py'
BASE_RUNNER=ROOT/'evaluation/substrate_capability/substrate_independent_adequacy_codewrite_transfer_v1.py'
SPEC=importlib.util.spec_from_file_location('codewrite_transfer_base',BASE_RUNNER); base=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(base)
TASKS=('parity','clamp','square'); REPEATS=3; PROVIDER='audit:cross-family-provider'; KEY=b'cross-family-adoption-boundary-key-32-bytes'
FIXTURES={**base.FIXTURES,'square':{'name':'square','source':'def square(x):\n    return x * x\n','known':[{'inputs':{'x':0},'expected':0}],'domain':[{'x':x} for x in range(-5,6)],'heldout':[{'x':x} for x in range(-20,21)]}}
ACTIVE=('domains/code_reading.py','domains/code_write_growth.py','domains/independent_adequacy.py','domains/adequacy_provider_auth.py','domains/teach.py','substrate/world_adapter.py','substrate/boot_core.py','runners/dsl/python/substrate_rs/__init__.py','runners/dsl/src/graph.rs','runners/dsl/src/py.rs')
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def json_default(value):
 if isinstance(value,set): return sorted(value,key=repr)
 try: return int(value)
 except (TypeError,ValueError): pass
 raise TypeError(f'not JSON serializable: {type(value).__name__}')
def active():
 import substrate_rs
 from domains.engine_provenance import rust_source_fingerprint
 return {'files':{p:sha(ROOT/p) for p in ACTIVE},'native':sha(substrate_rs._native.__file__),'rust_fingerprint':rust_source_fingerprint(str(ROOT)),'oracle':sha(ORACLE),'fixtures':sha(BASE_RUNNER)}
def frozen(): return {'schema':'SubstrateAdequacyAdoptionBoundaryV2Lock','files':{str(p.relative_to(ROOT)):sha(p) for p in (RUNNER,ANALYZER,PROTOCOL,ORACLE,BASE_RUNNER)},'active':active(),'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'design':{'tasks':list(TASKS),'repeats':REPEATS,'provider':PROVIDER,'fixtures':FIXTURES,'requests':base.REQUESTS}}
def snapshot(sub):
 g=sub.graph_to_dict()
 return {'nodes':sorted(g['nodes'],key=lambda x:x['id']),'edges':sorted(g['edges'],key=lambda x:(x['src'],x['type'],x['tgt'],json.dumps(x.get('attrs',{}),sort_keys=True))),'next_id':g['next_id']}
def shape_state(sub,agent_node,name):
 shapes=sorted((str(n),sub.node(n)['attrs']) for n in sub.nodes('ShapeSignature') if sub.node(n)['attrs'].get('kind')=='code_write_construction' and sub.node(n)['attrs'].get('name')==name)
 return {'shapes':shapes,'epoch':sub.node(agent_node)['attrs'].get('write_codebook_epoch',0) or 0}
def worker(task,rep,lock):
 if frozen()!=lock: raise RuntimeError('source lock drift before worker')
 os.environ['OZMA_SEED_PERSIST_DISABLED']='1'; os.environ['OZMA_NO_LLM']='1'
 from substrate.world_adapter import WorldAdapter
 from domains import code_reading as cdr, code_write_growth as cwg, independent_adequacy as ia
 from domains.adequacy_provider_auth import sign_label,teach_write_shape_from_example_authenticated
 from independent_codewrite_oracles import label as oracle_label
 fixture=FIXTURES[task]; request_text=base.REQUESTS[task]; adapter=WorldAdapter(shadow_read=False,deep_ingest=False,trusted_adequacy_provider_keys={PROVIDER:KEY},require_authenticated_code_examples=True)
 sub,native,agent_node=cdr._resolve(adapter); reading=cdr.read_function(adapter,fixture['source'],fixture['name']); term=reading['term']; args=list(reading['args'])
 candidate=ia.candidate_id_for_write_shape(fixture['source'],reading['name'],args,term,request_text); acquisition_id=f'acquisition:{task}:v1'; source_id=f'independent-codewrite-oracle-v1:{sha(ORACLE)}'
 request=ia.propose_audit_request(candidate,term,fixture['known'],fixture['domain'],acquisition_source_ids=[acquisition_id],count=1,seed=f'adoption-boundary-v2:{task}:{rep}'); probe=request['probes'][0]; truth=oracle_label(task,probe['inputs'])
 def evidence(value,label_tag):
  raw={'source_id':PROVIDER,'label_id':f'{task}:{rep}:{label_tag}','expected':value,'oracle_sha256':sha(ORACLE)}
  signed=sign_label(raw,request['request_id'],probe['probe_id'],probe['input_sha256'],KEY); rows=[{'probe_id':probe['probe_id'],'inputs':probe['inputs'],'labels':[signed]}]
  receipt=ia.adjudicate_audit_receipt(request,candidate,term,rows,lambda t,e:native.evaluate(t,e),acquisition_source_ids=[acquisition_id])
  return rows,receipt
 correct_rows,correct_receipt=evidence(truth,'truth'); false_value=(not truth) if isinstance(truth,bool) else truth+1; false_rows,false_receipt=evidence(false_value,'false')
 name='taught_'+fixture['name']; before_reject=shape_state(sub,agent_node,name); entered=[]; original=cwg._teach_shape
 def reject_spy(*a,**kw): entered.append(True); return original(*a,**kw)
 cwg._teach_shape=reject_spy
 try: rejected=teach_write_shape_from_example_authenticated(adapter,fixture['source'],request=request,audit_rows=false_rows,receipt=false_receipt,trusted_provider_keys={PROVIDER:KEY},request_text=request_text)
 finally: cwg._teach_shape=original
 after_reject=shape_state(sub,agent_node,name); boundary={}; original=cwg._teach_shape
 def capture_boundary(agent,**kw):
  boundary['before']=snapshot(sub); start=time.perf_counter_ns(); result=original(agent,**kw); boundary['elapsed_ns']=time.perf_counter_ns()-start; boundary['after']=snapshot(sub); return result
 cwg._teach_shape=capture_boundary
 try: accepted=teach_write_shape_from_example_authenticated(adapter,fixture['source'],request=request,audit_rows=correct_rows,receipt=correct_receipt,trusted_provider_keys={PROVIDER:KEY},request_text=request_text)
 finally: cwg._teach_shape=original
 heldout=[{'inputs':env,'prediction':native.evaluate(term,env),'expected':oracle_label(task,env)} for env in fixture['heldout']]
 return {'task':task,'rep':rep,'pid':os.getpid(),'candidate_id':candidate,'term':term,'request':request,'probe':probe,'truth':truth,'correct_rows':correct_rows,'correct_receipt':correct_receipt,'false_rows':false_rows,'false_receipt':false_receipt,'rejected':{'ok':rejected.get('ok'),'reason':rejected.get('reason')},'rejected_entered_adoption':bool(entered),'reject_before':before_reject,'reject_after':after_reject,'accepted':{'ok':accepted.get('ok'),'shape':str(accepted.get('shape')),'reason':accepted.get('reason')},'boundary':boundary,'accepted_shape_state':shape_state(sub,agent_node,name),'heldout':heldout,'active_after':active()}
def main():
 lock=frozen()
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or RAW.exists(): raise SystemExit('refusing overwrite')
  LOCK.write_text(json.dumps(lock,indent=2,sort_keys=True)+'\n'); print(LOCK.relative_to(ROOT)); return
 if not LOCK.is_file() or json.loads(LOCK.read_text())!=lock: raise SystemExit('missing/stale lock')
 if RAW.exists(): raise SystemExit('capture exists; refusing overwrite')
 env=dict(os.environ,OZMA_NO_LLM='1',OZMA_SEED_PERSIST_DISABLED='1'); env['PYTHONPATH']=str(ROOT)+':'+str(ROOT/'runners/dsl/python')+':'+str(ROOT/'evaluation/substrate_capability')
 rows=[]
 for task in TASKS:
  for rep in range(1,REPEATS+1):
   p=subprocess.run([sys.executable,str(RUNNER),'--worker',task,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=180)
   if p.returncode: raise RuntimeError(p.stderr[-3000:])
   row=json.loads(p.stdout.strip().splitlines()[-1]); rows.append(row); print(f"{task}/{rep}: reject={row['false_receipt']['status']} adopted={row['accepted']['ok']}",flush=True)
 post=frozen(); cap={'schema':'SubstrateAdequacyAdoptionBoundaryV2Capture','lock':lock,'post_lock':post,'source_stable':post==lock,'workers':rows,'host':platform.platform(),'python':sys.version}
 RAW.write_text(json.dumps(cap,indent=2,sort_keys=True,default=json_default)+'\n'); print(json.dumps({'workers':len(rows),'source_stable':cap['source_stable'],'raw':str(RAW.relative_to(ROOT))},indent=2))
if __name__=='__main__':
 if len(sys.argv)==4 and sys.argv[1]=='--worker': print(json.dumps(worker(sys.argv[2],int(sys.argv[3]),json.loads(LOCK.read_text())),sort_keys=True,default=json_default))
 else: main()
