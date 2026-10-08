#!/usr/bin/env python3
"""Freeze a safe, hash-selected pure-function prediction probe."""
from __future__ import annotations
import ast, hashlib, json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data/think_python_2e"
OUT=ROOT/"evaluation/reports/thinkpython_code_prediction_frame_v1_20260927.json"
BLOCK=re.compile(r"```(?:python)?\s*\n(.*?)\n```",re.S|re.I)
EXPR=(ast.BinOp,ast.UnaryOp,ast.BoolOp,ast.Compare,ast.IfExp,ast.Name,ast.Load,ast.Constant,
      ast.Add,ast.Sub,ast.Mult,ast.Div,ast.FloorDiv,ast.Mod,ast.Pow,ast.USub,ast.UAdd,ast.Not,
      ast.And,ast.Or,ast.Eq,ast.NotEq,ast.Lt,ast.LtE,ast.Gt,ast.GtE,ast.Call,ast.Tuple,ast.List,ast.keyword)
PURE_NAMES={"abs","min","max","sum","len","round"}
CASES={
    ("x1","y1","x2","y2"):[{"x1":0,"y1":0,"x2":3,"y2":4},{"x1":-2,"y1":4,"x2":1,"y2":0}],
    ("x","y"):[{"x":6,"y":3},{"x":7,"y":2},{"x":-8,"y":4}],
    ("t",):[{"t":[1,3,2]},{"t":[-2,5,0]}],
    ("hist",):[{"hist":{"a":2,"b":1}},{"hist":{}}],
}
def sha(b): return hashlib.sha256(b).hexdigest()
def main():
    rows=[]
    for path in sorted(DATA.glob("ch*.txt")):
        text=path.read_text(encoding="utf-8")
        for i,m in enumerate(BLOCK.finditer(text)):
            src=m.group(1)
            try: tree=ast.parse(src)
            except SyntaxError: continue
            fn=next((n for n in tree.body if isinstance(n,ast.FunctionDef)),None)
            if fn is None or tuple(a.arg for a in fn.args.args) not in CASES: continue
            if len(fn.body)!=1 or not isinstance(fn.body[0],ast.Return) or fn.body[0].value is None: continue
            expr=fn.body[0].value
            if not all(isinstance(n,EXPR) for n in ast.walk(expr)): continue
            if any(not isinstance(n.func,ast.Name) or n.func.id not in PURE_NAMES for n in ast.walk(expr) if isinstance(n,ast.Call)): continue
            ident=[path.name,i]
            rows.append({"id":ident,"chapter":path.name,"block_index":i,"function":fn.name,
                "args":[a.arg for a in fn.args.args],"source_sha256":sha(src.encode()),
                "selection_rank":sha(json.dumps(ident,separators=(",",":")).encode()),
                "input_cases":CASES[tuple(a.arg for a in fn.args.args)]})
    rows.sort(key=lambda r:(r["selection_rank"],r["chapter"],r["block_index"]))
    frame={"schema_version":1,"selection_rule":"first top-level function in a fenced code block, one return expression in a statically whitelisted pure AST grammar, exact declared argument signature; rank by SHA256(compact JSON [chapter, block_index])",
        "candidate_count":len(rows),"selected_count":len(rows),"selected":rows}
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(frame,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"candidate_count":len(rows),"frame":OUT.relative_to(ROOT).as_posix(),"sha256":sha(OUT.read_bytes())},indent=2))
if __name__=="__main__":main()
