#!/usr/bin/env python3
"""Build a temporary seed corpus with eventized rules in their original slots."""
from __future__ import annotations
import hashlib,json,os,shutil,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
def corpus_rows():
 rows=[]
 for p in sorted((ROOT/'seeds').glob('*.json')):rows.append((p.name,sha(p.read_bytes())))
 for p in sorted((ROOT/'seeds/generated').glob('*.json')):rows.append((f'generated/{p.name}',sha(p.read_bytes())))
 return rows
def write_snapshot(out: Path, files: dict[str, bytes]) -> None:
 if out.exists():
  for rel, data in files.items():
   target=out/rel
   if not target.is_file() or target.is_symlink() or target.read_bytes()!=data:
    raise RuntimeError(f"existing immutable snapshot differs: {target}")
  return
 out.parent.mkdir(mode=0o700,parents=True,exist_ok=True);out.mkdir(mode=0o700);(out/'generated').mkdir()
 for rel,data in files.items():
  target=out/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
 for target in out.rglob('*.json'):target.chmod(0o444)
 for directory in sorted((p for p in out.rglob('*') if p.is_dir()),key=lambda p:len(p.parts),reverse=True):directory.chmod(0o555)
 out.chmod(0o555)

def digest_files(files: dict[str, bytes]) -> str:
 rows=[(rel,sha(data)) for rel,data in sorted(files.items())]
 return sha(json.dumps(rows,separators=(',',':')).encode())

def build():
 from substrate_problem_shape_all_transitions import indexed_rules,PS_RULES
 source_files={}
 for p in sorted((ROOT/'seeds').glob('*.json')):source_files[p.name]=p.read_bytes()
 for p in sorted((ROOT/'seeds/generated').glob('*.json')):source_files[f'generated/{p.name}']=p.read_bytes()
 source_digest=digest_files(source_files)
 source=ROOT/'seeds/problem_shape_growth.json';seed=json.loads(source_files['problem_shape_growth.json'])
 original_order=[str(r.get('name')) for r in seed.get('rules',[]) if isinstance(r,dict) and r.get('name') in PS_RULES]
 variants=indexed_rules(None,seed,deactivate_existing=False)
 count=0
 for i,r in enumerate(seed.get('rules',[])):
  if isinstance(r,dict) and r.get('name') in PS_RULES:
   seed['rules'][i]=variants[r['name']];count+=1
 if count!=len(PS_RULES):raise RuntimeError(f'expected five in-place rule replacements, got {count}')
 transformed_order=[str(r.get('name')) for r in seed.get('rules',[]) if isinstance(r,dict) and r.get('name') in PS_RULES]
 if transformed_order!=original_order:raise RuntimeError('ProblemShape rule positions changed during seed transformation')
 transformed_files=dict(source_files);transformed_files['problem_shape_growth.json']=(json.dumps(seed,indent=2,sort_keys=True)+'\n').encode()
 base_digest=digest_files(source_files);candidate_digest=digest_files(transformed_files)
 root=Path(tempfile.gettempdir())/f'ocelot_ps_rule_order_v1_4_{source_digest[:16]}'
 base_dir=root/'baseline';candidate_dir=root/'candidate'
 write_snapshot(base_dir,source_files);write_snapshot(candidate_dir,transformed_files)
 # Detect concurrent source edits during snapshot materialization.
 current={}
 for p in sorted((ROOT/'seeds').glob('*.json')):current[p.name]=p.read_bytes()
 for p in sorted((ROOT/'seeds/generated').glob('*.json')):current[f'generated/{p.name}']=p.read_bytes()
 if digest_files(current)!=source_digest:raise RuntimeError('seed corpus changed while immutable snapshots were being built')
 return {'baseline_seed_dir':str(base_dir),'candidate_seed_dir':str(candidate_dir),'source_corpus_digest':source_digest,'baseline_snapshot_digest':base_digest,'candidate_snapshot_digest':candidate_digest,'manifest_count':len(source_files),'replaced_rule_count':count,'problem_shape_rule_order':original_order}
if __name__=='__main__':print(json.dumps(build(),sort_keys=True))
