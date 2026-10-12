#!/usr/bin/env python3
"""Independent replay and exact holdout audit of challenge-query adequacy."""
import json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/numeric_relation_model_adequacy_audit_v1_lock_20261003.json'
RAW=ROOT/'evaluation/reports/numeric_relation_model_adequacy_audit_v1_20261003.json'
OUT=ROOT/'evaluation/reports/numeric_relation_model_adequacy_audit_v1_analysis_20261003.json'
sys.path.insert(0,str(ROOT/'evaluation/substrate_capability'))
import numeric_relation_model_adequacy_audit_v1 as runner
from substrate_rs import _native
from domains.contract_query import select_discriminating_input
lock=json.loads(LOCK.read_text());raw=json.loads(RAW.read_text());workers=raw['workers']
assert runner.source_map()==lock['sources']==raw['sources']
assert raw['lock_sha256']==runner.sha(LOCK)
native=_native.Substrate();coverage=True;candidate_scores=True;transition=True;paired=True;positive=True
summary={task:{'panels':0,'base_false_singletons':0,'audit_empty':0,'audit_false_singletons':0,
 'audit_exact_singletons':0,'audit_ambiguous':0,'challenge_calls':0,'entropy_calls':0,
 'median_synthesis_ms':0.0} for task in runner.TASKS}
synth_by_task={t:[] for t in runner.TASKS};arm_rows=[]
for w in workers:
 task=w['task'];worker=w['worker'];summary[task]['panels']+=1;synth_by_task[task].append(w['synthesis_ns']/1e6)
 panel=next(p for p in lock['panels'] if p['task']==task and p['worker']==worker)
 coverage &= (w['training']==panel['training'] and w['selection_pool']==panel['selection_pool']
  and w['selection_order']==panel['selection_order'] and w['challenge_pool']==panel['challenge_pool']
  and w['challenge_order']==panel['challenge_order'])
 hypotheses={h['id']:h['term'] for h in w['hypotheses']}
 for hid,term in hypotheses.items():
  sc=runner.score(native,task,term)
  recorded=next(h['heldout'] for h in w['hypotheses'] if h['id']==hid)
  candidate_scores &= sc==recorded
 if task=='opposition':
  positive &= len(w['exact_initial_ids'])>0
 exact_ids=set(w['exact_initial_ids'])
 arms={a['policy']:a for a in w['arms']}
 paired &= set(arms)=={'entropy_stop','challenge_until_six'}
 base=arms['entropy_stop'];audit=arms['challenge_until_six']
 used_active=[];used_audit=[];entropy_obs=[];survivors=dict(hypotheses);saw_challenge=False
 for step in audit['steps']:
  query=step['input_env'];row=step['row']
  transition &= isinstance(query,dict) and set(query)==set(runner.KEYS)
  transition &= tuple(float(query[k]) for k in runner.KEYS)==tuple(row)
  actual=bool(runner.truth(task,row));transition &= step['label']==actual
  before=len(survivors);transition &= step['before']==before
  if step['phase']=='entropy':
   transition &= not saw_challenge
   available=[runner.env(r) for r in panel['selection_order'] if r not in used_active]
   choice=select_discriminating_input(lambda term,e:native.evaluate(term,e),
    [{'id':hid,'term':term} for hid,term in survivors.items()],available,entropy_obs)
   transition &= choice.get('ok') is True and choice.get('query')==query
   if choice.get('ok'):
    expected_preds=choice.get('predictions',[])
    transition &= step['predictions']==expected_preds
   used_active.append(row);entropy_obs.append({'inputs':query,'expected':actual})
  else:
   saw_challenge=True
   expected_row=next((r for r in panel['challenge_order'] if r not in used_audit),None)
   transition &= expected_row==row
   used_audit.append(row)
   expected_preds=[]
   for hid,term in survivors.items():
    try:expected_preds.append({'hypothesis':hid,'output':native.evaluate(term,query)})
    except Exception:expected_preds.append({'hypothesis':hid,'output':None,'evaluation_error':True})
   transition &= step['predictions']==expected_preds
  kept={}
  for hid,term in survivors.items():
   try:value=native.evaluate(term,query)
   except Exception:continue
   if type(value) is bool and value==actual:kept[hid]=term
  survivors=kept
  transition &= step['after']==len(survivors)
 transition &= audit['entropy_calls']==sum(s['phase']=='entropy' for s in audit['steps'])
 transition &= audit['challenge_calls']==sum(s['phase']=='challenge' for s in audit['steps'])
 transition &= audit['challenge_calls']<=runner.AUDIT_BUDGET and len(audit['steps'])<=runner.ENTROPY_BUDGET
 transition &= audit['survivors']==[{'id':hid,'term':term,'heldout':runner.score(native,task,term)} for hid,term in survivors.items()]
 # The stop policy and challenge policy must have the same entropy-stage transcript.
 b_entropy=[s for s in base['steps'] if s['phase']=='entropy']
 a_entropy=[s for s in audit['steps'] if s['phase']=='entropy']
 paired &= b_entropy==a_entropy
 base_false=len(base['survivors'])==1 and not base['survivors'][0]['heldout']['exact']
 audit_empty=not audit['survivors']
 audit_false=len(audit['survivors'])==1 and not audit['survivors'][0]['heldout']['exact']
 audit_exact=len(audit['survivors'])==1 and audit['survivors'][0]['heldout']['exact']
 audit_ambiguous=len(audit['survivors'])>1
 summary[task]['base_false_singletons']+=int(base_false)
 summary[task]['audit_empty']+=int(audit_empty)
 summary[task]['audit_false_singletons']+=int(audit_false)
 summary[task]['audit_exact_singletons']+=int(audit_exact)
 summary[task]['audit_ambiguous']+=int(audit_ambiguous)
 summary[task]['challenge_calls']+=audit['challenge_calls']
 summary[task]['entropy_calls']+=audit['entropy_calls']
 if task=='opposition':
  positive &= bool(exact_ids & set(survivors))
  positive &= not audit_empty
 arm_rows.append({'task':task,'worker':worker,'base_false_singleton':base_false,
  'audit_empty':audit_empty,'audit_false_singleton':audit_false,'audit_exact_singleton':audit_exact,
  'base_calls':base['entropy_calls'],'audit_entropy_calls':audit['entropy_calls'],
  'challenge_calls':audit['challenge_calls']})
for task in runner.TASKS:summary[task]['median_synthesis_ms']=statistics.median(synth_by_task[task])
checks={'all_15_panels_and_locked_input_pools':len(workers)==15 and all(v['panels']==5 for v in summary.values()) and bool(coverage),
 'active_and_challenge_transcripts_replay':bool(transition),
 'paired_entropy_phase_identical':bool(paired),
 'all_candidate_and_final_holdouts_rescored':bool(candidate_scores),
 'in_grammar_exact_target_survives_audit':bool(positive),
 'source_lock_and_capture_binding':runner.source_map()==raw['sources']==lock['sources'] and raw['lock_sha256']==runner.sha(LOCK)}
analysis={'schema':'NumericRelationModelAdequacyAuditV1Analysis','checks':checks,'passed':sum(checks.values()),'total':len(checks),
 'by_task':summary,'paired_outcomes':arm_rows,
 'interpretation':'A finite challenge batch can reject some false singleton models; surviving a finite audit is not a general adequacy guarantee.',
 'limits':['three authored numeric relations; five repeated panels per relation','challenge labels come from a local harness oracle',
  'the additive and product targets are outside the bounded grammar; opposition is a positive control',
  'six audit labels do not prove adequacy or generalization outside the held-out domain']}
OUT.write_text(json.dumps(analysis,indent=2,sort_keys=True)+'\n')
print(json.dumps(analysis,indent=2,sort_keys=True))
if not all(checks.values()):raise SystemExit(1)
