#!/usr/bin/env python3
"""Select among graph-Term matchers on Omniglot background data and test transfer."""
from __future__ import annotations
import hashlib,json,os,platform,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
RUNNER=Path(__file__).resolve()
PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_OMNIGLOT_MATCHER_SELECTION_V1_PREREG_20261002.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_omniglot_matcher_selection_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_omniglot_matcher_selection_v1_lock_20261002.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_omniglot_matcher_selection_v1_orders_20261002.json'
SCORES=ROOT/'evaluation/reports/thoughtexperiment_omniglot_matcher_selection_v1_scores_20261002.json'
WORKERS=3; EPISODES=40; WAY=20; N_POINTS=64
SPLITS=('background','evaluation')
SYSTEMS=('ordered_dtw','pointset','deformable')
SEEDS={'background':(1709,2713,3719),'evaluation':(4703,5701,6701)}
SOURCES=('domains/recognition_graph.py','domains/glyph_motor_world.py','domains/omniglot_world.py',
 'domains/dataset_root.py','domains/contract_query.py','runners/dsl/src/term.rs',
 'runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/src/graph.rs',
 'runners/dsl/src/persist.rs','runners/dsl/python/substrate_rs/__init__.py')
DATA_ROOT=ROOT/'data/omniglot'

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def data_manifest():
 from domains import omniglot_world as ow
 out={}
 for split in SPLITS:
  base=Path(ow.split_dir(split)); files=sorted(p for p in base.rglob('*') if p.is_file())
  h=hashlib.sha256()
  for p in files:
   rel=p.relative_to(base).as_posix().encode(); d=bytes.fromhex(sha(p))
   h.update(len(rel).to_bytes(4,'big'));h.update(rel);h.update(d)
  out[split]={'root':str(base.relative_to(ROOT)),'file_count':len(files),'sha256':h.hexdigest(),
   'alphabets':sorted(ow.alphabets(split))}
 return out
def frozen():
 from substrate_rs import _native
 paths=[ROOT/p for p in SOURCES]+[RUNNER,PROTOCOL,ANALYZER]
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in paths},
  'native_binary_sha256':sha(Path(_native.__file__).resolve()),'dataset':data_manifest()}
def make_specs(split,worker):
 import numpy as np
 from domains import omniglot_world as ow
 import os
 alphs=sorted(a for a in ow.alphabets(split) if len(ow.characters(a,split))>=WAY)
 if not alphs:raise RuntimeError(f'no eligible alphabets in {split}')
 rng=np.random.default_rng(SEEDS[split][worker]);base=Path(ow.split_dir(split));specs=[]
 for ep in range(EPISODES):
  alphabet=alphs[int(rng.integers(len(alphs)))];chars=ow.characters(alphabet,split)
  chosen=[chars[int(i)] for i in rng.permutation(len(chars))[:WAY]]
  ex=int(rng.integers(20))+1;q=int(rng.integers(19))+1
  if q>=ex:q+=1
  labels=[Path(c).relative_to(base).as_posix() for c in chosen]
  specs.append({'episode':ep,'split':split,'alphabet':alphabet,'classes':chosen,'labels':labels,
   'exemplar_drawer':ex,'query_drawer':q})
 return specs
def trajectory_cache(spec_sets):
 from domains import omniglot_world as ow
 cache={};input_keys=set()
 for specs in spec_sets:
  for e in specs:
   for cls in e['classes']:
    for drawer in (e['exemplar_drawer'],e['query_drawer']):input_keys.add((cls,drawer,e['split']))
 for cls,drawer,split in sorted(input_keys):
  paths=ow.drawings(cls);matches=[p for p in paths if Path(p).stem.rsplit('_',1)[-1]==f'{drawer:02d}']
  if len(matches)!=1:raise RuntimeError(f'expected one drawing for {cls} writer {drawer}: {len(matches)}')
  cache[(cls,drawer,split)]=ow.trajectory(matches[0],N_POINTS,per_stroke=True).tolist()
 return cache
class Pred:
 __slots__=('_json',)
 def __init__(self,term):self._json=term
def score_episode(spec,cache,system):
 import substrate_rs as srs
 from domains import glyph_motor_world as gm
 from domains.recognition_graph import predict_synth_term,predict_pointset_term,predict_deform_term
 terms={'ordered_dtw':predict_synth_term(),'pointset':predict_pointset_term(),'deformable':predict_deform_term()}
 term=Pred(terms[system]);s=srs.Substrate();t0=time.perf_counter_ns()
 for cls,label in zip(spec['classes'],spec['labels']):
  node=s.add_node('Concept',{'name':label,gm.WORD_ATTR:1.0})
  s.set_attr(node,gm.SYNTH_ATTR,cache[(cls,spec['exemplar_drawer'],spec['split'])])
 predictions=[];query_ns=0
 for cls in spec['classes']:
  mark=s.add_node('Mark',{gm.MARK_ATTR:cache[(cls,spec['query_drawer'],spec['split'])]})
  start=time.perf_counter_ns();winner=s.evaluate(term,{'s':mark});query_ns+=time.perf_counter_ns()-start
  predictions.append(s.node(winner)['attrs'].get('name') if winner is not None else None)
 return {'system':system,'episode':spec['episode'],'split':spec['split'],'alphabet':spec['alphabet'],
  'labels':spec['labels'],'predictions':predictions,'correct_count':sum(a==b for a,b in zip(predictions,spec['labels'])),'query_count':len(spec['labels']),
  'all_predictions_valid':all(p in spec['labels'] for p in predictions),
  'episode_key_sha256':hashlib.sha256(json.dumps({k:spec[k] for k in ('split','alphabet','labels','exemplar_drawer','query_drawer')},sort_keys=True,separators=(',',':')).encode()).hexdigest(),
  'matcher_wall_ns':time.perf_counter_ns()-t0,'term_eval_ns':query_ns}
def evaluate_split(specs,cache):
 rows=[]
 for system in SYSTEMS:
  for spec in specs:rows.append(score_episode(spec,cache,system))
 return rows
def train_worker(worker):
 from domains.contract_query import select_candidate_from_graph_evidence
 before=frozen(); t0=time.perf_counter_ns()
 train=make_specs('background',worker); held=make_specs('evaluation',worker)
 cache=trajectory_cache((train,held));prep_ns=time.perf_counter_ns()-t0
 rows=evaluate_split(train,cache)
 proposals=[{'proposal_id':s,'proposal_label':s} for s in SYSTEMS]
 evidence=[]
 by={(r['system'],r['episode']):r for r in rows}
 for system in SYSTEMS:
  for e in train:
   row=by[(system,e['episode'])]
   for i,(pred,gold) in enumerate(zip(row['predictions'],row['labels'])):
    evidence.append({'proposal_id':system,'probe_id':f"w{worker}_e{e['episode']}_q{i}",
     'predicted':'correct' if pred==gold else 'incorrect','expected':'correct'})
 primary=__import__('substrate_rs').Substrate()
 marker=primary.add_node('ExperimentEpisode',{'experiment_id':f'omni_match_w{worker}','train_episode_count':EPISODES})
 snapshot=primary.snapshot();branch=snapshot.fork();before_candidates=(len(branch.nodes('CandidateProposal')),len(branch.nodes('CandidateEvidence')))
 tick=time.perf_counter_ns();decision=select_candidate_from_graph_evidence(branch,f'omni_match_w{worker}',proposals,evidence);term_ns=time.perf_counter_ns()-tick
 decision.pop('proposal_node',None)
 control_results={}
 for control,predicted in [('all_wrong','incorrect'),('tie','correct')]:
  cb=snapshot.fork();ev=[{'proposal_id':x,'probe_id':f'{control}_{i}','predicted':predicted,'expected':'correct'} for x in SYSTEMS for i in range(4)]
  control_results[control]=select_candidate_from_graph_evidence(cb,f'omni_{control}_w{worker}',proposals,ev).get('ok')
 residual_start=time.perf_counter_ns()
 residual=primary.add_node('ExperimentResidual',{'experiment_id':f'omni_match_w{worker}',
  'selected_proposal_id':decision.get('proposal_id'),'training_probe_count':decision.get('probe_count',0),
  'training_episode_digest':hashlib.sha256(json.dumps([x['episode_key_sha256'] for x in rows if x['system']=='pointset']).encode()).hexdigest()})
 residual_ns=time.perf_counter_ns()-residual_start
 after=frozen()
 return {'worker':worker,'pid':os.getpid(),'train_specs':train,'heldout_specs':held,'training_rows':rows,
  'training_decision':decision,'controls':control_results,'selected_proposal_id':decision.get('proposal_id'),
  'training_accuracy_by_system':{s:sum(r['correct_count'] for r in rows if r['system']==s)/sum(r['query_count'] for r in rows if r['system']==s) for s in SYSTEMS},
  'feature_prep_ns':prep_ns,'graph_selection_ns':term_ns,'residual_return_ns':residual_ns,
  'branch_node_counts':{'before':before_candidates,'after':(len(branch.nodes('CandidateProposal')),len(branch.nodes('CandidateEvidence')))},
  'primary_has_no_candidate_evidence':not primary.nodes('CandidateProposal') and not primary.nodes('CandidateEvidence'),
  'residual_returned':primary.has_node(residual) and primary.node(residual)['attrs']['selected_proposal_id']==decision.get('proposal_id'),
  'source_before':before,'source_after':after,'source_stable':before==after}
def score_worker(order):
 before=frozen();cache=trajectory_cache((order['heldout_specs'],));rows=evaluate_split(order['heldout_specs'],cache);after=frozen()
 return {'worker':order['worker'],'pid':os.getpid(),'heldout_rows':rows,'heldout_accuracy_by_system':{s:sum(r['correct_count'] for r in rows if r['system']==s)/sum(r['query_count'] for r in rows if r['system']==s) for s in SYSTEMS},
  'source_before':before,'source_after':after,'source_stable':before==after}
def main():
 from domains.engine_provenance import build_is_stale,engine_provenance
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('stale native engine: '+'; '.join(stale))
 env={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}'}
 if sys.argv[1:]==['--lock']:
  if any(p.exists() for p in (LOCK,ORDERS,SCORES)):raise SystemExit('refusing to overwrite study capture')
  LOCK.write_text(json.dumps({'schema':'ThoughtexperimentOmniglotMatcherSelectionV1Lock','sources':frozen(),
   'engine':engine_provenance(),'workers':WORKERS,'episodes_per_split':EPISODES,'way':WAY,'points':N_POINTS,'systems':SYSTEMS},indent=2,sort_keys=True)+'\n');print(LOCK);return
 if not LOCK.exists() or frozen()!=json.loads(LOCK.read_text())['sources']:raise SystemExit('missing lock/source drift')
 if sys.argv[1:]==['--orders']:
  if ORDERS.exists() or SCORES.exists():raise SystemExit('orders/scores already exist')
  ws=[]
  for i in range(WORKERS):
   p=subprocess.run([sys.executable,str(RUNNER),'--train-worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True)
   if p.returncode:raise RuntimeError(p.stderr[-3000:])
   ws.append(json.loads(p.stdout.strip().splitlines()[-1]))
  ORDERS.write_text(json.dumps({'schema':'ThoughtexperimentOmniglotMatcherSelectionV1Orders','lock_sha256':sha(LOCK),'workers':ws,
   'captured_utc':datetime.now(timezone.utc).isoformat(),'host':{'platform':platform.platform(),'python':sys.version}},indent=2,sort_keys=True)+'\n');print(ORDERS);return
 if sys.argv[1:]==['--score']:
  if not ORDERS.exists() or SCORES.exists():raise SystemExit('orders missing or scores exist')
  od=json.loads(ORDERS.read_text())
  if od['lock_sha256']!=sha(LOCK):raise SystemExit('order lock mismatch')
  ws=[]
  for order in od['workers']:
   p=subprocess.run([sys.executable,str(RUNNER),'--score-worker'],input=json.dumps(order),cwd=ROOT,env=env,text=True,capture_output=True)
   if p.returncode:raise RuntimeError(p.stderr[-3000:])
   ws.append(json.loads(p.stdout.strip().splitlines()[-1]))
  SCORES.write_text(json.dumps({'schema':'ThoughtexperimentOmniglotMatcherSelectionV1Scores','orders_sha256':sha(ORDERS),'workers':ws},indent=2,sort_keys=True)+'\n');print(SCORES);return
 if sys.argv[1:2]==['--train-worker']:
  print(json.dumps(train_worker(int(sys.argv[2])),sort_keys=True,separators=(',',':')));return
 if sys.argv[1:2]==['--score-worker']:
  print(json.dumps(score_worker(json.load(sys.stdin)),sort_keys=True,separators=(',',':')));return
 raise SystemExit('use --lock, --orders, or --score')
if __name__=='__main__':main()
