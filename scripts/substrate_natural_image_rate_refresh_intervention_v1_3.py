#!/usr/bin/env python3
"""Measure a post-settlement oo_sunit_rate refresh as a bounded intervention."""
from __future__ import annotations
import hashlib,json,platform,resource,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts'),str(ROOT/'runners/dsl/python')]
import numpy as np
from PIL import Image
import substrate_vision_shared_substrate_multisheet_task_pilot_v1_4 as base
from scripts.rung8_lib import H,W
STEM='natural_image_rate_refresh_intervention_v1_3_20260929'
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_NATURAL_IMAGE_RATE_REFRESH_INTERVENTION_V1_3_PREREG_20260929.md'
LOCK=ROOT/f'evaluation/substrate_capability/{STEM}_lock.json';RAW=ROOT/f'evaluation/reports/{STEM}_raw.json'
ANALYZER=ROOT/'scripts/analyze_substrate_natural_image_rate_refresh_intervention_v1_2.py'
CHECKPOINT_DIRS={20260935:ROOT/'evaluation/reports/vision_multiseed_checkpoints_v2_0',20260936:ROOT/'evaluation/reports/vision_multiseed_checkpoints_v2_0',20260937:ROOT/'evaluation/reports/vision_multiseed_checkpoints_v2_0',20260938:ROOT/'evaluation/reports/vision_multiseed_checkpoints_v2_1',20260939:ROOT/'evaluation/reports/vision_multiseed_checkpoints_v2_1',20260940:ROOT/'evaluation/reports/vision_multiseed_checkpoints_v2_1'};TEST_DIR=ROOT/'data/vision_curriculum/BSDS300/images/test'
IMAGE_NAMES=('101085.jpg','130026.jpg','167062.jpg','219090.jpg','295087.jpg','376043.jpg','65033.jpg','97033.jpg')
IMAGES=tuple(TEST_DIR/n for n in IMAGE_NAMES)
SEEDS=(20260935,20260936,20260937,20260938,20260939,20260940);SCOPES=('global','root_scoped')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def node_num(x):return int(x.value if hasattr(x,'value') else x)
def source_inputs():
 from domains.engine_provenance import engine_provenance
 from substrate_rs import _native
 b=base.source_inputs();b.get('source_closure_sha256',{}).pop(f'scripts/{Path(base.__file__).name}',None);b.get('source_closure_sha256',{}).pop(f'scripts/{Path(__file__).name}',None)
 return {'protocol_sha256':sha(PROTOCOL),'runner_sha256':sha(__file__),'analyzer_sha256':sha(ANALYZER),
   'base_builder_sha256':sha(Path(base.__file__)),'base_source_inputs':b,
   'source_sha256':{p:sha(ROOT/p) for p in ('domains/wave_world.py','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/python/substrate_rs/__init__.py','seeds/vision_onoff.json')},
   'checkpoint_file_sha256':{str(s):sha(CHECKPOINT_DIRS[s]/f'seed_{s}.json') for s in SEEDS},
   'checkpoint_graph_sha256':{str(s):json.loads((CHECKPOINT_DIRS[s]/f'seed_{s}.json').read_text())['prepared_graph_sha256'] for s in SEEDS},
   'checkpoint_lock_sha256':{
     'v2_0':sha(ROOT/'evaluation/substrate_capability/vision_multiseed_checkpoint_replication_v2_0_lock_20260927.json'),
     'v2_1':sha(ROOT/'evaluation/substrate_capability/vision_multiseed_checkpoint_replication_v2_1_lock_20260929.json')},
   'image_sha256':{p.name:sha(p) for p in IMAGES},
   'prior_image_lock_sha256':sha(ROOT/'evaluation/substrate_capability/natural_image_rotation_equivariance_v1_20260929_lock.json'),'native_extension_sha256':sha(Path(_native.__file__).resolve()),
   'engine_provenance':engine_provenance(),'python':sys.version,'platform':platform.platform(),
   'seeds':list(SEEDS),'scopes':list(SCOPES),'image_names':list(IMAGE_NAMES),'frame_size':[H,W]}
def frame(path):return np.asarray(Image.open(path).convert('L').resize((W,H),Image.Resampling.BILINEAR),np.float32)/255.0
def restore(seed,scope):
 cp=json.loads((CHECKPOINT_DIRS[seed]/f'seed_{seed}.json').read_text());g=cp['graph'];expected=cp['prepared_graph_sha256']
 if base.graph_digest(g)!=expected:raise RuntimeError('checkpoint graph source mismatch')
 s,(wa,wb),(ua,ub),_,_=base.build_pair(seed,scope=='root_scoped');nat=s._inner;nat.graph_from_dict(g)
 if base.graph_digest(nat.graph_to_dict())!=expected:raise RuntimeError('restored checkpoint mismatch')
 return s,nat,wa,wb,ua,ub,expected
def state(s,units):
 keys=('act','theta','rate','act_step','rate_step','aff')
 return {k:[float(s.node(u)['attrs'].get(k,0.0)) for u in units] for k in keys}
def graph(s):return s._inner.graph_to_dict()
def intervention_diff(before,after,target_ids):
 bnodes={int(n['id']):n for n in before['nodes']};anodes={int(n['id']):n for n in after['nodes']}
 if set(bnodes)!=set(anodes):return {'node_inventory_equal':False,'edge_inventory_equal':before['edges']==after['edges'],'attr_changes':[],'only_allowed_target_attrs':False}
 changes=[]
 for nid in sorted(bnodes):
  b,a=bnodes[nid],anodes[nid]
  if b['type']!=a['type']:changes.append({'node_id':nid,'key':'<type>'})
  ba=b.get('attrs',{});aa=a.get('attrs',{})
  for key in sorted(set(ba)|set(aa)):
   if ba.get(key)!=aa.get(key):changes.append({'node_id':nid,'key':key})
 allowed=all(c['node_id'] in target_ids and c['key'] in ('rate','rate_step') for c in changes)
 return {'node_inventory_equal':True,'edge_inventory_equal':before['edges']==after['edges'] and before.get('next_id')==after.get('next_id'),
   'attr_changes':changes,'only_allowed_target_attrs':allowed}
def main():
 global LOCKED
 if sys.argv[1:]==['--lock']:
  LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps({'locked_inputs':source_inputs()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return
 LOCKED=source_inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=LOCKED:raise SystemExit('missing or stale source lock')
 if RAW.exists():raise SystemExit(f'refusing to overwrite {RAW}')
 blank=np.zeros((H,W),np.float32);records=[]
 for seed in SEEDS:
  for scope in SCOPES:
   for image_path in IMAGES:
    img=frame(image_path);rot=np.rot90(img,2).copy()
    for label,pixels in (('original',img),('rotated_180',rot),('blank',blank)):
     s,nat,wa,wb,ua,ub,cp_graph=restore(seed,scope);t0=time.perf_counter_ns();cpu0=time.process_time_ns()
     ix=[i for i,r in enumerate(nat.export_rules()) if r.get('name')=='oo_sunit_rate']
     if len(ix)!=1:raise RuntimeError('expected exactly one rate rule')
     step=int(wa.step(frame=pixels));default_state=state(s,ua);default_graph=graph(s)
     delivered=np.array([float(s.node(wa.cells[(r,c)])['attrs'].get('lum_raw',float('nan'))) for r in range(H) for c in range(W)],np.float32).reshape(H,W)
     pixels_exact=bool(np.array_equal(delivered,pixels))
     for u in ua:s.set_attr(u,'rate_step',-1.0)
     reset_graph=graph(s);act_before=[float(s.node(u)['attrs'].get('act',0.0)) for u in ua]
     rate_rule_invocations=0;termination_confirmed=False
     for _ in range(17):
      if not nat.apply_rule_batch(ix[0]):
       termination_confirmed=True;break
      rate_rule_invocations+=1
     fired=rate_rule_invocations>0;refreshed_state=state(s,ua);after_graph=graph(s)
     graph_diff=intervention_diff(reset_graph,after_graph,{node_num(u) for u in ua})
     record={'seed':seed,'scope':scope,'image_name':image_path.name,'label':label,'checkpoint_graph_sha256':cp_graph,
       'input_sha256':hashlib.sha256(pixels.tobytes()).hexdigest(),'step_return':step,
       'delivered_pixels_exact':pixels_exact,
       'root_step':float(s.node(wa.retina)['attrs'].get('step',0.0)),'default_state':default_state,
       'refreshed_state':refreshed_state,'intervention_fired':fired,'rate_rule_invocations':rate_rule_invocations,
       'termination_confirmed':termination_confirmed,'act_unchanged':act_before==refreshed_state['act'],
       'default_graph_sha256':base.graph_digest(default_graph),'reset_graph_sha256':base.graph_digest(reset_graph),
       'after_graph_sha256':base.graph_digest(after_graph),'intervention_graph_diff':graph_diff,'target_unit_ids':[node_num(u) for u in ua],
       'wall_ns':time.perf_counter_ns()-t0,
       'process_cpu_ns':time.process_time_ns()-cpu0,
       'peak_rss_bytes':int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1024 if sys.platform.startswith('linux') else 1))}
     records.append(record)
     RAW.parent.mkdir(parents=True,exist_ok=True)
     RAW.write_text(json.dumps({'run_id':STEM,'locked_inputs':LOCKED,'expected_workers':288,'workers':records,
        'source_stable':source_inputs()==LOCKED},indent=2,sort_keys=True)+'\n')
     print(f"worker={len(records)}/288 seed={seed} scope={scope} image={image_path.name} input={label} fired={fired}",flush=True)
 if source_inputs()!=LOCKED:raise SystemExit('source drift during intervention capture')
if __name__=='__main__':LOCKED={};main()
