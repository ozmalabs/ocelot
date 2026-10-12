#!/usr/bin/env python3
"""Build a temporary seed corpus with eventized rules in their original slots."""
from __future__ import annotations
import hashlib,json,os,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
def corpus_rows():
 rows=[]
 for p in sorted((ROOT/'seeds').glob('*.json')):rows.append((p.name,sha(p.read_bytes())))
 for p in sorted((ROOT/'seeds/generated').glob('*.json')):rows.append((f'generated/{p.name}',sha(p.read_bytes())))
 return rows
def build():
 from substrate_problem_shape_all_transitions import indexed_rules,PS_RULES
 source=ROOT/'seeds/problem_shape_growth.json';seed=json.loads(source.read_text())
 original_order=[str(r.get('name')) for r in seed.get('rules',[]) if isinstance(r,dict) and r.get('name') in PS_RULES]
 variants=indexed_rules(None,seed,deactivate_existing=False)
 count=0
 for i,r in enumerate(seed.get('rules',[])):
  if isinstance(r,dict) and r.get('name') in PS_RULES:
   seed['rules'][i]=variants[r['name']];count+=1
 if count!=len(PS_RULES):raise RuntimeError(f'expected five in-place rule replacements, got {count}')
 transformed_order=[str(r.get('name')) for r in seed.get('rules',[]) if isinstance(r,dict) and r.get('name') in PS_RULES]
 if transformed_order!=original_order:raise RuntimeError('ProblemShape rule positions changed during seed transformation')
 payload=(json.dumps(seed,indent=2,sort_keys=True)+'\n').encode()
 corpus_digest=sha(json.dumps(corpus_rows(),separators=(',',':')).encode())
 manifest_hash=sha(payload)
 out=Path(tempfile.gettempdir())/f'ocelot_ps_rule_order_{corpus_digest[:12]}_{manifest_hash[:12]}'
 if out.exists():
  target=out/'problem_shape_growth.json'
  if not target.exists() or sha(target.read_bytes())!=manifest_hash:raise RuntimeError(f'existing generated seed dir differs: {out}')
 else:
  out.mkdir(mode=0o700);(out/'generated').mkdir()
  for p in sorted((ROOT/'seeds').glob('*.json')):
   if p.name=='problem_shape_growth.json':continue
   (out/p.name).symlink_to(p)
  for p in sorted((ROOT/'seeds/generated').glob('*.json')):(out/'generated'/p.name).symlink_to(p)
  (out/'problem_shape_growth.json').write_bytes(payload)
 return {'seed_dir':str(out),'manifest_sha256':manifest_hash,'corpus_digest':corpus_digest,'replaced_rule_count':count,'problem_shape_rule_order':original_order}
if __name__=='__main__':print(json.dumps(build(),sort_keys=True))
