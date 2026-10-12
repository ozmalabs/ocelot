#!/usr/bin/env python3
"""Static inventory of Python call sites into the PyO3 seed-manifest loader."""
from __future__ import annotations
import ast, hashlib, json, subprocess
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"evaluation/reports/native_seed_manifest_caller_audit_v1_20260925.json"
RUST=ROOT/"runners/dsl/src/py.rs"

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    files=subprocess.check_output(["rg","-l","load_seed_manifest","--glob","*.py","."],cwd=ROOT,text=True).splitlines()
    calls=[]; errors=[]; source_manifest=[]
    for rel in sorted(files):
        path=ROOT/rel.removeprefix("./")
        source_manifest.append({"path":path.relative_to(ROOT).as_posix(),"sha256":sha(path)})
        try: tree=ast.parse(path.read_text(encoding="utf-8"))
        except Exception as e:
            errors.append(f"parse failed: {rel}: {type(e).__name__}"); continue
        for node in ast.walk(tree):
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=="load_seed_manifest":
                try: receiver=ast.unparse(node.func.value)
                except Exception: receiver="<unparsed>"
                calls.append({"path":path.relative_to(ROOT).as_posix(),"line":node.lineno,
                              "receiver":receiver,"positional_arg_count":len(node.args),
                              "keyword_args":sorted(k.arg for k in node.keywords if k.arg)})
    source=RUST.read_text()
    start=source.index("    fn load_seed_manifest(")
    end=source.index("    // --- mutation surface",start)
    body=source[start:end]
    import re
    native_keys=sorted(set(re.findall(r'\bm\s*\.\s*get\("([^"]+)"\)',body)))
    by_top=Counter(row["path"].split("/",1)[0] for row in calls)
    report={"schema_version":1,"audit_id":"native-seed-manifest-callers-v1-20260925",
            "static_only":True,"call_site_count":len(calls),"file_count":len(files),
            "parse_errors":errors,"calls_by_top_level_path":dict(sorted(by_top.items())),
            "native_function_source":"runners/dsl/src/py.rs::PySubstrate::load_seed_manifest",
            "native_function_sha256":sha(RUST),"native_read_keys":native_keys,
            "converts_entire_manifest_before_key_reads":"let manifest_json = pyobj_to_json(py, manifest)?;" in body,
            "call_sites":calls,
            "scanned_sources":source_manifest,
            "limits":"AST inventory finds direct syntactic call expressions only; it does not resolve aliases, runtime reachability, dataflow into manifest arguments, or native callers outside Python."}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"call_sites":len(calls),"files":len(files),"native_read_keys":native_keys,"parse_errors":errors,"report":str(OUT)}))
    return 0 if not errors else 2
if __name__=="__main__": raise SystemExit(main())
