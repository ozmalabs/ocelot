#!/usr/bin/env python3
"""Source-locked scale measurement for native probe eligibility and selection."""
from __future__ import annotations
import hashlib, json, os, random, resource, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'runners/dsl/python'), str(ROOT)]
from domains.engine_provenance import assert_measuring_engine
from substrate_rs import _native

RUNNER = Path(__file__).resolve()
ANALYZER = ROOT / 'evaluation/substrate_capability/analyze_native_query_eligibility_scale_v1.py'
PROTOCOL = ROOT / 'docs/research/engine_substrate/SUBSTRATE_NATIVE_QUERY_ELIGIBILITY_SCALE_V1_PREREG_20261005.md'
LOCK = ROOT / 'evaluation/substrate_capability/native_query_eligibility_scale_v1_lock_20261005.json'
OUT = ROOT / 'evaluation/reports/native_query_eligibility_scale_v1_20261005.json'
SOURCES = ('domains/engine_provenance.py', 'runners/dsl/src/py.rs', 'runners/dsl/src/term.rs',
           'runners/dsl/src/grammar.rs', 'runners/dsl/src/checker.rs', 'runners/dsl/src/rewrite.rs',
           'runners/dsl/src/substrate.rs', 'runners/dsl/src/graph.rs',
           'runners/dsl/python/substrate_rs/__init__.py',
           'runners/dsl/python/substrate_rs/_native.build.json', 'runners/dsl/Cargo.lock')
SIZES = (512, 1024, 2048, 4096, 8192)
REPLICATES = 5

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def manifest():
    provenance = assert_measuring_engine()
    return {'runner_sha256': sha(RUNNER), 'analyzer_sha256': sha(ANALYZER),
            'protocol_sha256': sha(PROTOCOL), 'engine_fingerprint': provenance['source_fingerprint'],
            'native_sha256': sha(Path(_native.__file__).resolve()),
            'sources': {path: sha(ROOT / path) for path in SOURCES}}

def panels():
    return [{'size': size, 'replicate': rep, 'seed': 2026100500 + size * 7 + rep}
            for size in SIZES for rep in range(REPLICATES)]

def v(name): return {'type': 'Var', 'name': name}
def a(name, key): return {'type': 'Attr', 'node': v(name), 'key': key}
def lit(value): return {'type': 'Lit', 'value': value}
def comp(term): return {'__term__': term}
def eq(left, right): return {'type': 'Eq', 'a': left, 'b': right}
def neighbours(node, edge): return {'type': 'Neighbours', 'node': node, 'edge_type': edge, 'any_type': False}

def install(substrate):
    for src, edge, tgt in (
        ('EligibilityEpisode', 'selected_family', 'EligibilityFamily'),
        ('EligibilityFamily', 'has_vote', 'EligibilityVote'),
        ('EligibilityVote', 'vote_for_example', 'EligibilityExample'),
        ('EligibilityEpisode', 'has_probe_example', 'EligibilityExample'),
        ('EligibilityEpisode', 'eligible_candidate_probe', 'EligibilityExample'),
    ):
        substrate.add_production({'src': {'type': src, 'var': 'src'}, 'edge_type': edge,
                                  'tgt': {'type': tgt, 'var': 'tgt'},
                                  'provenance': 'evaluation:native_query_eligibility_scale_v1'})
    eligible = {'type': 'And', 'items': [eq(a('episode', 'stage'), lit('probe_prepare')),
                                        eq(a('vote', 'prediction'), lit(True))]}
    substrate.add_rule({'name': 'eligibility_scale_positive_filter',
        'match': [['episode', 'selected_family', 'family'],
                  ['episode', 'has_probe_example', 'example'],
                  ['family', 'has_vote', 'vote'], ['vote', 'vote_for_example', 'example']],
        'where': eligible,
        'effects': [['add_edge', 'episode', 'eligible_candidate_probe', 'example']]})
    choice = {'type': 'ArgminUnique', 'source': neighbours(v('episode'), 'eligible_candidate_probe'),
              'var_name': 'candidate',
              'value': {'type': 'IfThenElse', 'cond': eq(a('candidate', 'queried'), lit(True)),
                        'then': lit(1_000_000.0), 'other': a('candidate', 'probe_rank')},
              'default': None}
    substrate.add_rule({'name': 'eligibility_scale_native_argmin',
        'match': [['episode', 'selected_family', 'family']],
        'where': eq(a('episode', 'stage'), lit('query_select')),
        'effects': [['set_attr', 'episode', 'selected_query_node', comp(choice)],
                    ['set_attr', 'episode', 'stage', comp(lit('selected'))]]})

def worker(panel, locked):
    before = manifest()
    if before != locked: raise RuntimeError('source lock drift')
    cpu_start, wall_start = time.process_time_ns(), time.perf_counter_ns()
    substrate = _native.Substrate(); install(substrate)
    episode = substrate.add_node('EligibilityEpisode', {'stage': 'init'})
    family = substrate.add_node('EligibilityFamily', {'kind': 'candidate'})
    substrate.add_edge(episode, 'selected_family', family, None)
    size, seed = panel['size'], panel['seed']
    rng = random.Random(seed)
    predictions = [bool(i % 2) for i in range(size)]
    rng.shuffle(predictions)
    ranks = list(range(size)); random.Random(seed ^ 0x5A17).shuffle(ranks)
    expected = {i for i, prediction in enumerate(predictions) if prediction}
    build_start = time.perf_counter_ns()
    example_nodes = []
    for i, (prediction, rank) in enumerate(zip(predictions, ranks)):
        example = substrate.add_node('EligibilityExample',
            {'probe_rank': float(rank), 'queried': False, 'ordinal': float(i)})
        vote = substrate.add_node('EligibilityVote', {'prediction': prediction})
        substrate.add_edge(episode, 'has_probe_example', example, None)
        substrate.add_edge(family, 'has_vote', vote, None)
        substrate.add_edge(vote, 'vote_for_example', example, None)
        example_nodes.append(example)
    graph_build_ns = time.perf_counter_ns() - build_start
    substrate.set_attr(episode, 'stage', 'probe_prepare')
    t = time.perf_counter_ns(); substrate.run_rules(10000); eligibility_ns = time.perf_counter_ns() - t
    eligible_nodes = set(substrate.neighbours(episode, 'eligible_candidate_probe'))
    node_to_ordinal = {node: i for i, node in enumerate(example_nodes)}
    eligible_ordinals = sorted(node_to_ordinal[node] for node in eligible_nodes)
    substrate.set_attr(episode, 'stage', 'query_select')
    t = time.perf_counter_ns(); substrate.run_rules(10000); selection_ns = time.perf_counter_ns() - t
    selected_node = substrate.node(episode)['attrs'].get('selected_query_node')
    expected_selected = min(expected, key=lambda i: ranks[i]) if expected else None
    expected_node = example_nodes[expected_selected] if expected_selected is not None else None
    selected_ordinal = node_to_ordinal.get(selected_node)
    after = manifest()
    return {'size': size, 'replicate': panel['replicate'], 'seed': seed,
        'prediction_positive_count': len(expected), 'eligible_count': len(eligible_nodes),
        'eligible_ordinals_sha256': hashlib.sha256(json.dumps(eligible_ordinals, separators=(',', ':')).encode()).hexdigest(),
        'expected_eligible_ordinals_sha256': hashlib.sha256(json.dumps(sorted(expected), separators=(',', ':')).encode()).hexdigest(),
        'eligible_identity_parity': eligible_nodes == {example_nodes[i] for i in expected},
        'selected_identity_parity': selected_node == expected_node,
        'selected_ordinal': selected_ordinal, 'expected_selected_ordinal': expected_selected,
        'selected_rank': ranks[selected_ordinal] if selected_ordinal is not None else None,
        'selected_count': int(selected_node is not None), 'source_stable': before == after,
        'source_before': before, 'source_after': after,
        'graph_build_ns': graph_build_ns, 'eligibility_closure_ns': eligibility_ns,
        'selection_closure_ns': selection_ns, 'worker_cpu_ns': time.process_time_ns() - cpu_start,
        'worker_wall_ns': time.perf_counter_ns() - wall_start,
        'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}

def main():
    args = sys.argv[1:]
    if args == ['--lock']:
        if LOCK.exists() or OUT.exists(): raise SystemExit('refusing overwrite')
        LOCK.write_text(json.dumps({'schema': 'NativeQueryEligibilityScaleV1Lock', 'inputs': manifest(),
            'panels': panels(), 'sizes': list(SIZES), 'replicates': REPLICATES}, indent=2, sort_keys=True) + '\n')
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
                  'twenty_five_workers': len(workers) == 25, 'all_workers_ok': not failures,
                  'eligible_count_matches': all(w['eligible_count'] == w['prediction_positive_count'] for w in workers),
                  'eligible_identity_parity': all(w['eligible_identity_parity'] for w in workers),
                  'selected_identity_parity': all(w['selected_identity_parity'] for w in workers),
                  'unique_selection': all(w['selected_count'] == 1 for w in workers),
                  'positive_and_negative_present': all(0 < w['eligible_count'] < w['size'] for w in workers)}
        report = {'schema': 'NativeQueryEligibilityScaleV1Capture', 'lock_sha256': sha(LOCK),
                  'locked_inputs': lock['inputs'], 'post_run_inputs': after, 'checks': checks,
                  'passed': all(checks.values()), 'workers': workers, 'failures': failures,
                  'limits': 'Synthetic graph-level population scale for the v1.3 native eligibility and selection rule shapes; not natural task prevalence or an asymptotic complexity proof.'}
        OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
        print(json.dumps({'passed': report['passed'], 'checks': checks, 'output': OUT.relative_to(ROOT).as_posix()}))
        return 0 if report['passed'] else 2
    raise SystemExit('usage: --lock | --run | --worker')

if __name__ == '__main__': raise SystemExit(main())
