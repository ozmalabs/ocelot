#!/usr/bin/env python3
"""Three-seed confirmatory K=16 vision settle-scope comparison."""
from __future__ import annotations
import contextlib, hashlib, importlib, json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'runners/dsl/python'))
PROTOCOL = ROOT / 'docs/research/engine_substrate/SUBSTRATE_VISION_K16_SCOPE_MULTISEED_V1_PREREG_20260927.md'
AMENDMENT = ROOT / 'docs/research/engine_substrate/SUBSTRATE_VISION_K16_SCOPE_MULTISEED_V1_1_AMENDMENT_20260927.md'
LOCK = ROOT / 'evaluation/substrate_capability/vision_k16_scope_multiseed_v1_1_lock_20260927.json'
OUT = ROOT / 'evaluation/reports/substrate_vision_k16_scope_multiseed_v1_1_20260927.json'
ANALYZER = ROOT / 'scripts/analyze_substrate_vision_k16_scope_multiseed_v1_1.py'
SEEDS = (20260931, 20260932, 20260933)
MODULES = ('scripts.settle_lib', 'scripts.rung8_lib', 'scripts.rung8b_lib',
           'scripts.substrate_vision_settle_k16_scope_gate', 'domains.engine_provenance',
           'domains.seed_registry', 'domains.settle_world', 'domains.wave_world',
           'domains.onoff_world', 'domains.lateral_world', 'domains.complex_cells',
           'substrate.boot_core', 'substrate.seed_loader', 'substrate.seeds',
           'evaluation.p0a.legacy_io_guard')
RUST = ('py.rs', 'scale_audit.rs', 'rewrite.rs', 'substrate.rs', 'graph_rules.rs', 'term.rs', 'cognitive_cycle.rs')

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def inputs():
    for name in MODULES:
        importlib.import_module(name)
    from substrate.boot_core import CORE_SEEDS
    from substrate.seeds import REGISTRY
    seed_ids = set(CORE_SEEDS)
    seed_ids.update(s.id for s in REGISTRY.resolve(['vision_waves', 'vision_settle', 'vision_onoff', 'vision_lateral', 'vision_compose']))
    pending, seen, paths = list(seed_ids), set(), set()
    while pending:
        sid = str(pending.pop())
        if sid in seen: continue
        seen.add(sid)
        path = ROOT / 'seeds' / f'{sid}.json'
        if not path.is_file(): continue
        paths.add(path)
        try: pending.extend(str(x) for x in json.loads(path.read_text()).get('depends_on', ()))
        except (OSError, json.JSONDecodeError): pass
    for module in tuple(sys.modules.values()):
        filename = getattr(module, '__file__', None)
        if not filename: continue
        path = Path(filename).resolve()
        if path.suffix != '.py' or '__pycache__' in path.parts: continue
        try: rel = path.relative_to(ROOT)
        except ValueError: continue
        if any(part in {'domains', 'substrate', 'scripts', 'evaluation', 'runners'} for part in rel.parts):
            if path not in {Path(__file__).resolve(), ANALYZER.resolve()}: paths.add(path)
    from substrate_rs import _native
    from domains.engine_provenance import engine_provenance
    return {
        'protocol_sha256': sha(PROTOCOL), 'amendment_sha256': sha(AMENDMENT), 'runner_sha256': sha(__file__),
        'analyzer_sha256': sha(ANALYZER),
        'source_closure_sha256': {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(paths)},
        'rust_sha256': {name: sha(ROOT / 'runners/dsl/src' / name) for name in RUST},
        'native_extension_sha256': sha(Path(_native.__file__).resolve()),
        'native_build_manifest_sha256': sha(ROOT / 'runners/dsl/python/substrate_rs/_native.build.json'),
        'engine_provenance': engine_provenance(),
        'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
    }

def worker(seed):
    from domains.engine_provenance import engine_preamble
    engine_preamble()
    import scripts.substrate_vision_settle_k16_scope_gate as prior
    from substrate.seed_loader import manifest_for
    docs = {sid: manifest_for(sid) for sid in prior.TARGETS}
    # Prime lazy imports reached by graph boot and evaluation before snapshotting.
    import evaluation.p0a.legacy_io_guard  # noqa: F401
    started = inputs()
    arms = []
    progress_path = OUT.parent / f'{OUT.stem}_{seed}.log'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with progress_path.open('w') as progress, contextlib.redirect_stdout(progress):
        for scoped in (False, True):
            print(f'ARM START seed={seed} scope={"root_scoped" if scoped else "global"}', flush=True)
            q = prior.arm(seed, scoped, 'full_rescan', docs['vision_settle'])
            arms.append(q)
            print(f'ARM DONE seed={seed} scope={q["variant"]["scope"]} OSI={q["mean_osi"]:.6f}', flush=True)
            OUT.parent.mkdir(parents=True, exist_ok=True)
            OUT.with_suffix(f'.{seed}.partial.json').write_text(json.dumps({'seed': seed, 'completed_arms': arms}, indent=2, sort_keys=True) + '\n')
    return {'seed': seed, 'pid': os.getpid(), 'started_inputs': started, 'arms': arms,
            'finished_inputs': inputs()}

def main():
    if sys.argv[1:] == ['--lock']:
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        LOCK.write_text(json.dumps({'locked_inputs': inputs()}, indent=2, sort_keys=True) + '\n')
        print(LOCK); return
    if len(sys.argv) == 3 and sys.argv[1] == '--worker':
        print(json.dumps(worker(int(sys.argv[2])), sort_keys=True)); return
    locked = inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text())['locked_inputs'] != locked:
        raise SystemExit('missing or stale source lock')
    env = dict(os.environ); env.setdefault('OZMA_NO_LLM', '1'); env.setdefault('OZMA_SEED_PERSIST_DISABLED', '1')
    runs = []
    for seed in SEEDS:
        p = subprocess.run([sys.executable, str(Path(__file__).resolve()), '--worker', str(seed)], cwd=ROOT,
                           env=env, text=True, capture_output=True, check=True)
        runs.append(json.loads(p.stdout))
    post = inputs()
    checks = {
        'three_distinct_fresh_workers': len({r['pid'] for r in runs}) == 3,
        'all_seed_pairs_present': [r['seed'] for r in runs] == list(SEEDS),
        'source_stable_each_worker_and_after': post == locked and all(r['started_inputs'] == locked == r['finished_inputs'] for r in runs),
        'native_source_matches': locked['engine_provenance'].get('source_match') in ('own', 'shared') and not locked['engine_provenance'].get('stale_rust'),
        'two_full_rescan_arms_per_seed': all(len(r['arms']) == 2 and {a['variant']['scope'] for a in r['arms']} == {'global', 'root_scoped'} and all(a['variant']['executor'] == 'full_rescan' for a in r['arms']) for r in runs),
        'complete_root_membership': all(a['root_membership_count'] == a['n_units'] == 16 for r in runs for a in r['arms']),
        'recognized_noncap_statuses': all(set(a['adaptation_status_counts']) <= {'fixed_point', 'repeated_graph_state'} and set(a['probe_status_counts']) <= {'fixed_point', 'repeated_graph_state'} and a['all_reports'] > 0 for r in runs for a in r['arms']),
    }
    payload = {'schema_version': 1, 'run_id': 'vision-k16-scope-multiseed-v1-20260927', 'locked_inputs': locked,
               'post_run_inputs': post, 'runs': runs, 'checks': checks, 'pass': all(checks.values()),
               'claim_boundary': 'Three independent 4x4 sheets compare global and Retina-root-scoped st_settle under full-rescan execution after matched development/adaptation. This estimates repeatability only for this controlled workload; it is not task prevalence or a speedup result.'}
    OUT.parent.mkdir(parents=True, exist_ok=True); OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'output': str(OUT.relative_to(ROOT)), 'checks': checks}, indent=2))
    if not payload['pass']: raise SystemExit('multi-seed scope capture gate failed')

if __name__ == '__main__': main()
