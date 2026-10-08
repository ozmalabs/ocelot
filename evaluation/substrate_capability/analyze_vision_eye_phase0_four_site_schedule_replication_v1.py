#!/usr/bin/env python3
"""Independent paired analysis of spatial site count and training schedule."""
from __future__ import annotations
import hashlib,json,math,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];CAPTURE=ROOT/'evaluation/reports/vision_eye_phase0_four_site_schedule_replication_v1_20261005.json';ANALYSIS=ROOT/'evaluation/reports/vision_eye_phase0_four_site_schedule_replication_v1_analysis_20261005.json';LOCK=ROOT/'evaluation/substrate_capability/vision_eye_phase0_four_site_schedule_replication_v1_lock_20261005.json';ANALYZER=Path(__file__).resolve()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def center_spread(w,n=16):
    total=sum(w)
    if total<=0:return None,None
    y=sum((i//n)*v for i,v in enumerate(w))/total;x=sum((i%n)*v for i,v in enumerate(w))/total
    spread=math.sqrt(sum(v*((i//n-y)**2+(i%n-x)**2) for i,v in enumerate(w))/total);return [y,x],spread
def main():
    before=sha(ANALYZER);d=json.loads(CAPTURE.read_text());lock=json.loads(LOCK.read_text());groups=[];workers=[]
    for r in d['rows']:
        fields=r['learned_fields'];trained=[tuple(x) for x in r['sites']];site_stats=[]
        for f in fields:
            c,sp=center_spread(f['weights']);nearest=min(range(len(trained)),key=lambda i:math.dist(c,trained[i]));site_stats.append({'unit':f['unit'],'center':c,'spread':sp,'nearest_site_index':nearest,'nearest_site_distance':math.dist(c,trained[nearest]),'localized_to_trained_site':sp<3 and min(math.dist(c,x) for x in trained)<1})
        probes=[]
        for p in r['probes']:
            site=tuple(p['site']);vals=[]
            for f in fields:
                c,sp=center_spread(f['weights']);vals.append({'center':c,'spread':sp,'distance':math.dist(c,site),'localized':sp<3 and math.dist(c,site)<1})
            winner=p['winners'][0];act=[sum(fields[i]['weights'][idx] for idx in p['mask']) for i in range(len(fields))];distances=[math.dist(site,x) for x in trained];min_distance=min(distances);regions=[i for i,v in enumerate(distances) if abs(v-min_distance)<1e-9]
            probes.append({'site':list(site),'site_index':p['site_index'],'location_status':p['location_status'],'winner':winner,'winner_localized':vals[winner]['localized'],'winner_distance':vals[winner]['distance'],'winner_spread':vals[winner]['spread'],'winner_nearest_site':site_stats[winner]['nearest_site_index'],'expected_nearest_sites':regions,'nearest_region_correct':site_stats[winner]['nearest_site_index'] in regions,'acts_match':all(abs(a-b)<1e-6 for a,b in zip(p['acts'],act)),'argmax_match':act[winner]>=max(act)-1e-9})
        workers.append({'seed':r['seed'],'site_count':r['site_count'],'schedule':r['schedule'],'localized_unit_count':sum(x['localized_to_trained_site'] for x in site_stats),'unique_sites_covered':len({x['nearest_site_index'] for x in site_stats if x['localized_to_trained_site']}),'fields':site_stats,'probes':probes})
    for sch in ('interleaved','blocked'):
        cell=[w for w in workers if w['site_count']==4 and w['schedule']==sch];pp=[p for w in cell for p in w['probes']]
        for status in ('trained','heldout'):
            v=[p for p in pp if p['location_status']==status]
            groups.append({'site_count':4,'schedule':sch,'location_status':status,'workers':len(cell),'probes':len(v),'localized_count':sum(p['winner_localized'] for p in v),'nearest_region_correct_count':sum(p['nearest_region_correct'] for p in v),'median_winner_distance':statistics.median(p['winner_distance'] for p in v),'median_winner_spread':statistics.median(p['winner_spread'] for p in v)})
    checks={'capture_gates_pass':d['passed'] and all(d['checks'].values()),'twelve_workers':len(workers)==12,'two_schedules_six_seeds_each':all(sum(w['schedule']==sch for w in workers)==6 for sch in ('interleaved','blocked')),'four_summary_cells':len(groups)==4,'probe_counts_exact':[(g['schedule'],g['location_status'],g['probes']) for g in groups]==[('interleaved','trained',72),('interleaved','heldout',216),('blocked','trained',72),('blocked','heldout',216)],'all_576_activation_vectors_reconcile':all(p['acts_match'] for w in workers for p in w['probes']),'all_576_winners_match_argmax':all(p['argmax_match'] for w in workers for p in w['probes']),'source_lock_stable':d['locked_inputs']==lock['locked_inputs']==d['post_run_inputs'],'analyzer_stable':before==sha(ANALYZER),'frozen_weights_unchanged':all(next(r for r in d['rows'] if r['seed']==w['seed'] and r['site_count']==w['site_count'] and r['schedule']==w['schedule'])['learned_fields']==next(r for r in d['rows'] if r['seed']==w['seed'] and r['site_count']==w['site_count'] and r['schedule']==w['schedule'])['post_probe_fields'] for w in workers)}
    out={'schema':'VisionEyeFourSiteScheduleReplicationV1Analysis','analyzer_sha256':before,'capture_sha256':sha(CAPTURE),'lock_sha256':sha(LOCK),'workers':workers,'groups':groups,'checks':checks,'passed':all(checks.values()),'claim_limit':d['claim_limit']};ANALYSIS.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':out['passed'],'checks':checks,'groups':groups,'field_coverage':[{k:w[k] for k in ('seed','site_count','schedule','localized_unit_count','unique_sites_covered')} for w in workers],'output':ANALYSIS.relative_to(ROOT).as_posix()}));return 0 if out['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
