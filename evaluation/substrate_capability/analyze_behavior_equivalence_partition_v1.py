#!/usr/bin/env python3
"""Independent partition parity, input digest, and H×P work audit."""
import hashlib,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'evaluation/substrate_capability'),str(ROOT/'runners/dsl/python')]
import behavior_equivalence_partition_v1 as runner
import primitive_semantic_equivalence_v1 as sem
from substrate_rs import _native
from domains.contract_query import partition_hypotheses_by_behavior
LOCK=ROOT/'evaluation/substrate_capability/behavior_equivalence_partition_v1_lock_20261003.json';RAW=ROOT/'evaluation/reports/behavior_equivalence_partition_v1_20261003.json';OUT=ROOT/'evaluation/reports/behavior_equivalence_partition_v1_analysis_20261003.json'
l=json.loads(LOCK.read_text());raw=json.loads(RAW.read_text());assert runner.source_map()==l['sources']==raw['sources'];assert raw['lock_sha256']==hashlib.sha256(LOCK.read_bytes()).hexdigest()
n=_native.Substrate();actual_ok=True;work_ok=True;scale_ok=True;cells=l['cells'];captured=raw['actual_panels'];actual_ok &= len(cells)==50 and len(captured)==50
actual_cost={d:[] for d in ('original','zero_aware')};actual_calls=[]
for cell,row in zip(cells,captured):
 actual_ok &= (cell['task'],cell['worker'],cell['domain'])==(row['task'],row['worker'],row['domain'])
 hyps=[{'id':h['id'],'term':h['term']} for h in cell['hypotheses']];probes=[dict(zip(('ax','ay','ex','ey'),x)) for x in cell['probes']]
 got=partition_hypotheses_by_behavior(lambda t,e:n.evaluate(t,e),hyps,probes)
 expected=[sorted(x) for x in sem.signatures(n,hyps,cell['probes'])]
 actual_ok &= got.get('ok') is True and row['partition']['class_ids']==[x['hypothesis_ids'] for x in got['classes']]
 actual_ok &= row['partition']['class_count']==len(expected)==got['class_count'] and got['probe_count']==len(probes) and row['partition']['probe_sha256']==got['probe_sha256']
 calls=len(hyps)*len(probes);work_ok &= row['evaluation_calls']==[calls]*l['repetitions'];actual_calls.append(calls);actual_cost[cell['domain']].append(row['median_ns'])
scale_rows=raw['scaling_curves'];expected_keys={(t,h,p) for t in runner.TASKS for h in l['H_sizes'] for p in l['P_sizes']};actual_keys={(x['task'],x['H'],x['P']) for x in scale_rows};scale_ok &= len(scale_rows)==len(expected_keys) and actual_keys==expected_keys
scale_summary=[]
for row in scale_rows:
 # Find the exact frozen task-specific source panel and reconstruct this matrix row.
 source=next(x for x in l['scale_inputs'] if x['task']==row['task'] and x['worker']==row['worker']);terms=source['hypotheses'];H=row['H'];P=row['P'];probe_rows=source['probes'][:P]
 hs=[{'id':f'scale{i:03d}','term':terms[i%len(terms)]['term']} for i in range(H)]
 got=partition_hypotheses_by_behavior(lambda t,e:n.evaluate(t,e),hs,[dict(zip(('ax','ay','ex','ey'),x)) for x in probe_rows])
 expected=[sorted(x) for x in sem.signatures(n,hs,probe_rows)]
 scale_ok &= row['partition']['class_ids']==[x['hypothesis_ids'] for x in got['classes']] and row['partition']['class_count']==len(expected)==got['class_count']
 scale_ok &= row['partition']['probe_sha256']==got['probe_sha256'] and row['evaluation_calls']==[H*P]*l['repetitions']
 scale_summary.append({'task':row['task'],'H':H,'P':P,'evaluations':H*P,'median_ns':row['median_ns'],'synthetic_repetition':row['synthetic_repetition'],'class_count':got['class_count']})
source_ok=runner.source_map()==raw['sources']==l['sources'] and raw['lock_sha256']==hashlib.sha256(LOCK.read_bytes()).hexdigest()
err=raw['typed_error_control'];error_ok=err['partition']['ok'] is True and err['partition']['class_count']==3 and err['class_ids']==[['bool'],['int'],['error']] and err['evaluation_calls']==[6]*l['repetitions']
checks={'50_actual_survivor_partitions_match_reference':bool(actual_ok),'exact_evaluator_work_is_H_times_P':bool(work_ok and scale_ok),'all_175_scaling_cells_replayed':bool(len(scale_rows)==175),'typed_bool_int_and_error_buckets_stay_distinct':bool(error_ok),'source_lock_and_capture_binding':bool(source_ok)}
actual_summary={d:{'cells':len(actual_cost[d]),'median_partition_ns':statistics.median(actual_cost[d]),'median_evaluator_calls':statistics.median([x for x,c in zip(actual_calls,cells) if c['domain']==d])} for d in actual_cost}
by_hp={}
for row in scale_summary:
 key=(row['H'],row['P']);by_hp.setdefault(key,[]).append(row['median_ns'])
scaling=[{'H':h,'P':p,'expected_evaluations':h*p,'median_ns_across_tasks':statistics.median(by_hp[(h,p)])} for h in l['H_sizes'] for p in l['P_sizes']]
analysis={'schema':'BehaviorEquivalencePartitionV1Analysis','checks':checks,'passed':sum(checks.values()),'total':len(checks),'actual_panel_cost':actual_summary,'scaling':scaling,'interpretation':'Grouping performs exactly H×P candidate evaluations on these finite scalar Terms. Returned classes depend on supplied probes; the API is a finite partition, not a general semantic-equivalence oracle.','limits':['candidate Terms inherited from five authored numeric tasks','five repetitions on one host','larger H arms repeat existing Terms when distinct candidates are unavailable','timings exclude probe-domain discovery, oracle labels, and synthesis']}
OUT.write_text(json.dumps(analysis,indent=2,sort_keys=True)+'\n');print(json.dumps(analysis,indent=2,sort_keys=True))
if not all(checks.values()):raise SystemExit(1)
