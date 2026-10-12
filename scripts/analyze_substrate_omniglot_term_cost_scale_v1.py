#!/usr/bin/env python3
"""Independent analysis for the Omniglot graph-Term candidate/length scale factorial."""
import hashlib,importlib.util,json,statistics
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];STEM='omniglot_term_cost_scale_v1_20260929'
RAW=ROOT/f'evaluation/reports/{STEM}_raw.jsonl';LOCK=ROOT/f'evaluation/substrate_capability/{STEM}_lock.json';OUT=ROOT/f'evaluation/reports/{STEM}_analysis.json'
SYSTEMS=('ordered_dtw','pointset','deformable');WAYS=(5,10,20);LENGTHS=(16,32,64)
def load_runner():
 sp=importlib.util.spec_from_file_location('scale_runner',ROOT/'scripts/substrate_omniglot_term_cost_scale_v1.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
def episode_key(s):
 v={'alphabet':s['alphabet'],'labels':s['labels'],'exemplar_drawer':s['exemplar_drawer'],'query_drawer':s['query_drawer']}
 return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def ci(by_alpha,seed,draws):
 names=sorted(by_alpha);c=np.array([by_alpha[a][0] for a in names],float);n=np.array([by_alpha[a][1] for a in names],float);rng=np.random.default_rng(seed)
 ix=rng.integers(0,len(names),size=(draws,len(names)));den=n[ix].sum(1);num=c[ix].sum(1);v=np.divide(num,den,out=np.zeros_like(num),where=den>0)
 return [float(x) for x in np.quantile(v,[.025,.975])]
def main():
 records=[json.loads(x) for x in RAW.read_text().splitlines() if x.strip()];heads=[r for r in records if r['kind']=='header'];foots=[r for r in records if r['kind']=='footer'];workers=[r for r in records if r['kind']=='worker']
 data=heads[0];footer=foots[-1] if foots else {};locked=json.loads(LOCK.read_text())['locked_inputs'];specs=data['specs'];runner=load_runner()
 lookup={(w['way'],w['trajectory_points'],w['system'],w['episode']):w for w in workers}
 expected={(k,n,s,e) for k in WAYS for n in LENGTHS for s in SYSTEMS for e in range(100)}
 complete=len(workers)==2700 and len(lookup)==2700 and set(lookup)==expected
 panel_ok=True;errors=[]
 for spec in specs:
  panel_ok &= len(spec['labels'])==20 and len(set(spec['labels']))==20 and spec['exemplar_drawer']!=spec['query_drawer']
 for k,n,s,e in sorted(expected):
  w=lookup[(k,n,s,e)];spec=specs[e];labels=spec['labels'][:k];valid=True
  valid &= w['episode_key_sha256']==episode_key(spec) and w['alphabet']==spec['alphabet'] and w['labels']==labels
  valid &= w['query_count']==k and w['candidate_count']==k and w['distance_evaluations_expected']==k*k
  valid &= len(w['predictions'])==k and len(w['random_predictions'])==k
  valid &= all(p is None or p in labels for p in w['predictions']) and all(p in labels for p in w['random_predictions'])
  valid &= w['correct']==sum(p==y for p,y in zip(w['predictions'],labels))
  valid &= w['random_correct']==sum(p==y for p,y in zip(w['random_predictions'],labels))
  panel_ok &= bool(valid)
  if not valid:errors.append([k,n,s,e])
  peers=[lookup[(k,n,x,e)]['random_predictions'] for x in SYSTEMS]
  panel_ok &= len({tuple(x) for x in peers})==1
source_match=runner.source_inputs()==locked
checks={'complete_2700_cell_matrix':complete,'capture_header_footer_and_lock':len(heads)==1 and len(foots)==1 and data.get('locked_inputs')==locked and footer.get('worker_count')==2700,
 'current_source_runtime_dataset_and_prior_panel_match_lock':source_match,'runner_source_stable_at_completion':footer.get('source_stable') is True,
 'nested_episode_writer_and_prediction_oracles':bool(panel_ok),'independent_score_and_candidate_work_reconstruction':not errors and all(w['correct']==sum(a==b for a,b in zip(w['predictions'],w['labels'])) and w['distance_evaluations_expected']==w['way']**2 for w in workers)}
by_cell={};alphas=sorted({x['alphabet'] for x in specs})
for ki,k in enumerate(WAYS):
 for ni,n in enumerate(LENGTHS):
  for si,s in enumerate(SYSTEMS):
   z=[lookup[(k,n,s,e)] for e in range(100)];counts={a:[0,0] for a in alphas}
   for w in z:counts[w['alphabet']][0]+=w['correct'];counts[w['alphabet']][1]+=k
   correct=sum(w['correct'] for w in z);total=sum(w['query_count'] for w in z);rand=sum(w['random_correct'] for w in z)
   walls=sorted(w['wall_ns']/1e6 for w in z);cpus=sorted(w['process_cpu_ns']/1e6 for w in z)
   by_cell[f'{s}:k{k}:L{n}']={'system':s,'way':k,'trajectory_points':n,'correct':correct,'total':total,'accuracy':correct/total,'chance_accuracy':1/k,
    'alphabet_cluster_bootstrap_95ci':ci(counts,locked['random_seed']+100*ki+10*ni+si,locked['bootstrap_draws']),
    'random_correct':rand,'random_accuracy':rand/total,'median_worker_wall_ms':statistics.median(walls),'p95_worker_wall_ms':walls[int(.95*(len(walls)-1))],
    'median_worker_cpu_ms':statistics.median(cpus),'p95_worker_cpu_ms':cpus[int(.95*(len(cpus)-1))],'peak_rss_bytes':max(w['peak_rss_bytes'] for w in z),
    'candidate_distance_evaluations_expected_per_episode':k*k,'candidate_distance_evaluations_expected_total':100*k*k}
diffs={}
for k in WAYS:
 for n in LENGTHS:
  for a,b in (('ordered_dtw','pointset'),('ordered_dtw','deformable'),('pointset','deformable')):
   ca={x:[0,0] for x in alphas}
   for e,spec in enumerate(specs):
    ca[spec['alphabet']][0]+=lookup[(k,n,a,e)]['correct']-lookup[(k,n,b,e)]['correct'];ca[spec['alphabet']][1]+=k
   diffs[f'{a}-minus-{b}:k{k}:L{n}']={'accuracy_difference':by_cell[f'{a}:k{k}:L{n}']['accuracy']-by_cell[f'{b}:k{k}:L{n}']['accuracy'],
    'alphabet_cluster_bootstrap_95ci':ci(ca,locked['random_seed']+7000+k*10+n+len(diffs),locked['bootstrap_draws'])}
out={'run_id':data['run_id'],'checks':checks,'passed_checks':sum(checks.values()),'total_checks':len(checks),'integrity_pass':all(checks.values()),
 'episode_count':len(specs),'alphabet_count':len(alphas),'worker_count':len(workers),'conditions':by_cell,'paired_system_differences':diffs,
 'feature_prep':data['feature_prep'],'total_run_wall_ns':footer.get('run_wall_ns'),'total_run_process_cpu_ns':footer.get('run_process_cpu_ns'),
 'claim_boundary':'100 reused Omniglot episodes; candidate count 5/10/20; trajectory resolution 16/32/64; three graph-Term systems. Alphabet-clustered uncertainty. k-squared candidate distance count is derived from Argmax-by-candidate structure, not a native operation counter.'}
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':checks,'passed_checks':out['passed_checks'],'total_checks':len(checks),
 'conditions':{k:{q:v for q,v in d.items() if q!='alphabet_cluster_bootstrap_95ci'} for k,d in by_cell.items()},'total_wall_s':footer.get('run_wall_ns',0)/1e9},indent=2))
if not out['integrity_pass']:raise SystemExit('Omniglot scaling integrity gate failed')
if __name__=='__main__':main()
