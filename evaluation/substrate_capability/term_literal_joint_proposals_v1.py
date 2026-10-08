#!/usr/bin/env python3
"""Measure joint literal-boundary proposals on the locked adversarial family."""
import hashlib,itertools,json,platform,struct,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'evaluation/substrate_capability'),str(ROOT/'runners/dsl/python'),str(ROOT)]
RUN=Path(__file__).resolve();PRE=ROOT/'docs/research/engine_substrate/TERM_LITERAL_JOINT_PROPOSALS_V1_PREREG_20261004.md';AN=ROOT/'evaluation/substrate_capability/analyze_term_literal_joint_proposals_v1.py'
FAMILY=ROOT/'evaluation/substrate_capability/term_literal_adversarial_family_v1.py';FLOCK=ROOT/'evaluation/substrate_capability/term_literal_adversarial_family_v1_lock_20261004.json';FRAW=ROOT/'evaluation/reports/term_literal_adversarial_family_v1_20261004.json';FAN=ROOT/'evaluation/reports/term_literal_adversarial_family_v1_analysis_20261004.json'
LOCK=ROOT/'evaluation/substrate_capability/term_literal_joint_proposals_v1_lock_20261004.json';OUT=ROOT/'evaluation/reports/term_literal_joint_proposals_v1_20261004.json';CAP=8;JOINT_CAP=64;KEYS=('ax','ay','ex','ey')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def fpkey(row):return tuple(struct.pack('>d',float(x)) for x in row)
def source_map():
 from substrate_rs import _native
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 if build_is_stale(str(ROOT)):raise RuntimeError('stale native build')
 ps=[RUN,PRE,AN,FAMILY,FLOCK,FRAW,FAN,ROOT/'evaluation/substrate_capability/term_literal_probe_repair_v1.py',ROOT/'domains/contract_query.py']
 b=Path(_native.__file__).resolve()
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in ps},'native':{'path':str(b),'sha256':sha(b)},'rust_fingerprint':rust_source_fingerprint(str(ROOT)),'python':sys.version,'platform':platform.platform()}
def joint_rows(panel,existing):
 import term_literal_probe_repair_v1 as h
 names=sorted(set().union(*(set(h.term_vars(z['term'])) for z in panel['terms'])));bounds={}
 for z in panel['terms']:
  for var,value in h.literal_bounds(z['term']):bounds.setdefault(var,set()).add(float(value))
 vars_=[v for v in names if bounds.get(v)]
 if len(vars_)<2:return []
 count=1
 for v in vars_:count*=len(bounds[v])
 if count>JOINT_CAP:raise RuntimeError(f'joint proposal cap exceeded: {count}>{JOINT_CAP}')
 forbidden=[z['row'] for z in panel['training']]+panel['prior_pool']+panel['holdout'];denied={fpkey(r) for r in forbidden}|{fpkey(r) for r in existing};rows=[]
 for values in itertools.product(*(sorted(bounds[v]) for v in vars_)):
  env={k:0. for k in KEYS};env.update(dict(zip(vars_,values)));row=[env[k] for k in KEYS]
  if fpkey(row) not in denied and fpkey(row) not in {fpkey(z) for z in rows}:rows.append(row)
 return rows
def arm(p,policy_name,probe_rows):
 import term_literal_probe_repair_v1 as h
 from substrate_rs import _native
 from adaptive_factored_operator_search_v1 import classify
 n=_native.Substrate();q=h.policy(n,p,probe_rows);scores=[]
 for z in p['terms']:
  bad=invalid=0
  for row in p['holdout']:
   pred=classify(n.evaluate(z['term'],dict(zip(KEYS,row))));truth=bool(h.truth(p['task'],row))
   if pred is None:invalid+=1
   elif pred is not truth:bad+=1
  scores.append({'id':z['id'],'n':len(p['holdout']),'mismatches':bad,'invalid':invalid})
 return {'policy':policy_name,'probe_rows':probe_rows,'prior_partition':q['prior_partition'],'events':q['events'],'survivor_ids':q['survivor_ids'],'final_partition':q['final_partition'],'decision':q['decision'],'native_evaluations':q['native_evaluations'],'wall_ns':q['wall_ns'],'cpu_ns':q['cpu_ns'],'holdout_scores':scores}
def run_panel(p):
 import term_literal_probe_repair_v1 as h
 start=time.perf_counter_ns();cpu=time.process_time_ns();edge,literals=h.probe_slates(p);proposal_ns=time.perf_counter_ns()-start;proposal_cpu=time.process_time_ns()-cpu
 pair_rows=edge+literals
 joint_start=time.perf_counter_ns();joint=joint_rows(p,pair_rows);joint_ns=time.perf_counter_ns()-joint_start
 joint_rows_all=pair_rows+joint
 return {'name':p['name'],'guard_arity':p['guard_arity'],'guard_kind':p['guard_kind'],'pairwise_probe_count':len(pair_rows),'joint_probe_count':len(joint),'proposal_wall_ns':proposal_ns,'joint_generation_wall_ns':joint_ns,'arms':[arm(p,'pairwise_literal',pair_rows),arm(p,'joint_literal',joint_rows_all)]}
def main():
 import term_literal_adversarial_family_v1 as f
 a=sys.argv[1:]
 if a==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  if not json.loads(FAN.read_text()).get('passed'):raise SystemExit('upstream adversarial evidence invalid')
  ps=f.panels();LOCK.write_text(json.dumps({'schema':'TermLiteralJointProposalsV1Lock','sources':source_map(),'family_lock_sha256':sha(FLOCK),'family_capture_sha256':sha(FRAW),'panel_sha256':{p['name']:hashlib.sha256(canon(p)).hexdigest() for p in ps},'policy':{'label_cap':CAP,'joint_proposal_cap':JOINT_CAP}},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if a==['--run']:
  lock=json.loads(LOCK.read_text());ps=f.panels()
  if source_map()!=lock['sources'] or sha(FRAW)!=lock['family_capture_sha256'] or {p['name']:hashlib.sha256(canon(p)).hexdigest() for p in ps}!=lock['panel_sha256']:raise SystemExit('source/panel drift')
  workers=[run_panel(p) for p in ps]
  if source_map()!=lock['sources']:raise SystemExit('source drift during capture')
  OUT.write_text(json.dumps({'schema':'TermLiteralJointProposalsV1Results','lock_sha256':sha(LOCK),'sources':source_map(),'workers':workers,'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
 raise SystemExit('usage --lock | --run')
if __name__=='__main__':raise SystemExit(main())
