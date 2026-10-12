#!/usr/bin/env python3
"""Inventory full-seed on-disk and structured payload footprint."""
import hashlib, json, statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SEEDS=ROOT/'seeds'
OUT=ROOT/'evaluation/reports/substrate_seed_manifest_footprint_v1_20260927.json'
FILES=sorted([*SEEDS.glob('*.json'),* (SEEDS/'generated').glob('*.json')])
rows=[]; totals={'bytes':0,'direct_nodes':0,'nested_graph_nodes':0,'edges':0,'rules':0,'concepts':0,'productions':0,'terms':0}
component_bytes={}
for p in FILES:
 try: data=json.loads(p.read_text(encoding='utf-8'))
 except Exception as exc:
  rows.append({'path':p.relative_to(ROOT).as_posix(),'parse_error':f'{type(exc).__name__}: {exc}'});continue
 if not isinstance(data,dict):continue
 size=p.stat().st_size; graph=data.get('graph') if isinstance(data.get('graph'),dict) else {}
 vals={
  'direct_nodes':len(data.get('nodes') or []),
  'nested_graph_nodes':len(graph.get('nodes') or []),
  'edges':len(data.get('edges') or [])+len(graph.get('edges') or []),
  'rules':len(data.get('rules') or []),
  'concepts':len(data.get('concepts') or []),
  'productions':len(data.get('productions') or []),
  'terms':len(data.get('terms') or []),
 }
 per_key={}
 for key,value in data.items():
  try: per_key[key]=len(json.dumps(value,ensure_ascii=False,separators=(',',':')).encode('utf-8'))
  except Exception: pass
  if key!='id' and key in ('nodes','edges','rules','concepts','productions','terms','graph'):
   component_bytes[key]=component_bytes.get(key,0)+per_key.get(key,0)
 for k,v in vals.items():totals[k]+=v
 totals['bytes']+=size
 rows.append({'path':p.relative_to(ROOT).as_posix(),'seed_id':data.get('id'),'bytes':size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),**vals,'top_level_payload_bytes':per_key,'self_load_only':bool(data.get('self_load_only')),'selective_content_keys':bool(data.get('selective_content_keys')),'generated':p.parent.name=='generated'})
valid=[r for r in rows if 'bytes' in r];ranked=sorted(valid,key=lambda x:x['bytes'],reverse=True);nbytes=totals['bytes']
shares={f'top_{n}':{'bytes':sum(x['bytes'] for x in ranked[:n]),'share':sum(x['bytes'] for x in ranked[:n])/nbytes} for n in (1,3,5,10,20,50)}
out={'schema_version':1,'run_id':'substrate-seed-manifest-footprint-v1-20260927','source_inputs':{'boot_all.py':hashlib.sha256((ROOT/'substrate/boot_all.py').read_bytes()).hexdigest(),'seed_loader.py':hashlib.sha256((ROOT/'substrate/seed_loader.py').read_bytes()).hexdigest()},'seed_file_count':len(valid),'parse_error_count':len(rows)-len(valid),'totals':totals,'top_level_component_bytes':component_bytes,'file_size_bytes':{'median':statistics.median(x['bytes'] for x in valid),'p90':sorted(x['bytes'] for x in valid)[int(.90*(len(valid)-1))],'p95':sorted(x['bytes'] for x in valid)[int(.95*(len(valid)-1))],'max':ranked[0]['bytes']},'top_size_shares':shares,'largest_manifests':ranked[:25],'files':sorted(valid,key=lambda x:x['path'])}
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps({'output':str(OUT.relative_to(ROOT)),'seed_file_count':len(valid),'totals':totals,'top_size_shares':shares,'largest_manifests':[{k:r.get(k) for k in ('path','bytes','direct_nodes','nested_graph_nodes','edges','rules','concepts','productions')} for r in ranked[:10]]},indent=2))
