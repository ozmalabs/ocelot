#!/usr/bin/env python3
"""Independent replay of locked primitive-menu queries, help, and holdouts."""
import hashlib,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'evaluation/substrate_capability'))
import primitive_menu_help_policy_v1 as r
from substrate_rs import _native
from domains.contract_query import select_discriminating_input
LOCK=ROOT/'evaluation/substrate_capability/primitive_menu_help_policy_v1_lock_20261003.json';RAW=ROOT/'evaluation/reports/primitive_menu_help_policy_v1_20261003.json';OUT=ROOT/'evaluation/reports/primitive_menu_help_policy_v1_analysis_20261003.json'
lock=json.loads(LOCK.read_text());raw=json.loads(RAW.read_text());assert r.source_map()==lock['sources']==raw['sources'];assert raw['lock_sha256']==hashlib.sha256(LOCK.read_bytes()).hexdigest();expected=r.panels();coverage=len(lock['panels'])==25 and len(raw['workers'])==25 and lock['panels']==expected
native=_native.Substrate();transcript=True;candidate_scores=True;settings=True;blind=True;help_valid=True
summary={t:{p:{'panels':0,'initial_candidates':0,'empty':0,'false_singleton':0,'exact_singleton':0,'ambiguous':0,'help_calls':0,'help_exact':0,'help_empty':0,'labels':[]} for p in ('fixed_order_query_only','fixed_order_help','entropy_query_only','entropy_help')} for t in r.TASKS};synthcost={t:[] for t in r.TASKS}
for w,panel in zip(raw['workers'],expected):
 settings &= [a['family'] for a in w['families']]==list(r.FAMILIES)
 settings &= w['training']==panel['training'] and w['selection_pool']==panel['selection_pool'] and w['selection_order']==panel['selection_order'] and w['challenge_order']==panel['challenge_order']
 hyps=[]
 for arm in w['families']:
  settings &= tuple(arm['ops'])==r.OPS[arm['family']]
  synthcost[w['task']].append(arm['wall_ns']/1e9)
  for h in arm['hypotheses']:
   candidate_scores &= r.score(native,w['task'],h['term'])==h['heldout'];hyps.append({'id':h['id'],'family':h['family'],'term':h['term']})
 for p in w['policies']:
  name=p['policy']+('_help' if p['assisted'] else '_query_only');s=summary[w['task']][name];s['panels']+=1;s['initial_candidates']+=len(hyps);survivors=list(hyps);obs=[];used=[];challenges=0;stop='candidate_singleton' if len(survivors)==1 else ('empty' if not survivors else '')
  for step in p['steps']:
   q=step['input_env'];row=step['row'];transcript &= set(q)==set(r.KEYS) and tuple(float(q[k]) for k in r.KEYS)==tuple(row);label=bool(r.truth(w['task'],row));transcript &= step['label']==label and step['before']==len(survivors)
   if step['phase']=='selection':
    available=[r.env(x) for x in panel['selection_order'] if x not in used]
    if p['policy']=='fixed_order':choice={'ok':bool(available),'query':available[0] if available else None}
    else:choice=select_discriminating_input(lambda term,e:native.evaluate(term,e),survivors,available,obs)
    transcript &= choice.get('ok') is True and choice.get('query')==q
    if p['policy']=='entropy' and choice.get('ok'):transcript &= step['predictions']==choice.get('predictions',[])
   elif step['phase']=='challenge':
    nextrow=next((x for x in panel['challenge_order'] if x not in used),None);transcript &= nextrow==row;challenges+=1
   else:transcript=False
   kept=[]
   for h in survivors:
    try:v=native.evaluate(h['term'],q)
    except Exception:continue
    if type(v) is bool and v==label:kept.append(h)
   survivors=kept;used.append(row);obs.append({'inputs':q,'expected':label});transcript &= step['after']==len(survivors)
   if not survivors:stop='empty';break
   if len(survivors)==1:stop='candidate_singleton'
  if not stop:stop='label_budget'
  if len(survivors)==1 and challenges>=r.POST_SINGLETON_CHALLENGE:stop='singleton_after_challenge'
  transcript &= p['stop']==stop and p['calls']==len(p['steps']) and p['calls']<=r.LABEL_BUDGET
  held=[{'id':h['id'],'family':h['family'],'term':h['term'],'heldout':r.score(native,w['task'],h['term'])} for h in survivors]
  for h in p['survivors']:candidate_scores &= h in held
  candidate_scores &= p['survivors']==held
  trigger=stop in ('empty','selector_abstention','query_pool_exhausted','label_budget','challenge_pool_exhausted')
  expected_help=bool(p['assisted'] and trigger)
  help_valid &= bool(p['help'])==expected_help
  if expected_help:
   hinted=r.HINT[w['task']];help_valid &= p['help']['calls']==1 and p['help']['trigger']==stop and p['help']['hinted_family']==hinted and p['helped_result'] is not None
   hh=p['helped_result'];help_valid &= hh['family']==hinted and hh['candidate_count']==len(hh['hypotheses'])
   help_valid &= hh['candidate_count']>0
   for h in hh['hypotheses']:candidate_scores &= r.score(native,w['task'],h['term'])==h['heldout']
  else:help_valid &= p['help'] is None and p['helped_result'] is None
  s['labels'].append(p['calls']);s['help_calls']+=int(bool(p['help']));s['empty']+=int(not survivors);s['false_singleton']+=int(len(held)==1 and not held[0]['heldout']['exact']);s['exact_singleton']+=int(len(held)==1 and held[0]['heldout']['exact']);s['ambiguous']+=int(len(held)>1)
  if p['helped_result']:
   exact=sum(1 for h in p['helped_result']['hypotheses'] if h['heldout']['exact']);s['help_exact']+=int(exact>0);s['help_empty']+=int(exact==0)
  blind &= not any('task' in step or 'heldout' in step for step in p['steps'])
for t in r.TASKS:
 for p,s in summary[t].items():s['median_labels']=statistics.median(s['labels']) if s['labels'] else 0
 synthsummary={t:{'median_family_synthesis_s':statistics.median(synthcost[t]),'family_arm_count':len(synthcost[t])} for t in r.TASKS}
checks={'all_25_locked_panels_replayed':bool(coverage),'candidate_grammars_and_panel_settings':bool(settings),'query_transcripts_and_candidate_transitions_replay':bool(transcript),'all_candidate_and_survivor_holdouts_rescored':bool(candidate_scores),'help_only_on_registered_unresolved_signals':bool(help_valid),'policy_inputs_exclude_task_identity_and_holdouts':bool(blind),'source_lock_and_capture_binding':r.source_map()==raw['sources']==lock['sources'] and raw['lock_sha256']==hashlib.sha256(LOCK.read_bytes()).hexdigest()}
analysis={'schema':'PrimitiveMenuHelpPolicyV1Analysis','checks':checks,'passed':sum(checks.values()),'total':len(checks),'by_task_and_policy':summary,'synthesis_by_task':synthsummary,'interpretation':'The explicit teacher hint is an oracle-assisted upper bound; query/help tradeoffs are reported in separate units. This measures bounded recovery over the registered menu and tasks, not autonomous primitive invention.','limits':['five authored numeric task families and five sampled panels each','operator menu is fixed to Base, Plus, Times, and Lt','the harness teacher provides task-relevant help hints only when requested','heldout exactness is a finite grid and is hidden from the policy','one host; help-call and label costs are not economically normalized']}
OUT.write_text(json.dumps(analysis,indent=2,sort_keys=True)+'\n');print(json.dumps(analysis,indent=2,sort_keys=True))
if not all(checks.values()):raise SystemExit(1)
