#!/usr/bin/env python3
"""Run and record the Rust TermArena lifecycle evaluation harness."""
from __future__ import annotations
import hashlib, json, platform, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
EXAMPLE=ROOT/'runners/dsl/examples/term_arena_growth_probe.rs'
PREREG=ROOT/'docs/research/engine_substrate/SUBSTRATE_TERM_ARENA_GROWTH_PREREG_20260925.md'
LOCK=ROOT/'evaluation/substrate_capability/term_arena_growth_lock_20260925.json'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    if len(sys.argv)!=2: raise SystemExit('usage: substrate_term_arena_growth_probe.py OUTPUT.json')
    lock=json.loads(LOCK.read_text()); expected={'preregistration_sha256':sha(PREREG),'runner_sha256':sha(EXAMPLE),'orchestrator_sha256':sha(__file__)}
    if any(lock.get(k)!=v for k,v in expected.items()): raise SystemExit('TermArena probe lock mismatch')
    completed=subprocess.run(['cargo','run','--example','term_arena_growth_probe','--quiet'],cwd=ROOT/'runners/dsl',text=True,capture_output=True,check=True)
    report=json.loads(completed.stdout)
    payload={'schema_version':1,'run_id':report['run_id'],'term':report['term'],'results':report['results'],'claim_boundary':report['claim_boundary'],'environment':{'python':sys.version,'platform':platform.platform(),'rustc':subprocess.check_output(['rustc','--version'],text=True).strip()},'provenance':{**expected,'lock_sha256':sha(LOCK),'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()},'build_stderr_sha256':hashlib.sha256(completed.stderr.encode()).hexdigest(),'build_stderr_bytes':len(completed.stderr)}
    output=Path(sys.argv[1]); output=output if output.is_absolute() else ROOT/output
    output.parent.mkdir(parents=True,exist_ok=True); output.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'record':str(output),'modes':[r['mode'] for r in payload['results']]}))
if __name__=='__main__': main()
