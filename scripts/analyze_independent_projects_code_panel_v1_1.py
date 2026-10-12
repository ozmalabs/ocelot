#!/usr/bin/env python3
"""Independent selector reconstruction and bounded AST oracle for external-project panel."""
from __future__ import annotations
import ast,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; SNAP=ROOT/'data/independent_python_projects_v1_1'; FRAME=ROOT/'evaluation/substrate_capability/independent_projects_code_panel_v1_1_frame_20260928.json';RAW=ROOT/'evaluation/reports/independent_projects_code_panel_v1_1_20260928.json';OUT=ROOT/'evaluation/reports/independent_projects_code_panel_v1_1_analysis_20260928.json'
FP=b'ocelot-independent-function-v1\0';PP=b'ocelot-independent-project-v1\0';ONE=[-3,-1,0,1,2,3,7,16,64];TWO=[(-3,-1),(-1,-3),(0,1),(1,0),(2,3),(3,2),(7,16),(16,7),(64,3)]
BIN={ast.Add:lambda x,y:x+y,ast.Sub:lambda x,y:x-y,ast.Mult:lambda x,y:x*y,ast.BitAnd:lambda x,y:x&y,ast.BitOr:lambda x,y:x|y,ast.BitXor:lambda x,y:x^y};CMP={ast.Eq:lambda x,y:x==y,ast.NotEq:lambda x,y:x!=y,ast.Lt:lambda x,y:x<y,ast.LtE:lambda x,y:x<=y,ast.Gt:lambda x,y:x>y,ast.GtE:lambda x,y:x>=y}
def sha(b):return hashlib.sha256(b).hexdigest()
def fsha(p):return sha(Path(p).read_bytes())
def without_doc(body):
 if body and isinstance(body[0],ast.Expr) and isinstance(body[0].value,ast.Constant) and type(body[0].value.value)is str:return body[1:]
 return body
def sig(f):
 a=f.args;return bool(a.args) and not(a.posonlyargs or a.kwonlyargs or a.vararg or a.kwarg or a.defaults or any(x is not None for x in a.kw_defaults))
def index(tree):
 fs={};dups=set()
 for n in tree.body:
  if isinstance(n,ast.FunctionDef):
   if n.name in fs:dups.add(n.name)
   fs[n.name]=n
 assigns={};unsafe=set()
 for n in tree.body:
  if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):continue
  if isinstance(n,(ast.Assign,ast.AnnAssign)):
   target=n.targets[0] if isinstance(n,ast.Assign) and len(n.targets)==1 else n.target if isinstance(n,ast.AnnAssign) else None
   if isinstance(target,ast.Name) and isinstance(n.value,ast.Constant) and type(n.value.value)is int:
    assigns.setdefault(target.id,[]).append(n.value.value);continue
  for x in ast.walk(n):
   if isinstance(x,ast.Name) and isinstance(x.ctx,(ast.Store,ast.Del)):unsafe.add(x.id)
   elif isinstance(x,ast.alias):unsafe.add(x.asname or x.name.split('.')[0])
 const={k:v[0] for k,v in assigns.items() if len(v)==1 and k not in unsafe};amb=(set(assigns)-set(const))|unsafe
 return fs,dups,const,amb
def inspect(e,env,fs,dups,const,amb,callstack,depth):
 if isinstance(e,ast.Constant):return type(e.value)is int,False
 if isinstance(e,ast.Name):return e.id in env or (e.id in const and e.id not in amb),False
 if isinstance(e,ast.BinOp) and type(e.op) in BIN:
  l,lo=inspect(e.left,env,fs,dups,const,amb,callstack,depth);r,ro=inspect(e.right,env,fs,dups,const,amb,callstack,depth);return l and r,True
 if isinstance(e,ast.UnaryOp) and type(e.op) in (ast.USub,ast.Not):return inspect(e.operand,env,fs,dups,const,amb,callstack,depth)
 if isinstance(e,ast.Compare) and len(e.ops)==len(e.comparators)==1 and type(e.ops[0]) in CMP:
  l,_=inspect(e.left,env,fs,dups,const,amb,callstack,depth);r,_=inspect(e.comparators[0],env,fs,dups,const,amb,callstack,depth);return l and r,True
 if isinstance(e,ast.Call) and isinstance(e.func,ast.Name) and not e.keywords:
  f=fs.get(e.func.id)
  if f is None or e.func.id in dups or e.func.id in callstack or depth==4 or f.decorator_list or not sig(f) or len(e.args)!=len(f.args.args):return False,False
  b=without_doc(f.body)
  if len(b)!=1 or not isinstance(b[0],ast.Return) or b[0].value is None:return False,False
  argres=[inspect(a,env,fs,dups,const,amb,callstack,depth) for a in e.args]
  bodyres=inspect(b[0].value,{a.arg for a in f.args.args},fs,dups,const,amb,callstack|{e.func.id},depth+1)
  return all(x[0] for x in argres) and bodyres[0],any(x[1] for x in argres) or bodyres[1]
 return False,False
def rebuild():
 manifest=json.loads((SNAP/'manifest.json').read_text());allfunc=[];file_inventory=[]
 for proj in sorted(manifest['projects'],key=lambda x:x['normalized_name']):
  root=SNAP/proj['normalized_name']/'source'
  for path in sorted(root.rglob('*.py')):
   data=path.read_bytes();rel=path.relative_to(root).as_posix();file_inventory.append({'project':proj['normalized_name'],'path':rel,'sha256':sha(data)})
   tree=ast.parse(data.decode(),filename=rel);fs,dups,const,amb=index(tree)
   for fn in tree.body:
    if not isinstance(fn,ast.FunctionDef) or fn.name in dups or fn.decorator_list or not sig(fn) or len(fn.args.args) not in (1,2):continue
    body=without_doc(fn.body)
    if len(body)!=1 or not isinstance(body[0],ast.Return) or body[0].value is None:continue
    valid,hasop=inspect(body[0].value,{a.arg for a in fn.args.args},fs,dups,const,amb,set(),0)
    if not valid or not hasop:continue
    source=ast.get_source_segment(data.decode(),fn)
    if not source:continue
    names=[a.arg for a in fn.args.args];inputs=([ {names[0]:v} for v in ONE] if len(names)==1 else [{names[0]:x,names[1]:y} for x,y in TWO])
    allfunc.append({'project':proj['normalized_name'],'file':rel,'function':fn.name,'line':fn.lineno,'arguments':names,'module_sha256':sha(data),'function_sha256':sha(source.encode()),'input_cases':inputs})
 allfunc.sort(key=lambda r:(sha(FP+r['project'].encode()+b'\0'+r['file'].encode()+b'\0'+r['function'].encode()+b'\0'+str(r['line']).encode()),r['project'],r['file'],r['function'],r['line']))
 reps={}
 for r in allfunc:reps.setdefault(r['project'],r)
 projects=sorted(reps.values(),key=lambda r:(sha(PP+r['project'].encode()),r['project']))
 inventory=[{'name':p['name'],'normalized_name':p['normalized_name'],'version':p['version'],'license_id':p['license_id'],'python_file_count':p['python_file_count'],'license_file_count':p['license_file_count']} for p in manifest['projects']]
 return {'schema':'independent-projects-code-frame-v1.1','snapshot_manifest_sha256':fsha(SNAP/'manifest.json'),'project_inventory':inventory,'files':file_inventory,'eligible_project_count':len(manifest['projects']),'projects_with_eligible_functions':len(reps),'eligible_function_count':len(allfunc),'eligible_functions':allfunc,'project_representatives':projects,'selected':projects[:24],'selected_project_count':min(24,len(projects))},fs

def oracle(source,function,args):
 tree=ast.parse(source); funcs,dups,const,amb=index(tree)
 def ev(e,env,depth,stack):
  if isinstance(e,ast.Constant) and type(e.value)is int:return e.value
  if isinstance(e,ast.Name):
   if e.id in env:return env[e.id]
   if e.id in const and e.id not in amb:return const[e.id]
   raise ValueError('unbound name')
  if isinstance(e,ast.BinOp) and type(e.op) in BIN:return BIN[type(e.op)](ev(e.left,env,depth,stack),ev(e.right,env,depth,stack))
  if isinstance(e,ast.UnaryOp) and isinstance(e.op,ast.USub):return -ev(e.operand,env,depth,stack)
  if isinstance(e,ast.UnaryOp) and isinstance(e.op,ast.Not):return not ev(e.operand,env,depth,stack)
  if isinstance(e,ast.Compare) and len(e.ops)==len(e.comparators)==1 and type(e.ops[0]) in CMP:return CMP[type(e.ops[0])](ev(e.left,env,depth,stack),ev(e.comparators[0],env,depth,stack))
  if isinstance(e,ast.Call) and isinstance(e.func,ast.Name) and not e.keywords:
   name=e.func.id;fn=funcs[name]
   if name in stack or depth>=4:raise ValueError('cycle/depth')
   vals=[ev(a,env,depth,stack) for a in e.args]
   if len(vals)!=len(fn.args.args):raise ValueError('arity')
   body=without_doc(fn.body)
   if len(body)!=1 or not isinstance(body[0],ast.Return):raise ValueError('helper shape')
   return ev(body[0].value,{p.arg:v for p,v in zip(fn.args.args,vals)},depth+1,stack|{name})
  raise ValueError('oracle rejected '+type(e).__name__)
 fn=funcs[function]; val=ev(without_doc(fn.body)[0].value,args,0,set())
 if type(val) not in (int,bool):raise ValueError('nonprimitive result')
 return {'type':type(val).__name__,'value':val}
def main():
 frame=json.loads(FRAME.read_text());raw=json.loads(RAW.read_text());expected,_=rebuild();runs=raw.get('runs',[]);tasks=[];oracle_errors=[]
 for fi,row in enumerate(expected['selected']):
  srcpath=SNAP/row['project']/'source'/row['file'];source=srcpath.read_text()
  for ci,args in enumerate(row['input_cases']):
   try:exp=oracle(source,row['function'],args)
   except Exception as e:exp=None;oracle_errors.append([row['project'],row['file'],row['function'],ci,type(e).__name__])
   tasks.append((fi,ci,row,args,exp))
 maps=[{(c['function_index'],c['case_index']):c for c in r.get('calls',[])} for r in runs]
 exact=True; summaries=[]
 for wi,r in enumerate(runs):
  scores=[]
  if len(r.get('calls',[]))!=len(tasks):exact=False
  for fi,ci,row,args,exp in tasks:
   c=maps[wi].get((fi,ci))
   if c is None:exact=False;continue
   path=SNAP/row['project']/'source'/row['file']
   expected_tuple=(row['project'],row['file'],row['function'],args,row['module_sha256'],row['function_sha256'],fsha(path))
   actual=(c.get('project'),c.get('file'),c.get('function'),c.get('args'),c.get('module_sha256_expected'),c.get('function_sha256_expected'),c.get('module_sha256_observed'))
   if actual!=expected_tuple:exact=False
   pred=c.get('prediction');err=c.get('error_type');correct=exp is not None and err is None and pred==exp;wrong=err is None and pred!=exp
   scores.append({'project':row['project'],'file':row['file'],'function':row['function'],'case_index':ci,'expected':exp,'prediction':pred,'error_type':err,'correct':correct,'abstained':err is not None,'wrong_return':wrong,'wall_ns':c['wall_ns'],'cpu_ns':c['cpu_ns'],'receipt_delta':c['receipt_delta'],'observations':len(c['new_observations']),'new_axis_count':c['new_axis_count']})
  walls=sorted(x['wall_ns'] for x in scores);cpus=sorted(x['cpu_ns'] for x in scores)
  summaries.append({'replicate':r.get('replicate'),'case_count':len(scores),'exact_correct':sum(x['correct'] for x in scores),'predictions':sum(not x['abstained'] for x in scores),'abstentions':sum(x['abstained'] for x in scores),'wrong_returns':sum(x['wrong_return'] for x in scores),'median_wall_ns':walls[len(walls)//2] if walls else None,'p95_wall_ns':walls[int(.95*len(walls))] if walls else None,'median_cpu_ns':cpus[len(cpus)//2] if cpus else None,'p95_cpu_ns':cpus[int(.95*len(cpus))] if cpus else None,'receipt_count':sum(x['receipt_delta'] for x in scores),'observation_count':sum(x['observations'] for x in scores),'minted_axis_observation_count':sum(x['new_axis_count'] for x in scores),'boot_loaded':r['boot']['loaded'],'boot_total':r['boot']['total'],'boot_failures':len(r['boot']['failed']),'peak_rss_bytes':r['runtime']['peak_rss_bytes'],'case_results':scores})
 parity=len(maps)==2 and all((maps[0].get((fi,ci),{}).get('prediction'),maps[0].get((fi,ci),{}).get('error_type'))==(maps[1].get((fi,ci),{}).get('prediction'),maps[1].get((fi,ci),{}).get('error_type')) for fi,ci,_,_,_ in tasks)
 m=raw.get('run_manifest',{});cap=m.get('stdout_stderr_capture')or{};lp=ROOT/cap.get('path','__missing__');log=lp.read_bytes()if lp.is_file()else b''
 checks={'independent_frame_reconstruction':frame==expected,'selected_project_count_nonzero':len(expected['selected'])>0,'independent_oracle_error_free':not oracle_errors,'two_fresh_workers':len(runs)==2 and len({r.get('pid')for r in runs})==2,'stable_source_locks':raw.get('post_run_inputs')==raw.get('locked_inputs')and all(r.get('source_stable')and r.get('locked_inputs_before')==raw.get('locked_inputs')==r.get('locked_inputs_after')for r in runs),'exact_schedules_and_source_hashes':exact,'worker_parity':parity,'manifest_capture_valid':m.get('manifest_schema')=='substrate-run-manifest-v1'and m.get('exit_status')==0 and bool(log)and len(log)==cap.get('bytes')and hashlib.sha256(log).hexdigest()==cap.get('sha256')and all(f'completed=worker{i} rc=0'.encode()in log for i in(0,1)),'workers_succeeded':all(r.get('worker_returncode')==0 and r.get('boot',{}).get('loaded',0)>0 for r in runs),'no_wrong_return_values':all(x['wrong_returns']==0 for x in summaries),'runner_integrity_passed':raw.get('integrity_pass')and all(raw.get('integrity_checks',{}).values())}
 result={'schema':'independent-projects-code-analysis-v1.1','checks':checks,'pass':all(checks.values()),'summary':{'eligible_projects':expected['eligible_project_count'],'projects_with_eligible_functions':expected['projects_with_eligible_functions'],'selected_projects':expected['selected_project_count'],'eligible_functions':expected['eligible_function_count'],'selected_functions':len(expected['selected']),'case_count':len(tasks),'oracle_errors':oracle_errors,'workers':summaries,'claim_boundary':raw.get('claim_boundary')}}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'analysis':OUT.relative_to(ROOT).as_posix(),'pass':result['pass'],'checks':checks,'selected_projects':len(expected['selected']),'cases':len(tasks)},indent=2,sort_keys=True))
 if not result['pass']:raise SystemExit('independent-project panel analysis failed')
if __name__=='__main__':main()
