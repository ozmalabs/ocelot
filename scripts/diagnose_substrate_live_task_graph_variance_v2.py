#!/usr/bin/env python3
"""Exploratory, source-locked diff of the three live-task graph outcomes."""
from __future__ import annotations
import hashlib,importlib.util,json,os,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
WORKER=ROOT/'scripts/substrate_parallel_rule_audit_context_v1_3_worker.py'
OUT=ROOT/'evaluation/reports/substrate_live_task_graph_variance_v2_20260927.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load_worker():
 spec=importlib.util.spec_from_file_location('parallel_audit_worker',WORKER)
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),default=str)
def diff_graph(base,g,base_index,index):
 bn={int(n['id']):n for n in base['nodes']};be={(int(e['src']),str(e['type']),int(e['tgt'])):e for e in base['edges']};gn={int(n['id']):n for n in g['nodes']};ge={(int(e['src']),str(e['type']),int(e['tgt'])):e for e in g['edges']}
 changed=[{'id':nid,'baseline':bn.get(nid),'replicate':gn.get(nid)} for nid in sorted(set(bn)|set(gn)) if canonical(bn.get(nid))!=canonical(gn.get(nid))]
 edges=[{'key':list(k),'baseline':be.get(k),'replicate':ge.get(k)} for k in sorted(set(be)|set(ge)) if canonical(be.get(k))!=canonical(ge.get(k))]
 return {'baseline_replicate':base_index,'replicate':index,'node_count_delta':len(gn)-len(bn),'edge_count_delta':len(ge)-len(be),'changed_node_records':changed,'changed_edge_records':edges}
def child(rep,path):
 mod=load_worker();original=mod.semantic_graph_digest
 def capture(graph):
  Path(path).write_text(json.dumps(graph,separators=(',',':'),sort_keys=True,default=str)+'\n')
  return original(graph)
 mod.semantic_graph_digest=capture
 result=mod.worker(rep,True)
 print(json.dumps({'result':result,'graph_path':path},sort_keys=True,default=str))
def main():
 if len(sys.argv)==4 and sys.argv[1]=='--worker':child(int(sys.argv[2]),sys.argv[3]);return
 mod=load_worker();started=mod.lock_inputs();driver_sha=sha(__file__);worker_sha=sha(WORKER)
 env={**os.environ,'OZMA_NO_LLM':'1','OZMA_SEED_PERSIST_DISABLED':'1'};runs=[];summaries=[];hashes=[];diffs=[]
 with tempfile.TemporaryDirectory(prefix='ocelot-live-graph-diff-v2-') as td:
  baseline=None
  for rep in range(6):
   path=str(Path(td)/f'graph-{rep}.json');proc=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',str(rep),path],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
   item=json.loads(proc.stdout);r=item['result'];g=json.loads(Path(path).read_text());runs.append(r)
   hashes.append(hashlib.sha256(canonical(g).encode()).hexdigest())
   summaries.append({'replicate':r['replicate'],'pid':r['pid'],'whole_graph_semantic_sha256':r['whole_graph_semantic_sha256'],'graph_node_count':len(g['nodes']),'graph_edge_count':len(g['edges']),'b_message_ids':r['final']['b'][0]['message_ids'],'b_origin_ids':r['final']['b'][0]['origin_ids'],'request_candidate_tests':{k:int(v['global'].get('cand_tested',0)) for k,v in r['request_cost'].items()},'replies':r['replies']})
   if baseline is None:baseline=g
   else:diffs.append(diff_graph(baseline,g,0,rep))
   del g
  finished=mod.lock_inputs()
 stable=started==finished and sha(__file__)==driver_sha and sha(WORKER)==worker_sha and all(r['worker_started_inputs']==started==r['worker_finished_inputs'] for r in runs)
 payload={'schema_version':1,'run_id':'substrate-live-task-graph-variance-v2-20260927','worker_source_sha256':worker_sha,'diagnostic_runner_sha256':driver_sha,'worker_inputs_stable':stable,'locked_worker_inputs':started,'post_worker_inputs':finished,'replicates':summaries,'raw_graph_hashes':hashes,'structural_diffs_from_replicate_0':diffs,'claim_boundary':'Exploratory forensic diagnostic, not an independent confirmatory cost capture. Reuses the v1.3 worker and captures final graph records solely to localize source-locked graph/work variation.'}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT),'worker_inputs_stable':stable,'graph_sizes':[(x['graph_node_count'],x['graph_edge_count']) for x in summaries],'b_message_ids':[x['b_message_ids'] for x in summaries],'candidate_tests':[x['request_candidate_tests'] for x in summaries],'changed_node_counts':[len(x['changed_node_records']) for x in diffs]},indent=2))
 if not payload['worker_inputs_stable']:raise SystemExit('diagnostic source fingerprints changed')
if __name__=='__main__':main()
