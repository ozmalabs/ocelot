#!/usr/bin/env python3
"""Corrected independent analysis; subtracts each checkpoint's blank response."""
import hashlib,json,math,statistics
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/natural_image_rotation_equivariance_v1_20260929_raw.json'
LOCK=ROOT/'evaluation/substrate_capability/natural_image_rotation_equivariance_v1_20260929_lock.json'
OUT=ROOT/'evaluation/reports/natural_image_rotation_equivariance_v1_20260929_corrected_analysis.json'
SEEDS=(20260935,20260936,20260937);SCOPES=('global','root_scoped')
TEST_DIR=ROOT/'data/vision_curriculum/BSDS300/images/test'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rel_error(a,b):return float(np.abs(np.asarray(a)-np.asarray(b)).sum()/(np.abs(b).sum()+1e-9))
def image_for(name):
    im=Image.open(TEST_DIR/name).convert('L').resize((16,16),Image.Resampling.BILINEAR)
    return np.asarray(im,dtype=np.float32)/255.0
def main():
    data=json.loads(RAW.read_text());locked=json.loads(LOCK.read_text())['locked_inputs'];workers=data['workers']
    expected={(s,c,n) for s in SEEDS for c in SCOPES for n in locked['image_names']}
    seen={(w['seed'],w['scope'],w['image']) for w in workers};rows=[]
    checkpoint_graph={}
    for s in SEEDS:
        cp=json.loads((ROOT/f'evaluation/reports/vision_multiseed_checkpoints_v2_0/seed_{s}.json').read_text())
        checkpoint_graph[str(s)]=cp['prepared_graph_sha256']
    for w in workers:
        arms={a['label']:a for a in w['arms']}
        if set(arms)!={'original','rotated_180','blank'}:continue
        scores={}
        for field in ('act','rate'):
            original=np.asarray(arms['original'][field],float).reshape(4,4)
            rotated=np.asarray(arms['rotated_180'][field],float).reshape(4,4)
            blank=np.asarray(arms['blank'][field],float).reshape(4,4)
            delta=original-blank;rot_delta=rotated-blank
            scores[field]={'blank_subtracted_equivariance_relative_l1':rel_error(np.rot90(delta,2),rot_delta),
                'blank_subtracted_identity_relative_l1':rel_error(delta,rot_delta),
                'original_delta_l1':float(np.abs(delta).sum()),'rotated_delta_l1':float(np.abs(rot_delta).sum()),
                'blank_l1':float(np.abs(blank).sum()),
                'input_response_present':bool(np.abs(delta).sum()>1e-9 and np.abs(rot_delta).sum()>1e-9)}
        rows.append({'seed':w['seed'],'scope':w['scope'],'image':w['image'],'scores':scores})
    grouped={}
    for f in ('act','rate'):
      for scope in SCOPES:
        rs=[r for r in rows if r['scope']==scope]
        equiv=[r['scores'][f]['blank_subtracted_equivariance_relative_l1'] for r in rs]
        ident=[r['scores'][f]['blank_subtracted_identity_relative_l1'] for r in rs]
        grouped[f'{f}:{scope}']={'image_count':len(rs),
            'median_blank_subtracted_equivariance_relative_l1':statistics.median(equiv) if equiv else None,
            'median_blank_subtracted_identity_relative_l1':statistics.median(ident) if ident else None,
            'proper_mapping_beats_identity_count':sum(a<b for a,b in zip(equiv,ident)),
            'nonblank_response_pair_count':sum(r['scores'][f]['input_response_present'] for r in rs),
            'median_original_delta_l1':statistics.median(r['scores'][f]['original_delta_l1'] for r in rs) if rs else None}
    checks={'worker_matrix_complete':len(workers)==48 and seen==expected,
      'raw_capture_matches_locked_inputs':data.get('locked_inputs')==locked,
      'capture_source_stable':data.get('source_stable') is True,
      'all_three_arms':all(len(w['arms'])==3 and {a['label'] for a in w['arms']}=={'original','rotated_180','blank'} for w in workers),
      'all_restore_exact_checkpoint_graph':all(a['checkpoint_sha256']==checkpoint_graph[str(w['seed'])] for w in workers for a in w['arms']),
      'checkpoint_files_match_lock':all(sha(ROOT/f'evaluation/reports/vision_multiseed_checkpoints_v2_0/seed_{s}.json')==locked['checkpoint_sha256'][str(s)] for s in SEEDS),
      'exact_pixel_delivery':all(a['delivered_pixels_exact'] for w in workers for a in w['arms']),
      'frame_transform_hashes_correct':all(w['arms'][0]['input_sha256']==hashlib.sha256(image_for(w['image']).tobytes()).hexdigest() and w['arms'][1]['input_sha256']==hashlib.sha256(np.rot90(image_for(w['image']),2).copy().tobytes()).hexdigest() and w['arms'][2]['input_sha256']==hashlib.sha256(np.zeros((16,16),np.float32).tobytes()).hexdigest() for w in workers),
      'complete_finite_maps':all(len(a['act'])==16 and len(a['rate'])==16 and all(math.isfinite(x) for x in a['act']+a['rate']) for w in workers for a in w['arms']),
      'steps_completed':all(a['step_return']>0 and a['root_step']>0 for w in workers for a in w['arms'])}
    task={k:{'nonblank_response_pair_count':v['nonblank_response_pair_count'],'worker_count':v['image_count'],
             'equivariance_supported':v['nonblank_response_pair_count']>0 and v['proper_mapping_beats_identity_count']>v['image_count']//2}
          for k,v in grouped.items()}
    out={'run_id':data['run_id'],'analysis_version':'corrected_background_subtracted_v1',
      'capture_analyzer_sha256':locked['analyzer_sha256'],'corrected_analyzer_sha256':sha(__file__),
      'checks':checks,'passed_checks':sum(checks.values()),'total_checks':len(checks),'integrity_pass':all(checks.values()),
      'task_gate':task,'task_gate_pass':all(v['equivariance_supported'] for v in task.values()),
      'worker_count':len(workers),'image_names':locked['image_names'],'image_level_scores':rows,'summary':grouped,
      'analysis_correction':'The original analyzer compared a prepared-graph digest against a checkpoint file hash and used raw output magnitude rather than blank-subtracted response. This correction compares graph digest to graph digest and measures the frame-induced response delta from an independently restored blank arm.',
      'claim_boundary':'Natural-image low-level 180-degree spatial-equivariance pilot on eight BSDS300 test patches, three adapted checkpoints, and two settlement scopes. Not semantic recognition, prevalence, frame discovery, or scaling.'}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':checks,'passed_checks':out['passed_checks'],'total_checks':out['total_checks'],'integrity_pass':out['integrity_pass'],'task_gate':task,'summary':grouped},indent=2))
    if not out['integrity_pass']:raise SystemExit('natural-image integrity gate failed')
if __name__=='__main__':main()
