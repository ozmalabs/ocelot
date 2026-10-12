#!/usr/bin/env python3
"""Common candidate and isolated-branch adapters for four Thoughtexperiment families."""
from __future__ import annotations
import copy,hashlib,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
import sys
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'evaluation/substrate_capability')]
FAMILIES=('shape_axis','recurrence','navigation','control_kind')

def digest(candidate:dict)->str:
 bundle={}
 for name,rule in sorted((candidate.get('rules') or {}).items()):
  row=copy.deepcopy(rule)
  if isinstance(row,dict):row.pop('name',None)
  bundle[name]=row
 return 'sha256:'+hashlib.sha256(json.dumps(bundle,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

def prepare(family:str,worker:int,split:str)->dict:
 import domains.self_correction as correction
 original_generator=correction._default_candidates;generation=[]
 def measured_generator(*args,**kwargs):
  started=time.perf_counter_ns();result=original_generator(*args,**kwargs)
  generation.append(time.perf_counter_ns()-started);return result
 correction._default_candidates=measured_generator
 setup_started=time.perf_counter_ns()
 try:
  return _prepare_unmeasured(family,worker,split,setup_started,generation)
 finally:
  correction._default_candidates=original_generator

def _prepare_unmeasured(family:str,worker:int,split:str,setup_started:int,generation:list[int])->dict:
 if family=='shape_axis':
  import thoughtexperiment_shape_axis_full_candidate_admission_v1 as task
  sub,agent,native,model,candidates,timing=task.build_context(worker,split)
  setup_ns=time.perf_counter_ns()-setup_started;enum_ns=sum(generation)
  return {'family':family,'worker':worker,'split':split,'sub':sub,'agent':agent,'native':native,
   'target':'sd_mint_quantum','candidates':candidates,'rule_overrides':{},'task_module':task,
   'training_context_ns':max(0,setup_ns-enum_ns),'enumeration_ns':enum_ns}
 if family=='recurrence':
  import thoughtexperiment_recurrence_candidate_admission_v1 as task
  sub,native,episode,keys,candidates=task.build_base(worker,split)
  rows=native.export_rules();fault=next(r for r in rows if r.get('name')==task.TARGET and r.get('active',True))
  setup_ns=time.perf_counter_ns()-setup_started;enum_ns=sum(generation)
  return {'family':family,'worker':worker,'split':split,'sub':sub,'native':native,'episode':episode,
   'keys':keys,'target':task.TARGET,'candidates':candidates,'rule_overrides':{task.TARGET:fault},
   'task_module':task,'training_context_ns':max(0,setup_ns-enum_ns),'enumeration_ns':enum_ns}
 if family=='control_kind':
  import thoughtexperiment_control_kind_classification_repair_v1 as task
  sub,root,native,source,fault,candidates=task.rule_setup(None)
  setup_ns=time.perf_counter_ns()-setup_started;enum_ns=sum(generation)
  return {'family':family,'worker':worker,'split':split,'sub':sub,'root':root,'native':native,
   'target':task.TARGET,'candidates':[c for c in candidates if c.get('rules',{}).get(task.TARGET) is not None],
   'rule_overrides':{task.TARGET:fault},'task_module':task,'training_context_ns':max(0,setup_ns-enum_ns),'enumeration_ns':enum_ns}
 if family=='navigation':
  import thoughtexperiment_navigation_polarity_repair_v1_1 as task
  from domains.self_correction import _default_candidates
  sub,agent,_rf=task.build_agent();native=agent.inner
  idx,original=task.active_rule(native);fault=task.faulted_rule(original)
  if not native.remove_rule(idx):raise RuntimeError('could not remove navigation target')
  native.add_rule(fault)
  candidates=_default_candidates(native,task.TASK_RULE);enum_ns=sum(generation)
  candidates=[c for c in candidates if c.get('rules',{}).get(task.TASK_RULE) is not None]
  setup_ns=time.perf_counter_ns()-setup_started
  return {'family':family,'worker':worker,'split':split,'sub':sub,'agent':agent,'native':native,
   'target':task.TASK_RULE,'candidates':candidates,'rule_overrides':{task.TASK_RULE:fault},
   'task_module':task,'training_context_ns':max(0,setup_ns-enum_ns),'enumeration_ns':enum_ns}
 raise ValueError(f'unknown task family {family}')

def _replace(native,candidate:dict)->list[str]:
 replace=getattr(native,'replace_active_rule_by_name',None)
 if replace is None:raise RuntimeError('native active-rule patch unavailable')
 applied=[]
 for target,variant in sorted((candidate.get('rules') or {}).items()):
  if replace(target,variant):applied.append(target)
 return applied

def _receipt(native,candidate:dict,applied:list[str])->bool:
 expected=candidate.get('rules') or {};active=native.export_rules();good=bool(expected) and set(applied)==set(expected)
 semantic=('match','match_type','where','effects')
 for target,variant in expected.items():
  expected_name=variant.get('name',target) if isinstance(variant,dict) else target
  row=next((r for r in active if r.get('name')==expected_name and r.get('active',True)),None)
  if row is None:row=next((r for r in active if r.get('name')==target and r.get('active',True)),None)
  if row is None:good=False;continue
  left={key:copy.deepcopy(row[key]) for key in semantic if key in row}
  right={key:copy.deepcopy(variant[key]) for key in semantic if key in variant}
  if left!=right:good=False
 return good

def score(ctx:dict,candidate:dict)->dict:
 family=ctx['family'];worker=ctx['worker'];split=ctx['split'];target=ctx['target'];sub=ctx['sub'];native=ctx['native']
 started=time.perf_counter_ns();source_rules=native.export_rules()
 revision_fn=getattr(native,'experiment_graph_rule_revision',None)
 source_revision=tuple(int(x) for x in revision_fn()) if revision_fn else None
 if family=='shape_axis':
  from domains.imagination import imagine
  branch_started=time.perf_counter_ns()
  detached=imagine(ctx['agent'],hypothesis=None,steps=0,cut_grounding=False,focus_hops=1,record_trace=False)
  branch=detached.detached;branch_ns=time.perf_counter_ns()-branch_started
 else:
  branch_started=time.perf_counter_ns();branch=sub.fork_full_copy_experiment();branch_ns=time.perf_counter_ns()-branch_started
 bn=branch._inner;patch_started=time.perf_counter_ns();applied=_replace(bn,candidate);patch_ns=time.perf_counter_ns()-patch_started
 scoring_started=time.perf_counter_ns();cases=[]
 if family=='control_kind':
  task=ctx['task_module'];registry=next((node for node in branch.nodes('SignalRegistry') if branch.node(node)['attrs'].get('name')=='control_family_signals'),None)
  if registry is None:raise RuntimeError('control-family signal registry absent in branch')
  caseset=task.TRAIN if split=='train' else task.HELDOUT
  for case in caseset:
   node=branch.add_node('ControlKind',{'name':case['name'],'name_lc':case['name'].lower(),'family_set':0.0})
   bn.add_edge_unchecked(registry,'has_kind',node,{})
   work=int(bn.run_rules(1000));attrs=branch.node(node)['attrs']
   cases.append({'case':case['name'],'expected':case['expected'],'actual':attrs.get('effect_family'),
    'family_set':attrs.get('family_set'),'closure_work':work,
    'pass':attrs.get('effect_family')==case['expected'] and attrs.get('family_set')==1.0})
  utility=bool(cases) and all(x['pass'] for x in cases)
 elif family=='navigation':
  task=ctx['task_module'];states=task.STATES
  chosen=({'up','left'} if split=='train' else {'down','right'})
  caseset=[x for x in states if x['case'] in chosen]
  for state in caseset:
   game=branch.add_node('Game',{'flood_epoch':0.0,'nav_mode':'frontier_seek'})
   avatar=branch.add_node('Cell',{'is_avatar_cell':1.0,'row':5.0,'col':5.0,'_adist':0.0,'_epoch':0.0,'_dist':1.0})
   target_node=branch.add_node('Cell',{'is_avatar_cell':0.0,'row':state['target'][0],'col':state['target'][1],
     '_adist':1.0,'_epoch':0.0,'_dist':0.0})
   bn.add_edge_unchecked(game,'reached',avatar,{});bn.add_edge_unchecked(game,'reached',target_node,{})
   work=int(bn.run_rules(100));actual=branch.node(game)['attrs'].get('chosen_action')
   cases.append({'case':state['case'],'expected':state['expected'],'actual':actual,'closure_work':work,'pass':actual==state['expected']})
  utility=bool(cases) and all(x['pass'] for x in cases)
 elif family=='recurrence':
  task=ctx['task_module'];episode=ctx['episode'];keys=ctx['keys']
  first_sweeps=[int(bn.run_rules(100)) for _ in range(5)]
  for j,key in enumerate(keys[1:],start=1):
   attrs={'predicate':'bind','recurrence_key':key,'structural_signature':[['relation','bind','ITEM',f'SLOT{j}',worker]],'capability_key':[key,'X']}
   cand=branch.add_node('PredicateRecurrenceCandidate',attrs)
   ev=branch.add_node('ResidualSegmentEvidence',{**attrs,'segment_ordinal':j,'integer_native':1})
   bn.add_edge_unchecked(episode,'has_predicate_recurrence_candidate',cand,{})
   bn.add_edge_unchecked(cand,'supported_by_segment',ev,{})
  second_sweeps=[int(bn.run_rules(100)) for _ in range(5)]
  counts=[]
  for key in keys:
   node=next(n for n in branch.nodes('PredicateRecurrenceCandidate') if branch.node(n)['attrs'].get('recurrence_key')==key)
   counts.append(len(list(branch.neighbours(node,'has_mint_offer'))))
  fixed=int(bn.run_rules(100))
  cases=[{'case':f'{split}_candidate_{i}','offer_count':count,'expected_offers':1,'pass':count==1} for i,count in enumerate(counts)]
  cases.append({'case':f'{split}_fixedpoint','work':fixed,'expected_work':0,'pass':fixed==0})
  utility=counts==[1,1] and fixed==0
  cases[0]['first_candidate_sweeps']=first_sweeps;cases[0]['second_candidate_sweeps']=second_sweeps
 elif family=='shape_axis':
  agent=ctx['agent']
  # Branch was created through the existing thoughtexperiment snapshot path.
  prefix=f'{split}_{worker}_P'
  observations=[]
  for i in range(3):
   token=f'{prefix}{i}'
   node=branch.add_node('Observation',{'signature':[[token,'X']],'key':[token],'status':'pending'})
   try:bn.add_edge_unchecked(agent.agent,'observed',node,{})
   except TypeError:bn.add_edge_unchecked(agent.agent,'observed',node)
   observations.append((token,node))
  work=int(bn.run_rules(2000));fixed=int(bn.run_rules(2000));pending=[];axes={}
  for token,node in observations:
   if branch.has_node(node) and branch.node(node)['attrs'].get('status')=='pending':pending.append(token)
   matches=[x for x in branch.nodes('CapabilityAxis') if branch.node(x)['attrs'].get('induced') and
    branch.node(x)['attrs'].get('capability_keys')==[[token,'X']]]
   axes[token]=len(matches)
  cases=[{'case':token,'axis_count':axes[token],'expected_axis_count':1,'settled':token not in pending,
    'pass':axes[token]==1 and token not in pending} for token,_ in observations]
  cases.append({'case':f'{split}_fixedpoint','work':fixed,'expected_work':0,'pass':fixed==0})
  utility=all(x['pass'] for x in cases)
 else:raise ValueError(family)
 scoring_ns=time.perf_counter_ns()-scoring_started
 verify_started=time.perf_counter_ns();receipt_ok=_receipt(bn,candidate,applied);verification_ns=time.perf_counter_ns()-verify_started
 after_revision=tuple(int(x) for x in revision_fn()) if revision_fn else None
 primary_unchanged=native.export_rules()==source_rules and after_revision==source_revision
 if not receipt_ok:utility=False
 return {'worker':worker,'family':family,'split':split,'label':candidate['label'],'digest':digest(candidate),
  'task_cases':cases,'utility':float(bool(utility)),'oracle_pass':all(x.get('pass',False) for x in cases),
  'receipt_verified':receipt_ok,'applied_rules':applied,'primary_preserved':primary_unchanged,
  'cost_ns':{'branch_creation_ns':branch_ns,'candidate_patch_ns':patch_ns,
   'task_scoring_ns':scoring_ns,'adoption_verification_ns':verification_ns,
   'candidate_trial_ns':time.perf_counter_ns()-started}}
