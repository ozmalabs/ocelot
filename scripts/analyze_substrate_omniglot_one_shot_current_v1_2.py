#!/usr/bin/env python3
"""Independent score and cluster-bootstrap analysis for Omniglot one-shot capture."""
import hashlib,importlib.util,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
STEM='omniglot_one_shot_current_v1_2_20260929'
RAW=ROOT/f'evaluation/reports/{STEM}_raw.jsonl';LOCK=ROOT/f'evaluation/substrate_capability/{STEM}_lock.json';OUT=ROOT/f'evaluation/reports/{STEM}_analysis.json'
SYSTEMS=('ordered_dtw','pointset','deformable')

def load_runner():
 spec=importlib.util.spec_from_file_location('omniglot_runner',ROOT/'scripts/substrate_omniglot_one_shot_current_v1_2.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def episode_key(spec):
 payload={'alphabet':spec['alphabet'],'labels':spec['labels'],'exemplar_drawer':spec['exemplar_drawer'],'query_drawer':spec['query_drawer']}
 return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def bootstrap_ci(by_alpha,seed,draws):
 names=sorted(by_alpha);correct=np.array([by_alpha[a][0] for a in names],dtype=float);total=np.array([by_alpha[a][1] for a in names],dtype=float)
 rng=np.random.default_rng(seed);sample=rng.integers(0,len(names),size=(draws,len(names)))
 den=total[sample].sum(axis=1);num=correct[sample].sum(axis=1);values=np.divide(num,den,out=np.zeros_like(num),where=den>0)
 return [float(x) for x in np.quantile(values,[.025,.975])]

def main():
 records=[json.loads(x) for x in RAW.read_text().splitlines() if x.strip()];heads=[x for x in records if x['kind']=='header'];workers=[x for x in records if x['kind']=='worker'];foots=[x for x in records if x['kind']=='footer'];data=heads[0];footer=foots[-1] if foots else {};locked=json.loads(LOCK.read_text())['locked_inputs'];specs=data['specs'];runner=load_runner()
 byspec={x['episode']:x for x in specs};expected={(s,e) for s in SYSTEMS for e in range(100)};keys={(w['system'],w['episode']) for w in workers}
 integrity=True;errors=[];matrix={}
 for e,spec in byspec.items():
  integrity &= len(spec['labels'])==20 and len(set(spec['labels']))==20 and spec['exemplar_drawer']!=spec['query_drawer']
  integrity &= spec['episode'] in range(100) and len(spec['classes'])==20
  integrity &= episode_key(spec)==next((w['episode_key_sha256'] for w in workers if w['episode']==e),None)
 for w in workers:
  spec=byspec.get(w['episode']);valid=spec is not None and w['episode_key_sha256']==episode_key(spec)
  valid &= w['alphabet']==spec['alphabet'] and w['labels']==spec['labels']
  valid &= w['exemplar_drawer']==spec['exemplar_drawer'] and w['query_drawer']==spec['query_drawer']
  valid &= w['query_count']==20 and w['candidate_count']==20 and len(w['predictions'])==20 and len(w['random_predictions'])==20
  valid &= w['all_predictions_valid'] and all(p in spec['labels'] for p in w['predictions'])
  valid &= all(p in spec['labels'] for p in w['random_predictions'])
  valid &= w['correct']==sum(p==y for p,y in zip(w['predictions'],spec['labels']))
  valid &= w['random_correct']==sum(p==y for p,y in zip(w['random_predictions'],spec['labels']))
  integrity &= bool(valid)
  if not valid:errors.append({'system':w.get('system'),'episode':w.get('episode')})
  matrix[(w['system'],w['episode'])]=w
 for e in range(100):
  integrity &= len({matrix[(s,e)]['episode_key_sha256'] for s in SYSTEMS if (s,e) in matrix})==1
 current_sources=runner.source_inputs()
 checks={'complete_system_episode_matrix':len(workers)==300 and keys==expected,
  'capture_matches_preregistered_lock':data.get('locked_inputs')==locked and len(heads)==1 and len(foots)==1,
  'current_source_and_dataset_inputs_match_lock':current_sources==locked,
  'runner_observed_source_stability':footer.get('source_stable') is True,
  'episode_design_and_shared_inputs_valid':bool(integrity),
  'independent_prediction_and_accuracy_reconstruction':not errors and len(workers)==300}
 alphabets=sorted({x['alphabet'] for x in specs});rows={};by_system={}
 for si,system in enumerate(SYSTEMS):
  a_counts={a:[0,0] for a in alphabets};episode_scores=[];all_correct=all_total=0
  for e in range(100):
   w=matrix[(system,e)];spec=byspec[e];all_correct+=w['correct'];all_total+=20;a_counts[spec['alphabet']][0]+=w['correct'];a_counts[spec['alphabet']][1]+=20
   episode_scores.append({'episode':e,'alphabet':spec['alphabet'],'correct':w['correct'],'total':20,'accuracy':w['correct']/20})
  random_correct=sum(matrix[(system,e)]['random_correct'] for e in range(100));random_total=all_total
  ci=bootstrap_ci(a_counts,locked['bootstrap_seed']+si,locked['bootstrap_draws'])
  by_system[system]={'correct':all_correct,'total':all_total,'accuracy':all_correct/all_total,'alphabet_cluster_bootstrap_95ci':ci,
   'random_correct':random_correct,'random_total':random_total,'random_accuracy':random_correct/random_total,'chance_accuracy':1/20,
   'median_episode_accuracy':float(np.median([x['accuracy'] for x in episode_scores])),
   'median_episode_wall_ms':float(np.median([matrix[(system,e)]['wall_ns'] for e in range(100)])/1e6),
   'median_episode_cpu_ms':float(np.median([matrix[(system,e)]['process_cpu_ns'] for e in range(100)])/1e6),
   'peak_rss_bytes':max(matrix[(system,e)]['peak_rss_bytes'] for e in range(100)),
   'by_alphabet':{a:{'correct':c,'total':n,'accuracy':c/n if n else None} for a,(c,n) in a_counts.items()},
   'episode_scores':episode_scores}
  rows[system]=a_counts
 deltas={}
 for left,right in (('ordered_dtw','pointset'),('ordered_dtw','deformable'),('pointset','deformable')):
  d={a:[rows[left][a][0]-rows[right][a][0],rows[left][a][1]] for a in alphabets}
  deltas[f'{left}-minus-{right}']={'accuracy_difference':by_system[left]['accuracy']-by_system[right]['accuracy'],
   'alphabet_cluster_bootstrap_95ci':bootstrap_ci(d,locked['bootstrap_seed']+100+len(deltas),locked['bootstrap_draws'])}
 out={'run_id':data['run_id'],'checks':checks,'passed_checks':sum(checks.values()),'total_checks':len(checks),'integrity_pass':all(checks.values()),
  'episode_count':len(specs),'system_count':len(SYSTEMS),'worker_count':len(workers),'alphabet_count':len(alphabets),'systems':by_system,'paired_system_differences':deltas,
  'feature_prep':data['feature_prep'],'total_run_wall_ns':footer.get('run_wall_ns'),'total_run_process_cpu_ns':footer.get('run_process_cpu_ns'),
  'claim_boundary':'100 deterministic 20-way one-shot episodes from one Omniglot evaluation split; alphabet-clustered uncertainty; host-side trajectory loading/caching plus graph-Term substrate recognition. No training or task-family generality claim.'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':checks,'passed_checks':out['passed_checks'],'total_checks':len(checks),'alphabet_count':len(alphabets),
  'systems':{k:{q:v for q,v in x.items() if q not in ('by_alphabet','episode_scores')} for k,x in by_system.items()},'paired_system_differences':deltas},indent=2))
 if not out['integrity_pass']:raise SystemExit('Omniglot integrity gate failed')
if __name__=='__main__':main()
