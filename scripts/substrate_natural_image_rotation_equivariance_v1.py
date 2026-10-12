#!/usr/bin/env python3
"""Locked natural-image spatial-equivariance pilot on production WaveWorld."""
from __future__ import annotations
import hashlib,json,platform,resource,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts'),str(ROOT/'runners/dsl/python')]
import numpy as np
from PIL import Image
import substrate_vision_shared_substrate_multisheet_task_pilot_v1_4 as base
from scripts.rung8_lib import H,W

STEM='natural_image_rotation_equivariance_v1_20260929'
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_NATURAL_IMAGE_ROTATION_EQUIVARIANCE_V1_PREREG_20260929.md'
LOCK=ROOT/f'evaluation/substrate_capability/{STEM}_lock.json'
RAW=ROOT/f'evaluation/reports/{STEM}_raw.json'
ANALYZER=ROOT/'scripts/analyze_substrate_natural_image_rotation_equivariance_v1.py'
CHECKPOINT_DIR=ROOT/'evaluation/reports/vision_multiseed_checkpoints_v2_0'
SEEDS=(20260935,20260936,20260937);SCOPES=('global','root_scoped')
TEST_DIR=ROOT/'data/vision_curriculum/BSDS300/images/test'
ALL_IMAGES=sorted(TEST_DIR.glob('*.jpg'))
IMAGE_PATHS=tuple(ALL_IMAGES[round(i*(len(ALL_IMAGES)-1)/7)] for i in range(8))

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def peak_rss():
    n=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(n*(1024 if sys.platform.startswith('linux') else 1))
def source_inputs():
    from domains.engine_provenance import engine_provenance
    from substrate_rs import _native
    builder=base.source_inputs()
    builder.get('source_closure_sha256',{}).pop(f'scripts/{Path(base.__file__).name}',None)
    builder.get('source_closure_sha256',{}).pop(f'scripts/{Path(__file__).name}',None)
    files=('domains/wave_world.py','domains/lateral_world.py','domains/onoff_world.py',
           'domains/settle_world.py','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs',
           'runners/dsl/python/substrate_rs/__init__.py')
    return {'protocol_sha256':sha(PROTOCOL),'runner_sha256':sha(__file__),'analyzer_sha256':sha(ANALYZER),
        'base_source_inputs':builder,'source_sha256':{f:sha(ROOT/f) for f in files},
        'checkpoint_sha256':{str(s):sha(CHECKPOINT_DIR/f'seed_{s}.json') for s in SEEDS},
        'checkpoint_lock_sha256':sha(ROOT/'evaluation/substrate_capability/vision_multiseed_checkpoint_replication_v2_0_lock_20260927.json'),
        'image_sha256':{p.name:sha(p) for p in IMAGE_PATHS},'image_names':[p.name for p in IMAGE_PATHS],
        'native_extension_sha256':sha(Path(_native.__file__).resolve()),'engine_provenance':engine_provenance(),
        'python':sys.version,'platform':platform.platform(),'seeds':list(SEEDS),'scopes':list(SCOPES),
        'frame_size':[H,W],'resampler':'Pillow Image.Resampling.BILINEAR','arms':['original','rotated_180','blank']}

def load_frame(path):
    im=Image.open(path).convert('L').resize((W,H),Image.Resampling.BILINEAR)
    return np.asarray(im,dtype=np.float32)/255.0
def restore(seed,scope):
    cp=json.loads((CHECKPOINT_DIR/f'seed_{seed}.json').read_text());expected=cp['prepared_graph_sha256']
    if base.graph_digest(cp['graph'])!=expected:raise RuntimeError('checkpoint source digest mismatch')
    s,(wa,wb),(ua,ub),_,_=base.build_pair(seed,scope=='root_scoped');inner=s._inner
    rules=[r for r in inner.export_rules() if r.get('name') in ('st_settle','st_settle_root_scoped_benchmark')]
    wanted='st_settle_root_scoped_benchmark' if scope=='root_scoped' else 'st_settle'
    if len(rules)!=1 or rules[0].get('name')!=wanted:raise RuntimeError('wrong settlement scope')
    inner.graph_from_dict(cp['graph'])
    if base.graph_digest(inner.graph_to_dict())!=expected:raise RuntimeError('restored checkpoint mismatch')
    return s,inner,wa,wb,ua,ub,expected
def trial(seed,scope,image,label):
    s,inner,wa,wb,ua,ub,cp_hash=restore(seed,scope)
    t0=time.perf_counter_ns();c0=time.process_time_ns()
    step=int(wa.step(frame=image))
    delivered=np.array([float(s.node(wa.cells[(r,c)])['attrs'].get('lum_raw',float('nan')))
                        for r in range(H) for c in range(W)],dtype=np.float32).reshape(H,W)
    if not np.array_equal(delivered,image):raise RuntimeError('adapter pixel delivery mismatch')
    graph=inner.graph_to_dict()
    return {'label':label,'checkpoint_sha256':cp_hash,'input_sha256':hashlib.sha256(image.tobytes()).hexdigest(),
        'step_return':step,'root_step':float(s.node(wa.retina)['attrs'].get('step',0.0)),
        'act':[float(s.node(u)['attrs'].get('act',0.0)) for u in ua],
        'rate':[float(s.node(u)['attrs'].get('rate',0.0)) for u in ua],
        'delivered_pixels_exact':True,'final_graph_sha256':base.graph_digest(graph),
        'graph_node_count':len(graph.get('nodes',[])),'graph_edge_count':len(graph.get('edges',[])),
        'wall_ns':time.perf_counter_ns()-t0,'process_cpu_ns':time.process_time_ns()-c0,'peak_rss_bytes':peak_rss()}
def main():
    global LOCKED
    if sys.argv[1:]==['--lock']:
        LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps({'locked_inputs':source_inputs()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return
    LOCKED=source_inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=LOCKED:raise SystemExit('missing or stale source lock')
    if RAW.exists():raise SystemExit(f'refusing to overwrite {RAW}')
    records=[];blank=np.zeros((H,W),np.float32)
    for seed in SEEDS:
      for scope in SCOPES:
       for path in IMAGE_PATHS:
        frame=load_frame(path);rot=np.rot90(frame,2).copy()
        row={'seed':seed,'scope':scope,'image':path.name,'image_sha256':sha(path),
             'arms':[trial(seed,scope,frame,'original'),trial(seed,scope,rot,'rotated_180'),trial(seed,scope,blank,'blank')]}
        records.append(row)
        RAW.parent.mkdir(parents=True,exist_ok=True)
        RAW.write_text(json.dumps({'run_id':STEM,'locked_inputs':LOCKED,'expected_workers':48,
            'workers':records,'source_stable':source_inputs()==LOCKED},indent=2,sort_keys=True)+'\n')
        print(f"worker={len(records)}/48 seed={seed} scope={scope} image={path.name}",flush=True)
    if source_inputs()!=LOCKED:raise SystemExit('source drift during capture')
if __name__=='__main__':
    LOCKED={};main()
