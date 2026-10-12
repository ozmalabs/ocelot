#!/usr/bin/env python3
"""Cross-family anonymized trace-guided candidate generation and selection."""
from __future__ import annotations
import copy,hashlib,importlib.util,json,os,platform,random,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'evaluation/substrate_capability')]
RUNNER=Path(__file__).resolve();PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_ANONYMIZED_CAUSE_SITE_TRANSFER_V1_PREREG_20261002.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_anonymized_cause_site_transfer_v1.py'
BASE=ROOT/'evaluation/substrate_capability/thoughtexperiment_bidirectional_edge_identity_guards_v1_1.py'
PILOT=ROOT/'evaluation/substrate_capability/thoughtexperiment_anonymized_cause_site_discovery_v1.py'
PILOT_PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_ANONYMIZED_CAUSE_SITE_DISCOVERY_V1_PREREG_20261002.md'
EDITOPS=ROOT/'domains/edit_ops.py'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_anonymized_cause_site_transfer_v1_lock_20261002.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_anonymized_cause_site_transfer_v1_orders_20261002.json'
SCORES=ROOT/'evaluation/reports/thoughtexperiment_anonymized_cause_site_transfer_v1_scores_20261002.json'
ANALYSIS=ROOT/'evaluation/reports/thoughtexperiment_anonymized_cause_site_transfer_v1_analysis_20261002.json'
WORKERS=4;REPEATS=2;SEED=20261027;FAMILIES=('recurrence','conversation')
TRAIN_CONV=(('hello there','greeting'),('good morning','greeting'))
HELDOUT_CONV=(('what is it?','question'),('hello again','greeting'),('hi there','greeting'))

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod
def frozen():
    from substrate_rs import _native
    base=load_module('transfer_base_hash',BASE)
    return {'runner':sha(RUNNER),'protocol':sha(PROTOCOL),'analyzer':sha(ANALYZER),'edit_ops':sha(EDITOPS),
      'base_sources':base.frozen(),'prior_pilot':sha(PILOT),'prior_protocol':sha(PILOT_PROTOCOL),
      'loaded_native_binary':sha(Path(_native.__file__).resolve())}
def modules():return load_module('transfer_base',BASE),load_module('transfer_pilot',PILOT)

def add_conversation_confounds(ctx):
    native=ctx['native'];source=copy.deepcopy(ctx['source_rule']);shadow=copy.deepcopy(source);shadow['name']='shadow_writer'
    for clause in shadow.get('where',{}).get('items',[]):
        if clause.get('type')=='Not':clause.get('arg',{}).get('source',{})['edge_type']='shadow_responds_to'
    for effect in shadow.get('effects',[]):
        if isinstance(effect,list) and len(effect)>3 and effect[0]=='add_edge' and effect[2]=='responds_to':effect[2]='shadow_responds_to'
    native.add_rule(shadow)
    noop=copy.deepcopy(source);noop['name']='no_op_writer';noop['effects']=[];native.add_rule(noop)

def new_context(base,pilot,family,worker,split,sample):
    if family=='recurrence':return pilot.context(base,worker,split,sample)
    ctx=base.conversation_context(fault=True);add_conversation_confounds(ctx);return ctx,['shadow_writer','no_op_writer']

def trace_for(base,pilot,family,worker):
    ctx,_=new_context(base,pilot,family,worker,'discovery',0)
    if family=='recurrence':ctx['add_due'](0);report=ctx['native'].run_rules_delta_report(5,False)
    else:
        text,act=TRAIN_CONV[0];ctx['adapter'].receive_utterance(text,speech_act=act,speaker='user',tick=0)
        report=ctx['native'].run_rules_delta_report(100,False)
    active={r['name']:r for r in ctx['native'].export_rules() if r.get('active',True)}
    anon,arules,aliases=pilot.anonymize(report,active)
    proposals,writers=pilot.discover(anon,arules)
    reverse={v:k for k,v in aliases.items()}
    source_map={p['proposal_id']:reverse[p['alias']] for p in proposals}
    audit={'event_count':len(report['rule_write_events']),'dropped':report['rule_write_events_dropped'],
      'productive_writer_aliases':writers,'productive_writer_count':len(writers),
      'shadow_writer_seen':aliases.get('shadow_writer') in writers,
      'noop_attempt_seen':any(e['rule_name']=='no_op_writer' and not e['progressed'] and not e['node_ids'] and not e['edges']
         for e in report['rule_write_events']),
      'candidate_aliases':[p['alias'] for p in proposals],
      'candidate_count':len(proposals),'active_rule_count':len(active),
      'target_name_passed_to_discovery':False,'cue_passed_to_discovery':False,
      'original_names_passed_to_discovery':False}
    return ctx,proposals,source_map,audit

def score_conversation(base,worker,split,sample,proposal,source):
    ctx=base.conversation_context(fault=True);add_conversation_confounds(ctx);wa=ctx['adapter'];native=ctx['native']
    if proposal is not None:pilot_install(native,source,proposal)
    seq=TRAIN_CONV if split.startswith('train') else HELDOUT_CONV
    counts=[];ids=[]
    for i,(text,act) in enumerate(seq):
        mid=wa.receive_utterance(text,speech_act=act,speaker='user',tick=i);native.run_rules(100)
        ids.append(str(mid));counts.append(sum(1 for reply in wa.agent_outbound_messages() if mid in wa.responds_to(reply)))
    return {'correct':counts==[1]*len(seq),'output_counts':counts,'expected_counts':[1]*len(seq),'input_ids':ids}
def pilot_install(native,source,proposal):
    rows=native.export_rules();hits=[(i,r) for i,r in enumerate(rows) if r.get('name')==source and r.get('active',True)]
    if len(hits)!=1 or not native.remove_rule(hits[0][0]):raise RuntimeError('candidate source is absent/ambiguous')
    clone=copy.deepcopy(proposal);clone['name']=source;native.add_rule(clone)
def score(base,pilot,family,worker,split,sample,proposal,source):
    if family=='recurrence':return pilot.score(base,worker,split,sample,proposal,source)
    return score_conversation(base,worker,split,sample,proposal,source)

def worker_orders(i):
    base,pilot=modules();before=frozen();fam_rows={}
    for family in FAMILIES:
        ctx,props,source_map,audit=trace_for(base,pilot,family,i)
        if not props:raise RuntimeError(f'{family}: no candidates from observed writes: {audit}')
        rng=random.Random(SEED+i*10+FAMILIES.index(family));perm=list(range(len(props)));rng.shuffle(perm);props=[props[j] for j in perm]
        descriptors=[{'proposal_id':p['proposal_id'],'proposal_label':'candidate'} for p in props]
        evidence=[];outcomes=[];train_ns=0
        for p in props:
            trials=[]
            for s in range(REPEATS):
                t=time.perf_counter_ns();out=score(base,pilot,family,i,f'train_{i}',s,p['rule'],source_map[p['proposal_id']]);train_ns+=time.perf_counter_ns()-t
                trials.append(out);evidence.append({'proposal_id':p['proposal_id'],'probe_id':f'{family}_{i}_{s}',
                  'predicted':'correct' if out['correct'] else 'incorrect','expected':'correct'})
            outcomes.append({'proposal_id':p['proposal_id'],'trials':trials})
        t=time.perf_counter_ns();decision=base.selector_decision(ctx['sub'],f'anonymized_transfer_{family}',i,descriptors,evidence);select_ns=time.perf_counter_ns()-t
        decision.pop('proposal_node',None);controls={}
        for ctl in ('tie','all_wrong'):
            d=base.selector_decision(ctx['sub'],f'anonymized_transfer_{family}_{ctl}',i,descriptors,evidence,ctl);d.pop('proposal_node',None);controls[ctl]=d
        selected=decision.get('proposal_id')
        fam_rows[family]={'source_stable':True,'discovery':audit,'candidate_order':[p['proposal_id'] for p in props],
          'candidate_descriptors':descriptors,'candidate_rules':{p['proposal_id']:p['rule'] for p in props},
          'candidate_source_map':source_map,'training_outcomes':outcomes,'training_evidence':evidence,
          'decision':decision,'selected_source':source_map.get(selected),'controls':controls,
          'training_scoring_ns':train_ns,'selection_ns':select_ns}
    after=frozen();return {'worker':i,'source_before':before,'source_after':after,'source_stable':before==after,'families':fam_rows}

def worker_scores(order):
    base,pilot=modules();i=order['worker'];before=frozen();fam_rows={}
    for family in FAMILIES:
        _,props,source_map,audit=trace_for(base,pilot,family,i);byid={p['proposal_id']:p for p in props}
        if audit!=order['families'][family]['discovery']:raise RuntimeError(f'{family}: discovery replay drift')
        if set(byid)!=set(order['families'][family]['candidate_rules']):raise RuntimeError(f'{family}: candidate set drift')
        scores=[]
        for pid in order['families'][family]['candidate_order']:
            p=byid[pid];trials=[score(base,pilot,family,i,f'heldout_{i}',s,p['rule'],source_map[pid]) for s in range(REPEATS)]
            scores.append({'proposal_id':pid,'heldout':trials})
        chosen=order['families'][family]['decision'].get('proposal_id')
        fam_rows[family]={'discovery_replayed':True,'candidate_scores':scores,
            'selected_heldout':[r for r in scores if r['proposal_id']==chosen]}
    after=frozen();return {'worker':i,'source_before':before,'source_after':after,'source_stable':before==after,'families':fam_rows}

def main():
    args=sys.argv[1:]
    if args[:1]==['--worker-orders']:
        print(json.dumps(worker_orders(int(args[1])),sort_keys=True,separators=(',',':')));return 0
    if args[:1]==['--worker-scores']:
        print(json.dumps(worker_scores(json.load(sys.stdin)),sort_keys=True,separators=(',',':')));return 0
    if args==['--lock']:
        if any(p.exists() for p in (LOCK,ORDERS,SCORES,ANALYSIS)):raise SystemExit('refusing to overwrite artifacts')
        LOCK.write_text(json.dumps({'schema':'ThoughtexperimentAnonymizedCauseSiteTransferV1Lock','sources':frozen(),
          'workers':WORKERS,'repeats':REPEATS,'seed':SEED,'families':FAMILIES,
          'controls':['correlated shadow writer','empty-effect no-op'],'training_conversation':TRAIN_CONV,
          'heldout_conversation':HELDOUT_CONV,'candidate_operator':'edge identity guard'},indent=2,sort_keys=True)+'\n')
        print(LOCK.relative_to(ROOT));return 0
    if args in (['--orders'],['--scores']):
        lock=json.loads(LOCK.read_text())
        if frozen()!=lock['sources']:raise SystemExit('source drift from lock')
        env={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}:{ROOT}/evaluation/substrate_capability'}
        if args==['--orders']:
            if ORDERS.exists() or SCORES.exists():raise SystemExit('refusing to overwrite')
            workers=[]
            for i in range(WORKERS):
                p=subprocess.run([sys.executable,str(RUNNER),'--worker-orders',str(i)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=600)
                if p.returncode:raise RuntimeError(f'orders worker {i}: {p.stderr[-4000:]}')
                workers.append(json.loads(p.stdout.strip().splitlines()[-1]))
            dest=ORDERS;payload={'schema':'ThoughtexperimentAnonymizedCauseSiteTransferV1Orders','lock_sha256':sha(LOCK),'workers':workers}
        else:
            if not ORDERS.exists() or SCORES.exists():raise SystemExit('orders missing or scores already exist')
            workers=[]
            for row in json.loads(ORDERS.read_text())['workers']:
                p=subprocess.run([sys.executable,str(RUNNER),'--worker-scores'],input=json.dumps(row),cwd=ROOT,env=env,text=True,capture_output=True,timeout=600)
                if p.returncode:raise RuntimeError(f"scores worker {row['worker']}: {p.stderr[-4000:]}")
                workers.append(json.loads(p.stdout.strip().splitlines()[-1]))
            dest=SCORES;payload={'schema':'ThoughtexperimentAnonymizedCauseSiteTransferV1Scores','lock_sha256':sha(LOCK),'orders_sha256':sha(ORDERS),'workers':workers}
        if frozen()!=lock['sources']:raise SystemExit('source drift during capture')
        payload.update({'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),'sources':frozen()})
        dest.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n');print(dest.relative_to(ROOT));return 0
    if args==['--analyze']:
        p=subprocess.run([sys.executable,str(ANALYZER)],cwd=ROOT,text=True,capture_output=True)
        if p.returncode:raise RuntimeError(p.stderr)
        print(p.stdout.strip());return 0
    raise SystemExit('usage: --lock, --orders, --scores, --analyze, --worker-orders ID')
if __name__=='__main__':raise SystemExit(main())
