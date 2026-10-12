#!/usr/bin/env python3
"""Independent audit of tagged default-tick versus full-rescan frame."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/'evaluation/reports/substrate_vision_hard_realtime_tag_gate_20260925.json';LOCK=ROOT/'evaluation/substrate_capability/vision_hard_realtime_tag_gate_lock_20260925.json';OUT=ROOT/'evaluation/reports/substrate_vision_hard_realtime_tag_gate_analysis_20260925.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 d=json.loads(RAW.read_text());l=json.loads(LOCK.read_text());p=d['provenance'];a,b=d['arms'];
 checks={'runner_protocol_seed_match':l['hashes']['runner']==p['runner_sha256'] and l['hashes']['protocol']==p['protocol_sha256'] and l['hashes']['seed']==p['seed_sha256'],'analyzer_hash':l['hashes']['analyzer']==sha(Path(__file__)),'extension_hash':l['native_extension_sha256']==p['native_extension_sha256'],'engine_source_current':p['engine_provenance']['source_match'] in ('own','shared') and not p['engine_provenance']['stale_rust'],'control_unfiltered_closure_progressed':a['progress']>0 and a['report']['status'] in ('fixed_point','repeated_graph_state'),'metadata_does_not_change_rule_count':a['rule_count']==b['rule_count'],'required_vision_rules_tagged':len(b['selected_rules'])==7 and all(q['latency_class']=='hard_realtime' for q in b['selected_rules']),'authored_rules_remain_untagged':all(q['latency_class']=='' for q in a['selected_rules']),'default_tick_progressed_under_tag':b['progress']>0 and b['progress']<200000,'relevant_states_exactly_equal':a['state']==b['state'],'responding_outputs_nonzero':b['max_sunit_act']>0 and b['max_sunit_rate']>0,'runner_checks_agree':all(d['checks'].values())}
 out={'run_id':'vision-hard-realtime-tag-gate-independent-audit','raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'analyzer_sha256':sha(Path(__file__)),'checks':checks,'pass':all(checks.values()),'interpretation':'On this registered frame, benchmark-only hard_realtime tagging makes default tick execute the vision pipeline and exactly matches unfiltered closure on recorded relevant state. This is single-frame evidence only.'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':checks,'pass':out['pass']},indent=2))
 if not out['pass']:raise SystemExit('independent hard-realtime tag audit failed')
if __name__=='__main__':main()
