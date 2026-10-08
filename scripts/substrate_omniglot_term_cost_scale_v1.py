#!/usr/bin/env python3
"""Source-locked Omniglot graph-Term accuracy/cost scale factorial."""
from __future__ import annotations
import hashlib,json,os,platform,random,sys,time,resource
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
import numpy as np
import substrate_rs as srs
from domains import glyph_motor_world as gm,omniglot_world as ow
from domains.recognition_graph import predict_synth_term,predict_pointset_term,predict_deform_term
from domains.engine_provenance import engine_provenance
STEM='omniglot_term_cost_scale_v1_20260929';PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_OMNIGLOT_TERM_COST_SCALE_V1_PREREG_20260929.md'
LOCK=ROOT/f'evaluation/substrate_capability/{STEM}_lock.json';RAW=ROOT/f'evaluation/reports/{STEM}_raw.jsonl';ANALYZER=ROOT/'scripts/analyze_substrate_omniglot_term_cost_scale_v1.py'
BASE_RAW=ROOT/'evaluation/reports/omniglot_one_shot_current_v1_2_20260929_raw.jsonl';BASE_LOCK=ROOT/'evaluation/substrate_capability/omniglot_one_shot_current_v1_2_20260929_lock.json'
DATA=Path(ow.split_dir('evaluation'));WAYS=(5,10,20);LENGTHS=(16,32,64);SYSTEMS=('ordered_dtw','pointset','deformable');BOOT_SEED=2718;BOOT_DRAWS=10000
def sha_file(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def dataset_manifest():
 h=hashlib.sha256();files=sorted(p for p in DATA.rglob('*') if p.is_file())
 for p in files:
  rel=p.relative_to(DATA).as_posix().encode();h.update(len(rel).to_bytes(4,'big'));h.update(rel);h.update(bytes.fromhex(sha_file(p)))
 return {'file_count':len(files),'manifest_sha256':h.hexdigest()}
def source_inputs():
 from substrate_rs import _native
 paths=('domains/recognition_graph.py','domains/glyph_motor_world.py','domains/omniglot_world.py','domains/dataset_root.py','runners/dsl/src/term.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/python/substrate_rs/__init__.py')
 return {'protocol_sha256':sha_file(PROTOCOL),'runner_sha256':sha_file(__file__),'analyzer_sha256':sha_file(ANALYZER),
  'source_sha256':{p:sha_file(ROOT/p) for p in paths},'native_extension_sha256':sha_file(Path(_native.__file__).resolve()),
  'dataset':dataset_manifest(),'base_capture_sha256':sha_file(BASE_RAW),'base_lock_sha256':sha_file(BASE_LOCK),
  'engine_provenance':engine_provenance(),'python':sys.version,'platform':platform.platform(),
  'ways':list(WAYS),'trajectory_lengths':list(LENGTHS),'systems':list(SYSTEMS),'episode_count':100,'random_seed':BOOT_SEED,'bootstrap_draws':BOOT_DRAWS}
def episode_key(s):
 v={'alphabet':s['alphabet'],'labels':s['labels'],'exemplar_drawer':s['exemplar_drawer'],'query_drawer':s['query_drawer']}
 return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
class Pred:
 __slots__=('_json',)
 def __init__(self,term):self._json=term
def main():
 if sys.argv[1:]==['--lock']:
  LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps({'locked_inputs':source_inputs()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return
 if sys.argv[1:]:raise SystemExit('usage: script [--lock]')
 locked=source_inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing/stale lock')
 if RAW.exists():raise SystemExit(f'refusing to overwrite {RAW}')
 lines=[json.loads(x) for x in BASE_RAW.read_text().splitlines() if x.strip()];base=[x for x in lines if x.get('kind')=='header']
 if len(base)!=1:raise SystemExit('base panel header missing/duplicated')
 specs=base[0]['specs']
 if len(specs)!=100:raise SystemExit('base panel must contain exactly 100 episodes')
 terms={'ordered_dtw':predict_synth_term(),'pointset':predict_pointset_term(),'deformable':predict_deform_term()}
 need={(str(c),d,n) for ep in specs for c in ep['classes'] for d in (ep['exemplar_drawer'],ep['query_drawer']) for n in LENGTHS}
 cache={};prep0=time.perf_counter_ns();prepc=time.process_time_ns()
 for c,d,n in sorted(need):
  fs=ow.drawings(c);match=[p for p in fs if Path(p).stem.rsplit('_',1)[-1]==f'{d:02d}']
  if len(match)!=1:raise RuntimeError(f'expected one drawing for {c} drawer {d}')
  cache[(c,d,n)]=ow.trajectory(match[0],n,per_stroke=True)
 prep={'wall_ns':time.perf_counter_ns()-prep0,'process_cpu_ns':time.process_time_ns()-prepc,'unique_trajectories':len(cache)}
 fh=RAW.open('x',encoding='utf-8');fh.write(json.dumps({'kind':'header','run_id':STEM,'locked_inputs':locked,'specs':specs,'feature_prep':prep},separators=(',',':'),sort_keys=True)+'\n');fh.flush()
 all0=time.perf_counter_ns();allc=time.process_time_ns();nrows=0
 for k in WAYS:
  for n in LENGTHS:
   for e,spec in enumerate(specs):
    labels=spec['labels'][:k];classes=spec['classes'][:k];key=episode_key(spec)
    rng=random.Random(BOOT_SEED+e*1009+k*31+n);random_preds=[labels[rng.randrange(k)] for _ in labels]
    for system in SYSTEMS:
     t0=time.perf_counter_ns();c0=time.process_time_ns();s=srs.Substrate()
     for c,label in zip(classes,labels):
      node=s.add_node('Concept',{'name':label,gm.WORD_ATTR:1.0});s.set_attr(node,gm.SYNTH_ATTR,cache[(c,spec['exemplar_drawer'],n)].tolist())
     preds=[]
     for c in classes:
      mark=s.add_node('Mark',{gm.MARK_ATTR:cache[(c,spec['query_drawer'],n)].tolist()});winner=s.evaluate(Pred(terms[system]),{'s':mark})
      preds.append(s.node(winner)['attrs'].get('name') if winner is not None else None)
     row={'kind':'worker','system':system,'episode':e,'episode_key_sha256':key,'alphabet':spec['alphabet'],'way':k,'trajectory_points':n,
      'labels':labels,'predictions':preds,'random_predictions':random_preds,'correct':sum(a==b for a,b in zip(preds,labels)),
      'random_correct':sum(a==b for a,b in zip(random_preds,labels)),'query_count':k,'candidate_count':k,'distance_evaluations_expected':k*k,
      'wall_ns':time.perf_counter_ns()-t0,'process_cpu_ns':time.process_time_ns()-c0,
      'peak_rss_bytes':int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1024 if sys.platform.startswith('linux') else 1))}
     fh.write(json.dumps(row,separators=(',',':'),sort_keys=True)+'\n');fh.flush();nrows+=1
     if nrows%100==0:print(f'worker={nrows}/2700 way={k} points={n} system={system} episode={e+1}',flush=True)
 stable=source_inputs()==locked
 fh.write(json.dumps({'kind':'footer','worker_count':nrows,'run_wall_ns':time.perf_counter_ns()-all0,'run_process_cpu_ns':time.process_time_ns()-allc,'source_stable':stable},separators=(',',':'),sort_keys=True)+'\n');fh.close()
 if not stable:raise SystemExit('source drift during run')
 print(f'completed {nrows}/2700 rows; source_stable={stable}',flush=True)
if __name__=='__main__':main()
