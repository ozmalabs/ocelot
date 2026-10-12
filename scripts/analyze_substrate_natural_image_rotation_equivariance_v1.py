#!/usr/bin/env python3
"""Independent analysis of natural-image spatial-equivariance pilot."""
import hashlib,json,math,statistics
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/natural_image_rotation_equivariance_v1_20260929_raw.json'
LOCK=ROOT/'evaluation/substrate_capability/natural_image_rotation_equivariance_v1_20260929_lock.json'
OUT=ROOT/'evaluation/reports/natural_image_rotation_equivariance_v1_20260929_analysis.json'
SEEDS=(20260935,20260936,20260937);SCOPES=('global','root_scoped')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rel_error(a,b):return float(np.abs(np.asarray(a)-np.asarray(b)).sum()/(np.abs(b).sum()+1e-9))
def main():
    data=json.loads(RAW.read_text());locked=json.loads(LOCK.read_text())['locked_inputs'];workers=data['workers']
    seen={(w['seed'],w['scope'],w['image']) for w in workers}
    expected_names=locked['image_names'];matrix={(s,c,n) for s in SEEDS for c in SCOPES for n in expected_names}
    rows=[]
    for w in workers:
        arms={a['label']:a for a in w['arms']}
        if len(arms)!=3:continue
        scores={}
        for field in ('act','rate'):
            orig=np.asarray(arms['original'][field],float).reshape(4,4)
            rot=np.asarray(arms['rotated_180'][field],float).reshape(4,4)
            blank=np.asarray(arms['blank'][field],float).reshape(4,4)
            scores[field]={'equivariance_relative_l1':rel_error(np.rot90(orig,2),rot),
                'identity_relative_l1':rel_error(orig,rot),
                'original_mass':float(np.abs(orig).sum()),'rotated_mass':float(np.abs(rot).sum()),
                'blank_mass':float(np.abs(blank).sum()),
                'signal_above_blank':float((np.abs(orig).sum()+np.abs(rot).sum())/2-np.abs(blank).sum())}
        rows.append({'seed':w['seed'],'scope':w['scope'],'image':w['image'],'scores':scores})
    grouped={}
    for f in ('act','rate'):
      for scope in SCOPES:
        rs=[r for r in rows if r['scope']==scope]
        grouped[f'{f}:{scope}']={'image_count':len(rs),
            'median_equivariance_relative_l1':statistics.median(r['scores'][f]['equivariance_relative_l1'] for r in rs) if rs else None,
            'median_identity_relative_l1':statistics.median(r['scores'][f]['identity_relative_l1'] for r in rs) if rs else None,
            'proper_mapping_beats_identity_count':sum(r['scores'][f]['equivariance_relative_l1']<r['scores'][f]['identity_relative_l1'] for r in rs),
            'signal_above_blank_count':sum(r['scores'][f]['signal_above_blank']>1e-9 for r in rs),
            'median_signal_above_blank':statistics.median(r['scores'][f]['signal_above_blank'] for r in rs) if rs else None}
    checks={'worker_matrix_complete':len(workers)==48 and seen==matrix,
       'capture_lock_matches':data.get('locked_inputs')==locked,
       'source_stable':data.get('source_stable') is True,
       'all_three_arms':all(len(w['arms'])==3 and {a['label'] for a in w['arms']}=={'original','rotated_180','blank'} for w in workers),
       'all_restored_same_checkpoint':all(len({a['checkpoint_sha256'] for a in w['arms']})==1 and a['checkpoint_sha256']==locked['checkpoint_sha256'][str(w['seed'])] for w in workers for a in w['arms']),
       'exact_pixel_delivery':all(a['delivered_pixels_exact'] for w in workers for a in w['arms']),
       'exact_input_transform_hashes':all(w['arms'][0]['input_sha256']!=w['arms'][1]['input_sha256'] and w['arms'][2]['input_sha256']==hashlib.sha256(np.zeros((16,16),np.float32).tobytes()).hexdigest() for w in workers),
       'complete_finite_maps':all(len(a['act'])==16 and len(a['rate'])==16 and all(math.isfinite(x) for x in a['act']+a['rate']) for w in workers for a in w['arms']),
       'steps_completed':all(a['step_return']>0 and a['root_step']>0 for w in workers for a in w['arms'])}
    out={'run_id':data['run_id'],'checks':checks,'passed_checks':sum(checks.values()),'total_checks':len(checks),'pass':all(checks.values()),
       'worker_count':len(workers),'image_names':expected_names,'image_level_scores':rows,'summary':grouped,
       'claim_boundary':'Natural-image low-level 180-degree spatial-equivariance pilot on eight BSDS300 test patches, three adapted checkpoints, and two settlement scopes. Not semantic recognition, prevalence, frame discovery, or scaling.'}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':checks,'passed_checks':out['passed_checks'],'total_checks':out['total_checks'],'summary':grouped},indent=2))
    if not out['pass']:raise SystemExit('natural-image equivariance integrity gate failed')
if __name__=='__main__':main()
