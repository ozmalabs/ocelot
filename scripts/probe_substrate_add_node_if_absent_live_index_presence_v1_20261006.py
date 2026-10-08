#!/usr/bin/env python3
"""Source-locked check for Concept.name index presence after live-route boot."""
from __future__ import annotations
import hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'scripts')]
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_ADD_NODE_IF_ABSENT_LIVE_INDEX_PRESENCE_V1_PREREG_20261006.md'
RUNNER=Path(__file__).resolve();PANEL_LOCK=ROOT/'evaluation/substrate_capability/add_node_if_absent_indexed_lookup_v1_20261006_lock.json'
LOCK=ROOT/'evaluation/substrate_capability/add_node_if_absent_live_index_presence_v1_20261006_lock.json'
OUT=ROOT/'evaluation/reports/add_node_if_absent_indexed_lookup_v1_20261006/live_index_presence_probe.json'
HARVEST=ROOT/'evaluation/substrate_capability/live_conversation_task_graph_harvest_v2.py'
def sha(p):return 'sha256:'+hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def inputs():
 from substrate_rs import _native
 h=load(HARVEST,'live_index_presence_harvest');return {'protocol_sha256':sha(PROTOCOL),'runner_sha256':sha(RUNNER),
  'panel_lock_sha256':sha(PANEL_LOCK),'harvest_runner_sha256':sha(HARVEST),'harvest_inputs':h.inputs(),
  'native_extension_sha256':sha(Path(_native.__file__).resolve()),'native_build_record_sha256':sha(Path(_native.__file__).resolve().with_name('_native.build.json'))}
def main():
 from domains.engine_provenance import assert_measuring_engine
 assert_measuring_engine()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=inputs():raise SystemExit('missing/stale index-presence source lock')
 locked=inputs();panel=json.loads(PANEL_LOCK.read_text())['locked_inputs'];h=load(HARVEST,'live_index_presence_worker')
 if locked['harvest_inputs']!=panel['harvest_inputs']:raise SystemExit('harvest input differs from indexed lookup panel')
 from substrate.world_adapter import WorldAdapter
 from substrate.boot_all import load_all_seeds
 agent=WorldAdapter(seeds=());initial=bool(agent.inner.has_attr_index('Concept','name'))
 try:agent.set_self_teacher(lambda q:(None,'teacher')[1])
 except Exception:pass
 boot=load_all_seeds(agent);after=bool(agent.inner.has_attr_index('Concept','name'))
 sample=None;matches=[]
 for node in agent.s.nodes('Concept'):
  value=agent.s.node(node)['attrs'].get('name')
  if isinstance(value,str):sample={'node_id':int(node.value if hasattr(node,'value') else node),'name':value};matches=agent.inner.nodes_where('Concept','name',value);break
 post=inputs();payload={'schema':'AddNodeIfAbsentLiveIndexPresenceV1','locked_inputs':locked,'post_run_inputs':post,
  'harvest_fingerprint_matches_panel':locked['harvest_inputs']==panel['harvest_inputs'],'source_stable':locked==post,
  'index_present_after_adapter_init':initial,'index_present_after_full_seed_load':after,'loaded_seed_count':boot.get('loaded'),
  'concept_count':len(agent.s.nodes('Concept')),'sample_indexed_name':sample,'sample_lookup_contains_node':bool(sample and any((int(x.value if hasattr(x,'value') else x)==sample['node_id']) for x in matches))}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n');print(json.dumps({k:payload[k] for k in ('harvest_fingerprint_matches_panel','source_stable','index_present_after_adapter_init','index_present_after_full_seed_load','loaded_seed_count','concept_count','sample_lookup_contains_node')},indent=2))
 if not payload['harvest_fingerprint_matches_panel'] or not payload['source_stable']:raise SystemExit('probe provenance failed')
if __name__=='__main__':
 import sys
 if sys.argv[1:]==['--lock']:
  LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps({'schema':'AddNodeIfAbsentLiveIndexPresenceV1Lock','locked_inputs':inputs()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT))
 else:main()
