"""P8.02 native graph-rule tests for bounded transition induction."""
import json
from pathlib import Path
from substrate_rs import _native
from scripts.gen_process_induction_seed import build_seed
ROOT=Path(__file__).resolve().parents[1]

def _boot(enabled=True,budget=100):
 s=_native.Substrate();ag=s.add_node('Agent',{})
 for name in ('default_mode_core','thinking_budget','cognition_signature','experience_signature'):
  s.load_seed_manifest(json.loads((ROOT/'seeds'/f'{name}.json').read_text()),ag)
 result=s.load_seed_manifest(build_seed(),ag);assert result['rules_skipped']==[],result
 for n in s.nodes('ThinkingBudget'):
  s.set_attr(n,'enabled',1.);s.set_attr(n,'remaining',float(budget));s.set_attr(n,'last_refill_epoch',10.)
 s.set_attr(s.nodes('NetworkModeState')[0],'epoch',10.)
 s.set_attr(s.nodes('ModelLearningPolicy')[0],'enabled',1. if enabled else 0.)
 return s,ag

def _transition(s,ag,i,obj,after,*,before='cold',action='warm',object_type='Widget',feature='temperature',owner='owner-a',model=2,source=3,receipt=True):
 ep=f'episode-{i}';event=f'event-{i}'
 obs=s.add_node('TransitionObservation',{'owner_id':owner,'episode_id':ep,'event_id':event,'object_id':obj,'object_type':object_type,'action_kind':action,'feature_key':feature,'before_value':before,'after_value':after,'source_epoch':source,'model_epoch':model,'frame_epoch':5,'status':'observed'})
 ar=s.add_node('TransitionActionReceipt',{'owner_id':owner,'episode_id':ep,'event_id':event,'source_epoch':source,'model_epoch':model,'frame_epoch':5,'status':'observed'})
 s.add_edge(ag,'has_transition_observation',obs);s.add_edge(obs,'has_action_receipt',ar)
 if receipt:
  r=s.add_node('TransitionOutcomeReceipt',{'owner_id':owner,'episode_id':ep,'event_id':event,'source_epoch':source,'model_epoch':model,'frame_epoch':5,'status':'observed'})
  s.add_edge(obs,'has_outcome_receipt',r)
 return obs

def _tick(s):
 for _ in range(30):
  if not s.run_rules(2000):return
 raise AssertionError('process-induction rules failed to reach fixpoint')

def _two_support(s,ag):
 _transition(s,ag,1,'object-1','warm')
 _transition(s,ag,2,'object-2','warm')
 _tick(s)
 return s.nodes('ProcessInductionHypothesis')

def test_effect_learned_from_trace():
 s,ag=_boot();hyps=_two_support(s,ag)
 assert len(hyps)==1
 attrs=s.node(hyps[0])['attrs']
 assert attrs['status']=='candidate' and attrs['after_value']=='warm'
 assert attrs['support_count']==2.0
 assert len(s.neighbours(hyps[0],'supported_by_transition'))==2
 assert all(s.node(n)['attrs']['status']=='approved' for n in s.nodes('TransitionLearningRequest'))

def test_unseen_object_binding():
 s,ag=_boot();hyps=_two_support(s,ag);hyp=hyps[0]
 query=s.add_node('ProcessPredictionQuery',{'query_id':'query-new-object','owner_id':'owner-a','object_id':'object-3','object_type':'Widget','action_kind':'warm','feature_key':'temperature','before_value':'cold','source_epoch':3,'model_epoch':2,'frame_epoch':5,'status':'pending'})
 s.add_edge(ag,'has_process_prediction_query',query);_tick(s)
 pred=s.nodes('ProcessPrediction');assert len(pred)==1
 assert s.node(pred[0])['attrs']['expected_after_value']=='warm'
 assert s.node(pred[0])['attrs']['evidence_status']=='predicted'
 assert s.node(query)['attrs'].get('after_value') is None
 assert s.neighbours(pred[0],'based_on_hypothesis')==[hyp]

def test_counterexample_revises_model():
 s,ag=_boot();hyps=_two_support(s,ag);hyp=hyps[0]
 _transition(s,ag,3,'object-3','cold',before='cold')
 _tick(s)
 assert s.node(hyp)['attrs']['status']=='disputed'
 assert s.node(hyp)['attrs']['counterexample_count']>=1
 assert s.neighbours(hyp,'has_counterexample')
 assert len(s.neighbours(hyp,'supported_by_transition'))==2

def test_indistinguishable_hypotheses_retained():
 s,ag=_boot()
 _transition(s,ag,1,'object-1','warm')
 _transition(s,ag,2,'object-2','warm')
 _transition(s,ag,3,'object-3','hot')
 _transition(s,ag,4,'object-4','hot')
 _tick(s)
 by={s.node(n)['attrs']['after_value']:n for n in s.nodes('ProcessInductionHypothesis')}
 assert {'warm','hot'} <= set(by)
 assert all(s.node(n)['attrs']['status']=='disputed' for n in by.values())
 assert all(s.neighbours(n,'has_counterexample') for n in by.values())

def test_no_trace_no_model_and_disabled_policy():
 s,ag=_boot();_tick(s)
 assert not s.nodes('ProcessInductionHypothesis')
 s2,ag2=_boot(enabled=False);_transition(s2,ag2,1,'object-1','warm');_tick(s2)
 assert not s2.nodes('ProcessInductionHypothesis')

def test_mismatched_receipt_epoch_is_rejected():
 s,ag=_boot();obs=_transition(s,ag,1,'object-1','warm')
 rec=s.neighbours(obs,'has_outcome_receipt')[0];s.set_attr(rec,'model_epoch',99)
 _transition(s,ag,2,'object-2','warm');_tick(s)
 assert len(s.nodes('TransitionLearningRequest'))==1
 assert not s.nodes('ProcessInductionHypothesis')


def test_old_plan_invalidated_on_new_model_epoch():
 s,ag=_boot()
 plan=s.add_node('ProcessPlan',{'plan_id':'old-plan','owner_id':'owner-a','model_epoch':1,'status':'current'})
 s.add_edge(ag,'has_model_dependent_plan',plan)
 _transition(s,ag,1,'object-1','warm',model=2)
 _tick(s)
 attrs=s.node(plan)['attrs']
 assert attrs['status']=='stale'
 assert attrs['stale_reason']=='model_epoch_changed'
