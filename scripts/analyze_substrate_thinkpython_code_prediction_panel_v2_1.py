#!/usr/bin/env python3
"""Independent selector reconstruction, bounded interpreter, and scorer."""
from __future__ import annotations
import ast,hashlib,json,operator,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/"data/think_python_2e"
FRAME=ROOT/"evaluation/reports/thinkpython_code_prediction_frame_v2_1_20260927.json"
RAW=ROOT/"evaluation/reports/thinkpython_code_prediction_panel_v2_1_20260927.json"
BLOCK=re.compile(r"```(?:python)?\s*\n(.*?)\n```",re.S|re.I)
CALLS={"abs":abs,"min":min,"max":max,"sum":sum,"len":len,"round":round,"all":all,"any":any,"sorted":sorted}
EXPR=(ast.Name,ast.Load,ast.Store,ast.Constant,ast.BinOp,ast.UnaryOp,ast.BoolOp,ast.Compare,ast.IfExp,ast.Call,ast.List,ast.Tuple,ast.Subscript,ast.Slice,
 ast.Add,ast.Sub,ast.Mult,ast.Div,ast.FloorDiv,ast.Mod,ast.Pow,ast.USub,ast.UAdd,ast.Not,ast.And,ast.Or,ast.Eq,ast.NotEq,ast.Lt,ast.LtE,ast.Gt,ast.GtE,ast.In,ast.NotIn,ast.Is,ast.IsNot,ast.keyword,ast.BitAnd,ast.BitOr,ast.BitXor,ast.LShift,ast.RShift,ast.Invert)
STMT=(ast.Return,ast.Assign,ast.AugAssign,ast.For,ast.If,ast.Pass)
CASES={("x",):[{"x":-4},{"x":0}],("n",):[{"n":0},{"n":4}],("x","y"):[{"x":6,"y":3},{"x":7,"y":2}],
 ("x1","y1","x2","y2"):[{"x1":0,"y1":0,"x2":3,"y2":4},{"x1":-2,"y1":4,"x2":1,"y2":0}],
 ("word",):[{"word":"alphabet"},{"word":"xyz"}],("word","forbidden"):[{"word":"abcde","forbidden":"xyz"},{"word":"axc","forbidden":"x"}],
 ("word","available"):[{"word":"abc","available":"abc"},{"word":"dax","available":"ax"}],("word","required"):[{"word":"abc","required":"ac"},{"word":"ax","required":"xyz"}],
 ("t",):[{"t":[1,3,2]},{"t":[4,5]}],("hist",):[{"hist":{"a":2,"b":1}},{"hist":{}}],
 ("prefix","word"):[{"prefix":{"$tuple":["p","q","r"]},"word":"fix"},{"prefix":{"$tuple":["a"]},"word":"bc"}]}
BIN={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv,ast.FloorDiv:operator.floordiv,ast.Mod:operator.mod,ast.Pow:operator.pow,ast.BitAnd:operator.and_,ast.BitOr:operator.or_,ast.BitXor:operator.xor,ast.LShift:operator.lshift,ast.RShift:operator.rshift}
CMP={ast.Eq:operator.eq,ast.NotEq:operator.ne,ast.Lt:operator.lt,ast.LtE:operator.le,ast.Gt:operator.gt,ast.GtE:operator.ge,ast.In:lambda a,b:a in b,ast.NotIn:lambda a,b:a not in b,ast.Is:operator.is_,ast.IsNot:operator.is_not}
def sha(b):return hashlib.sha256(b).hexdigest()
def expr_ok(n):
 if not isinstance(n,EXPR):return False
 if isinstance(n,ast.Call) and (not isinstance(n.func,ast.Name) or n.func.id not in set(CALLS)|{"range"} or n.keywords):return False
 return all(expr_ok(c) for c in ast.iter_child_nodes(n))
def stmt_ok(s):
 if not isinstance(s,STMT):return False
 if isinstance(s,ast.Assign):return len(s.targets)==1 and isinstance(s.targets[0],ast.Name) and expr_ok(s.value)
 if isinstance(s,ast.AugAssign):return isinstance(s.target,ast.Name) and expr_ok(s.op) and expr_ok(s.value)
 if isinstance(s,ast.Return):return s.value is None or expr_ok(s.value)
 if isinstance(s,ast.For):return isinstance(s.target,ast.Name) and expr_ok(s.iter) and all(stmt_ok(x) for x in s.body+s.orelse)
 if isinstance(s,ast.If):return expr_ok(s.test) and all(stmt_ok(x) for x in s.body+s.orelse)
 return isinstance(s,ast.Pass)
def input_cases(fn):return CASES.get(tuple(a.arg for a in fn.args.args))
def candidates():
 rows=[]
 for p in sorted(DATA.glob("ch*.txt")):
  text=p.read_text(encoding="utf-8")
  for i,m in enumerate(BLOCK.finditer(text)):
   src=m.group(1)
   try:tree=ast.parse(src)
   except SyntaxError:continue
   fn=next((n for n in tree.body if isinstance(n,ast.FunctionDef)),None)
   if fn is None or input_cases(fn) is None or not any(isinstance(n,ast.Return) for n in ast.walk(fn)) or not all(stmt_ok(s) for s in fn.body):continue
   if any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id==fn.name for n in ast.walk(fn)):continue
   ident=[p.name,i];rows.append({"id":ident,"chapter":p.name,"block_index":i,"function":fn.name,"args":[a.arg for a in fn.args.args],"source_sha256":sha(src.encode()),"selection_rank":sha(json.dumps(ident,separators=(",",":")).encode()),"input_cases":input_cases(fn)})
 return sorted(rows,key=lambda r:(r["selection_rank"],r["chapter"],r["block_index"]))
class ReturnSignal(Exception):
 def __init__(self,value):self.value=value
class Interpreter:
 def __init__(self):self.steps=0
 def tick(self):
  self.steps+=1
  if self.steps>2048:raise RuntimeError("oracle step cap")
 def guard(self,x):
  if isinstance(x,int) and x.bit_length()>1024:raise RuntimeError("oracle integer cap")
  if isinstance(x,(str,list,tuple,dict)) and len(x)>256:raise RuntimeError("oracle container cap")
  return x
 def expr(self,n,e):
  self.tick()
  if isinstance(n,ast.Constant):v=n.value
  elif isinstance(n,ast.Name):v=e[n.id]
  elif isinstance(n,ast.Tuple):v=tuple(self.expr(x,e) for x in n.elts)
  elif isinstance(n,ast.List):v=[self.expr(x,e) for x in n.elts]
  elif isinstance(n,ast.BinOp):v=BIN[type(n.op)](self.expr(n.left,e),self.expr(n.right,e))
  elif isinstance(n,ast.UnaryOp):v={ast.UAdd:operator.pos,ast.USub:operator.neg,ast.Not:operator.not_,ast.Invert:operator.invert}[type(n.op)](self.expr(n.operand,e))
  elif isinstance(n,ast.BoolOp):
   v=self.expr(n.values[0],e)
   for x in n.values[1:]:
    if isinstance(n.op,ast.And) and not v:break
    if isinstance(n.op,ast.Or) and v:break
    v=self.expr(x,e)
  elif isinstance(n,ast.Compare):
   left=self.expr(n.left,e);v=True
   for op,rn in zip(n.ops,n.comparators):
    right=self.expr(rn,e)
    if not CMP[type(op)](left,right):v=False;break
    left=right
  elif isinstance(n,ast.IfExp):v=self.expr(n.body if self.expr(n.test,e) else n.orelse,e)
  elif isinstance(n,ast.Subscript):v=self.expr(n.value,e)[self.expr(n.slice,e)]
  elif isinstance(n,ast.Slice):v=slice(self.expr(n.lower,e) if n.lower else None,self.expr(n.upper,e) if n.upper else None,self.expr(n.step,e) if n.step else None)
  elif isinstance(n,ast.Call):
   name=n.func.id;args=[self.expr(x,e) for x in n.args]
   if name=="range":
    r=range(*args)
    if len(r)>32:raise RuntimeError("oracle range cap")
    v=list(r)
   else:v=CALLS[name](*args)
  else:raise TypeError("unsupported oracle expression: "+type(n).__name__)
  return self.guard(v)
 def suite(self,ss,e):
  for s in ss:
   self.tick()
   if isinstance(s,ast.Return):raise ReturnSignal(self.expr(s.value,e) if s.value else None)
   if isinstance(s,ast.Assign):e[s.targets[0].id]=self.expr(s.value,e)
   elif isinstance(s,ast.AugAssign):
    fn=BIN.get(type(s.op))
    if fn is None:raise TypeError("unsupported augmented operator")
    e[s.target.id]=self.guard(fn(e[s.target.id],self.expr(s.value,e)))
   elif isinstance(s,ast.If):
    branch=s.body if self.expr(s.test,e) else s.orelse
    self.suite(branch,e)
   elif isinstance(s,ast.For):
    it=self.expr(s.iter,e)
    if len(it)>32:raise RuntimeError("oracle loop cap")
    for item in it:
     e[s.target.id]=item;self.suite(s.body,e)
    self.suite(s.orelse,e)
   elif not isinstance(s,ast.Pass):raise TypeError("unsupported oracle statement")
 def run(self,src,name,args):
  tree=ast.parse(src);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
  e=dict(args)
  try:self.suite(fn.body,e)
  except ReturnSignal as r:return r.value
  return None
def norm(x):
 if isinstance(x,tuple):v=[norm(y) for y in x]
 elif isinstance(x,list):v=[norm(y) for y in x]
 elif isinstance(x,dict):v={str(k):norm(y) for k,y in sorted(x.items(),key=lambda z:str(z[0]))}
 elif x is None or isinstance(x,(bool,int,float,str)):v=x
 else:raise TypeError(type(x).__name__)
 return {"type":type(x).__name__,"value":v}
def decode_input(x):
 if isinstance(x,dict) and set(x)=={"$tuple"}:return tuple(decode_input(v) for v in x["$tuple"])
 if isinstance(x,dict):return {k:decode_input(v) for k,v in x.items()}
 if isinstance(x,list):return [decode_input(v) for v in x]
 return x
def main():
 frame=json.loads(FRAME.read_text());raw=json.loads(RAW.read_text());rows=candidates()
 checks={"eligible_count_18":len(rows)==18,"frame_independent_reconstruction":frame.get("candidate_count")==len(rows) and frame.get("selected")==rows,
  "fixed_case_count_36":sum(len(r["input_cases"]) for r in rows)==36,"two_workers":len(raw.get("runs",[]))==2,"distinct_pids":len({r.get("pid") for r in raw.get("runs",[])})==2,
  "all_rows_each":all(len(r.get("calls",[]))==36 for r in raw.get("runs",[])),"worker_locks_stable":all(r.get("source_stable") and r.get("locked_inputs_before")==raw.get("locked_inputs")==r.get("locked_inputs_after") for r in raw.get("runs",[])),
  "parent_lock_stable":raw.get("post_run_inputs")==raw.get("locked_inputs"),"workers_succeeded":all(r.get("worker_returncode")==0 and r.get("boot",{}).get("loaded",0)>0 for r in raw.get("runs",[])),
  "hash_schedule_arguments_match":all(c["function_index"]<len(rows) and c["sample_id"]==rows[c["function_index"]]["id"] and c["source_sha256_expected"]==c["source_sha256_observed"]==rows[c["function_index"]]["source_sha256"] and c["args"]==rows[c["function_index"]]["input_cases"][c["case_index"]] for r in raw.get("runs",[]) for c in r.get("calls",[]))}
 expected=[];oracle_err=[]
 for fi,row in enumerate(rows):
  src=list(BLOCK.finditer((DATA/row["chapter"]).read_text(encoding="utf-8")))[row["block_index"]].group(1)
  for ci,args in enumerate(row["input_cases"]):
   try:v=norm(Interpreter().run(src,row["function"],decode_input(args)));expected.append((fi,ci,v,None))
   except Exception as ex:oracle_err.append((fi,ci,type(ex).__name__));expected.append((fi,ci,None,type(ex).__name__))
 checks["oracle_type_compatible_all_cases"]=(len(expected)==36 and not oracle_err)
 scored=[]
 for run in raw.get("runs",[]):
  by={(c["function_index"],c["case_index"]):c for c in run["calls"]};case_rows=[]
  for fi,ci,want,oracle_error in expected:
   c=by[(fi,ci)];correct=oracle_error is None and not c["abstained"] and c["prediction"]==want
   case_rows.append({"function":rows[fi]["function"],"sample_id":rows[fi]["id"],"case_index":ci,"expected":want,"prediction":c["prediction"],"abstained":c["abstained"],"error_type":c["error_type"],"correct":correct,"oracle_error":oracle_error,"wall_ns":c["wall_ns"],"cpu_ns":c["cpu_ns"],"receipt_delta":c["receipt_delta"],"minted_observation_count":sum(bool(o["minted_axis_ids"]) for o in c["new_observations"])})
  pred=[c for c in case_rows if not c["abstained"]]
  byfn={}
  for c in case_rows:
   x=byfn.setdefault(c["function"],{"cases":0,"predictions":0,"abstentions":0,"correct":0})
   x["cases"]+=1;x["predictions"]+=not c["abstained"];x["abstentions"]+=c["abstained"];x["correct"]+=c["correct"]
  scored.append({"replicate":run["replicate"],"case_count":len(case_rows),"correct":sum(c["correct"] for c in case_rows),"predictions":len(pred),"abstentions":len(case_rows)-len(pred),"coverage":len(pred)/len(case_rows),"accuracy_all_cases":sum(c["correct"] for c in case_rows)/len(case_rows),"accuracy_when_predicted":sum(c["correct"] for c in pred)/len(pred) if pred else None,"by_function":byfn,"receipt_count":sum(c["receipt_delta"] for c in case_rows),"minted_observation_count":sum(c["minted_observation_count"] for c in case_rows),"boot_loaded":run["boot"]["loaded"],"boot_total":run["boot"]["total"],"boot_failures":len(run["boot"]["failed"]),"boot_wall_ns":run["boot"]["wall_ns"],"peak_rss_bytes":run["runtime"]["peak_rss_bytes"],"case_results":case_rows})
 checks["worker_prediction_parity"]=len(scored)==2 and [(c["prediction"],c["error_type"]) for c in scored[0]["case_results"]]==[(c["prediction"],c["error_type"]) for c in scored[1]["case_results"]]
 result={"checks":checks,"pass":all(checks.values()),"summary":{"candidate_count":len(rows),"case_count":sum(len(r["input_cases"]) for r in rows),"claim_boundary":raw.get("claim_boundary"),"workers":scored}}
 print(json.dumps(result,indent=2,sort_keys=True))
 if not result["pass"]:raise SystemExit("prediction panel v2 analysis failed")
if __name__=="__main__":main()
