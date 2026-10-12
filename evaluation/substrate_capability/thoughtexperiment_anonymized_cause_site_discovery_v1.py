#!/usr/bin/env python3
"""Blinded order/score panel for trace-guided edit discovery with confounders."""
from __future__ import annotations
import copy, hashlib, importlib.util, json, os, platform, random, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'evaluation/substrate_capability')]
RUNNER=Path(__file__).resolve(); PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_ANONYMIZED_CAUSE_SITE_DISCOVERY_V1_PREREG_20261002.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_anonymized_cause_site_discovery_v1.py'
BASE=ROOT/'evaluation/substrate_capability/thoughtexperiment_bidirectional_edge_identity_guards_v1_1.py'
EDITOPS=ROOT/'domains/edit_ops.py'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_anonymized_cause_site_discovery_v1_lock_20261002.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_anonymized_cause_site_discovery_v1_orders_20261002.json'
SCORES=ROOT/'evaluation/reports/thoughtexperiment_anonymized_cause_site_discovery_v1_scores_20261002.json'
ANALYSIS=ROOT/'evaluation/reports/thoughtexperiment_anonymized_cause_site_discovery_v1_analysis_20261002.json'
WORKERS=4; REPEATS=2; SEED=20261025

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load_base():
    spec=importlib.util.spec_from_file_location('anon_cause_base',BASE); mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod);return mod
def frozen():
    from substrate_rs import _native
    base=load_base()
    return {'runner':sha(RUNNER),'protocol':sha(PROTOCOL),'analyzer':sha(ANALYZER),'edit_ops':sha(EDITOPS),
            'base_sources':base.frozen(),'loaded_native_binary':sha(Path(_native.__file__).resolve())}

def add_confounds(ctx):
    """Add one correlated shadow emitter and one empty-effect control."""
    native=ctx['native']; source=copy.deepcopy(ctx['source_rule'])
    shadow=copy.deepcopy(source); shadow['name']='shadow_writer'
    for clause in shadow['where'].get('items',[]):
        if clause.get('type')=='Not':
            arg=clause.get('arg',{});arg.get('source',{}).__setitem__('edge_type','has_shadow_offer')
    for effect in shadow.get('effects',[]):
        if isinstance(effect,list) and len(effect)>3 and effect[0]=='add_edge' and effect[2]=='has_mint_offer':effect[2]='has_shadow_offer'
    native.add_rule(shadow)
    noop=copy.deepcopy(source);noop['name']='no_op_writer';noop['effects']=[];native.add_rule(noop)
    return ['shadow_writer','no_op_writer']

def context(base,worker,split,sample):
    ctx=base.recurrence_context(worker,split,sample,fault=True)
    ctx['add_due'](0); confounds=add_confounds(ctx)
    return ctx,confounds

def anonymize(report,active_rules):
    names=sorted(active_rules)
    aliases={name:f'rule_{i:03d}' for i,name in enumerate(names)}
    arules={}
    for name,row in active_rules.items():
        clone=copy.deepcopy(row);clone['name']=aliases[name];arules[aliases[name]]=clone
    areport=copy.deepcopy(report)
    for event in areport['rule_write_events']:
        event['rule_name']=aliases.get(event['rule_name'],'unknown')
        event['origin_rules']=[aliases.get(n,'unknown') for n in event.get('origin_rules',[])]
    return areport,arules,aliases

def discover(areport,arules):
    """No original rule names, task cue, target identity or oracle enter here."""
    from domains.edit_ops import find_edge_identity_sites,apply_add_edge_identity_guard
    writers=[]
    for event in areport['rule_write_events']:
        if event['progressed'] and (event['node_ids'] or event['edges']) and event['rule_name'] not in writers:
            writers.append(event['rule_name'])
    proposals=[]
    for alias in writers:
        rule=arules.get(alias)
        if rule is None:continue
        for site in find_edge_identity_sites(rule):
            if site.get('scope','edge')!='edge':continue
            variant=apply_add_edge_identity_guard(rule,site,'opaque_proposal')
            if variant is None:continue
            variant['name']=alias
            pid=hashlib.sha256(json.dumps(variant,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
            proposals.append({'proposal_id':pid,'alias':alias,'site':site,'rule':variant})
    return proposals,writers

def capture_pool(base,worker):
    ctx,confounds=context(base,worker,'trace',0)
    report=ctx['native'].run_rules_delta_report(5,False)
    active={r['name']:r for r in ctx['native'].export_rules() if r.get('active',True)}
    anon,arules,aliases=anonymize(report,active)
    proposals,writers=discover(anon,arules)
    reverse={v:k for k,v in aliases.items()}
    target_alias=aliases.get(ctx['target'])
    # Keep the alias -> evaluator mapping private to the orchestration/scorer.
    evaluator_source={p['proposal_id']:reverse[p['alias']] for p in proposals}
    audit={'event_count':len(report['rule_write_events']),'dropped':report['rule_write_events_dropped'],
      'trace_writer_aliases':writers,'productive_writer_count':len(writers),
      'noop_attempt_seen':any(aliases.get(e['rule_name'])==aliases.get('no_op_writer') and not e['progressed']
          and not e['node_ids'] and not e['edges'] for e in report['rule_write_events']),
      'shadow_writer_seen':aliases.get('shadow_writer') in writers,
      'candidate_origin_aliases':[p['alias'] for p in proposals],
      'candidate_site_families':[p['site'] for p in proposals],
      'target_alias_in_pool':target_alias in [p['alias'] for p in proposals],
      'candidate_count':len(proposals),'active_rule_count':len(active),
      'original_rule_names_passed_to_discovery':False,'cue_passed_to_discovery':False,
      'target_name_passed_to_discovery':False}
    return ctx,proposals,evaluator_source,audit

def install_source(native,source,variant):
    rows=native.export_rules();hits=[(i,r) for i,r in enumerate(rows) if r.get('name')==source and r.get('active',True)]
    if len(hits)!=1 or not native.remove_rule(hits[0][0]):raise RuntimeError(f'cannot replace proposal source {source}')
    row=copy.deepcopy(variant);row['name']=source;native.add_rule(row)

def score(base,worker,split,sample,proposal,source):
    ctx,_=context(base,worker,split,sample);native=ctx['native'];sub=ctx['sub']
    if proposal is not None:install_source(native,source,proposal)
    first=[int(native.run_rules(100)) for _ in range(5)]
    ctx['add_due'](1);second=[int(native.run_rules(100)) for _ in range(5)]
    counts=[]
    for key in ctx['keys']:
        node=next(n for n in sub.nodes('PredicateRecurrenceCandidate') if sub.node(n)['attrs'].get('recurrence_key')==key)
        counts.append(len(list(sub.neighbours(node,'has_mint_offer'))))
    fixed=int(native.run_rules(100))
    return {'correct':counts==[1,1] and fixed==0,'output_counts':counts,'fixedpoint_progress':fixed,
            'first_sweeps':first,'second_sweeps':second}

def worker_orders(i):
    base=load_base();before=frozen();ctx,props,source_map,audit=capture_pool(base,i)
    if len(props)<2:raise RuntimeError(f'insufficient anonymized candidate pool: {audit}')
    rng=random.Random(SEED+i);perm=list(range(len(props)));rng.shuffle(perm);props=[props[j] for j in perm]
    descriptors=[{'proposal_id':p['proposal_id'],'proposal_label':'candidate'} for p in props]
    evidence=[];outcomes=[];train_ns=0
    for p in props:
        rows=[]
        for s in range(REPEATS):
            t=time.perf_counter_ns();result=score(base,i,f'train_{i}',s,p['rule'],source_map[p['proposal_id']]);train_ns+=time.perf_counter_ns()-t
            rows.append(result);evidence.append({'proposal_id':p['proposal_id'],'probe_id':f'train_{i}_{s}',
                'predicted':'correct' if result['correct'] else 'incorrect','expected':'correct'})
        outcomes.append({'proposal_id':p['proposal_id'],'outcomes':rows})
    t=time.perf_counter_ns();decision=base.selector_decision(ctx['sub'],'anon_cause',i,descriptors,evidence);select_ns=time.perf_counter_ns()-t
    decision.pop('proposal_node',None)
    controls={}
    for ctl in ('tie','all_wrong'):
        d=base.selector_decision(ctx['sub'],'anon_cause_'+ctl,i,descriptors,evidence,ctl);d.pop('proposal_node',None);controls[ctl]=d
    chosen=decision.get('proposal_id')
    target_sources={p['proposal_id']:source_map[p['proposal_id']] for p in props}
    after=frozen()
    return {'worker':i,'source_before':before,'source_after':after,'source_stable':before==after,
       'discovery':audit,'candidate_order':[p['proposal_id'] for p in props],
       'candidate_descriptors':descriptors,'private_evaluator_source_map':target_sources,
       'candidate_rules':{p['proposal_id']:p['rule'] for p in props},'training_outcomes':outcomes,
       'training_evidence':evidence,'decision':decision,'selected_source':source_map.get(chosen),
       'controls':controls,'training_scoring_ns':train_ns,'selection_ns':select_ns}

def worker_scores(order):
    base=load_base();i=int(order['worker']);before=frozen();ctx,props,source_map,audit=capture_pool(base,i)
    byid={p['proposal_id']:p for p in props}
    if list(order['candidate_order'])!=[p['proposal_id'] for p in [byid[x] for x in order['candidate_order']]]:raise RuntimeError('candidate identity drift')
    rows=[]
    for pid in order['candidate_order']:
        p=byid[pid];trials=[score(base,i,f'heldout_{i}',s,p['rule'],source_map[pid]) for s in range(REPEATS)]
        rows.append({'proposal_id':pid,'source_alias':p['alias'],'heldout':trials})
    after=frozen()
    return {'worker':i,'source_before':before,'source_after':after,'source_stable':before==after,
       'discovery_replayed':audit==order['discovery'],'candidate_scores':rows,
       'selected_heldout':[r for r in rows if r['proposal_id']==order['decision'].get('proposal_id')]}

def main():
    args=sys.argv[1:]
    if args[:1]==['--worker-orders']:
        print(json.dumps(worker_orders(int(args[1])),sort_keys=True,separators=(',',':')));return 0
    if args[:1]==['--worker-scores']:
        print(json.dumps(worker_scores(json.load(sys.stdin)),sort_keys=True,separators=(',',':')));return 0
    if args==['--lock']:
        if any(p.exists() for p in (LOCK,ORDERS,SCORES,ANALYSIS)):raise SystemExit('refusing to overwrite artifacts')
        LOCK.write_text(json.dumps({'schema':'ThoughtexperimentAnonymizedCauseSiteDiscoveryV1Lock','sources':frozen(),
            'workers':WORKERS,'repeats':REPEATS,'seed':SEED,'families':['recurrence'],'candidate_operator':'edge identity guard',
            'confounders':['correlated shadow writer','empty-effect no-op writer']},indent=2,sort_keys=True)+'\n')
        print(LOCK.relative_to(ROOT));return 0
    if args in (['--orders'],['--scores']):
        lock=json.loads(LOCK.read_text())
        if frozen()!=lock['sources']:raise SystemExit('source drift from lock')
        env={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}:{ROOT}/evaluation/substrate_capability'}
        if args==['--orders']:
            if ORDERS.exists() or SCORES.exists():raise SystemExit('refusing to overwrite captures')
            rows=[]
            for i in range(lock['workers']):
                p=subprocess.run([sys.executable,str(RUNNER),'--worker-orders',str(i)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=300)
                if p.returncode:raise RuntimeError(f'order worker {i}: {p.stderr[-3000:]}')
                rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
            dest=ORDERS;payload={'schema':'ThoughtexperimentAnonymizedCauseSiteDiscoveryV1Orders','lock_sha256':sha(LOCK),'workers':rows}
        else:
            if not ORDERS.exists() or SCORES.exists():raise SystemExit('missing orders or scores already exist')
            rows=[]
            for order in json.loads(ORDERS.read_text())['workers']:
                p=subprocess.run([sys.executable,str(RUNNER),'--worker-scores'],input=json.dumps(order),cwd=ROOT,env=env,text=True,capture_output=True,timeout=300)
                if p.returncode:raise RuntimeError(f"score worker {order['worker']}: {p.stderr[-3000:]}")
                rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
            dest=SCORES;payload={'schema':'ThoughtexperimentAnonymizedCauseSiteDiscoveryV1Scores','lock_sha256':sha(LOCK),'orders_sha256':sha(ORDERS),'workers':rows}
        if frozen()!=lock['sources']:raise SystemExit('source drift during capture')
        payload.update({'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),'sources':frozen()})
        dest.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n');print(dest.relative_to(ROOT));return 0
    if args==['--analyze']:
        p=subprocess.run([sys.executable,str(ANALYZER)],cwd=ROOT,text=True,capture_output=True)
        if p.returncode:raise RuntimeError(p.stderr)
        print(p.stdout.strip());return 0
    raise SystemExit('usage: --lock, --orders, --scores, --analyze, --worker-orders ID')

if __name__=='__main__':raise SystemExit(main())
