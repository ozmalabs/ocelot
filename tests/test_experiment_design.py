"""P8.04 native rules for funded discriminating experiments."""
import json
from pathlib import Path
from substrate_rs import _native
from scripts.gen_experiment_design_seed import build_seed
ROOT=Path(__file__).resolve().parents[1]

def _boot(enabled=True,budget=100):
 s=_native.Substrate();ag=s.add_node('Agent',{})
 for name in ('default_mode_core','thinking_budget','cognition_signature','experience_signature','cognition_manifold','process_induction'):
  s.load_seed_manifest(json.loads((ROOT/'seeds'/f'{name}.json').read_text()),ag)
 result=s.load_seed_manifest(build_seed(),ag);assert result['rules_skipped']==[],result
 for b in s.nodes('ThinkingBudget'):
  s.set_attr(b,'enabled',1.);s.set_attr(b,'remaining',float(budget));s.set_attr(b,'last_refill_epoch',10.)
 s.set_attr(s.nodes('NetworkModeState')[0],'epoch',10.)
 s.set_attr(s.nodes('ExperimentDesignPolicy')[0],'enabled',1. if enabled else 0.)
 return s,ag

def _probe(s,ag,name,predictions,cost=1.,veto=False):
 probe=s.add_node('ExperimentProbe',{'probe_id':name,'owner_id':'owner-a','source_epoch':3,'model_epoch':2,'frame_epoch':5,'status':'proposed','host_veto':veto,'cost':cost,'action_id':f'action-{name}'})
 s.add_edge(ag,'has_experiment_probe',probe)
 preds=[]
 for key,outcome in predictions:
  hyp=s.add_node('ProcessInductionHypothesis',{'hypothesis_key':key,'owner_id':'owner-a','status':'candidate','counterexample_count':0.0})
  s.add_edge(ag,'has_process_induction_hypothesis',hyp)
  p=s.add_node('ProbePrediction',{'prediction_id':f'{name}-{key}','owner_id':'owner-a','hypothesis_key':key,'predicted_outcome':outcome,'model_epoch':2,'frame_epoch':5})
  s.add_edge(probe,'has_probe_prediction',p);s.add_edge(p,'based_on_hypothesis',hyp);preds.append(p)
 return probe,preds

def _tick(s):
 for _ in range(30):
  if not s.run_rules(2000):return
 raise AssertionError('experiment-design rules failed to reach fixpoint')

def _projection(s,ag):
 node=s.add_node('WorldModelProjection',{'owner_id':'owner-a','model_epoch':2,'version':4.0,'status':'current'})
 s.add_edge(ag,'has_world_model_projection',node);return node

def test_probe_distinguishes_hypotheses_and_minimum_cost_selected():
 s,ag=_boot();_projection(s,ag)
 expensive,_=_probe(s,ag,'expensive',[('h1','red'),('h2','blue')],cost=3.)
 cheap,_=_probe(s,ag,'cheap',[('h1','left'),('h2','right')],cost=1.)
 _tick(s)
 selected=[n for n in s.nodes('SelectedExperiment') if s.node(n)['attrs']['status']=='selected']
 assert len(selected)==1
 assert s.node(selected[0])['attrs']['probe_id']=='cheap'
 assert s.node(selected[0])['attrs']['information_status']=='hypotheses_separated'
 assert 'information_gain' not in s.node(selected[0])['attrs']
 assert s.node(expensive)['attrs']['status']=='superseded'

def test_no_information_no_voi_claim():
 s,ag=_boot();_projection(s,ag)
 _probe(s,ag,'uninformative',[('h1','same'),('h2','same')])
 _tick(s)
 assert not s.nodes('SelectedExperiment')
 assert not s.nodes('ThinkingBudgetRequest')

def test_actual_outcome_updates_portfolio():
 s,ag=_boot();_projection(s,ag)
 probe,preds=_probe(s,ag,'probe',[('h1','red'),('h2','blue')]);_tick(s)
 selected=s.nodes('SelectedExperiment')[0]
 result=s.add_node('ObservedExperimentResult',{'result_id':'result-1','probe_id':'probe','owner_id':'owner-a','model_epoch':2,'status':'observed','observed_outcome':'red'})
 s.add_edge(ag,'has_experiment_result',result);s.add_edge(result,'result_for_experiment',selected)
 _tick(s)
 assert s.node(selected)['attrs']['status']=='completed'
 audit=s.nodes('ExperimentRevisionAudit');assert len(audit)==3
 assert {s.node(n)['attrs']['status'] for n in audit}=={'supports','disconfirms','projection_recomputed'}
 assert any(s.node(n)['attrs'].get('expected_outcome')=='red' for n in audit)
 hypotheses={s.node(s.neighbours(pred,'based_on_hypothesis')[0])['attrs']['hypothesis_key']:s.neighbours(pred,'based_on_hypothesis')[0] for pred in preds}
 assert s.node(hypotheses['h1'])['attrs']['last_experiment_evidence']=='supporting'
 assert s.node(hypotheses['h2'])['attrs']['status']=='disputed'
 assert s.neighbours(hypotheses['h2'],'has_counterexample')

def test_funded_refinement_changes_audit():
 s,ag=_boot();projection=_projection(s,ag)
 _probe(s,ag,'probe',[('h1','red'),('h2','blue')]);_tick(s)
 selected=s.nodes('SelectedExperiment')[0]
 result=s.add_node('ObservedExperimentResult',{'result_id':'result-2','probe_id':'probe','owner_id':'owner-a','model_epoch':2,'status':'observed','observed_outcome':'unexpected'})
 s.add_edge(ag,'has_experiment_result',result);s.add_edge(result,'result_for_experiment',selected);_tick(s)
 assert s.node(projection)['attrs']['version']==5.0
 assert s.node(projection)['attrs']['last_result_id']=='result-2'
 assert any(s.node(n)['attrs']['status']=='projection_recomputed' for n in s.nodes('ExperimentRevisionAudit'))

def test_exhaustion_not_retained_and_host_veto():
 s,ag=_boot(budget=0);_projection(s,ag)
 s.set_attr(s.nodes('ThinkingBudget')[0],'last_refill_epoch',10.0)
 probe,_=_probe(s,ag,'denied',[('h1','red'),('h2','blue')]);_tick(s)
 assert not s.nodes('SelectedExperiment')
 request=s.nodes('ThinkingBudgetRequest');assert len(request)==1
 assert s.node(request[0])['attrs']['status']=='denied'
 assert s.node(probe)['attrs']['status']=='proposed'
 s2,ag2=_boot();_projection(s2,ag2);_probe(s2,ag2,'vetoed',[('h1','red'),('h2','blue')],veto=True);_tick(s2)
 assert not s2.nodes('ThinkingBudgetRequest') and not s2.nodes('SelectedExperiment')
