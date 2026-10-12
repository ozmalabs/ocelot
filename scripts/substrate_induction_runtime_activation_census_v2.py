#!/usr/bin/env python3
"""Measure MetaShape teaching activation in the daemon's actual fresh-boot arms."""
from __future__ import annotations
import hashlib, json, platform, sys, tempfile
from pathlib import Path

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()
from domains.teach import teach
from substrate.boot_all import load_all_seeds
from substrate.boot_core import CORE_SEEDS
from substrate.world_adapter import WorldAdapter
from substrate.seed_loader import manifest_for
from substrate_rs import _native

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'evaluation/reports/substrate_induction_runtime_activation_census_v2_20260926.json'
FLAGS = ['gen_infer_enabled','time_infer_enabled','depth_infer_enabled','blink_bridge_enabled']
SOURCES = ['scripts/substrate_induction_runtime_activation_census_v2.py','scripts/jabberwock_daemon.py','substrate/boot_core.py','substrate/boot_all.py','substrate/seed_loader.py','substrate/world_adapter.py','domains/teach.py','domains/meta_shape.py','seeds/meta_shape_growth.json','seeds/shape_vocabulary.json','domains/engine_provenance.py','runners/dsl/python/substrate_rs/_native.build.json']

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def teach_twice(adapter, tag):
    out=[]
    with tempfile.TemporaryDirectory(prefix='induction-activation-v2-') as td:
        for attrs in ({'slot_a':tag+'_one','slot_b':'shared'}, {'slot_a':tag+'_two','slot_b':'shared'}):
            rec=teach(adapter,'ActivationCensusItem',attrs,seeds_dir=td)
            obs=list(adapter.s.nodes('ShapeObservation'))
            current=obs[-1] if obs else None
            out.append({'saved':rec.get('saved'),'status':adapter.s.node(current)['attrs'].get('status') if current is not None else None,
                        'observation_count':len(obs),'minted_meta_shapes':[adapter.s.node(n)['attrs'].get('name') for n in adapter.s.nodes('MetaShape')]})
    return out

def run_arm(name, adapter, order, load_report=None, load_failures=None):
    baseline_shapes=[adapter.s.node(n)['attrs'].get('name') for n in adapter.s.nodes('MetaShape')]
    before={'seed_ids_selected_or_attempted':len(order),'shape_decode_loop_loaded':'shape_decode_loop' in order,
            'meta_shape_growth_loaded':'meta_shape_growth' in order,'shape_vocabulary_loaded':'shape_vocabulary' in order,
            'flags':{key:adapter.s.node(adapter.agent)['attrs'].get(key) for key in FLAGS}}
    if load_failures is not None: before['seed_load_failures']=load_failures
    if load_report is not None:
        before.update({'loader_loaded':load_report.get('loaded'),'loader_total':load_report.get('total'),
                       'loader_failed':load_report.get('failed',[]),'loader_complete':not bool(load_report.get('failed'))})
    teaching=teach_twice(adapter,name)
    teaching[-1]['new_meta_shapes']=[n for n in teaching[-1]['minted_meta_shapes'] if n not in baseline_shapes]
    return {'arm':name,'before':before,'baseline_meta_shapes':baseline_shapes,'teach':teaching}

def main():
    cases=[]
    # Match jabberwock_daemon.boot() fresh-boot seed branches. Checkpoint resume
    # is excluded because it depends on an external serialized prior state.
    full=WorldAdapter(seeds=()); report=load_all_seeds(full)
    full_order=set(report.get('order') or [])
    cases.append(run_arm('daemon_full',full,full_order,report))

    from scripts.jabberwock_daemon import CHAT_SEEDS
    chat=WorldAdapter()
    chat_order=set(CORE_SEEDS)
    chat_failures=[]
    for seed_id in CHAT_SEEDS:
        try:
            chat.inner.load_seed_manifest(manifest_for(seed_id),chat.agent)
            chat_order.add(seed_id)
        except Exception as exc:
            chat_failures.append(f'{seed_id}:{type(exc).__name__}:{exc}')
    cases.append(run_arm('daemon_chat',chat,chat_order,load_failures=chat_failures))

    embodied=WorldAdapter(seeds=('embodied_motor_bootstrap','embodied_instruction_goal','comprehend_instruction','learned_lexicon','energy_ledger','surprise_promotion','imagination_trace_retention'))
    embodied_order={'embodied_motor_bootstrap','embodied_instruction_goal','comprehend_instruction','learned_lexicon','energy_ledger','surprise_promotion','imagination_trace_retention'}
    cases.append(run_arm('daemon_embodied',embodied,embodied_order,load_failures=[]))

    raw={'schema_version':2,'run_id':'substrate-induction-runtime-activation-census-v2-20260926',
         'engine':provenance_line(),'python':sys.version,'platform':platform.platform(),
         'native_extension_path':str(Path(_native.__file__).resolve()),'native_extension_sha256':sha(_native.__file__),
         'source_sha256':{p:sha(ROOT/p) for p in SOURCES},'core_seed_ids':list(CORE_SEEDS),
         'chat_seed_ids':CHAT_SEEDS,'cases':cases,
         'scope':'One process, fresh adapters reproducing the daemon full, chat, and embodied boot branches. Checkpoint resume is excluded. Two intentionally repeated authored teach() examples probe MetaShape activation, not natural frequency or learning quality.'}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(raw,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'output':str(OUT),'arms':[{'arm':c['arm'],'before':c['before'],'statuses':[x['status'] for x in c['teach']],'new_meta_shapes':[n for n in c['teach'][-1]['minted_meta_shapes'] if n not in c['baseline_meta_shapes']]} for c in cases]},indent=2))

if __name__=='__main__': main()
