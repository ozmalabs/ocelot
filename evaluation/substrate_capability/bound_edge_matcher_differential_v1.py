#!/usr/bin/env python3
"""Differential semantics gate for fully bound graph match clauses."""
from __future__ import annotations
import hashlib, json, os, random, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'runners/dsl/python'), str(ROOT)]
from domains.engine_provenance import assert_measuring_engine
from substrate_rs import _native

RUNNER = Path(__file__).resolve()
ANALYZER = ROOT / 'evaluation/substrate_capability/analyze_bound_edge_matcher_differential_v1.py'
PROTOCOL = ROOT / 'docs/research/engine_substrate/SUBSTRATE_BOUND_EDGE_MATCHER_DIFFERENTIAL_V1_PREREG_20261005.md'
LOCK = ROOT / 'evaluation/substrate_capability/bound_edge_matcher_differential_v1_lock_20261005.json'
OUT = ROOT / 'evaluation/reports/bound_edge_matcher_differential_v1_20261005.json'
SOURCES = ('domains/engine_provenance.py', 'runners/dsl/src/py.rs', 'runners/dsl/src/rewrite.rs',
           'runners/dsl/src/graph.rs', 'runners/dsl/src/substrate.rs', 'runners/dsl/src/term.rs',
           'runners/dsl/src/grammar.rs', 'runners/dsl/src/checker.rs',
           'runners/dsl/python/substrate_rs/__init__.py',
           'runners/dsl/python/substrate_rs/_native.build.json', 'runners/dsl/Cargo.lock')
DENSITIES = (0.0, 0.1, 0.5, 1.0)
REPLICATES = 8
NODE_COUNT = 12

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def manifest():
    provenance = assert_measuring_engine()
    return {'runner_sha256': sha(RUNNER), 'analyzer_sha256': sha(ANALYZER),
        'protocol_sha256': sha(PROTOCOL), 'engine_fingerprint': provenance['source_fingerprint'],
        'native_sha256': sha(Path(_native.__file__).resolve()),
        'sources': {path: sha(ROOT / path) for path in SOURCES}}
def panels():
    return [{'density': density, 'replicate': rep, 'seed': 202610051700 + int(density * 100) * 100 + rep}
        for density in DENSITIES for rep in range(REPLICATES)]
def v(name): return {'type': 'Var', 'name': name}
def lit(value): return {'type': 'Lit', 'value': value}

def install(substrate):
    for src, edge, tgt in (
        ('MatchEpisode', 'selected_family', 'MatchFamily'),
        ('MatchEpisode', 'left_member', 'MatchItem'),
        ('MatchEpisode', 'right_member', 'MatchItem'),
        ('MatchItem', 'candidate_link', 'MatchItem'),
        ('MatchItem', 'decoy_link', 'MatchItem'),
        ('MatchItem', 'witness', 'MatchItem'),
    ):
        substrate.add_production({'src': {'type': src, 'var': 'src'}, 'edge_type': edge,
            'tgt': {'type': tgt, 'var': 'tgt'}, 'provenance': 'evaluation:bound_edge_matcher_differential_v1'})
    substrate.add_rule_preserving_match_order({'name': 'bound_edge_exact_witness',
        'match': [['episode', 'selected_family', 'family'],
                  ['episode', 'left_member', 'source_item'],
                  ['episode', 'right_member', 'target_item'],
                  ['source_item', 'candidate_link', 'target_item']],
        'effects': [['add_edge', 'source_item', 'witness', 'target_item']]})

def digest_pairs(pairs):
    return hashlib.sha256(json.dumps(sorted([list(x) for x in pairs]), separators=(',', ':')).encode()).hexdigest()

def worker(panel, locked):
    before = manifest()
    if before != locked: raise RuntimeError('source lock drift')
    density, seed = panel['density'], panel['seed']
    rng = random.Random(seed)
    substrate = _native.Substrate(); install(substrate)
    episode = substrate.add_node('MatchEpisode', {})
    family = substrate.add_node('MatchFamily', {})
    substrate.add_edge(episode, 'selected_family', family, None)
    nodes = [substrate.add_node('MatchItem', {'ordinal': float(i)}) for i in range(NODE_COUNT)]
    left = list(range(0, 8)); right = list(range(4, 12))
    for i in left: substrate.add_edge(episode, 'left_member', nodes[i], None)
    for i in right: substrate.add_edge(episode, 'right_member', nodes[i], None)
    candidates = [(i, j) for i in left for j in right if i != j]
    if density == 1.0: selected = list(candidates)
    elif density == 0.0: selected = []
    else: selected = [pair for pair in candidates if rng.random() < density]
    decoys = [pair for pair in candidates if rng.random() < 0.35]
    rng.shuffle(selected)
    split = len(selected) // 2
    first, second = selected[:split], selected[split:]
    for i, j in decoys: substrate.add_edge(nodes[i], 'decoy_link', nodes[j], None)
    for i, j in first: substrate.add_edge(nodes[i], 'candidate_link', nodes[j], None)
    t0 = time.perf_counter_ns(); substrate.run_rules(10000); first_closure_ns = time.perf_counter_ns() - t0
    # Read witness pairs in ordinal coordinates.
    node_ord = {node: i for i, node in enumerate(nodes)}
    def witnesses():
        return {(i, node_ord[j]) for i in left for j in substrate.neighbours(nodes[i], 'witness') if j in node_ord}
    observed_first = witnesses()
    expected_first = set(first)
    # Add remaining selected relation edges and reach fixpoint again.
    for i, j in second: substrate.add_edge(nodes[i], 'candidate_link', nodes[j], None)
    t1 = time.perf_counter_ns(); substrate.run_rules(10000); second_closure_ns = time.perf_counter_ns() - t1
    observed_final = witnesses()
    expected_final = set(selected)
    decoy_digest = digest_pairs(decoys)
    after = manifest()
    return {'density': density, 'replicate': panel['replicate'], 'seed': seed, 'node_count': NODE_COUNT,
        'left_count': len(left), 'right_count': len(right), 'candidate_pair_count': len(candidates),
        'selected_relation_count': len(selected), 'first_relation_count': len(first),
        'second_relation_count': len(second), 'decoy_relation_count': len(decoys),
        'first_relation_sha256': digest_pairs(first), 'final_relation_sha256': digest_pairs(selected),
        'decoy_relation_sha256': decoy_digest,
        'first_witness_sha256': digest_pairs(observed_first), 'expected_first_witness_sha256': digest_pairs(expected_first),
        'final_witness_sha256': digest_pairs(observed_final), 'expected_final_witness_sha256': digest_pairs(expected_final),
        'first_witness_count': len(observed_first), 'expected_first_witness_count': len(expected_first),
        'final_witness_count': len(observed_final), 'expected_final_witness_count': len(expected_final),
        'first_phase_parity': observed_first == expected_first, 'final_phase_parity': observed_final == expected_final,
        'source_stable': before == after, 'source_before': before, 'source_after': after,
        'first_closure_ns': first_closure_ns, 'second_closure_ns': second_closure_ns}

def main():
    args = sys.argv[1:]
    if args == ['--lock']:
        if LOCK.exists() or OUT.exists(): raise SystemExit('refusing overwrite')
        LOCK.write_text(json.dumps({'schema': 'BoundEdgeMatcherDifferentialV1Lock', 'inputs': manifest(),
            'panels': panels(), 'densities': list(DENSITIES), 'replicates': REPLICATES,
            'node_count': NODE_COUNT}, indent=2, sort_keys=True) + '\n')
        print(LOCK.relative_to(ROOT)); return 0
    if args == ['--worker']:
        lock = json.loads(LOCK.read_text()); panel = json.loads(sys.stdin.read())
        print(json.dumps(worker(panel, lock['inputs']), sort_keys=True, separators=(',', ':'))); return 0
    if args == ['--run']:
        lock = json.loads(LOCK.read_text())
        if manifest() != lock['inputs']: raise SystemExit('source lock drift')
        env = {**os.environ, 'PYTHONPATH': f'{ROOT}/runners/dsl/python:{ROOT}', 'OZMA_NO_LLM': '1'}
        workers, failures = [], []
        for panel in lock['panels']:
            proc = subprocess.run([sys.executable, str(RUNNER), '--worker'], input=json.dumps(panel),
                cwd=ROOT, env=env, text=True, capture_output=True)
            if proc.returncode: failures.append({'panel': panel, 'stderr': proc.stderr[-2000:]})
            else: workers.append(json.loads(proc.stdout.strip().splitlines()[-1]))
        after = manifest()
        checks = {'source_stable': after == lock['inputs'] and all(w['source_stable'] for w in workers),
            'thirty_two_workers': len(workers) == 32, 'all_workers_ok': not failures,
            'first_phase_oracle_parity': all(w['first_phase_parity'] for w in workers),
            'final_phase_oracle_parity': all(w['final_phase_parity'] for w in workers),
            'empty_and_complete_controls': all((w['density'] != 0 or w['selected_relation_count'] == 0) and
                (w['density'] != 1 or w['selected_relation_count'] == w['candidate_pair_count']) for w in workers),
            'mutation_additions_exact': all(w['final_witness_count'] - w['first_witness_count'] == w['second_relation_count'] for w in workers),
            'left_out_and_source_attribution': all(w['candidate_pair_count'] > 0 and w['node_count'] == NODE_COUNT for w in workers)}
        result = {'schema': 'BoundEdgeMatcherDifferentialV1Capture', 'lock_sha256': sha(LOCK),
            'locked_inputs': lock['inputs'], 'post_run_inputs': after, 'checks': checks,
            'passed': all(checks.values()), 'workers': workers, 'failures': failures,
            'limits': 'Targeted exact semantic differential of the fully bound edge matcher clause; small generated graphs, not general matcher proof.'}
        OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
        print(json.dumps({'passed': result['passed'], 'checks': checks, 'output': OUT.relative_to(ROOT).as_posix()}))
        return 0 if result['passed'] else 2
    raise SystemExit('usage: --lock | --run | --worker')

if __name__ == '__main__': raise SystemExit(main())
