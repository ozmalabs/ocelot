#!/usr/bin/env python3
"""Independent gates for competing deferred SetRuleClause writers."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_deferred_rule_edit_competing_v1_lock_20261005.json'
CAP=ROOT/'evaluation/reports/thoughtexperiment_deferred_rule_edit_competing_v1_20261005.json'
OUT=CAP.with_name('thoughtexperiment_deferred_rule_edit_competing_v1_analysis_20261005.json')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(r,errors,where):
 sc=r.get('scenario');events=r.get('events',[]);changes=r.get('changes',[]);origins=r.get('origins',[]);branches={b['omitted_writer']:b['marker'] for b in r.get('branches',[])}
 if not r.get('primary_unchanged'):errors.append(where+': primary state changed')
 if sc in ('competing','duplicate'):
  if [e['writer'] for e in events]!=['writer_a','writer_b']:errors.append(where+': queue event order mismatch')
  if [(o['writer'],o['effect_index']) for o in origins]!=[('writer_a',0),('writer_b',0)]:errors.append(where+': source origins mismatch')
  if len(changes)!=2 or [c.get('revision') for c in changes]!=[1,2] or any(not c.get('committed') for c in changes):errors.append(where+': sequential commits/revisions mismatch')
  if [c.get('previous_revision') for c in changes]!=[0,1]:errors.append(where+': revision chain mismatch')
  if r.get('target_revision_after')!=0:errors.append(where+': experiment mutated primary target')
  if sc=='competing' and branches!={'writer_a':False,'writer_b':True}:errors.append(where+': competing-writer necessity oracle mismatch')
  if sc=='duplicate' and branches!={'writer_a':False,'writer_b':False}:errors.append(where+': duplicate-writer non-unique necessity oracle mismatch')
 else:
  if len(events)!=2 or len(origins)!=2 or changes:errors.append(where+': ambiguous target should preserve origins and refuse both edits')
  if any(e.get('progressed') for e in events):errors.append(where+': ambiguous edit reported progress')
  if r.get('target_revision_after')!=0 or branches!={'writer_a':True,'writer_b':True}:errors.append(where+': ambiguous target refusal/branch outcome mismatch')
def main():
 lock=json.loads(LOCK.read_text());cap=json.loads(CAP.read_text());errors=[]
 if cap.get('lock_sha256')!=sha(LOCK):errors.append('capture lock hash mismatch')
 ws=cap.get('workers',[]);iso=cap.get('isolated',[])
 if len(ws)!=3 or len({w.get('pid') for w in ws})!=3:errors.append('worker count/PID uniqueness failure')
 if len(iso)!=9 or len({r.get('pid') for r in iso})!=9:errors.append('isolated count/PID uniqueness failure')
 rows=[]
 for w in ws:
  if w.get('sources_before')!=lock['sources'] or w.get('sources_after')!=lock['sources']:errors.append('worker lock mismatch')
  if {r.get('scenario') for r in w.get('rows',[])}!={'competing','duplicate','ambiguous_target'}:errors.append('worker scenario matrix incomplete')
  for r in w.get('rows',[]):check(r,errors,f"worker {w.get('worker')} {r.get('scenario')}");rows.append(r)
 for r in iso:
  if r.get('sources_before')!=lock['sources'] or r.get('sources_after')!=lock['sources']:errors.append('isolated lock mismatch')
  check(r,errors,f"isolated {r.get('scenario')}")
 summary={}
 for sc in ('competing','duplicate','ambiguous_target'):
  rs=[r for r in iso if r.get('scenario')==sc]
  summary[sc]={'replicates':len(rs),'median_wall_ms':statistics.median([r['wall_ns']/1e6 for r in rs]) if rs else None}
 result={'schema':'DeferredRuleEditCompetingV1Analysis','gates_pass':not errors,'errors':errors,'summary':{'workers':len(ws),'isolated_runs':len(iso),'unique_worker_pids':len({w.get('pid') for w in ws}),'unique_isolated_pids':len({r.get('pid') for r in iso}),'scenarios':summary,'causal_conclusion':'writer_b uniquely necessary in the competing fixture; neither writer individually necessary in duplicate fixture; ambiguous target causes abstention/refusal'}}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
