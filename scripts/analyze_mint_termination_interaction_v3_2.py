#!/usr/bin/env python3
"""Independent closure oracle and analysis for current-source interaction v2."""
from __future__ import annotations
import gzip,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/mint_termination_interaction_v3_2_20261004.json.gz'
LOCK=ROOT/'evaluation/substrate_capability/mint_termination_interaction_v3_2_lock_20261004.json'
OUT=ROOT/'evaluation/reports/mint_termination_interaction_v3_2_analysis_20261004.json'
sys.path.insert(0,str(ROOT/'scripts'))
from analyze_mint_termination_fragment import analyze

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bindings(patterns,edges):
    by_type={}
    for fact in edges:
        by_type.setdefault(fact[1],[]).append(fact)
    for facts in by_type.values():facts.sort(key=lambda x:(x[0],x[1],x[2]))
    by_source={};by_target={}
    for et,facts in by_type.items():
        src={};tgt={}
        for fact in facts:
            src.setdefault(fact[0],[]).append(fact);tgt.setdefault(fact[2],[]).append(fact)
        by_source[et]=src;by_target[et]=tgt
    out=[{}]
    for sv,et,tv in patterns:
        nxt=[]
        for binding in out:
            if et not in by_type:continue
            if sv in binding and tv in binding:
                candidates=by_source[et].get(binding[sv],())
            elif sv in binding:
                candidates=by_source[et].get(binding[sv],())
            elif tv in binding:
                candidates=by_target[et].get(binding[tv],())
            else:candidates=by_type[et]
            for source,_,target,_ in candidates:
                if sv in binding and binding[sv]!=source:continue
                if tv in binding and binding[tv]!=target:continue
                q=dict(binding);q[sv],q[tv]=source,target;nxt.append(q)
        out=nxt
    return out

def reference(case):
    nodes=[{'id':i,'type':'Seed','attrs':{'idx':i}} for i in range(case['n_initial_nodes'])]; edges=set()
    for s,et,t,a in case['initial_edges']:edges.add((int(s[1:]),et,int(t[1:]),tuple(sorted(a.items()))))
    rounds=0;changed=True
    while changed:
        rounds+=1
        if rounds>100:raise RuntimeError('reference closure exceeded pass cap')
        changed=False
        for rule in case['rule_specs']:
            for b0 in bindings(rule['match'],edges):
                b=dict(b0)
                for eff in rule['effects']:
                    if eff[0]=='add_node_if_absent':
                        _,var,typ,attrs=eff
                        found=next((n['id'] for n in nodes if n['type']==typ and all(n['attrs'].get(k,object())==v for k,v in attrs.items())),None)
                        if found is None:found=len(nodes);nodes.append({'id':found,'type':typ,'attrs':dict(attrs)});changed=True
                        b[var]=found
                    else:
                        _,s,et,t,attrs=eff;fact=(b[s],et,b[t],tuple(sorted(attrs.items())))
                        if fact not in edges:edges.add(fact);changed=True
    return nodes,edges,rounds
def norm(nodes,edges):
    labels={}
    for n in nodes:
        a=n['attrs']; labels[n['id']]=f"seed:{a['idx']}" if n['type']=='Seed' else f"witness:{a['tag']}"
    ns={(n['type'],json.dumps(n['attrs'],sort_keys=True)) for n in nodes}
    es={(labels[s],et,labels[t],json.dumps(dict(a),sort_keys=True)) for s,et,t,a in edges}
    return ns,es
def main():
    with gzip.open(RAW,'rt',encoding='utf-8') as f:raw=json.load(f)
    lock=json.loads(LOCK.read_text())['locked_inputs'];rows=[];by_design={};errors=[]
    def req(ok,msg):
        if not ok:errors.append(msg)
    req(raw.get('locked_inputs')==lock==raw.get('post_run_inputs'),'source lock mismatch')
    req(raw.get('source_stable') is True and raw.get('all_checks_pass') is True and not raw.get('failed_cases'),'runner source/case gate failed')
    for c in raw['cases']:
        st=analyze(c['rule_specs'],c['initial_node_ids'],c['initial_edges']);rn,re,orounds=reference(c)
        gn,ge=norm(c['native_graph']['nodes'],[(e['src'],e['type'],e['tgt'],tuple(sorted(e['attrs'].items()))) for e in c['native_graph']['edges']]);en,ee=norm(rn,re)
        b=st['progress_steps_upper_bound'];checks={'checker_accepts':st['accepted'],'M_is_3':st['unique_mint_signatures']==3,'E_is_5':st['edge_type_count']==5,'fixed_point':c['native_report']['status']=='fixed_point','exact_nodes':gn==en,'exact_edges':ge==ee,'within_bound':c['native_report']['progress_steps']<=b,'no_budget_overshoot':c['native_report']['budget_overshoot']==0,'positive_runtime':c['execution_wall_ns']>0}
        req(all(checks.values()),'case failed '+c['case_id']);key=(c['n_initial_nodes'],c['degree']);by_design.setdefault(key,set()).add((frozenset(gn),frozenset(ge)))
        rows.append({'case_id':c['case_id'],'n':c['n_initial_nodes'],'degree':c['degree'],'order':c['rule_order'],'replicate':c['replicate'],'bound':b,'progress':c['native_report']['progress_steps'],'passes':c['native_report']['passes_completed'],'oracle_passes':orounds,'execution_wall_ns':c['execution_wall_ns'],'checks':checks})
    expected={f'n{n}_d{top}_{order}_r{r}' for n in (32,64,128,256) for top in (1,2,4,8,16) for order in ('ABC','CBA','BCA') for r in (1,2,3)}
    req({r['case_id'] for r in rows}==expected,'180-cell factorial mismatch')
    order_inv=all(len(v)==1 for v in by_design.values());req(order_inv,'terminal semantics vary by rule order')
    out={'schema':'MintTerminationInteractionV3_2Analysis','passed':not errors,'errors':errors,'raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'case_count':len(rows),'design_cells':len(by_design),'order_invariant':order_inv,'cases':rows,'claim_boundary':raw['design']['claim_limit']}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'passed':out['passed'],'errors':errors,'case_count':len(rows),'design_cells':len(by_design),'order_invariant':order_inv},indent=2))
    return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
