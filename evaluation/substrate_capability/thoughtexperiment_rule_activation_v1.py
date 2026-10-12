#!/usr/bin/env python3
"""Source-locked activation of validated edit-op candidates."""
from __future__ import annotations
import hashlib, importlib.util, json, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'evaluation/substrate_capability')]
RUNNER=Path(__file__).resolve()
PRE=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_RULE_ACTIVATION_V1_PREREG_20261003.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_rule_activation_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_rule_activation_v1_lock_20261003.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_rule_activation_v1_20261003.json'
BASE=ROOT/'evaluation/substrate_capability/thoughtexperiment_editops_cross_family_cow_v1.py'
SOURCES=[
 'runners/dsl/src/py.rs','runners/dsl/src/substrate.rs',
 'runners/dsl/python/substrate_rs/__init__.py','domains/edit_ops.py',
 'domains/contract_query.py','domains/engine_provenance.py',
 'evaluation/substrate_capability/thoughtexperiment_editops_cross_family_cow_v1.py',
 'evaluation/substrate_capability/analyze_thoughtexperiment_editops_cross_family_cow_v1.py',
 'evaluation/substrate_capability/thoughtexperiment_bidirectional_edge_identity_guards_v1_1.py',
 'evaluation/substrate_capability/thoughtexperiment_editops_edge_hypotheses_v1.py',
 'evaluation/substrate_capability/thoughtexperiment_editops_cross_family_cow_v1_lock_20261003.json',
 'evaluation/reports/thoughtexperiment_editops_cross_family_cow_v1_orders_20261003.json',
 'evaluation/reports/thoughtexperiment_editops_cross_family_cow_v1_scores_20261003.json']
FAMILIES=('recurrence','conversation');WORKERS=4
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;assert spec.loader;spec.loader.exec_module(m);return m
def frozen():
 from substrate_rs import _native
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 if build_is_stale(str(ROOT)): raise RuntimeError('native engine is stale')
 paths=[ROOT/p for p in SOURCES]+[RUNNER,PRE,ANALYZER]
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in paths},
  'native':{'path':str(Path(_native.__file__).resolve()),'sha256':sha(Path(_native.__file__).resolve())},
  'rust_fingerprint':rust_source_fingerprint(str(ROOT))}
def run(lock):
 from thoughtexperiment_editops_cross_family_cow_v1 import modules,make_pool,make_ctx,execute_recurrence,execute_conversation
 b,_=modules();rows=[]
 for family in FAMILIES:
  for worker in range(WORKERS):
   _,candidates,descriptors,*_=make_pool(family,worker)
   for candidate,descriptor in zip(candidates,descriptors):
    candidate['proposal_id']=descriptor['proposal_id']
   needle='candidate:has_mint_offer' if family=='recurrence' else 'in:m:responds_to'
   candidate=next(c for c in candidates if needle in c['label'])
   ctx=make_ctx(b,family,worker,f'train_{worker}',True);sub=ctx['sub'];native=ctx['native'];target=ctx['target']
   before_rules=digest(native.export_rules());revision=tuple(sub.experiment_graph_rule_revision())
   t=time.perf_counter_ns();installed=sub.replace_active_rule_by_name_if_revision(revision,target,candidate['rules'][target]);activation_ns=time.perf_counter_ns()-t
   if not installed: raise RuntimeError(f'{family}/{worker}: target rule absent')
   t=time.perf_counter_ns()
   outcome=execute_recurrence(ctx,sub) if family=='recurrence' else execute_conversation(ctx,sub,f'train_{worker}')
   execution_ns=time.perf_counter_ns()-t
   rules_after=native.export_rules();active_names=[r['name'] for r in rules_after if r.get('active',True)]
   rows.append({'family':family,'worker':worker,'candidate_id':candidate['proposal_id'],'label':candidate['label'],
    'outcome':outcome,'activation_ns':activation_ns,'execution_ns':execution_ns,
    'rule_store_changed':before_rules!=digest(rules_after),'successor_active':candidate['rules'][target]['name'] in active_names,
    'target_active':target in active_names})
   # Stale revision and malformed rule controls use independent substrates.
   bad=make_ctx(b,family,worker,f'control_{worker}',True);s=bad['sub'];n=bad['native'];name=bad['target']
   stale=tuple(s.experiment_graph_rule_revision());rules0=digest(n.export_rules());s.add_node('ActivationRevisionProbe',{})
   try: s.replace_active_rule_by_name_if_revision(stale,name,candidate['rules'][name]);stale_rejected=False
   except ValueError as e: stale_rejected='stale experiment revision' in str(e)
   stale_unchanged=rules0==digest(n.export_rules())
   malformed=tuple(s.experiment_graph_rule_revision());rules1=digest(n.export_rules())
   try: s.replace_active_rule_by_name_if_revision(malformed,name,{'not':'a rule'});malformed_rejected=False
   except (ValueError,TypeError): malformed_rejected=True
   malformed_unchanged=rules1==digest(n.export_rules())
   rows[-1]['controls']={'stale_rejected':stale_rejected,'stale_unchanged':stale_unchanged,
    'malformed_rejected':malformed_rejected,'malformed_unchanged':malformed_unchanged}
 return rows
def main():
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or OUT.exists(): raise SystemExit('refusing to overwrite existing capture')
  LOCK.write_text(json.dumps({'schema':'ThoughtexperimentRuleActivationV1Lock','sources':frozen(),
   'families':FAMILIES,'workers':WORKERS},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if sys.argv[1:]==['--run']:
  lock=json.loads(LOCK.read_text())
  if frozen()!=lock['sources']: raise SystemExit('source drift from lock')
  rows=run(lock)
  if frozen()!=lock['sources']: raise SystemExit('source drift during capture')
  OUT.write_text(json.dumps({'schema':'ThoughtexperimentRuleActivationV1Results','lock_sha256':sha(LOCK),'sources':frozen(),
   'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'rows':rows},indent=2,sort_keys=True)+'\n')
  print(OUT.relative_to(ROOT));return 0
 raise SystemExit('usage: --lock | --run')
if __name__=='__main__': raise SystemExit(main())
