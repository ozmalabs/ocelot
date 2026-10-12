#!/usr/bin/env python3
"""Independently derive graph-field deltas and audit event attribution."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CAPTURE=ROOT/'evaluation/reports/thoughtexperiment_event_value_attribution_v1_2_8_20261005.json'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_event_value_attribution_v1_2_8_lock_20261005.json'
RUNNER=ROOT/'evaluation/substrate_capability/thoughtexperiment_event_value_attribution_v1_2_8.py'
ANALYZER=Path(__file__).resolve()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def derive(before,after):
    out=[]
    bn={int(x['id']):x for x in before['nodes']};an={int(x['id']):x for x in after['nodes']}
    for ident in sorted(bn.keys()|an.keys()):
        b,a=bn.get(ident),an.get(ident)
        if b is None or a is None:out.append({'entity':'node','id':ident,'field':'existence','before':b,'after':a});continue
        if b['type']!=a['type']:out.append({'entity':'node','id':ident,'field':'type','before':b['type'],'after':a['type']})
        ba,aa=b.get('attrs',{}),a.get('attrs',{})
        for key in sorted(ba.keys()|aa.keys()):
            if (key in ba)!=(key in aa) or (key in ba and ba[key]!=aa[key]):out.append({'entity':'node','id':ident,'field':'attr:'+key,'before':ba.get(key,'<ABSENT>'),'after':aa.get(key,'<ABSENT>')})
    def edge_map(g):return {(int(e['src']),e['type'],int(e['tgt'])):e.get('attrs',{}) for e in g['edges']}
    be,ae=edge_map(before),edge_map(after)
    for key in sorted(be.keys()|ae.keys()):
        b,a=be.get(key),ae.get(key)
        if b is None or a is None:out.append({'entity':'edge','key':list(key),'field':'existence','before':b,'after':a});continue
        for attr in sorted(b.keys()|a.keys()):
            if (attr in b)!=(attr in a) or (attr in b and b[attr]!=a[attr]):out.append({'entity':'edge','key':list(key),'field':'attr:'+attr,'before':b.get(attr,'<ABSENT>'),'after':a.get(attr,'<ABSENT>')})
    return out
def candidates(change,events):
    out=[]
    for index,event in enumerate(events):
        if not event['progressed']:continue
        if change['entity']=='node':covered=int(change['id']) in set(map(int,event['node_ids']))
        else:covered=tuple(change['key']) in {(int(e[0]),str(e[1]),int(e[2])) for e in event['edges']}
        if covered:out.append(index)
    return out

def replay_event_values(initial, final, events):
    nodes={int(n['id']):{'type':n['type'],'attrs':n.get('attrs',{})} for n in initial['nodes']}
    edges={(int(e['src']),str(e['type']),int(e['tgt'])):e.get('attrs',{}) for e in initial['edges']}
    complete=True; before_match=True
    for event in events:
        complete &= not event.get('values_truncated', True)
        for item in event.get('node_values',[]):
            ident=int(item['node_id']); current=nodes.get(ident)
            before_match &= current==item['before']
            if item['after'] is None: nodes.pop(ident,None)
            else: nodes[ident]=item['after']
        for item in event.get('edge_values',[]):
            edge=(int(item['edge'][0]),str(item['edge'][1]),int(item['edge'][2]))
            current=edges.get(edge)
            before_match &= current==item['before']
            if item['after'] is None: edges.pop(edge,None)
            else: edges[edge]=item['after']
    expected_nodes={int(n['id']):{'type':n['type'],'attrs':n.get('attrs',{})} for n in final['nodes']}
    expected_edges={(int(e['src']),str(e['type']),int(e['tgt'])):e.get('attrs',{}) for e in final['edges']}
    return {'complete':bool(complete),'event_before_values_match_ordered_replay':bool(before_match),
            'replayed_final_nodes_match':nodes==expected_nodes,'replayed_final_edges_match':edges==expected_edges}
def main():
    analyzer_hash=sha(ANALYZER);d=json.loads(CAPTURE.read_text());lock=json.loads(LOCK.read_text());workers=d['workers'];pids=[w['pid'] for w in workers]
    semantic=lambda w:[{k:v for k,v in f.items() if k!='mode_measurements'} for f in w['fixtures']]
    checks={'schema_correct':d['schema']=='ThoughtexperimentEventValueAttributionV1_2_8','lock_matches_capture':d['lock_sha256']==sha(LOCK),'source_lock_stable':all(w['sources_before']==w['sources_after']==lock['sources'] for w in workers),'runner_hash_matches_lock':lock['sources']['files']['evaluation/substrate_capability/thoughtexperiment_event_value_attribution_v1_2_8.py']==sha(RUNNER),'analyzer_hash_matches_lock':lock['sources']['files']['evaluation/substrate_capability/analyze_thoughtexperiment_event_value_attribution_v1_2_8.py']==analyzer_hash,'three_distinct_workers':len(workers)==3 and len(set(pids))==3,'workers_semantically_replicate':all(semantic(w)==semantic(workers[0]) for w in workers[1:]),'independent_analyzer_stable':analyzer_hash==sha(ANALYZER)}
    fixtures=workers[0]['fixtures'];checks['fixture_set_exact']={f['fixture'] for f in fixtures}=={'direct','deferred','overlap','byte_cap','depth_cap','edge_mutation','same_event_multiwrite','object_cap','direct_deferred_overlap','report_object_cap'}
    deltas_recompute=True;assignment_recompute=True;modes_match=True;no_drops=True;observed=set();field_rows=[]
    event_replays=[]
    for f in fixtures:
        snaps=f['graph_snapshots'];modes_match &= len({(v['status'],v['progress_steps'],v['passes_completed']) for v in f['summaries'].values()})==1
        modes_match &= all(snaps[x]['before']==snaps['plain']['before'] and snaps[x]['after']==snaps['plain']['after'] for x in ('traced','exact'))
        recomputed=derive(snaps['traced']['before'],snaps['traced']['after']);deltas_recompute &= recomputed==f['changes']
        events=f['events'];observed|={e['rule_name'] for e in events};no_drops &= f['dropped_events']==0
        event_replays.append(replay_event_values(snaps['traced']['before'],snaps['traced']['after'],events))
        rebuilt=[]
        if f['fixture']!='report_object_cap':
            for change in recomputed:
                ix=candidates(change,events);rebuilt.append({'change':change,'candidate_event_indices':ix,'attributed_event_index':ix[0] if len(ix)==1 else None,'status':'unique' if len(ix)==1 else ('ambiguous' if ix else 'uncovered')})
            assignment_recompute &= rebuilt==f['assignments']
        else:
            assignment_recompute &= f['assignments']==[]
        field_rows.append((f,recomputed,rebuilt))
    replayed_by_fixture={f['fixture']:event_replays[i] for i,f in enumerate(fixtures)}
    full_fixtures=('direct','deferred','overlap','edge_mutation','same_event_multiwrite','direct_deferred_overlap')
    checks.update({'snapshot_field_deltas_independently_recomputed':bool(deltas_recompute),'event_assignments_independently_recomputed':bool(assignment_recompute),'ordinary_traced_exact_modes_match':bool(modes_match),'no_events_dropped':bool(no_drops),'complete_fixture_values_complete':all(replayed_by_fixture[k]['complete'] for k in full_fixtures),'event_before_values_match_ordered_replay':all(replayed_by_fixture[k]['event_before_values_match_ordered_replay'] for k in full_fixtures),'event_replay_matches_final_graph':all(replayed_by_fixture[k]['replayed_final_nodes_match'] and replayed_by_fixture[k]['replayed_final_edges_match'] for k in full_fixtures),'event_replay_details':{k:v for k,v in zip((f['fixture'] for f in fixtures),event_replays)},'all_mode_measurements_present':all(set(f['mode_measurements'])=={'plain','traced','exact'} for f in fixtures),'event_snapshot_json_measured':all(f['mode_measurements']['traced']['event_snapshot_json_bytes']>0 for f in fixtures),'expected_direct_and_deferred_writers_observed':{'direct_writer','trans_frame_identity_assignment','trace_direct_control'}<=observed})
    overlap=next((f for f in fixtures if f['fixture']=='overlap'),None)
    if overlap:
        transitions=[]
        for event in overlap['events']:
            for item in event.get('node_values',[]):
                before=item['before'];after=item['after']
                if before is None or after is None:continue
                bv=before.get('attrs',{}).get('value');av=after.get('attrs',{}).get('value')
                if bv!=av:transitions.append((event['rule_name'],bv,av))
        target=next((a for a in overlap['assignments'] if a['change']['entity']=='node' and a['change']['field']=='attr:value'),None)
        checks['overlap_value_chain_exact']=transitions==[('writer_one',0,1),('writer_two',1,2)]
        checks['overlap_last_writer_identified']=bool(transitions and transitions[-1][0]=='writer_two' and target and target['status']=='ambiguous' and len(target['candidate_event_indices'])==2)
        checks['overlap_transition_detail']=[list(x) for x in transitions]
    else:
        checks['overlap_value_chain_exact']=False;checks['overlap_last_writer_identified']=False
    by_fixture={f['fixture']:f for f in fixtures}
    byte_events=by_fixture['byte_cap']['events'];object_events=by_fixture['object_cap']['events']
    byte_truncated=any(e['values_truncated'] for e in byte_events)
    object_truncated=any(e['values_truncated'] for e in object_events)
    object_captured=max((len(e.get('node_values',[]))+len(e.get('edge_values',[])) for e in object_events),default=0)
    checks['oversized_value_fails_closed']=byte_truncated and all(not e.get('node_values') for e in byte_events if e['values_truncated'])
    checks['object_cap_truncates_explicitly']=object_truncated and object_captured==512
    checks['reported_budget_metadata_consistent']=all(
        f['mode_measurements']['traced']['snapshot_bytes_estimated']<=f['mode_measurements']['traced']['snapshot_byte_budget']
        and f['mode_measurements']['traced']['snapshot_objects']<=f['mode_measurements']['traced']['snapshot_object_budget']
        for f in fixtures)
    report_cap=by_fixture['report_object_cap'];report_events=report_cap['events'];report_measure=report_cap['mode_measurements']['traced']
    group_counts=[len(e.get('node_values',[]))+len(e.get('edge_values',[])) for e in report_events]
    checks['report_object_budget_reached_exactly']=report_measure['snapshot_objects']==16384 and report_measure['snapshot_objects']==report_measure['snapshot_object_budget']
    checks['report_object_cap_truncates_next_group']=len(report_events)>=33 and group_counts[32]==0 and report_events[32]['values_truncated'] and all(group_counts[i]==512 and not report_events[i]['values_truncated'] for i in range(32))
    checks['report_byte_cap_unreachable_before_object_cap']=report_measure['snapshot_byte_budget']==4*1024*1024 and report_measure['snapshot_event_byte_budget']==64*1024 and report_measure['snapshot_object_budget']==16384 and report_measure['snapshot_event_object_budget']==512 and report_measure['snapshot_byte_budget']>((report_measure['snapshot_object_budget']//report_measure['snapshot_event_object_budget'])*report_measure['snapshot_event_byte_budget'])
    conflict=by_fixture['direct_deferred_overlap']
    conflict_transitions=[]
    for event_index,event in enumerate(conflict['events']):
        for item in event.get('node_values',[]):
            before=item['before'];after=item['after']
            if before is None or after is None or before.get('type')!='CurPercept' or after.get('type')!='CurPercept':continue
            bv=before.get('attrs',{}).get('identity','<ABSENT>');av=after.get('attrs',{}).get('identity','<ABSENT>')
            if bv!=av:conflict_transitions.append((event_index,event['rule_name'],bool(event['deferred']),bv,av))
    expected_names=['identity_direct','identity_deferred']*((len(conflict_transitions)+1)//2)
    expected_names=expected_names[:len(conflict_transitions)]
    target_change=next((a for a in conflict['assignments'] if a['change']['entity']=='node' and a['change']['field']=='attr:identity'),None)
    after_nodes={int(n['id']):n for n in conflict['graph_snapshots']['traced']['after']['nodes']}
    target_ids={int(n['id']) for n in conflict['graph_snapshots']['traced']['before']['nodes'] if n['type']=='CurPercept'}
    target_id=next(iter(target_ids),None);final_identity=after_nodes.get(target_id,{}).get('attrs',{}).get('identity','<ABSENT>') if target_id is not None else '<MISSING>'
    checks['direct_deferred_overlap_status_is_budgeted']=conflict['summaries']['traced']['status']=='progress_budget_reached' and conflict['summaries']['traced']['progress_steps']==10
    checks['direct_deferred_identity_alternation']=len(conflict_transitions)>=5 and [x[1] for x in conflict_transitions]==expected_names and all(x[2]==(x[1]=='identity_deferred') for x in conflict_transitions)
    checks['direct_deferred_final_writer_matches_graph']=bool(conflict_transitions and conflict_transitions[-1][1]=='identity_direct' and conflict_transitions[-1][4]==final_identity==99 and target_change and len(target_change['candidate_event_indices'])>1)
    checks['direct_deferred_transition_detail']=[list(x) for x in conflict_transitions]
    summary={'workers':len(workers),'distinct_pids':len(set(pids)),'fixtures':len(fixtures),'changed_fields':sum(len(x[1]) for x in field_rows),'uniquely_attributed_fields':sum(sum(a['status']=='unique' for a in x[2]) for x in field_rows),'ambiguous_fields':sum(sum(a['status']=='ambiguous' for a in x[2]) for x in field_rows),'uncovered_fields':sum(sum(a['status']=='uncovered' for a in x[2]) for x in field_rows),'all_fields_uniquely_attributed':all(a['status']=='unique' for x in field_rows for a in x[2]),'observed_writers':sorted(observed),'progress_budget':lock['progress_budget']}
    out={'schema':'ThoughtexperimentEventValueAttributionV1_2_8Analysis','analyzer_sha256':analyzer_hash,'capture_sha256':sha(CAPTURE),'lock_sha256':sha(LOCK),'checks':checks,'passed':all(checks.values()),'summary':summary,'claim_limit':'Independent graph-snapshot reconstruction and target-event matching are validated for these bounded fixtures. Ambiguous overlaps remain unresolved; this is not native event-local attribution, causal necessity, diagnosis, or general self-repair.'}
    dest=ROOT/'evaluation/reports/thoughtexperiment_event_value_attribution_v1_2_8_analysis_20261005.json';dest.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':out['passed'],'checks':checks,'summary':summary}));return 0 if out['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
