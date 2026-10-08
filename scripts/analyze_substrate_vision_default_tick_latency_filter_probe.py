#!/usr/bin/env python3
"""Independent provenance and behavior checks for the latency-filter probe."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/'evaluation/reports/substrate_vision_default_tick_latency_filter_20260925.json';LOCK=ROOT/'evaluation/substrate_capability/vision_default_tick_latency_filter_lock_20260925.json';OUT=ROOT/'evaluation/reports/substrate_vision_default_tick_latency_filter_analysis_20260925.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 d=json.loads(RAW.read_text());l=json.loads(LOCK.read_text());p=d['provenance'];
 checks={'runner_protocol_hashes':l['hashes']['runner']==p['runner_sha256'] and l['hashes']['protocol']==p['protocol_sha256'],'analyzer_hash':l['hashes']['analyzer']==sha(Path(__file__)),'extension_hash':l['native_extension_sha256']==p['native_extension_sha256'],'engine_source_match':p['engine_provenance']['source_match'] in ('own','shared') and not p['engine_provenance']['stale_rust'],'policy_enabled':any(float(q.get('enabled',0))>.5 for q in d['policies']),'all_selected_vision_rules_untagged':len(d['vision_rule_latency'])==7 and all(not q['latency_class'] for q in d['vision_rule_latency']),'default_tick_zero':d['default_tick_progress']==0,'full_rescan_nonzero':d['unfiltered_report']['progress_steps']>0 and d['post_rescan_max_act']>0 and d['post_rescan_max_rate']>0,'runner_check_agrees':all(d['checks'].values())}
 out={'run_id':'vision-default-tick-latency-filter-independent-audit','raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'analyzer_sha256':sha(Path(__file__)),'checks':checks,'pass':all(checks.values()),'interpretation':'The enabled dual-process default routes to hard_realtime rules; selected vision rules have no latency_class and are skipped on this default tick. Unfiltered closure then progresses and responds. This supports a scheduling-class mismatch, not a missing attr-notification claim.'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':checks,'pass':out['pass']},indent=2))
 if not out['pass']:raise SystemExit('independent latency-filter analysis failed')
if __name__=='__main__':main()
