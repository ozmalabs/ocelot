#!/usr/bin/env python3
"""Outcome-blind safe-AST frame for broadened Think Python predictions."""
from __future__ import annotations
import ast,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/"data/think_python_2e"
OUT=ROOT/"evaluation/reports/thinkpython_code_prediction_frame_v2_1_20260927.json"
BLOCK=re.compile(r"```(?:python)?\s*\n(.*?)\n```",re.S|re.I)
CALLS={"abs","min","max","sum","len","round","all","any","sorted","range"}
EXPR=(ast.Name,ast.Load,ast.Store,ast.Constant,ast.BinOp,ast.UnaryOp,ast.BoolOp,ast.Compare,ast.IfExp,ast.Call,
 ast.List,ast.Tuple,ast.Subscript,ast.Slice,ast.Add,ast.Sub,ast.Mult,ast.Div,ast.FloorDiv,ast.Mod,ast.Pow,
 ast.USub,ast.UAdd,ast.Not,ast.And,ast.Or,ast.Eq,ast.NotEq,ast.Lt,ast.LtE,ast.Gt,ast.GtE,ast.In,ast.NotIn,
 ast.Is,ast.IsNot,ast.keyword,ast.BitAnd,ast.BitOr,ast.BitXor,ast.LShift,ast.RShift,ast.Invert)
STMT=(ast.Return,ast.Assign,ast.AugAssign,ast.For,ast.If,ast.Pass)
def sha(b):return hashlib.sha256(b).hexdigest()
def expr_ok(n):
 if not isinstance(n,EXPR):return False
 if isinstance(n,ast.Call) and (not isinstance(n.func,ast.Name) or n.func.id not in CALLS or n.keywords):return False
 return all(expr_ok(c) for c in ast.iter_child_nodes(n))
def stmt_ok(s):
 if not isinstance(s,STMT):return False
 if isinstance(s,ast.Assign):return len(s.targets)==1 and isinstance(s.targets[0],ast.Name) and expr_ok(s.value)
 if isinstance(s,ast.AugAssign):return isinstance(s.target,ast.Name) and expr_ok(s.op) and expr_ok(s.value)
 if isinstance(s,ast.Return):return s.value is None or expr_ok(s.value)
 if isinstance(s,ast.For):return isinstance(s.target,ast.Name) and expr_ok(s.iter) and all(stmt_ok(x) for x in s.body+s.orelse)
 if isinstance(s,ast.If):return expr_ok(s.test) and all(stmt_ok(x) for x in s.body+s.orelse)
 return isinstance(s,ast.Pass)
def input_cases(fn):
 sig=tuple(a.arg for a in fn.args.args)
 if sig==("x",):return [{"x":-4},{"x":0}]
 if sig==("n",):return [{"n":0},{"n":4}]
 if sig==("x","y"):return [{"x":6,"y":3},{"x":7,"y":2}]
 if sig==("x1","y1","x2","y2"):return [{"x1":0,"y1":0,"x2":3,"y2":4},{"x1":-2,"y1":4,"x2":1,"y2":0}]
 if sig==("word",):return [{"word":"alphabet"},{"word":"xyz"}]
 if sig==("word","forbidden"):return [{"word":"abcde","forbidden":"xyz"},{"word":"axc","forbidden":"x"}]
 if sig==("word","available"):return [{"word":"abc","available":"abc"},{"word":"dax","available":"ax"}]
 if sig==("word","required"):return [{"word":"abc","required":"ac"},{"word":"ax","required":"xyz"}]
 if sig==("t",):return [{"t":[1,3,2]},{"t":[4,5]}]
 if sig==("hist",):return [{"hist":{"a":2,"b":1}},{"hist":{}}]
 if sig==("prefix","word"):return [{"prefix":{"$tuple":["p","q","r"]},"word":"fix"},{"prefix":{"$tuple":["a"]},"word":"bc"}]
 return None
def main():
 rows=[]
 for p in sorted(DATA.glob("ch*.txt")):
  text=p.read_text(encoding="utf-8")
  for i,m in enumerate(BLOCK.finditer(text)):
   src=m.group(1)
   try:tree=ast.parse(src)
   except SyntaxError:continue
   fn=next((n for n in tree.body if isinstance(n,ast.FunctionDef)),None)
   if fn is None or input_cases(fn) is None or not any(isinstance(n,ast.Return) for n in ast.walk(fn)):continue
   if not all(stmt_ok(s) for s in fn.body):continue
   # Recursive/self calls are outside this interpreter's static safety envelope.
   if any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id==fn.name for n in ast.walk(fn)):continue
   ident=[p.name,i]
   rows.append({"id":ident,"chapter":p.name,"block_index":i,"function":fn.name,"args":[a.arg for a in fn.args.args],
     "source_sha256":sha(src.encode()),"selection_rank":sha(json.dumps(ident,separators=(",",":")).encode()),"input_cases":input_cases(fn)})
 rows.sort(key=lambda r:(r["selection_rank"],r["chapter"],r["block_index"]))
 frame={"schema_version":21,"selection_rule":"all fenced examples whose first top-level function has a returned value, is in the frozen bounded statement/expression whitelist, and has a predeclared exact signature; recursive, attribute, import, mutation, while, I/O, and unknown-call functions are excluded; IDs ranked by SHA256(compact JSON)","candidate_count":len(rows),"selected_count":len(rows),"selected":rows}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(frame,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"candidate_count":len(rows),"calls":sum(len(x["input_cases"]) for x in rows),"frame":OUT.relative_to(ROOT).as_posix(),"sha256":sha(OUT.read_bytes())},indent=2))
if __name__=="__main__":main()
