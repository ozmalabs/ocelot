#!/usr/bin/env python3
"""Independent integrity checks for trace-guided edit-site discovery v1."""
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCK = ROOT / 'evaluation/substrate_capability/thoughtexperiment_blind_rule_site_discovery_v1_lock_20261002.json'
OUT = ROOT / 'evaluation/reports/thoughtexperiment_blind_rule_site_discovery_v1_analysis_20261002.json'
TARGET = 'mrl_offer_due_once'
EXPECTED = {('out', 'agent', 'observed'), ('out', 'candidate', 'has_mint_offer'), ('out', 'episode', 'has_mint_offer')}

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def analyze(path):
    capture = json.loads(Path(path).read_text()); lock = json.loads(LOCK.read_text()); checks = []
    checks.append(('capture_schema', capture.get('schema') == 'ThoughtexperimentBlindRuleSiteDiscoveryV1Results'))
    checks.append(('lock_binding', capture.get('lock_sha256') == sha(LOCK)))
    checks.append(('source_binding', capture.get('sources') == lock['sources']))
    checks.append(('worker_count', len(capture.get('workers', [])) == lock['workers']))
    for row in capture.get('workers', []):
        idx = row['worker']; sites = row['candidate_sites']
        got = {(s['direction'], s['var'], s['edge_type']) for s in sites}
        checks.extend([
            (f'w{idx}_source_stable', row['source_stable'] and row['source_before'] == lock['sources'] and row['source_after'] == lock['sources']),
            (f'w{idx}_trace_complete', row['report']['dropped'] == 0 and row['report']['event_count'] > 0),
            (f'w{idx}_target_not_passed', row['target_oracle_used_by_discovery'] is False and row['cue_used_by_discovery'] is False),
            (f'w{idx}_target_found', row['target_present_in_candidate_origins'] is True and TARGET in row['candidate_source_rules']),
            (f'w{idx}_candidate_sites_exact', got == EXPECTED and len(sites) == 3),
            (f'w{idx}_narrowed_search', row['proposal_count'] == 3 and row['active_rule_count'] > row['proposal_count']),
            (f'w{idx}_primary_unchanged', row['primary_rule_store_unchanged_by_discovery'] is True),
        ])
    result = {'schema':'ThoughtexperimentBlindRuleSiteDiscoveryV1Analysis','passed':sum(v for _,v in checks),
              'total':len(checks),'checks':[{'name':n,'passed':bool(v)} for n,v in checks],
              'workers':capture.get('workers',[]),
              'interpretation':'Activity-trace-guided candidate narrowing on one authored fixture; semantic rule names remain visible, and causal necessity, ranking, abstention, held-out utility, and generalization are untested.'}
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(f"{result['passed']}/{result['total']} checks; {OUT.relative_to(ROOT)}")
    return 0 if all(v for _,v in checks) else 1

if __name__ == '__main__': raise SystemExit(analyze(sys.argv[1]))
