#!/usr/bin/env python3
"""Probe whether ordinary full-profile conversation reaches MetaShape teaching."""
from __future__ import annotations
import hashlib, json, os, platform, sys, time
from pathlib import Path

os.environ['OZMA_SEED_PERSIST_DISABLED']='1'
from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()
from substrate.boot_all import load_all_seeds
from substrate.world_adapter import WorldAdapter
from substrate_rs import _native

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'evaluation/reports/substrate_daemon_conversation_metashape_bridge_v1_20260926.json'
LOCK=ROOT/'evaluation/substrate_capability/daemon_conversation_metashape_bridge_v1_lock_20260926.json'
TEXTS=('A dax has a red shell.','A wug has a blue shell.','A dax has a red shell.','A wug has a blue shell.')
SOURCES=['scripts/substrate_daemon_conversation_metashape_bridge_v1.py','scripts/jabberwock_daemon.py','substrate/world_adapter.py','substrate/boot_all.py','domains/teach.py','domains/meta_shape.py','seeds/meta_shape_growth.json','domains/engine_provenance.py','runners/dsl/python/substrate_rs/_native.build.json']

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def counts(adapter):
    return {kind:len(list(adapter.s.nodes(kind))) for kind in ('ShapeObservation','MetaShape','TaughtHint','TeacherEvidence')}
def snapshot(adapter):
    return {'counts':counts(adapter),
            'shape_observations':[{'id':str(n),'status':adapter.s.node(n)['attrs'].get('status')} for n in adapter.s.nodes('ShapeObservation')],
            'meta_shapes':[{'id':str(n),'name':adapter.s.node(n)['attrs'].get('name')} for n in adapter.s.nodes('MetaShape')]}

def main():
    lock=json.loads(LOCK.read_text())
    observed_lock={p:sha(ROOT/p) for p in lock['source_sha256']}
    if observed_lock!=lock['source_sha256']:
        raise RuntimeError('locked source digest mismatch; re-lock before execution')
    native_path=Path(_native.__file__).resolve()
    adapter=WorldAdapter(seeds=())
    boot_started=time.perf_counter_ns(); load=load_all_seeds(adapter)
    boot_ms=(time.perf_counter_ns()-boot_started)/1e6
    baseline=snapshot(adapter); turns=[]; teach_events=[]; pending=[]
    teach_path=(ROOT/'domains/teach.py').resolve()
    def profiler(frame,event,arg):
        if Path(frame.f_code.co_filename).resolve()!=teach_path or frame.f_code.co_name!='teach': return
        if event=='call':
            pending.append({'type':frame.f_locals.get('type_'),'attrs':frame.f_locals.get('attrs')})
        elif event=='return' and pending:
            started=pending.pop()
            result=arg if isinstance(arg,dict) else {}
            teach_events.append({'type':started['type'],'category':result.get('category'),'saved':result.get('saved'),'persisted':result.get('persisted')})
    prior_profile=sys.getprofile(); sys.setprofile(profiler)
    try:
        for index,text in enumerate(TEXTS,1):
            started=time.perf_counter_ns(); reply=adapter.converse(text,speech_act='statement',speaker='user')
            elapsed_ms=(time.perf_counter_ns()-started)/1e6
            current=snapshot(adapter)
            turns.append({'turn':index,'text':text,'reply':str(reply),'elapsed_ms':elapsed_ms,'snapshot':current,
                          'count_delta':{k:current['counts'][k]-baseline['counts'][k] for k in baseline['counts']}})
    finally:
        sys.setprofile(prior_profile)
    raw={'schema_version':1,'run_id':'substrate-daemon-conversation-metashape-bridge-v1-20260926',
         'engine':provenance_line(),'python':sys.version,'platform':platform.platform(),
         'native_extension_path':str(native_path),'native_extension_sha256':sha(native_path),
         'source_sha256':{p:sha(ROOT/p) for p in SOURCES},
         'protocol_sha256':sha(ROOT/'docs/research/engine_substrate/SUBSTRATE_DAEMON_CONVERSATION_METASHAPE_BRIDGE_PREREG_20260926.md'),
         'lock_sha256':sha(LOCK),
         'seed_load':{'loaded':load.get('loaded'),'total':load.get('total'),'failed':load.get('failed',[]),'selected_order_count':len(load.get('order') or [])},
         'seed_persistence_disabled':os.environ.get('OZMA_SEED_PERSIST_DISABLED')=='1',
         'boot_elapsed_ms':boot_ms,'baseline':baseline,'turns':turns,'teach_calls':teach_events,
         'scope':'One process, one fresh daemon-full-equivalent adapter, four fixed repeated ordinary utterances through WorldAdapter.converse. No explicit TeacherRequest, teach(), or external teacher injection; seed persistence guard enabled. Not a prevalence or learning-quality estimate.'}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(raw,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'output':str(OUT),'seed_load':raw['seed_load'],'baseline':baseline,
                      'turns':[{'turn':t['turn'],'elapsed_ms':t['elapsed_ms'],'count_delta':t['count_delta'],'reply':t['reply']} for t in turns],
                      'teach_calls':teach_events},indent=2))
if __name__=='__main__': main()
