#!/usr/bin/env python3
"""Measure three real describe rules over controlled populations in a full-seed graph."""
from __future__ import annotations
import hashlib,importlib.util,json,os,platform,resource,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'scripts')]
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_DESCRIBE_RULE_FULL_SEED_CANDIDATE_SCALE_V1_PREREG_20260927.md'
LOCK=ROOT/'evaluation/substrate_capability/describe_rule_full_seed_candidate_scale_v1_lock_20260927.json'
OUT=ROOT/'evaluation/reports/describe_rule_full_seed_candidate_scale_v1_20260927.json'
PROVENANCE=ROOT/'scripts/substrate_seed_rule_provenance_live_capture_v1.py'
ARC=ROOT/'scripts/arc_self_report.py'
TARGETS={'a_counter':'meter','a_thing_that_stays_put':'static','a_thing_that_moves_itself':'mover'}
RULES={f'recognise_{name}' for name in TARGETS}
SCENES=(1,4);DISTRACTORS=(0,4096);REPLICATES=2
SCHEDULE=[(s,d,r) for s in SCENES for d in DISTRACTORS for r in range(REPLICATES)]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def runtime_inputs():
 spec=importlib.util.spec_from_file_location('seed_provenance_fullscale',PROVENANCE);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m.inputs()
def inputs():return {'protocol_sha256':sha(PROTOCOL),'runner_sha256':sha(__file__),'provenance_helper_sha256':sha(PROVENANCE),'arc_self_report_sha256':sha(ARC),'runtime_inputs':runtime_inputs(),'gaming_seed_sha256':sha(ROOT/'seeds/gaming.json'),'gaming_words_seed_sha256':sha(ROOT/'seeds/gaming_words.json')}
def nid(x):return int(x.value) if hasattr(x,'value') else int(x)
def worker(scene_count,distractors,rep):
 from substrate.world_adapter import WorldAdapter
 from substrate.boot_all import load_all_seeds
 from scripts.arc_self_report import build_describe_faculty
 from substrate_rs import _native
 a=WorldAdapter(seeds=());boot0=time.perf_counter_ns();boot=load_all_seeds(a);boot_ns=time.perf_counter_ns()-boot0
 faculty0=time.perf_counter_ns();build_describe_faculty(a);faculty_ns=time.perf_counter_ns()-faculty0
 n=a.inner;s=a.s
 # Verify exact target inventory before adding controlled inputs.
 target_nodes={name:[] for name in TARGETS}
 for node in s.nodes('Concept'):
  name=s.node(node)['attrs'].get('name')
  if name in target_nodes:target_nodes[name].append(nid(node))
 baseline_members=sum(len(n.neighbours(mt,'has_concept')) for mt in s.nodes('Microtheory'))
 baseline_scenes=sum(bool(n.neighbours(sc,'has_percept')) for sc in s.nodes('Scene'))
 member=[]
 for mt in s.nodes('Microtheory'):member.extend(n.neighbours(mt,'has_concept'))
 baseline_counts={'microtheories':len(s.nodes('Microtheory')),'concept_nodes':len(s.nodes('Concept')),'has_concept_memberships':baseline_members,'scenes_with_percepts':baseline_scenes,'target_concept_counts':{k:len(v) for k,v in target_nodes.items()}}
 # A dedicated Microtheory exists in every cell to keep the graph shape constant.
 noise_mt=n.add_node('Microtheory',{'name':'candidate_scale_noise_mt','fixture_role':'controlled_distractor_domain'})
 noise_ids=[]
 for i in range(distractors):
  c=s.add_node('Concept',{'name':f'fullscale_distractor_{i:05d}','fixture_role':'controlled_negative'})
  n.add_edge_unchecked(noise_mt,'has_concept',c);noise_ids.append(nid(c))
 scene_ids=[];percept_by_scene={}
 for si in range(scene_count):
  sc=s.add_node('Scene',{'name':f'candidate_scale_scene_{si}','fixture_role':'controlled_scene'})
  scene_ids.append(nid(sc));percept_by_scene[nid(sc)]={}
  for kind in ('meter','static','mover'):
   attrs={'kind':kind,'fixture_role':'controlled_percept'}
   if kind=='mover':attrs['responds_to_my_action']=False
   p=s.add_node('Percept',attrs);n.add_edge_unchecked(sc,'has_percept',p);percept_by_scene[nid(sc)][kind]=nid(p)
 # Tombstone every other rule, leaving the real source-generated recognition rules active.
 access=n.rule_access_sets();kept=[];removed=0
 for row in access:
  idx,name,active=int(row[0]),str(row[1]),bool(row[2])
  if active and name in RULES:kept.append((idx,name))
  elif active:
   if n.remove_rule(idx):removed+=1
 active_after=[str(row[1]) for row in n.rule_access_sets() if bool(row[2])]
 # Only mutate the full graph's workload through native closure after counters start.
 Native=_native.Substrate;Native.scale_audit_reset();Native.scale_audit_per_rule_reset();Native.scale_audit_set_enabled(True);Native.scale_audit_set_per_rule_enabled(True)
 wall0,cpu0=time.perf_counter_ns(),time.process_time_ns();settle=n.run_rules_report(100000,False);wall_ns,cpu_ns=time.perf_counter_ns()-wall0,time.process_time_ns()-cpu0
 scale=dict(Native.scale_audit_snapshot());raw=Native.scale_audit_per_rule_snapshot();rule_names={int(x[0]):str(x[1]) for x in n.rule_access_sets()}
 per=[{'rule_index':int(idx),'rule_name':rule_names.get(int(idx),'?'),'metric':str(metric),'count':int(count)} for idx,metric,count in raw]
 Native.scale_audit_set_per_rule_enabled(False);Native.scale_audit_set_enabled(False)
 actual={}
 for scene_id,bykind in percept_by_scene.items():
  for kind,pid in bykind.items():
   found=[]
   for target in n.neighbours(_native.NodeID(pid),'is_a'):
    attrs=s.node(target)['attrs'];name=attrs.get('name')
    if name in TARGETS:found.append(nid(target))
   actual[f'{scene_id}:{kind}']=sorted(found)
 expected={f'{scene_id}:{kind}':sorted(target_nodes[label]) for scene_id,bykind in percept_by_scene.items() for label,kind in TARGETS.items()}
 no_distractor_classification=all(not n.has_edge(_native.NodeID(pid),'is_a',_native.NodeID(cid)) for bykind in percept_by_scene.values() for pid in bykind.values() for cid in noise_ids)
 final_members=sum(len(n.neighbours(mt,'has_concept')) for mt in s.nodes('Microtheory'))
 return {'scene_count':scene_count,'distractor_count':distractors,'replicate':rep,'pid':os.getpid(),'boot_loaded':boot.get('loaded'),'boot_failure_count':len(boot.get('failed',[])),'boot_wall_ns':boot_ns,'faculty_wall_ns':faculty_ns,
  'baseline_graph_counts':baseline_counts,'final_microtheory_count':len(s.nodes('Microtheory')),'final_concept_count':len(s.nodes('Concept')),'final_has_concept_memberships':final_members,
  'target_rule_names':sorted(RULES),'target_rule_indices':sorted(kept),'removed_active_rule_count':removed,'active_rule_names_after_tombstone':sorted(active_after),
  'settle_report':settle,'expected_classifications':expected,'actual_classifications':actual,'classification_exact':actual==expected,'no_distractor_classification':no_distractor_classification,
  'scale_audit':scale,'per_rule_audit':per,'wall_ns':wall_ns,'cpu_ns':cpu_ns,'peak_rss_bytes':int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024),'environment':{'python':sys.version,'platform':platform.platform()}}
def worker_ok(r):return r['settle_report']['status']=='fixed_point' and r['classification_exact'] and r['no_distractor_classification'] and set(r['active_rule_names_after_tombstone'])==RULES and all(v==1 for v in r['baseline_graph_counts']['target_concept_counts'].values())
def main():
 if sys.argv[1:]==['--lock']:print(json.dumps({'locked_inputs':inputs()},indent=2,sort_keys=True));return
 if sys.argv[1:]==['--worker']:
  before=inputs();r=worker(int(os.environ['OCEL0_FULLSCALE_SCENES']),int(os.environ['OCEL0_FULLSCALE_DISTRACTORS']),int(os.environ['OCEL0_FULLSCALE_REP']));after=inputs();r.update({'worker_inputs_before':before,'worker_inputs_after':after,'source_stable':before==after});print(json.dumps(r,sort_keys=True));return
 locked=inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing/stale full-seed candidate scale lock')
 env={**os.environ,'PYTHONPATH':f'{ROOT}:{ROOT / "runners/dsl/python"}:{ROOT / "scripts"}','OZMA_NO_LLM':'1','OZMA_SEED_PERSIST_DISABLED':'1'}
 stale=subprocess.check_output([sys.executable,'-c',"from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')) )"],cwd=ROOT,env=env,text=True).strip()
 if stale:raise SystemExit(f'native build stale: {stale}')
 runs=[]
 for scenes,distractors,rep in SCHEDULE:
  e=env.copy();e.update(OCEL0_FULLSCALE_SCENES=str(scenes),OCEL0_FULLSCALE_DISTRACTORS=str(distractors),OCEL0_FULLSCALE_REP=str(rep));p=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker'],cwd=ROOT,env=e,text=True,capture_output=True,timeout=300)
  r=json.loads(p.stdout) if p.stdout.strip() else {'scene_count':scenes,'distractor_count':distractors,'replicate':rep,'worker_error':p.stderr};r['worker_returncode']=p.returncode;r['worker_stderr']=p.stderr;runs.append(r);print(f'completed=scenes{scenes}_distractors{distractors}/{rep} rc={p.returncode}',file=sys.stderr,flush=True)
 after=inputs();checks={'eight_workers':len(runs)==8,'unique_pids':len({r.get('pid') for r in runs})==8,'two_per_cell':all(sum(r.get('scene_count')==s and r.get('distractor_count')==d for r in runs)==2 for s,d,_ in SCHEDULE),'parent_source_stable':after==locked,'workers_source_stable':all(r.get('source_stable') and r.get('worker_inputs_before')==locked==r.get('worker_inputs_after') for r in runs),'all_workers_returned':all(r.get('worker_returncode')==0 for r in runs),'all_semantics_fixedpoint':all(worker_ok(r) for r in runs)}
 summary=[]
 for scenes,distractors in ((s,d) for s in SCENES for d in DISTRACTORS):
  group=[r for r in runs if r.get('scene_count')==scenes and r.get('distractor_count')==distractors]
  def med(metric):return int(sorted(r[metric] for r in group)[len(group)//2]) if group else None
  terms=sum(x['count'] for r in group for x in r.get('per_rule_audit',[]) if x['metric']=='term_evaluations')//max(1,len(group))
  pairs=sum(x['count'] for r in group for x in r.get('per_rule_audit',[]) if x['metric']=='candidate_pairs')//max(1,len(group))
  summary.append({'scene_count':scenes,'percepts_total':scenes*3,'distractor_count':distractors,'replicates':len(group),'candidate_pairs_median':pairs,'term_evaluations_median':terms,'closure_wall_ms_median':med('wall_ns')/1e6 if group else None,'closure_cpu_ms_median':med('cpu_ns')/1e6 if group else None})
 report={'schema_version':1,'run_id':'describe-rule-full-seed-candidate-scale-v1-20260927','locked_inputs':locked,'post_run_inputs':after,'schedule':SCHEDULE,'checks':checks,'all_checks_pass':all(checks.values()),'summary_by_cell':summary,'runs':runs,'claim_boundary':'Full-seed graph with only three exact describe recognition rules active during measured closure; other graph state remains loaded, but their rules are tombstoned. Not full active-rule conversation closure or natural-task scale.'}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':checks,'summary_by_cell':summary},indent=2))
 if not all(checks.values()):raise SystemExit('full-seed candidate scale gates failed')
if __name__=='__main__':main()
