#!/usr/bin/env python3
"""Full candidate-level train/held-out utility capture for shape-axis repair."""
from __future__ import annotations
import hashlib, json, os, platform, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'evaluation/substrate_capability')]
RUNNER=Path(__file__).resolve()
PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_SHAPE_AXIS_FULL_CANDIDATE_ADMISSION_V1_PREREG_20261002.md'
BASE_RUNNER=ROOT/'evaluation/substrate_capability/thoughtexperiment_graph_authored_correction_rank_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_shape_axis_full_candidate_admission_v1_lock_20261002.json'
RAW=ROOT/'evaluation/reports/thoughtexperiment_shape_axis_full_candidate_admission_v1_raw_20261002.json'
SOURCES=(
 'domains/reflective_faculty.py','domains/collapse_watch.py','domains/collapse_model.py',
 'domains/self_correction.py','domains/self_correct_dispatch.py','domains/imagination.py',
 'domains/engine_provenance.py','substrate/boot_core.py','substrate/seed_loader.py',
 'seeds/shape_decode_loop.json','seeds/relation_vocabulary.json',
 'seeds/composer_dispatch.json','seeds/autonomy.json',
 'runners/dsl/src/py.rs','runners/dsl/src/substrate.rs','runners/dsl/src/graph.rs',
 'runners/dsl/src/graph_rules.rs','runners/dsl/src/term.rs','runners/dsl/src/persist.rs',
 'runners/dsl/src/grammar.rs','runners/dsl/src/sym.rs','runners/dsl/src/lib.rs',
 'runners/dsl/Cargo.toml','runners/dsl/Cargo.lock',
 'runners/dsl/python/substrate_rs/__init__.py')
TARGET='sd_mint_quantum'
WORKERS=4

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def frozen()->dict:
 from substrate_rs import _native
 rows={p:sha(ROOT/p) for p in SOURCES}
 rows.update({str(p.relative_to(ROOT)):sha(p) for p in (RUNNER,PROTOCOL,BASE_RUNNER)})
 rows['loaded_native_binary']=sha(Path(_native.__file__).resolve())
 return rows
def digest(candidate:dict)->str:
 bundle={}
 for target,rule in sorted((candidate.get('rules') or {}).items()):
  value=json.loads(json.dumps(rule,sort_keys=True)) if rule is not None else None
  if isinstance(value,dict):value.pop('name',None)
  bundle[target]=value
 return 'sha256:'+hashlib.sha256(json.dumps(bundle,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

class Agent:
 def __init__(self,sub,root):self.s=sub;self.inner=sub._inner;self.agent=root

def build_context(worker:int,split:str)->tuple:
 import domains.reflective_faculty as rf
 from substrate.boot_core import boot_core
 from substrate.seed_loader import manifest_for
 from domains import collapse_watch as cw
 from domains.collapse_model import predict_collapse
 from domains.self_correction import _default_candidates,_infer_growth_rule
 import thoughtexperiment_graph_authored_correction_rank_v1 as base
 started=time.perf_counter_ns()
 sub,root=boot_core()
 for seed in ('relation_vocabulary','composer_dispatch','autonomy'):
  sub._inner.load_seed_manifest(manifest_for(seed),root)
 agent=Agent(sub,root)
 for phrase,tag in ((['predict','COLLAPSE','of','DIVERGENCE'],f'shape_cw_{worker}_{split}'),
                    (['correct','DIVERGENCE','by','CANDIDATE'],f'shape_sc_{worker}_{split}')):
  induced=rf.induce_concern(agent,[phrase],name_hint=tag)
  rf.ground_concern(agent,[induced['capability_key']])
 native=rf._native_eval2(sub)
 rf._ensure_shape_decode_loop(sub,native,root)
 for rule_name in ('sd_mint_quantum','sd_dedup_existing'):
  sub.add_node('RuleSummary',{'name':rule_name,'from_seed':'shape_axis_full_candidate_admission'})
 sub.add_node('SeedSummary',{'seed_id':'self_correction_rank_eval','skippable':1.0})
 base.add_wave(sub,root,f'{split}_{worker}_A')
 cw.scan_and_predict(agent)
 int(native.run_rules(2000))
 base.add_wave(sub,root,f'{split}_{worker}_B')
 model=predict_collapse(agent)
 target=_infer_growth_rule(native,model)
 if target!=TARGET:raise RuntimeError(f'expected target {TARGET}, got {target!r}')
 enum_started=time.perf_counter_ns();candidates=_default_candidates(native,target);enum_ns=time.perf_counter_ns()-enum_started
 candidates=[c for c in candidates if (c.get('rules') or {}).get(TARGET) is not None]
 if len(candidates)!=6:raise RuntimeError(f'expected six usable candidates, got {len(candidates)}')
 elapsed=time.perf_counter_ns()-started
 return sub,agent,native,model,candidates,{'context_setup_ns':elapsed,'enumeration_ns':enum_ns}

def score_candidate(worker:int,split:str,candidate:dict)->dict:
 import thoughtexperiment_graph_authored_correction_rank_v1 as base
 from domains.imagination import imagine
 total_started=time.perf_counter_ns()
 sub,agent,native,_model,_candidates,setup=build_context(worker,split)
 source_revision=tuple(int(x) for x in native.experiment_graph_rule_revision())
 original_rules=native.export_rules()
 branch_started=time.perf_counter_ns()
 branch_record=imagine(agent,hypothesis=None,steps=0,cut_grounding=False,focus_hops=1,record_trace=False)
 branch_ns=time.perf_counter_ns()-branch_started
 branch=branch_record.detached;bn=branch._inner;patch_started=time.perf_counter_ns();applied=[]
 replace=getattr(bn,'replace_active_rule_by_name',None)
 if replace is None:raise RuntimeError('native active-rule patch unavailable')
 for name,variant in sorted((candidate.get('rules') or {}).items()):
  if replace(name,variant):applied.append(name)
 patch_ns=time.perf_counter_ns()-patch_started
 prefix=f'{split}_{worker}_C'
 heldout=[]
 for i in range(3):
  token=f'{prefix}{i}'
  node=branch.add_node('Observation',{'signature':[[token,'X']],'key':[token],'status':'pending'})
  try:bn.add_edge_unchecked(agent.agent,'observed',node,{})
  except TypeError:bn.add_edge_unchecked(agent.agent,'observed',node)
  heldout.append((token,node))
 closure_started=time.perf_counter_ns();first_work=int(bn.run_rules(2000));fixed_work=int(bn.run_rules(2000));closure_ns=time.perf_counter_ns()-closure_started
 pending=[];axis_counts={}
 for token,node in heldout:
  if branch.has_node(node) and branch.node(node)['attrs'].get('status')=='pending':pending.append(token)
  matching=[axis for axis in branch.nodes('CapabilityAxis')
            if branch.node(axis)['attrs'].get('induced')
            and branch.node(axis)['attrs'].get('capability_keys')==[[token,'X']]]
  axis_counts[token]=len(matching)
 patched_names=set((candidate.get('rules') or {}).keys())
 active={r.get('name'):r.get('active',True) for r in bn.export_rules()
         if r.get('name') in patched_names}
 source_still=tuple(int(x) for x in native.experiment_graph_rule_revision())==source_revision and native.export_rules()==original_rules
 applied_task_rule=TARGET in applied
 oracle={'all_observations_settled':not pending,'one_axis_per_signature':all(v==1 for v in axis_counts.values()),
         'native_fixed_point':fixed_work==0,'candidate_applied':applied_task_rule}
 return {'worker':worker,'split':split,'label':candidate['label'],'digest':digest(candidate),
  'applied_rules':applied,'branch_target_state':active,
  'task_cases':[x[0] for x in heldout],'pending':pending,'axis_count_by_signature':axis_counts,
  'first_closure_work':first_work,'fixedpoint_work':fixed_work,'active_rule_state':active,
  'oracle':oracle,'utility':float(all(oracle.values())),'primary_preserved':source_still,
  'cost_ns':{**setup,'branch_creation_ns':branch_ns,
   'candidate_patch_ns':patch_ns,'task_closure_ns':closure_ns,
   'candidate_total_ns':time.perf_counter_ns()-total_started}}

def worker(index:int)->dict:
 before=frozen();train_ctx=build_context(index,'train');held_ctx=build_context(index,'heldout')
 train_candidates=train_ctx[4];held_candidates=held_ctx[4]
 train_desc=[{'label':c['label'],'digest':digest(c),'targets':sorted(c.get('rules',{}))} for c in train_candidates]
 held_desc=[{'label':c['label'],'digest':digest(c),'targets':sorted(c.get('rules',{}))} for c in held_candidates]
 if train_desc!=held_desc:raise RuntimeError('candidate descriptors differ between train and heldout contexts')
 train_scores=[score_candidate(index,'train',c) for c in train_candidates]
 held_scores=[score_candidate(index,'heldout',c) for c in held_candidates]
 train_cases={x for row in train_scores for x in row['task_cases']};held_cases={x for row in held_scores for x in row['task_cases']}
 after=frozen()
 return {'worker':index,'pid':os.getpid(),'source_before':before,'source_after':after,'source_stable':before==after,
  'candidate_descriptors':train_desc,'candidate_count':len(train_desc),
  'training_case_ids':sorted(train_cases),'heldout_case_ids':sorted(held_cases),
  'disjoint_cases':not bool(train_cases&held_cases),'training_outcomes':train_scores,'heldout_outcomes':held_scores}

def main()->int:
 if sys.argv[1:2]==['--worker']:
  print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,separators=(',',':')));return 0
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('stale native engine: '+'; '.join(stale))
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or RAW.exists():raise SystemExit('refusing to overwrite lock/capture')
  LOCK.write_text(json.dumps({'schema':'ShapeAxisFullCandidateAdmissionV1Lock','sources':frozen(),
   'semantic_engine':rust_source_fingerprint(str(ROOT)),'workers':WORKERS,'candidate_count':6,
   'train_heldout_disjoint':True},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
 if not LOCK.exists() or RAW.exists():raise SystemExit('missing lock or capture already exists')
 before=frozen();lock=json.loads(LOCK.read_text())
 if before!=lock['sources']:raise SystemExit('source drift from lock')
 env={**os.environ,'PYTHONPATH':f'{ROOT / "runners/dsl/python"}:{ROOT}:{ROOT / "evaluation/substrate_capability"}'}
 workers=[]
 for i in range(WORKERS):
  proc=subprocess.run([sys.executable,str(RUNNER),'--worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True)
  if proc.returncode:raise RuntimeError(f'worker {i}: {proc.stderr[-4000:]}')
  workers.append(json.loads(proc.stdout.strip().splitlines()[-1]))
 after=frozen()
 if before!=after:raise SystemExit('source drift during candidate admission capture')
 raw={'schema':'ShapeAxisFullCandidateAdmissionV1Capture','captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
  'host':{'platform':platform.platform(),'machine':platform.machine(),'python':sys.version.split()[0]},
  'lock':lock,'semantic_engine':rust_source_fingerprint(str(ROOT)),
  'source_before':before,'source_after':after,'workers':workers}
 RAW.write_text(json.dumps(raw,indent=2,sort_keys=True)+'\n')
 held=workers[0]['heldout_outcomes']
 print(json.dumps({'workers':len(workers),'candidates':len(workers[0]['candidate_descriptors']),
  'heldout_utility':{x['label']:x['utility'] for x in held},'raw':RAW.relative_to(ROOT).as_posix()},sort_keys=True));return 0
 raise SystemExit('choose --lock or capture')
if __name__=='__main__':raise SystemExit(main())
