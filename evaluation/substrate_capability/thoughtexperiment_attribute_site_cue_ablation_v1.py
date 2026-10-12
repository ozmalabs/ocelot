#!/usr/bin/env python3
"""Source-locked cue ablation for ordered structural edit-site selection."""
from __future__ import annotations
import copy, hashlib, json, os, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
RUNNER=Path(__file__).resolve()
PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_ATTRIBUTE_SITE_CUE_ABLATION_V1_PREREG_20261002.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_attribute_site_cue_ablation_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_attribute_site_cue_ablation_v1_lock_20261002.json'
CAPTURE=ROOT/'evaluation/reports/thoughtexperiment_attribute_site_cue_ablation_v1_20261002.json'
WORKERS=4; TARGET='classify_meter_delta'
CUES={
 'answer_bearing':['classify','meter','delta','swap','attribute','bad_score to good_score'],
 'direction_omitted':['classify','meter','delta','swap','attribute'],
 'source_only':['classify','meter','delta','swap','attribute','bad_score'],
 'destination_only':['classify','meter','delta','swap','attribute','good_score'],
}
ACTIVE=('domains/reflective_faculty.py','domains/edit_ops.py','domains/self_correction.py','domains/engine_provenance.py',
 'substrate/boot_core.py','substrate/seed_loader.py','runners/dsl/src/py.rs','runners/dsl/src/substrate.rs',
 'runners/dsl/src/graph.rs','runners/dsl/src/graph_rules.rs','runners/dsl/src/term.rs','runners/dsl/src/persist.rs',
 'runners/dsl/src/grammar.rs','runners/dsl/src/sym.rs','runners/dsl/src/lib.rs','runners/dsl/Cargo.toml','runners/dsl/Cargo.lock',
 'runners/dsl/python/substrate_rs/__init__.py','seeds/relation_vocabulary.json')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def frozen():
 from substrate_rs import _native
 paths=[ROOT/p for p in ACTIVE]+[RUNNER,ANALYZER,PROTOCOL]
 out={str(p.relative_to(ROOT)):sha(p) for p in paths};out['loaded_native_binary']=sha(Path(_native.__file__).resolve());return out
def target_rule():
 V=lambda n:{'type':'Var','name':n}; A=lambda n,k:{'type':'Attr','node':V(n),'key':k}; L=lambda x:{'type':'Lit','value':x}
 return {'name':TARGET,'active':True,'match':[['world','has_request','req'],['req','has_measurement','m']],
 'where':{'type':'Eq','a':A('req','classified'),'b':L(0.0)},
 'effects':[['set_attr','req','predicted',{'__term__':{'type':'IfThenElse','cond':{'type':'Gt','a':A('m','bad_score'),'b':L(0.0)},'then':A('m','positive'),'other':A('m','negative')}}],
 ['set_attr','req','classified',1.0],['set_attr','req','audit',{'__term__':A('m','good_score')}]]}
def one(worker,condition,cue):
 from substrate.boot_core import boot_core
 from substrate.seed_loader import manifest_for
 import domains.reflective_faculty as rf
 from domains.self_correction import _default_candidates
 sub,root=boot_core(seeds=());native=sub._inner;native.load_seed_manifest(manifest_for('relation_vocabulary'),root)
 native.add_rule(target_rule());before=copy.deepcopy(next(r for r in native.export_rules() if r.get('name')==TARGET))
 key=f'cue_ablation_{worker}_{condition}'
 sub.add_node('CapabilityAxis',{'is_axis':1.0,'capability_keys':[key],'induced':1.0,'residual_predicates':cue,
  'structural_rule_scope':'all_mutable_rules','from_observation':1.0,'source':'attribute_site_cue_ablation_v1'})
 agent=type('Agent',(),{'s':sub,'inner':native,'agent':root})()
 t=time.perf_counter_ns();result=rf.compose_general_structural_variant(agent,[key],f'{worker}_{condition}');elapsed=time.perf_counter_ns()-t
 after=copy.deepcopy(next(r for r in native.export_rules() if r.get('name')==TARGET))
 candidates=_default_candidates(native,TARGET);labels=sorted(c['label'] for c in candidates if c['label'].startswith('swap_term_leaf:'))
 return {'worker':worker,'condition':condition,'cue':cue,'built':bool(result.get('built')),'wall':result.get('wall'),
  'target':result.get('removed_rule'),'operator':result.get('kind'),'site':result.get('site'),'decision_ns':elapsed,
  'ordered_swap_candidate_labels':labels,'primary_unchanged':before==after}
def capture():
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('stale native engine: '+'; '.join(stale))
 if not LOCK.exists():raise SystemExit('missing source lock')
 lock=json.loads(LOCK.read_text())
 if frozen()!=lock['sources']:raise SystemExit('source drift from lock')
 rows=[one(w,c,cue) for w in range(WORKERS) for c,cue in CUES.items()]
 if frozen()!=lock['sources']:raise SystemExit('source drift during capture')
 doc={'schema':'AttributeSiteCueAblationV1','lock_sha256':sha(LOCK),'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
 'semantic_engine':rust_source_fingerprint(str(ROOT)),'workers':WORKERS,'conditions':rows}
 CAPTURE.write_text(json.dumps(doc,indent=2,sort_keys=True)+'\n');print(CAPTURE.relative_to(ROOT))
def main():
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or CAPTURE.exists():raise SystemExit('refusing to overwrite')
  from domains.engine_provenance import rust_source_fingerprint
  LOCK.write_text(json.dumps({'schema':'AttributeSiteCueAblationV1Lock','sources':frozen(),'semantic_engine':rust_source_fingerprint(str(ROOT)),
   'workers':WORKERS,'conditions':CUES},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT))
 elif sys.argv[1:]==['--capture']:capture()
 else:raise SystemExit('use --lock or --capture')
if __name__=='__main__':main()
