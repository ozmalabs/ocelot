#!/usr/bin/env python3
"""Source-hashed census of multi-edge match patterns in top-level seed manifests."""
from __future__ import annotations
import collections, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SEEDS=ROOT/'seeds'
OUT=ROOT/'evaluation/reports/substrate_seed_join_shapes_v1_20260927.json'
MIN_EDGES=3

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def pattern_shape(match):
    # Seed match rows are [source, relation, target]. Variable incidence is
    # reported syntactically; constants and aliases are not inferred here.
    vars_=[]
    for edge in match:
        if not isinstance(edge,list) or len(edge)!=3 or not all(isinstance(x,str) for x in edge):
            raise ValueError(f'unsupported match row: {edge!r}')
        vars_.extend((edge[0],edge[2]))
    parent={v:v for v in set(vars_)}
    def find(x):
        while parent[x]!=x:
            parent[x]=parent[parent[x]];x=parent[x]
        return x
    for s,_,t in match:
        a,b=find(s),find(t)
        if a!=b:parent[a]=b
    components=len({find(v) for v in parent})
    incidence=collections.Counter(vars_)
    # Project each ternary match edge to an undirected variable edge.
    pair_edges=[]
    for s,_,t in match:
        if s!=t:pair_edges.append(tuple(sorted((s,t))))
    unique_pairs=set(pair_edges)
    v=len(parent);e=len(unique_pairs)
    return {'edge_count':len(match),'variable_count':v,'component_count':components,
            'connected':components==1,'cyclic_projection':components==1 and e>=v,
            'repeated_endpoint_occurrences':sum(n-1 for n in incidence.values() if n>1),
            'max_endpoint_occurrence':max(incidence.values(),default=0),
            'unique_variable_pairs':e}

def main():
    files=sorted(SEEDS.glob('*.json'))
    source_hashes={str(p.relative_to(ROOT)):sha(p) for p in files}
    rules=[]
    for path in files:
        try:data=json.loads(path.read_text())
        except (UnicodeDecodeError,json.JSONDecodeError):continue
        if not isinstance(data,dict) or not isinstance(data.get('rules'),list):continue
        for pos,rule in enumerate(data['rules']):
            if not isinstance(rule,dict):continue
            match=rule.get('match')
            if not isinstance(match,list) or len(match)<MIN_EDGES:continue
            shape=pattern_shape(match)
            rules.append({'seed_id':data.get('id'),'manifest':str(path.relative_to(ROOT)),
                          'rule_index':pos,'rule_name':rule.get('name'),**shape})
    arity=collections.Counter(r['edge_count'] for r in rules)
    manifest_counts=collections.Counter(r['manifest'] for r in rules)
    duplicate_names=collections.Counter(r['rule_name'] for r in rules if r['rule_name'])
    repeated=[{'name':n,'count':c} for n,c in sorted(duplicate_names.items()) if c>1]
    per_manifest=[]
    for manifest,count in manifest_counts.most_common():
        rr=[r for r in rules if r['manifest']==manifest]
        per_manifest.append({'manifest':manifest,'multi_edge_rule_count':count,
                             'arity_histogram':dict(sorted(collections.Counter(r['edge_count'] for r in rr).items())),
                             'connected_fraction':sum(r['connected'] for r in rr)/count,
                             'cyclic_count':sum(r['cyclic_projection'] for r in rr)})
    payload={'schema_version':1,'measurement':'static_seed_match_pattern_census',
             'minimum_match_edges':MIN_EDGES,'top_level_manifest_count':len(files),
             'hashed_manifest_count':len(source_hashes),'manifest_sha256':source_hashes,
             'multi_edge_rule_count':len(rules),'arity_histogram':dict(sorted(arity.items())),
             'connected_pattern_count':sum(r['connected'] for r in rules),
             'cyclic_projection_count':sum(r['cyclic_projection'] for r in rules),
             'duplicate_multi_edge_names':repeated,'top_manifests':per_manifest,
             'selected_task_family_patterns':[r for r in rules if r['manifest'] in {
                'seeds/conversation_discourse_state.json','seeds/conversation_deliberation_phase4a.json',
                'seeds/conversation_topic_reply.json','seeds/vision_eye.json','seeds/llvm_passes.json'}],
             'rules':rules,
             'claim_boundary':'Authored seed-rule pattern structure only. Does not prove these rules are loaded, fire on a task, or predict matcher candidate work.'}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'manifest_count':len(files),'multi_edge_rule_count':len(rules),
      'arity_histogram':payload['arity_histogram'],'connected':payload['connected_pattern_count'],
      'cyclic_projection':payload['cyclic_projection_count'],'output':str(OUT.relative_to(ROOT))},indent=2))
if __name__=='__main__':main()
