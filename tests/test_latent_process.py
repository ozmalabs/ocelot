"""P8.03 native rules for regular-window residual hypotheses."""
import json
from pathlib import Path
from substrate_rs import _native
from scripts.gen_latent_process_seed import build_seed
ROOT=Path(__file__).resolve().parents[1]

def _boot(enabled=True):
 s=_native.Substrate();ag=s.add_node('Agent',{})
 for name in ('default_mode_core','thinking_budget','cognition_signature','experience_signature'):
  s.load_seed_manifest(json.loads((ROOT/'seeds'/f'{name}.json').read_text()),ag)
 s.load_seed_manifest(build_seed(),ag)
 for b in s.nodes('ThinkingBudget'):
  s.set_attr(b,'enabled',1.);s.set_attr(b,'remaining',100.);s.set_attr(b,'last_refill_epoch',10.)
 s.set_attr(s.nodes('NetworkModeState')[0],'epoch',10.)
 s.set_attr(s.nodes('LatentProcessPolicy')[0],'enabled',1. if enabled else 0.)
 return s,ag

def _residual(s,ag,i,feature,outcome,*,regular=True,owner='owner-a',window=None,interval=1.0):
 ep=f'episode-{i}';ev_id=f'event-{i}';
 obs=s.add_node('TransitionObservation',{'owner_id':owner,'episode_id':ep,'event_id':ev_id,'source_epoch':3,'model_epoch':2,'frame_epoch':5,'status':'observed'})
 rec=s.add_node('ObservedPredictionResidual',{'owner_id':owner,'episode_id':ep,'event_id':ev_id,'window_id':window or f'window-{i}','residual_key':'visible-state-action-prediction','feature_key':'latent-cue','observed_feature_value':feature,'residual_outcome':outcome,'source_epoch':3,'model_epoch':2,'frame_epoch':5,'sampling_interval':interval,'regular_sampling':regular,'complete_window':True,'status':'observed'})
 s.add_edge(ag,'has_transition_observation',obs);s.add_edge(ag,'has_prediction_residual',rec);s.add_edge(rec,'residual_from_transition',obs)
 return rec

def _tick(s):
 for _ in range(30):
  if not s.run_rules(2000):return
 raise AssertionError('latent process rules failed to reach a fixpoint')

def test_latent_explains_persistent_error():
 s,ag=_boot()
 for i,(f,o) in enumerate([('cold','low'),('warm','high'),('cold','low')],1):_residual(s,ag,i,f,o)
 _tick(s)
 candidates=s.nodes('LatentProcessCandidate')
 assert len(candidates)==1
 assert s.node(candidates[0])['attrs']['status']=='proposed'
 assert len(s.neighbours(candidates[0],'supported_by_residual'))==3

def test_future_continuation_verifies():
 s,ag=_boot()
 for i,(f,o) in enumerate([('cold','low'),('warm','high'),('cold','low')],1):_residual(s,ag,i,f,o)
 _tick(s);candidate=s.nodes('LatentProcessCandidate')[0]
 _residual(s,ag,4,'warm','high',window='future-window')
 _tick(s)
 assert s.node(candidate)['attrs']['status']=='validated'
 assert len(s.neighbours(candidate,'has_latent_validation'))==1
 assert len(s.neighbours(candidate,'supported_by_residual'))==4

def test_shuffled_residual_no_latent():
 s,ag=_boot()
 for i,(f,o) in enumerate([('cold','low'),('warm','noise'),('cold','high'),('warm','low')],1):_residual(s,ag,i,f,o)
 _tick(s)
 assert not s.nodes('LatentProcessCandidate')

def test_irregular_stream_still_refused():
 s,ag=_boot()
 for i,(f,o) in enumerate([('cold','low'),('warm','high'),('cold','low')],1):_residual(s,ag,i,f,o,regular=False,interval=float(i))
 _tick(s)
 assert not s.nodes('LatentProcessCandidate')

def test_policy_disabled_no_latent_search():
 s,ag=_boot(enabled=False)
 for i,(f,o) in enumerate([('cold','low'),('warm','high'),('cold','low')],1):_residual(s,ag,i,f,o)
 _tick(s)
 assert not s.nodes('ThinkingBudgetRequest')
 assert not s.nodes('LatentProcessCandidate')
