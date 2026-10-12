#!/usr/bin/env python3
"""AST-shape census and fixed-case selector for Stacks string predicates."""
from __future__ import annotations
import ast, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data/stacks/repo/scripts/functions.py"
def sha(b): return hashlib.sha256(b).hexdigest()
def marker_test(node):
    if not (isinstance(node,ast.Compare) and len(node.ops)==1 and len(node.comparators)==1): return None
    left,right=node.left,node.comparators[0]
    if not isinstance(left,ast.Name) or left.id!="n" or not isinstance(right,ast.Constant) or right.value!=0: return None
    op=node.ops[0]
    if isinstance(op,ast.Eq): return "eq0"
    if isinstance(op,ast.Lt): return "lt0"
    return None
def row_for(fn,text,raw):
    if len(fn.args.args)!=1 or fn.args.vararg or fn.args.kwarg or fn.args.kwonlyargs: return None
    arg=fn.args.args[0].arg
    body=fn.body
    if len(body)!=3 or not isinstance(body[0],ast.Assign) or len(body[0].targets)!=1 or not isinstance(body[0].targets[0],ast.Name) or body[0].targets[0].id!="n": return None
    call=body[0].value
    if not (isinstance(call,ast.Call) and len(call.args)==1 and not call.keywords and isinstance(call.func,ast.Attribute) and call.func.attr=="find" and isinstance(call.func.value,ast.Name) and call.func.value.id==arg and isinstance(call.args[0],ast.Constant) and isinstance(call.args[0].value,str)): return None
    if not isinstance(body[1],ast.If) or body[1].orelse or len(body[1].body)!=1 or not isinstance(body[1].body[0],ast.Return): return None
    comparison=marker_test(body[1].test)
    if comparison is None: return None
    early=body[1].body[0].value; tail=body[2]
    if not isinstance(early,ast.Constant) or type(early.value) is not int or early.value not in (0,1) or not isinstance(tail,ast.Return) or not isinstance(tail.value,ast.Constant) or type(tail.value.value) is not int or tail.value.value not in (0,1): return None
    marker=call.args[0].value
    if comparison=="lt0": vals=[marker+" body", "prefix "+marker+" body", "plain body", marker+" "+marker]
    else: vals=[marker+" body", "prefix "+marker+" body", "plain body", " "+marker+" body"]
    segment=ast.get_source_segment(text,fn)
    return {"file":DATA.relative_to(ROOT).as_posix(),"module_sha256":sha(raw),"function":fn.name,"line":fn.lineno,
      "function_sha256":sha(segment.encode()),"argument":arg,"marker_sha256":sha(marker.encode()),"comparison":comparison,
      "input_cases":[{arg:x} for x in vals]}
def candidates():
    raw=DATA.read_bytes(); text=raw.decode("utf-8"); tree=ast.parse(text,filename=DATA.name)
    rows=[r for n in tree.body if isinstance(n,ast.FunctionDef) if (r:=row_for(n,text,raw)) is not None]
    return sorted(rows,key=lambda r:r["function"])
if __name__=="__main__":
    rows=candidates(); print(json.dumps({"schema_version":1,"candidate_count":len(rows),"selected":rows},indent=2,sort_keys=True))
