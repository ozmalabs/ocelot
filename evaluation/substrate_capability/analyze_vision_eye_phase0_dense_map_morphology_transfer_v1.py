#!/usr/bin/env python3
"""Independent paired scoring of square and cross retinotopy maps."""
from __future__ import annotations
import hashlib,json,math,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];CAPTURE=ROOT/'evaluation/reports/vision_eye_phase0_dense_map_morphology_transfer_v1_20261005.json';ANALYSIS=ROOT/'evaluation/reports/vision_eye_phase0_dense_map_morphology_transfer_v1_analysis_20261005.json';LOCK=ROOT/'evaluation/substrate_capability/vision_eye_phase0_dense_map_morphology_transfer_v1_lock_20261005.json';ANALYZER=Path(__file__).resolve()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def center_spread(w,n=16):
    total=sum(w)
    if total<=0:raise ValueError('nonpositive receptive field')
    y=sum((i//n)*v for i,v in enumerate(w))/total;x=sum((i%n)*v for i,v in enumerate(w))/total
    spread=math.sqrt(sum(v*((i//n-y)**2+(i%n-x)**2) for i,v in enumerate(w))/total);return [y,x],spread
def nearest_regions(point,sites):
    ds=[math.dist(point,s) for s in sites];m=min(ds);return [i for i,d in enumerate(ds) if abs(d-m)<1e-9]
def main():
    before=sha(ANALYZER);d=json.loads(CAPTURE.read_text());lock=json.loads(LOCK.read_text());workers=[];groups=[]
    for r in d['rows']:
        sites=[tuple(x) for x in r['sites']];fields=r['learned_fields'];fs=[]
        for f in fields:
            c,sp=center_spread(f['weights']);near=nearest_regions(c,sites);fs.append({'unit':f['unit'],'center':c,'spread':sp,'nearest_site_regions':near,'localized_to_trained_site':sp<3 and min(math.dist(c,x) for x in sites)<1})
        probes=[]
        for p in r['probes']:
            site=tuple(p['site']);acts=[sum(f['weights'][idx] for idx in p['mask']) for f in fields];winner=p['winners'][0];f=fs[winner];truth=nearest_regions(site,sites)
            probes.append({'site':list(site),'site_index':p['site_index'],'location_status':p['location_status'],'winner':winner,'winner_center':f['center'],'winner_spread':f['spread'],'winner_nearest_site_regions':f['nearest_site_regions'],'true_nearest_site_regions':truth,'winner_localized_to_probe':f['spread']<3 and math.dist(f['center'],site)<1,'nearest_region_correct':bool(set(f['nearest_site_regions'])&set(truth)),'acts_match':all(abs(a-b)<1e-6 for a,b in zip(p['acts'],acts)),'argmax_match':acts[winner]>=max(acts)-1e-9})
        workers.append({'seed':r['seed'],'morphology':r['morphology'],'field_coverage':sum(x['localized_to_trained_site'] for x in fs),'unique_trained_sites_covered':len({i for f in fs if f['localized_to_trained_site'] for i in f['nearest_site_regions']}),'fields':fs,'probes':probes})
    for morph in ('square','cross'):
        ww=[w for w in workers if w['morphology']==morph]
        for status in ('trained','heldout'):
            pp=[p for w in ww for p in w['probes'] if p['location_status']==status]
            groups.append({'morphology':morph,'location_status':status,'workers':len(ww),'probes':len(pp),'exact_localization_count':sum(p['winner_localized_to_probe'] for p in pp),'nearest_region_correct_count':sum(p['nearest_region_correct'] for p in pp),'median_winner_center_distance':statistics.median(math.dist(p['winner_center'],p['site']) for p in pp),'median_winner_spread':statistics.median(p['winner_spread'] for p in pp)})
    paired=[]
    for seed in range(30,36):
        sw=next(w for w in workers if w['seed']==seed and w['morphology']=='square');cw=next(w for w in workers if w['seed']==seed and w['morphology']=='cross')
        vals=[]
        for w in (sw,cw):
            pp=[p for p in w['probes'] if p['location_status']=='heldout'];vals.append({'morphology':w['morphology'],'heldout_region_correct':sum(p['nearest_region_correct'] for p in pp),'heldout_count':len(pp),'trained_localized_fields':w['unique_trained_sites_covered']})
        paired.append({'seed':seed,'conditions':vals,'cross_minus_square_heldout_correct':vals[1]['heldout_region_correct']-vals[0]['heldout_region_correct']})
    checks={'capture_gates_pass':d['passed'] and all(d['checks'].values()),'twelve_workers':len(workers)==12,'six_paired_seeds':len(paired)==6,'four_condition_cells':len(groups)==4,'expected_probe_counts':[(g['morphology'],g['location_status'],g['probes']) for g in groups]==[('square','trained',162),('square','heldout',288),('cross','trained',162),('cross','heldout',288)],'all_900_activation_vectors_reconcile':all(p['acts_match'] for w in workers for p in w['probes']),'all_900_winners_match_argmax':all(p['argmax_match'] for w in workers for p in w['probes']),'source_lock_stable':d['locked_inputs']==lock['locked_inputs']==d['post_run_inputs'],'analyzer_stable':before==sha(ANALYZER),'frozen_weights_unchanged':all(next(r for r in d['rows'] if r['seed']==w['seed'] and r['morphology']==w['morphology'])['learned_fields']==next(r for r in d['rows'] if r['seed']==w['seed'] and r['morphology']==w['morphology'])['post_probe_fields'] for w in workers)}
    out={'schema':'VisionEyeDenseMapMorphologyTransferV1Analysis','analyzer_sha256':before,'capture_sha256':sha(CAPTURE),'lock_sha256':sha(LOCK),'workers':workers,'groups':groups,'paired_seed_comparison':paired,'checks':checks,'passed':all(checks.values()),'claim_limit':d['claim_limit']};ANALYSIS.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':out['passed'],'checks':checks,'groups':groups,'seed_coverage':[{'seed':w['seed'],'morphology':w['morphology'],'trained_sites':w['unique_trained_sites_covered']} for w in workers],'paired':paired,'output':ANALYSIS.relative_to(ROOT).as_posix()}));return 0 if out['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
