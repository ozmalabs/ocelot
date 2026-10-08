#!/usr/bin/env python3
"""Source-locked full-graph audit at the authenticated adoption boundary."""
from __future__ import annotations
import hashlib, importlib.util, json, os, platform, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'evaluation/substrate_capability')]
RUNNER=Path(__file__).resolve()
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_ADEQUACY_ADOPTION_BOUNDARY_V1_PREREG_20261002.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_substrate_adequacy_adoption_boundary_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/substrate_adequacy_adoption_boundary_v1_lock_20261002.json'
RAW=ROOT/'evaluation/reports/substrate_adequacy_adoption_boundary_v1_raw_20261002.json'
BASE=ROOT/'evaluation/substrate_capability/substrate_adequacy_stochastic_noise_v1.py'
SPEC=importlib.util.spec_from_file_location('adequacy_base',BASE); base=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(base)
SOURCE='def square(x):\n    return x * x\n'; REQUEST_TEXT='square x'; PROVIDER='audit:test-provider'; KEY=b'adoption-boundary-test-key-v1-32-bytes-minimum'; REPEATS=3
ACTIVE=('domains/code_reading.py','domains/code_write_growth.py','domains/independent_adequacy.py','domains/adequacy_provider_auth.py','domains/teach.py','substrate/world_adapter.py','substrate/boot_core.py','runners/dsl/python/substrate_rs/__init__.py','runners/dsl/src/graph.rs','runners/dsl/src/py.rs')
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def json_default(value):
 if isinstance(value,set): return sorted(value,key=repr)
 try: return int(value)
 except (TypeError,ValueError): pass
 raise TypeError(f'not JSON serializable: {type(value).__name__}')
def hashes():
 import substrate_rs
 from domains.engine_provenance import rust_source_fingerprint
 return {'files':{p:sha(ROOT/p) for p in ACTIVE},'native':sha(substrate_rs._native.__file__),'rust_fingerprint':rust_source_fingerprint(str(ROOT))}
def frozen():
 return {'schema':'SubstrateAdequacyAdoptionBoundaryV1Lock','files':{str(p.relative_to(ROOT)):sha(p) for p in (RUNNER,ANALYZER,PROTOCOL,BASE,base.ORACLE)},'active':hashes(),'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'design':{'repeats':REPEATS,'source':SOURCE,'request_text':REQUEST_TEXT,'provider':PROVIDER}}
def snapshot(sub):
 g=sub.graph_to_dict()
 return {'nodes':sorted(g['nodes'],key=lambda x:x['id']),'edges':sorted(g['edges'],key=lambda x:(x['src'],x['type'],x['tgt'],json.dumps(x.get('attrs',{}),sort_keys=True))),'next_id':g['next_id']}
def shape_state(sub,agent_node):
 return {'shapes':sorted((str(n),sub.node(n)['attrs']) for n in sub.nodes('ShapeSignature') if sub.node(n)['attrs'].get('kind')=='code_write_construction'),'epoch':sub.node(agent_node)['attrs'].get('write_codebook_epoch',0) or 0}
def worker(rep,lock):
 if frozen()!=lock: raise RuntimeError('source lock drift before worker')
 os.environ['OZMA_SEED_PERSIST_DISABLED']='1'; os.environ['OZMA_NO_LLM']='1'
 from substrate.world_adapter import WorldAdapter
 from domains import code_reading as cdr, code_write_growth as cwg, independent_adequacy as ia
 from domains.adequacy_provider_auth import sign_label, teach_write_shape_from_example_authenticated
 adapter=WorldAdapter(shadow_read=False,deep_ingest=False,trusted_adequacy_provider_keys={PROVIDER:KEY},require_authenticated_code_examples=True)
 sub,native,agent_node=cdr._resolve(adapter); read=cdr.read_function(adapter,SOURCE,'square'); term=read['term']; args=list(read['args'])
 candidate=ia.candidate_id_for_write_shape(SOURCE,'square',args,term,REQUEST_TEXT)
 acquisition=[{'inputs':{'x':0},'expected':0}]; source_ids=['acquisition:square:v1']
 request=ia.propose_audit_request(candidate,term,acquisition,[{'x':1},{'x':2},{'x':3}],acquisition_source_ids=source_ids,count=1,seed=f'adoption-boundary:{rep}')
 probe=request['probes'][0]
 def make_receipt(label):
  raw={'source_id':PROVIDER,'label_id':f'{rep}:{label}','expected':label,'oracle_sha256':sha(base.ORACLE)}
  signed=sign_label(raw,request['request_id'],probe['probe_id'],probe['input_sha256'],KEY)
  rows=[{'probe_id':probe['probe_id'],'inputs':probe['inputs'],'labels':[signed]}]
  receipt=ia.adjudicate_audit_receipt(request,candidate,term,rows,lambda t,e:native.evaluate(t,e),acquisition_source_ids=source_ids)
  return rows,receipt
 correct=native.evaluate(term,probe['inputs']); bad=(correct+1 if isinstance(correct,(int,float)) else 'false')
 bad_rows,bad_receipt=make_receipt(bad); bad_before=shape_state(sub,agent_node); entered=[]
 original=cwg._teach_shape
 def capture(*args,**kwargs): entered.append(True); return original(*args,**kwargs)
 cwg._teach_shape=capture
 try: rejected=teach_write_shape_from_example_authenticated(adapter,SOURCE,request=request,audit_rows=bad_rows,receipt=bad_receipt,trusted_provider_keys={PROVIDER:KEY},request_text=REQUEST_TEXT)
 finally: cwg._teach_shape=original
 bad_after=shape_state(sub,agent_node)
 good_rows,good_receipt=make_receipt(correct); boundary={}; original=cwg._teach_shape
 def capture_boundary(agent,**kwargs):
  boundary['before']=snapshot(sub); t0=time.perf_counter_ns(); result=original(agent,**kwargs); boundary['elapsed_ns']=time.perf_counter_ns()-t0; boundary['after']=snapshot(sub); return result
 cwg._teach_shape=capture_boundary
 try: accepted=teach_write_shape_from_example_authenticated(adapter,SOURCE,request=request,audit_rows=good_rows,receipt=good_receipt,trusted_provider_keys={PROVIDER:KEY},request_text=REQUEST_TEXT)
 finally: cwg._teach_shape=original
 rejected_summary={'ok':rejected.get('ok'),'reason':rejected.get('reason')}
 accepted_summary={'ok':accepted.get('ok'),'reason':accepted.get('reason'),'shape':str(accepted.get('shape'))}
 return {'pid':os.getpid(),'rep':rep,'candidate_id':candidate,'request':request,'probe':probe,'good_rows':good_rows,'good_receipt':good_receipt,'bad_rows':bad_rows,'bad_receipt':bad_receipt,'rejected':rejected_summary,'rejected_entered_adoption':bool(entered),'rejected_before':bad_before,'rejected_after':bad_after,'accepted':accepted_summary,'adoption_boundary':boundary,'accepted_shape_state':shape_state(sub,agent_node),'active_after':hashes()}
def main():
 lock=frozen()
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or RAW.exists(): raise SystemExit('refusing overwrite')
  LOCK.write_text(json.dumps(lock,indent=2,sort_keys=True)+'\n'); print(LOCK.relative_to(ROOT)); return
 if not LOCK.exists() or json.loads(LOCK.read_text())!=lock: raise SystemExit('missing/stale lock')
 if RAW.exists(): raise SystemExit('capture exists; refusing overwrite')
 env=dict(os.environ,OZMA_NO_LLM='1',OZMA_SEED_PERSIST_DISABLED='1'); env['PYTHONPATH']=str(ROOT)+':'+str(ROOT/'runners/dsl/python')+':'+str(ROOT/'evaluation/substrate_capability')
 rows=[]
 for rep in range(1,REPEATS+1):
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=180)
  if p.returncode: raise RuntimeError(p.stderr[-3000:])
  row=json.loads(p.stdout.strip().splitlines()[-1]); rows.append(row); print(f"rep {rep}: rejected={row['bad_receipt']['status']} entered={row['rejected_entered_adoption']} accepted={row['accepted'].get('ok')}",flush=True)
 post=frozen(); cap={'schema':'SubstrateAdequacyAdoptionBoundaryV1Capture','lock':lock,'post_lock':post,'source_stable':post==lock,'workers':rows,'host':platform.platform(),'python':sys.version}
 RAW.write_text(json.dumps(cap,indent=2,sort_keys=True)+'\n'); print(json.dumps({'workers':len(rows),'source_stable':cap['source_stable'],'raw':str(RAW.relative_to(ROOT))},indent=2))
if __name__=='__main__':
 if len(sys.argv)==3 and sys.argv[1]=='--worker':
  if not LOCK.exists(): raise SystemExit('lock required')
  print(json.dumps(worker(int(sys.argv[2]),json.loads(LOCK.read_text())),sort_keys=True,default=json_default))
 else: main()
