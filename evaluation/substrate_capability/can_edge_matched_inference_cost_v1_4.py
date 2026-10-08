#!/usr/bin/env python3
"""Higher-width exact-inference replay using the locked v1.3 worker."""
from __future__ import annotations
import hashlib,importlib.util,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
RUNNER=Path(__file__).resolve();PROTOCOL=ROOT/'docs/research/engine_substrate/CAN_EDGE_MATCHED_INFERENCE_COST_V1_4_PREREG_20261002.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_can_edge_matched_inference_cost_v1_4.py'
BASE=ROOT/'evaluation/substrate_capability/can_edge_matched_inference_cost_v1_3.py'
BASE_PROTOCOL=ROOT/'docs/research/engine_substrate/CAN_EDGE_MATCHED_INFERENCE_COST_V1_3_PREREG_20261002.md'
BASE_LOCK=ROOT/'evaluation/substrate_capability/can_edge_matched_inference_cost_v1_3_lock_20261002.json'
BASE_ANALYZER=ROOT/'evaluation/substrate_capability/analyze_can_edge_matched_inference_cost_v1_3.py'
BASE_CAPTURE=ROOT/'evaluation/reports/can_edge_matched_inference_cost_v1_3_20261002.json'
BASE_ANALYSIS=ROOT/'evaluation/reports/can_edge_matched_inference_cost_v1_3_20261002_analysis.json'
GENERATOR=ROOT/'evaluation/substrate_capability/can_edge_matched_width_topology_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/can_edge_matched_inference_cost_v1_4_lock_20261002.json'
OUT=ROOT/'evaluation/reports/can_edge_matched_inference_cost_v1_4_20261002.json'
WIDTHS=(6,7,8,9);CONTROL_WIDTH=6;FAMILIES=('grid','sparse_partial_qtree');N=120;REPLICATES=6

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def digest(path):return {'path':path.relative_to(ROOT).as_posix(),'bytes':path.stat().st_size,'sha256':sha(path)}
def load_base():
    spec=importlib.util.spec_from_file_location('edge_inference_v1_3',BASE);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m
def source_lock():
    from substrate_rs import _native
    base=load_base()
    return {'runner':digest(RUNNER),'protocol':digest(PROTOCOL),'analyzer':digest(ANALYZER),
      'base_runner':digest(BASE),'base_protocol':digest(BASE_PROTOCOL),'base_lock':digest(BASE_LOCK),
      'base_analyzer':digest(BASE_ANALYZER),'base_capture':digest(BASE_CAPTURE),'base_analysis':digest(BASE_ANALYSIS),
      'generator':digest(GENERATOR),'base_input_lock':base.input_lock(),
      'loaded_native_binary':digest(Path(_native.__file__).resolve()),
      'widths':list(WIDTHS),'control_width':CONTROL_WIDTH,'families':list(FAMILIES),'nodes':N,'replicates':REPLICATES}
def historical_python_compatibility():
    """Check v1.3 code/data inputs except its replaced native artifact pair."""
    current=load_base().input_lock();historical=json.loads(BASE_LOCK.read_text())
    def without_engine(lock):
        out=dict(lock);out['sources']=[x for x in lock['sources'] if x['path'] not in (
          'runners/dsl/python/substrate_rs/_native.abi3.so','runners/dsl/python/substrate_rs/_native.build.json')]
        return out
    return without_engine(current)==without_engine(historical)
def worker(q,family,rep):
    return load_base().worker(q,family,rep)
def main():
    args=sys.argv[1:]
    if args[:1]==['--worker']:
        print(json.dumps(worker(int(args[1]),args[2],int(args[3])),sort_keys=True,separators=(',',':')));return 0
    if args==['--lock']:
        if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite lock/capture')
        LOCK.write_text(json.dumps({'schema':'CanEdgeMatchedInferenceCostV1_4Lock','sources':source_lock()},indent=2,sort_keys=True)+'\n')
        print(LOCK.relative_to(ROOT));return 0
    if args!=['--run']:raise SystemExit('usage: --lock, --run, or --worker Q FAMILY REP')
    lock=json.loads(LOCK.read_text())
    if source_lock()!=lock['sources']:raise SystemExit('source/input drift from lock')
    if not historical_python_compatibility():raise SystemExit('v1.3 Python/generator sources differ from historical lock')
    from domains.engine_provenance import build_is_stale
    stale=build_is_stale(str(ROOT))
    if stale:raise SystemExit('native engine stale: '+'; '.join(stale))
    env={**os.environ,'PYTHONPATH':f"{ROOT/'runners/dsl/python'}:{ROOT}:{os.environ.get('PYTHONPATH','')}"}
    rows=[]
    for q in WIDTHS:
      for rep in range(REPLICATES):
       for family in FAMILIES:
        p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(q),family,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=300)
        if p.returncode:raise RuntimeError(f'q={q} family={family} rep={rep}: {p.stderr[-3000:]}')
        row=json.loads(p.stdout.strip());rows.append(row)
        print(f"q={q} family={family} rep={rep} minfill={row['minfill_width']} JTmf={row['timing_ns']['jt_minfill_wall']/1e6:.2f}ms JTcert={row['timing_ns']['jt_certificate_wall']/1e6:.2f}ms",flush=True)
    post=source_lock()
    checks={'complete_workers':len(rows)==len(WIDTHS)*len(FAMILIES)*REPLICATES,
      'full_cell_coverage':all(sum(r['width']==q and r['family']==f for r in rows)==REPLICATES for q in WIDTHS for f in FAMILIES),
      'edge_sizes_match':all(r['nodes']==N and r['edges']==r['expected_edges'] for r in rows),
      'exact_extraction':all(r['extraction_exact'] for r in rows),
      'certificate_width_q':all(r['certificate_width']==r['width'] for r in rows),
      'profile_reconciliation':all(r['decomposition_profiles']['minfill']['max_bag_size']==r['minfill_bag_size'] and r['decomposition_profiles']['certificate']['max_bag_size']==r['certificate_bag_size'] for r in rows),
      'minfill_oracle_parity':all(abs(r['minfill_energy']-r['oracle_energy'])<1e-8 and abs(r['minfill_direct_energy']-r['oracle_energy'])<1e-8 for r in rows),
      'certificate_oracle_parity':all(abs(r['certificate_energy']-r['oracle_energy'])<1e-8 and abs(r['certificate_direct_energy']-r['oracle_energy'])<1e-8 for r in rows),
      'no_mutation':all(r['no_mutation'] for r in rows),'pre_post_source_match':post==lock['sources']}
    OUT.write_text(json.dumps({'schema':'CanEdgeMatchedInferenceCostV1_4Results','lock_sha256':sha(LOCK),
      'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),
      'sources':source_lock(),'post_run_sources':post,'configuration':{'widths':WIDTHS,'control_width':CONTROL_WIDTH,'nodes':N,'replicates':REPLICATES,'families':FAMILIES},
      'claim_boundary':'exact MAP cost on a contemporaneous q=6 baseline and certified widths 7-9 across two synthetic binary pairwise families; no natural topology estimate',
      'checks':checks,'runs':rows},indent=2,sort_keys=True)+'\n')
    print(json.dumps({'capture':OUT.relative_to(ROOT).as_posix(),'checks':checks},indent=2))
    if not all(checks.values()):raise SystemExit('higher-width exact-inference gate failed')
if __name__=='__main__':main()
