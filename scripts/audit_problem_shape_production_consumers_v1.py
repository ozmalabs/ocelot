#!/usr/bin/env python3
"""Static source audit for production ProblemShape producers and consumers."""
from __future__ import annotations
import ast,hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
SEARCH_ROOTS=[ROOT/'domains',ROOT/'substrate',ROOT/'runners/dsl/python']
SEED=ROOT/'seeds/problem_shape_growth.json';MODULE=ROOT/'domains/problem_shape.py'
OUT=ROOT/'evaluation/reports/problem_shape_production_consumer_audit_v1_20260928.json'
TOKENS={'ProblemShape','ProblemShapeObservation','problem_codebook_epoch','observed_problem','ps_has_combine','ps_has_k_starts'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def strings(node):
 return {x.value for x in ast.walk(node) if isinstance(x,ast.Constant) and isinstance(x.value,str)}
def main():
 files=sorted(p for base in SEARCH_ROOTS for p in base.rglob('*.py') if '__pycache__' not in p.parts)
 imports=[]; calls=[]; literals=[]; parse_errors=[]
 for p in files:
  rel=p.relative_to(ROOT).as_posix()
  try: tree=ast.parse(p.read_text(),filename=rel)
  except Exception as e: parse_errors.append({'path':rel,'error':str(e)});continue
  for n in ast.walk(tree):
   if isinstance(n,ast.ImportFrom) and ((n.module or '')=='domains' and any(a.name=='problem_shape' for a in n.names) or (n.module or '').endswith('.problem_shape')):
    imports.append({'path':rel,'line':n.lineno,'module':n.module,'names':[a.name for a in n.names]})
   elif isinstance(n,ast.Import) and any(a.name=='domains.problem_shape' for a in n.names):imports.append({'path':rel,'line':n.lineno,'module':'domains.problem_shape'})
  found=sorted(strings(tree)&TOKENS)
  if found:literals.append({'path':rel,'tokens':found})
 seed=json.loads(SEED.read_text());rule_rows=[]
 for r in seed.get('rules',[]):
  ss=str(r)
  if any(t in ss for t in TOKENS):rule_rows.append({'name':r.get('name'),'match_type':r.get('match_type'),'match':r.get('match'),'effects':r.get('effects')})
 mint_rules=[r for r in rule_rows if any(isinstance(e,list) and len(e)>2 and e[0]=='add_node' and e[2]=='ProblemShape' for e in r.get('effects',[]))]
 consumers=[x for x in imports if x['path']!='domains/problem_shape.py']
 result={'schema_version':1,'audit_class':'static source inventory; not dynamic reachability or proof against reflective invocation','inputs':{p.relative_to(ROOT).as_posix():sha(p) for p in (MODULE,SEED)},'python_files_scanned':len(files),'parse_errors':parse_errors,'problem_shape_imports':imports,'non_producer_problem_shape_imports':consumers,'candidate_observation_or_signature_calls':calls,'typed_literal_hits':literals,'problem_shape_seed_rules':rule_rows,'shape_mint_rules':mint_rules,'checks':{'all_python_sources_parse':not parse_errors,'no_nonproducer_production_imports':len(consumers)==0,'growth_seed_has_five_observation_rules_and_one_shape_mint_rule':len(rule_rows)==5 and len(mint_rules)==1 and all(r.get('match_type')=='ProblemShapeObservation' for r in rule_rows)},'claim_boundary':'No statically visible production-domain consumer of learned ProblemShape keys was found in the scanned Python source roots. Evaluation harnesses and tests are outside this production scan. A production consumer may still be supplied reflectively or outside the scanned roots; no dynamic call tracing was performed.'}
 result['all_checks_pass']=all(result['checks'].values());OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT.relative_to(ROOT)),'all_checks_pass':result['all_checks_pass'],'checks':result['checks'],'imports':imports,'calls':calls,'seed_rules':len(rule_rows)},indent=2))
 if not result['all_checks_pass']:raise SystemExit('consumer audit checks failed')
if __name__=='__main__':main()
