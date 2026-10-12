#!/usr/bin/env python3
"""Independent frame reconstruction, safe AST oracle and scorer."""
from __future__ import annotations
import ast, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CORPUS=ROOT/'data/cpython_lib_3_13_5'
FRAME=ROOT/'evaluation/substrate_capability/code_module_heldout_panel_v1_1_frame_20260928.json'
RAW=ROOT/'evaluation/reports/code_module_heldout_panel_v1_1_20260928.json'
OUT=ROOT/'evaluation/reports/code_module_heldout_panel_v1_1_analysis_20260928.json'
MODULE_PREFIX=b'CPython3.13.5-module-heldout-v1\0'; FUNCTION_PREFIX=b'CPython3.13.5-function-heldout-v1\0'
INPUTS=[-1,0,1,63,64,65,127,128,255]
PAIRS=[(-1,0),(0,-1),(0,1),(1,0),(63,64),(64,63),(64,65),(65,64),(255,128)]
OPS={ast.BitAnd:lambda a,b:a&b,ast.BitOr:lambda a,b:a|b,ast.BitXor:lambda a,b:a^b}
CMPS={ast.Eq:lambda a,b:a==b,ast.NotEq:lambda a,b:a!=b,ast.Lt:lambda a,b:a<b,ast.LtE:lambda a,b:a<=b,ast.Gt:lambda a,b:a>b,ast.GtE:lambda a,b:a>=b}

def sha(data): return hashlib.sha256(data).hexdigest()
def bytes_sha(path): return sha(Path(path).read_bytes())
def docless(body):
    if body and isinstance(body[0],ast.Expr) and isinstance(body[0].value,ast.Constant) and isinstance(body[0].value.value,str): return body[1:]
    return body
def signature_ok(fn):
    a=fn.args
    return bool(a.args) and not a.posonlyargs and not a.kwonlyargs and not a.vararg and not a.kwarg and not a.defaults and not any(x is not None for x in a.kw_defaults)
def module_tables(tree):
    funcs={}; dup=set()
    for n in tree.body:
        if isinstance(n,ast.FunctionDef):
            if n.name in funcs: dup.add(n.name)
            funcs[n.name]=n
    assignments={}; bad=set()
    for n in tree.body:
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)): continue
        if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and isinstance(n.value,ast.Constant) and type(n.value.value)is int:
            assignments.setdefault(n.targets[0].id,[]).append(n.value.value); continue
        if isinstance(n,ast.AnnAssign) and isinstance(n.target,ast.Name) and isinstance(n.value,ast.Constant) and type(n.value.value)is int:
            assignments.setdefault(n.target.id,[]).append(n.value.value); continue
        for x in ast.walk(n):
            if isinstance(x,ast.Name) and isinstance(x.ctx,(ast.Store,ast.Del)): bad.add(x.id)
            if isinstance(x,ast.alias): bad.add(x.asname or x.name.split('.',1)[0])
    const={k:v[0] for k,v in assignments.items() if len(v)==1 and k not in bad}
    ambiguous=(set(assignments)-set(const))|bad
    return funcs,dup,const,ambiguous

def valid_expr(e,env,funcs,dups,const,amb,stack,depth):
    if isinstance(e,ast.Constant): return type(e.value)is int,False
    if isinstance(e,ast.Name): return (e.id in env or (e.id in const and e.id not in amb)),False
    if isinstance(e,ast.BinOp) and type(e.op) in OPS:
        a,ba=valid_expr(e.left,env,funcs,dups,const,amb,stack,depth); b,bb=valid_expr(e.right,env,funcs,dups,const,amb,stack,depth); return a and b,True or ba or bb
    if isinstance(e,ast.UnaryOp) and type(e.op) in (ast.USub,ast.Not): return valid_expr(e.operand,env,funcs,dups,const,amb,stack,depth)
    if isinstance(e,ast.Compare) and len(e.ops)==1 and len(e.comparators)==1 and type(e.ops[0]) in CMPS:
        a,ba=valid_expr(e.left,env,funcs,dups,const,amb,stack,depth); b,bb=valid_expr(e.comparators[0],env,funcs,dups,const,amb,stack,depth); return a and b,ba or bb
    if isinstance(e,ast.Call) and isinstance(e.func,ast.Name) and not e.keywords:
        name=e.func.id; fn=funcs.get(name)
        if fn is None or name in dups or name in stack or depth>=4 or fn.decorator_list or not signature_ok(fn) or len(e.args)!=len(fn.args.args): return False,False
        body=docless(fn.body)
        if len(body)!=1 or not isinstance(body[0],ast.Return) or body[0].value is None:return False,False
        good=False; bit=False
        for arg in e.args:
            x,b=valid_expr(arg,env,funcs,dups,const,amb,stack,depth); good=good or x; bit=bit or b
            if not x:return False,False
        x,b=valid_expr(body[0].value,{a.arg for a in fn.args.args},funcs,dups,const,amb,stack|{name},depth+1)
        return x and all(valid_expr(a,env,funcs,dups,const,amb,stack,depth)[0] for a in e.args),bit or b
    return False,False

def expected_frame():
    files=sorted(CORPUS.glob('*.py'))
    inventory=[{'name':p.name,'sha256':bytes_sha(p)} for p in files]
    eligible=[p for p in files if p.name!='stat.py' and not p.name.startswith('__')]
    modules=sorted(eligible,key=lambda p:(sha(MODULE_PREFIX+p.name.encode()),p.name))
    rows=[]
    for path in modules:
        data=path.read_bytes(); text=data.decode(); tree=ast.parse(text,filename=path.name); funcs,dups,const,amb=module_tables(tree)
        for fn in tree.body:
            if not isinstance(fn,ast.FunctionDef) or fn.name in dups or fn.decorator_list or not signature_ok(fn) or len(fn.args.args) not in (1,2):continue
            body=docless(fn.body)
            if len(body)!=1 or not isinstance(body[0],ast.Return) or body[0].value is None:continue
            ok,bit=valid_expr(body[0].value,{a.arg for a in fn.args.args},funcs,dups,const,amb,set(),0)
            if not ok or not bit:continue
            segment=ast.get_source_segment(text,fn)
            if not segment:continue
            args=[a.arg for a in fn.args.args]
            cases=([{args[0]:v} for v in INPUTS] if len(args)==1 else [{args[0]:x,args[1]:y} for x,y in PAIRS])
            rows.append({'file':path.name,'function':fn.name,'line':fn.lineno,'arguments':args,'module_sha256':sha(data),'function_sha256':sha(segment.encode()),'input_cases':cases})
    rows.sort(key=lambda r:(sha(FUNCTION_PREFIX+r['file'].encode()+b'\0'+r['function'].encode()+b'\0'+str(r['line']).encode()),r['file'],r['function'],r['line']))
    modrows=[{'name':p.name,'sha256':bytes_sha(p),'eligible_function_count':sum(x['file']==p.name for x in rows)} for p in modules]
    return {'schema':'code-module-heldout-frame-v1.1','corpus':'CPython 3.13.5 top-level Lib Python files; stat.py excluded','corpus_inventory':inventory,'corpus_license_sha256':bytes_sha(CORPUS/'LICENSE.txt'),'module_sample':modrows,'eligible_functions':rows,'eligible_function_count':len(rows),'selected':rows[:24],'selected_function_count':min(24,len(rows))}

def safe_oracle(source,function,args):
    tree=ast.parse(source); funcs,dups,const,amb=module_tables(tree)
    def ev(n,env,depth,stack):
        if isinstance(n,ast.Constant):
            if type(n.value)is not int:raise TypeError('literal outside oracle grammar')
            return n.value
        if isinstance(n,ast.Name):
            if n.id in env:return env[n.id]
            if n.id in const and n.id not in amb:return const[n.id]
            raise TypeError('unbound name')
        if isinstance(n,ast.BinOp) and type(n.op) in OPS:return OPS[type(n.op)](ev(n.left,env,depth,stack),ev(n.right,env,depth,stack))
        if isinstance(n,ast.UnaryOp) and isinstance(n.op,ast.USub):return -ev(n.operand,env,depth,stack)
        if isinstance(n,ast.UnaryOp) and isinstance(n.op,ast.Not):return not ev(n.operand,env,depth,stack)
        if isinstance(n,ast.Compare) and len(n.ops)==1 and len(n.comparators)==1 and type(n.ops[0]) in CMPS:return CMPS[type(n.ops[0])](ev(n.left,env,depth,stack),ev(n.comparators[0],env,depth,stack))
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and not n.keywords:
            name=n.func.id; fn=funcs[name]
            if name in stack or depth>=4:raise TypeError('recursion/depth')
            vals=[ev(a,env,depth,stack) for a in n.args]
            if len(vals)!=len(fn.args.args):raise TypeError('arity')
            body=docless(fn.body)
            if len(body)!=1 or not isinstance(body[0],ast.Return):raise TypeError('helper shape')
            return ev(body[0].value,{p.arg:v for p,v in zip(fn.args.args,vals)},depth+1,stack|{name})
        raise TypeError('oracle rejected '+type(n).__name__)
    fn=funcs[function]; result=ev(docless(fn.body)[0].value,args,0,set())
    if type(result) not in (bool,int):raise TypeError('output outside primitive target')
    return {'type':type(result).__name__,'value':result}

def main():
    frame=json.loads(FRAME.read_text()); raw=json.loads(RAW.read_text()); expected=expected_frame()
    tasks=[]; oracle_fail=[]
    for fi,row in enumerate(expected['selected']):
        source=(CORPUS/row['file']).read_text()
        for ci,args in enumerate(row['input_cases']):
            try: exp=safe_oracle(source,row['function'],args)
            except Exception as e: exp=None; oracle_fail.append([row['file'],row['function'],ci,type(e).__name__])
            tasks.append((fi,ci,row,args,exp))
    runs=raw.get('runs',[]); manifest=raw.get('run_manifest',{}); cap=manifest.get('stdout_stderr_capture') or {}; logpath=ROOT/cap.get('path','__missing__'); log=logpath.read_bytes() if logpath.is_file() else b''
    base=raw.get('locked_inputs',{}); outcome_maps=[]
    for run in runs: outcome_maps.append({(c.get('function_index'),c.get('case_index')):c for c in run.get('calls',[])})
    exact_schedule=True; score_ok=True; summaries=[]
    for wi,run in enumerate(runs):
        calls=run.get('calls',[]); scores=[]
        if len(calls)!=len(tasks): exact_schedule=False
        for task in tasks:
            fi,ci,row,args,exp=task; call=outcome_maps[wi].get((fi,ci))
            if not call: exact_schedule=False; continue
            src=CORPUS/row['file']; segment=ast.get_source_segment(src.read_text(),next(n for n in ast.parse(src.read_text()).body if isinstance(n,ast.FunctionDef) and n.name==row['function']))
            if (call.get('file'),call.get('function'),call.get('args'),call.get('module_sha256_expected'),call.get('function_sha256_expected'),call.get('module_sha256_observed'))!=(row['file'],row['function'],args,row['module_sha256'],row['function_sha256'],bytes_sha(src)):exact_schedule=False
            pred=call.get('prediction'); error=call.get('error_type'); correct=(exp is not None and not error and pred==exp)
            wrong=bool(not error and pred!=exp)
            if exp is None:score_ok=False
            scores.append({'function':row['function'],'file':row['file'],'case_index':ci,'expected':exp,'prediction':pred,'error_type':error,'abstained':bool(error),'correct':correct,'wrong_return':wrong,'wall_ns':call['wall_ns'],'cpu_ns':call['cpu_ns'],'receipt_delta':call['receipt_delta'],'new_observations':len(call['new_observations']),'new_axis_count':call['new_axis_count']})
        summaries.append({'replicate':run.get('replicate'),'primary_cases':len(scores),'exact_correct':sum(x['correct'] for x in scores),'predictions':sum(not x['abstained'] for x in scores),'abstentions':sum(x['abstained'] for x in scores),'wrong_returns':sum(x['wrong_return'] for x in scores),'median_wall_ns':sorted(x['wall_ns'] for x in scores)[len(scores)//2] if scores else None,'p95_wall_ns':sorted(x['wall_ns'] for x in scores)[int(.95*len(scores))] if scores else None,'median_cpu_ns':sorted(x['cpu_ns'] for x in scores)[len(scores)//2] if scores else None,'p95_cpu_ns':sorted(x['cpu_ns'] for x in scores)[int(.95*len(scores))] if scores else None,'receipt_count':sum(x['receipt_delta'] for x in scores),'observation_count':sum(x['new_observations'] for x in scores),'minted_axis_observation_count':sum(x['new_axis_count'] for x in scores),'boot_loaded':run['boot']['loaded'],'boot_total':run['boot']['total'],'boot_failures':len(run['boot']['failed']),'peak_rss_bytes':run['runtime']['peak_rss_bytes'],'case_results':scores})
    parity=len(outcome_maps)==2 and all((outcome_maps[0].get((fi,ci),{}).get('prediction'),outcome_maps[0].get((fi,ci),{}).get('error_type'))==(outcome_maps[1].get((fi,ci),{}).get('prediction'),outcome_maps[1].get((fi,ci),{}).get('error_type')) for fi,ci,_,_,_ in tasks)
    checks={'independent_frame_reconstruction':frame==expected,'nonempty_frozen_selection':len(expected['selected'])>0,'selected_functions_below_cap':len(expected['selected'])<=24,'oracle_error_free':not oracle_fail,'two_fresh_workers':len(runs)==2 and len({r.get('pid') for r in runs})==2,'stable_source_locks':raw.get('post_run_inputs')==base and all(r.get('source_stable') and r.get('locked_inputs_before')==base==r.get('locked_inputs_after') for r in runs),'complete_exact_schedule_and_hashes':exact_schedule,'worker_parity':parity,'manifest_console_capture_valid':manifest.get('manifest_schema')=='substrate-run-manifest-v1' and manifest.get('exit_status')==0 and bool(log) and len(log)==cap.get('bytes') and hashlib.sha256(log).hexdigest()==cap.get('sha256') and all(f'completed=worker{i} rc=0'.encode() in log for i in (0,1)),'workers_succeeded':all(r.get('worker_returncode')==0 and r.get('boot',{}).get('loaded',0)>0 for r in runs),'no_wrong_return_values':all(s['wrong_returns']==0 for s in summaries),'candidate_source_matches_frame':all(t[2]['module_sha256']==bytes_sha(CORPUS/t[2]['file']) for t in tasks)}
    result={'schema':'code-module-heldout-analysis-v1.1','checks':checks,'pass':all(checks.values()),'summary':{'module_inventory_count':len(frame.get('corpus_inventory',[])),'sampled_module_count':len(frame.get('module_sample',[])),'eligible_function_count':frame.get('eligible_function_count'),'selected_function_count':len(frame.get('selected',[])),'case_count_per_function':9,'total_cases':len(tasks),'oracle_errors':oracle_fail,'claim_boundary':raw.get('claim_boundary'),'workers':summaries}}
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'analysis':OUT.relative_to(ROOT).as_posix(),'pass':result['pass'],'checks':checks,'selected':len(frame.get('selected',[])),'cases':len(tasks)},indent=2,sort_keys=True))
    if not result['pass']:raise SystemExit('module-heldout analysis failed')
if __name__=='__main__':main()
