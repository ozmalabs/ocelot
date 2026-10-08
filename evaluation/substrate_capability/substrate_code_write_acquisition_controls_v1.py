#!/usr/bin/env python3
"""Source-locked exposure-only and misleading-example controls."""
from __future__ import annotations
import hashlib, json, os, platform, random, resource, subprocess, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
RUNNER=Path(__file__).resolve()
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_CODE_WRITE_ACQUISITION_CONTROLS_V1_PREREG_20261001.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_substrate_code_write_acquisition_controls_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/substrate_code_write_acquisition_controls_v1_lock_20261001.json'
RAW=ROOT/'evaluation/reports/substrate_code_write_acquisition_controls_v1_raw_20261001.json'
SOURCE='def parity(value):\n    return value % 2 == 0\n'
PARITY='Write a function that returns the parity of an integer.'
CLAMP='Write a function that clamps a value between lower and upper bounds.'
CASES=[{'value':-10,'lower':-3,'upper':4},{'value':-3,'lower':-3,'upper':4},
 {'value':-2,'lower':-3,'upper':4},{'value':0,'lower':-3,'upper':4},
 {'value':3,'lower':-3,'upper':4},{'value':4,'lower':-3,'upper':4},
 {'value':5,'lower':-3,'upper':4},{'value':10,'lower':-3,'upper':4},
 {'value':-5,'lower':1,'upper':6},{'value':1,'lower':1,'upper':6},
 {'value':3,'lower':1,'upper':6},{'value':8,'lower':1,'upper':6}]
ACTIVE=('domains/code_reading.py','domains/code_writing.py','domains/code_write_growth.py',
 'domains/ast_to_term.py','domains/teach.py','domains/engine_provenance.py',
 'substrate/world_adapter.py','substrate/boot_all.py','substrate/boot_core.py',
 'substrate/seed_loader.py','runners/dsl/src/term.rs','runners/dsl/src/py.rs',
 'runners/dsl/src/graph_rules.rs','runners/dsl/src/substrate.rs',
 'runners/dsl/python/substrate_rs/__init__.py','runners/dsl/python/substrate_rs/_native.build.json',
 'seeds/code_constructions.json','seeds/code_write_constructions.json',
 'seeds/code_write_request_cues.json','seeds/code_write_gap.json','seeds/gap_awareness.json')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def tree(paths,suffixes):
 entries=[]
 for rel in paths:
  p=ROOT/rel
  for f in ([p] if p.is_file() else sorted(x for x in p.rglob('*') if x.is_file())):
   if f.suffix in suffixes or f.name in {'_native.abi3.so','_native.build.json'}: entries.append((f.relative_to(ROOT).as_posix(),sha(f)))
 h=hashlib.sha256()
 for a,b in sorted(entries): h.update(a.encode()+b'\0'+b.encode()+b'\n')
 return h.hexdigest()
def active():
 sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
 import substrate_rs as srs
 result={x:sha(ROOT/x) for x in ACTIVE}; result['native']=sha(Path(srs._native.__file__).resolve()); return result
def seedsha():
 files=sorted([*(ROOT/'seeds').glob('*.json'),*(ROOT/'seeds/generated').glob('*.json')]); h=hashlib.sha256()
 for p in files: h.update(p.relative_to(ROOT).as_posix().encode()+b'\0'+sha(p).encode()+b'\n')
 return h.hexdigest()
def payload():
 a=active()
 return {'schema':'SubstrateCodeWriteAcquisitionControlsV1Lock',
  'files':{str(p.relative_to(ROOT)):sha(p) for p in (RUNNER,ANALYZER,PROTOCOL)},
  'trees':{'domains':tree(('domains',),('.py',)),'substrate':tree(('substrate',),('.py',)),
   'seed_manifests':seedsha(),'rust':tree(('runners/dsl/src',),('.rs',)),
   'python_native':tree(('runners/dsl/python/substrate_rs',),('.py',))},
  'active':a,'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
  'design':{'arms':['exposure_only','mismatched_teaching'],'repetitions':2,'seed':20261019,
   'source':SOURCE,'parity_request':PARITY,'clamp_request':CLAMP,'heldout':CASES}}
def worker(arm,rep):
 os.environ.setdefault('OZMA_NO_LLM','1'); os.environ.setdefault('OZMA_SEED_PERSIST_DISABLED','1')
 lock=json.loads(LOCK.read_text()); before=active()
 if before!=lock['active']: raise RuntimeError('active source differs from lock')
 from domains import code_reading as cdr, code_writing as cw, code_write_growth as cwg
 from substrate.boot_all import load_all_seeds
 from substrate.world_adapter import WorldAdapter
 a=WorldAdapter(seeds=()); t=time.perf_counter_ns(); boot=load_all_seeds(a); boot_ns=time.perf_counter_ns()-t
 sub,native,agent=cdr._resolve(a)
 baseline=cw.write_function_from_request(a, PARITY if arm=='exposure_only' else CLAMP, name='candidate')
 shapes0=[n for n in sub.nodes('ShapeSignature') if sub.node(n)['attrs'].get('kind')=='code_write_construction']
 t=time.perf_counter_ns()
 if arm=='exposure_only': intervention=cdr.read_function(a,SOURCE,'parity')
 else: intervention=cwg.teach_write_shape_from_example(a,SOURCE,request_text=CLAMP)
 intervention_ns=time.perf_counter_ns()-t
 req=PARITY if arm=='exposure_only' else CLAMP
 composed=cw.compose_function_from_request(a,req); written=cw.write_function_from_request(a,req,name='candidate')
 scope={};
 try: exec(written.get('source',''),scope); fn=scope.get('candidate')
 except Exception: fn=None
 held=[]
 for env in (CASES if arm=='mismatched_teaching' else [{'value':-2},{'value':-1},{'value':0},{'value':1}]):
  nv=native.evaluate(composed['term'],env) if composed.get('ok') else None
  try: pv=fn(**env) if callable(fn) else None
  except Exception as e: pv={'error':type(e).__name__}
  held.append({'input':env,'native':nv,'python':pv})
 after=active()
 return {'kind':'worker','arm':arm,'rep':rep,'pid':os.getpid(),'source_stable':before==after,
  'before':before,'after':after,'boot_ns':boot_ns,'boot_loaded':len(getattr(boot,'loaded',[]) or []),
  'baseline':baseline,'shapes_before':len(shapes0),'intervention':intervention,
  'intervention_ns':intervention_ns,'shapes_after':len([n for n in sub.nodes('ShapeSignature') if sub.node(n)['attrs'].get('kind')=='code_write_construction']),
  'compose':composed,'written':{k:written.get(k) for k in ('ok','source','construction','args','term','sample_ok')},
  'heldout':held,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024}
def main():
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or RAW.exists(): raise SystemExit('refusing overwrite')
  LOCK.write_text(json.dumps(payload(),indent=2,sort_keys=True)+'\n'); print(LOCK.relative_to(ROOT)); return
 current=payload()
 if not LOCK.exists() or json.loads(LOCK.read_text())!=current: raise SystemExit('missing/stale lock')
 if RAW.exists(): raise SystemExit('refusing overwrite capture')
 schedule=[(a,r) for a in ('exposure_only','mismatched_teaching') for r in (1,2)]; random.Random(20261019).shuffle(schedule)
 env=dict(os.environ,OZMA_NO_LLM='1',OZMA_SEED_PERSIST_DISABLED='1'); env['PYTHONPATH']=f"{ROOT}:{ROOT/'runners/dsl/python'}:{env.get('PYTHONPATH','')}"
 rows=[]; start=time.perf_counter()
 for i,(arm,rep) in enumerate(schedule,1):
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',arm,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=120)
  row=json.loads(p.stdout.strip().splitlines()[-1]) if p.returncode==0 else {'kind':'worker_error','arm':arm,'rep':rep,'error':p.stderr[-4000:]}
  rows.append(row); print(f'{i}/4 {arm} r={rep}: {row["kind"]}',flush=True)
 post=payload(); RAW.write_text(json.dumps({'schema':'SubstrateCodeWriteAcquisitionControlsV1Capture','lock':current,'post_lock':post,'schedule':[{'arm':a,'rep':r} for a,r in schedule],'workers':rows,'elapsed_seconds':time.perf_counter()-start,'environment':{'python':sys.version,'platform':platform.platform()}},indent=2,sort_keys=True,default=str)+'\n')
 print(json.dumps({'raw':str(RAW.relative_to(ROOT)),'workers':len(rows),'errors':sum(x.get('kind')!='worker' for x in rows),'stable':current==post}))
if __name__=='__main__':
 if len(sys.argv)==4 and sys.argv[1]=='--worker': print(json.dumps(worker(sys.argv[2],int(sys.argv[3])),sort_keys=True,default=str))
 else: main()
