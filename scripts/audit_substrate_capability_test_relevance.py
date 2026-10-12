#!/usr/bin/env python3
"""Conservative lexical/AST crosswalk from capability source links to linked Python tests.

This reports candidate relevance only. A name occurrence is not proof that a
test executes the production path or asserts its behavior.
"""
import argparse, ast, hashlib, json, re, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
IN=ROOT/"evaluation/substrate_capability/capability_map.json"
OUT=ROOT/"evaluation/reports/substrate_capability_test_relevance_audit_20260928.json"
GENERIC={"run","evaluate","node","observe","main","get","set","load","save","read","write","build","apply","test","solve","call","update","open","close","process","process_audio","run_pipeline","tick","advance","install","dispatch"}

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def test_refs(row):
    return sorted({x["path"] for x in row.get("evidence_catalog",[]) if x.get("category")=="test" and x.get("exists")})
def source_symbols(row):
    out=[]
    for s in row.get("source_links",[]):
        sym=s.get("symbol")
        if sym:
            leaf=re.split(r"::|\.",sym)[-1]
            out.append({"path":s.get("path"),"symbol":sym,"leaf":leaf})
    return out
def rust_unit_tests(row):
    """Report test modules local to linked Rust sources; presence is not relevance proof."""
    out=[]
    for source in sorted({s.get("path") for s in row.get("source_links",[]) if s.get("path","").endswith(".rs")}):
        path=ROOT/source
        if not path.is_file():
            continue
        text=path.read_text(errors="replace")
        source_hash=sha(path)
        marker=text.find("#[cfg(test)]")
        if marker < 0:
            out.append({"path":source,"source_sha256":source_hash,"has_cfg_test":False,"test_count":0,"test_names":[],"source_symbol_mentions_in_test_tail":[]})
            continue
        tail=text[marker:]
        names=re.findall(r"#\[test\]\s*(?:#\[[^\]]+\]\s*)*(?:pub\s+)?fn\s+([A-Za-z_][A-Za-z0-9_]*)",tail)
        symbols=sorted({s["leaf"] for s in source_symbols(row) if s["path"]==source and s["leaf"]})
        mentions=[symbol for symbol in symbols if re.search(r"\b"+re.escape(symbol)+r"\b",tail)]
        out.append({"path":source,"source_sha256":source_hash,"has_cfg_test":True,"test_count":len(names),"test_names":names,"source_symbol_mentions_in_test_tail":mentions})
    return out
def analyze_test(path, symbols):
    p=ROOT/path; text=p.read_text(errors="replace")
    source_hash=sha(p)
    try: tree=ast.parse(text,filename=path); parse=True
    except SyntaxError: return {"path":path,"source_sha256":source_hash,"parseable":False,"error":"SyntaxError"}
    parents={}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node): parents[child]=node
    calls=set(); names=set(); attrs=set(); call_sites=[]
    function_calls={}; function_asserts={}
    for node in ast.walk(tree):
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
            function_asserts[node.name]=sum(isinstance(x,ast.Assert) for x in ast.walk(node))
            function_calls[node.name]=set()
            for child in ast.walk(node):
                if isinstance(child,ast.Call) and isinstance(child.func,ast.Name):
                    function_calls[node.name].add(child.func.id)
    function_names=set(function_calls)
    for node in ast.walk(tree):
        if isinstance(node,ast.Call):
            f=node.func
            if isinstance(f,ast.Name): leaf=f.id
            elif isinstance(f,ast.Attribute): leaf=f.attr
            else: leaf=None
            if leaf:
                calls.add(leaf)
                ancestor=node; enclosing=None
                while ancestor in parents:
                    ancestor=parents[ancestor]
                    if isinstance(ancestor,(ast.FunctionDef,ast.AsyncFunctionDef)):
                        enclosing=ancestor;break
                assertions=sum(isinstance(x,ast.Assert) for x in ast.walk(enclosing)) if enclosing else 0
                call_sites.append({"leaf":leaf,"line":node.lineno,"enclosing_function":enclosing.name if enclosing else None,"inside_test_function":bool(enclosing and enclosing.name.startswith("test_")),"assert_statement_count_in_function":assertions})
        elif isinstance(node,ast.Name): names.add(node.id)
        elif isinstance(node,ast.Attribute): attrs.add(node.attr)
    # Follow same-file helper calls from test_* functions. This is a lexical
    # reachability path only; it does not model dispatch, decorators, fixtures,
    # monkeypatches, or runtime branches.
    test_reach={}
    for name in function_names:
        if not name.startswith("test_"): continue
        reached={name}; frontier=[name]
        while frontier:
            current=frontier.pop()
            for callee in function_calls.get(current,()):
                if callee in function_names and callee not in reached:
                    reached.add(callee); frontier.append(callee)
        test_reach[name]=sorted(reached)
    hits=[]
    for s in symbols:
        leaf=s["leaf"]
        if leaf in calls:
            matching=[dict(x,reachable_from_tests=sorted(t for t, reached in test_reach.items() if x["enclosing_function"] in reached)) for x in call_sites if x["leaf"]==leaf]
            hits.append({**s,"evidence":"call_name","specificity":"low" if leaf in GENERIC else "candidate","call_sites":matching})
        elif leaf in names or leaf in attrs:
            hits.append({**s,"evidence":"name_or_attribute","specificity":"low" if leaf in GENERIC else "candidate"})
    return {"path":path,"source_sha256":source_hash,"parseable":True,"callable_hits":hits,"test_helper_reachability":test_reach,"call_sites_to_linked_source_leaves":[site for h in hits for site in h.get("call_sites",[])],"calls_to_linked_source_leaves":sorted(set(h["leaf"] for h in hits if h["evidence"]=="call_name")),"generic_name_hits":sorted(set(h["leaf"] for h in hits if h["specificity"]=="low"))}
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=OUT,help="write JSON report to this path (default: dated legacy path)")
    args=parser.parse_args()
    inv=json.loads(IN.read_text()); rows=[]
    for row in inv["capabilities"]:
        syms=source_symbols(row); tests=[analyze_test(p,syms) for p in test_refs(row)]
        candidate=sorted({x["leaf"] for t in tests if t.get("parseable") for x in t.get("callable_hits",[]) if x["specificity"]=="candidate" and x["evidence"]=="call_name"})
        weak=sorted({x["leaf"] for t in tests if t.get("parseable") for x in t.get("callable_hits",[]) if x["specificity"]=="low"})
        candidate_sites=[(t,h,site) for t in tests for h in t.get("callable_hits",[]) if h["specificity"]=="candidate" and h["evidence"]=="call_name" for site in h.get("call_sites",[])]
        test_assert_sites=[x for x in candidate_sites if x[2]["inside_test_function"] and x[2]["assert_statement_count_in_function"]>0]
        test_call_no_assert=[x for x in candidate_sites if x[2]["inside_test_function"] and x[2]["assert_statement_count_in_function"]==0]
        helper_sites=[x for x in candidate_sites if not x[2]["inside_test_function"]]
        reachable_sites=[(t,h,site) for t in tests for h in t.get("callable_hits",[]) if h["specificity"]=="candidate" and h["evidence"]=="call_name" for site in h.get("call_sites",[]) if site.get("reachable_from_tests")]
        rust_tests=rust_unit_tests(row)
        rows.append({"id":row["id"],"source_symbols":syms,"linked_test_count":len(tests),"tests":tests,"rust_source_local_test_inventory":rust_tests,"rust_source_files_with_cfg_test":sum(t["has_cfg_test"] for t in rust_tests),"rust_source_files_with_zero_test_name_mentions_of_linked_symbol":sum(t["has_cfg_test"] and not t["source_symbol_mentions_in_test_tail"] for t in rust_tests),"candidate_callable_calls":candidate,"generic_name_only_hits":weak,"candidate_call_sites_in_assert_bearing_test_functions":len(test_assert_sites),"candidate_call_sites_in_test_functions_without_assert":len(test_call_no_assert),"candidate_call_sites_outside_test_functions":len(helper_sites),"candidate_source_calls_lexically_reachable_from_test_functions":len(reachable_sites),"test_functions_reaching_candidate_source_calls":sorted({test for _,_,site in reachable_sites for test in site["reachable_from_tests"]}),"static_status":"candidate_call_match" if candidate else ("generic_name_only" if weak else "no_source_symbol_call_found")})
    report={"schema_version":"substrate-capability-test-relevance-audit-v3","input":{"capability_map":"evaluation/substrate_capability/capability_map.json","sha256":sha(IN)},"runner":{"path":"scripts/audit_substrate_capability_test_relevance.py","sha256":sha(Path(__file__).resolve()),"python":sys.version},"method":"Parse each linked Python test file with Python AST. Compare source-linked callable leaves to call expressions, separately flag generic leaves. Record the enclosing function, syntactic Assert count, and same-file lexical helper-call reachability from test_* functions. Separately inventory Rust #[cfg(test)] blocks and #[test] names in linked source files, recording whether linked callable identifiers occur in the test tail. Python lexical reachability and Rust test-tail name presence do not establish runtime execution, assertion relevance, independent oracle use, production-path coverage, or branch execution.","generic_leaf_vocabulary":sorted(GENERIC),"rows":rows,"summary":{"capability_rows":len(rows),"rows_with_candidate_callable_calls":sum(x["static_status"]=="candidate_call_match" for x in rows),"rows_with_candidate_call_in_assert_bearing_test":sum(x["candidate_call_sites_in_assert_bearing_test_functions"]>0 for x in rows),"rows_with_candidate_calls_only_outside_test_functions":sum(x["static_status"]=="candidate_call_match" and x["candidate_call_sites_in_assert_bearing_test_functions"]==0 for x in rows),"candidate_call_sites_in_assert_bearing_test_functions":sum(x["candidate_call_sites_in_assert_bearing_test_functions"] for x in rows),"candidate_call_sites_in_test_functions_without_assert":sum(x["candidate_call_sites_in_test_functions_without_assert"] for x in rows),"candidate_call_sites_outside_test_functions":sum(x["candidate_call_sites_outside_test_functions"] for x in rows),"candidate_source_calls_lexically_reachable_from_test_functions":sum(x["candidate_source_calls_lexically_reachable_from_test_functions"] for x in rows),"rows_with_candidate_calls_reachable_from_test_functions":sum(bool(x["test_functions_reaching_candidate_source_calls"]) for x in rows),"rows_with_only_generic_name_hits":sum(x["static_status"]=="generic_name_only" for x in rows),"rows_with_no_source_symbol_call_found":sum(x["static_status"]=="no_source_symbol_call_found" for x in rows),"linked_test_files":sum(x["linked_test_count"] for x in rows),"rust_source_files_with_cfg_test":sum(x["rust_source_files_with_cfg_test"] for x in rows),"rust_test_name_occurrence_rows":sum(any(t["source_symbol_mentions_in_test_tail"] for t in x["rust_source_local_test_inventory"]) for x in rows)}}
    output=args.output if args.output.is_absolute() else ROOT/args.output
    output.parent.mkdir(parents=True,exist_ok=True); output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"output":str(output.relative_to(ROOT) if output.is_relative_to(ROOT) else output),"summary":report["summary"],"by_row":{r["id"]:r["static_status"] for r in rows}},indent=2))
if __name__=="__main__":main()
