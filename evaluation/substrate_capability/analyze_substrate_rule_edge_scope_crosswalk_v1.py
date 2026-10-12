#!/usr/bin/env python3
"""Reconcile captured discourse rule traces with typed cross-frame event edges."""
from __future__ import annotations
import collections,hashlib,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
TRACE=ROOT/'evaluation/reports/substrate_connected_conversation_access_trace_panel_v1_3_20261003.json'
TRACE_ANALYSIS=ROOT/'evaluation/reports/substrate_connected_conversation_access_trace_panel_v1_3_1_analysis_20261003.json'
TRACE_LOCK=ROOT/'evaluation/substrate_capability/substrate_connected_conversation_access_trace_panel_v1_3_lock_20261003.json'
TYPED=ROOT/'evaluation/reports/substrate_typed_frame_interaction_census_v1_20261003.json'
TYPED_ANALYSIS=ROOT/'evaluation/reports/substrate_typed_frame_interaction_census_v1_analysis_20261003.json'
SEEDS=[ROOT/'seeds/conversation_discourse_state.json',ROOT/'seeds/communication_intent_arbitration.json',ROOT/'seeds/communication_reported_content_recall.json']
TRACE_RUNNER=ROOT/'evaluation/substrate_capability/substrate_connected_conversation_access_trace_panel_v1_3.py'
OUT=ROOT/'evaluation/reports/substrate_rule_edge_scope_crosswalk_v1_analysis_20261003.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 trace=json.loads(TRACE.read_text());ta=json.loads(TRACE_ANALYSIS.read_text());typed=json.loads(TYPED.read_text());tpa=json.loads(TYPED_ANALYSIS.read_text());lock=json.loads(TRACE_LOCK.read_text());errs=[]
 if not ta.get('gates_pass') or ta.get('errors'):errs.append('source trace analysis did not pass')
 if not tpa.get('gates_pass') or tpa.get('errors'):errs.append('typed interaction analysis did not pass')
 if trace.get('source_lock_sha256')!=sha(TRACE_LOCK):errs.append('trace capture does not bind to trace lock')
 cases=[c for run in trace.get('runs',[]) for c in run.get('cases',[])];direct=collections.Counter();resources=collections.Counter();kinds=collections.Counter();rule_names=set();static_sets=[];edge_types=collections.Counter()
 for case in cases:
  t=case['trace_on'];static={r['name']:r for r in t.get('static_rule_access',[])};static_sets.append(static)
  for name in static:rule_names.add(name)
  for e in t.get('direct_cross_frame_edges',[]):direct[e['type']]+=1
  for cp in t.get('checkpoints',[]):
   for e in cp.get('runtime_access_trace_events',[]):
    resources[e.get('resource')]+=int(e.get('count',1));kinds[e['kind']]+=int(e.get('count',1))
    if 'edge' in e['kind']:edge_types[e.get('resource')]+=int(e.get('count',1))
 # Extract source rule patterns without using captures or labels to select the rule.
 predecessor_rules=[]
 for path in SEEDS:
  data=json.loads(path.read_text())
  for rule in data.get('rules',[]):
   if not isinstance(rule,dict):continue
   matched=[x for x in rule.get('match',[]) if isinstance(x,list) and len(x)==3 and x[1]=='follows_event']
   if matched:predecessor_rules.append({'seed':path.relative_to(ROOT).as_posix(),'name':rule.get('name'),'follows_event_match':matched,
    'match_edge_count':len(rule.get('match',[])),'index_hints':rule.get('index_hints',[]),
    'scope_anchor_var':rule.get('scope_anchor_var'),'scope_anchor_type':rule.get('scope_anchor_type')})
 rel=ta['summary'].get('access_counts_by_owner_relation',{})
 active_reads={rec['name']:sorted(x.split(':',1)[1] for x in rec.get('reads',[]) if x.startswith('edge:')) for rec in (static_sets[0].values() if static_sets else [])}
 missing_from_trace=[r for r in predecessor_rules if r['name'] not in rule_names]
 # One control: panel boot source names exactly one seed, so missing dynamic rules are panel coverage gaps.
 source=TRACE_RUNNER.read_text();loads_discourse_only="load_seeds_into(a.s,a.agent,['conversation_discourse_state'])" in source
 if static_sets and any(s!=static_sets[0] for s in static_sets[1:]):errs.append('static rule access sets differ across cases')
 if len(cases)!=12:errs.append(f'expected 12 trace cases, got {len(cases)}')
 if direct['follows_event']!=90 or sum(direct.values())!=90:errs.append('trace panel cross-frame edge count differs from locked expectation')
 if resources['follows_event']!=0:errs.append('selected trace unexpectedly records follows_event')
 if len(rule_names)!=4 or any(not n.startswith('discourse_goal_') for n in rule_names):errs.append('selected runtime rule set differs from four discourse lifecycle rules')
 if 'follows_event' in {e for vals in active_reads.values() for e in vals}:errs.append('selected lifecycle rules statically claim follows_event')
 if set(rel)!={'same_frame','one_endpoint_shared_or_unowned'} or rel.get('same_frame')!=720 or rel.get('one_endpoint_shared_or_unowned')!=5520:errs.append('runtime access owner-relation summary mismatch')
 if not loads_discourse_only:errs.append('trace runner seed-loading scope changed; review audit interpretation')
 inputs=[Path(__file__),TRACE,TRACE_ANALYSIS,TRACE_LOCK,TYPED,TYPED_ANALYSIS,*SEEDS,TRACE_RUNNER]
 report={'schema':'SubstrateRuleEdgeScopeCrosswalkV1Analysis','generated_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'gates_pass':not errs,'errors':errs,
  'input_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in inputs},'summary':{'trace_cases':len(cases),'captured_cross_frame_edges_by_type':dict(direct),
  'runtime_access_multiplicity_by_edge_resource':dict(sorted(edge_types.items())),'runtime_follows_event_access_multiplicity':resources['follows_event'],
  'observed_access_owner_relation':rel,'selected_runtime_rule_names':sorted(rule_names),'selected_rule_edge_reads':active_reads,
  'seed_rules_that_match_follows_event':predecessor_rules,'predecessor_rules_absent_from_dynamic_panel':[x['name'] for x in missing_from_trace],
  'trace_runner_loads_only_discourse_state_seed':loads_discourse_only,
  'typed_census_cross_frame_relation_counts':tpa['summary']['disjoint_frame_relation_counts']}}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'analysis':OUT.relative_to(ROOT).as_posix(),'gates_pass':not errs,'errors':errs,'summary':report['summary']},sort_keys=True));return 0 if not errs else 1
if __name__=='__main__':raise SystemExit(main())
