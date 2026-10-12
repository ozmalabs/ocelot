#!/usr/bin/env python3
"""Independent paired outcome and cost analysis for role-separator capture."""
import hashlib,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/llm_transport_role_separator_v1_2_lock_20261002.json'
CAPTURE=ROOT/'evaluation/reports/llm_transport_role_separator_v1_2_20261002.json'
OUT=ROOT/'evaluation/reports/llm_transport_role_separator_v1_2_analysis_20261002.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 lock=json.loads(LOCK.read_text());x=json.loads(CAPTURE.read_text());errs=[]
 def req(ok,msg):
  if not ok:errs.append(msg)
 req(x['lock_sha256']==sha(LOCK),'capture lock hash mismatch');req(x['sources']==lock['sources']==x['post_run_sources'],'source lock mismatch')
 req(not x['failures'],'worker failure');runs=x['runs'];req(len(runs)==3 and len({r['pid'] for r in runs})==3,'expected three fresh workers')
 cells=[c for r in runs for c in r['rows']];req(len(cells)==60,'expected 60 cells')
 req(all(v for v in x['checks'].values()),'runner gate failure')
 req(all(abs(c['jt_energy']-c['conditioned_energy'])<1e-8 for c in cells),'conditioned energy differs from JT')
 req(all(abs(c['conditioned_energy']-c['conditioned_direct_rescore'])<1e-8 for c in cells),'conditioned direct rescore mismatch')
 req(all(c['conditioned_prediction']==c['jt_prediction'] for c in cells),'conditioned returned signs differ from monolithic JT')
 req(all(c['conditioned_repeat_stable'] for c in cells),'traced repeat differs from uninstrumented solve')
 req(all(c['conditioned_state_valid'] and c['connected'] and c['width']==c['certified_width']==8 for c in cells),'invalid graph/state/width')
 groups={}
 for condition in ('learned','shuffled'):
  cc=[c for c in cells if c['condition']==condition]
  jt=[c['timing_ns']['junction_tree']/1e6 for c in cc];part=[c['timing_ns']['conditioned_solver']/1e6 for c in cc]
  groups[condition]={'n':len(cc),'conditioned_accuracy_mean':statistics.mean(c['conditioned_accuracy'] for c in cc),'bp_accuracy_mean':statistics.mean(c['bp_accuracy'] for c in cc),
   'median_junction_tree_ms':statistics.median(jt),'median_conditioned_ms':statistics.median(part),'median_speed_ratio_jt_over_conditioned':statistics.median(a/b for a,b in zip(jt,part)),
   'median_conditioned_python_peak_mib':statistics.median(c['conditioned_traced_peak_bytes'] for c in cc)/1048576,
   'median_process_rss_mib':statistics.median(r['peak_rss_kib'] for r in runs)/1024}
 pairs=[]
 for r in runs:
  for i in range(10):
   a,b=r['rows'][2*i:2*i+2]
   req(a['heldout_index']==b['heldout_index'] and a['condition']=='learned' and b['condition']=='shuffled','paired cell order mismatch')
   pairs.append({'replicate':r['replicate'],'heldout_index':i,'learned_ms':a['timing_ns']['conditioned_solver']/1e6,'shuffled_ms':b['timing_ns']['conditioned_solver']/1e6})
 out={'schema':'LlmTransportRoleSeparatorV1Analysis','gates_pass':not errs,'errors':errs,'checks':x['checks'],'by_condition':groups,
  'interpretation':'The model builder supplies the source/target role partition; these results measure exact conditional decomposition cost, not automatic partition discovery or natural task prevalence.',
  'paired_conditioned_timings':pairs}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2));return int(bool(errs))
if __name__=='__main__':sys.exit(main())
