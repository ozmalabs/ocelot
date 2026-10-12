#!/usr/bin/env python3
"""Exploratory, source-locked diff of the three live-task graph outcomes."""
from __future__ import annotations
import hashlib,importlib.util,json,os,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
WORKER=ROOT/'scripts/substrate_parallel_rule_audit_context_v1_3_worker.py'
OUT=ROOT/'evaluation/reports/substrate_live_task_graph_variance_v1_20260927.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load_worker():
 spec=importlib.util.spec_from_file_location('parallel_audit_worker',WORKER)
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),default=str)
def diff_graphs(graphs):
 base=graphs[0];bn={int(n['id']):n for n in base['nodes']};be={(int(e['src']),str(e['type']),int(e['tgt'])):e for e in base['edges']};out=[]
 for index,g in enumerate(graphs[1:],1):
  gn={int(n['id']):n for n in g['nodes']};ge={(int(e['src']),str(e['type']),int(e['tgt'])):e for e in g['edges']}
  node_ids=sorted(set(bn)|set(gn));changed=[]
  for nid in node_ids:
   a=bn.get(nid);b=gn.get(nid)
   if canonical(a)!=canonical(b):changed.append({'id':nid,'baseline':a,'replicate':b})
  edge_keys=sorted(set(be)|set(ge));edges=[{'key':list(k),'baseline':be.get(k),'replicate':ge.get(k)} for k in edge_keys if canonical(be.get(k))!=canonical(ge.get(k))]
  out.append({'baseline_replicate':0,'replicate':index,'node_count_delta':len(gn)-len(bn),'edge_count_delta':len(ge)-len(be),'changed_node_records':changed,'changed_edge_records':edges})
 return out
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
 env={**os.environ,'OZMA_NO_LLM':'1','OZMA_SEED_PERSIST_DISABLED':'1'};runs=[];graphs=[];paths=[]
 with tempfile.TemporaryDirectory(prefix='ocelot-live-graph-diff-') as td:
  for rep in range(3):
   path=str(Path(td)/f'graph-{rep}.json');proc=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',str(rep),path],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
   item=json.loads(proc.stdout);runs.append(item['result']);paths.append(path);graphs.append(json.loads(Path(path).read_text()))
  finished=mod.lock_inputs()
 digests=[hashlib.sha256(canonical(g).encode()).hexdigest() for g in graphs]
 payload={'schema_version':1,'run_id':'substrate-live-task-graph-variance-v1-20260927','worker_source_sha256':worker_sha,'diagnostic_runner_sha256':driver_sha,'worker_inputs_stable':started==finished and sha(__file__)==driver_sha and sha(WORKER)==worker_sha and all(r['worker_started_inputs']==started==r['worker_finished_inputs'] for r in runs),'locked_worker_inputs':started,'post_worker_inputs':finished,'replicates':[{'replicate':r['replicate'],'pid':r['pid'],'whole_graph_semantic_sha256':r['whole_graph_semantic_sha256'],'graph_node_count':len(g['nodes']),'graph_edge_count':len(g['edges']),'b_message_ids':r['final']['b'][0]['message_ids'],'b_origin_ids':r['final']['b'][0]['origin_ids'],'request_candidate_tests':{k:int(v['global'].get('cand_tested',0)) for k,v in r['request_cost'].items()},'replies':r['replies']} for r,g in zip(runs,graphs)],'raw_graph_hashes':digests,'structural_diffs_from_replicate_0':diff_graphs(graphs),'claim_boundary':'Exploratory forensic diagnostic, not an independent confirmatory cost capture. It reuses the exact v1.3 worker and captures final graph records solely to localize the already observed source-locked graph/work variation.'}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT),'worker_inputs_stable':payload['worker_inputs_stable'],'graph_sizes':[(len(g['nodes']),len(g['edges'])) for g in graphs],'diffs':payload['structural_diffs_from_replicate_0']},indent=2))
 if not payload['worker_inputs_stable']:raise SystemExit('diagnostic source fingerprints changed')
if __name__=='__main__':main()
