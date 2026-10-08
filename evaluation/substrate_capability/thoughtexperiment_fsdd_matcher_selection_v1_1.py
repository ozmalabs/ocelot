#!/usr/bin/env python3
"""Choose among native speech-matching Terms on FSDD speakers, then test transfer."""
from __future__ import annotations
import hashlib,json,os,platform,re,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
RUNNER=Path(__file__).resolve()
PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_FSDD_MATCHER_SELECTION_V1_1_PREREG_20261002.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_fsdd_matcher_selection_v1_1.py'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_fsdd_matcher_selection_v1_1_lock_20261002.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_fsdd_matcher_selection_v1_1_orders_20261002.json'
SCORES=ROOT/'evaluation/reports/thoughtexperiment_fsdd_matcher_selection_v1_1_scores_20261002.json'
FSDD=ROOT/'data/fsdd-current/free-spoken-digit-dataset-26eb9aaf76e81b692f806f9140c2d2777410d7a1/recordings'
FOLDS=3; WAY=10; GALLERY_PER_SPEAKER=5; TRAIN_QUERIES_PER_SPEAKER=5; TEST_QUERY_START=10; TEST_QUERIES_PER_SPEAKER=10
SYSTEMS=('ordered_dtw','pointset','matched_filter')
_FN=re.compile(r'(\d)_([a-zA-Z]+)_(\d+)\.wav$')
SOURCES=('scripts/jabberwock_cross_modal.py','domains/recognition_graph.py','domains/glyph_motor_world.py',
 'domains/contract_query.py','domains/engine_provenance.py','runners/dsl/src/term.rs',
 'runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/src/graph.rs',
 'runners/dsl/src/persist.rs','runners/dsl/python/substrate_rs/__init__.py')

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def corpus_manifest():
 files=sorted(FSDD.glob('*.wav'));h=hashlib.sha256();speakers=set();records=[]
 for p in files:
  m=_FN.fullmatch(p.name)
  if not m:raise RuntimeError(f'unrecognized FSDD filename {p.name}')
  digit,speaker,index=int(m.group(1)),m.group(2),int(m.group(3));speakers.add(speaker)
  rel=p.relative_to(ROOT).as_posix().encode();digest=bytes.fromhex(sha(p));h.update(len(rel).to_bytes(4,'big'));h.update(rel);h.update(digest)
  records.append((speaker,digit,index))
 expected={(s,d,i) for s in speakers for d in range(WAY) for i in range(50)}
 if set(records)!=expected or len(records)!=len(expected):raise RuntimeError('FSDD corpus is not a complete six-speaker, 50-recording grid')
 return {'path':str(FSDD.relative_to(ROOT)),'file_count':len(files),'sha256':h.hexdigest(),'speakers':sorted(speakers),
  'digits':list(range(WAY)),'recordings_per_speaker_digit':50}
def frozen():
 from substrate_rs import _native
 paths=[ROOT/p for p in SOURCES]+[RUNNER,PROTOCOL,ANALYZER]
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in paths},
  'native_binary_sha256':sha(Path(_native.__file__).resolve()),'corpus':corpus_manifest()}
def folds():
 speakers=corpus_manifest()['speakers']
 return [{'fold':i,'heldout_speakers':speakers[2*i:2*i+2],
  'training_speakers':[s for s in speakers if s not in speakers[2*i:2*i+2]]} for i in range(FOLDS)]
def file_for(digit,speaker,index):return FSDD/f'{digit}_{speaker}_{index}.wav'
def load_features(paths):
 from scripts.jabberwock_cross_modal import fsdd_feat,load_wav
 cache={};start=time.perf_counter_ns()
 for path in sorted(set(paths)):
  feat=fsdd_feat(load_wav(str(path)))
  if feat.shape!=(32,13):raise RuntimeError(f'unexpected audio feature shape {feat.shape}: {path}')
  cache[str(path.relative_to(ROOT))]=feat.tolist()
 return cache,time.perf_counter_ns()-start
def specs_for(fold,phase):
 f=folds()[fold];specs=[]
 if phase=='train':
  for speaker in f['training_speakers']:
   for digit in range(WAY):
    for index in range(GALLERY_PER_SPEAKER):
     p=file_for(digit,speaker,index);specs.append({'kind':'gallery','speaker':speaker,'digit':digit,'index':index,'path':str(p.relative_to(ROOT))})
    for index in range(GALLERY_PER_SPEAKER,GALLERY_PER_SPEAKER+TRAIN_QUERIES_PER_SPEAKER):
     p=file_for(digit,speaker,index);specs.append({'kind':'query','speaker':speaker,'digit':digit,'index':index,'path':str(p.relative_to(ROOT))})
 else:
  for speaker in f['heldout_speakers']:
   for digit in range(WAY):
    for index in range(TEST_QUERY_START,TEST_QUERY_START+TEST_QUERIES_PER_SPEAKER):
     p=file_for(digit,speaker,index);specs.append({'kind':'query','speaker':speaker,'digit':digit,'index':index,'path':str(p.relative_to(ROOT))})
 return specs
class Pred:
 __slots__=('_json',)
 def __init__(self,term):self._json=term
def score_system(fold,specs,features,system):
 import substrate_rs as srs
 from domains.glyph_motor_world import WORD_ATTR,SYNTH_ATTR,MARK_ATTR
 from domains.recognition_graph import predict_synth_term,predict_pointset_term,predict_matched_filter_term
 terms={'ordered_dtw':predict_synth_term(),'pointset':predict_pointset_term(),'matched_filter':predict_matched_filter_term()}
 s=srs.Substrate();gallery=[x for x in specs if x['kind']=='gallery'];queries=[x for x in specs if x['kind']=='query']
 build_start=time.perf_counter_ns()
 for row in gallery:
  n=s.add_node('Concept',{'name':str(row['digit']),WORD_ATTR:1.0,'is_audio':1.0})
  s.set_attr(n,SYNTH_ATTR,features[row['path']])
 gallery_build_ns=time.perf_counter_ns()-build_start
 predictions=[];term_ns=0;matcher_start=time.perf_counter_ns()
 for q in queries:
  m=s.add_node('Mark',{});s.set_attr(m,MARK_ATTR,features[q['path']])
  tick=time.perf_counter_ns();winner=s.evaluate(Pred(terms[system]),{'s':m});term_ns+=time.perf_counter_ns()-tick
  pred=s.node(winner)['attrs'].get('name') if winner is not None else None
  predictions.append({'query_id':f"{q['speaker']}:{q['digit']}:{q['index']}",'speaker':q['speaker'],
   'digit':q['digit'],'index':q['index'],'prediction':int(pred) if pred is not None else None,
   'correct':pred==str(q['digit'])})
 return {'fold':fold,'system':system,'gallery_count':len(gallery),'query_count':len(queries),
  'gallery_digest':hashlib.sha256(json.dumps([(x['speaker'],x['digit'],x['index'],x['path']) for x in gallery],separators=(',',':')).encode()).hexdigest(),
  'predictions':predictions,'correct_count':sum(r['correct'] for r in predictions),
  'accuracy':sum(r['correct'] for r in predictions)/len(predictions),
  'per_speaker':{sp:{'correct':sum(r['correct'] for r in predictions if r['speaker']==sp),
    'queries':sum(r['speaker']==sp for r in predictions)} for sp in sorted({r['speaker'] for r in predictions})},
  'per_digit':{str(d):{'correct':sum(r['correct'] for r in predictions if r['digit']==d),
    'queries':sum(r['digit']==d for r in predictions)} for d in range(WAY)},
  'gallery_build_ns':gallery_build_ns,'matcher_wall_ns':time.perf_counter_ns()-matcher_start,
  'term_eval_ns':term_ns,'distance_comparison_cells':len(gallery)*len(queries)}
def training_worker(fold):
 from domains.contract_query import select_candidate_from_graph_evidence
 before=frozen();specs=specs_for(fold,'train');features,prep_ns=load_features([ROOT/x['path'] for x in specs])
 rows=[score_system(fold,specs,features,s) for s in SYSTEMS]
 proposals=[{'proposal_id':s,'proposal_label':s} for s in SYSTEMS]; evidence=[]
 rowmap={x['system']:x for x in rows}
 for system in SYSTEMS:
  for r in rowmap[system]['predictions']:
   evidence.append({'proposal_id':system,'probe_id':r['query_id'],
    'predicted':'correct' if r['correct'] else 'incorrect','expected':'correct'})
 primary=__import__('substrate_rs').Substrate();primary.add_node('ExperimentEpisode',{'experiment_id':f'fsdd_match_fold_{fold}','train_query_count':200})
 snapshot_tick=time.perf_counter_ns();snapshot=primary.snapshot();snapshot_ns=time.perf_counter_ns()-snapshot_tick
 fork_tick=time.perf_counter_ns();branch=snapshot.fork();fork_ns=time.perf_counter_ns()-fork_tick
 before_counts=[len(branch.nodes('CandidateProposal')),len(branch.nodes('CandidateEvidence'))]
 select_tick=time.perf_counter_ns();decision=select_candidate_from_graph_evidence(branch,f'fsdd_match_fold_{fold}',proposals,evidence);selection_ns=time.perf_counter_ns()-select_tick
 decision.pop('proposal_node',None);controls={};control_fork_ns=0
 for name,value in [('all_wrong','incorrect'),('tie','correct')]:
  t=time.perf_counter_ns();cb=snapshot.fork();control_fork_ns+=time.perf_counter_ns()-t
  ev=[{'proposal_id':s,'probe_id':f'{name}_{i}','predicted':value,'expected':'correct'} for s in SYSTEMS for i in range(4)]
  controls[name]=select_candidate_from_graph_evidence(cb,f'fsdd_{name}_fold_{fold}',proposals,ev).get('ok')
 chosen=decision.get('proposal_id');residual_tick=time.perf_counter_ns()
 rid=primary.add_node('ExperimentResidual',{'experiment_id':f'fsdd_match_fold_{fold}',
  'selected_proposal_id':chosen,'training_probe_count':decision.get('probe_count',0),
  'training_input_digest':hashlib.sha256(json.dumps([x['path'] for x in specs],separators=(',',':')).encode()).hexdigest()})
 residual_ns=time.perf_counter_ns()-residual_tick;after=frozen()
 return {'fold':fold,'pid':os.getpid(),'fold_spec':folds()[fold],'training_specs':specs,'training_rows':rows,
  'decision':decision,'selected_proposal_id':chosen,'controls':controls,'feature_prep_ns':prep_ns,
  'snapshot_ns':snapshot_ns,'branch_fork_ns':fork_ns,'control_branch_fork_ns':control_fork_ns,
  'graph_selection_ns':selection_ns,'residual_return_ns':residual_ns,
  'prediction_term_calls':sum(x['query_count'] for x in rows),'training_query_gallery_cells':sum(x['distance_comparison_cells'] for x in rows),
  'branch_node_counts':{'before':before_counts,'after':[len(branch.nodes('CandidateProposal')),len(branch.nodes('CandidateEvidence'))]},
  'primary_has_no_candidate_evidence':not primary.nodes('CandidateProposal') and not primary.nodes('CandidateEvidence'),
  'residual_returned':primary.has_node(rid) and primary.node(rid)['attrs']['selected_proposal_id']==chosen,
  'source_before':before,'source_after':after,'source_stable':before==after}
def score_worker(order):
 fold=order['fold'];before=frozen();specs=specs_for(fold,'heldout')
 gallery=[x for x in specs_for(fold,'train') if x['kind']=='gallery'];combined=gallery+specs
 features,prep_ns=load_features([ROOT[x['path']] for x in combined])
 rows=[score_system(fold,combined,features,s) for s in SYSTEMS];after=frozen()
 return {'fold':fold,'pid':os.getpid(),'fold_spec':folds()[fold],'heldout_specs':specs,'heldout_rows':rows,
  'feature_prep_ns':prep_ns,'prediction_term_calls':sum(x['query_count'] for x in rows),
  'heldout_query_gallery_cells':sum(x['distance_comparison_cells'] for x in rows),
  'source_before':before,'source_after':after,'source_stable':before==after}
def main():
 from domains.engine_provenance import build_is_stale,engine_provenance
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('stale native engine: '+'; '.join(stale))
 env={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}'}
 if sys.argv[1:]==['--lock']:
  if any(p.exists() for p in (LOCK,ORDERS,SCORES)):raise SystemExit('refusing to overwrite study artifacts')
  LOCK.write_text(json.dumps({'schema':'ThoughtexperimentFSDDMatcherSelectionV1Lock','sources':frozen(),
   'engine':engine_provenance(),'folds':folds(),'way':WAY,'gallery_per_speaker_digit':GALLERY_PER_SPEAKER,
   'train_queries_per_speaker_digit':TRAIN_QUERIES_PER_SPEAKER,'heldout_query_index_range':[TEST_QUERY_START,TEST_QUERY_START+TEST_QUERIES_PER_SPEAKER-1],
   'heldout_queries_per_speaker_digit':TEST_QUERIES_PER_SPEAKER,
   'feature_shape':[32,13],'systems':SYSTEMS},indent=2,sort_keys=True)+'\n');print(LOCK);return
 if not LOCK.exists() or frozen()!=json.loads(LOCK.read_text())['sources']:raise SystemExit('missing lock/source drift')
 if sys.argv[1:]==['--orders']:
  if ORDERS.exists() or SCORES.exists():raise SystemExit('orders/scores already exist')
  workers=[]
  for fold in range(FOLDS):
   p=subprocess.run([sys.executable,str(RUNNER),'--train-worker',str(fold)],cwd=ROOT,env=env,text=True,capture_output=True)
   if p.returncode:raise RuntimeError(p.stderr[-3000:])
   workers.append(json.loads(p.stdout.strip().splitlines()[-1]))
  ORDERS.write_text(json.dumps({'schema':'ThoughtexperimentFSDDMatcherSelectionV1Orders','lock_sha256':sha(LOCK),
   'workers':workers,'captured_utc':datetime.now(timezone.utc).isoformat(),'host':platform.platform()},indent=2,sort_keys=True)+'\n');print(ORDERS);return
 if sys.argv[1:]==['--score']:
  if not ORDERS.exists() or SCORES.exists():raise SystemExit('orders missing or scores exist')
  od=json.loads(ORDERS.read_text())
  if od['lock_sha256']!=sha(LOCK):raise SystemExit('orders/lock mismatch')
  workers=[]
  for order in od['workers']:
   p=subprocess.run([sys.executable,str(RUNNER),'--score-worker'],input=json.dumps(order),cwd=ROOT,env=env,text=True,capture_output=True)
   if p.returncode:raise RuntimeError(p.stderr[-3000:])
   workers.append(json.loads(p.stdout.strip().splitlines()[-1]))
  SCORES.write_text(json.dumps({'schema':'ThoughtexperimentFSDDMatcherSelectionV1Scores','orders_sha256':sha(ORDERS),'workers':workers},indent=2,sort_keys=True)+'\n');print(SCORES);return
 if sys.argv[1:2]==['--train-worker']:
  print(json.dumps(training_worker(int(sys.argv[2])),sort_keys=True,separators=(',',':')));return
 if sys.argv[1:2]==['--score-worker']:
  print(json.dumps(score_worker(json.load(sys.stdin)),sort_keys=True,separators=(',',':')));return
 raise SystemExit('use --lock, --orders, or --score')
if __name__=='__main__':main()
