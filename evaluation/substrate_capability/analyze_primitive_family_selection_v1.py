#!/usr/bin/env python3
"""Independent replay of family candidate pools, queries, and outcomes."""
import hashlib,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'evaluation/substrate_capability'))
import primitive_family_selection_v1 as r
from substrate_rs import _native
from domains.contract_query import select_discriminating_input
LOCK=ROOT/'evaluation/substrate_capability/primitive_family_selection_v1_lock_20261003.json';RAW=ROOT/'evaluation/reports/primitive_family_selection_v1_20261003.json';OUT=ROOT/'evaluation/reports/primitive_family_selection_v1_analysis_20261003.json'
lock=json.loads(LOCK.read_text());raw=json.loads(RAW.read_text());assert r.source_map()==lock['sources']==raw['sources'];assert raw['lock_sha256']==hashlib.sha256(LOCK.read_bytes()).hexdigest()
prior=json.loads(r.PANEL_LOCK.read_text());expected=[p for p in prior['panels'] if p['task'] in r.TASKS];coverage=len(raw['workers'])==10 and [(w['task'],w['worker'],w['training'],w['selection_pool'],w['selection_order']) for w in raw['workers']]==[(p['task'],p['worker'],p['training'],p['selection_pool'],p['selection_order']) for p in expected]
n=_native.Substrate();score_ok=True;replay=True;settings=True;paired=True
summary={t:{pol:{'panels':0,'empty':0,'singleton':0,'exact_singleton':0,'false_singleton':0,'ambiguous':0,'calls':[],'family_correct_singleton':0} for pol in ('fixed_order','entropy')} for t in r.TASKS};synth={f:{'wall_s':[],'cpu_s':[],'candidates':0,'exact_panel':0} for f in r.FAMILIES}
for w,panel in zip(raw['workers'],expected):
 settings &= [(a['family'],tuple(a['ops'])) for a in w['families']]==[(f,r.OPS[f]) for f in r.FAMILIES]
 hyps=[]
 for arm in w['families']:
  f=arm['family'];synth[f]['wall_s'].append(arm['wall_ns']/1e9);synth[f]['cpu_s'].append(arm['cpu_ns']/1e9);synth[f]['candidates']+=len(arm['hypotheses']);exact=0
  for h in arm['hypotheses']:
   sc=r.score(n,w['task'],h['term']);score_ok &= sc==h['heldout'];exact+=int(sc['exact']);hyps.append({'id':h['id'],'family':f,'term':h['term']})
  synth[f]['exact_panel']+=int(exact>0)
 policies={x['policy']:x for x in w['policies']};paired &= set(policies)=={'fixed_order','entropy'}
 for kind,a in policies.items():
  s=summary[w['task']][kind];s['panels']+=1;survivors=list(hyps);observations=[];used=[]
  for step in a['steps']:
   q=step['input_env'];row=step['row'];replay &= tuple(float(q[k]) for k in r.KEYS)==tuple(row);label=bool(r.truth(w['task'],row));replay &= step['label']==label;replay &= step['before']==len(survivors)
   if kind=='fixed_order':
    nextrow=next((x for x in panel['selection_order'] if x not in used),None);replay &= nextrow==row
   else:
    available=[r.env(x) for x in panel['selection_order'] if x not in used]
    choice=select_discriminating_input(lambda t,e:n.evaluate(t,e),survivors,available,observations)
    replay &= choice.get('ok') is True and choice.get('query')==q
    if choice.get('ok'):replay &= step['predictions']==choice.get('predictions',[])
   used.append(row);kept=[]
   for h in survivors:
    try:v=n.evaluate(h['term'],q)
    except Exception:continue
    if type(v) is bool and v==label:kept.append(h)
   survivors=kept;observations.append({'inputs':q,'expected':label});replay &= step['after']==len(survivors)
  expected_final=[{'id':h['id'],'family':h['family'],'term':h['term'],'heldout':r.score(n,w['task'],h['term'])} for h in survivors]
  replay &= a['survivors']==expected_final and a['calls']==len(a['steps']) and a['calls']<=r.BUDGET
  s['calls'].append(a['calls']);s['empty']+=int(not survivors);s['singleton']+=int(len(survivors)==1);s['exact_singleton']+=int(len(survivors)==1 and expected_final[0]['heldout']['exact']);s['false_singleton']+=int(len(survivors)==1 and not expected_final[0]['heldout']['exact']);s['ambiguous']+=int(len(survivors)>1)
  s['family_correct_singleton']+=int(len(survivors)==1 and ((w['task']=='additive' and survivors[0]['family']=='Plus') or (w['task']=='product' and survivors[0]['family']=='Times')))
for f in r.FAMILIES:
 synth[f]['median_wall_s']=statistics.median(synth[f]['wall_s']);synth[f]['median_cpu_s']=statistics.median(synth[f]['cpu_s']);del synth[f]['wall_s'];del synth[f]['cpu_s']
for t in r.TASKS:
 for pol in summary[t]:summary[t][pol]['median_calls']=statistics.median(summary[t][pol]['calls'])
checks={'all_ten_locked_panels_replayed':bool(coverage),'family_grammar_and_search_settings':bool(settings),'entropy_and_fixed_query_transcripts_replay':bool(replay),'all_candidate_and_final_holdouts_rescored':bool(score_ok),'paired_policy_arms_present':bool(paired),'source_lock_and_capture_binding':r.source_map()==raw['sources']==lock['sources'] and raw['lock_sha256']==hashlib.sha256(LOCK.read_bytes()).hexdigest()}
analysis={'schema':'PrimitiveFamilySelectionV1Analysis','checks':checks,'passed':sum(checks.values()),'total':len(checks),'by_task_and_policy':summary,'synthesis_by_family':synth,'interpretation':'The measured policies select only among two supplied operator families using oracle labels; this is not open-ended primitive discovery or autonomous help-seeking.','limits':['two related numeric tasks and five panels each','operator menu is supplied','local harness supplies oracle labels','finite candidate pools and 1,296-point holdout','single host; query cost excludes external-oracle economics']}
OUT.write_text(json.dumps(analysis,indent=2,sort_keys=True)+'\n');print(json.dumps(analysis,indent=2,sort_keys=True))
if not all(checks.values()):raise SystemExit(1)
