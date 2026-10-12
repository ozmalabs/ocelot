#!/usr/bin/env python3
"""Verify source provenance and summarize no-op route failure instrumentation."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CAP=ROOT/'evaluation/reports/conversation_route_failure_diagnostics_v1_20261004.json'
LOCK=ROOT/'evaluation/substrate_capability/conversation_route_failure_diagnostics_v1_lock_20261004.json'
OUT=ROOT/'evaluation/reports/conversation_route_failure_diagnostics_v1_analysis_20261004.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 x=json.loads(CAP.read_text());lk=json.loads(LOCK.read_text())['locked_inputs'];checks={}
 checks['runner_hash_current']=sha(ROOT/'evaluation/substrate_capability/conversation_route_failure_diagnostics_v1.py')==lk['runner_sha256']==x['locked_inputs']['runner_sha256']
 checks['analyzer_hash_current']=sha(__file__)==lk['analyzer_sha256']==x['locked_inputs']['analyzer_sha256']
 checks['protocol_hash_current']=sha(ROOT/'docs/research/engine_substrate/SUBSTRATE_CONVERSATION_ROUTE_FAILURE_DIAGNOSTICS_V1_PREREG_20261004.md')==lk['protocol_sha256']==x['locked_inputs']['protocol_sha256']
 checks['two_source_stable_workers']=len(x['runs'])==2 and len({r['pid'] for r in x['runs']})==2 and all(r['locked_inputs']==lk==r['post_run_inputs'] for r in x['runs'])
 checks['capture_gates_pass']=x['passed'] and all(x['checks'].values())
 summaries=[]
 for r in x['runs']:
  turns=[]
  for t in r['turns']:
   calls=[z for z in t['trace'] if z['function']=='_ensure_describe'];describe=[z for z in t['trace'] if z['function']=='_act_describe_scene'];ask=[z for z in t['trace'] if z['function']=='ask_back'];act=[z for z in t['trace'] if z['function']=='act_on_instruction']
   turns.append({'condition':t['condition'],'message_fields':t['message_fields'],'interpretation_fields':t['interpretation_fields'],'reply':t['reply'],'ensure_describe_calls':[{'built':z.get('built'),'rule_count_delta':z.get('rule_count_after',0)-z.get('rule_count_before',0)} for z in calls],'describe_results':[z.get('summary') for z in describe],'act_results':[z.get('summary') for z in act],'ask_back_results':[z.get('summary') for z in ask]})
  summaries.append({'replicate':r['replicate'],'graph_summary':r['graph_summary'],'turns':turns})
 scene=[t for r in summaries for t in r['turns'] if t['condition']=='scene_description'];concern=[t for r in summaries for t in r['turns'] if t['condition']=='concern_authoring']
 scene_states=[]
 for t in scene:
  desc=t['describe_results'];ensure=t['ensure_describe_calls'];scene_states.append('not_attempted' if not ensure else 'faculty_unavailable' if not ensure[0]['built'] else 'describe_no_reply_then_fallback' if desc and not next((d or {}).get('reply') for d in desc) else 'describe_reply_returned')
 concern_states=[t['interpretation_fields'] for t in concern]
 out={'schema':'ConversationRouteFailureDiagnosticsV1Analysis','capture_sha256':sha(CAP),'analyzer_sha256':sha(__file__),'checks':checks,'passed':all(checks.values()),'runs':summaries,'diagnostic_summary':{'scene_route_states':scene_states,'concern_interpretation_states':concern_states},'claim_boundary':'Instrumentation identifies observed call order and returned values in two workers on one prompt sequence. It does not establish task intent validity or route prevalence.'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':out['passed'],'checks':checks,'diagnostic_summary':out['diagnostic_summary']},indent=2))
 if not out['passed']:raise SystemExit('analysis failed')
if __name__=='__main__':main()
