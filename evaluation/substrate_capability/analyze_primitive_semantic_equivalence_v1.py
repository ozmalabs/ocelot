#!/usr/bin/env python3
"""Independent query/class replay and zero-inclusive holdout audit."""
import hashlib,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'evaluation/substrate_capability'))
import primitive_semantic_equivalence_v1 as r
from substrate_rs import _native
from domains.contract_query import select_discriminating_input
LOCK=ROOT/'evaluation/substrate_capability/primitive_semantic_equivalence_v1_lock_20261003.json';RAW=ROOT/'evaluation/reports/primitive_semantic_equivalence_v1_20261003.json';OUT=ROOT/'evaluation/reports/primitive_semantic_equivalence_v1_analysis_20261003.json'
l=json.loads(LOCK.read_text());raw=json.loads(RAW.read_text());assert r.source_map()==l['sources']==raw['sources'];assert raw['lock_sha256']==hashlib.sha256(LOCK.read_bytes()).hexdigest();expected=r.panels();coverage=len(expected)==25 and l['panels']==expected and len(raw['workers'])==25
up=json.loads(r.UPRAW.read_text());upworkers={(w['task'],w['worker']):w for w in up['workers']};n=_native.Substrate();schedule=True;transcript=True;classes_ok=True;scores=True;help_ok=True;legacy=True
summary={t:{d:{'panels':0,'abstentions':0,'labels':[],'survivors':0,'exact_survivors':0,'all_survivors_exact':0,'behavior_classes':[],'help_calls':0,'help_exact_panels':0} for d in ('original','zero_aware')} for t in r.TASKS}
for worker,panel in zip(raw['workers'],expected):
 schedule &= (worker['task'],worker['worker'],worker['training'])==(panel['task'],panel['worker'],panel['training'])
 hyps=panel['initial_hypotheses'];ids=[h['id'] for h in hyps];schedule &= worker['initial_hypothesis_ids']==ids
 for domain in ('original','zero_aware'):
  run=worker[domain];sel=panel['original_selection_order'] if domain=='original' else panel['zero_selection_order'];chall=panel['original_challenge_order'] if domain=='original' else panel['zero_challenge_order'];allprobe=(panel['original_selection_pool']+panel['original_challenge_order']) if domain=='original' else (panel['zero_selection_pool']+panel['zero_challenge_pool'])
  if domain=='zero_aware':
   train={tuple(x['row']) for x in panel['training']};sset={tuple(x) for x in panel['zero_selection_pool']};cset={tuple(x) for x in panel['zero_challenge_pool']}
   schedule &= len(sset)==32 and len(cset)==32 and not (sset&cset) and not (sset&train) and not (cset&train) and (0.,0.,0.,0.) not in sset|cset
   schedule &= all(x in sset for x in ((0.,1.,1.,1.),(1.,1.,0.,1.),(0.,-1.,1.,-1.),(-1.,1.,0.,1.)))
   holdout={x for x in __import__('itertools').product(r.HELDOUT,repeat=4) if x!=(0.,0.,0.,0.)}
   schedule &= not (holdout & (sset|cset|train))
  surv=list(hyps);obs=[];used=[];challenge_count=0;stop='empty' if not surv else '';abstained=False
  for step in run['steps']:
   q=step['input_env'];row=step['row'];transcript &= tuple(float(q[k]) for k in r.KEYS)==tuple(row) and step['before']==len(surv) and step['label']==bool(r.truth(worker['task'],row))
   if step['phase']=='selection':
    available=[r.env(x) for x in sel if x not in used];choice=select_discriminating_input(lambda term,e:n.evaluate(term,e),surv,available,obs)
    transcript &= choice.get('ok') is True and choice.get('query')==q and step['predictions']==choice.get('predictions',[])
   elif step['phase']=='challenge':
    expected_row=next((x for x in chall if x not in used),None);transcript &= expected_row==row;challenge_count+=1
   else:transcript=False
   kept=[]
   for h in surv:
    try:v=n.evaluate(h['term'],q)
    except Exception:continue
    if type(v)is bool and v==step['label']:kept.append(h)
   surv=kept;used.append(row);obs.append({'inputs':q,'expected':step['label']});transcript &= step['after']==len(surv)
   if not surv:stop='empty';break
  if not surv:stop='empty'
  elif len(surv)==1 and challenge_count>=r.CHALLENGE:stop='singleton_after_challenge'
  elif len(run['steps'])>=r.BUDGET:
   stop='singleton_after_challenge' if len(surv)==1 and challenge_count>=r.CHALLENGE else 'label_budget'
  else:
   available=[r.env(x) for x in sel if x not in used]
   if not available:stop='query_pool_exhausted'
   else:
    final_choice=select_discriminating_input(lambda term,e:n.evaluate(term,e),surv,available,obs)
    if not final_choice.get('ok'):stop='selector_abstention';abstained=True
    elif len(surv)==1:stop='candidate_singleton'
    else:stop='label_budget'
  transcript &= run['stop']==stop and run['calls']==len(run['steps']) and run['calls']<=r.BUDGET
  classes=r.signatures(n,surv,allprobe);classes_ok &= run['equivalence_classes']==classes
  scored=[{'id':h['id'],'family':h['family'],'term':h['term'],'heldout':r.score(n,worker['task'],h['term'])} for h in surv]
  scores &= run['scored_survivors']==scored and all(x['heldout']['n']==6560 for x in scored)
  help_needed=stop in ('empty','selector_abstention','query_pool_exhausted','challenge_pool_exhausted','label_budget')
  help_ok &= bool(run['help'])==help_needed
  if help_needed:
   hr=run['help'];hint=r.HINT[worker['task']];help_ok &= hr['help_calls']==1 and hr['hinted_family']==hint and hr['candidate_count']==len(hr['hypotheses'])
   help_ok &= all(x['heldout']==r.score(n,worker['task'],x['term']) and x['heldout']['n']==6560 for x in hr['hypotheses'])
  else:help_ok &= run['help'] is None
  # The old-domain transcript must reproduce the v1.1 query-only entropy arm.
  if domain=='original':
   old=next(x for x in upworkers[(worker['task'],worker['worker'])]['policies'] if x['policy']=='entropy' and not x['assisted'])
   legacy &= [(x['phase'],x['row'],x['input_env'],x['label'],x['before'],x['after']) for x in run['steps']]==[(x['phase'],x['row'],x['input_env'],x['label'],x['before'],x['after']) for x in old['steps']]
  s=summary[worker['task']][domain];s['panels']+=1;s['abstentions']+=int(stop=='selector_abstention');s['labels'].append(run['calls']);s['survivors']+=len(surv);exact=sum(x['heldout']['exact'] for x in scored);s['exact_survivors']+=exact;s['all_survivors_exact']+=int(bool(scored) and exact==len(scored));s['behavior_classes'].append(len(classes));s['help_calls']+=int(bool(run['help']));s['help_exact_panels']+=int(bool(run['help']) and any(x['heldout']['exact'] for x in run['help']['hypotheses']))
for t in r.TASKS:
 for d,s in summary[t].items():s['median_labels']=statistics.median(s.pop('labels'));s['median_behavior_classes']=statistics.median(s.pop('behavior_classes'))
checks={'all_25_panels_and_disjoint_zero_aware_schedules':bool(coverage and schedule),'query_and_survivor_transitions_replay':bool(transcript),'finite_equivalence_partitions_replay':bool(classes_ok),'all_survivors_and_help_candidates_rescored':bool(scores),'teacher_help_matches_registered_trigger':bool(help_ok),'original_domain_reproduces_v1_1_transcript':bool(legacy),'source_lock_and_capture_binding':r.source_map()==raw['sources']==l['sources'] and raw['lock_sha256']==hashlib.sha256(LOCK.read_bytes()).hexdigest()}
analysis={'schema':'PrimitiveSemanticEquivalenceV1Analysis','checks':checks,'passed':sum(checks.values()),'total':len(checks),'by_task_and_domain':summary,'interpretation':'Zero-aware probes test a known finite alias class. Finite prediction-equivalence classes are reports about supplied probes, not universal equivalence certificates. Teacher hints are separate oracle calls.','limits':['five authored tasks, five fixed-seed panels each','candidate terms inherited from source-locked v1.1 captures','finite query and holdout domains; no universal semantic proof','teacher hint is harness supplied and task relevant','single host; query and help costs are not normalized']}
OUT.write_text(json.dumps(analysis,indent=2,sort_keys=True)+'\n');print(json.dumps(analysis,indent=2,sort_keys=True))
if not all(checks.values()):raise SystemExit(1)
