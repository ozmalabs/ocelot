#!/usr/bin/env python3
"""Measure node_deleted hook behavior during ownership-aware Term cleanup."""
from __future__ import annotations
import hashlib, json, os, platform, subprocess, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'runners/dsl/python')]
os.environ.setdefault('OZMA_NO_LLM', '1')
os.environ.setdefault('OZMA_SEED_PERSIST_DISABLED', '1')
import substrate_rs as srs
PREREG = ROOT / 'docs/research/engine_substrate/SUBSTRATE_TERM_CLEANUP_HOOKS_PREREG_20260925.md'
LOCK = ROOT / 'evaluation/substrate_capability/term_cleanup_hooks_lock_20260925.json'
TERM = {'type':'Cat','items':[{'type':'Lit','value':'left'}, {'type':'Reverse','seq':{'type':'Var','name':'x'}}]}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def nodes(sub):
    return [(int(n['id']),n['type']) for n in sub.graph_to_dict()['nodes']]
def setup(shared_leaf=False):
    sub=srs.Substrate(); root=sub._inner.add_term_subgraph(TERM)
    ts=[(i,t) for i,t in nodes(sub) if t.startswith('Term.')]
    leaf=next(i for i,t in ts if t=='Term.Var')
    owner=None
    if shared_leaf:
        owner=sub.add_node('TermOwner',{})
        sub.add_edge_unchecked(owner,'keeps',srs.NodeID(leaf))
    return sub,root,ts,leaf,owner
def main():
    if len(sys.argv)!=2: raise SystemExit('usage: substrate_term_cleanup_hooks_probe.py OUTPUT.json')
    output=Path(sys.argv[1]); lock=json.loads(LOCK.read_text()); native=Path(srs._native.__file__).resolve()
    expected={'preregistration_sha256':sha(PREREG),'runner_sha256':sha(__file__),'native_sha256':sha(native)}
    if any(lock.get(k)!=v for k,v in expected.items()): raise SystemExit('probe lock mismatch')
    stale=subprocess.check_output([sys.executable,'-c',"from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')))"] ,cwd=ROOT,text=True).strip()
    if stale: raise SystemExit('native build stale:\n'+stale)
    start=time.perf_counter_ns(); cases=[]
    for shared in (False,True):
        sub,root,terms,leaf,owner=setup(shared); seen=[]
        sub._inner.register_hook('node_deleted',lambda nid,ty: seen.append((int(nid.value),str(ty))))
        try: report=sub._inner.remove_term_subgraph(root); error=None
        except Exception as e: report=None; error=repr(e)
        removed=report['removed_node_ids'] if report is not None else []
        protected=report['protected_node_ids'] if report is not None else []
        live={i for i,t in nodes(sub) if t.startswith('Term.')}
        cases.append({'case':'shared_leaf' if shared else 'success','callback_records':seen,'removed_ids':removed,'protected_ids':protected,'live_term_ids':sorted(live),'error':error,'hooks_match_removed_order':seen==[(i,next(t for ni,t in terms if ni==i)) for i in removed],'protected_silent':not(set(i for i,_ in seen)&set(protected)),'passed':error is None and seen==[(i,next(t for ni,t in terms if ni==i)) for i in removed] and not(set(i for i,_ in seen)&set(protected)) and (leaf in live if shared else not live)})
    sub,root,terms,leaf,owner=setup(False); seen=[]
    def fail_once(nid,ty):
        seen.append(('raising',int(nid.value),str(ty)))
        raise RuntimeError('hook_probe_failure')
    observer=[]
    sub._inner.register_hook('node_deleted',fail_once)
    sub._inner.register_hook('node_deleted',lambda nid,ty: observer.append((int(nid.value),str(ty))))
    try: sub._inner.remove_term_subgraph(root); error=None
    except Exception as e: error=repr(e)
    live={i for i,t in nodes(sub) if t.startswith('Term.')}
    cases.append({'case':'callback_raises_then_observer','callback_records':seen,'observer_records':observer,'observed_error':error,'live_term_ids':sorted(live),'mutation_committed':not live,'all_events_dispatched':len(seen)==4 and len(observer)==4,'first_error_surfaced':error is not None and 'hook_probe_failure' in error})
    passed=all(c.get('passed',True) for c in cases[:2]) and cases[2]['all_events_dispatched'] and cases[2]['first_error_surfaced'] and not cases[2]['live_term_ids']
    payload={'schema_version':1,'run_id':'term-cleanup-hooks-20260925-v1','cases':cases,'all_cases_pass':passed,'wall_ns':time.perf_counter_ns()-start,'environment':{'python':sys.version,'platform':platform.platform(),'native_path':str(native),'native_sha256':sha(native)},'provenance':{**expected,'lock_sha256':sha(LOCK),'build_record_sha256':sha(native.with_name('_native.build.json')),'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()},'claim_boundary':'hook accounting and failure semantics only; no arena compaction, concurrency, or broad performance claim'}
    output.parent.mkdir(parents=True,exist_ok=True); output.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n'); print(json.dumps({'all_cases_pass':passed,'output':str(output)})); return 0 if passed else 2
if __name__=='__main__': raise SystemExit(main())
