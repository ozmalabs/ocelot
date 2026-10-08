#!/usr/bin/env python3
"""Read-only census of inference Term references in seed JSON manifests."""
from __future__ import annotations
import hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SEEDS=ROOT/'seeds'
OUT=ROOT/'evaluation/reports/substrate_induction_seed_census_v1_20260926.json'
TERMS=['DimInfer','GenInfer','RatioInduce','TimeInfer','SupportInfer','DepthInfer','BlinkBridge','MetaShapeMint','SynthEnumerate']
GATES=['gen_infer_enabled','time_infer_enabled','depth_infer_enabled','blink_bridge_enabled']
STATUSES=['motion_seq','motion_seq_robust','depth_seq','blink_seq','residual','decoded','minted','time_inferred','depth_inferred','blink_bridged']

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def walk(x,path='$'):
    if isinstance(x,dict):
        yield x,path
        for k,v in x.items():
            yield from walk(v,f'{path}.{k}')
    elif isinstance(x,list):
        for i,v in enumerate(x):
            yield from walk(v,f'{path}[{i}]')

def main():
    files=sorted(SEEDS.glob('*.json'))
    loaded=[]
    for p in files:
        try:
            loaded.append((p,json.loads(p.read_text())))
        except Exception:
            continue
    results={}
    for term in TERMS:
        hits=[]
        for p,data in loaded:
            for obj,path in walk(data):
                if obj.get('type')==term:
                    hits.append({'seed':p.stem,'path':path})
        results[term]={'seed_count':len({h['seed'] for h in hits}),'occurrence_count':len(hits),'seeds':sorted({h['seed'] for h in hits}),'occurrences':hits}
    gates={g:[] for g in GATES}
    statuses={s:[] for s in STATUSES}
    for p,data in loaded:
        text=json.dumps(data,sort_keys=True)
        for g in GATES:
            if g in text:gates[g].append(p.stem)
        for status in STATUSES:
            if status in text:statuses[status].append(p.stem)
    report={'schema_version':1,'scope':'Literal JSON Term references and exact gate/status-token mentions in seeds/*.json; this does not prove runtime loading, rule reachability, default flag values, or production observations.','seed_file_count':len(files),'term_references':results,'gate_mentions':gates,'status_mentions':statuses,'source_sha256':{'script':sha(Path(__file__)),**{f'seeds/{p.name}':sha(p) for p in files}}}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'output':str(OUT),'seed_file_count':len(files),'terms':{k:v['seed_count'] for k,v in results.items()},'gate_seed_counts':{k:len(v) for k,v in gates.items()}},indent=2))

if __name__=='__main__':
    main()
