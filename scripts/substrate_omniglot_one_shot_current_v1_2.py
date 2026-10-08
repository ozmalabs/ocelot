#!/usr/bin/env python3
"""Locked Omniglot one-shot evaluation through the current substrate graph-Term route."""
from __future__ import annotations
import hashlib,json,os,platform,random,statistics,sys,time,resource
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
import numpy as np
import substrate_rs as srs
from domains import glyph_motor_world as gm
from domains import omniglot_world as ow
from domains.recognition_graph import predict_synth_term,predict_pointset_term,predict_deform_term
from domains.engine_provenance import engine_provenance

STEM='omniglot_one_shot_current_v1_2_20260929'
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_OMNIGLOT_ONE_SHOT_CURRENT_V1_2_PREREG_20260929.md'
LOCK=ROOT/f'evaluation/substrate_capability/{STEM}_lock.json'
RAW=ROOT/f'evaluation/reports/{STEM}_raw.jsonl'
ANALYZER=ROOT/'scripts/analyze_substrate_omniglot_one_shot_current_v1_2.py'
DATA=Path(ow.split_dir('evaluation'))
WAY=20;EPISODES=100;N_POINTS=64;SPEC_SEED=7;BOOT_SEED=1709;BOOT_DRAWS=10000
SYSTEMS=('ordered_dtw','pointset','deformable')

def sha_file(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for block in iter(lambda:f.read(1<<20),b''):h.update(block)
 return h.hexdigest()
def dataset_manifest():
 h=hashlib.sha256();files=sorted(p for p in DATA.rglob('*') if p.is_file())
 for p in files:
  rel=p.relative_to(DATA).as_posix().encode();digest=bytes.fromhex(sha_file(p));h.update(len(rel).to_bytes(4,'big'));h.update(rel);h.update(digest)
 return {'file_count':len(files),'manifest_sha256':h.hexdigest()}
def source_inputs():
 from substrate_rs import _native
 paths=('domains/recognition_graph.py','domains/glyph_motor_world.py','domains/omniglot_world.py','domains/dataset_root.py','runners/dsl/src/term.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/python/substrate_rs/__init__.py')
 return {'protocol_sha256':sha_file(PROTOCOL),'runner_sha256':sha_file(__file__),'analyzer_sha256':sha_file(ANALYZER),
  'source_sha256':{p:sha_file(ROOT/p) for p in paths},'native_extension_sha256':sha_file(Path(_native.__file__).resolve()),
  'dataset':dataset_manifest(),'engine_provenance':engine_provenance(),'python':sys.version,'platform':platform.platform(),
  'episode_count':EPISODES,'way':WAY,'trajectory_points':N_POINTS,'episode_seed':SPEC_SEED,'bootstrap_seed':BOOT_SEED,'bootstrap_draws':BOOT_DRAWS,'systems':list(SYSTEMS)}
class Pred:
 __slots__=('_json',)
 def __init__(self,term):self._json=term

def make_specs():
 alphs=ow.alphabets('evaluation');by_alph={a:ow.characters(a,'evaluation') for a in alphs};by_alph={a:c for a,c in by_alph.items() if len(c)>=WAY};names=sorted(by_alph)
 rng=np.random.default_rng(SPEC_SEED);specs=[]
 for i in range(EPISODES):
  ai=int(rng.integers(len(names)));alphabet=names[ai];chars=by_alph[alphabet];idx=rng.permutation(len(chars))[:WAY]
  ex=int(rng.integers(20));q=int(rng.integers(20))
  while q==ex:q=int(rng.integers(20))
  chosen=[chars[int(j)] for j in idx]
  labels=[os.path.relpath(c,DATA).replace(os.sep,'/') for c in chosen]
  specs.append({'episode':i,'alphabet':alphabet,'classes':chosen,'labels':labels,'exemplar_drawer':ex+1,'query_drawer':q+1})
 return specs

def main():
 if sys.argv[1:]==['--lock']:
  LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps({'locked_inputs':source_inputs()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return
 if sys.argv[1:]:raise SystemExit('usage: script [--lock]')
 locked=source_inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing/stale source lock')
 if RAW.exists():raise SystemExit(f'refusing to overwrite {RAW}')
 specs=make_specs();paths={(str(c),d) for e in specs for c in e['classes'] for d in (e['exemplar_drawer'],e['query_drawer'])}
 cache={};prep_wall=time.perf_counter_ns();prep_cpu=time.process_time_ns()
 for c,d in sorted(paths):
  files=ow.drawings(c);matches=[p for p in files if Path(p).stem.rsplit('_',1)[-1]==f'{d:02d}']
  if len(matches)!=1:raise RuntimeError(f'expected one drawer {d} in {c}; found {len(matches)}')
  cache[(c,d)]=ow.trajectory(matches[0],N_POINTS,per_stroke=True)
 feature_prep={'wall_ns':time.perf_counter_ns()-prep_wall,'process_cpu_ns':time.process_time_ns()-prep_cpu,'unique_trajectories':len(cache)}
 random_rng=random.Random(BOOT_SEED);workers=[]
 terms={'ordered_dtw':predict_synth_term(),'pointset':predict_pointset_term(),'deformable':predict_deform_term()}
 raw_handle=RAW.open('x',encoding='utf-8')
 raw_handle.write(json.dumps({'kind':'header','run_id':STEM,'locked_inputs':locked,'specs':specs,'feature_prep':feature_prep},separators=(',',':'),sort_keys=True)+'\n');raw_handle.flush()
 all_start=time.perf_counter_ns();all_cpu=time.process_time_ns()
 for system in SYSTEMS:
  term=terms[system]
  for spec in specs:
   t0=time.perf_counter_ns();c0=time.process_time_ns();s=srs.Substrate();candidate_nodes=[]
   for c,label,d in zip(spec['classes'],spec['labels'],[spec['exemplar_drawer']]*WAY):
    node=s.add_node('Concept',{'name':label,gm.WORD_ATTR:1.0});s.set_attr(node,gm.SYNTH_ATTR,cache[(c,d)].tolist());candidate_nodes.append(node)
   predictions=[];random_predictions=[]
   for c,label in zip(spec['classes'],spec['labels']):
    mark=s.add_node('Mark',{gm.MARK_ATTR:cache[(c,spec['query_drawer'])].tolist()})
    winner=s.evaluate(Pred(term),{'s':mark});pred=s.node(winner)['attrs'].get('name') if winner is not None else None
    predictions.append(pred);random_predictions.append(spec['labels'][random_rng.randrange(WAY)])
   row={'system':system,'episode':spec['episode'],'alphabet':spec['alphabet'],'labels':spec['labels'],'predictions':predictions,'random_predictions':random_predictions,
    'correct':sum(a==b for a,b in zip(predictions,spec['labels'])),'random_correct':sum(a==b for a,b in zip(random_predictions,spec['labels'])),
    'query_count':len(spec['labels']),'candidate_count':len(candidate_nodes),'all_predictions_valid':all(p in spec['labels'] for p in predictions),
    'episode_key_sha256':hashlib.sha256(json.dumps({'alphabet':spec['alphabet'],'labels':spec['labels'],'exemplar_drawer':spec['exemplar_drawer'],'query_drawer':spec['query_drawer']},sort_keys=True,separators=(',',':')).encode()).hexdigest(),
    'exemplar_drawer':spec['exemplar_drawer'],'query_drawer':spec['query_drawer'],'wall_ns':time.perf_counter_ns()-t0,'process_cpu_ns':time.process_time_ns()-c0,
    'peak_rss_bytes':int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1024 if sys.platform.startswith('linux') else 1))}
   workers.append(row);RAW.parent.mkdir(parents=True,exist_ok=True)
   raw_handle.write(json.dumps({'kind':'worker',**row},separators=(',',':'),sort_keys=True)+'\n');raw_handle.flush()
   print(f"worker={len(workers)}/{EPISODES*len(SYSTEMS)} system={system} episode={spec['episode']+1}/{EPISODES}",flush=True)
 stable=source_inputs()==locked
 raw_handle.write(json.dumps({'kind':'footer','run_wall_ns':time.perf_counter_ns()-all_start,'run_process_cpu_ns':time.process_time_ns()-all_cpu,'source_stable':stable},separators=(',',':'),sort_keys=True)+'\n');raw_handle.close()
 if not stable:raise SystemExit('source drift during run')
if __name__=='__main__':main()
