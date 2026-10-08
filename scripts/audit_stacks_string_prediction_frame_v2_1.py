#!/usr/bin/env python3
"""AST-shape census for v2; appends one Unicode-prefix case per function."""
from __future__ import annotations
import ast,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/"data/stacks/repo/scripts/functions.py"
def sha(b):return hashlib.sha256(b).hexdigest()
def candidate(fn,text,raw):
    if len(fn.args.args)!=1 or fn.args.vararg or fn.args.kwarg or fn.args.kwonlyargs:return None
    arg=fn.args.args[0].arg;body=fn.body
    if len(body)!=3 or not isinstance(body[0],ast.Assign) or len(body[0].targets)!=1 or not isinstance(body[0].targets[0],ast.Name) or body[0].targets[0].id!="n":return None
    call=body[0].value
    if not(isinstance(call,ast.Call) and len(call.args)==1 and not call.keywords and isinstance(call.func,ast.Attribute) and call.func.attr=="find" and isinstance(call.func.value,ast.Name) and call.func.value.id==arg and isinstance(call.args[0],ast.Constant) and isinstance(call.args[0].value,str)):return None
    branch=body[1]
    if not(isinstance(branch,ast.If) and not branch.orelse and len(branch.body)==1 and isinstance(branch.body[0],ast.Return)):return None
    test=branch.test
    if not(isinstance(test,ast.Compare) and len(test.ops)==1 and len(test.comparators)==1 and isinstance(test.left,ast.Name) and test.left.id=="n" and isinstance(test.comparators[0],ast.Constant) and test.comparators[0].value==0):return None
    cmp="eq0" if isinstance(test.ops[0],ast.Eq) else "lt0" if isinstance(test.ops[0],ast.Lt) else None
    early=branch.body[0].value;tail=body[2]
    if cmp is None or not(isinstance(early,ast.Constant) and type(early.value)is int and early.value in(0,1) and isinstance(tail,ast.Return) and isinstance(tail.value,ast.Constant) and type(tail.value.value)is int and tail.value.value in(0,1)):return None
    marker=call.args[0].value
    vals=[marker+" body","prefix "+marker+" body","plain body",marker+" "+marker,"é"+marker+" body"] if cmp=="lt0" else [marker+" body","prefix "+marker+" body","plain body"," "+marker+" body","é"+marker+" body"]
    seg=ast.get_source_segment(text,fn)
    return {"file":DATA.relative_to(ROOT).as_posix(),"module_sha256":sha(raw),"function":fn.name,"line":fn.lineno,"function_sha256":sha(seg.encode()),"argument":arg,"marker_sha256":sha(marker.encode()),"comparison":cmp,"input_cases":[{arg:x} for x in vals]}
def candidates():
    raw=DATA.read_bytes();text=raw.decode();tree=ast.parse(text,filename=DATA.name)
    rows=[r for n in tree.body if isinstance(n,ast.FunctionDef) if (r:=candidate(n,text,raw)) is not None]
    return sorted(rows,key=lambda r:r["function"])
if __name__=="__main__":
    rows=candidates();print(json.dumps({"schema_version":2,"candidate_count":len(rows),"selected":rows},indent=2,sort_keys=True))
