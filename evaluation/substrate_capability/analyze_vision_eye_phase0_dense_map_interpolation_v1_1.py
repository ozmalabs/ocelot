#!/usr/bin/env python3
"""Independent corrected analysis of the dense-map v1 capture.

The capture runner's probe-count validator mistakenly multiplies the 25-site
probe matrix by REPEATS twice. This analyzer independently checks the locked
protocol's 25 sites x 3 repeats = 75 probes/worker and records the correction.
"""
from __future__ import annotations
import hashlib,json,math,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];CAPTURE=ROOT/'evaluation/reports/vision_eye_phase0_dense_map_interpolation_v1_20261005.json';ANALYSIS=ROOT/'evaluation/reports/vision_eye_phase0_dense_map_interpolation_v1_1_analysis_20261005.json';LOCK=ROOT/'evaluation/substrate_capability/vision_eye_phase0_dense_map_interpolation_v1_lock_20261005.json';RUNNER=ROOT/'evaluation/substrate_capability/vision_eye_phase0_dense_map_interpolation_v1.py';ORIGINAL_ANALYZER=ROOT/'evaluation/substrate_capability/analyze_vision_eye_phase0_dense_map_interpolation_v1.py';ANALYZER=Path(__file__).resolve()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def center_spread(w,n=16):
    total=sum(w)
    if total<=0:raise ValueError('nonpositive receptive field')
    y=sum((i//n)*v for i,v in enumerate(w))/total;x=sum((i%n)*v for i,v in enumerate(w))/total
    spread=math.sqrt(sum(v*((i//n-y)**2+(i%n-x)**2) for i,v in enumerate(w))/total);return [y,x],spread
def nearest_regions(point,sites):
    ds=[math.dist(point,s) for s in sites];m=min(ds);return [i for i,d in enumerate(ds) if abs(d-m)<1e-9]
def main():
    before=sha(ANALYZER);d=json.loads(CAPTURE.read_text());lock=json.loads(LOCK.read_text());workers=[];groups=[];site_count_checks=[]
    for r in d['rows']:
        sites=[tuple(x) for x in r['sites']];fields=r['learned_fields'];field_stats=[]
        for f in fields:
            c,sp=center_spread(f['weights']);near=nearest_regions(c,sites);field_stats.append({'unit':f['unit'],'center':c,'spread':sp,'nearest_site_regions':near,'localized_to_trained_site':sp<3 and min(math.dist(c,x) for x in sites)<1})
        probes=[]
        for p in r['probes']:
            site=tuple(p['site']);acts=[sum(f['weights'][idx] for idx in p['mask']) for f in fields];winner=p['winners'][0];ws=field_stats[winner];truth=nearest_regions(site,sites)
            probes.append({'site':list(site),'site_index':p['site_index'],'location_status':p['location_status'],'winner':winner,'winner_center':ws['center'],'winner_spread':ws['spread'],'winner_nearest_site_regions':ws['nearest_site_regions'],'true_nearest_site_regions':truth,'winner_localized_to_probe':ws['spread']<3 and math.dist(ws['center'],site)<1,'nearest_region_correct':bool(set(ws['nearest_site_regions'])&set(truth)),'acts_match':all(abs(a-b)<1e-6 for a,b in zip(p['acts'],acts)),'argmax_match':acts[winner]>=max(acts)-1e-9})
        site_counts=[sum(p['site_index']==i for p in r['probes']) for i in range(25)];site_count_checks.append(len(r['probes'])==75 and site_counts==[3]*25)
        workers.append({'seed':r['seed'],'field_coverage':sum(x['localized_to_trained_site'] for x in field_stats),'unique_trained_sites_covered':len({i for f in field_stats if f['localized_to_trained_site'] for i in f['nearest_site_regions']}),'fields':field_stats,'probes':probes})
    for status in ('trained','heldout'):
        pp=[p for w in workers for p in w['probes'] if p['location_status']==status]
        groups.append({'location_status':status,'probes':len(pp),'exact_localization_count':sum(p['winner_localized_to_probe'] for p in pp),'nearest_region_correct_count':sum(p['nearest_region_correct'] for p in pp),'median_winner_center_distance':statistics.median(math.dist(p['winner_center'],p['site']) for p in pp),'median_winner_spread':statistics.median(p['winner_spread'] for p in pp)})
    labels=[str(tuple(x)) for x in d['parameters']['train_sites']];conf={truth:{pred:0 for pred in labels} for truth in labels}
    for w in workers:
        for p in w['probes']:
            if p['location_status']!='heldout':continue
            t=labels[p['true_nearest_site_regions'][0]];q=labels[p['winner_nearest_site_regions'][0]];conf[t][q]+=1
    old_checks=dict(d['checks']);old_checks.pop('probe_matrix_exact',None)
    checks={'all_original_capture_gates_except_known_count_bug':all(old_checks.values()),'corrected_25_site_probe_matrix':len(site_count_checks)==6 and all(site_count_checks),'raw_runner_flag_matches_documented_bug':d['checks'].get('probe_matrix_exact') is False and "len(r['probes'])==75*REPEATS" in RUNNER.read_text(),'six_workers':len(workers)==6,'trained_and_heldout_probe_counts':[x['probes'] for x in groups]==[162,288],'all_450_activation_vectors_reconcile':all(p['acts_match'] for w in workers for p in w['probes']),'all_450_winners_match_argmax':all(p['argmax_match'] for w in workers for p in w['probes']),'source_lock_stable':d['locked_inputs']==lock['locked_inputs']==d['post_run_inputs'],'locked_runner_and_original_analyzer_current':sha(RUNNER)==d['locked_inputs']['runner_sha256'] and sha(ORIGINAL_ANALYZER)==d['locked_inputs']['analyzer_sha256'],'frozen_weights_unchanged':all(next(r for r in d['rows'] if r['seed']==w['seed'])['learned_fields']==next(r for r in d['rows'] if r['seed']==w['seed'])['post_probe_fields'] for w in workers),'amended_analyzer_stable':before==sha(ANALYZER)}
    out={'schema':'VisionEyeDenseMapInterpolationV1_1Analysis','amended_analyzer_sha256':before,'original_locked_analyzer_sha256':d['locked_inputs']['analyzer_sha256'],'capture_sha256':sha(CAPTURE),'lock_sha256':sha(LOCK),'workers':workers,'groups':groups,'heldout_nearest_region_confusion':conf,'checks':checks,'passed':all(checks.values()),'amendment':'The v1 runner gate checked 75*REPEATS probes per worker, but 75 is already the full 25-site by 3-repeat matrix. The capture has exactly 75 probes per worker and exactly three probes at each of 25 sites. All other original gates pass; this analysis recomputes the matrix and scoring directly from raw capture.','claim_limit':d['claim_limit']};ANALYSIS.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':out['passed'],'checks':checks,'groups':groups,'coverage':[{'seed':w['seed'],'fields':w['field_coverage'],'sites':w['unique_trained_sites_covered']} for w in workers],'confusion':conf,'output':ANALYSIS.relative_to(ROOT).as_posix()}));return 0 if out['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
