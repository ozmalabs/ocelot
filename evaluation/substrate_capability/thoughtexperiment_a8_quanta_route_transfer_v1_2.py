#!/usr/bin/env python3
"""Source-locked graph proposal transfer into production quantum-route worlds."""
from __future__ import annotations
import copy,hashlib,json,os,platform,subprocess,sys,time
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'evaluation/substrate_capability')]
RUNNER=Path(__file__).resolve()
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_a8_quanta_route_transfer_v1_2.py'
PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_A8_QUANTA_ROUTE_TRANSFER_V1_PREREG_20261002.md'
AMENDMENT=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_A8_QUANTA_ROUTE_TRANSFER_V1_2_AMENDMENT_20261002.md'
EVIDENCE=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_A8_QUANTA_ROUTE_TRANSFER_V1_1_RESULTS_20261002.md'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_a8_quanta_route_transfer_v1_2_lock_20261002.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_a8_quanta_route_transfer_v1_2_orders_20261002.json'
SCORES=ROOT/'evaluation/reports/thoughtexperiment_a8_quanta_route_transfer_v1_2_scores_20261002.json'
TARGET='qf_hop_route';WORKERS=4
COMMON=['test','send','judge','structure','gradient']
PROMPT=COMMON+['qf','hop','route','flip','comparison','gate']
CASES=[
 {'case':'H1_vertical_portal','start':[0,0],'goal':[0,4],'orientation':'vertical','opening':2},
 {'case':'H2_horizontal_portal','start':[0,0],'goal':[4,0],'orientation':'horizontal','opening':2},
 {'case':'H3_vertical_portal_mirror','start':[4,0],'goal':[4,4],'orientation':'vertical','opening':1},
 {'case':'H4_horizontal_portal_mirror','start':[4,4],'goal':[0,4],'orientation':'horizontal','opening':3},
]
SOURCES=(
 'domains/reflective_faculty.py','domains/edit_ops.py','domains/self_correction.py',
 'domains/engine_provenance.py','substrate/boot_core.py','substrate/seed_loader.py',
 'runners/dsl/src/py.rs','runners/dsl/src/substrate.rs','runners/dsl/src/graph.rs',
 'runners/dsl/src/graph_rules.rs','runners/dsl/src/term.rs','runners/dsl/src/persist.rs',
 'runners/dsl/src/grammar.rs','runners/dsl/src/sym.rs','runners/dsl/src/lib.rs',
 'runners/dsl/Cargo.toml','runners/dsl/Cargo.lock',
 'runners/dsl/python/substrate_rs/__init__.py','seeds/quanta_navigation.json',
 'seeds/relation_vocabulary.json','tests/test_quanta_navigation_migrated.py')

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def frozen()->dict:
 from substrate_rs import _native
 paths=(*[ROOT/p for p in SOURCES],RUNNER,ANALYZER,PROTOCOL,AMENDMENT,EVIDENCE)
 rows={str(p.relative_to(ROOT)):sha(p) for p in paths}
 rows['loaded_native_binary']=sha(Path(_native.__file__).resolve())
 return rows

def semantic_digest(candidate):
 bundle={}
 for name,rule in sorted((candidate.get('rules') or {}).items()):
  row=copy.deepcopy(rule)
  if isinstance(row,dict):
   for key in ('name','content_hash','revision','rule_uid'):row.pop(key,None)
  bundle[name]=row
 return 'sha256:'+hashlib.sha256(json.dumps(bundle,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

def _receipt_equal(actual,expected):
 def edge_counter(rows):return Counter(json.dumps(row,sort_keys=True,separators=(',',':')) for row in rows or [])
 if actual.get('name')!=expected.get('name'):return False
 if edge_counter(actual.get('match'))!=edge_counter(expected.get('match')):return False
 if actual.get('where')!=expected.get('where') or actual.get('effects')!=expected.get('effects'):return False
 if actual.get('match_type')!=expected.get('match_type'):return False
 return True

def _mutate_literal(value):
 if isinstance(value,dict):
  if value.get('type')=='Lit' and 'value' in value:
   value['value']=str(value['value'])+'__receipt_mismatch__';return True
  for child in value.values():
   if _mutate_literal(child):return True
 elif isinstance(value,list):
  for child in value:
   if _mutate_literal(child):return True
 return False

def _receipt_controls():
 s,root,n,agent,source,fault=_fresh_faulted();branch=s.fork_full_copy_experiment();bn=branch._inner
 if not bn.replace_active_rule_by_name(TARGET,source):raise RuntimeError('receipt preflight could not install source rule')
 active=next(r for r in bn.export_rules() if r.get('name')==source['name'] and r.get('active',True))
 positives={'exact_source_receipt':_receipt_equal(active,source)}
 reordered=copy.deepcopy(source);reordered['match']=list(reversed(reordered.get('match',[])))
 positives['match_edge_order_canonicalized']=_receipt_equal(active,reordered)
 negatives={}
 changed=copy.deepcopy(source);changed['where']=copy.deepcopy(changed['where'])
 if not _mutate_literal(changed['where']):raise RuntimeError('receipt guard mismatch control unavailable')
 negatives['guard_literal_rejected']=not _receipt_equal(active,changed)
 changed=copy.deepcopy(source);changed['effects']=copy.deepcopy(changed['effects']);changed['effects'][0][0]=str(changed['effects'][0][0])+'__mismatch__'
 negatives['effect_operator_rejected']=not _receipt_equal(active,changed)
 changed=copy.deepcopy(source);changed['effects']=copy.deepcopy(changed['effects'])
 if not _mutate_literal(changed['effects']):raise RuntimeError('receipt effect-literal control unavailable')
 negatives['effect_literal_rejected']=not _receipt_equal(active,changed)
 order_rule=next(copy.deepcopy(r) for r in n.export_rules()
  if r.get('name')=='qf_stale_on_belief_change' and r.get('active',True))
 reordered_active=copy.deepcopy(order_rule);reordered_expected=copy.deepcopy(order_rule)
 reordered_active['effects']=list(reversed(reordered_active['effects']))
 negatives['effect_order_rejected']=not _receipt_equal(reordered_active,reordered_expected)
 if not all(positives.values()) or not all(negatives.values()):raise RuntimeError(f'receipt controls failed: {positives} {negatives}')
 return {'positive':positives,'negative':negatives}

def describe(candidate):
 return {'label':candidate['label'],'semantic_digest':semantic_digest(candidate),
  'targets':sorted((candidate.get('rules') or {}).keys())}

def _fresh_faulted():
 from substrate.boot_core import boot_core
 from substrate.seed_loader import manifest_for
 from domains.edit_ops import apply_flip_comparison
 s,root=boot_core(seeds=());n=s._inner
 n.load_seed_manifest(manifest_for('relation_vocabulary'),root)
 n.load_seed_manifest(manifest_for('quanta_navigation'),root)
 rows=n.export_rules();idx=next(i for i,r in enumerate(rows) if r.get('name')==TARGET and r.get('active',True))
 source=copy.deepcopy(rows[idx]);fault=apply_flip_comparison(source,TARGET)
 if fault is None:raise RuntimeError('qf_hop_route has no flip-comparison variant')
 if not n.remove_rule(idx):raise RuntimeError('could not install faulted qf_hop_route')
 n.add_rule(fault)
 class Agent:
  def __init__(self):self.s=s;self.inner=n;self.agent=root
 return s,root,n,Agent(),source,fault

def compose(worker,cue):
 import domains.reflective_faculty as rf
 s,root,n,agent,source,fault=_fresh_faulted()
 axis=f'a8_quanta_route_{worker}_'+('prompted' if cue else 'unprompted')
 preds=list(PROMPT if cue else COMMON)
 s.add_node('CapabilityAxis',{'is_axis':1.0,'capability_keys':[axis],'induced':1.0,
  'residual_predicates':preds,'from_observation':1.0,
  'source':'thoughtexperiment_a8_quanta_route_transfer_v1'})
 before=next(copy.deepcopy(r) for r in n.export_rules() if r.get('name')==TARGET and r.get('active',True))
 start=time.perf_counter_ns();result=rf.ground_concern(agent,[axis]);elapsed=time.perf_counter_ns()-start
 after=next(copy.deepcopy(r) for r in n.export_rules() if r.get('name')==TARGET and r.get('active',True))
 structural=result.get('structural_variant') or {};rule=structural.get('rule') if structural.get('built') else None
 candidate={'label':'a8_graph_'+str(structural.get('kind')),'rules':{TARGET:copy.deepcopy(rule)}} if rule else None
 return {'grounded':bool(result.get('grounded')),'served_by':result.get('served_by'),
  'path':result.get('path'),'built':bool(structural.get('built')),'kind':structural.get('kind'),
  'target':structural.get('removed_rule'),'candidate':candidate,
  'semantic_digest':semantic_digest(candidate) if candidate else None,
  'target_rule_preserved':before==after,'composer_ns':elapsed,
  'graph_revision':list(n.experiment_graph_rule_revision()),'residual':preds}

def order_worker(worker):
 from domains.self_correction import _default_candidates
 before=frozen();setup_started=time.perf_counter_ns();s,root,n,agent,source,fault=_fresh_faulted()
 common_setup_ns=time.perf_counter_ns()-setup_started
 enum_started=time.perf_counter_ns();candidates=[copy.deepcopy(c) for c in _default_candidates(n,TARGET) if c.get('rules',{}).get(TARGET) is not None]
 enumeration_ns=time.perf_counter_ns()-enum_started
 if len(candidates)<2:raise RuntimeError('host candidate set incomplete for qf_hop_route')
 prompt=compose(worker,True);no=compose(worker,False)
 after=frozen()
 if before!=after:raise RuntimeError('source drift during quanta-route order capture')
 return {'worker':worker,'source_before':before,'source_after':after,'source_stable':before==after,
  'target':TARGET,'source_rule':source,'fault_rule':fault,
  'host_candidates':candidates,'host_descriptors':[describe(c) for c in candidates],
  'common_setup_ns':common_setup_ns,'host_enumeration_ns':enumeration_ns,
  'prompted':prompt,'unprompted':no}

def _build_world(s,n,case):
 game=s.add_node('WorldInstance',{'world_type':'Game','nav_repr':'quanta','nav_mode':'seek',
  'avatar_pose':case['start'],'flood_epoch':0.0})
 grid=[]
 for r in range(5):
  row=[]
  for c in range(5):
   wall=(c==2 and r!=case['opening']) if case['orientation']=='vertical' else (r==2 and c!=case['opening'])
   row.append('#' if wall else 0)
   cell=s.add_node('WorldInstance',{'world_type':'Cell','row':float(r),'col':float(c),
    'value':3.0 if wall else 4.0})
   n.add_edge_unchecked(game,'has_cell',cell,{})
  grid.append(row)
 gid=int(str(game).lstrip('#'));n.space_quantize(gid,2,'1x1',[4],[0,0],[4,4],1)
 region=s.add_node('Region',{'is_self':1.0});n.add_edge_unchecked(game,'has_region',region,{})
 for name,(dr,dc) in (('Up',(-1,0)),('Down',(1,0)),('Left',(0,-1)),('Right',(0,1))):
  cr=s.add_node('ControlResponse',{'dr':float(dr),'dc':float(dc),'dz':0.0,'cname':name})
  n.add_edge_unchecked(region,'responds_via',cr,{})
 goal=s.add_node('Goal',{'pose':case['goal'],'committed':1.0,'world':1.0})
 n.add_edge_unchecked(game,'committed_goal',goal,{})
 return game,grid

DISP={'Up':(-1,0),'Down':(1,0),'Left':(0,-1),'Right':(0,1)}
def _run_prebuilt_case(s,n,game,grid,case,max_steps=16):
 started=time.perf_counter_ns();pos=tuple(case['start']);path=[list(pos)];wall_hits=0;work=0
 for step in range(max_steps):
  if pos==tuple(case['goal']):break
  n.set_attr(game,'avatar_pose',[pos[0],pos[1]])
  n.set_attr(game,'chosen_action','');n.set_attr(game,'closed',-1.0);n.set_attr(game,'flood_epoch',float(step+1))
  work+=int(n.run_rules(10000));n.set_attr(game,'closed',0.0);work+=int(n.run_rules(10000))
  action=s.node(game)['attrs'].get('chosen_action') or ''
  if action not in DISP:break
  dr,dc=DISP[action];next_pos=(pos[0]+dr,pos[1]+dc)
  in_bounds=0<=next_pos[0]<5 and 0<=next_pos[1]<5
  if not in_bounds or grid[next_pos[0]][next_pos[1]]=='#':wall_hits+=1
  else:pos=next_pos
  path.append(list(pos))
 passed=pos==tuple(case['goal']) and wall_hits==0 and (2,case['opening']) in {tuple(p) for p in path} if case['orientation']=='vertical' else pos==tuple(case['goal']) and wall_hits==0 and (case['opening'],2) in {tuple(p) for p in path}
 attrs=s.node(game)['attrs'];minted=list(n.neighbours(game,'minted'))
 return {'case':case['case'],'passed':bool(passed),'reached_goal':pos==tuple(case['goal']),
  'wall_hits':wall_hits,'crossed_opening':(2,case['opening']) in {tuple(p) for p in path} if case['orientation']=='vertical' else (case['opening'],2) in {tuple(p) for p in path},
  'steps':len(path)-1,'path':path,'closed':attrs.get('closed'),'minted_hypotheses':len(minted),
  'closure_work':work,'task_elapsed_ns':time.perf_counter_ns()-started}

def _primary_fingerprint(s,n):
 nodes=sorted((str(node),s.node(node)['type'],s.node(node)['attrs']) for node in s.nodes())
 return {'rules':n.export_rules(),'revision':tuple(n.experiment_graph_rule_revision()),
  'nodes':nodes,'edges':int(n.edge_count())}

def _make_primary(case):
 from substrate.boot_core import boot_core
 from substrate.seed_loader import manifest_for
 s,root=boot_core(seeds=());n=s._inner
 n.load_seed_manifest(manifest_for('relation_vocabulary'),root);n.load_seed_manifest(manifest_for('quanta_navigation'),root)
 rows=n.export_rules();idx=next(i for i,r in enumerate(rows) if r.get('name')==TARGET and r.get('active',True))
 original=copy.deepcopy(rows[idx]);from domains.edit_ops import apply_flip_comparison
 fault=apply_flip_comparison(original,TARGET);n.remove_rule(idx);n.add_rule(fault)
 setup_started=time.perf_counter_ns();game,grid=_build_world(s,n,case);setup_ns=time.perf_counter_ns()-setup_started
 return {'substrate':s,'native':n,'game':game,'grid':grid,'setup_ns':setup_ns,
  'fingerprint':_primary_fingerprint(s,n)}

def _preflight_worlds():
 rows=[]
 for case in CASES:
  primary=_make_primary(case);s=primary['substrate']
  quanta=[s.node(node)['attrs'] for node in s.nodes('SpaceQuantum')]
  if not quanta:raise RuntimeError(f"{case['case']}: quantizer created no SpaceQuantum nodes")
  rows.append({'case':case['case'],'space_quanta':len(quanta),
   'wall_cells':sum(1 for row in primary['grid'] for cell in row if cell=='#'),
   'setup_ns':primary['setup_ns'],'ran_navigation_outcomes':False})
 return rows

def score_candidate(primary,candidate,case):
 s=primary['substrate'];n=primary['native'];fingerprint=primary['fingerprint']
 branch_started=time.perf_counter_ns();branch=s.fork_full_copy_experiment();branch_ns=time.perf_counter_ns()-branch_started
 bn=branch._inner
 rules=candidate.get('rules',{});variant=rules.get(TARGET)
 patch_started=time.perf_counter_ns()
 replaced=bool(variant and bn.replace_active_rule_by_name(TARGET,variant))
 patch_ns=time.perf_counter_ns()-patch_started
 result=_run_prebuilt_case(branch,bn,primary['game'],primary['grid'],case)
 active=next((r for r in bn.export_rules() if r.get('name')==(variant or {}).get('name') and r.get('active',True)),None)
 receipt=bool(replaced and active and _receipt_equal(active,variant))
 primary_preserved=_primary_fingerprint(s,n)==fingerprint
 return {**result,'receipt_verified':receipt,'primary_preserved':primary_preserved,
  'replaced':replaced,'candidate_label':candidate.get('label'),
  'candidate_semantic_digest':semantic_digest(candidate),
  'branch_creation_ns':branch_ns,'candidate_patch_ns':patch_ns,
  'common_case_setup_ns':primary['setup_ns']}

def score_worker(payload):
 before=frozen();worker=int(payload['worker']);outcomes=[]
 primaries={case['case']:_make_primary(case) for case in CASES};by_sem={}
 for c in payload['host_candidates']:
  rows=[score_candidate(primaries[case['case']],c,case) for case in CASES]
  outcome={'label':c['label'],'semantic_digest':semantic_digest(c),'cases':rows,
   'utility':all(x['passed'] and x['receipt_verified'] and x['primary_preserved'] for x in rows),
   'cost_ns':sum(x['closure_work'] for x in rows)}
  outcomes.append(outcome);by_sem[outcome['semantic_digest']]=outcome
 graph=payload['prompted']['candidate'];graph_out=None
 if graph:
  sem=semantic_digest(graph)
  if sem in by_sem:graph_out={'outcome':by_sem[sem],'semantic_digest_match':True,
   'reused_host_candidate_label':by_sem[sem]['label']}
  else:
   rows=[score_candidate(primaries[case['case']],graph,case) for case in CASES]
   graph_out={'outcome':{'label':graph['label'],'semantic_digest':sem,'cases':rows,
    'utility':all(x['passed'] and x['receipt_verified'] and x['primary_preserved'] for x in rows)},
    'semantic_digest_match':False,'reused_host_candidate_label':None}
 source={'label':'source_rule','rules':{TARGET:payload['source_rule']}}
 fault={'label':'fault_rule','rules':{TARGET:payload['fault_rule']}}
 controls={name:[score_candidate(primaries[case['case']],c,case) for case in CASES] for name,c in (('source',source),('fault',fault))}
 after=frozen()
 if before!=after:raise RuntimeError('source drift during quanta-route scoring')
 return {'worker':worker,'source_before':before,'source_after':after,'source_stable':before==after,
  'host_outcomes':outcomes,'graph_outcome':graph_out,
  'source_control':controls['source'],'fault_control':controls['fault']}

def main():
 if sys.argv[1:2]==['--order-worker']:
  print(json.dumps(order_worker(int(sys.argv[2])),sort_keys=True,separators=(',',':')));return 0
 if sys.argv[1:2]==['--score-worker']:
  print(json.dumps(score_worker(json.load(sys.stdin)),sort_keys=True,separators=(',',':')));return 0
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('stale native engine: '+'; '.join(stale))
 if sys.argv[1:]==['--lock']:
  if any(p.exists() for p in (LOCK,ORDERS,SCORES)):raise SystemExit('refusing to overwrite existing capture')
  preflight=_preflight_worlds()
  receipt_controls=_receipt_controls()
  LOCK.write_text(json.dumps({'schema':'ThoughtexperimentA8QuantaRouteTransferV1_2Lock',
   'sources':frozen(),'semantic_engine':rust_source_fingerprint(str(ROOT)),
   'preflight_worlds':preflight,'receipt_controls':receipt_controls,
   'workers':WORKERS,'target':TARGET,'cases':CASES,'prompt_residual':PROMPT,
   'unprompted_residual':COMMON,'candidate_policy':'all host candidates; graph proposal by semantic digest or separate branch'},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
 if not LOCK.exists():raise SystemExit('missing source lock')
 lock=json.loads(LOCK.read_text());before=frozen()
 if before!=lock['sources']:raise SystemExit('source drift from quanta-route lock')
 env={**os.environ,'PYTHONPATH':f'{ROOT / "runners/dsl/python"}:{ROOT}:{ROOT / "evaluation/substrate_capability"}'}
 if sys.argv[1:]==['--orders']:
  if ORDERS.exists() or SCORES.exists():raise SystemExit('orders or scores already exist')
  rows=[]
  for worker in range(WORKERS):
   proc=subprocess.run([sys.executable,str(RUNNER),'--order-worker',str(worker)],cwd=ROOT,env=env,text=True,capture_output=True)
   if proc.returncode:raise RuntimeError(f'order worker {worker}: {proc.stderr[-4000:]}')
   rows.append(json.loads(proc.stdout.strip().splitlines()[-1]))
  after=frozen()
  if before!=after:raise SystemExit('source drift during order capture')
  ORDERS.write_text(json.dumps({'schema':'ThoughtexperimentA8QuantaRouteTransferV1_2Orders',
   'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
   'host':{'platform':platform.platform(),'machine':platform.machine(),'python':sys.version.split()[0]},
   'lock':lock,'source_before':before,'source_after':after,
   'semantic_engine':rust_source_fingerprint(str(ROOT)),'workers':rows},indent=2,sort_keys=True)+'\n')
  print(json.dumps({'stage':'orders_frozen','workers':len(rows),'orders':ORDERS.relative_to(ROOT).as_posix()}));return 0
 if sys.argv[1:]==['--score']:
  if not ORDERS.exists() or SCORES.exists():raise SystemExit('missing orders or score capture exists')
  doc=json.loads(ORDERS.read_text());rows=[]
  for payload in doc['workers']:
   p=payload['prompted'];n=payload['unprompted']
   if p.get('served_by')!='graph' or not p.get('built') or p.get('kind')!='flip_comparison' or p.get('target')!=TARGET or not p.get('target_rule_preserved'):
    raise SystemExit(f"refusing score: worker {payload['worker']} prompted graph target gate failed")
   if n.get('served_by')!='graph' or n.get('built') or n.get('candidate') is not None:
    raise SystemExit(f"refusing score: worker {payload['worker']} no-cue abstention gate failed")
   proc=subprocess.run([sys.executable,str(RUNNER),'--score-worker'],input=json.dumps(payload),cwd=ROOT,env=env,text=True,capture_output=True)
   if proc.returncode:raise RuntimeError(f"score worker {payload['worker']}: {proc.stderr[-4000:]}")
   rows.append(json.loads(proc.stdout.strip().splitlines()[-1]))
  after=frozen()
  if before!=after:raise SystemExit('source drift during score capture')
  SCORES.write_text(json.dumps({'schema':'ThoughtexperimentA8QuantaRouteTransferV1_2Scores',
   'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'orders_sha256':sha(ORDERS),
   'source_before':before,'source_after':after,'workers':rows},indent=2,sort_keys=True)+'\n')
  print(json.dumps({'stage':'heldout_scored','workers':len(rows),'scores':SCORES.relative_to(ROOT).as_posix()}));return 0
 raise SystemExit('choose --lock, --orders, or --score')

if __name__=='__main__':raise SystemExit(main())
