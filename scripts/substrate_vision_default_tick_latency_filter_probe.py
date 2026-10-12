#!/usr/bin/env python3
"""Runtime/source probe of vision rules under default cycle latency filtering."""
import hashlib,json,platform,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_VISION_DEFAULT_TICK_LATENCY_FILTER_PREREG_20260925.md"
OUT=ROOT/"evaluation/reports/substrate_vision_default_tick_latency_filter_20260925.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 from domains.engine_provenance import engine_preamble,engine_provenance
 engine_preamble()
 from scripts.settle_lib import build_sheet
 from domains.complex_cells import grating,binarize
 from substrate_rs import _native
 w,units,_=build_sheet(seed=20260925,n_side=3,channels='lateral',connectivity=8,settle=1,bubble=0)
 s=w.s;inner=s._inner
 policies=[dict(s.node(n)['attrs']) for n in s.nodes('DualProcessPolicy')]
 rules=inner.export_rules(); names={'st_settle','st_commit','oo_sunit_activate','oo_sunit_rate','lat_pool','lat_residual','lat_bipolar'}
 selected=[{'name':r['name'],'active':r['active'],'latency_class':r.get('latency_class','')} for r in rules if r['name'] in names]
 frame=binarize(grating((w.h,w.w),0.0,0.0,4.0));step=float(s.node(w.retina)['attrs'].get('step',0.0))+10.0;s.set_attr(w.retina,'step',step)
 for (r,c),nid in w.cells.items():
  on=(r<frame.shape[0] and c<frame.shape[1] and frame[r,c]>0.5)
  s.set_attr(nid,'bursting',1.0 if on else 0.0);s.set_attr(nid,'last_burst',step if on else -999.0);s.set_attr(nid,'state','rested')
 for nid in s.nodes('Unit'):s.set_attr(nid,'bursting',0.0)
 tick=int(inner.tick(200000,False))
 report=inner.run_rules_report(200000,True)
 result={'run_id':'vision-default-tick-latency-filter-probe-20260925','policies':policies,'vision_rule_latency':selected,'default_tick_progress':tick,'unfiltered_report':report,'post_rescan_max_act':max(float(s.node(u)['attrs'].get('act',0.0)) for u in units),'post_rescan_max_rate':max(float(s.node(u)['attrs'].get('rate',0.0)) for u in units),'provenance':{'python':sys.version,'platform':platform.platform(),'runner_sha256':sha(Path(__file__)),'protocol_sha256':sha(PROTOCOL),'native_extension_path':str(Path(_native.__file__).resolve()),'native_extension_sha256':sha(Path(_native.__file__).resolve()),'engine_provenance':engine_provenance(),'source_sha256':{n:sha(ROOT/'runners/dsl/src'/n) for n in ('cognitive_cycle.rs','substrate.rs','rewrite.rs','py.rs')}}}
 result['checks']={'enabled_dual_policy':any(float(p.get('enabled',0))>0.5 for p in policies),'vision_rules_untagged':all(not r['latency_class'] for r in selected),'default_tick_skipped':tick==0,'full_rescan_progressed':report['progress_steps']>0,'full_rescan_responded':result['post_rescan_max_act']>0 and result['post_rescan_max_rate']>0}
 result['pass']=all(result['checks'].values());OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':result['checks'],'progress':report['progress_steps'],'status':report['status'],'max_act':result['post_rescan_max_act'],'max_rate':result['post_rescan_max_rate']},indent=2))
 if not result['pass']:raise SystemExit('latency-filter probe failed registered predictions')
if __name__=='__main__':main()
