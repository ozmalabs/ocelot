#!/usr/bin/env python3
"""Generate bounded graph rules for source-bound perceptual numerosity."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'seeds'/'numerosity.json'
AREA='perceptual_numerosity'
def V(n): return {'type':'Var','name':n}
def L(x): return {'type':'Lit','value':x}
def T(x): return {'__term__':x}
def A(n,k): return {'type':'Attr','node':V(n),'key':k}
def N(n,e): return {'type':'Neighbours','node':V(n),'edge_type':e,'any_type':False}
def Eq(a,b): return {'type':'Eq','a':a,'b':b}
def Not(x): return {'type':'Not','arg':x}
def And(*xs): return {'type':'And','items':list(xs)}
def Or(*xs): return {'type':'Or','items':list(xs)}
def Gt(a,b): return {'type':'Gt','a':a,'b':b}
def Gte(a,b): return {'type':'Gte','a':a,'b':b}
def Lt(a,b): return {'type':'Lt','a':a,'b':b}
def Count(s): return {'type':'Count','source':s}
def Times(a,b): return {'type':'Times','items':[a,b]}
def Plus(*xs): return {'type':'Plus','items':list(xs)}
def Minus(a,b): return {'type':'Minus','a':a,'b':b}
def Div(a,b): return {'type':'Div','a':a,'b':b}

def build_seed():
    relations=[('Agent','has_numerosity_policy','NumerosityPolicy'),('Agent','has_numerosity_request','NumerosityCompareRequest'),('NumerosityCompareRequest','compares_group_a','NumerosityGroup'),('NumerosityCompareRequest','compares_group_b','NumerosityGroup'),('NumerosityGroup','has_individuated_object','NumerosityObject'),('NumerosityGroup','observed_in_scene','NumerosityScene'),('Agent','has_numerosity_scene','NumerosityScene'),('NumerosityScene','has_numerosity_group','NumerosityGroup')]
    base=[['ag','has_numerosity_policy','pol'],['ag','has_numerosity_request','req'],['req','compares_group_a','ga'],['req','compares_group_b','gb']]
    eligible=And(Eq(A('pol','enabled'),L(1.0)),Eq(A('req','status'),L('pending')),Eq(A('req','owner_id'),A('ga','owner_id')),Eq(A('req','owner_id'),A('gb','owner_id')),Eq(A('req','source_epoch'),A('ga','source_epoch')),Eq(A('req','source_epoch'),A('gb','source_epoch')),Eq(A('req','frame_epoch'),A('ga','frame_epoch')),Eq(A('req','frame_epoch'),A('gb','frame_epoch')),Eq(A('ga','status'),L('observed')),Eq(A('gb','status'),L('observed')))
    small=And(eligible,Eq(A('ga','mode'),L('small')),Eq(A('gb','mode'),L('small')),Eq(A('ga','individuation_status'),L('clear')),Eq(A('gb','individuation_status'),L('clear')),Lt(Count(N('ga','has_individuated_object')),L(5)),Lt(Count(N('gb','has_individuated_object')),L(5)))
    rules=[]
    for name,cond,result in [('small_more',Gt(Count(N('ga','has_individuated_object')),Count(N('gb','has_individuated_object'))),'MORE'),('small_less',Lt(Count(N('ga','has_individuated_object')),Count(N('gb','has_individuated_object'))),'LESS'),('small_same',Eq(Count(N('ga','has_individuated_object')),Count(N('gb','has_individuated_object'))),'SAME_WITHIN_RESOLUTION')]:
        rules.append({'name':'num_'+name,'area':AREA,'order':10,'latency_class':'hard_realtime','batch':False,'match':base,'where':And(small,cond),'effects':[['set_attr','req','status','completed'],['set_attr','req','result',result],['set_attr','req','method','individuated_tokens'],['set_attr','req','evidence_status','observed'],['set_attr','req','exact_a',T(Count(N('ga','has_individuated_object')))],['set_attr','req','exact_b',T(Count(N('gb','has_individuated_object')))]]})
    ambiguous=And(eligible,Eq(A('ga','mode'),L('small')),Eq(A('gb','mode'),L('small')),Or(Eq(A('ga','individuation_status'),L('ambiguous')),Eq(A('gb','individuation_status'),L('ambiguous')),Gte(Count(N('ga','has_individuated_object')),L(5)),Gte(Count(N('gb','has_individuated_object')),L(5))))
    rules.append({'name':'num_small_ambiguous_abstain','area':AREA,'order':11,'latency_class':'hard_realtime','batch':False,'match':base,'where':ambiguous,'effects':[['set_attr','req','status','completed'],['set_attr','req','result','UNKNOWN'],['set_attr','req','method','abstain'],['set_attr','req','evidence_status','observed']]})
    center_a=Times(A('ga','occupied_area'),A('ga','density_signal')); center_b=Times(A('gb','occupied_area'),A('gb','density_signal'))
    error_a=Plus(Times(A('ga','area_uncertainty'),A('ga','density_signal')),Times(A('ga','occupied_area'),A('ga','density_uncertainty')))
    error_b=Plus(Times(A('gb','area_uncertainty'),A('gb','density_signal')),Times(A('gb','occupied_area'),A('gb','density_uncertainty')))
    lower_a=Minus(center_a,error_a); upper_a=Plus(center_a,error_a)
    lower_b=Minus(center_b,error_b); upper_b=Plus(center_b,error_b)
    aggregate=And(eligible,Eq(A('ga','mode'),L('aggregate')),Eq(A('gb','mode'),L('aggregate')),Not(Eq(A('ga','occupied_area'),L(None))),Not(Eq(A('gb','occupied_area'),L(None))),Not(Eq(A('ga','density_signal'),L(None))),Not(Eq(A('gb','density_signal'),L(None))),Gte(A('ga','occupied_area'),L(0.0)),Gte(A('gb','occupied_area'),L(0.0)),Gte(A('ga','density_signal'),L(0.0)),Gte(A('gb','density_signal'),L(0.0)),Gte(A('ga','area_uncertainty'),L(0.0)),Gte(A('gb','area_uncertainty'),L(0.0)),Gte(A('ga','density_uncertainty'),L(0.0)),Gte(A('gb','density_uncertainty'),L(0.0)),Gt(center_b,L(0.0)))
    cue_conflict=Or(And(Gt(A('ga','occupied_area'),A('gb','occupied_area')),Lt(A('ga','density_signal'),A('gb','density_signal'))),And(Lt(A('ga','occupied_area'),A('gb','occupied_area')),Gt(A('ga','density_signal'),A('gb','density_signal'))))
    common=['set_attr','req','result']
    def outcome(name,where,result):
        return {'name':'num_aggregate_'+name,'area':AREA,'order':12,'latency_class':'hard_realtime','batch':False,'match':base,'where':And(aggregate,where),'effects':[['set_attr','req','status','completed'],['set_attr','req','result',result],['set_attr','req','method','aggregate_interval'],['set_attr','req','evidence_status','observed'],['set_attr','req','estimate_a',T(center_a)],['set_attr','req','estimate_b',T(center_b)],['set_attr','req','lower_a',T(lower_a)],['set_attr','req','upper_a',T(upper_a)],['set_attr','req','lower_b',T(lower_b)],['set_attr','req','upper_b',T(upper_b)],['set_attr','req','ratio_estimate',T(Div(center_a,center_b))]]}
    rules += [outcome('conflict',cue_conflict,'UNKNOWN'),outcome('more',And(Not(cue_conflict),Gt(lower_a,upper_b)),'MORE'),outcome('less',And(Not(cue_conflict),Gt(lower_b,upper_a)),'LESS')]
    same=And(Not(cue_conflict),Lt(Minus(center_a,center_b),A('pol','resolution_tolerance')),Lt(Minus(center_b,center_a),A('pol','resolution_tolerance')),Lt(Plus(error_a,error_b),A('pol','max_uncertainty')))
    rules.append(outcome('same',same,'SAME_WITHIN_RESOLUTION'))
    more=And(Not(cue_conflict),Gt(lower_a,upper_b))
    less=And(Not(cue_conflict),Gt(lower_b,upper_a))
    unresolved=And(Not(cue_conflict),Not(more),Not(less),Not(same))
    rules.append(outcome('unresolved_abstain',unresolved,'UNKNOWN'))
    return {'id':'numerosity','version':'1.0.0','depends_on':['thinking_budget','qualia_acquisition'],'self_load_only':True,'area':AREA,'description':'P7.05: bounded exact small-set comparison and uncertainty-aware aggregate perceptual comparison.','microtheory':{'name':AREA,'description':'Perceive small individuated sets and compare larger aggregate visual evidence without hidden cardinalities.'},'nodes':[{'local_id':0,'type':'NumerosityPolicy','attrs':{'name':'numerosity_policy','enabled':0.0,'small_set_limit':4.0,'max_scene_regions':4096.0,'max_decision_steps':64.0,'max_graph_objects':512.0,'resolution_tolerance':0.1,'max_uncertainty':0.25}}],'edges':[{'src':{'role':'agent_root'},'type':'has_numerosity_policy','tgt':{'local':0},'attrs':{}}],'productions':[{'provenance':f'seed:{AREA}:{e}:{s}:{t}','src':{'type':s,'var':'src'},'edge_type':e,'tgt':{'type':t,'var':'tgt'}} for s,e,t in relations],'rules':rules}

if __name__=='__main__':
    OUT.write_text(json.dumps(build_seed(),indent=2,ensure_ascii=False)+'\n',encoding='utf-8');print(OUT)
