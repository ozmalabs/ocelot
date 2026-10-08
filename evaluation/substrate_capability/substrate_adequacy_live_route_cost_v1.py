#!/usr/bin/env python3
"""Source-locked timing and outcome panel for strict live code adoption."""
from __future__ import annotations
import hashlib,importlib.util,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; RUNNER=Path(__file__).resolve()
BASE_PATH=ROOT/'evaluation/substrate_capability/substrate_adequacy_stochastic_noise_v1.py'
SPEC=importlib.util.spec_from_file_location('adequacy_noise_base_live_cost',BASE_PATH); base=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(base)
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_ADEQUACY_LIVE_ROUTE_COST_V1_PREREG_20261002.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_substrate_adequacy_live_route_cost_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/substrate_adequacy_live_route_cost_v1_lock_20261002.json'
RAW=ROOT/'evaluation/reports/substrate_adequacy_live_route_cost_v1_raw_20261002.json'
TASKS=base.TASKS; COUNTS=base.COUNTS; CASES=['truthful_correct','truthful_wrong','trusted_false_label','conflicting_signed_labels']; REPEATS=3
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(BASE_PATH.parent)]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def active():
 import substrate_rs
 return {'native':sha(substrate_rs._native.__file__),'oracle':sha(base.ORACLE),'adequacy_tree':base.tree('domains',('.py',)),'rust_tree':base.tree('runners/dsl/src',('.rs',)),'substrate_tree':base.tree('substrate',('.py',))}
def frozen():
 if json.loads(base.LOCK.read_text())!=base.frozen(): raise RuntimeError('base noise panel lock is stale')
 return {'schema':'SubstrateAdequacyLiveRouteCostV1Lock','files':{str(p.relative_to(ROOT)):sha(p) for p in (RUNNER,BASE_PATH,base.ORACLE,base.LOCK,base.PROTOCOL,PROTOCOL,ANALYZER)},'base_lock':base.frozen(),'active':active(),'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'design':{'tasks':TASKS,'counts':COUNTS,'cases':CASES,'repeats':REPEATS}}
def shape_ids(sub): return sorted(str(n) for n in sub.nodes('ShapeSignature') if sub.node(n)['attrs'].get('kind')=='code_write_construction')
def worker(task,case,count,rep,lock):
 if frozen()!=lock: raise RuntimeError('source/base/native lock drift')
 from substrate.world_adapter import WorldAdapter
 from domains import code_reading as cdr, independent_adequacy as ia
 from domains.adequacy_probe_selection import select_disagreement_probe
 from domains.adequacy_provider_auth import sign_label,verify_signed_audit_evidence
 from independent_adequacy_noise_oracles_v1 import label as oracle
 t0=time.perf_counter_ns(); wa=WorldAdapter(shadow_read=False,deep_ingest=False,trusted_adequacy_provider_keys=base.KEYS,require_discriminating_code_example_probe=True); t_ready=time.perf_counter_ns()
 good_name='parity' if task=='parity' else 'exceeds'; bad_name='always_false'; good_source=base.GOOD[task]; bad_source=base.BAD[task]
 if case=='truthful_correct': src,name,chall_source,chall_name=good_source,good_name,bad_source,bad_name
 else: src,name,chall_source,chall_name=bad_source,bad_name,good_source,good_name
 sub,native,_=cdr._resolve(wa); cand_read=cdr.read_function(wa,src,name); challenger_read=cdr.read_function(wa,chall_source,chall_name); term=cand_read.get('term'); challenger=challenger_read.get('term')
 if term is None or challenger is None: raise RuntimeError('Term parse failed')
 candidate_id=ia.candidate_id_for_write_shape(src,name,cand_read['args'],term,None); seed=f'live-route-cost-v1:{task}:{case}:{count}:{rep}'; sources=[f'oracle:{task}:v1']
 selection_start=time.perf_counter_ns(); selection=select_disagreement_probe(candidate_id,term,[challenger],[],base.DOMAINS[task],lambda t,e:native.evaluate(t,e),seed=seed); selection_done=time.perf_counter_ns()
 context={'challenger_terms':[challenger],'acquisition_rows':[],'admissible_inputs':base.DOMAINS[task],'acquisition_source_ids':sources,'seed':seed,'selection':selection}
 request_start=time.perf_counter_ns(); request=ia.propose_audit_request(candidate_id,term,[],[selection['input']],acquisition_source_ids=sources,count=1,seed=selection['selection_id']); probe=request['probes'][0]; truth=oracle(task,probe['inputs'])
 if case=='trusted_false_label': values=[not truth]*count
 elif case=='conflicting_signed_labels': values=([truth]*((count+1)//2))+([not truth]*(count//2))
 else: values=[truth]*count
 labels=[]
 for i,provider in enumerate(base.PROVIDERS[:count]):
  raw={'source_id':provider,'label_id':f'{task}:{case}:{count}:{rep}:{i}','expected':values[i],'oracle_sha256':sha(base.ORACLE)}
  labels.append(sign_label(raw,request['request_id'],probe['probe_id'],probe['input_sha256'],base.KEYS[provider]))
 rows=[{'probe_id':probe['probe_id'],'inputs':probe['inputs'],'labels':labels}]; request_done=time.perf_counter_ns()
 receipt_start=time.perf_counter_ns(); receipt=ia.adjudicate_audit_receipt(request,candidate_id,term,rows,lambda t,e:native.evaluate(t,e),acquisition_source_ids=sources); receipt_done=time.perf_counter_ns()
 auth=verify_signed_audit_evidence(request,rows,receipt,base.KEYS); before=shape_ids(sub)
 converse_start=time.perf_counter_ns(); reply=wa.converse(src,code_example_evidence={'request':request,'audit_rows':rows,'receipt':receipt,'probe_selection_context':context}); converse_done=time.perf_counter_ns(); after=shape_ids(sub)
 heldout=[{'inputs':env,'prediction':native.evaluate(term,env),'expected':oracle(task,env)} for env in base.HELD[task]]; heldout_done=time.perf_counter_ns()
 return {'task':task,'case':case,'providers':count,'rep':rep,'pid':os.getpid(),'candidate_id':candidate_id,'candidate_term':term,'challenger_term':challenger,'source':src,'name':name,'selection':selection,'context':context,'request':request,'rows':rows,'labels_expected':values,'receipt':receipt,'auth':auth,'truth':truth,'shape_delta':len(set(after)-set(before)),'added_shapes':sorted(set(after)-set(before)),'heldout':heldout,'reply':reply,'timing_ns':{'adapter_construct':t_ready-t0,'probe_selection':selection_done-selection_start,'request_signing':request_done-request_start,'receipt_adjudication':receipt_done-receipt_start,'live_converse':converse_done-converse_start,'heldout_eval':heldout_done-converse_done,'pipeline_after_ready':converse_done-t_ready},'active_after':active()}
def main():
 lock=frozen()
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or RAW.exists(): raise SystemExit('refusing overwrite')
  LOCK.write_text(json.dumps(lock,indent=2,sort_keys=True)+'\n'); print(LOCK.relative_to(ROOT)); return
 if not LOCK.is_file() or json.loads(LOCK.read_text())!=lock: raise SystemExit('missing/stale lock')
 if RAW.exists(): raise SystemExit('capture exists; refusing overwrite')
 env=dict(os.environ,OZMA_NO_LLM='1',OZMA_SEED_PERSIST_DISABLED='1'); env['PYTHONPATH']=f'{ROOT}:{ROOT}/runners/dsl/python:{RUNNER.parent}:{BASE_PATH.parent}:'
 workers=[]
 for task in TASKS:
  for case in CASES:
   for count in COUNTS:
    if case=='conflicting_signed_labels' and count==1: continue
    for rep in range(1,REPEATS+1):
     start=time.perf_counter_ns(); p=subprocess.run([sys.executable,str(RUNNER),'--worker',task,case,str(count),str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=180); elapsed=time.perf_counter_ns()-start
     if p.returncode: raise RuntimeError(f'{task}/{case}/{count}/{rep}: {p.stderr[-3000:]}')
     row=json.loads(p.stdout.strip().splitlines()[-1]); row['process_wall_ns']=elapsed; row['active_after']=active(); workers.append(row); print(f"{task}/{case}/m{count}/{rep}: {row['receipt']['status']} Δshape={row['shape_delta']} converse={row['timing_ns']['live_converse']/1e6:.3f}ms",flush=True)
 post=frozen(); cap={'schema':'SubstrateAdequacyLiveRouteCostV1Capture','lock':lock,'post_lock':post,'source_stable':post==lock,'workers':workers,'host':platform.platform(),'python':sys.version}
 RAW.write_text(json.dumps(cap,indent=2,sort_keys=True)+'\n'); print(json.dumps({'workers':len(workers),'source_stable':cap['source_stable'],'raw':str(RAW.relative_to(ROOT))},indent=2))
if __name__=='__main__':
 if len(sys.argv)==6 and sys.argv[1]=='--worker': print(json.dumps(worker(sys.argv[2],sys.argv[3],int(sys.argv[4]),int(sys.argv[5]),json.loads(LOCK.read_text())),sort_keys=True))
 else: main()
