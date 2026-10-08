#!/usr/bin/env python3
"""Sample per-thread Linux schedstat CPU during the locked warm converse."""
from __future__ import annotations
import hashlib, importlib.util, json, os, platform, subprocess, sys, tempfile, threading, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = Path(__file__).resolve()
PROTOCOL = ROOT / 'docs/research/engine_substrate/SUBSTRATE_ADEQUACY_WARM_CONVERSE_THREAD_CPU_V1_PREREG_20261002.md'
ANALYZER = ROOT / 'evaluation/substrate_capability/analyze_substrate_adequacy_warm_converse_thread_cpu_v1.py'
LOCK = ROOT / 'evaluation/substrate_capability/substrate_adequacy_warm_converse_thread_cpu_v1_lock_20261002.json'
RAW = ROOT / 'evaluation/reports/substrate_adequacy_warm_converse_thread_cpu_v1_raw_20261002.json'
CALLER = ROOT / 'evaluation/substrate_capability/substrate_adequacy_warm_converse_caller_cpu_v1.py'
CALLER_LOCK = ROOT / 'evaluation/substrate_capability/substrate_adequacy_warm_converse_caller_cpu_v1_lock_20261002.json'
SCHEDULE = [('default', 1), ('one_thread', 2), ('one_thread', 3), ('default', 4), ('default', 5), ('one_thread', 6)]
SAMPLE_NS = 2_000_000

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
def frozen():
    caller = load(CALLER, 'thread_cpu_caller')
    return {'runner': sha(RUNNER), 'protocol': sha(PROTOCOL), 'analyzer': sha(ANALYZER),
            'caller_runner': sha(CALLER), 'caller_lock_file': sha(CALLER_LOCK),
            'caller_runtime_lock': caller.load_base().frozen()}
def read_threads():
    rows = {}
    try: tids = list(Path('/proc/self/task').iterdir())
    except OSError: return rows
    for entry in tids:
        try:
            tid = int(entry.name)
            stat = (entry / 'stat').read_text(); close = stat.rfind(')')
            # schedstat exposes per-thread runtime in ns; stat starttime disambiguates TID reuse.
            fields = stat[close + 2:].split()
            starttime = int(fields[19])
            sched = (entry / 'schedstat').read_text().split()
            comm = (entry / 'comm').read_text().strip()
            rows[(tid, starttime)] = {'runtime_ns': int(sched[0]), 'comm': comm, 'state': fields[0]}
        except (OSError, ValueError, IndexError):
            continue
    return rows
def worker(mode, rep, expected):
    from substrate import world_adapter as wa
    Original = wa.WorldAdapter
    sampled = []; stop = threading.Event(); target = {'begin_ns': None, 'end_ns': None}
    def sample_loop():
        while not stop.is_set():
            sampled.append((time.monotonic_ns(), read_threads()))
            stop.wait(SAMPLE_NS / 1e9)
    class ThreadCpuAdapter(Original):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs); self._thread_cpu_call = 0
        def converse(self, *args, **kwargs):
            call = self._thread_cpu_call
            if call == 1:
                target['begin_ns'] = time.monotonic_ns()
                sampler = threading.Thread(target=sample_loop, name='thread-cpu-probe', daemon=True)
                sampler.start()
                try: return super().converse(*args, **kwargs)
                finally:
                    target['end_ns'] = time.monotonic_ns(); stop.set(); sampler.join()
                    sampled.append((target['end_ns'], read_threads()))
            self._thread_cpu_call += 1
            return super().converse(*args, **kwargs)
    wa.WorldAdapter = ThreadCpuAdapter
    caller = load(CALLER, 'warm_converse_caller_cpu_for_thread_probe')
    row = caller.worker(mode, rep, expected)
    # Integrate max observed schedstat delta by (TID,starttime); first/last sample
    # bounds are conservative because short-lived threads may run between polls.
    ranges = {}; names = {}
    for _, snap in sampled:
        for key, value in snap.items():
            agg = ranges.setdefault(key, [value['runtime_ns'], value['runtime_ns']])
            agg[0] = min(agg[0], value['runtime_ns']); agg[1] = max(agg[1], value['runtime_ns'])
            names[key] = {'comm': value['comm'], 'state': value['state']}
    per_thread = [{'tid': key[0], 'starttime_ticks': key[1], 'comm': names[key]['comm'],
                   'sampled_runtime_delta_ns': max(0, bounds[1] - bounds[0])}
                  for key, bounds in ranges.items()]
    per_thread.sort(key=lambda r: r['sampled_runtime_delta_ns'], reverse=True)
    return {'caller_worker': row, 'thread_cpu': {'sample_count': len(sampled),
            'sample_interval_ms': SAMPLE_NS / 1e6, 'target_interval_ns': target,
            'unique_thread_instances': len(per_thread), 'sampled_thread_runtime_sum_ns': sum(x['sampled_runtime_delta_ns'] for x in per_thread),
            'threads': per_thread}}
def run_child(mode, rep, expected):
    env = os.environ.copy(); env.update(OZMA_NO_LLM='1', OZMA_SEED_PERSIST_DISABLED='1',
        PYTHONPATH=f"{ROOT}:{ROOT/'runners/dsl/python'}:{ROOT/'evaluation/substrate_capability'}")
    if mode == 'one_thread': env['RAYON_NUM_THREADS'] = '1'
    else: env.pop('RAYON_NUM_THREADS', None)
    with tempfile.TemporaryFile(mode='w+t') as out, tempfile.TemporaryFile(mode='w+t') as err:
        proc = subprocess.Popen([sys.executable, str(RUNNER), '--worker', mode, str(rep)], cwd=ROOT, env=env, text=True, stdout=out, stderr=err)
        proc.wait(); out.seek(0); stdout = out.read(); err.seek(0); stderr = err.read()
    if proc.returncode: raise RuntimeError(f'{mode}/{rep}: {stderr[-2000:]}')
    row = json.loads(stdout.splitlines()[-1]); row['mode'] = mode; row['rep'] = rep
    return row
def main():
    if sys.argv[1:2] == ['--worker']:
        lock = json.loads(LOCK.read_text()); print(json.dumps(worker(sys.argv[2], int(sys.argv[3]), lock['sources']['caller_runtime_lock']), sort_keys=True)); return
    if sys.argv[1:] == ['--lock']:
        if LOCK.exists() or RAW.exists(): raise SystemExit('refusing to overwrite lock or raw capture')
        LOCK.write_text(json.dumps({'schema': 'WarmConverseThreadCpuV1Lock', 'sources': frozen(), 'schedule': SCHEDULE,
                                    'sample_interval_ms': SAMPLE_NS / 1e6}, indent=2, sort_keys=True) + '\n')
        print(LOCK.relative_to(ROOT)); return
    lock = json.loads(LOCK.read_text())
    if lock['sources'] != frozen(): raise SystemExit('source lock drift')
    if RAW.exists(): raise SystemExit('capture exists; refusing overwrite')
    before = frozen(); rows = []
    for mode, rep in SCHEDULE:
        row = run_child(mode, rep, lock['sources']); rows.append(row)
        t = row['thread_cpu']; cpu = row['caller_worker']['worker']['timing_ns']['target_cpu']
        print(json.dumps({'mode': mode, 'rep': rep, 'samples': t['sample_count'], 'threads': t['unique_thread_instances'],
                          'sampled_thread_cpu_ms': t['sampled_thread_runtime_sum_ns']/1e6,
                          'process_cpu_ms': cpu/1e6}), flush=True)
    after = frozen()
    capture = {'schema': 'WarmConverseThreadCpuV1Capture', 'lock': lock, 'source_before': before,
               'source_after': after, 'source_stable': before == after, 'host': platform.platform(),
               'logical_cpus': os.cpu_count(), 'rows': rows}
    RAW.write_text(json.dumps(capture, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'workers': len(rows), 'source_stable': capture['source_stable'], 'raw': str(RAW.relative_to(ROOT))}))
if __name__ == '__main__': main()
