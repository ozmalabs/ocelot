#!/usr/bin/env python3
"""Current-source census of ReachableFrom term authoring and access paths."""
from __future__ import annotations
import ast,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'evaluation/reports/substrate_reachable_from_cache_usage_v2_20261005.json'
SEED_ROOT=ROOT/'seeds'
PY_ROOTS=(ROOT/'domains',ROOT/'substrate',ROOT/'worlds',ROOT/'runners/dsl/python')
ENGINE_FILES=('runners/dsl/src/term.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/python/substrate_rs/__init__.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def collect_terms(v,rel,path,out):
 if isinstance(v,dict):
  if v.get('type')=='ReachableFrom':out.append({'file':rel,'path':path,'edge_type':v.get('edge_type'),'node':v.get('node')})
  for k,x in v.items():collect_terms(x,rel,f'{path}.{k}',out)
 elif isinstance(v,list):
  for i,x in enumerate(v):collect_terms(x,rel,f'{path}[{i}]',out)
class Visitor(ast.NodeVisitor):
 def __init__(self,rel):self.rel=rel;self.scope=[];self.refs=[];self.calls=[]
 def visit_FunctionDef(self,node):
  self.scope.append(node.name);self.generic_visit(node);self.scope.pop()
 visit_AsyncFunctionDef=visit_FunctionDef
 def visit_Constant(self,node):
  if node.value=='ReachableFrom':self.refs.append({'file':self.rel,'line':node.lineno,'function':'.'.join(self.scope) or None})
 def visit_Call(self,node):
  f=node.func;name=f.id if isinstance(f,ast.Name) else f.attr if isinstance(f,ast.Attribute) else None
  if name in {'grounding_reach','flag_ungrounded_confident','seed_dependency_closure'}:self.calls.append({'file':self.rel,'line':node.lineno,'function':'.'.join(self.scope) or None,'callee':name})
  self.generic_visit(node)
def main():
 seed_listing=subprocess.run(['rg','--files','seeds','-g','*.json'],cwd=ROOT,text=True,capture_output=True,check=True).stdout.splitlines(); seeds=sorted(ROOT/x for x in seed_listing)
 matching=subprocess.run(['rg','-l','\"type\"\\s*:\\s*\"ReachableFrom\"','seeds','-g','*.json'],cwd=ROOT,text=True,capture_output=True)
 if matching.returncode not in (0,1):raise RuntimeError(matching.stderr)
 candidates=sorted(ROOT/x for x in matching.stdout.splitlines());terms=[]
 for p in candidates:
  collect_terms(json.loads(p.read_text()),p.relative_to(ROOT).as_posix(),'$',terms)
 pyfiles=sorted(p for root in PY_ROOTS if root.exists() for p in root.rglob('*.py'))
 refs=[];calls=[]
 for p in pyfiles:
  try:v=Visitor(p.relative_to(ROOT).as_posix());v.visit(ast.parse(p.read_text()));refs.extend(v.refs);calls.extend(v.calls)
  except (SyntaxError,UnicodeDecodeError):continue
 engine={}
 for rel in ENGINE_FILES:
  p=ROOT/rel;s=p.read_text();engine[rel]={'sha256':sha(p),'reachable_cache_mentions':s.count('reachable_cache'),'fresh_default_evalcache_mentions':s.count('EvalCache::default'),'has_setter_symbol':'set_reachable_cache' in s}
 py=(ROOT/'runners/dsl/src/py.rs').read_text();i=py.find("fn evaluate<'py>");j=py.find('\n    #[pyo3',i+1) if i>=0 else -1;body=py[i:j if j>i else None]
 init=(ROOT/'runners/dsl/python/substrate_rs/__init__.py').read_text()
 records={}
 for p in pyfiles+[ROOT/x for x in ENGINE_FILES]+[Path(__file__).resolve()]+candidates:records[p.relative_to(ROOT).as_posix()]=sha(p)
 listing_digest=hashlib.sha256(('\n'.join(seed_listing)+'\n').encode()).hexdigest()
 results={'schema':'ReachableFromUsageCensusV2','scope':'All current seeds/**/*.json typed Term trees and AST string literals in domains, substrate, worlds, runners/dsl/python; source inspection only, not a dynamic call graph or activation frequency.','seed_manifest_count':len(seeds),'seed_manifest_path_list_sha256':listing_digest,'seed_manifest_search':'rg -l \"type\"\\s*:\\s*\"ReachableFrom\" seeds -g *.json','candidate_seed_manifest_count':len(candidates),'typed_seed_term_count':len(terms),'typed_seed_terms':terms,'python_source_count':len(pyfiles),'python_literal_reference_count':len(refs),'python_literal_references':refs,'reachability_helper_calls':calls,'engine_source':engine,'native_evaluate_method_found':i>=0,'native_evaluate_method_has_fresh_evalcache':i>=0 and 'EvalCache::default()' in body,'high_level_wrapper_has_cache_toggle':'set_reachable_cache' in init,'input_sha256':records}
 results['interpretation']='The census locates authored syntax and source references, not runtime task frequency. Compare the unique typed seed routes with dynamic browser-profile cache captures; direct host evaluation paths must be separately assessed because they may not share the substrate-owned rewrite cache.'
 OUT.write_text(json.dumps(results,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':OUT.relative_to(ROOT).as_posix(),'seed_manifests':len(seeds),'typed_seed_terms':len(terms),'python_files':len(pyfiles),'python_literal_references':len(refs),'fresh_eval_cache':results['native_evaluate_method_has_fresh_evalcache'],'high_level_toggle':results['high_level_wrapper_has_cache_toggle']}));return 0
if __name__=='__main__':raise SystemExit(main())
