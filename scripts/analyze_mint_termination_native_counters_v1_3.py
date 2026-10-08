#!/usr/bin/env python3
"""Independent closure oracle and conservation checks for native counter v1."""
from __future__ import annotations
import gzip,hashlib,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/mint_termination_native_counters_v1_3_20261004.json.gz'
LOCK=ROOT/'evaluation/substrate_capability/mint_termination_native_counters_v1_3_lock_20261004.json'
OUT=ROOT/'evaluation/reports/mint_termination_native_counters_v1_3_analysis_20261004.json'
sys.path.insert(0,str(ROOT/'scripts'))
from analyze_mint_termination_fragment import analyze

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bindings(patterns,edges):
    by_type={}
    for fact in edges:by_type.setdefault(fact[1],[]).append(fact)
    by_source={};by_target={}
    for et,facts in by_type.items():
        facts.sort(key=lambda x:(x[0],x[1],x[2]));src={};tgt={}
        for fact in facts:src.setdefault(fact[0],[]).append(fact);tgt.setdefault(fact[2],[]).append(fact)
        by_source[et]=src;by_target[et]=tgt
    out=[{}]
    for sv,et,tv in patterns:
        nxt=[]
        for binding in out:
            if et not in by_type:continue
            if sv in binding:candidates=by_source[et].get(binding[sv],())
            elif tv in binding:candidates=by_target[et].get(binding[tv],())
            else:candidates=by_type[et]
            for source,_,target,_ in candidates:
                if sv in binding and binding[sv]!=source:continue
                if tv in binding and binding[tv]!=target:continue
                q=dict(binding);q[sv],q[tv]=source,target;nxt.append(q)
        out=nxt
    return out
def reference(pair):
    nodes=[{'id':i,'type':'Seed','attrs':{'idx':i}} for i in range(pair['n'])];edges=set()
    for s,et,t,a in pair['initial_edges']:edges.add((int(s[1:]),et,int(t[1:]),tuple(sorted(a.items()))))
    changed=True;passes=0
    while changed:
        passes+=1
        if passes>100:raise RuntimeError('reference closure exceeded pass cap')
        changed=False
        for rule in pair['rule_specs']:
            for b0 in bindings(rule['match'],edges):
                b=dict(b0)
                for eff in rule['effects']:
                    if eff[0]=='add_node_if_absent':
                        _,var,typ,attrs=eff;found=next((n['id'] for n in nodes if n['type']==typ and all(n['attrs'].get(k,object())==v for k,v in attrs.items())),None)
                        if found is None:found=len(nodes);nodes.append({'id':found,'type':typ,'attrs':dict(attrs)});changed=True
                        b[var]=found
                    else:
                        _,s,et,t,attrs=eff;fact=(b[s],et,b[t],tuple(sorted(attrs.items())))
                        if fact not in edges:edges.add(fact);changed=True
    return nodes,edges
def norm(nodes,edges):
    labels={n['id']:(f"seed:{n['attrs']['idx']}" if n['type']=='Seed' else f"witness:{n['attrs']['tag']}") for n in nodes}
    return ({(n['type'],json.dumps(n['attrs'],sort_keys=True)) for n in nodes},
            {(labels[s],et,labels[t],json.dumps(dict(a),sort_keys=True)) for s,et,t,a in edges})
def main():
    with gzip.open(RAW,'rt',encoding='utf8') as f:raw=json.load(f)
    locked=json.loads(LOCK.read_text())['locked_inputs'];errors=[];rows=[];by_design={}
    def req(ok,msg):
        if not ok:errors.append(msg)
    req(raw['locked_inputs']==locked==raw['post_run_inputs'],'source lock mismatch')
    req(raw['source_stable'] and raw['all_checks_pass'],'runner source or case gate failed')
    for pair in raw['pairs']:
        stat=analyze(pair['rule_specs'],pair['initial_node_ids'],pair['initial_edges']);refn,refe=reference(pair)
        req(stat['accepted'] and stat['unique_mint_signatures']==3 and stat['edge_type_count']==5,'fragment admission '+pair['pair_id'])
        arms={a['mode']:a for a in pair['arms']};req(set(arms)=={'off','on'},'missing arm '+pair['pair_id'])
        normalized={};arm_checks={}
        for mode,arm in arms.items():
            gedges=[(e['src'],e['type'],e['tgt'],tuple(sorted(e['attrs'].items()))) for e in arm['graph']['edges']]
            gn,ge=norm(arm['graph']['nodes'],gedges);rn,re=norm(refn,refe);normalized[mode]=(frozenset(gn),frozenset(ge))
            report=arm['report'];checks={'fixed_point':report['status']=='fixed_point','no_overshoot':report['budget_overshoot']==0,'within_fact_bound':report['progress_steps']<=stat['progress_steps_upper_bound'],'exact_nodes':gn==rn,'exact_edges':ge==re,'positive_runtime':arm['execution_wall_ns']>0}
            arm_checks[mode]=checks;req(all(checks.values()),f'{mode} closure gate {pair["pair_id"]}')
            global_counts=dict(arm['scale_global']);per=arm['per_rule'];clauses=arm['clauses'];metadata=arm['metadata'];edge_rows=arm['edge_candidates']
            if mode=='off':
                req(not per and not clauses and not metadata and not edge_rows and all(v==0 for v in global_counts.values()),'audit-off counters nonzero '+pair['pair_id'])
            else:
                per_by={i:{metric:int(count) for rid,metric,count in per if int(rid)==i} for i in range(3)}
                meta_by={int(row[0]):row for row in metadata}
                req(set(meta_by)=={0,1,2},'metadata ids missing '+pair['pair_id'])
                for idx,key in enumerate(pair['order']):
                    if idx not in meta_by:continue
                    req(meta_by[idx][2]=={'A':'mint_A','B':'mint_B','C':'join_AB'}[key] and meta_by[idx][4] is False,'rule metadata identity '+pair['pair_id'])
                req(global_counts.get('cand_tested_unattributed')==0 and global_counts.get('term_evals_unattributed')==0,'unattributed work '+pair['pair_id'])
                req(sum(v.get('candidate_pairs',0) for v in per_by.values())==global_counts.get('cand_enum',-1),'per-rule/global enumeration conservation '+pair['pair_id'])
                req(sum(v.get('candidate_tests',0) for v in per_by.values())==global_counts.get('cand_tested',-1),'per-rule/global test conservation '+pair['pair_id'])
                clause_sum={i:sum(int(v) for rid,_,v in clauses if int(rid)==i) for i in range(3)}
                edge_sum={i:sum(int(row[5]) for row in edge_rows if int(row[0])==i) for i in range(3)}
                for i in range(3):
                    req(clause_sum[i]==per_by[i].get('candidate_tests',0),'clause attribution conservation '+pair['pair_id'])
                    req(edge_sum[i]==per_by[i].get('candidate_pairs',0),'edge attribution conservation '+pair['pair_id'])
                req(global_counts.get('cand_enum_local',0)+global_counts.get('cand_enum_scan',0)+global_counts.get('cand_enum_hinted',0)==global_counts.get('cand_enum',-1),'enum path conservation '+pair['pair_id'])
                req(global_counts.get('cand_enum_first',0)+global_counts.get('cand_enum_repeat',0)==global_counts.get('cand_enum',-1),'first/repeat conservation '+pair['pair_id'])
        req(normalized['off']==normalized['on'],'audit mode changed graph '+pair['pair_id'])
        idx_to_name={int(row[0]):row[2] for row in arms['on']['metadata']}
        per_by={i:{metric:int(count) for rid,metric,count in arms['on']['per_rule'] if int(rid)==i} for i in range(3)}
        counts_by_name={idx_to_name[i]:per_by[i] for i in idx_to_name if i in per_by}
        row={'pair_id':pair['pair_id'],'n':pair['n'],'degree':pair['degree'],'order':pair['order'],'replicate':pair['replicate'],'off_ns':arms['off']['execution_wall_ns'],'on_ns':arms['on']['execution_wall_ns'],'paired_ratio':arms['on']['execution_wall_ns']/arms['off']['execution_wall_ns'],'rule_counts':counts_by_name,'global_on':dict(arms['on']['scale_global']),'arm_checks':arm_checks}
        rows.append(row);key=(pair['n'],pair['degree']);by_design.setdefault(key,[]).append(normalized['off'])
    expected={f'n{n}_d{d}_{o}_r{r}' for n in (32,64,128,256) for d in (1,2,4,8,16) for o in ('ABC','CBA','BCA') for r in (1,2,3)}
    req({p['pair_id'] for p in raw['pairs']}==expected,'180-pair factorial mismatch')
    order_inv=all(len(set(v))==1 for v in by_design.values());req(order_inv,'terminal state varies by rule order')
    cells=[]
    for (n,d) in sorted(by_design):
        rs=[x for x in rows if x['n']==n and x['degree']==d]
        cells.append({'n':n,'degree':d,'pairs':len(rs),'off_median_ns':statistics.median(x['off_ns'] for x in rs),'on_median_ns':statistics.median(x['on_ns'] for x in rs),'paired_ratio_median':statistics.median(x['paired_ratio'] for x in rs),'candidate_tests_by_rule':{name:statistics.median(x['rule_counts'].get(name,{}).get('candidate_tests',0) for x in rs) for name in ('mint_A','mint_B','join_AB')}})
    out={'schema':'MintTerminationNativeCountersV1_3Analysis','passed':not errors,'errors':errors,'raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'pair_count':len(rows),'design_cells':len(by_design),'order_invariant':order_inv,'cells':cells,'pairs':rows,'claim_boundary':raw['design']['claim_limit']}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':out['passed'],'errors':errors[:30],'error_count':len(errors),'pair_count':len(rows),'design_cells':len(by_design),'order_invariant':order_inv},indent=2));return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
