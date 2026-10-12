#!/usr/bin/env python3
"""Production-path structural transfer probe for nonlinear shape transforms.

Run with PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_nonlinear_dimension_induction_v1_5.py --lock
then rerun without --lock to execute against the frozen lock.
"""
from __future__ import annotations
import argparse, hashlib, itertools, json, platform, subprocess, sys, time
from pathlib import Path

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()
from substrate.boot_core import boot_core
from domains import reflective_faculty as rf
from substrate_rs import _native

ROOT=Path(__file__).resolve().parents[1]
LOCK=ROOT/'evaluation/substrate_capability/nonlinear_dimension_induction_v1_5_lock_20261005.json'
OUT=ROOT/'evaluation/reports/substrate_nonlinear_dimension_induction_v1_5_20261005.json'
DT=['pred','id','coord:r','coord:c','val']
FAMILIES={
 'linear':lambda x,y:(x+y,2*y),
 'coupled_quadratic':lambda x,y:(x+x*y,y+x*x),
}
TRAIN=[(0,0),(1,0),(0,1),(1,1),(0,2),(1,2)]
TRANSFER=[(0,0),(2,0),(0,2),(2,2),(1,3),(3,3)]
REPS=10
SEED=20261005
SOURCES=['scripts/substrate_nonlinear_dimension_induction_v1_5.py','scripts/analyze_substrate_nonlinear_dimension_induction_v1_5.py','docs/research/engine_substrate/SUBSTRATE_NONLINEAR_DIMENSION_INDUCTION_V1_5_PREREG_20261005.md','seeds/shape_decode_loop.json','domains/reflective_faculty.py','domains/engine_provenance.py','substrate/boot_core.py','runners/dsl/src/scale_audit.rs','runners/dsl/src/shape_decode.rs','runners/dsl/src/term.rs','runners/dsl/src/py.rs','runners/dsl/python/substrate_rs/_native.build.json']

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def signature(points,family,shape):
    rows=[]
    for i,(x,y) in enumerate(points):
        u,v=FAMILIES[family](x,y)
        rows.append(['cell',f'{shape}:{i}',u,v,'red'])
    return rows
def base_signature(points,shape): return [['cell',f'{shape}:{i}',x,y,'red'] for i,(x,y) in enumerate(points)]
def matrices_match(base,target,bound):
    # Independent exhaustive check for exact identity-aligned 2x2 integer maps.
    tgt={r[1]:(r[2],r[3]) for r in target}
    bmap={r[1]:(r[2],r[3]) for r in base}
    for m in itertools.product(range(-bound,bound+1),repeat=4):
        if m==(1,0,0,1): continue
        mins=(min(x for x,y in bmap.values()),min(y for x,y in bmap.values()))
        ok=True
        for ident,(x,y) in bmap.items():
            px=m[0]*(x-mins[0])+m[1]*(y-mins[1]); py=m[2]*(x-mins[0])+m[3]*(y-mins[1])
            if tgt.get(ident)!=(px,py): ok=False; break
        if ok:return list(m)
    return None
def lock_body():
    cases=[]
    for fam in FAMILIES:
      for rep in range(REPS):
        train=base_signature(TRAIN,f'train{rep}')
        trans=signature(TRAIN,fam,f'train{rep}')
        hold=base_signature(TRANSFER,f'transfer{rep}')
        hold_target=signature(TRANSFER,fam,f'transfer{rep}')
        bound=max(max(abs(r[2]),abs(r[3])) for r in train+trans)
        cases.append({'family':fam,'replicate':rep,'training_base':train,'training_target':trans,'transfer_base':hold,'transfer_target':hold_target,'matrix_bound':bound,'any_exact_linear_fit':matrices_match(train,trans,bound) is not None})
    return {'schema_version':1,'protocol':'SUBSTRATE_NONLINEAR_DIMENSION_INDUCTION_V1_3_PREREG_20261005','seed':SEED,'families':list(FAMILIES),'repetitions':REPS,'arms':['production_induction','frozen_no_induction'],'train_relations':len(TRAIN),'transfer_relations':len(TRANSFER),'dim_types':DT,'cases':cases}
def lock_payload():
    native_path=Path(_native.__file__).resolve()
    body=lock_body()
    return {'protocol_sha256':sha(ROOT/'docs/research/engine_substrate/SUBSTRATE_NONLINEAR_DIMENSION_INDUCTION_V1_3_PREREG_20261005.md'),
            'runner_sha256':sha(ROOT/SOURCES[0]),'analyzer_sha256':sha(ROOT/SOURCES[1]),
            'source_sha256':{p:sha(ROOT/p) for p in SOURCES[2:]},
            'native_extension':{'path':str(native_path),'sha256':sha(native_path)},'inputs':body}
def write_or_check_lock():
    payload=lock_payload()
    if '--lock' in sys.argv:
        LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n');print(f'locked {LOCK}');return None
    if not LOCK.exists(): raise SystemExit('missing pre-run lock; invoke once with --lock, then do not change sources or inputs')
    old=json.loads(LOCK.read_text())
    if old!=payload: raise SystemExit('lock/source/input mismatch; preserve lock and create a versioned amendment')
    return payload
def observe(s,ag,sig,key):
    epoch=s.node(ag)['attrs'].get('codebook_epoch') or 0.0
    obs=s.add_node('Observation',{'signature':sig,'key':['nonlinear_induction',*key],'status':'decoded','residual':sig,'decoded_epoch':epoch,'dim_types':DT})
    s.add_edge(ag,'observed',obs);return obs
def generators(s):
    out=[]
    for n in s.nodes('DimensionGenerator'):
        a=s.node(n)['attrs'];out.append({'name':a.get('name'),'kind':a.get('kind'),'matrix':a.get('matrix'),'coord_dims':a.get('coord_dims')})
    return out
def run_case(case,enabled):
    s,ag=boot_core();native=rf._native_eval2(s);rf._ensure_shape_decode_loop(s,native,ag)
    if enabled:s.set_attr(ag,'gen_infer_enabled',1.0)
    s.add_node('ShapeSignature',{'name':'training_base','signature':json.dumps(case['training_base']),'kind':'faculty','faculty':'training_base','dim_types':DT})
    s.add_node('ShapeSignature',{'name':'transfer_base','signature':json.dumps(case['transfer_base']),'kind':'faculty','faculty':'transfer_base','dim_types':DT})
    start_axis=len(list(s.nodes('CapabilityAxis')));initial_generators=generators(s);events=[]
    for stage,sig in [('train',case['training_target']),('transfer',case['transfer_target'])]:
        obs=observe(s,ag,sig,[case['family'],str(case['replicate']),stage,str(enabled)])
        before=len(list(s.nodes('CapabilityAxis')));_native.Substrate.scale_audit_reset();_native.Substrate.scale_audit_set_enabled(True)
        try:
            t0=time.perf_counter();native.run_rules();elapsed=time.perf_counter()-t0
        finally:
            _native.Substrate.scale_audit_set_enabled(False)
        audit=dict(_native.Substrate.scale_audit_snapshot())
        infer_counters={k:v for k,v in audit.items() if k.startswith('gen_infer_')}
        infer_counters['gen_infer_bases_by_bound']={k.split(':',1)[1]:v for k,v in audit.items() if k.startswith('gen_infer_bases_by_bound:')}
        a=s.node(obs)['attrs'];events.append({'stage':stage,'status':a.get('status'),'residual':a.get('residual'),'quanta_added':len(list(s.nodes('CapabilityAxis')))-before,'generators':generators(s),'closure_seconds':elapsed,'graph_nodes':len(list(s.nodes())),'gen_infer_counters':infer_counters})
    return {'family':case['family'],'replicate':case['replicate'],'enabled':enabled,'events':events,'total_quanta':len(list(s.nodes('CapabilityAxis')))-start_axis,'initial_generators':initial_generators,'final_generators':generators(s)}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--lock',action='store_true');args=ap.parse_args()
    if args.lock:
        payload=write_or_check_lock();return 0
    lock=write_or_check_lock();samples=[];started=time.perf_counter()
    # deterministic family/replicate interleave from the published seed.
    import random
    schedule=[(c,e) for c in lock['inputs']['cases'] for e in (False,True)]
    random.Random(SEED).shuffle(schedule)
    for case,enabled in schedule:samples.append(run_case(case,enabled))
    native_path=Path(_native.__file__).resolve()
    post_payload=lock_payload()
    out={'schema_version':1,'run_id':'substrate-nonlinear-dimension-induction-v1-3-20261005','engine':provenance_line(),'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'environment':{'python':sys.version,'platform':platform.platform()},'lock_sha256':sha(LOCK),'pre_lock_payload':lock,'post_lock_payload':post_payload,'source_native_stable':post_payload==lock,'schedule_seed':SEED,'schedule':[[c['family'],c['replicate'],e] for c,e in schedule],'samples':samples,'runtime_seconds':time.perf_counter()-started,'provenance':{'native_extension_path':str(native_path),'native_extension_sha256':sha(native_path)}}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT),'samples':len(samples),'runtime_seconds':out['runtime_seconds']},indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
