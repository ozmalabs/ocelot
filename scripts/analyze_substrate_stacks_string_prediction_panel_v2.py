#!/usr/bin/env python3
"""Independent AST reconstruction, bounded oracle, and scorer."""
from __future__ import annotations
import ast,hashlib,json
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SOURCE=ROOT/"data/stacks/repo/scripts/functions.py"
TPDATA=ROOT/"data/think_python_2e";BLOCK=re.compile(r"```(?:python)?\s*\n(.*?)\n```",re.S|re.I)
FRAME=ROOT/"evaluation/reports/stacks_string_prediction_frame_v2_20260927.json"
RAW=ROOT/"evaluation/reports/stacks_string_prediction_panel_v2_20260927.json"
BASE_RAW=ROOT/"evaluation/reports/stacks_string_prediction_panel_v1_20260927.json"
BASE_ANALYSIS=ROOT/"evaluation/reports/stacks_string_prediction_panel_v1_analysis_20260927.json"
BASE_FRAME=ROOT/"evaluation/reports/stacks_string_prediction_frame_v1_20260927.json"
BASE_HASHES={"raw":"7805756c4bace58b64033fa71a54f07d47d48162f36cca947a752d35d050bb4e","analysis":"d8a2a350743d3b427e1e245db254625417e7bee70ef9b720f39dda37432f9033","frame":"5b35d14054401e6dd1f749a95f43ee0c58c0b90f9af36d1292ed51bbb8d5873d"}
def sha(b):return hashlib.sha256(b).hexdigest()
def candidates():
    raw=SOURCE.read_bytes();text=raw.decode();tree=ast.parse(text);out=[]
    for fn in tree.body:
      if not isinstance(fn,ast.FunctionDef) or len(fn.args.args)!=1 or fn.args.vararg or fn.args.kwarg or fn.args.kwonlyargs or len(fn.body)!=3:continue
      arg=fn.args.args[0].arg;ass,branch,tail=fn.body
      if not (isinstance(ass,ast.Assign) and len(ass.targets)==1 and isinstance(ass.targets[0],ast.Name) and ass.targets[0].id=="n"):continue
      call=ass.value
      if not (isinstance(call,ast.Call) and len(call.args)==1 and not call.keywords and isinstance(call.func,ast.Attribute) and call.func.attr=="find" and isinstance(call.func.value,ast.Name) and call.func.value.id==arg and isinstance(call.args[0],ast.Constant) and isinstance(call.args[0].value,str)):continue
      test=branch.test if isinstance(branch,ast.If) else None
      if not (isinstance(branch,ast.If) and not branch.orelse and len(branch.body)==1 and isinstance(branch.body[0],ast.Return) and isinstance(test,ast.Compare) and len(test.ops)==1 and len(test.comparators)==1 and isinstance(test.left,ast.Name) and test.left.id=="n" and isinstance(test.comparators[0],ast.Constant) and test.comparators[0].value==0):continue
      cmp="eq0" if isinstance(test.ops[0],ast.Eq) else "lt0" if isinstance(test.ops[0],ast.Lt) else None
      early=branch.body[0].value
      if cmp is None or not (isinstance(early,ast.Constant) and type(early.value)is int and early.value in (0,1) and isinstance(tail,ast.Return) and isinstance(tail.value,ast.Constant) and type(tail.value.value)is int and tail.value.value in (0,1)):continue
      marker=call.args[0].value;cases=[marker+" body","prefix "+marker+" body","plain body",marker+" "+marker,"é"+marker+" body"] if cmp=="lt0" else [marker+" body","prefix "+marker+" body","plain body"," "+marker+" body","é"+marker+" body"]
      segment=ast.get_source_segment(text,fn)
      out.append({"file":SOURCE.relative_to(ROOT).as_posix(),"module_sha256":sha(raw),"function":fn.name,"line":fn.lineno,"function_sha256":sha(segment.encode()),"argument":arg,"marker_sha256":sha(marker.encode()),"comparison":cmp,"input_cases":[{arg:x} for x in cases]})
    return sorted(out,key=lambda r:r["function"])
def positive_control():
    chapter="ch06_thinkpython2007.txt";block_index=17;path=TPDATA/chapter;raw=path.read_bytes();text=raw.decode();snippet=list(BLOCK.finditer(text))[block_index].group(1)
    fn=next(n for n in ast.parse(snippet).body if isinstance(n,ast.FunctionDef))
    return {"chapter":chapter,"block_index":block_index,"function":fn.name,"args":[a.arg for a in fn.args.args],"source_sha256":sha(snippet.encode()),"file_sha256":sha(raw),"input_cases":[{"x":6,"y":3},{"x":7,"y":2}]}
class Return(Exception):
    def __init__(self,value):self.value=value
def oracle(src,name,args):
    fn=next(n for n in ast.parse(src).body if isinstance(n,ast.FunctionDef) and n.name==name);env=dict(args)
    def ev(node):
      if isinstance(node,ast.Constant):return node.value
      if isinstance(node,ast.Name):return env[node.id]
      if isinstance(node,ast.BinOp) and type(node.op)is ast.Mod:return ev(node.left)%ev(node.right)
      if isinstance(node,ast.Call) and not node.keywords and len(node.args)==1 and isinstance(node.func,ast.Attribute) and node.func.attr=="find":
        obj=ev(node.func.value);needle=ev(node.args[0])
        if type(obj)is str and type(needle)is str:return obj.find(needle)
      if isinstance(node,ast.Compare) and len(node.ops)==1:
        a=ev(node.left);b=ev(node.comparators[0])
        if type(node.ops[0]) is ast.Lt:return a<b
        if type(node.ops[0]) is ast.Eq:return a==b
      raise TypeError("oracle rejected AST node "+type(node).__name__)
    for stmt in fn.body:
      if isinstance(stmt,ast.Expr) and isinstance(stmt.value,ast.Constant) and isinstance(stmt.value.value,str):continue
      if isinstance(stmt,ast.Assign) and len(stmt.targets)==1 and isinstance(stmt.targets[0],ast.Name):env[stmt.targets[0].id]=ev(stmt.value);continue
      if isinstance(stmt,ast.If):
        if ev(stmt.test):
          only=stmt.body
          for branch_stmt in only:
            if isinstance(branch_stmt,ast.Return):raise Return(ev(branch_stmt.value))
            raise TypeError("oracle rejected branch")
        continue
      if isinstance(stmt,ast.Return):raise Return(ev(stmt.value))
      raise TypeError("oracle rejected statement "+type(stmt).__name__)
    return None
def exact_schedule(run,all_rows,expected):
    calls=run.get("calls",[])
    if len(calls)!=len(expected): return False
    for c,(corpus,fi,ci,_want,_oracle_error) in zip(calls,expected):
      row=all_rows[fi][1]
      expected_function=row.get("function_sha256") or row.get("source_sha256")
      expected_source=row.get("module_sha256") or row.get("source_sha256")
      expected_file=row.get("module_sha256") or row.get("file_sha256")
      if (c["corpus"],c["function_index"],c["case_index"],c["function_sha256_expected"],c["source_sha256_expected"])!=(corpus,fi,ci,expected_function,expected_source): return False
      if c["source_sha256_observed"]!=expected_source or c["corpus_file_sha256_expected"]!=expected_file or c["args"]!=row["input_cases"][ci]: return False
    return True
def main():
    rows=candidates();control=positive_control();frame=json.loads(FRAME.read_text());raw=json.loads(RAW.read_text());runs=raw.get("runs",[]);manifest=raw.get("run_manifest",{});capture=manifest.get("stdout_stderr_capture") or {};lp=ROOT/capture.get("path","__missing__");log=lp.read_bytes() if lp.is_file() else b""
    base_raw=json.loads(BASE_RAW.read_text());base_analysis=json.loads(BASE_ANALYSIS.read_text());base_frame=json.loads(BASE_FRAME.read_text())
    baseline_hashes={"raw":sha(BASE_RAW.read_bytes()),"analysis":sha(BASE_ANALYSIS.read_bytes()),"frame":sha(BASE_FRAME.read_bytes())}
    same_v1_inputs=len(base_frame.get("selected",[]))==len(rows) and all({**new,"input_cases":old["input_cases"][:4]}==old for new,old in zip(rows,base_frame.get("selected",[])))
    expected=[];oracle_errors=[]
    all_rows=[("stacks",r) for r in rows]+[("positive_control",control)]
    for fi,(corpus,row) in enumerate(all_rows):
      if corpus=="stacks":src=SOURCE.read_text()
      else:src=list(BLOCK.finditer((TPDATA/row["chapter"]).read_text(encoding="utf-8")))[row["block_index"]].group(1)
      for ci,args in enumerate(row["input_cases"]):
        try:
          try:value=oracle(src,row["function"],args)
          except Return as ret:value=ret.value
          expected.append((corpus,fi,ci,{"type":type(value).__name__,"value":value},None))
        except Exception as exc:expected.append((corpus,fi,ci,None,type(exc).__name__));oracle_errors.append(type(exc).__name__)
    checks={"candidate_count_five":len(rows)==5,"independent_frame_reconstruction":frame.get("candidate_count")==len(rows) and frame.get("selected")==rows and frame.get("positive_control")==control,
      "acquisition_and_four_heldouts":bool(rows) and rows[0]["function"]=="beginning_of_definition" and len(rows[1:])==4,
      "twenty_five_stacks_cases_plus_two_control_cases":len(expected)==27 and sum(c=="stacks" for c,_,_,_,_ in expected)==25 and sum(c=="positive_control" for c,_,_,_,_ in expected)==2,"oracle_error_free":not oracle_errors,
      "two_fresh_workers":len(runs)==2 and len({r.get("pid") for r in runs})==2,
      "worker_schedule_exact":all(len(r.get("calls",[]))==27 for r in runs),
      "source_locks_stable":raw.get("post_run_inputs")==raw.get("locked_inputs") and all(r.get("source_stable") and r.get("locked_inputs_before")==raw.get("locked_inputs")==r.get("locked_inputs_after") for r in runs),
      "source_and_case_hashes_exact":all(exact_schedule(r,all_rows,expected) for r in runs),
      "shared_manifest_console_valid":manifest.get("manifest_schema")=="substrate-run-manifest-v1" and manifest.get("exit_status")==0 and bool(log) and len(log)==capture.get("bytes") and sha(log)==capture.get("sha256") and all(f"completed=worker{i} rc=0".encode() in log for i in (0,1)),
      "frozen_v1_baseline_hashes_and_scores":baseline_hashes==BASE_HASHES and raw.get("locked_inputs",{}).get("baseline_artifacts")==BASE_HASHES and base_raw.get("integrity_pass") and base_analysis.get("pass") and all(w.get("stacks_exact_correct")==0 and w.get("stacks_predictions")==0 and w.get("positive_control_correct")==2 for w in base_analysis.get("summary",{}).get("workers",[])),
      "v1_cases_paired_and_unicode_case_added":same_v1_inputs and all("é" in str(r["input_cases"][4]) for r in rows),
      "workers_succeeded":all(r.get("worker_returncode")==0 and r.get("boot",{}).get("loaded",0)>0 for r in runs)}
    summaries=[]
    for run in runs:
      by={(c["function_index"],c["case_index"]):c for c in run.get("calls",[])};scored=[]
      for corpus,fi,ci,want,oracle_error in expected:
        c=by[(fi,ci)];correct=oracle_error is None and not c["abstained"] and c["prediction"]==want
        scored.append({"corpus":corpus,"function":all_rows[fi][1]["function"],"split":"positive_control" if corpus=="positive_control" else ("acquisition" if fi==0 else "held_out_function"),"case_index":ci,"expected":want,"prediction":c["prediction"],"abstained":c["abstained"],"error_type":c["error_type"],"correct":correct,"oracle_error":oracle_error,"wall_ns":c["wall_ns"],"receipt_delta":c["receipt_delta"],"minted_observation_count":sum(bool(o["minted_axis_ids"]) for o in c["new_observations"])})
      primary=[x for x in scored if x["corpus"]=="stacks"];preds=[x for x in primary if not x["abstained"]];held=[x for x in primary if x["split"]=="held_out_function"];ctrl=[x for x in scored if x["corpus"]=="positive_control"]
      timing=sorted(c["wall_ns"] for c in scored)
      summaries.append({"replicate":run.get("replicate"),"stacks_cases":len(primary),"stacks_exact_correct":sum(x["correct"] for x in primary),"stacks_predictions":len(preds),"stacks_abstentions":len(primary)-len(preds),"stacks_coverage":len(preds)/len(primary),"stacks_conditional_accuracy":sum(x["correct"] for x in preds)/len(preds) if preds else None,"held_out_cases":len(held),"held_out_exact_correct":sum(x["correct"] for x in held),"held_out_predictions":sum(not x["abstained"] for x in held),"held_out_abstentions":sum(x["abstained"] for x in held),"positive_control_cases":len(ctrl),"positive_control_correct":sum(x["correct"] for x in ctrl),"positive_control_predictions":sum(not x["abstained"] for x in ctrl),"receipt_count":sum(c["receipt_delta"] for c in run["calls"]),"minted_observation_count":sum(sum(bool(o["minted_axis_ids"]) for o in c["new_observations"]) for c in run["calls"]),"median_wall_ns":timing[len(timing)//2],"p95_wall_ns":timing[int(.95*len(timing))],"boot_loaded":run["boot"]["loaded"],"boot_total":run["boot"]["total"],"boot_failures":len(run["boot"]["failed"]),"peak_rss_bytes":run["runtime"]["peak_rss_bytes"],"case_results":scored})
    checks["worker_outcome_parity"]=len(summaries)==2 and [(c["prediction"],c["error_type"]) for c in summaries[0]["case_results"]]==[(c["prediction"],c["error_type"]) for c in summaries[1]["case_results"]]
    checks["positive_control_passes"]=all(s["positive_control_correct"]==2 for s in summaries)
    result={"checks":checks,"pass":all(checks.values()),"summary":{"candidate_count":len(rows),"stacks_case_count":25,"positive_control_case_count":2,"oracle_errors":oracle_errors,"baseline_v1":{"stacks_cases":20,"exact_correct":0,"predictions":0,"abstentions":20,"baseline_artifact_hashes":baseline_hashes},"claim_boundary":raw.get("claim_boundary"),"workers":summaries}}
    print(json.dumps(result,indent=2,sort_keys=True))
    if not result["pass"]:raise SystemExit("Stacks string prediction analysis failed")
if __name__=="__main__":main()
