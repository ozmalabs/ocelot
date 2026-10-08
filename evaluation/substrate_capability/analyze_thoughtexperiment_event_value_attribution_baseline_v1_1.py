#!/usr/bin/env python3
"""Independently derive graph-field deltas and audit event attribution."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CAPTURE=ROOT/'evaluation/reports/thoughtexperiment_event_value_attribution_baseline_v1_1_20261005.json'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_event_value_attribution_baseline_v1_1_lock_20261005.json'
RUNNER=ROOT/'evaluation/substrate_capability/thoughtexperiment_event_value_attribution_baseline_v1_1.py'
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
def main():
    analyzer_hash=sha(ANALYZER);d=json.loads(CAPTURE.read_text());lock=json.loads(LOCK.read_text());workers=d['workers'];pids=[w['pid'] for w in workers]
    checks={'schema_correct':d['schema']=='ThoughtexperimentEventValueAttributionBaselineV1_1','lock_matches_capture':d['lock_sha256']==sha(LOCK),'source_lock_stable':all(w['sources_before']==w['sources_after']==lock['sources'] for w in workers),'runner_hash_matches_lock':lock['sources']['files']['evaluation/substrate_capability/thoughtexperiment_event_value_attribution_baseline_v1_1.py']==sha(RUNNER),'analyzer_hash_matches_lock':lock['sources']['files']['evaluation/substrate_capability/analyze_thoughtexperiment_event_value_attribution_baseline_v1_1.py']==analyzer_hash,'three_distinct_workers':len(workers)==3 and len(set(pids))==3,'workers_semantically_replicate':all(w['fixtures']==workers[0]['fixtures'] for w in workers[1:]),'independent_analyzer_stable':analyzer_hash==sha(ANALYZER)}
    fixtures=workers[0]['fixtures'];checks['fixture_set_exact']={f['fixture'] for f in fixtures}=={'direct','deferred'}
    deltas_recompute=True;assignment_recompute=True;modes_match=True;no_drops=True;observed=set();field_rows=[]
    for f in fixtures:
        snaps=f['graph_snapshots'];modes_match &= len({(v['status'],v['progress_steps'],v['passes_completed']) for v in f['summaries'].values()})==1
        modes_match &= all(snaps[x]['before']==snaps['plain']['before'] and snaps[x]['after']==snaps['plain']['after'] for x in ('traced','exact'))
        recomputed=derive(snaps['traced']['before'],snaps['traced']['after']);deltas_recompute &= recomputed==f['changes']
        events=f['events'];observed|={e['rule_name'] for e in events};no_drops &= f['dropped_events']==0
        rebuilt=[]
        for change in recomputed:
            ix=candidates(change,events);rebuilt.append({'change':change,'candidate_event_indices':ix,'attributed_event_index':ix[0] if len(ix)==1 else None,'status':'unique' if len(ix)==1 else ('ambiguous' if ix else 'uncovered')})
        assignment_recompute &= rebuilt==f['assignments'];field_rows.append((f,recomputed,rebuilt))
    checks.update({'snapshot_field_deltas_independently_recomputed':bool(deltas_recompute),'event_assignments_independently_recomputed':bool(assignment_recompute),'ordinary_traced_exact_modes_match':bool(modes_match),'no_events_dropped':bool(no_drops),'expected_direct_and_deferred_writers_observed':{'direct_writer','trans_frame_identity_assignment','trace_direct_control'}<=observed})
    summary={'workers':len(workers),'distinct_pids':len(set(pids)),'fixtures':len(fixtures),'changed_fields':sum(len(x[1]) for x in field_rows),'uniquely_attributed_fields':sum(sum(a['status']=='unique' for a in x[2]) for x in field_rows),'ambiguous_fields':sum(sum(a['status']=='ambiguous' for a in x[2]) for x in field_rows),'uncovered_fields':sum(sum(a['status']=='uncovered' for a in x[2]) for x in field_rows),'all_fields_uniquely_attributed':all(a['status']=='unique' for x in field_rows for a in x[2]),'observed_writers':sorted(observed),'progress_budget':lock['progress_budget']}
    out={'schema':'ThoughtexperimentEventValueAttributionBaselineV1_1Analysis','analyzer_sha256':analyzer_hash,'capture_sha256':sha(CAPTURE),'lock_sha256':sha(LOCK),'checks':checks,'passed':all(checks.values()),'summary':summary,'claim_limit':'Independent graph-snapshot reconstruction and target-event matching are validated for these bounded fixtures. Ambiguous overlaps remain unresolved; this is not native event-local attribution, causal necessity, diagnosis, or general self-repair.'}
    dest=ROOT/'evaluation/reports/thoughtexperiment_event_value_attribution_baseline_v1_1_analysis_20261005.json';dest.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':out['passed'],'checks':checks,'summary':summary}));return 0 if out['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
