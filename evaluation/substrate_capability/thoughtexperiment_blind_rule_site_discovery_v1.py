#!/usr/bin/env python3
"""Probe trace-guided structural candidate discovery without target/cue args."""
from __future__ import annotations
import hashlib, json, os, platform, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'runners/dsl/python'), str(ROOT / 'evaluation/substrate_capability')]
RUNNER = Path(__file__).resolve()
PROTOCOL = ROOT / 'docs/research/engine_substrate/THOUGHTEXPERIMENT_BLIND_RULE_SITE_DISCOVERY_V1_PREREG_20261002.md'
BASE = ROOT / 'evaluation/substrate_capability/thoughtexperiment_bidirectional_edge_identity_guards_v1_1.py'
EDITOPS = ROOT / 'domains/edit_ops.py'
LOCK = ROOT / 'evaluation/substrate_capability/thoughtexperiment_blind_rule_site_discovery_v1_lock_20261002.json'
OUT = ROOT / 'evaluation/reports/thoughtexperiment_blind_rule_site_discovery_v1_20261002.json'
ANALYZER = ROOT / 'evaluation/substrate_capability/analyze_thoughtexperiment_blind_rule_site_discovery_v1.py'
ANALYSIS = ROOT / 'evaluation/reports/thoughtexperiment_blind_rule_site_discovery_v1_analysis_20261002.json'
WORKERS = 3

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def frozen() -> dict:
    from substrate_rs import _native
    return {'runner': sha(RUNNER), 'protocol': sha(PROTOCOL), 'base_fixture': sha(BASE),
            'edit_ops': sha(EDITOPS), 'analyzer': sha(ANALYZER),
            'loaded_native_binary': sha(Path(_native.__file__).resolve())}

def discover(report: dict, rules: dict) -> list[dict]:
    """Input is only the write report and active rules; no target/cue arguments."""
    from domains.edit_ops import find_edge_identity_sites, apply_add_edge_identity_guard
    writer_names = []
    for event in report['rule_write_events']:
        if event['progressed'] and (event['node_ids'] or event['edges']):
            name = event['rule_name']
            if name in rules and name not in writer_names:
                writer_names.append(name)
    proposals = []
    for name in writer_names:
        rule = rules[name]
        sites = [site for site in find_edge_identity_sites(rule) if site.get('scope', 'edge') == 'edge']
        for site in sites:
            variant = apply_add_edge_identity_guard(rule, site, 'blind_candidate')
            if variant is None:
                continue
            canonical = json.dumps(variant, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
            proposal_id = hashlib.sha256(canonical.encode()).hexdigest()
            proposals.append({'proposal_id': proposal_id, 'site': site, 'source_rule': name})
    return proposals

def worker(index: int) -> dict:
    import importlib.util
    spec = importlib.util.spec_from_file_location('blind_rule_site_base', BASE)
    base = importlib.util.module_from_spec(spec); sys.modules[spec.name] = base; spec.loader.exec_module(base)
    from domains.engine_provenance import build_is_stale
    if build_is_stale(str(ROOT)):
        raise RuntimeError('native engine is stale')
    before = frozen()
    ctx = base.recurrence_context(index, 'blind_discovery', 0, fault=True)
    ctx['add_due'](0)
    report = ctx['native'].run_rules_delta_report(1, False)
    active_rules = {row['name']: row for row in ctx['native'].export_rules() if row.get('active', True)}
    rule_store_before_discovery = ctx['native'].export_rules()
    # Deliberately do not pass ctx['target'] or any cue/label into discover().
    proposals = discover(report, active_rules)
    target_oracle = ctx['target']
    rows = ctx['native'].export_rules()
    target_in_pool = any(p['source_rule'] == target_oracle for p in proposals)
    after = frozen()
    return {'worker': index, 'source_before': before, 'source_after': after,
            'source_stable': before == after, 'report': {
                'status': report['status'], 'progress_steps': report['progress_steps'],
                'event_count': len(report['rule_write_events']),
                'dropped': report['rule_write_events_dropped'],
                'progressed_writer_count': len({e['rule_name'] for e in report['rule_write_events']
                    if e['progressed'] and (e['node_ids'] or e['edges'])}),
                'progressed_writer_names': sorted({e['rule_name'] for e in report['rule_write_events']
                    if e['progressed'] and (e['node_ids'] or e['edges'])})},
            'active_rule_count': len(active_rules), 'proposal_count': len(proposals),
            'proposal_ids': [p['proposal_id'] for p in proposals],
            'candidate_sites': [p['site'] for p in proposals],
            'candidate_source_rules': [p['source_rule'] for p in proposals],
            'target_oracle_used_by_discovery': False, 'cue_used_by_discovery': False,
            'target_present_in_candidate_origins': target_in_pool,
            'primary_rule_store_unchanged_by_discovery': rows == rule_store_before_discovery}

def main() -> int:
    args = sys.argv[1:]
    if args[:1] == ['--worker']:
        print(json.dumps(worker(int(args[1])), sort_keys=True, separators=(',', ':'))); return 0
    if args == ['--lock']:
        if LOCK.exists() or OUT.exists() or ANALYSIS.exists(): raise SystemExit('refusing to overwrite locked artifacts')
        LOCK.write_text(json.dumps({'schema': 'ThoughtexperimentBlindRuleSiteDiscoveryV1Lock',
            'sources': frozen(), 'workers': WORKERS, 'fixture': 'recurrence duplicate-offer fault',
            'observer_progress_budget': 1, 'candidate_operator': 'edge identity guard'}, indent=2, sort_keys=True) + '\n')
        print(LOCK.relative_to(ROOT)); return 0
    if args == ['--run']:
        lock = json.loads(LOCK.read_text())
        if frozen() != lock['sources']: raise SystemExit('source drift from lock')
        env = {**os.environ, 'PYTHONPATH': f'{ROOT}/runners/dsl/python:{ROOT}:{ROOT}/evaluation/substrate_capability'}
        workers = []
        for i in range(lock['workers']):
            proc = subprocess.run([sys.executable, str(RUNNER), '--worker', str(i)], cwd=ROOT,
                env=env, text=True, capture_output=True, timeout=180)
            if proc.returncode: raise RuntimeError(f'worker {i} failed: {proc.stderr[-2000:]}')
            workers.append(json.loads(proc.stdout.strip().splitlines()[-1]))
        if frozen() != lock['sources']: raise SystemExit('source drift during capture')
        OUT.write_text(json.dumps({'schema': 'ThoughtexperimentBlindRuleSiteDiscoveryV1Results',
            'lock_sha256': sha(LOCK), 'captured_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'host': platform.platform(), 'sources': frozen(), 'workers': workers}, indent=2, sort_keys=True) + '\n')
        print(OUT.relative_to(ROOT)); return 0
    if args == ['--analyze']:
        proc = subprocess.run([sys.executable, str(ANALYZER), str(OUT)], cwd=ROOT, text=True, capture_output=True)
        if proc.returncode: raise RuntimeError(proc.stderr)
        print(proc.stdout.strip()); return 0
    raise SystemExit('usage: --lock, --run, --analyze, or --worker ID')

if __name__ == '__main__': raise SystemExit(main())
