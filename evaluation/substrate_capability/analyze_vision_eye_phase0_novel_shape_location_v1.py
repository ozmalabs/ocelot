#!/usr/bin/env python3
"""Score held-out morphology responses independently from captured weights/acts."""
from __future__ import annotations
import hashlib,json,math,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];CAPTURE=ROOT/'evaluation/reports/vision_eye_phase0_novel_shape_location_v1_20261005.json';ANALYSIS=ROOT/'evaluation/reports/vision_eye_phase0_novel_shape_location_v1_analysis_20261005.json';LOCK=ROOT/'evaluation/substrate_capability/vision_eye_phase0_novel_shape_location_v1_lock_20261005.json';ANALYZER=Path(__file__).resolve()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def center_spread(w,n=16):
    total=sum(w)
    if total<=0:return None,None
    y=sum((i//n)*v for i,v in enumerate(w))/total;x=sum((i%n)*v for i,v in enumerate(w))/total
    spread=math.sqrt(sum(v*((i//n-y)**2+(i%n-x)**2) for i,v in enumerate(w))/total);return [y,x],spread
def main():
    before=sha(ANALYZER);d=json.loads(CAPTURE.read_text());lock=json.loads(LOCK.read_text());workers=[]
    for r in d['rows']:
        fields=r['learned_fields'];per=[]
        for p in r['probes']:
            site=p['site'];scores=[]
            for f in fields:
                center,spread=center_spread(f['weights']);dist=math.dist(center,site);scores.append({'unit':f['unit'],'center':center,'spread':spread,'distance':dist,'localized_for_site':spread<3 and dist<1})
            winner=p['winners'][0];winner_score=scores[winner];derived_acts=[sum(fields[i]['weights'][idx] for idx in p['mask']) for i in range(len(fields))]
            act_match=all(abs(a-b)<1e-6 for a,b in zip(p['acts'],derived_acts));argmax_match=derived_acts[winner]>=max(derived_acts)-1e-9
            per.append({'pattern':p['pattern'],'location_status':p['location_status'],'site':site,'rep':p['rep'],'native_winner':winner,'winner_localized_for_site':winner_score['localized_for_site'],'winner_distance':winner_score['distance'],'winner_spread':winner_score['spread'],'native_acts':p['acts'],'weight_recomputed_acts':derived_acts,'act_recomputation_matches':act_match,'winner_is_recomputed_argmax':argmax_match})
        workers.append({'seed':r['seed'],'probes':per,'by_pattern':{name:{'n':sum(p['pattern']==name for p in per),'winner_localized_count':sum(p['pattern']==name and p['winner_localized_for_site'] for p in per),'act_recomputation_matches':sum(p['pattern']==name and p['act_recomputation_matches'] for p in per),'recomputed_argmax_matches':sum(p['pattern']==name and p['winner_is_recomputed_argmax'] for p in per)} for name in ('seen_square3','seen_plus5','heldout_x5')}})
    groups=[]
    for name,status in (('seen_square3','trained'),('seen_plus5','trained'),('heldout_x5','trained'),('heldout_x5','novel')):
        vals=[p for w in workers for p in w['probes'] if p['pattern']==name and p['location_status']==status]
        groups.append({'pattern':name,'location_status':status,'probes':len(vals),'localized_winner_count':sum(p['winner_localized_for_site'] for p in vals),'native_act_recomputation_matches':sum(p['act_recomputation_matches'] for p in vals),'recomputed_argmax_matches':sum(p['winner_is_recomputed_argmax'] for p in vals),'median_winner_center_distance':statistics.median(p['winner_distance'] for p in vals),'median_winner_spread':statistics.median(p['winner_spread'] for p in vals)})
    checks={'capture_gates_pass':d['passed'] and all(d['checks'].values()),'three_workers':len(workers)==3,'location_novelty_cells':all(g['probes']==(30 if g['pattern']=='heldout_x5' and g['location_status']=='trained' else 30 if g['location_status']=='novel' else 15) for g in groups),'all_90_acts_reconcile':all(p['act_recomputation_matches'] for w in workers for p in w['probes']),'all_90_winners_match_recomputed_argmax':all(p['winner_is_recomputed_argmax'] for w in workers for p in w['probes']),'source_lock_stable':d['locked_inputs']==lock['locked_inputs']==d['post_run_inputs'],'analyzer_stable':before==sha(ANALYZER),'frozen_fields_unchanged':all(r['learned_fields']==r['post_probe_fields'] for r in d['rows'])}
    out={'schema':'VisionEyeNovelShapeLocationV1Analysis','analyzer_sha256':before,'capture_sha256':sha(CAPTURE),'lock_sha256':sha(LOCK),'groups':groups,'workers':workers,'checks':checks,'passed':all(checks.values()),'claim_limit':d['claim_limit']};ANALYSIS.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':out['passed'],'checks':checks,'groups':groups,'output':ANALYSIS.relative_to(ROOT).as_posix()}));return 0 if out['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
