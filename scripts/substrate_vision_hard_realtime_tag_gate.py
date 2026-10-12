#!/usr/bin/env python3
"""Check benchmark-only hard_realtime tagging against full rescan."""
import copy,hashlib,json,platform,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_VISION_HARD_REALTIME_TAG_GATE_PREREG_20260925.md"
OUT=ROOT/"evaluation/reports/substrate_vision_hard_realtime_tag_gate_20260925.json"
TARGETS={'vision_waves','vision_settle','vision_onoff','vision_lateral','vision_compose'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run_arm(tagged):
 import substrate.boot_core as boot_core
 from substrate.seed_loader import manifest_for as original
 from scripts.settle_lib import build_sheet
 from domains.complex_cells import grating,binarize
 if tagged:
  def wrapped(sid):
   m=copy.deepcopy(original(sid))
   if sid in TARGETS:
    for r in m.get('rules',[]):
     if 'match' in r:r['latency_class']='hard_realtime'
   return m
  boot_core.manifest_for=wrapped
 try:w,units,_=build_sheet(seed=20260925,n_side=3,channels='lateral',connectivity=8,settle=1,bubble=0)
 finally:
  if tagged:boot_core.manifest_for=original
 s=w.s;inner=s._inner;frame=binarize(grating((w.h,w.w),0,0,4));step=float(s.node(w.retina)['attrs'].get('step',0))+10;s.set_attr(w.retina,'step',step)
 for (r,c),node in w.cells.items():
  on=frame[r,c]>.5;s.set_attr(node,'bursting',1.0 if on else 0.0);s.set_attr(node,'last_burst',step if on else -999.0);s.set_attr(node,'state','rested')
 for node in s.nodes('Unit'):s.set_attr(node,'bursting',0.0)
 rules=inner.export_rules();wanted={'lat_pool','lat_residual','lat_bipolar','st_settle','st_commit','oo_sunit_activate','oo_sunit_rate'}
 selected=[{'name':r['name'],'latency_class':r.get('latency_class','')} for r in rules if r['name'] in wanted]
 if tagged: progress=int(inner.tick(200000,True));report=None
 else: report=inner.run_rules_report(200000,True);progress=int(report['progress_steps'])
 state={}
 for typ,keys in {'RetinaCell':['bursting','last_burst'],'HCell':['h1','h2','resid','resid_step'],'LBipolar':['bursting','bstep'],'SUnit':['act','act_next','rate','act_step','aff_step']}.items():
  state[typ]=[{k:s.node(n)['attrs'].get(k) for k in keys} for n in s.nodes(typ)]
 return {'variant':'tagged_default_tick' if tagged else 'unfiltered_rescan','progress':progress,'report':report,'selected_rules':selected,'state':state,'max_sunit_act':max(float(s.node(n)['attrs'].get('act',0)) for n in units),'max_sunit_rate':max(float(s.node(n)['attrs'].get('rate',0)) for n in units),'rule_count':len(rules)}
def main():
 from domains.engine_provenance import engine_preamble,engine_provenance
 engine_preamble()
 from substrate_rs import _native
 arms=[run_arm(False),run_arm(True)]
 exact=True
 for typ in arms[0]['state']:
  exact &= arms[0]['state'][typ]==arms[1]['state'][typ]
 checks={'both_arms_have_same_rule_count':arms[0]['rule_count']==arms[1]['rule_count'],'tagged_vision_rules_all_hard':all(r['latency_class']=='hard_realtime' for r in arms[1]['selected_rules']),'control_vision_rules_untagged':all(r['latency_class']=='' for r in arms[0]['selected_rules']),'control_full_rescan_progressed':arms[0]['progress']>0,'tagged_tick_progressed':arms[1]['progress']>0,'tagged_tick_responded':arms[1]['max_sunit_act']>0 and arms[1]['max_sunit_rate']>0,'tagged_tick_below_cap':arms[1]['progress']<200000,'all_relevant_state_exactly_matches':bool(exact)}
 result={'run_id':'vision-hard-realtime-tag-gate-20260925','arms':arms,'checks':checks,'pass':all(checks.values()),'provenance':{'python':sys.version,'platform':platform.platform(),'runner_sha256':sha(Path(__file__)),'protocol_sha256':sha(PROTOCOL),'seed_sha256':sha(ROOT/'seeds/vision_settle.json'),'native_extension_path':str(Path(_native.__file__).resolve()),'native_extension_sha256':sha(Path(_native.__file__).resolve()),'engine_provenance':engine_provenance(),'source_sha256':{n:sha(ROOT/'runners/dsl/src'/n) for n in ('cognitive_cycle.rs','substrate.rs','rewrite.rs','py.rs')}}}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':checks,'progress':[a['progress'] for a in arms],'status':arms[0]['report']['status'] if arms[0]['report'] else 'tick-cycle-report-not-exposed'},indent=2))
 if not result['pass']:raise SystemExit('hard-realtime tag gate did not pass')
if __name__=='__main__':main()
