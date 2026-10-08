#!/usr/bin/env python3
"""Cross-family live/replay check for native rule-scheduler checkpoints."""
from __future__ import annotations
import copy, hashlib, json, os, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
import substrate_rs as sr
from substrate.seed_loader import engine_rules_only
from domains.engine_provenance import assert_measuring_engine
from substrate_rs import _native
CAN_SEED=ROOT/'seeds/can_native_reimplementation.json'
RETINA_SEED=ROOT/'seeds/photon_retina_per_sensor.json'
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_SCHEDULER_CHECKPOINT_TRANSFER_V1_PREREG_20261004.md'
RUNNER=Path(__file__).resolve(); ANALYZER=ROOT/'evaluation/substrate_capability/analyze_scheduler_checkpoint_transfer_v4.py'
LOCK=ROOT/'evaluation/substrate_capability/scheduler_checkpoint_transfer_v4_lock_20261004.json'
OUT=ROOT/'evaluation/reports/scheduler_checkpoint_transfer_v4_20261004.json'
MAX_STEPS=100_000
CAN_TARGETS={'can_native_hebbian_mint','can_native_hebbian_reweight'}
RETINA_TARGET='photon_column_synthesizes_retinal_percept'
SOURCES=('runners/dsl/src/py.rs','runners/dsl/src/substrate.rs','runners/dsl/src/graph.rs','runners/dsl/src/persist.rs','runners/dsl/src/scale_audit.rs','runners/dsl/src/rewrite.rs','runners/dsl/python/substrate_rs/__init__.py','runners/dsl/python/substrate_rs/_native.build.json','runners/dsl/Cargo.lock','substrate/seed_loader.py')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inputs():
 p=assert_measuring_engine()
 names=(str(RUNNER.relative_to(ROOT)),str(ANALYZER.relative_to(ROOT)),str(PROTOCOL.relative_to(ROOT)),str(CAN_SEED.relative_to(ROOT)),str(RETINA_SEED.relative_to(ROOT)),*SOURCES)
 return {'files':{x:sha(ROOT/x) for x in names},'native_sha256':p['sha256'],'source_fingerprint':p['source_fingerprint'],'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()}
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),default=str)
def make_can():
 inner=sr.Substrate()._inner;doc=json.loads(CAN_SEED.read_text());inner.load_seed_manifest(engine_rules_only(doc))
 for idx,row in enumerate(inner.export_rules()):
  if row['name'] not in CAN_TARGETS:inner.remove_rule(idx)
 n=32;q=128;mt=inner.add_node('Microtheory',{'temperature':2.0,'discrete_mode':'3state','can_tick':1});concepts=[]
 for i in range(n):
  concepts.append(inner.add_node('Concept',{'name':f'c{i}','state':1.0,'external_field':0.0,'identity_field':0.0}));inner.add_edge(mt,'has_concept',concepts[-1],{})
 pairs=[(i,(i+off)%n) for off in range(1,n) for i in range(n)][:q]
 for j,(a,b) in enumerate(pairs):
  co=inner.add_node('Coactivation',{'noted_tick':0,'evidence_confirm':0,'evidence_disconfirm':0,'evidence_tick':0,'pair_index':j});inner.add_edge(concepts[a],'coactivated_with',co,{});inner.add_edge(co,'coactivation_of',concepts[b],{})
  if j%2:inner.add_edge(concepts[a],'causal_influence',concepts[b],{'weight':0.5})
 inner.set_incremental_match(True);return inner

def make_retina():
 inner=sr.Substrate()._inner;doc=json.loads(RETINA_SEED.read_text());rule=copy.deepcopy(next(x for x in doc['rules'] if x.get('name')==RETINA_TARGET));doc['rules']=[];inner.load_seed_manifest(engine_rules_only(doc))
 relations=('rod_receptor','l_receptor','m_receptor','s_receptor');counts=(2,2,2,2);activation={'rod_receptor':0.25,'l_receptor':0.75,'m_receptor':0.5,'s_receptor':0.125}
 for i in range(12):
  col=inner.add_node('RetinalColumn',{'fixture_id':f'column:{i}','column_index':i,'column_epoch':1})
  for et,n in zip(relations,counts):
   for j in range(n):
    rec=inner.add_node('Photoreceptor',{'fixture_id':f'{et}:{i}:{j}','rod_epoch':1,'activation':activation[et]});inner.add_edge(col,et,rec,{})
  percept=inner.add_node('RetinalPercept',{'fixture_id':f'percept:{i}','percept_index':i,'percept_epoch':0 if i==11 else 1,'intensity':0.0,'red_green':0.0,'blue_yellow':0.0,'salience':0.0});inner.add_edge(col,'has_retinal_percept',percept,{})
 inner.add_rule(rule);inner.set_predicate_retraction(True);return inner

def snapshot(inner):
 rules=inner.export_rules();rules=json.loads(rules) if isinstance(rules,str) else rules
 return {'graph':inner.graph_to_dict(),'rules':rules,'scheduler':inner.rule_scheduler_checkpoint()}
def normalize_global(c):return {str(k):int(v) for k,v in dict(c).items() if not str(k).endswith('_ns') and k!='scheduler_plan_ns'}
def audited_run(inner):
 inner.scale_audit_set_enabled(False);inner.scale_audit_set_per_rule_enabled(False);inner.scale_audit_reset();inner.scale_audit_per_rule_reset();inner.scale_audit_set_per_rule_enabled(True);inner.scale_audit_set_enabled(True)
 started=time.perf_counter_ns();steps=int(inner.run_rules(MAX_STEPS));elapsed=time.perf_counter_ns()-started
 global_counts=normalize_global(inner.scale_audit_snapshot());ids={int(a):(int(store),int(local)) for a,store,local in inner.scale_audit_rule_identity_snapshot()};per_rule={}
 for aid,metric,value in inner.scale_audit_per_rule_snapshot():
  ident=ids.get(int(aid))
  if ident is None:continue
  local=int(ident[1]);per_rule.setdefault(local,{})[str(metric)]=int(value)
 inner.scale_audit_set_per_rule_enabled(False);inner.scale_audit_set_enabled(False)
 return {'steps':steps,'elapsed_ns':elapsed,'global':global_counts,'per_rule':per_rule,'graph':inner.graph_to_dict(),'rules':inner.export_rules(),'scheduler':inner.rule_scheduler_checkpoint()}
def restore(state):
 inner=sr.Substrate()._inner;inner.graph_from_dict(state['graph']);graph_ok=inner.graph_to_dict()==state['graph'];inner.import_rules_preserving_match_order(state['rules']);inner.restore_rule_scheduler_checkpoint(state['scheduler'])
 return inner,graph_ok,inner.rule_scheduler_checkpoint()==state['scheduler']
def run_family(name,build,mutate=None):
 inner=build();before=snapshot(inner);live1=audited_run(inner)
 if mutate is not None:mutate(inner)
 between=snapshot(inner);live2=audited_run(inner);live=[live1,live2];states=[before,between];rows=[]
 for phase,(state,expected) in enumerate(zip(states,live)):
  replay,graph_rt,scheduler_rt=restore(state);rules_rt=canon(replay.export_rules())==canon(state['rules']);actual=audited_run(replay)
  rows.append({'phase':phase,'entry_rules':len(state['rules']),'entry_dirty_rule_count':sum(state['scheduler']['rule_dirty']),'entry_cursor_count':sum(len(x) for x in state['scheduler']['rule_cursors']),'entry_dirty_node_count':sum(len(x) for x in state['scheduler']['rule_dirty_nodes']),'edge_delete_versions_by_type_count':len(state['scheduler']['edge_delete_versions_by_type']),'incremental_match':state['scheduler']['flags']['incremental_match'],'graph_roundtrip':graph_rt,'rules_roundtrip':rules_rt,'scheduler_roundtrip':scheduler_rt,'live_steps':expected['steps'],'replay_steps':actual['steps'],'global_exact':expected['global']==actual['global'],'per_rule_exact':canon(expected['per_rule'])==canon(actual['per_rule']),'graph_after_exact':canon(expected['graph'])==canon(actual['graph']),'rules_after_exact':canon(expected['rules'])==canon(actual['rules']),'scheduler_after_exact':canon(expected['scheduler'])==canon(actual['scheduler']),'live_global':expected['global'],'replay_global':actual['global'],'live_per_rule':expected['per_rule'],'replay_per_rule':actual['per_rule']})
 return {'family':name,'states':rows}
def mutate_can(inner):
 graph=inner.graph_to_dict();mt=next(x for x in graph['nodes'] if x['type']=='Microtheory');concept=next(x for x in graph['nodes'] if x['type']=='Concept' and x['attrs'].get('name')=='c31')
 if not inner.remove_edge(sr.NodeID(int(mt['id'])),'has_concept',sr.NodeID(int(concept['id']))):raise RuntimeError('CAN deletion control did not remove its edge')
def mutate_retina(inner):
 graph=inner.graph_to_dict();node=next(x for x in graph['nodes'] if x['type']=='Photoreceptor');inner.set_attr(sr.NodeID(int(node['id'])),'activation',0.875)
def main():
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite prior scheduler transfer artifacts')
  LOCK.write_text(json.dumps({'schema':'SchedulerCheckpointTransferV4Lock','locked_inputs':inputs()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 assert_measuring_engine();locked=inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing or stale scheduler checkpoint transfer lock')
 results=[run_family('can_productive_coactivation_incremental_retraction',make_can,mutate_can),run_family('retinal_percept_synthesis_predicate_retraction',make_retina,mutate_retina)]
 post=inputs();out={'schema':'SchedulerCheckpointTransferV4','locked_inputs':locked,'post_run_inputs':post,'source_stable':locked==post,'families':results}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'source_stable':out['source_stable'],'families':[{'family':x['family'],'states':len(x['states']),'all_exact':all(all(row[k] for k in ('graph_roundtrip','rules_roundtrip','scheduler_roundtrip','global_exact','per_rule_exact','graph_after_exact','rules_after_exact','scheduler_after_exact')) for row in x['states'])} for x in results],'output':OUT.relative_to(ROOT).as_posix()}));return 0 if out['source_stable'] else 2
if __name__=='__main__':raise SystemExit(main())
