#!/usr/bin/env python3
"""Measure malformed Term rollback and seed-reflex AST retention."""
from __future__ import annotations
import hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
os.environ.setdefault('OZMA_NO_LLM','1'); os.environ.setdefault('OZMA_SEED_PERSIST_DISABLED','1')
import substrate_rs as srs
PREREG=ROOT/'docs/research/engine_substrate/SUBSTRATE_TERM_ARENA_ROLLBACK_EDGECASES_V1_1_AMENDMENT_20260925.md'
LOCK=ROOT/'evaluation/substrate_capability/term_arena_rollback_edgecases_v1_1_lock_20260925.json'
TERM={'type':'Cat','items':[{'type':'Lit','value':'left'},{'type':'Reverse','seq':{'type':'Var','name':'x'}}]}
BAD={'type':'Cat','items':[{'type':'Lit','value':'prefix'},{'type':'NoSuchVariant'}]}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fp(sub): return hashlib.sha256(json.dumps(sub.graph_to_dict(),sort_keys=True,separators=(',',':')).encode()).hexdigest()
def manifest(reflex): return {'id':'arena-rollback-probe','version':1,'nodes':[],'edges':[],'productions':[],'reflexes':[reflex]}
def main():
 if len(sys.argv)!=2: raise SystemExit('usage: substrate_term_arena_rollback_edgecases.py OUTPUT.json')
 native=Path(srs._native.__file__).resolve(); lock=json.loads(LOCK.read_text())
 expected={'preregistration_sha256':sha(PREREG),'runner_sha256':sha(__file__),'native_sha256':sha(native),'adapter_sha256':sha(ROOT/'runners/dsl/python/substrate_rs/__init__.py')}
 if any(lock.get(k)!=v for k,v in expected.items()): raise SystemExit('edgecase probe lock mismatch')
 stale=subprocess.check_output([sys.executable,'-c',"from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')))" ],cwd=ROOT,text=True).strip()
 if stale: raise SystemExit('native build stale:\n'+stale)
 sub=srs.Substrate(); arena0=sub._inner.term_arena_len(); graph0=fp(sub); direct_error=None
 try: sub._inner.add_term_subgraph(BAD)
 except ValueError as exc: direct_error=str(exc)
 direct={'error':direct_error,'arena_before':arena0,'arena_after':sub._inner.term_arena_len(),'graph_unchanged':graph0==fp(sub)}
 direct['passed']=direct['error'] is not None and direct['arena_before']==direct['arena_after'] and direct['graph_unchanged']
 bad_reflex={'name':'bad_reflex','response':'noop','stimulus':BAD}
 bad_before=fp(sub); bad_arena=sub._inner.term_arena_len(); bad_summary=sub.load_seed_manifest(manifest(bad_reflex))
 bad={'summary':bad_summary,'arena_before':bad_arena,'arena_after':sub._inner.term_arena_len(),'graph_unchanged':bad_before==fp(sub)}
 bad['passed']=bad_summary.get('reflexes')==0 and len(bad_summary.get('reflexes_skipped',[]))==1 and bad['arena_before']==bad['arena_after'] and bad['graph_unchanged']
 good_reflex={'name':'good_reflex','response':'answer','refractory_ticks':3,'stimulus':TERM}
 good_arena=sub._inner.term_arena_len(); good_summary=sub.load_seed_manifest(manifest(good_reflex))
 graph=sub.graph_to_dict(); reflex_nodes=[n for n in graph['nodes'] if n['type']=='Reflex']
 stim_root=None; readback=None
 if reflex_nodes:
  targets=sub.neighbours(srs.NodeID(int(reflex_nodes[0]['id'])),'stimulus_term')
  if len(targets)==1:
   stim_root=targets[0]; readback=json.loads(sub._inner.term_subgraph_json(stim_root))
 good={'summary':good_summary,'arena_before':good_arena,'arena_after':sub._inner.term_arena_len(),'reflex_nodes':len(reflex_nodes),'stimulus_root_found':stim_root is not None,'readback_matches':readback==TERM}
 good['passed']=good_summary.get('reflexes')==1 and good['arena_before']==good['arena_after'] and len(reflex_nodes)==1 and stim_root is not None and readback==TERM
 cases={'direct_malformed_partial_parse':direct,'malformed_seed_reflex':bad,'valid_seed_reflex':good}
 payload={'schema_version':1,'run_id':'term-arena-rollback-edgecases-20260925-v1.1','cases':cases,'all_cases_pass':all(v['passed'] for v in cases.values()),'provenance':{**expected,'lock_sha256':sha(LOCK),'build_record_sha256':sha(native.with_name('_native.build.json')),'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()},'native_path':str(native),'claim_boundary':'fixed parser/reflex edge cases; no broad persistence or memory claim'}
 out=Path(sys.argv[1]); out=out if out.is_absolute() else ROOT/out; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'all_cases_pass':payload['all_cases_pass'],'output':str(out)})); return 0 if payload['all_cases_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
