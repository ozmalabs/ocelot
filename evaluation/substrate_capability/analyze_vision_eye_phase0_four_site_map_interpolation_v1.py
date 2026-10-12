#!/usr/bin/env python3
"""Independently score four-site RF coverage and held-out-location responses."""
from __future__ import annotations
import hashlib,json,math,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];CAPTURE=ROOT/'evaluation/reports/vision_eye_phase0_four_site_map_interpolation_v1_20261005.json';ANALYSIS=ROOT/'evaluation/reports/vision_eye_phase0_four_site_map_interpolation_v1_analysis_20261005.json';LOCK=ROOT/'evaluation/substrate_capability/vision_eye_phase0_four_site_map_interpolation_v1_lock_20261005.json';ANALYZER=Path(__file__).resolve();TRAIN=((3,3),(3,12),(12,3),(12,12))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def center_spread(w,n=16):
    total=sum(w)
    if total<=0:return None,None
    y=sum((i//n)*v for i,v in enumerate(w))/total;x=sum((i%n)*v for i,v in enumerate(w))/total
    spread=math.sqrt(sum(v*((i//n-y)**2+(i%n-x)**2) for i,v in enumerate(w))/total);return [y,x],spread
def main():
    before=sha(ANALYZER);d=json.loads(CAPTURE.read_text());lock=json.loads(LOCK.read_text());workers=[]
    for r in d['rows']:
        fs=r['learned_fields'];field_stats=[]
        for f in fs:
            c,s=center_spread(f['weights']);nearest=min(range(4),key=lambda i:math.dist(c,TRAIN[i]));field_stats.append({'unit':f['unit'],'center':c,'spread':s,'nearest_train_site':nearest,'nearest_train_distance':math.dist(c,TRAIN[nearest]),'localized_to_any_train_site':s<3 and min(math.dist(c,x) for x in TRAIN)<1})
        ps=[]
        for p in r['probes']:
            site=p['site'];vals=[]
            for f in fs:
                c,s=center_spread(f['weights']);vals.append({'unit':f['unit'],'center':c,'spread':s,'distance':math.dist(c,site),'localized_for_target':s<3 and math.dist(c,site)<1})
            wi=p['winners'][0];acts=[sum(fs[i]['weights'][idx] for idx in p['mask']) for i in range(len(fs))]
            nearest_site=min(range(4),key=lambda i:math.dist(site,TRAIN[i]));winner_field=field_stats[wi]
            ps.append({'site_index':p['site_index'],'site':site,'location_status':p['location_status'],'rep':p['rep'],'winner':wi,'winner_localized_for_target':vals[wi]['localized_for_target'],'winner_distance':vals[wi]['distance'],'winner_spread':vals[wi]['spread'],'winner_nearest_train_site':winner_field['nearest_train_site'],'nearest_train_site_expected':nearest_site,'winner_matches_nearest_train_region':winner_field['nearest_train_site']==nearest_site,'native_acts':p['acts'],'weight_recomputed_acts':acts,'acts_match':all(abs(a-b)<1e-6 for a,b in zip(p['acts'],acts)),'winner_is_recomputed_argmax':acts[wi]>=max(acts)-1e-9})
        workers.append({'seed':r['seed'],'fields':field_stats,'unique_train_sites_covered':len({f['nearest_train_site'] for f in field_stats if f['localized_to_any_train_site']}),'probes':ps})
    groups=[]
    for status in ('trained','heldout'):
        vals=[p for w in workers for p in w['probes'] if p['location_status']==status]
        groups.append({'location_status':status,'probes':len(vals),'target_localized_winner_count':sum(p['winner_localized_for_target'] for p in vals),'nearest_region_winner_count':sum(p['winner_matches_nearest_train_region'] for p in vals),'native_act_recomputation_matches':sum(p['acts_match'] for p in vals),'recomputed_argmax_matches':sum(p['winner_is_recomputed_argmax'] for p in vals),'median_winner_distance':statistics.median(p['winner_distance'] for p in vals),'median_winner_spread':statistics.median(p['winner_spread'] for p in vals)})
    checks={'capture_gates_pass':d['passed'] and all(d['checks'].values()),'three_workers':len(workers)==3,'expected_probe_counts':[(g['location_status'],g['probes']) for g in groups]==[('trained',60),('heldout',180)],'all_240_activation_vectors_reconcile':all(p['acts_match'] for w in workers for p in w['probes']),'all_240_winners_match_recomputed_argmax':all(p['winner_is_recomputed_argmax'] for w in workers for p in w['probes']),'source_lock_stable':d['locked_inputs']==lock['locked_inputs']==d['post_run_inputs'],'analyzer_stable':before==sha(ANALYZER),'frozen_weights_unchanged':all(r['learned_fields']==r['post_probe_fields'] for r in d['rows'])}
    out={'schema':'VisionEyeFourSiteMapInterpolationV1Analysis','analyzer_sha256':before,'capture_sha256':sha(CAPTURE),'lock_sha256':sha(LOCK),'workers':workers,'groups':groups,'checks':checks,'passed':all(checks.values()),'claim_limit':d['claim_limit']};ANALYSIS.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':out['passed'],'checks':checks,'groups':groups,'unique_sites_covered':[w['unique_train_sites_covered'] for w in workers],'output':ANALYSIS.relative_to(ROOT).as_posix()}));return 0 if out['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
