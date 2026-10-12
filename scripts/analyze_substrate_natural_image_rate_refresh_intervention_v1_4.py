#!/usr/bin/env python3
"""Analyze the 144-cell natural-image rate refresh replication."""
import hashlib,json,math,statistics
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/natural_image_rate_refresh_intervention_v1_4_20260929_raw.json'
LOCK=ROOT/'evaluation/substrate_capability/natural_image_rate_refresh_intervention_v1_4_20260929_lock.json'
OUT=ROOT/'evaluation/reports/natural_image_rate_refresh_intervention_v1_4_20260929_analysis.json'
SEEDS=(20260935,20260936,20260937,20260938,20260939,20260940);SCOPES=('global','root_scoped')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def frame(name):return np.asarray(Image.open(ROOT/'data/vision_curriculum/BSDS300/images/test'/name).convert('L').resize((16,16),Image.Resampling.BILINEAR),np.float32)/255.0
def relerr(a,b):return float(np.abs(np.asarray(a)-np.asarray(b)).sum()/(np.abs(b).sum()+1e-9))
def main():
 data=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text())['locked_inputs'];workers=data['workers'];images=lock['image_names']
 expected={(s,c,img,l) for s in SEEDS for c in SCOPES for img in images for l in ('original','rotated_90','blank')}
 keys={(w['seed'],w['scope'],w['image_name'],w['label']) for w in workers};matrix={};equation_residuals=[];valid=True
 for w in workers:
  img=frame(w['image_name']);rot=np.rot90(img,1).copy();blank=np.zeros((16,16),np.float32)
  pixels={'original':img,'rotated_90':rot,'blank':blank}[w['label']]
  valid &= w['image_name'] in lock['image_sha256'] and sha(ROOT/'data/vision_curriculum/BSDS300/images/test'/w['image_name'])==lock['image_sha256'][w['image_name']]
  valid &= w['input_sha256']==hashlib.sha256(pixels.tobytes()).hexdigest()
  valid &= w['checkpoint_graph_sha256']==lock['checkpoint_graph_sha256'][str(w['seed'])]
  d=w['intervention_graph_diff'];valid &= d['node_inventory_equal'] and d['edge_inventory_equal'] and d['only_allowed_target_attrs']
  valid &= all(c['node_id'] in w['target_unit_ids'] and c['key'] in ('rate','rate_step') for c in d['attr_changes'])
  valid &= w['act_unchanged'] and w['delivered_pixels_exact'] and w['intervention_fired'] and w['termination_confirmed'] and w['rate_rule_invocations']==16 and w['step_return']>0
  before=w['default_state'];after=w['refreshed_state']
  valid &= before['act']==after['act'] and before['theta']==after['theta'] and before['act_step']==after['act_step']
  valid &= all(abs(a-max(v-t,0.0))<=1e-9 for a,v,t in zip(after['rate'],after['act'],after['theta']))
  valid &= all(abs(st-w['root_step'])<1e-9 for st in after['rate_step'])
  equation_residuals.extend(abs(a-max(v-t,0.0)) for a,v,t in zip(after['rate'],after['act'],after['theta']))
  matrix[(w['seed'],w['scope'],w['image_name'],w['label'])]=w
 scores={};by_seed={};by_image={}
 for scope in SCOPES:
  for arm in ('default','refreshed'):
   cells=[]
   for seed in SEEDS:
    for image in images:
     o=matrix[(seed,scope,image,'original')][arm+'_state']['rate'];r=matrix[(seed,scope,image,'rotated_90')][arm+'_state']['rate'];b=matrix[(seed,scope,image,'blank')][arm+'_state']['rate']
     od=np.asarray(o)-np.asarray(b);rd=np.asarray(r)-np.asarray(b)
     ee=relerr(np.rot90(od.reshape(4,4),1),rd.reshape(4,4));ei=relerr(od,rd)
     present=bool(np.abs(od).sum()>1e-9 and np.abs(rd).sum()>1e-9)
     cells.append({'seed':seed,'image':image,'expected_error':ee,'identity_error':ei,'expected_wins':ee<ei,
       'response_present':present,'original_delta_l1':float(np.abs(od).sum()),'rotated_delta_l1':float(np.abs(rd).sum())})
   nondeg=[x for x in cells if x['response_present']]
   scores[f'{scope}:{arm}']={'cell_count':len(cells),'expected_permutation_wins':sum(x['expected_wins'] for x in cells),
      'nondegenerate_response_cells':len(nondeg),'wins_among_nondegenerate':sum(x['expected_wins'] for x in nondeg),
      'median_expected_error_all_cells':statistics.median(x['expected_error'] for x in cells),
      'median_identity_error_all_cells':statistics.median(x['identity_error'] for x in cells),
      'median_expected_error_nondegenerate':statistics.median(x['expected_error'] for x in nondeg) if nondeg else None,
      'median_identity_error_nondegenerate':statistics.median(x['identity_error'] for x in nondeg) if nondeg else None,
      'cells':cells}
   for seed in SEEDS:
    z=[x for x in cells if x['seed']==seed]
    by_seed[f'{scope}:{arm}:{seed}']={'images':len(z),'response_cells':sum(x['response_present'] for x in z),'expected_wins':sum(x['expected_wins'] for x in z)}
   for image in images:
    z=[x for x in cells if x['image']==image]
    by_image[f'{scope}:{arm}:{image}']={'checkpoints':len(z),'response_cells':sum(x['response_present'] for x in z),'expected_wins':sum(x['expected_wins'] for x in z)}
 checks={'worker_matrix_complete':len(workers)==288 and keys==expected,
  'capture_lock_matches':data.get('locked_inputs')==lock,'source_stable':data.get('source_stable') is True,
  'checkpoint_images_and_transform_hashes_valid':valid,
  'exact_intervention_write_footprint':all(w['intervention_graph_diff']['only_allowed_target_attrs'] and w['intervention_graph_diff']['node_inventory_equal'] and w['intervention_graph_diff']['edge_inventory_equal'] for w in workers),
  'act_unchanged':all(w['act_unchanged'] and w['default_state']['act']==w['refreshed_state']['act'] for w in workers),
  'full_refresh_equation_and_stamp_oracle':all(w['rate_rule_invocations']==16 and w['termination_confirmed'] for w in workers) and all(abs(a-max(v-t,0.0))<=1e-9 for w in workers for a,v,t in zip(w['refreshed_state']['rate'],w['refreshed_state']['act'],w['refreshed_state']['theta'])) and all(abs(st-w['root_step'])<1e-9 for w in workers for st in w['refreshed_state']['rate_step'])}
 out={'run_id':data['run_id'],'checks':checks,'passed_checks':sum(checks.values()),'total_checks':len(checks),'integrity_pass':all(checks.values()),
  'worker_count':len(workers),'rate_equation_max_abs_residual':max(equation_residuals,default=None),
  'summary':scores,'by_seed':by_seed,'by_image':by_image,
  'claim_boundary':'Eight BSDS300 test images, six adapted checkpoints, one exact 90-degree transform, global/root-scoped settlement, and a post-settlement rate-rule refresh intervention. Low-level spatial behavior only; not semantic recognition or a scheduler recommendation.'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':checks,'passed_checks':out['passed_checks'],'total_checks':len(checks),'rate_equation_max_abs_residual':out['rate_equation_max_abs_residual'],
  'summary':{k:{kk:vv for kk,vv in v.items() if kk!='cells'} for k,v in scores.items()},'by_seed':by_seed},indent=2))
 if not out['integrity_pass']:raise SystemExit('multi-image refresh integrity gate failed')
if __name__=='__main__':main()
