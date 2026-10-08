#!/usr/bin/env python3
"""Independent source-AST oracle and exact-output audit."""
from __future__ import annotations
import ast,hashlib,json,operator,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/"data/think_python_2e"
FRAME=ROOT/"evaluation/reports/thinkpython_code_prediction_frame_v1_20260927.json"
RAW=ROOT/"evaluation/reports/thinkpython_code_prediction_panel_v1_20260927.json"
BLOCK=re.compile(r"```(?:python)?\s*\n(.*?)\n```",re.S|re.I)
EXPR=(ast.BinOp,ast.UnaryOp,ast.BoolOp,ast.Compare,ast.IfExp,ast.Name,ast.Load,ast.Constant,ast.Add,ast.Sub,ast.Mult,ast.Div,ast.FloorDiv,ast.Mod,ast.Pow,ast.USub,ast.UAdd,ast.Not,ast.And,ast.Or,ast.Eq,ast.NotEq,ast.Lt,ast.LtE,ast.Gt,ast.GtE,ast.Call,ast.Tuple,ast.List,ast.keyword)
CALLS={"abs":abs,"min":min,"max":max,"sum":sum,"len":len,"round":round}
OPS={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv,ast.FloorDiv:operator.floordiv,ast.Mod:operator.mod,ast.Pow:operator.pow,
 ast.Eq:operator.eq,ast.NotEq:operator.ne,ast.Lt:operator.lt,ast.LtE:operator.le,ast.Gt:operator.gt,ast.GtE:operator.ge}
CASES={("x1","y1","x2","y2"):[{"x1":0,"y1":0,"x2":3,"y2":4},{"x1":-2,"y1":4,"x2":1,"y2":0}],
 ("x","y"):[{"x":6,"y":3},{"x":7,"y":2},{"x":-8,"y":4}],("t",):[{"t":[1,3,2]},{"t":[-2,5,0]}],
 ("hist",):[{"hist":{"a":2,"b":1}},{"hist":{}}]}
def sha(b):return hashlib.sha256(b).hexdigest()
def candidate_rows():
 rows=[]
 for p in sorted(DATA.glob("ch*.txt")):
  text=p.read_text(encoding="utf-8")
  for i,m in enumerate(BLOCK.finditer(text)):
   src=m.group(1)
   try:tree=ast.parse(src)
   except SyntaxError:continue
   fn=next((n for n in tree.body if isinstance(n,ast.FunctionDef)),None)
   if fn is None or tuple(a.arg for a in fn.args.args) not in CASES or len(fn.body)!=1 or not isinstance(fn.body[0],ast.Return) or fn.body[0].value is None:continue
   expr=fn.body[0].value
   if not all(isinstance(n,EXPR) for n in ast.walk(expr)):continue
   if any(not isinstance(n.func,ast.Name) or n.func.id not in CALLS for n in ast.walk(expr) if isinstance(n,ast.Call)):continue
   ident=[p.name,i];rows.append({"id":ident,"chapter":p.name,"block_index":i,"function":fn.name,"args":[a.arg for a in fn.args.args],
    "source_sha256":sha(src.encode()),"selection_rank":sha(json.dumps(ident,separators=(",",":")).encode()),"input_cases":CASES[tuple(a.arg for a in fn.args.args)]})
 return sorted(rows,key=lambda r:(r["selection_rank"],r["chapter"],r["block_index"]))
def norm(x):
 if isinstance(x,tuple):v=[norm(y) for y in x]
 elif isinstance(x,list):v=[norm(y) for y in x]
 elif isinstance(x,dict):v={str(k):norm(y) for k,y in sorted(x.items(),key=lambda z:str(z[0]))}
 elif x is None or isinstance(x,(bool,int,float,str)):v=x
 else:raise TypeError(type(x).__name__)
 return {"type":type(x).__name__,"value":v}
def ev(n,env):
 if isinstance(n,ast.Constant):return n.value
 if isinstance(n,ast.Name):return env[n.id]
 if isinstance(n,ast.Tuple):return tuple(ev(x,env) for x in n.elts)
 if isinstance(n,ast.List):return [ev(x,env) for x in n.elts]
 if isinstance(n,ast.BinOp):return OPS[type(n.op)](ev(n.left,env),ev(n.right,env))
 if isinstance(n,ast.UnaryOp):return {ast.UAdd:operator.pos,ast.USub:operator.neg,ast.Not:operator.not_}[type(n.op)](ev(n.operand,env))
 if isinstance(n,ast.BoolOp):
  value=ev(n.values[0],env)
  for x in n.values[1:]:
   if isinstance(n.op,ast.And) and not value:return value
   if isinstance(n.op,ast.Or) and value:return value
   value=ev(x,env)
  return value
 if isinstance(n,ast.IfExp):return ev(n.body if ev(n.test,env) else n.orelse,env)
 if isinstance(n,ast.Compare):
  left=ev(n.left,env)
  for op,rightnode in zip(n.ops,n.comparators):
   right=ev(rightnode,env)
   if not OPS[type(op)](left,right):return False
   left=right
  return True
 if isinstance(n,ast.Call):return CALLS[n.func.id](*(ev(x,env) for x in n.args))
 raise TypeError("oracle AST node outside frozen whitelist: "+type(n).__name__)
def oracle(src,fn_name,args):
 tree=ast.parse(src);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==fn_name)
 env=dict(args)
 return norm(ev(fn.body[0].value,env))
def main():
 frame=json.loads(FRAME.read_text());raw=json.loads(RAW.read_text());rows=candidate_rows()
 checks={"four_static_candidates":len(rows)==4,"frame_equals_independent_selection":frame.get("selected")==rows and frame.get("candidate_count")==len(rows),
  "nine_fixed_cases":sum(len(r["input_cases"]) for r in rows)==9,"two_workers":len(raw.get("runs",[]))==2,
  "unique_worker_pids":len({r.get("pid") for r in raw.get("runs",[])})==2,
  "worker_call_counts":all(len(r.get("calls",[]))==9 for r in raw.get("runs",[])),
  "worker_locks_stable":all(r.get("source_stable") and r.get("locked_inputs_before")==raw.get("locked_inputs")==r.get("locked_inputs_after") for r in raw.get("runs",[])),
  "parent_lock_stable":raw.get("post_run_inputs")==raw.get("locked_inputs"),
  "workers_succeeded":all(r.get("worker_returncode")==0 and r.get("boot",{}).get("loaded",0)>0 for r in raw.get("runs",[])),
  "source_hash_and_schedule":all(c["sample_id"]==rows[c["function_index"]]["id"] and c["source_sha256_expected"]==c["source_sha256_observed"]==rows[c["function_index"]]["source_sha256"] and c["args"]==rows[c["function_index"]]["input_cases"][c["case_index"]] for r in raw.get("runs",[]) for c in r.get("calls",[])),
  "schedule_parity":len(raw.get("runs",[]))==2 and [[(c["sample_id"],c["case_index"],c["prediction"],c["error_type"]) for c in r["calls"]] for r in raw["runs"]][0]==[(c["sample_id"],c["case_index"],c["prediction"],c["error_type"]) for c in raw["runs"][1]["calls"]]}
 expected=[];case_results=[]
 for fi,row in enumerate(rows):
  src=list(BLOCK.finditer((DATA/row["chapter"]).read_text(encoding="utf-8")))[row["block_index"]].group(1)
  for ci,args in enumerate(row["input_cases"]):
   val=oracle(src,row["function"],args);expected.append(val);case_results.append((fi,ci,val))
 oracle_errors=[];scored=[]
 for run in raw.get("runs",[]):
  by={(c["function_index"],c["case_index"]):c for c in run["calls"]};out=[]
  for fi,ci,want in case_results:
   c=by[(fi,ci)];correct=(not c["abstained"] and c["prediction"]==want)
   out.append({"function":rows[fi]["function"],"case_index":ci,"expected":want,
      "prediction":c["prediction"],"abstained":c["abstained"],"correct":correct,"error_type":c["error_type"],"wall_ns":c["wall_ns"],"cpu_ns":c["cpu_ns"]})
  pred=[x for x in out if not x["abstained"]];scored.append({"replicate":run["replicate"],"cases":len(out),
    "correct":sum(x["correct"] for x in out),"predictions":len(pred),"abstentions":len(out)-len(pred),
    "coverage":len(pred)/len(out),"accuracy_all_cases":sum(x["correct"] for x in out)/len(out),
    "accuracy_when_predicted":sum(x["correct"] for x in pred)/len(pred) if pred else None,
    "boot_loaded":run["boot"]["loaded"],"boot_total":run["boot"]["total"],"boot_failures":len(run["boot"]["failed"]),
    "boot_wall_ns":run["boot"]["wall_ns"],"peak_rss_bytes":run["runtime"]["peak_rss_bytes"],"case_results":out})
 checks["independent_oracle_all_cases"]=(len(expected)==9 and not oracle_errors)
 checks["two_worker_results_identical"]=len(scored)==2 and [(x["prediction"],x["correct"],x["abstained"]) for x in scored[0]["case_results"]]==[(x["prediction"],x["correct"],x["abstained"]) for x in scored[1]["case_results"]]
 result={"checks":checks,"pass":all(checks.values()),"summary":{"claim_boundary":raw.get("claim_boundary"),"case_count":9,"functions":[{"id":r["id"],"function":r["function"],"input_count":len(r["input_cases"])} for r in rows],"workers":scored}}
 print(json.dumps(result,indent=2,sort_keys=True))
 if not result["pass"]:raise SystemExit("prediction analysis failed")
if __name__=="__main__":main()
