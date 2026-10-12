#!/usr/bin/env python3
"""Sample memory during recurrence-ledger thoughtexperiment rule repair."""
from __future__ import annotations
import gc, hashlib, json, os, subprocess, sys, threading, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
RUNNER = Path(__file__).resolve()
RAW = ROOT / "evaluation/reports/thoughtexperiment_recurrence_repair_memory_v1_raw_20261001.json"
BACKENDS = {"full_copy": "fork_full_copy_experiment", "shared_pages": "fork_shared_graph_pages_experiment"}
SOURCES = (
    "docs/research/engine_substrate/THOUGHTEXPERIMENT_RECURRENCE_REPAIR_MEMORY_V1_PREREG_20261001.md",
    "evaluation/substrate_capability/thoughtexperiment_recurrence_repair_memory_v1.py",
    "evaluation/substrate_capability/thoughtexperiment_recurrence_offer_idempotence_v1.py",
    "substrate/boot_core.py", "substrate/seed_loader.py", "seeds/minting_recurrence_ledger.json",
    "runners/dsl/python/substrate_rs/__init__.py", "runners/dsl/src/cow_paged_vec.rs",
    "runners/dsl/src/graph.rs", "runners/dsl/src/substrate.rs", "runners/dsl/src/py.rs",
    "runners/dsl/src/persist.rs", "domains/engine_provenance.py",
)

def sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()

def smaps() -> dict[str, int]:
    out = {}
    for line in Path('/proc/self/smaps_rollup').read_text().splitlines():
        key, sep, val = line.partition(':')
        if sep and key in {'Rss','Pss','Private_Clean','Private_Dirty','Shared_Clean','Shared_Dirty','Swap'}:
            out[key] = int(val.strip().split()[0]) * 1024
    return out

def worker(size: int, backend: str, rep: int) -> dict:
    from evaluation.substrate_capability.thoughtexperiment_recurrence_offer_idempotence_v1 import make_case
    before = {p: sha(ROOT / p) for p in SOURCES}
    primary, native, authored, _candidate, fault_only = make_case()
    if not fault_only:
        raise RuntimeError('fault fixture did not remove only the authored negative-existence guard')
    previous = None
    for i in range(size):
        node = primary.add_node('ThoughtexperimentNoise', {'ordinal': i, 'partition': i % 32, 'payload': 'x' * 24})
        if previous is not None:
            primary.add_edge_unchecked(previous, 'te_noise_next', node)
        previous = node
    candidate = next(n for n in primary.nodes('PredicateRecurrenceCandidate')
                     if primary.node(n)['attrs'].get('recurrence_key') == 'audit-key')
    revision = native.experiment_graph_rule_revision()
    counts = (native.node_count(), native.edge_count())
    rules = json.dumps(native.export_rules(), sort_keys=True, default=str)
    gc.collect(); baseline = smaps(); samples = [baseline]; stop = threading.Event()
    def sampling():
        while not stop.wait(.01):
            try: samples.append(smaps())
            except (OSError, ValueError): pass
    monitor = threading.Thread(target=sampling, daemon=True); monitor.start()
    start = time.perf_counter_ns()
    branch = getattr(primary, BACKENDS[backend])(); bn = branch._inner
    idx = next(i for i, rule in enumerate(bn.export_rules())
               if rule.get('name') == 'mrl_offer_due_once' and rule.get('active', True))
    removed = bool(bn.remove_rule(idx)); bn.add_rule(authored)
    closure = [int(bn.run_rules(100)) for _ in range(5)]
    branch_candidate = next(n for n in branch.nodes('PredicateRecurrenceCandidate')
                            if branch.node(n)['attrs'].get('recurrence_key') == 'audit-key')
    offer_count = len(list(branch.neighbours(branch_candidate, 'has_mint_offer')))
    fixedpoint = int(bn.run_rules(100))
    active = next(r for r in bn.export_rules() if r.get('name') == 'mrl_offer_due_once' and r.get('active', True))
    duration_ms = (time.perf_counter_ns() - start) / 1e6
    samples.append(smaps()); del branch; gc.collect(); samples.append(smaps())
    stop.set(); monitor.join(); after = smaps()
    peak = {k: max(row.get(k, 0) for row in samples) for k in baseline}
    after_hashes = {p: sha(ROOT / p) for p in SOURCES}
    return {
        'pid': os.getpid(), 'size': size, 'backend': backend, 'replicate': rep,
        'sample_interval_ms': 10, 'sample_count': len(samples), 'duration_ms': duration_ms,
        'fault_only_guard_removed': fault_only, 'removed_fault_rule': removed,
        'restored_authored_where': active.get('where') == authored.get('where'),
        'closure_progress': closure, 'offer_count': offer_count, 'fixedpoint_progress': fixedpoint,
        'primary_revision_unchanged': native.experiment_graph_rule_revision() == revision,
        'primary_counts_unchanged': (native.node_count(), native.edge_count()) == counts,
        'primary_rules_unchanged': json.dumps(native.export_rules(), sort_keys=True, default=str) == rules,
        'baseline_bytes': baseline, 'peak_bytes': peak,
        'peak_delta_bytes': {k: peak[k] - baseline[k] for k in baseline}, 'after_drop_bytes': after,
        'source_hashes_before': before, 'source_hashes_after': after_hashes,
        'sources_stable': before == after_hashes,
    }

def main() -> int:
    if len(sys.argv) == 5 and sys.argv[1] == '--worker':
        print(json.dumps(worker(int(sys.argv[2]), sys.argv[3], int(sys.argv[4])), sort_keys=True, default=str)); return 0
    from domains.engine_provenance import build_is_stale, rust_source_fingerprint
    stale = build_is_stale(str(ROOT))
    if stale: raise SystemExit('stale native engine: ' + '; '.join(stale))
    env = {**os.environ, 'PYTHONPATH': f"{ROOT / 'runners/dsl/python'}:{ROOT}"}
    rows = []
    for size in (100000, 200000):
        for rep in range(3):
            order = list(BACKENDS) if rep % 2 == 0 else list(reversed(BACKENDS))
            for backend in order:
                p = subprocess.run([sys.executable, str(RUNNER), '--worker', str(size), backend, str(rep)],
                                   cwd=ROOT, env=env, text=True, capture_output=True, check=True)
                rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
    gates = {
        '12_unique_fresh_processes': len(rows) == 12 and len({r['pid'] for r in rows}) == 12,
        'stable_sources': all(r['sources_stable'] for r in rows),
        'correct_rule_and_one_offer': all(r['fault_only_guard_removed'] and r['removed_fault_rule'] and r['restored_authored_where'] and r['offer_count'] == 1 for r in rows),
        'zero_progress_fixedpoint': all(r['fixedpoint_progress'] == 0 for r in rows),
        'primary_isolated': all(r['primary_revision_unchanged'] and r['primary_counts_unchanged'] and r['primary_rules_unchanged'] for r in rows),
        'backend_outcome_parity': all(len({(r['offer_count'], r['fixedpoint_progress'], tuple(r['closure_progress']) == tuple(next(q for q in rows if q['size']==r['size'] and q['replicate']==r['replicate'] and q['backend']!=r['backend'])['closure_progress'])) for r in rows if r['size']==s}) == 1 for s in (100000,200000)),
    }
    from substrate_rs import _native
    binary = Path(_native.__file__).resolve()
    capture = {'schema':'ThoughtexperimentRecurrenceRepairMemoryV1','captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
               'host':{'platform':sys.platform},'engine_fingerprint':rust_source_fingerprint(str(ROOT)),
               'native_binary':{'path':str(binary),'sha256':sha(binary)},'source_hashes':rows[0]['source_hashes_before'],
               'protocol':{'sizes':[100000,200000],'backends':list(BACKENDS),'repeats_per_cell':3,'sampler_ms':10,'closure_sweeps':5},
               'rows':rows,'gates':gates}
    RAW.parent.mkdir(parents=True,exist_ok=True); RAW.write_text(json.dumps(capture,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'gates':gates,'raw':str(RAW),'rows':len(rows)},indent=2,sort_keys=True))
    return 0 if all(gates.values()) else 1

if __name__ == '__main__': raise SystemExit(main())
