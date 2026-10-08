#!/usr/bin/env python3
"""Multi-shape semantic differential for fully bound matcher clauses."""
from __future__ import annotations
import hashlib, json, os, random, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'runners/dsl/python'), str(ROOT)]
from domains.engine_provenance import assert_measuring_engine
from substrate_rs import _native

RUNNER = Path(__file__).resolve()
ANALYZER = ROOT / 'evaluation/substrate_capability/analyze_bound_edge_matcher_differential_v3.py'
PROTOCOL = ROOT / 'docs/research/engine_substrate/SUBSTRATE_BOUND_EDGE_MATCHER_DIFFERENTIAL_V3_PREREG_20261005.md'
LOCK = ROOT / 'evaluation/substrate_capability/bound_edge_matcher_differential_v3_lock_20261005.json'
OUT = ROOT / 'evaluation/reports/bound_edge_matcher_differential_v3_20261005.json'
SOURCES = ('domains/engine_provenance.py', 'runners/dsl/src/py.rs', 'runners/dsl/src/rewrite.rs',
           'runners/dsl/src/graph.rs', 'runners/dsl/src/substrate.rs', 'runners/dsl/src/term.rs',
           'runners/dsl/src/grammar.rs', 'runners/dsl/src/checker.rs',
           'runners/dsl/python/substrate_rs/__init__.py',
           'runners/dsl/python/substrate_rs/_native.build.json', 'runners/dsl/Cargo.lock')
DENSITIES = (0.0, 0.1, 0.5, 1.0)
REPLICATES = 8
NODE_COUNT = 12
RULES = ('left_to_right', 'right_to_left', 'repeated_self_loop', 'bound_attribute_predicate')

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def manifest():
    provenance = assert_measuring_engine()
    return {'runner_sha256': sha(RUNNER), 'analyzer_sha256': sha(ANALYZER),
        'protocol_sha256': sha(PROTOCOL), 'engine_fingerprint': provenance['source_fingerprint'],
        'native_sha256': sha(Path(_native.__file__).resolve()),
        'sources': {path: sha(ROOT / path) for path in SOURCES}}
def panels():
    return [{'density': d, 'replicate': r, 'seed': 202610052300 + int(d * 100) * 100 + r}
        for d in DENSITIES for r in range(REPLICATES)]
def v(name): return {'type': 'Var', 'name': name}
def a(name, key): return {'type': 'Attr', 'node': v(name), 'key': key}
def lit(value): return {'type': 'Lit', 'value': value}
def eq(left, right): return {'type': 'Eq', 'a': left, 'b': right}

def install(substrate):
    for src, edge, tgt in (
        ('MatchEpisode', 'selected_family', 'MatchFamily'),
        ('MatchEpisode', 'left_member', 'MatchItem'),
        ('MatchEpisode', 'right_member', 'MatchItem'),
        ('MatchItem', 'candidate_link', 'MatchItem'),
        ('MatchItem', 'decoy_link', 'MatchItem'),
        ('MatchItem', 'witness_lr', 'MatchItem'),
        ('MatchItem', 'witness_rl', 'MatchItem'),
        ('MatchItem', 'witness_loop', 'MatchItem'),
        ('MatchItem', 'witness_where', 'MatchItem'),
    ):
        substrate.add_production({'src': {'type': src, 'var': 'src'}, 'edge_type': edge,
            'tgt': {'type': tgt, 'var': 'tgt'}, 'provenance': 'evaluation:bound_edge_matcher_differential_v3'})
    prefix = [['episode', 'selected_family', 'family'],
              ['episode', 'left_member', 'source_item'],
              ['episode', 'right_member', 'target_item']]
    rules = [
        ('bound_edge_left_to_right', prefix + [['source_item', 'candidate_link', 'target_item']],
         'source_item', 'witness_lr', None),
        ('bound_edge_right_to_left', prefix + [['target_item', 'candidate_link', 'source_item']],
         'source_item', 'witness_rl', None),
        ('bound_edge_repeated_self_loop', [['episode', 'selected_family', 'family'],
         ['episode', 'left_member', 'loop_item'], ['loop_item', 'candidate_link', 'loop_item']],
         'loop_item', 'witness_loop', None),
        ('bound_edge_attribute_predicate', prefix + [['source_item', 'candidate_link', 'target_item']],
         'source_item', 'witness_where', eq(a('source_item', 'bucket'), a('target_item', 'bucket'))),
    ]
    for name, match, source, witness_edge, where in rules:
        rule = {'name': name, 'match': match,
                'effects': [['add_edge', source, witness_edge,
                    'target_item' if witness_edge != 'witness_loop' else 'loop_item']]}
        if where is not None: rule['where'] = where
        substrate.add_rule_preserving_match_order(rule)

def digest(pairs):
    return hashlib.sha256(json.dumps(sorted([list(x) for x in pairs]), separators=(',', ':')).encode()).hexdigest()

def worker(panel, locked):
    before = manifest()
    if before != locked: raise RuntimeError('source lock drift')
    density, seed = panel['density'], panel['seed']; rng = random.Random(seed)
    substrate = _native.Substrate(); install(substrate)
    episode = substrate.add_node('MatchEpisode', {}); family = substrate.add_node('MatchFamily', {})
    substrate.add_edge(episode, 'selected_family', family, None)
    nodes = [substrate.add_node('MatchItem', {'ordinal': float(i), 'bucket': float(i % 3)}) for i in range(NODE_COUNT)]
    left, right = list(range(0, 8)), list(range(4, 12))
    for i in left: substrate.add_edge(episode, 'left_member', nodes[i], None)
    for j in right: substrate.add_edge(episode, 'right_member', nodes[j], None)
    universe = [(i, j) for i in range(NODE_COUNT) for j in range(NODE_COUNT)]
    if density == 1.0: selected = list(universe)
    elif density == 0.0: selected = []
    else: selected = [pair for pair in universe if rng.random() < density]
    decoys = [pair for pair in universe if rng.random() < 0.25]
    rng.shuffle(selected); split = len(selected) // 2
    first, second = selected[:split], selected[split:]
    for i, j in decoys: substrate.add_edge(nodes[i], 'decoy_link', nodes[j], None)
    for i, j in first: substrate.add_edge(nodes[i], 'candidate_link', nodes[j], None)
    def closure():
        t = time.perf_counter_ns(); substrate.run_rules(10000); return time.perf_counter_ns() - t
    first_ns = closure()
    node_ord = {node: i for i, node in enumerate(nodes)}
    def observed(edge):
        return {(i, node_ord[j]) for i in range(NODE_COUNT) for j in substrate.neighbours(nodes[i], edge) if j in node_ord}
    left_right = {(i, j) for i in left for j in right if i != j and (i, j) in set(first)}
    right_left = {(i, j) for i in left for j in right if i != j and (j, i) in set(first)}
    loops = {(i, i) for i in left if (i, i) in set(first)}
    where_pairs = {(i, j) for i in left for j in right if i != j and (i, j) in set(first) and i % 3 == j % 3}
    expected_first = {'witness_lr': left_right, 'witness_rl': right_left,
        'witness_loop': loops, 'witness_where': where_pairs}
    observed_first = {edge: observed(edge) for edge in expected_first}
    for i, j in second: substrate.add_edge(nodes[i], 'candidate_link', nodes[j], None)
    second_ns = closure()
    relation = set(selected)
    expected_final = {
        'witness_lr': {(i, j) for i in left for j in right if i != j and (i, j) in relation},
        'witness_rl': {(i, j) for i in left for j in right if i != j and (j, i) in relation},
        'witness_loop': {(i, i) for i in left if (i, i) in relation},
        'witness_where': {(i, j) for i in left for j in right if i != j and (i, j) in relation and i % 3 == j % 3},
    }
    observed_final = {edge: observed(edge) for edge in expected_final}
    first_records = {edge: {'actual_sha256': digest(observed_first[edge]),
        'expected_sha256': digest(expected_first[edge]), 'actual_count': len(observed_first[edge]),
        'expected_count': len(expected_first[edge]), 'parity': observed_first[edge] == expected_first[edge]}
        for edge in expected_first}
    final_records = {edge: {'actual_sha256': digest(observed_final[edge]),
        'expected_sha256': digest(expected_final[edge]), 'actual_count': len(observed_final[edge]),
        'expected_count': len(expected_final[edge]), 'parity': observed_final[edge] == expected_final[edge]}
        for edge in expected_final}
    after = manifest()
    return {'density': density, 'replicate': panel['replicate'], 'seed': seed,
        'node_count': NODE_COUNT, 'candidate_edge_count': len(selected), 'decoy_edge_count': len(decoys),
        'first_edge_count': len(first), 'second_edge_count': len(second),
        'first_relation_sha256': digest(first), 'final_relation_sha256': digest(selected),
        'decoy_relation_sha256': digest(decoys), 'first_results': first_records, 'final_results': final_records,
        'source_stable': before == after, 'source_before': before, 'source_after': after,
        'first_closure_ns': first_ns, 'second_closure_ns': second_ns}

def main():
    args = sys.argv[1:]
    if args == ['--lock']:
        if LOCK.exists() or OUT.exists(): raise SystemExit('refusing overwrite')
        LOCK.write_text(json.dumps({'schema': 'BoundEdgeMatcherDifferentialV3Lock', 'inputs': manifest(),
            'panels': panels(), 'densities': list(DENSITIES), 'replicates': REPLICATES,
            'node_count': NODE_COUNT, 'rules': list(RULES)}, indent=2, sort_keys=True) + '\n')
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
            'all_first_phase_rule_oracles': all(r['parity'] for w in workers for r in w['first_results'].values()),
            'all_final_phase_rule_oracles': all(r['parity'] for w in workers for r in w['final_results'].values()),
            'empty_and_complete_controls': all((w['density'] != 0 or w['candidate_edge_count'] == 0) and
                (w['density'] != 1 or w['candidate_edge_count'] == NODE_COUNT ** 2) for w in workers)}
        result = {'schema': 'BoundEdgeMatcherDifferentialV3Capture', 'lock_sha256': sha(LOCK),
            'locked_inputs': lock['inputs'], 'post_run_inputs': after, 'checks': checks,
            'passed': all(checks.values()), 'workers': workers, 'failures': failures,
            'limits': 'Targeted semantic differential for directed, repeated-variable, attribute-predicate, decoy-type, and add-only mutation cases; not a general proof of matcher correctness.'}
        OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
        print(json.dumps({'passed': result['passed'], 'checks': checks, 'output': OUT.relative_to(ROOT).as_posix()}))
        return 0 if result['passed'] else 2
    raise SystemExit('usage: --lock | --run | --worker')

if __name__ == '__main__': raise SystemExit(main())
