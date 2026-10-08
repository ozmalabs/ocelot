#!/usr/bin/env python3
"""Independent closure oracle and conservation checks for native counter v1."""
from __future__ import annotations
import gzip,hashlib,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/mint_termination_native_counters_v1_2_20261004.json.gz'
LOCK=ROOT/'evaluation/substrate_capability/mint_termination_native_counters_v1_2_lock_20261004.json'
OUT=ROOT/'evaluation/reports/mint_termination_native_counters_v1_2_analysis_20261004.json'
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
        arms={a['mode']:a for a in pair['arms']};req(set(arms)=={'off','on'},'missing mode '+pair['pair_id'])
        normalized={}
        for mode,arm in arms.items():
            gedges=[(e['src'],e['type'],e['tgt'],tuple(sorted(e['attrs'].items()))) for e in arm['graph']['edges']]
            gn,ge=norm(arm['graph']['nodes'],gedges);rn,re=norm(refn,refe);normalized[mode]=(gn,ge)
            report=arm['report'];checks={'fixed_point':report['status']=='fixed_point','no_overshoot':report['budget_overshoot']==0,'within_fact_bound':report['progress_steps']<=stat['progress_steps_upper_bound'],'exact_nodes':gn==rn,'exact_edges':ge==re,'positive_runtime':arm['execution_wall_ns']>0}
            req(all(checks.values()),f'{mode} closure gate {pair["pair_id"]}')
            global_counts=dict(arm['scale_global']);per=arm['per_rule'];clauses=arm['clauses']
            if mode=='off':
                req(not per and not clauses and all(v==0 for v in global_counts.values()),'audit-off counters nonzero '+pair['pair_id'])
            else:
                n,d,o=pair['n'],pair['degree'],pair['order'];by_index={i:{metric:int(count) for rid,metric,count in per if int(rid)==i} for i in range(3)};units={'A':n*d,'B':n*d+n*d*d,'C':2*n};expected={name:units[name]*by_index[o.index(name)].get('rule_enumerations',0) for name in 'ABC'}
                for name,want in expected.items():
                    idx=o.index(name);counts=by_index[idx]
                    req(counts.get('candidate_pairs',-1)==want,f'{name} candidate pairs {pair["pair_id"]}')
                    req(counts.get('candidate_tests',-1)==want,f'{name} candidate tests {pair["pair_id"]}')
                req(global_counts.get('cand_enum')==sum(expected.values()),'global candidate enum total '+pair['pair_id'])
                req(global_counts.get('cand_tested')==sum(expected.values()),'global tested total '+pair['pair_id'])
                req(global_counts.get('cand_tested_unattributed')==0 and global_counts.get('term_evals_unattributed')==0,'unattributed work '+pair['pair_id'])
                clauses_by={(int(i),int(c)):int(v) for i,c,v in clauses}
                for idx,name in enumerate(o):
                    enum_count=by_index[idx].get('rule_enumerations',0);wants=([n*d*enum_count] if name=='A' else [n*d*enum_count,n*d*d*enum_count] if name=='B' else [n*enum_count,n*enum_count])
                    for ci,want in enumerate(wants):req(clauses_by.get((idx,ci))==want,f'clause count {pair["pair_id"]} rule {name} clause {ci}')
                req(global_counts.get('cand_enum_local',0)+global_counts.get('cand_enum_scan',0)+global_counts.get('cand_enum_hinted',0)==global_counts.get('cand_enum',-1),'enum path conservation '+pair['pair_id'])
                req(global_counts.get('cand_enum_first',0)+global_counts.get('cand_enum_repeat',0)==global_counts.get('cand_enum',-1),'first/repeat conservation '+pair['pair_id'])
        rows.append({'pair_id':pair['pair_id'],'n':pair['n'],'degree':pair['degree'],'order':pair['order'],'replicate':pair['replicate'],'expected_total_candidate_tests':sum(({'A':pair['n']*pair['degree'],'B':pair['n']*pair['degree']+pair['n']*pair['degree']**2,'C':2*pair['n']}[name])*next(int(count) for ri,metric,count in arms['on']['per_rule'] if int(ri)==pair['order'].index(name) and metric=='rule_enumerations') for name in 'ABC'),'off_ns':arms['off']['execution_wall_ns'],'on_ns':arms['on']['execution_wall_ns'],'on_global':dict(arms['on']['scale_global']),'on_per_rule':arms['on']['per_rule'],'checks':checks})
        req(normalized['off']==normalized['on'],'audit mode changed graph '+pair['pair_id'])
        key=(pair['n'],pair['degree']);by_design.setdefault(key,[]).append((frozenset(normalized['off'][0]),frozenset(normalized['off'][1])))
    expected={f'n{n}_d{d}_{o}_r{r}' for n in (32,64,128,256) for d in (1,2,4,8,16) for o in ('ABC','CBA','BCA') for r in (1,2,3)}
    req({p['pair_id'] for p in raw['pairs']}==expected,'180-pair factorial mismatch')
    order_inv=all(len(set(v))==1 for v in by_design.values());req(order_inv,'terminal state varies by rule order')
    by_cell=[]
    for (n,d),rs in sorted({(r['n'],r['degree']):[x for x in rows if x['n']==r['n'] and x['degree']==r['degree']] for r in rows}.items()):
        ratios=[x['on_ns']/x['off_ns'] for x in rs];by_cell.append({'n':n,'degree':d,'pairs':len(rs),'off_median_ns':statistics.median(x['off_ns'] for x in rs),'on_median_ns':statistics.median(x['on_ns'] for x in rs),'paired_ratio_median':statistics.median(ratios)})
    out={'schema':'MintTerminationNativeCountersV1_2Analysis','passed':not errors,'errors':errors,'raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'pair_count':len(rows),'design_cells':len(by_design),'order_invariant':order_inv,'cells':by_cell,'pairs':rows,'claim_boundary':raw['design']['claim_limit']}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':out['passed'],'errors':errors,'pair_count':len(rows),'design_cells':len(by_design),'order_invariant':order_inv},indent=2));return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
