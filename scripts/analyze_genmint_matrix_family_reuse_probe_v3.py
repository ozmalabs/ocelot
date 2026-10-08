#!/usr/bin/env python3
"""Independent analysis of the extended-horizon GenMint capture."""
import hashlib, json, random, statistics
from collections import defaultdict, Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_genmint_matrix_family_reuse_v3_20260926.json'
LOCK=ROOT/'evaluation/substrate_capability/genmint_matrix_family_reuse_v3_lock_20260926.json'
MAPS={'prior_matrix':[1,1,0,2],'shearA':[1,0,1,1],'shearB':[1,1,0,1],'shearC':[1,2,0,1],'axis_swap':[0,1,1,0],'quarter_turn':[0,1,-1,0]}
POINTS=[(0,0),(1,0),(0,1),(1,1),(2,0),(0,2)]
LAYOUTS={'adjacent_01':[0,1,4],'opposite_03':[0,3,4],'adjacent_12':[1,2,5]}
KS=(0,4,16); REPS=3; SEED=20260926

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def heldouts():
 rng=random.Random(SEED);tasks=[];seen=set()
 while len(tasks)<16:
  pts=tuple((rng.randrange(0,8),rng.randrange(0,8)) for _ in range(4))
  if len(set(pts))<4 or pts in seen:continue
  if len({p[0] for p in pts})<3 or len({p[1] for p in pts})<3:continue
  area=(pts[1][0]-pts[0][0])*(pts[2][1]-pts[0][1])-(pts[2][0]-pts[0][0])*(pts[1][1]-pts[0][1])
  if area==0:continue
  seen.add(pts);tasks.append(list(pts))
 return tasks
HELD=heldouts()
def predict(x,step,matrix):
 tr=next((t for t in step['transforms'] if t.get('generator')),None)
 if tr is None:return {'route':'no_generator_transform','selected_generator':None,'matrix':None,'predictions':None,'correct':None}
 after=step['linear_generators'];gen=next((g for g in after if g['name']==tr['generator']),None)
 if gen is None:return {'route':'other_seed_generator','selected_generator':tr['generator'],'matrix':None,'predictions':None,'correct':None}
 initial={g['name'] for g in x['initial_linear_generators']};trained={g['name']:g for g in x['train']['linear_generators']};before={g['name'] for g in step['linear_generators_before']};after_names={g['name'] for g in after}
 if tr['generator'] in set(trained)-initial:route='reused_expected_training' if gen['matrix']==matrix else 'reused_other_training'
 elif tr['generator'] in initial:route='preexisting_linear'
 elif tr['generator'] in after_names-before:route='minted_during_application'
 elif tr['generator'] in before-initial:route='reused_application_linear'
 elif tr['generator'] in trained:route='reused_other_training'
 else:route='unclassified'
 cur=[list(r) for r in step['base']];a,b,c,d=gen['matrix']
 for _ in range(max(1,int(tr.get('k',1)))):
  mins=[min(r[j] for r in cur) for j in (1,2)]
  cur=[[r[0],a*(r[1]-mins[0])+b*(r[2]-mins[1]),c*(r[1]-mins[0])+d*(r[2]-mins[1]),r[3]] for r in cur]
 for residual in tr.get('transforms') or []:
  for row in cur:
   if residual.get('pred') is not None and residual['pred']!=row[0]:continue
   dim=residual.get('dim')
   if residual.get('kind')=='shift' and dim in (1,2):row[dim]+=residual.get('delta',0)
   elif residual.get('kind')=='subst' and row[3]==residual.get('from'):row[3]=residual.get('to')
 return {'route':route,'selected_generator':tr['generator'],'matrix':gen['matrix'],'predictions':cur,'correct':[p==q for p,q in zip(cur,step['target'])]}
def timing(x):return x['train']['closure_seconds']+sum(a['closure_seconds'] for a in x['applications'])
def expected_rows(points,m):
 a,b,c,d=m; bases=[];targets=[]
 for i,(r,q) in enumerate(points):
  pred='p0' if i%2==0 else 'p1';bases.append([pred,r,q,'red']);targets.append([pred,a*r+b*q,c*r+d*q,'red'])
 return bases,targets
def main():
 d=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text()); workers=d['workers']
 checks={'raw_embedded_lock_matches':d['locked_inputs']==lock,'raw_lock_sha_matches':d['lock_sha256']==sha(LOCK),'worker_count_324':len(workers)==324,'no_worker_failures':not d['worker_failures'],'unique_worker_pids':len({w.get('pid') for w in workers})==324,'protocol_tag':d['protocol']=='SUBSTRATE_GENMINT_MATRIX_FAMILY_REUSE_V3','runner_hash_matches':lock['locked_inputs']['files_sha256']['scripts/genmint_matrix_family_reuse_probe_v3.py']==sha(ROOT/'scripts/genmint_matrix_family_reuse_probe_v3.py'),'locked_analyzer_hash_matches':lock['locked_inputs']['files_sha256']['scripts/analyze_genmint_matrix_family_reuse_probe_v3.py']==sha(ROOT/'scripts/analyze_genmint_matrix_family_reuse_probe_v3.py'),'native_hash_matches':d['native']['sha256']==sha(Path(d['native']['path']))}
 jobs=[(mn,ln,en,k) for mn in MAPS for ln in LAYOUTS for en in (0,1) for k in KS];rng=random.Random(SEED);expected_schedule=[]
 for rep in range(1,REPS+1):
  q=jobs.copy();rng.shuffle(q);expected_schedule.append([[*z,rep] for z in q])
 checks['exact_randomized_schedule']=d['schedule']==expected_schedule
 cells=defaultdict(list); scores=[];input_ok=True
 for x in workers:
  if 'worker_failure' in x:continue
  m=MAPS[x['matrix_name']];layout=set(LAYOUTS[x['layout']]);base=[];target=[]
  for i,(r,c) in enumerate(POINTS):
   pred='p0' if i in layout else 'p1';a,b,d0,e=m;base.append([pred,r,c,'red']);target.append([pred,a*r+b*c,d0*r+e*c,'red'])
  input_ok &= x['matrix']==m and x['p0_indices']==sorted(layout) and x['training_base']==base and x['training_target']==target and len(x['applications'])==x['K']
  for j,st in enumerate(x['applications']):
   hb,ht=expected_rows(HELD[j],m)
   input_ok &= st['base']==hb and st['target']==ht and st['task_index']==j
   q=predict(x,st,m);scores.append({'matrix_name':x['matrix_name'],'layout':x['layout'],'enabled':x['enabled'],'K':x['K'],'replicate':x['replicate'],'task_index':j,**q})
  cells[(x['matrix_name'],x['layout'],x['enabled'],x['K'])].append(x)
 checks['independent_input_reconstruction']=bool(input_ok)
 checks['balanced_108_cells']=len(cells)==108 and all(len(v)==REPS for v in cells.values())
 checks['balanced_schedules']=len(d['schedule'])==REPS and all(len(s)==108 for s in d['schedule'])
 checks['no_unclassified_routes']=all(z['route']!='unclassified' for z in scores)
 checks['replicate_task_outcome_determinism']=all(len({json.dumps((w['train']['status'],w['train']['linear_generators'],w['train']['quanta_delta'],[(a['status'],a['transforms'],a['quanta_delta']) for a in w['applications']],[(z['route'],z['correct']) for z in scores if (z['matrix_name'],z['layout'],z['enabled'],z['K'],z['replicate'])==(w['matrix_name'],w['layout'],w['enabled'],w['K'],w['replicate'])]),sort_keys=True) for w in vs})==1 for vs in cells.values())
 # Matched costs and stage-separated summaries.
 index={(w['matrix_name'],w['layout'],w['K'],w['replicate'],w['enabled']):w for w in workers if 'worker_failure' not in w};paired=[]
 for mn in MAPS:
  for ln in LAYOUTS:
   for k in KS:
    for rep in range(1,REPS+1):
     on=index[(mn,ln,k,rep,True)];off=index[(mn,ln,k,rep,False)]
     paired.append({'matrix_name':mn,'layout':ln,'K':k,'replicate':rep,'enabled_train_s':on['train']['closure_seconds'],'disabled_train_s':off['train']['closure_seconds'],'enabled_app_s':sum(a['closure_seconds'] for a in on['applications']),'disabled_app_s':sum(a['closure_seconds'] for a in off['applications']),'enabled_total_s':timing(on),'disabled_total_s':timing(off),'enabled_quanta':on['total_quanta_delta'],'disabled_quanta':off['total_quanta_delta'],'enabled_rss_kib':on['peak_rss_kib'],'disabled_rss_kib':off['peak_rss_kib'],'acquired':any(g['matrix']==MAPS[mn] for g in on['train']['linear_generators'])})
 summaries=[]
 for k in KS:
  ps=[p for p in paired if p['K']==k]
  median=lambda key:statistics.median(p[key] for p in ps)
  apps=[z for z in scores if z['K']==k]
  exact=[z for z in apps if z['route']=='reused_expected_training']
  summaries.append({'K':k,'pairs':len(ps),'acquired_enabled_pairs':sum(p['acquired'] for p in ps),'enabled_training_median_ms':1000*median('enabled_train_s'),'disabled_training_median_ms':1000*median('disabled_train_s'),'enabled_application_only_median_ms':1000*median('enabled_app_s'),'disabled_application_only_median_ms':1000*median('disabled_app_s'),'enabled_total_median_ms':1000*median('enabled_total_s'),'disabled_total_median_ms':1000*median('disabled_total_s'),'enabled_faster_pairs':sum(p['enabled_total_s']<p['disabled_total_s'] for p in ps),'enabled_quanta_median':median('enabled_quanta'),'disabled_quanta_median':median('disabled_quanta'),'enabled_rss_median_kib':median('enabled_rss_kib'),'disabled_rss_median_kib':median('disabled_rss_kib'),'expected_training_reuse_calls':len(exact),'exact_rows':sum(sum(z['correct']) for z in exact),'scored_rows':4*len(exact)})
 pooled=[]
 for k in KS:
  p=[x for x in paired if x['K']==k];pooled.append({'K':k,'median_enabled_minus_disabled_ms':1000*statistics.median(x['enabled_total_s']-x['disabled_total_s'] for x in p),'enabled_faster_pairs':sum(x['enabled_total_s']<x['disabled_total_s'] for x in p),'pairs':len(p)})
 cross=next((x['K'] for x in pooled if x['median_enabled_minus_disabled_ms']<0),None)
 per_stratum=[]
 for mn in MAPS:
  for ln in LAYOUTS:
   xs=[]
   for k in KS:
    p=[x for x in paired if x['matrix_name']==mn and x['layout']==ln and x['K']==k]
    xs.append({'K':k,'median_delta_ms':1000*statistics.median(x['enabled_total_s']-x['disabled_total_s'] for x in p)})
   per_stratum.append({'matrix_name':mn,'layout':ln,'first_crossover_K':next((x['K'] for x in xs if x['median_delta_ms']<0),None),'by_K':xs})
 checks['acquisition_metric_defined']=all(isinstance(p['acquired'],bool) for p in paired)
 out={'checks':checks,'all_checks_pass':all(checks.values()),'raw_sha256':sha(RAW),'analyzer_sha256':sha(Path(__file__)),'heldout_bases':HELD,'summaries':summaries,'paired_costs':paired,'pooled_costs':pooled,'pooled_first_runtime_crossover_K':cross,'stratum_crossover':per_stratum,'application_routes':dict(Counter(z['route'] for z in scores)),'scored_applications':scores}
 path=ROOT/'evaluation/reports/substrate_genmint_matrix_family_reuse_v3_analysis_20260926.json';path.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'analysis':str(path),'all_checks_pass':out['all_checks_pass'],'failed_checks':[k for k,v in checks.items() if not v],'workers':len(workers),'summary':summaries,'pooled_costs':pooled,'pooled_first_runtime_crossover_K':cross},indent=2))
if __name__=='__main__':main()
