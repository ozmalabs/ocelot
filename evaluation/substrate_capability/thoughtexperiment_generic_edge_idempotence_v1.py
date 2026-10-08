#!/usr/bin/env python3
"""Generate generic edge-idempotence edits and select by graph-resident evidence."""
from __future__ import annotations
import copy,hashlib,json,os,platform,random,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'evaluation/substrate_capability')]
RUNNER=Path(__file__).resolve()
PREREG=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_GENERIC_EDGE_IDEMPOTENCE_V1_PREREG_20261002.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_generic_edge_idempotence_v1.py'
INTEGRATION=ROOT/'evaluation/substrate_capability/thoughtexperiment_recurrence_compose_and_select_v1.py'
INTEGRATION_RESULTS=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_RECURRENCE_COMPOSE_AND_SELECT_V1_1_RESULTS_20261002.md'
PREV_RESULTS=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_RECURRENCE_GENERAL_STRUCTURAL_PROPOSAL_V1_1_RESULTS_20261002.md'
SOURCES=('domains/contract_query.py','domains/reflective_faculty.py','domains/edit_ops.py','domains/engine_provenance.py',
 'substrate/boot_core.py','substrate/seed_loader.py','runners/dsl/src/py.rs','runners/dsl/src/substrate.rs',
 'runners/dsl/src/graph.rs','runners/dsl/src/graph_rules.rs','runners/dsl/src/term.rs','runners/dsl/src/persist.rs',
 'runners/dsl/src/grammar.rs','runners/dsl/src/sym.rs','runners/dsl/src/lib.rs','runners/dsl/Cargo.toml','runners/dsl/Cargo.lock',
 'runners/dsl/python/substrate_rs/__init__.py','seeds/minting_recurrence_ledger.json','seeds/relation_vocabulary.json',
 'seeds/composer_dispatch.json','seeds/autonomy.json')
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_generic_edge_idempotence_v1_lock_20261002.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_generic_edge_idempotence_v1_orders_20261002.json'
SCORES=ROOT/'evaluation/reports/thoughtexperiment_generic_edge_idempotence_v1_scores_20261002.json'
WORKERS=4;REPEATS=2;SEED=20261022;TARGET='mrl_offer_due_once'
CUE=['mrl','offer','due','once','guard','constrain','restrict','narrow','extra','condition','equality']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def frozen():
 from substrate_rs import _native
 files=[ROOT/p for p in SOURCES]+[RUNNER,PREREG,ANALYZER,INTEGRATION,INTEGRATION_RESULTS,PREV_RESULTS]
 out={str(p.relative_to(ROOT)):sha(p) for p in files};out['loaded_native_binary']=sha(Path(_native.__file__).resolve());return out
def digest(c):
 row=copy.deepcopy(c['rules'][TARGET]);row.pop('name',None)
 return 'sha256:'+hashlib.sha256(json.dumps({TARGET:row},sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def build_fault(worker,split,sample):
 from substrate.boot_core import boot_core
 from substrate.seed_loader import manifest_for
 sub,agent=boot_core(seeds=());native=sub._inner
 for seed in ('relation_vocabulary','composer_dispatch','autonomy','minting_recurrence_ledger'):
  native.load_seed_manifest(manifest_for(seed),agent)
 rows=native.export_rules();active=[(i,r) for i,r in enumerate(rows) if r.get('name')==TARGET and r.get('active',True)]
 if len(active)!=1:raise RuntimeError('expected exactly one active recurrence target')
 fault=json.loads(json.dumps(active[0][1]));fault['where']['items']=[x for x in fault['where']['items'] if x.get('type')!='Not']
 if not native.remove_rule(active[0][0]):raise RuntimeError('failed to replace target with fault')
 native.add_rule(fault)
 episode=sub.add_node('MintingRecurrenceEpisode',{'mint_after_quanta':1,'integer_native':1,'generator':'generic_edge_idempotence_v1'})
 sub.add_edge(agent,'has_minting_recurrence_episode',episode)
 keys=[f'generic-ei-{worker}-{split}-{sample}-{j}' for j in range(2)]
 def add_due(j):
  key=keys[j];attrs={'predicate':'bind','recurrence_key':key,
   'structural_signature':[['relation','bind','ITEM',f'SLOT{j}',worker]],'capability_key':[key,'X']}
  cand=sub.add_node('PredicateRecurrenceCandidate',attrs)
  ev=sub.add_node('ResidualSegmentEvidence',{**attrs,'segment_ordinal':j,'integer_native':1})
  sub.add_edge(episode,'has_predicate_recurrence_candidate',cand);sub.add_edge(cand,'supported_by_segment',ev)
  return cand
 add_due(0)
 return sub,agent,native,episode,keys,fault,add_due
def generic_guard_candidates(rule):
 bound=set()
 for edge in rule.get('match') or []:
  if isinstance(edge,list) and len(edge)>=3:
   if isinstance(edge[0],str):bound.add(edge[0])
   if isinstance(edge[2],str):bound.add(edge[2])
 sites=[]
 for eff in rule.get('effects') or []:
  if isinstance(eff,list) and len(eff)>=4 and eff[0]=='add_edge' and eff[1] in bound:
   pair=(eff[1],eff[2])
   if pair not in sites:sites.append(pair)
 out=[]
 for i,(var,edge_type) in enumerate(sites):
  guard={'type':'Not','arg':{'type':'Exists','source':{'type':'Neighbours',
   'node':{'type':'Var','name':var},'edge_type':edge_type},'var_name':f'existing_{i}',
   'predicate':{'type':'Lit','value':True}}}
  variant=copy.deepcopy(rule);variant['name']=f'{TARGET}_edge_once_{i}';variant.pop('active',None)
  where=variant.get('where')
  if isinstance(where,dict) and where.get('type')=='And':where.setdefault('items',[]).append(guard)
  elif where:variant['where']={'type':'And','items':[where,guard]}
  else:variant['where']=guard
  out.append({'label':f'edge_once:{var}:{edge_type}','rules':{TARGET:variant}})
 if len(out)!=3:raise RuntimeError(f'expected 3 bound add_edge sites, got {sites!r}')
 return out
def build_pool(worker,split='train',sample=0):
 import domains.reflective_faculty as rf
 sub,agent,native,episode,keys,fault,add_due=build_fault(worker,split,sample)
 primary_rules=native.export_rules()
 generated=generic_guard_candidates(fault)
 key=f'generic_edge_idempotence_{worker}_{split}_{sample}'
 sub.add_node('CapabilityAxis',{'is_axis':1.0,'capability_keys':[key],'induced':1.0,
  'residual_predicates':CUE,'structural_rule_scope':'all_mutable_rules','from_observation':1.0,
  'source':'generic_edge_idempotence_v1'})
 before=time.perf_counter_ns();composition=rf.compose_general_structural_variant(sub,[key],f'generic_ei_{worker}')
 compose_ns=time.perf_counter_ns()-before
 if not composition.get('built'):raise RuntimeError(f"generic composer abstained: {composition.get('wall')}")
 generic={'label':f"composer:{composition['kind']}",'rules':{composition['removed_rule']:composition['rule']}}
 candidates=generated+[generic];descriptors=[{'proposal_id':digest(c),'label':c['label']} for c in candidates]
 if len(descriptors)!=4 or len({x['proposal_id'] for x in descriptors})!=4:raise RuntimeError('expected four unique generic hypotheses')
 return {'sub':sub,'agent':agent,'native':native,'episode':episode,'keys':keys,'fault':fault,'primary_rules':primary_rules,
  'add_due':add_due,'candidates':candidates,'descriptors':descriptors,'compose_ns':compose_ns,
  'composition':{'target':composition.get('removed_rule'),'operator':composition.get('kind'),'site':composition.get('site')}}
def score_episode(worker,split,sample,candidate):
 g=build_fault(worker,split,sample);sub,native,episode,keys,fault,add_due=g[0],g[2],g[3],g[4],g[5],g[6]
 if not native.remove_rule(next(i for i,r in enumerate(native.export_rules()) if r.get('name')==TARGET and r.get('active',True))):
  raise RuntimeError('could not remove fault rule before proposal install')
 native.add_rule(candidate['rules'][TARGET])
 first=[int(native.run_rules(100)) for _ in range(5)]
 add_due(1);second=[int(native.run_rules(100)) for _ in range(5)]
 counts=[]
 for key in keys:
  node=next(n for n in sub.nodes('PredicateRecurrenceCandidate') if sub.node(n)['attrs'].get('recurrence_key')==key)
  counts.append(len(list(sub.neighbours(node,'has_mint_offer'))))
 fixed=int(native.run_rules(100));correct=counts==[1,1] and fixed==0
 return {'correct':correct,'offer_counts':counts,'fixedpoint_progress':fixed,'first_sweeps':first,'second_sweeps':second,'keys':keys}
def orders_worker(worker):
 from domains.contract_query import select_candidate_from_graph_evidence
 before=frozen();pool=build_pool(worker);candidates=pool['candidates'];descriptors=pool['descriptors']
 rng=random.Random(SEED+worker);perm=list(range(4));rng.shuffle(perm)
 candidates=[candidates[i] for i in perm];descriptors=[descriptors[i] for i in perm]
 outcomes=[];evidence=[];train_keys=[];training_ns=0
 for c,d in zip(candidates,descriptors):
  rows=[]
  for sample in range(REPEATS):
   started=time.perf_counter_ns();row=score_episode(worker,f'train_{worker}',sample,c);training_ns+=time.perf_counter_ns()-started
   rows.append({'sample':sample,**row});train_keys.extend(row['keys'])
   evidence.append({'proposal_id':d['proposal_id'],'probe_id':f'train_{worker}_{sample}',
    'predicted':'correct' if row['correct'] else 'incorrect','expected':'correct'})
  outcomes.append({'proposal_id':d['proposal_id'],'label':d['label'],'rows':rows})
 branch=pool['sub'].snapshot().fork();start=time.perf_counter_ns()
 decision=select_candidate_from_graph_evidence(branch,f'generic_edge_ei_{worker}',
  [{'proposal_id':d['proposal_id'],'proposal_label':'hypothesis'} for d in descriptors],evidence)
 selector_ns=time.perf_counter_ns()-start;decision.pop('proposal_node',None)
 label=next((d['label'] for d in descriptors if d['proposal_id']==decision.get('proposal_id')),None)
 controls={}
 for name,value in (('all_wrong','incorrect'),('tie','correct')):
  cb=pool['sub'].snapshot().fork();ev=[{'proposal_id':d['proposal_id'],'probe_id':f'{name}_{i}',
    'predicted':value,'expected':'correct'} for d in descriptors for i in range(REPEATS)]
  x=select_candidate_from_graph_evidence(cb,f'generic_edge_ei_{name}_{worker}',
   [{'proposal_id':d['proposal_id'],'proposal_label':'hypothesis'} for d in descriptors],ev);x.pop('proposal_node',None);controls[name]=x
 after=frozen()
 return {'worker':worker,'descriptors':descriptors,'selector_proposals':[{'proposal_id':d['proposal_id'],'proposal_label':'hypothesis'} for d in descriptors],
  'training_evidence':evidence,'outcomes':outcomes,'training_keys':train_keys,'decision':decision,'selected_label':label,
  'controls':controls,'candidate_order':perm,'composition':pool['composition'],'compose_ns':pool['compose_ns'],
  'training_scoring_ns':training_ns,'selector_ns':selector_ns,
  'branch_isolated':not pool['sub'].nodes('CandidateProposal') and not pool['sub'].nodes('CandidateEvidence'),
  'primary_rule_unchanged':pool['native'].export_rules()==pool['primary_rules'],
  'source_before':before,'source_after':after,'source_stable':before==after}
def score_worker(order):
 before=frozen();worker=int(order['worker']);pool=build_pool(worker,'heldout',0)
 perm=order['candidate_order'];candidates=[pool['candidates'][i] for i in perm]
 descriptors=[pool['descriptors'][i] for i in perm]
 if descriptors!=order['descriptors']:raise RuntimeError('heldout proposal descriptors differ from frozen order')
 selected=next((c for c in candidates if digest(c)==order['decision'].get('proposal_id')),None)
 if selected is None:raise RuntimeError('frozen winner not regenerated')
 rows=[]
 for sample in range(REPEATS):rows.append(score_episode(worker,f'heldout_{worker}',sample,selected))
 after=frozen()
 return {'worker':worker,'selected_digest':order['decision'].get('proposal_id'),'selected_label':order['selected_label'],
  'heldout_rows':rows,'source_before':before,'source_after':after,'source_stable':before==after}
def main():
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('stale native engine: '+'; '.join(stale))
 env={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}:{ROOT}/evaluation/substrate_capability'};args=sys.argv[1:]
 if args[:1]==['--orders-worker']:
  print(json.dumps(orders_worker(int(args[1])),sort_keys=True,separators=(',',':')));return 0
 if args[:1]==['--score-worker']:
  print(json.dumps(score_worker(json.load(sys.stdin)),sort_keys=True,separators=(',',':')));return 0
 if args==['--lock']:
  if any(p.exists() for p in (LOCK,ORDERS,SCORES)):raise SystemExit('refusing to overwrite')
  LOCK.write_text(json.dumps({'schema':'ThoughtexperimentGenericEdgeIdempotenceV1Lock','sources':frozen(),
   'semantic_engine':rust_source_fingerprint(str(ROOT)),'workers':WORKERS,'repeats':REPEATS,'seed':SEED,
   'target':TARGET,'generated_candidate_count':3,'candidate_count':4,'positive_candidate_not_supplied':True,
   'selector':'select_candidate_from_graph_evidence','cue':CUE},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
 if args==['--orders']:
  if not LOCK.exists() or ORDERS.exists() or SCORES.exists():raise SystemExit('missing lock or captures exist')
  lock=json.loads(LOCK.read_text());before=frozen()
  if before!=lock['sources']:raise SystemExit('source drift from lock')
  ws=[]
  for i in range(WORKERS):
   p=subprocess.run([sys.executable,str(RUNNER),'--orders-worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=90)
   if p.returncode:raise RuntimeError(f'worker {i}: {p.stderr[-3000:]}')
   ws.append(json.loads(p.stdout.strip().splitlines()[-1]))
  if frozen()!=before:raise SystemExit('source drift during order capture')
  ORDERS.write_text(json.dumps({'schema':'ThoughtexperimentGenericEdgeIdempotenceV1Orders','lock_sha256':sha(LOCK),
   'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),'workers':ws},indent=2,sort_keys=True)+'\n')
  print(ORDERS.relative_to(ROOT));return 0
 if args==['--scores']:
  if not ORDERS.exists() or SCORES.exists():raise SystemExit('orders missing or scores exist')
  lock=json.loads(LOCK.read_text());before=frozen()
  if before!=lock['sources']:raise SystemExit('source drift from lock')
  ws=[]
  for order in json.loads(ORDERS.read_text())['workers']:
   p=subprocess.run([sys.executable,str(RUNNER),'--score-worker'],input=json.dumps(order),cwd=ROOT,env=env,text=True,capture_output=True,timeout=90)
   if p.returncode:raise RuntimeError(f"score worker {order['worker']}: {p.stderr[-3000:]}")
   ws.append(json.loads(p.stdout.strip().splitlines()[-1]))
  if frozen()!=before:raise SystemExit('source drift during scoring')
  SCORES.write_text(json.dumps({'schema':'ThoughtexperimentGenericEdgeIdempotenceV1Scores','lock_sha256':sha(LOCK),
   'orders_sha256':sha(ORDERS),'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'workers':ws},indent=2,sort_keys=True)+'\n')
  print(SCORES.relative_to(ROOT));return 0
 raise SystemExit('use --lock, --orders, or --scores')
if __name__=='__main__':raise SystemExit(main())
