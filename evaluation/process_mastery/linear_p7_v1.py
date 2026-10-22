"""Frozen P7 mechanism runner for episode-built distinctions and numerosity.

Python constructs source observations and scores detached labels. Acquisition and
comparison decisions run only in Rust graph rules. The synthetic sensory adapter
is a mechanism fixture, not a real-world perception claim.
"""
from __future__ import annotations
import argparse, hashlib, json, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT/'runners/dsl/python'):
    if str(p) not in sys.path: sys.path.insert(0,str(p))
from substrate_rs import _native
from scripts.gen_qualia_acquisition_seed import build_seed as qa_seed
from scripts.gen_numerosity_seed import build_seed as num_seed
from evaluation.process_mastery.scorecard import write_scorecard
PHASE='linear-p7-v1'
SEED_BLOCKS={'qualia_tool':(2_000_000,40),'qualia_social':(2_000_040,40),
 'tool_label_shuffled':(2_000_080,100),'tool_exposure_only':(2_000_180,100),'tool_orthogonal':(2_000_280,100),
 'social_label_shuffled':(2_000_380,100),'social_exposure_only':(2_000_480,100),'social_orthogonal':(2_000_580,100),
 'small_sets':(2_001_000,200),'ratio_1_1':(2_001_200,200),
 'ratio_1_25':(2_001_400,200),'ratio_1_5':(2_001_600,200),'ratio_2':(2_001_800,200)}
LIMITS={'episodes_per_distinction':5,'validation_episodes':2,'max_rule_steps':2000,
        'small_limit':4,'aggregate_regions':4096,'max_graph_objects':512}

def sha(data): return hashlib.sha256(data).hexdigest()
def provenance():
    paths=['evaluation/process_mastery/linear_p7_v1.py','evaluation/process_mastery/analyze_linear_p7_v1.py',
      'scripts/gen_qualia_acquisition_seed.py','seeds/qualia_acquisition.json',
      'scripts/gen_numerosity_seed.py','seeds/numerosity.json','domains/number_world.py',
      'substrate/boot_profiles.py','docs/research/engine_substrate/COGNITION_QUALIA_ACQUISITION_CONTRACT.md',
      'docs/research/engine_substrate/COGNITION_NUMEROSITY_CONTRACT.md']
    h=hashlib.sha256()
    for rel in paths: h.update(rel.encode()+b'\0'+(ROOT/rel).read_bytes()+b'\0')
    engine=hashlib.sha256()
    for rel in ['runners/dsl/Cargo.toml','runners/dsl/src/term.rs','runners/dsl/src/eval.rs']:
      path=ROOT/rel
      if path.exists(): engine.update(rel.encode()+b'\0'+path.read_bytes()+b'\0')
    try: commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    except Exception: commit='unavailable'
    import substrate_rs
    return {'phase':PHASE,'git_commit':commit,'source_bundle_sha256':h.hexdigest(),
      'engine_source_sha256':engine.hexdigest(),'engine_binary_sha256':sha(Path(substrate_rs.__file__).read_bytes()),
      'python':sys.version.split()[0],'limits':LIMITS,'seed_blocks':SEED_BLOCKS}

def boot(*,acquisition=True,numerosity=False):
    s=_native.Substrate(); ag=s.add_node('Agent',{})
    for name in ('default_mode_core','thinking_budget','qualia_space','cognition_signature'):
      s.load_seed_manifest(json.loads((ROOT/'seeds'/f'{name}.json').read_text()),ag)
    from scripts.gen_experience_signature_seed import build_seed as exp_seed
    s.load_seed_manifest(exp_seed(),ag)
    s.load_seed_manifest(qa_seed(),ag)
    s.load_seed_manifest(num_seed(),ag)
    for n in s.nodes('ThinkingBudget'):
      s.set_attr(n,'enabled',1.0);s.set_attr(n,'remaining',100.0);s.set_attr(n,'last_refill_epoch',10.0)
    s.set_attr(s.nodes('NetworkModeState')[0],'epoch',10.0)
    s.set_attr(s.nodes('QualiaAcquisitionPolicy')[0],'enabled',1.0 if acquisition else 0.0)
    s.set_attr(s.nodes('NumerosityPolicy')[0],'enabled',1.0 if numerosity else 0.0)
    return s,ag

def tick(s):
    for _ in range(30):
      if not s.run_rules(LIMITS['max_rule_steps']): return
    raise RuntimeError('native P7 rules did not reach fixpoint')

def episode(s,ag,i,feature,value,outcome,*,owner='owner-a',receipt=True,label=None):
    epid=f'ep-{i}'; eventid=f'event-{i}'; fid=f'feature-{i}'
    ep=s.add_node('ExperienceEpisode',{'owner_id':owner,'episode_id':epid,'context_id':f'context-{i}','status':'observed'})
    ev=s.add_node('ExperienceEvent',{'owner_id':owner,'episode_id':epid,'event_id':eventid,'action_id':f'action-{i}','frame_id':f'frame-{i}','status':'observed','source_epoch':3,'model_epoch':2,'frame_epoch':5})
    f=s.add_node('ExperienceFeatureObservation',{'owner_id':owner,'episode_id':epid,'event_id':eventid,'feature_id':fid,'feature_key':feature,'feature_family':'tool_contact' if feature.startswith('tool') else 'social_request_repair','feature_value':value,'value_kind':'symbol','grain':0.0,'is_missing':False,'source_epoch':3,'model_epoch':2,'frame_epoch':5,'status':'observed'})
    s.add_edge(ag,'has_experience_episode',ep);s.add_edge(ep,'has_experience_event',ev);s.add_edge(ev,'has_episode_feature',f)
    if receipt:
      rec=s.add_node('ExperienceOutcomeReceipt',{'owner_id':owner,'episode_id':epid,'event_id':eventid,'feature_id':fid,'source_epoch':3,'model_epoch':2,'frame_epoch':5,'status':'observed','evidence_status':'observed','consequence_kind':'measured_outcome','consequence_value':outcome})
      s.add_edge(f,'has_outcome_receipt',rec)
    if label is not None:
      # Detached scorer annotation is deliberately never attached to agent input.
      pass

def qualia_trial(seed,family,*,track):
    s,ag=boot(acquisition=track)
    feature='tool-contact-pattern' if family=='tool' else 'social-repair-pattern'
    values=('rough','smooth') if family=='tool' else ('repair-needed','repair-not-needed')
    outcomes=('repair','continue') if family=='tool' else ('repair-request','normal-response')
    maps=[(values[0],outcomes[0]),(values[1],outcomes[1]),(values[0],outcomes[0]),(values[1],outcomes[1]),(values[0],outcomes[0])]
    t0=time.perf_counter()
    for j,(v,o) in enumerate(maps): episode(s,ag,seed*10+j,feature,v,o)
    tick(s)
    candidates=s.nodes('QualiaAxisCandidate')
    validated=any(s.node(n)['attrs'].get('status')=='validated' for n in candidates)
    leaked=any(any(k in s.node(n)['attrs'] for k in ('target_dimension','expected_class','answer','hidden_count')) for typ in ('ExperienceEpisode','ExperienceEvent','ExperienceFeatureObservation') for n in s.nodes(typ))
    return {'family':'qualia_'+family,'seed':seed,'profile':'experience-built' if track else 'frozen-space','status':'COMPLETED',
      'outcome':'validated_distinction' if validated else 'no_distinction','external_outcome':{'pass':validated},
      'source_leaks':int(leaked),'compute':{'rule_ticks':'bounded_fixpoint','seconds':round(time.perf_counter()-t0,6),'episodes':5,'graph_nodes':len(s.nodes())},
      'input_labels_exposed':False,'truth':{'distinction':True}}

def control_trial(seed,family,kind):
    s,ag=boot(acquisition=True)
    key='tool-contact-pattern' if family=='tool' else 'social-repair-pattern'
    vals=('rough','smooth','rough') if family=='tool' else ('repair-needed','repair-not-needed','repair-needed')
    outs=('repair','continue','ignore') if kind=='orthogonal' else (('repair','continue','repair') if family=='tool' else ('repair-request','normal-response','repair-request'))
    for j in range(3): episode(s,ag,seed*10+j,key,vals[j],outs[j],receipt=(kind!='exposure_only'))
    tick(s)
    has=bool(s.nodes('QualiaAxisCandidate'))
    return {'family':f'{family}_{kind}','seed':seed,'profile':'experience-built','status':'COMPLETED',
      'outcome':'candidate' if has else 'no_candidate','external_outcome':{'pass':(has if kind=='label_shuffled' else not has)},
      'source_leaks':0,'input_labels_exposed':False,
      'detached_scorer_labels':(['failure','success','success'] if kind=='label_shuffled' else None)}

def number_trial(seed,ratio=None,small=False):
    from domains.number_world import perceptual_scene_attrs
    s,ag=boot(acquisition=False,numerosity=True)
    def grp(name,area,density,mode):
      attrs=perceptual_scene_attrs(scene_id=name,owner_id='owner-a',source_epoch=2,frame_epoch=5,mode=mode,scene_regions=1,individuation_status='clear' if mode=='small' else None,occupied_area=area,density_signal=density,area_uncertainty=.01,density_uncertainty=.01) if mode=='aggregate' else perceptual_scene_attrs(scene_id=name,owner_id='owner-a',source_epoch=2,frame_epoch=5,mode='small',scene_regions=int(area),individuation_status='clear')
      scene=s.add_node('NumerosityScene',attrs);g=s.add_node('NumerosityGroup',{**attrs,'group_id':name});s.add_edge(ag,'has_numerosity_scene',scene);s.add_edge(scene,'has_numerosity_group',g);s.add_edge(g,'observed_in_scene',scene)
      if mode=='small':
        for k in range(int(area)):
          obj=s.add_node('NumerosityObject',{'object_id':f'{name}-{k}','owner_id':'owner-a','source_epoch':2,'frame_epoch':5,'status':'observed'});s.add_edge(g,'has_individuated_object',obj)
      return g
    if small:
      a=grp(f'a-{seed}',seed%5,0,'small');b=grp(f'b-{seed}',(seed*3)%5,0,'small');expected='MORE' if seed%5>(seed*3)%5 else 'LESS' if seed%5<(seed*3)%5 else 'SAME_WITHIN_RESOLUTION'
    else:
      a=grp(f'a-{seed}',ratio,2.0,'aggregate');b=grp(f'b-{seed}',1.0,2.0,'aggregate');expected='MORE'
    req=s.add_node('NumerosityCompareRequest',{'request_id':str(seed),'owner_id':'owner-a','source_epoch':2,'frame_epoch':5,'status':'pending'})
    s.add_edge(ag,'has_numerosity_request',req);s.add_edge(req,'compares_group_a',a);s.add_edge(req,'compares_group_b',b)
    tick(s);actual=s.node(req)['attrs'].get('result');passed=actual==expected
    return {'family':'numerosity_small' if small else f'numerosity_ratio_{ratio}','seed':seed,'profile':'perceptual-graph','status':'COMPLETED' if actual else 'UNSUPPORTED','outcome':actual,'external_outcome':{'pass':passed},'truth':{'relation':expected},'hidden_truth_exposed':False,'compute':{'graph_nodes':len(s.nodes())}}

def run(*,split='development',self_check=False,n=None):
    if self_check:
      rows=[qualia_trial(1,'tool',track=False),qualia_trial(1,'tool',track=True),control_trial(10,'tool','label_shuffled'),control_trial(11,'tool','exposure_only'),control_trial(12,'tool','orthogonal'),number_trial(20,small=True),number_trial(21,ratio=1.5)]
    else:
      n=200 if n is None else n
      if n!=200: raise ValueError('registered P7 allocation fixes 200 per family/ratio bin')
      offset=2_000_000 if split=='heldout' else 0;rows=[]
      for family,block in [('tool',0),('social',40)]:
        for i in range(n//5):
          seed=offset+block+i; rows.append(qualia_trial(seed,family,track=False));rows.append(qualia_trial(seed,family,track=True))
      for family,base in [('tool',80),('social',380)]:
        for k,kind in enumerate(('label_shuffled','exposure_only','orthogonal')):
          for i in range(100): rows.append(control_trial(offset+base+k*100+i,family,kind))
      for i in range(n): rows.append(number_trial(offset+1000+i,small=True))
      for ratio,block in ((1.1,1200),(1.25,1400),(1.5,1600),(2.0,1800)):
        for i in range(n): rows.append(number_trial(offset+block+i,ratio=ratio))
    return {'schema':'pmb-scorecard-v1','metadata':{**provenance(),'split':split,'registered_draw':not self_check,'n_records':len(rows)},'records':rows}

def main():
    p=argparse.ArgumentParser();p.add_argument('--split',choices=('development','heldout'),default='development');p.add_argument('--n',type=int);p.add_argument('--output',type=Path);p.add_argument('--self-check',action='store_true');a=p.parse_args()
    result=run(split=a.split,n=a.n,self_check=a.self_check)
    if a.output: write_scorecard(a.output,metadata=result['metadata'],records=result['records'])
    else: print(json.dumps(result,indent=2,sort_keys=True))
    if a.self_check:
      assert len(result['records'])==7 and all(r.get('status') in ('COMPLETED','UNSUPPORTED') for r in result['records'])
      print('linear_p7 runner self-check: PASS')
if __name__=='__main__': main()
