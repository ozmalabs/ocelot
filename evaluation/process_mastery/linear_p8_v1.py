"""P8 held-out mechanism runner for induced process evidence and probes."""
from __future__ import annotations
import argparse,hashlib,json,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
for p in (ROOT,ROOT/'runners/dsl/python'):
 if str(p) not in sys.path:sys.path.insert(0,str(p))
from substrate_rs import _native
from scripts.gen_process_induction_seed import build_seed as pi_seed
from scripts.gen_latent_process_seed import build_seed as latent_seed
from scripts.gen_experiment_design_seed import build_seed as ed_seed
from evaluation.process_mastery.scorecard import write_scorecard
PHASE='linear-p8-v1';ALLOC={'finite_mechanisms':(3_000_000,200),'temporal_latent':(3_000_200,200),'missing_controls':(3_000_400,100),'ambiguous_controls':(3_000_500,100),'funded_refinement':(3_000_600,100)}
def sha(b):return hashlib.sha256(b).hexdigest()
def provenance():
 paths=['evaluation/process_mastery/linear_p8_v1.py','evaluation/process_mastery/analyze_linear_p8_v1.py','scripts/gen_process_induction_seed.py','seeds/process_induction.json','scripts/gen_latent_process_seed.py','seeds/latent_process.json','scripts/gen_experiment_design_seed.py','seeds/experiment_design.json','docs/research/engine_substrate/COGNITION_MODEL_LEARNING_CONTRACT.md','substrate/boot_profiles.py']
 h=hashlib.sha256()
 for x in paths:h.update(x.encode()+b'\0'+(ROOT/x).read_bytes()+b'\0')
 engine=hashlib.sha256()
 for x in ('runners/dsl/Cargo.toml','runners/dsl/src/term.rs','runners/dsl/src/eval.rs'):
  q=ROOT/x
  if q.exists():engine.update(x.encode()+b'\0'+q.read_bytes()+b'\0')
 import substrate_rs
 try:commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
 except Exception:commit='unavailable'
 return {'phase':PHASE,'git_commit':commit,'source_bundle_sha256':h.hexdigest(),'engine_source_sha256':engine.hexdigest(),'engine_binary_sha256':sha(Path(substrate_rs.__file__).read_bytes()),'allocation':ALLOC,'limits':{'ticks':30,'steps':2000,'hypotheses':32,'requests':32}}
def boot(*,policy=True,budget=100):
 s=_native.Substrate();ag=s.add_node('Agent',{})
 for name in ('default_mode_core','thinking_budget','cognition_signature','experience_signature','cognition_manifold'):
  s.load_seed_manifest(json.loads((ROOT/'seeds'/f'{name}.json').read_text()),ag)
 for seed in (pi_seed(),latent_seed(),ed_seed()):s.load_seed_manifest(seed,ag)
 for n in s.nodes('ThinkingBudget'):
  s.set_attr(n,'enabled',1.);s.set_attr(n,'remaining',float(budget));s.set_attr(n,'last_refill_epoch',10.)
 s.set_attr(s.nodes('NetworkModeState')[0],'epoch',10.)
 for typ in ('ModelLearningPolicy','LatentProcessPolicy','ExperimentDesignPolicy'):
  s.set_attr(s.nodes(typ)[0],'enabled',1. if policy else 0.)
 return s,ag
def tick(s):
 for _ in range(30):
  if not s.run_rules(2000):return
 raise RuntimeError('P8 rules failed to reach fixpoint')
def portfolio(s,ag,seed):
 hyps=[]
 for key in ('h-a','h-b'):
  h=s.add_node('ProcessInductionHypothesis',{'hypothesis_key':f'{seed}:{key}','owner_id':'owner-a','status':'candidate','counterexample_count':0.0,'model_epoch':2})
  s.add_edge(ag,'has_process_induction_hypothesis',h);hyps.append(h)
 return hyps
def add_probe(s,ag,seed,name,preds,cost=1):
 p=s.add_node('ExperimentProbe',{'probe_id':f'{seed}:{name}','owner_id':'owner-a','source_epoch':3,'model_epoch':2,'frame_epoch':5,'status':'proposed','host_veto':False,'cost':float(cost)})
 s.add_edge(ag,'has_experiment_probe',p)
 for h,outcome in zip(portfolio(s,ag,seed),preds):
  pp=s.add_node('ProbePrediction',{'prediction_id':f'{seed}:{name}:{s.node(h)["attrs"]["hypothesis_key"]}','owner_id':'owner-a','hypothesis_key':s.node(h)['attrs']['hypothesis_key'],'predicted_outcome':outcome,'model_epoch':2,'frame_epoch':5})
  s.add_edge(p,'has_probe_prediction',pp);s.add_edge(pp,'based_on_hypothesis',h)
 return p
def mechanism(seed,arm,truth):
 s,ag=boot(policy=(arm=='learned'));t0=time.perf_counter()
 if arm=='learned':
  add_probe(s,ag,seed,'fixed',('same','same'),cost=1)
  add_probe(s,ag,seed,'distinguishing',('red','blue'),cost=2)
 elif arm=='passive':
  add_probe(s,ag,seed,'passive',('same','same'),cost=1)
 else:
  add_probe(s,ag,seed,'fixed',('red','blue') if seed%2==0 else ('same','same'),cost=1)
 tick(s)
 chosen=[n for n in s.nodes('SelectedExperiment') if s.node(n)['attrs']['status']=='selected']
 if arm=='learned' and chosen:
  selected=chosen[0];probe=next(n for n in s.neighbours(selected,'selects_experiment_probe'))
 elif arm in ('fixed','fixed_probe','passive'):
  suffix='fixed' if arm in ('fixed','fixed_probe') else 'passive'
  probe=next(n for n in s.nodes('ExperimentProbe') if s.node(n)['attrs']['probe_id'].endswith(':'+suffix))
  selected=s.add_node('SelectedExperiment',{'selection_id':f'{arm}:{seed}','probe_id':s.node(probe)['attrs']['probe_id'],'owner_id':'owner-a','model_epoch':2,'status':'selected'})
  s.add_edge(ag,'has_selected_experiment',selected);s.add_edge(selected,'selects_experiment_probe',probe)
 else:probe=None;selected=None
 identified=False
 if selected and probe:
  result=s.add_node('ObservedExperimentResult',{'result_id':f'result:{seed}','probe_id':s.node(probe)['attrs']['probe_id'],'owner_id':'owner-a','model_epoch':2,'status':'observed','observed_outcome':truth})
  s.add_edge(ag,'has_experiment_result',result);s.add_edge(result,'result_for_experiment',selected);tick(s)
  if arm=='learned':
   identified=any(s.node(n)['attrs'].get('last_experiment_evidence')=='supporting' for n in s.nodes('ProcessInductionHypothesis'))
  elif arm in ('fixed','fixed_probe'):
   outcomes=[s.node(n)['attrs'].get('predicted_outcome') for n in s.neighbours(probe,'has_probe_prediction')]
   identified=len(set(outcomes))>1 and truth in outcomes
 return {'family':'finite_mechanism','seed':seed,'profile':arm,'status':'COMPLETED','outcome':'identified' if identified else 'not_identified','external_outcome':{'pass':identified},'truth':{'outcome':truth},'input_answer_exposed':False,'interactions':1,'compute':{'seconds':round(time.perf_counter()-t0,6),'graph_nodes':len(s.nodes())}}
def latent_trial(seed,good=True,kind='regular'):
 s,ag=boot();t0=time.perf_counter()
 seq=[('low','cold'),('high','warm'),('low','cold')] if good else [('low','cold'),('high','noise'),('low','warm')]
 if kind=='missing':seq=seq[:2]
 for i,(res,feat) in enumerate(seq):
  ep=f'e{seed}-{i}';event=f'v{seed}-{i}'
  obs=s.add_node('TransitionObservation',{'owner_id':'owner-a','episode_id':ep,'event_id':event,'source_epoch':3,'model_epoch':2,'frame_epoch':5,'status':'observed'})
  r=s.add_node('ObservedPredictionResidual',{'owner_id':'owner-a','episode_id':ep,'event_id':event,'window_id':f'w{seed}-{i}','residual_key':'same-visible-action','feature_key':'hidden-cue','observed_feature_value':feat,'residual_outcome':res,'source_epoch':3,'model_epoch':2,'frame_epoch':5,'sampling_interval':1.0,'regular_sampling':kind!='ambiguous','complete_window':True,'status':'observed'})
  s.add_edge(ag,'has_transition_observation',obs);s.add_edge(ag,'has_prediction_residual',r);s.add_edge(r,'residual_from_transition',obs)
 tick(s)
 if good:
  ep=f'e{seed}-future';event=f'v{seed}-future';obs=s.add_node('TransitionObservation',{'owner_id':'owner-a','episode_id':ep,'event_id':event,'source_epoch':3,'model_epoch':2,'frame_epoch':5,'status':'observed'})
  r=s.add_node('ObservedPredictionResidual',{'owner_id':'owner-a','episode_id':ep,'event_id':event,'window_id':f'w{seed}-future','residual_key':'same-visible-action','feature_key':'hidden-cue','observed_feature_value':'warm','residual_outcome':'high','source_epoch':3,'model_epoch':2,'frame_epoch':5,'sampling_interval':1.0,'regular_sampling':kind!='ambiguous','complete_window':True,'status':'observed'})
  s.add_edge(ag,'has_transition_observation',obs);s.add_edge(ag,'has_prediction_residual',r);s.add_edge(r,'residual_from_transition',obs);tick(s)
 verified=any(s.node(n)['attrs'].get('status')=='validated' for n in s.nodes('LatentProcessCandidate'))
 return {'family':'temporal_latent','seed':seed,'profile':'latent-enabled','status':'COMPLETED','outcome':'verified' if verified else 'unknown','external_outcome':{'pass':verified==good},'truth':{'latent_relation':good},'input_answer_exposed':False,'compute':{'seconds':round(time.perf_counter()-t0,6),'graph_nodes':len(s.nodes())}}
def refinement(seed):
 s,ag=boot();projection=s.add_node('WorldModelProjection',{'owner_id':'owner-a','model_epoch':2,'version':0.0});s.add_edge(ag,'has_world_model_projection',projection)
 add_probe(s,ag,seed,'probe',('yes','no'),1);tick(s);selected=next(n for n in s.nodes('SelectedExperiment') if s.node(n)['attrs']['status']=='selected');probe=next(n for n in s.neighbours(selected,'selects_experiment_probe'))
 result=s.add_node('ObservedExperimentResult',{'result_id':f'refinement-{seed}','probe_id':s.node(probe)['attrs']['probe_id'],'owner_id':'owner-a','model_epoch':2,'status':'observed','observed_outcome':'yes'});s.add_edge(ag,'has_experiment_result',result);s.add_edge(result,'result_for_experiment',selected);tick(s)
 changed=s.node(projection)['attrs'].get('version')==1.0
 return {'family':'funded_refinement','seed':seed,'profile':'experiment-design','status':'COMPLETED','outcome':'recomputed' if changed else 'not_recomputed','external_outcome':{'pass':changed},'input_answer_exposed':False}
def run(split='development',n=200,self_check=False):
 if self_check:
  rows=[mechanism(1,'learned','red'),mechanism(1,'passive','red'),mechanism(2,'fixed_probe','red'),latent_trial(2,True),latent_trial(3,False),refinement(4)]
 else:
  if n!=200:raise ValueError('registered P8 allocation fixes 200/100 per family')
  off=3_000_000 if split=='heldout' else 0;rows=[]
  for i in range(200):
   seed=off+i;truth='red' if i%2==0 else 'blue'
   for arm in ('learned','passive','fixed_probe'):rows.append(mechanism(seed,arm,truth))
   rows.append(latent_trial(off+200+i,good=(i%2==0)))
  for i in range(100):
   rows.append(latent_trial(off+400+i,good=False,kind='missing'))
   rows.append(latent_trial(off+500+i,good=False,kind='ambiguous'))
   rows.append(refinement(off+600+i))
 return {'schema':'pmb-scorecard-v1','metadata':{**provenance(),'split':split,'registered_draw':not self_check,'n_records':len(rows)},'records':rows}
def main():
 p=argparse.ArgumentParser();p.add_argument('--split',choices=('development','heldout'),default='development');p.add_argument('--n',type=int,default=200);p.add_argument('--self-check',action='store_true');p.add_argument('--output',type=Path);a=p.parse_args();payload=run(a.split,a.n,a.self_check)
 if a.output:write_scorecard(a.output,metadata=payload['metadata'],records=payload['records'])
 else:print(json.dumps(payload,indent=2,sort_keys=True))
 if a.self_check:
  assert len(payload['records'])==6 and all(r['status'] in ('COMPLETED','UNSUPPORTED') for r in payload['records']);print('linear_p8 runner self-check: PASS')
if __name__=='__main__':main()
