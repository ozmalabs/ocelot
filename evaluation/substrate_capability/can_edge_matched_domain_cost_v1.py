#!/usr/bin/env python3
"""Paired exact-inference cost for supported binary and ternary CAN modes."""
from __future__ import annotations
import hashlib,importlib.util,itertools,json,os,platform,resource,subprocess,sys,time,tracemalloc
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
RUNNER=Path(__file__).resolve()
PROTOCOL=ROOT/'docs/research/engine_substrate/CAN_EDGE_MATCHED_DOMAIN_COST_V1_PREREG_20261002.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_can_edge_matched_domain_cost_v1.py'
BASE=ROOT/'evaluation/substrate_capability/can_edge_matched_inference_cost_v1_3.py'
BASE_PROTOCOL=ROOT/'docs/research/engine_substrate/CAN_EDGE_MATCHED_INFERENCE_COST_V1_3_PREREG_20261002.md'
GENERATOR=ROOT/'evaluation/substrate_capability/can_edge_matched_width_topology_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/can_edge_matched_domain_cost_v1_lock_20261002.json'
OUT=ROOT/'evaluation/reports/can_edge_matched_domain_cost_v1_20261002.json'
WIDTHS=(4,5,6);FAMILIES=('grid','sparse_partial_qtree');MODES={'2state':(-1.0,1.0),'3state':(-1.0,0.0,1.0)};N=120;REPLICATES=3;TOL=1e-8
def digest(path):
 raw=path.read_bytes();return {'path':path.relative_to(ROOT).as_posix(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def load_base():
 spec=importlib.util.spec_from_file_location('can_domain_cost_base',BASE);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m
def source_lock():
 from substrate_rs import _native
 return {'runner':digest(RUNNER),'protocol':digest(PROTOCOL),'analyzer':digest(ANALYZER),'base_runner':digest(BASE),
  'base_protocol':digest(BASE_PROTOCOL),'generator':digest(GENERATOR),'solver_sources':[digest(ROOT/p) for p in ('domains/can_junction_tree.py','domains/graph_treewidth.py')],
  'native_binary':digest(Path(_native.__file__).resolve()),'native_build_manifest':digest(ROOT/'runners/dsl/python/substrate_rs/_native.build.json'),
  'nodes':N,'widths':list(WIDTHS),'families':list(FAMILIES),'modes':{k:list(v) for k,v in MODES.items()},'replicates':REPLICATES,'tolerance':TOL}
def oracle_ve(order,unary,pair,vocab):
 factors=[];operations=0
 for v,h in unary.items():factors.append(((v,),{(x,):-float(h)*float(x) for x in vocab}))
 for (a,b),w in pair.items():factors.append(((a,b),{(x,y):-float(w)*float(x)*float(y) for x in vocab for y in vocab}))
 for v in order:
  bucket=[f for f in factors if v in f[0]];factors=[f for f in factors if v not in f[0]]
  scope=tuple(sorted({x for s,_ in bucket for x in s}));rest=tuple(x for x in scope if x!=v);table={}
  for values in itertools.product(vocab,repeat=len(rest)):
   ctx=dict(zip(rest,values));best=float('inf')
   for x in vocab:
    ctx[v]=x;score=0.0
    for fs,ft in bucket:score+=ft[tuple(ctx[y] for y in fs)]
    operations+=len(bucket);best=min(best,score)
   table[values]=best
  factors.append((rest,table))
 energy=0.0
 for scope,table in factors:
  if scope:raise AssertionError('oracle left nonconstant factor')
  energy+=table[()]
 return energy,operations
def direct_energy(state,unary,pair):
 return -sum(float(h)*float(state[i]) for i,h in unary.items())-sum(float(w)*float(state[a])*float(state[b]) for (a,b),w in pair.items())
def worker(q,family,rep,mode):
 import substrate_rs as sr
 import domains.can_junction_tree as cjt
 from domains.graph_treewidth import min_fill_upper_bound,build_elimination_triangulation
 base=load_base();vocab=MODES[mode];base.VOCAB=vocab
 seed,nodes,edges,cert,unary,pair,expected_edges=base.fixture(q,family,rep)
 t=time.perf_counter_ns();s=sr.Substrate();inner=s._inner;mt=inner.add_node('Microtheory',{'discrete_mode':mode})
 handles={i:inner.add_node('Concept',{'name':f'x{i}','external_field':unary[i],'identity_field':0.0,'state':0.0}) for i in nodes}
 for node in handles.values():inner.add_edge_unchecked(mt,'has_concept',node,{})
 for (a,b),w in pair.items():
  inner.add_edge_unchecked(handles[a],'causal_influence',handles[b],{'weight':w});inner.add_edge_unchecked(handles[b],'causal_influence',handles[a],{'weight':w})
 construct_ns=time.perf_counter_ns()-t
 t=time.perf_counter_ns();net=cjt.can_network_from_mt(s,mt);extract_ns=time.perf_counter_ns()-t
 actual_to_fixture={h.value:i for i,h in handles.items()};actual_unary={actual_to_fixture[i]:v for i,v in net['unary'].items()}
 actual_pair={tuple(sorted(actual_to_fixture[i] for i in edge)):v for edge,v in net['pairwise'].items()}
 extraction_exact=actual_unary==unary and actual_pair==pair and tuple(net['vocab'])==vocab
 ids=list(net['nodes']);graph_edges=[tuple(x) for x in net['edges']];engine_unary=dict(net['unary']);engine_pair=dict(net['pairwise'])
 cert_native=[handles[i].value for i in cert]
 t=time.perf_counter_ns();mf=min_fill_upper_bound(ids,graph_edges);mf_ns=time.perf_counter_ns()-t
 cert_tri=build_elimination_triangulation(ids,graph_edges,cert_native);cert_width=max((len(b)-1 for b in cert_tri['bags'].values()),default=0)
 t=time.perf_counter_ns();oracle,oracle_ops=oracle_ve(cert,unary,pair,vocab);oracle_ns=time.perf_counter_ns()-t
 state_before={i:float(inner.node(handles[i])['attrs'].get('state',0)) for i in nodes}
 def timed(order):
  tracemalloc.start();t=time.perf_counter_ns();cpu=time.process_time_ns()
  result=cjt.junction_tree_map(ids,graph_edges,engine_unary,engine_pair,vocab,order=order)
  cpu_ns=time.process_time_ns()-cpu;wall=time.perf_counter_ns()-t;_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
  energy=direct_energy({actual_to_fixture[i]:v for i,v in result['state'].items()},unary,pair)
  return result,wall,cpu_ns,peak,energy
 mfres,mf_wall,mf_cpu,mf_peak,mf_direct=timed(mf['elimination_order']);certres,cert_wall,cert_cpu,cert_peak,cert_direct=timed(cert_native)
 state_after={i:float(inner.node(handles[i])['attrs'].get('state',0)) for i in nodes}
 return {'width':q,'family':family,'replicate':rep,'mode':mode,'vocabulary':list(vocab),'seed':seed,'worker_pid':os.getpid(),
  'nodes':len(ids),'edges':len(graph_edges),'expected_edges':expected_edges,'extraction_exact':extraction_exact,
  'certificate_width':cert_width,'minfill_width':mf['treewidth'],'oracle_energy':oracle,'minfill_energy':float(mfres['energy']),
  'certificate_energy':float(certres['energy']),'minfill_direct_energy':mf_direct,'certificate_direct_energy':cert_direct,
  'oracle_operations':oracle_ops,'no_mutation':state_before==state_after,
  'timing_ns':{'graph_construction':construct_ns,'runtime_extraction':extract_ns,'minfill_order':mf_ns,'oracle':oracle_ns,
   'jt_minfill_wall':mf_wall,'jt_minfill_cpu':mf_cpu,'jt_certificate_wall':cert_wall,'jt_certificate_cpu':cert_cpu},
  'traced_peak_bytes':{'jt_minfill':mf_peak,'jt_certificate':cert_peak},'process_peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
def main():
 args=sys.argv[1:]
 if args[:1]==['--worker']:
  print(json.dumps(worker(int(args[1]),args[2],int(args[3]),args[4]),sort_keys=True,separators=(',',':')));return 0
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite lock/capture')
  LOCK.write_text(json.dumps({'schema':'CanEdgeMatchedDomainCostV1Lock','sources':source_lock()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock, --run, or --worker Q FAMILY REP MODE')
 lock=json.loads(LOCK.read_text())
 if source_lock()!=lock['sources']:raise SystemExit('source/input drift from lock')
 from domains.engine_provenance import build_is_stale
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('native engine stale: '+'; '.join(stale))
 env={**os.environ,'PYTHONPATH':f"{ROOT/'runners/dsl/python'}:{ROOT}:{os.environ.get('PYTHONPATH','')}"};rows=[]
 for q in WIDTHS:
  for rep in range(REPLICATES):
   for family in FAMILIES:
    for mode in MODES:
     p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(q),family,str(rep),mode],cwd=ROOT,env=env,text=True,capture_output=True,timeout=600)
     if p.returncode:raise RuntimeError(f'q={q} {family} rep={rep} mode={mode}: {p.stderr[-3000:]}')
     row=json.loads(p.stdout.strip());rows.append(row)
     print(f"q={q} {family} rep={rep} mode={mode} JTcert={row['timing_ns']['jt_certificate_wall']/1e6:.2f}ms",flush=True)
 post=source_lock();cells=[(q,f,m) for q in WIDTHS for f in FAMILIES for m in MODES]
 checks={'worker_count':len(rows)==36,'fresh_worker_pids':len({r['worker_pid'] for r in rows})==36,
  'complete_paired_cells':all(sum((r['width'],r['family'],r['mode'])==(q,f,m) for r in rows)==REPLICATES for q,f,m in cells),
  'same_fixture_across_modes':all(len({(r['nodes'],r['edges'],r['seed']) for r in rows if (r['width'],r['family'],r['replicate'])==(q,f,rep)})==1 for q in WIDTHS for f in FAMILIES for rep in range(REPLICATES)),
  'edge_counts':all(r['nodes']==N and r['edges']==r['expected_edges'] for r in rows),
  'domain_matches_mode':all(r['vocabulary']==list(MODES[r['mode']]) and len(r['vocabulary'])==({'2state':2,'3state':3}[r['mode']]) for r in rows),
  'exact_extraction':all(r['extraction_exact'] for r in rows),'certificate_width_q':all(r['certificate_width']==r['width'] for r in rows),
  'oracle_parity':all(abs(r[k]-r['oracle_energy'])<TOL for r in rows for k in ('minfill_energy','certificate_energy','minfill_direct_energy','certificate_direct_energy')),
  'no_mutation':all(r['no_mutation'] for r in rows),'pre_post_source_match':post==lock['sources']}
 OUT.write_text(json.dumps({'schema':'CanEdgeMatchedDomainCostV1Results','lock_sha256':hashlib.sha256(LOCK.read_bytes()).hexdigest(),
  'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),'sources':source_lock(),'post_run_sources':post,
  'configuration':{'nodes':N,'widths':WIDTHS,'families':FAMILIES,'modes':{k:MODES[k] for k in MODES},'replicates':REPLICATES},
  'claim_boundary':'paired exact MAP domain-cardinality cost at q<=6 on two synthetic binary pairwise graph families; no natural domain or topology prevalence estimate',
  'checks':checks,'runs':rows},indent=2,sort_keys=True)+'\n')
 print(json.dumps({'capture':OUT.relative_to(ROOT).as_posix(),'checks':checks},indent=2))
 if not all(checks.values()):raise SystemExit('domain cost inference gate failed')
if __name__=='__main__':main()
