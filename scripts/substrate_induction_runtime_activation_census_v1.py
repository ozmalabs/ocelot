#!/usr/bin/env python3
"""Compare actual boot profiles and teaching-path activation for shape growth."""
from __future__ import annotations
import hashlib,json,platform,sys,tempfile
from pathlib import Path

from domains.engine_provenance import engine_preamble,provenance_line
engine_preamble()
from substrate.boot_core import CORE_SEEDS
from substrate.boot_profiles import load_conversation_seed_profile
from substrate.boot_all import load_all_seeds
from substrate.world_adapter import WorldAdapter
from domains.teach import teach
from substrate_rs import _native

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'evaluation/reports/substrate_induction_runtime_activation_census_v1_20260926.json'
SOURCE_PATHS=['scripts/substrate_induction_runtime_activation_census_v1.py','substrate/boot_core.py','substrate/boot_profiles.py','substrate/boot_all.py','substrate/world_adapter.py','domains/teach.py','domains/meta_shape.py','seeds/meta_shape_growth.json','seeds/shape_vocabulary.json','domains/engine_provenance.py','runners/dsl/python/substrate_rs/_native.build.json']
FLAGS=['gen_infer_enabled','time_infer_enabled','depth_infer_enabled','blink_bridge_enabled']

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def seed_ids_from_profile(report):return set(report.get('order') or report.get('selection',{}).get('selected_seed_ids') or [])
def flags(w):
    attrs=w.s.node(w.agent)['attrs']
    return {key:attrs.get(key) for key in FLAGS}
def add_teaching_examples(w,prefix):
    outcomes=[]
    with tempfile.TemporaryDirectory(prefix='induction-activation-') as td:
        for i,attrs in enumerate(({'slot_a':f'{prefix}_one','slot_b':'shared'}, {'slot_a':f'{prefix}_two','slot_b':'shared'})):
            record=teach(w,'ActivationCensusItem',attrs,seeds_dir=td)
            observations=list(w.s.nodes('ShapeObservation'))
            current=observations[-1] if observations else None
            outcomes.append({'teach_saved':record.get('saved'),'status':w.s.node(current)['attrs'].get('status') if current is not None else None,'observation_count':len(observations),'minted_shapes':[w.s.node(n)['attrs'].get('name') for n in w.s.nodes('MetaShape') if str(w.s.node(n)['attrs'].get('name','')).startswith('ms_')]})
    return outcomes
def snapshot(w,seed_order=None,report=None):
    seeds=set(seed_order or ())
    if report:
        seeds=seed_ids_from_profile(report)
    return {'loaded_seed_count':len(seeds),'shape_decode_loop_loaded':'shape_decode_loop' in seeds,'meta_shape_growth_loaded':'meta_shape_growth' in seeds,'shape_vocabulary_loaded':'shape_vocabulary' in seeds,'agent_flags':flags(w)}
def main():
    native_path=Path(_native.__file__).resolve()
    cases=[]
    w=WorldAdapter()
    cases.append({'arm':'WorldAdapter_default_core','before':snapshot(w,CORE_SEEDS),'teach':add_teaching_examples(w,'core')})

    wp=WorldAdapter(seeds=())
    profile=load_conversation_seed_profile(wp)
    pstate=snapshot(wp,report=profile)
    pstate.update({'profile_loaded':profile.get('loaded'),'profile_failed':profile.get('failed'),'profile_complete':profile.get('selection_complete',not bool(profile.get('failed'))),'selected_seed_ids':profile.get('order')})
    cases.append({'arm':'selected_conversation_profile','before':pstate,'teach':add_teaching_examples(wp,'conversation')})

    wg=WorldAdapter(seeds=())
    growth=load_all_seeds(wg,seed_ids={'meta_shape_growth'})
    gstate=snapshot(wg,report=growth)
    gstate.update({'profile_loaded':growth.get('loaded'),'profile_failed':growth.get('failed'),'profile_complete':growth.get('selection_complete',not bool(growth.get('failed'))),'selected_seed_ids':growth.get('order')})
    cases.append({'arm':'explicit_meta_shape_growth_dependency_closure','before':gstate,'teach':add_teaching_examples(wg,'growth')})

    result={'schema_version':1,'run_id':'substrate-induction-runtime-activation-census-v1-20260926','engine':provenance_line(),'python':sys.version,'platform':platform.platform(),'native_extension_path':str(native_path),'native_extension_sha256':sha(native_path),'source_sha256':{p:sha(ROOT/p) for p in SOURCE_PATHS},'core_seed_ids':list(CORE_SEEDS),'cases':cases,'scope':'One process, three fresh WorldAdapter instances. Measures the two-item teach path under default core, selected production conversation profile, and explicit MetaShape-growth profile. Does not measure other producers, natural teach-task prevalence, or scaling.'}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'output':str(OUT),'cases':[{'arm':c['arm'],'before':{k:v for k,v in c['before'].items() if k not in ('selected_seed_ids',)},'teach':c['teach']} for c in cases]},indent=2))
if __name__=='__main__':main()
