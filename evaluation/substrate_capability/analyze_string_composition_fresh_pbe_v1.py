#!/usr/bin/env python3
"""Independent oracle, held-out IR, and replay audit for fresh string PBE."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'scripts'),str(ROOT/'runners/dsl/python')]
FIXTURE=ROOT/'tests/fixtures/substrate_string_composition_fresh/tasks.json';RAW=ROOT/'evaluation/reports/string_composition_fresh_pbe_v1_20261003.json';OUT=ROOT/'evaluation/reports/string_composition_fresh_pbe_v1_analysis_20261003.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def oracle(family,s,arg):
 if family=='casefold_count':return s.casefold().count(arg.casefold())
 if family=='casefold_split':return s.casefold().split(arg.casefold())
 if family=='reverse_then_split':return s[::-1].split(arg)
 if family=='remove_separator':return ''.join(s.split(arg))
 if family=='reverse_then_replace':return s[::-1].replace(arg[0],arg[1])
 if family=='split_reverse_tokens':return [x[::-1] for x in s.split(arg)]
 raise ValueError(family)
def main():
 import prog_synthesis_battery as p4
 suite=json.loads(FIXTURE.read_text());raw=json.loads(RAW.read_text());errors=[];checked=0
 if len(suite['tasks'])!=18:errors.append('task count')
 if raw.get('design',{}).get('task_count')!=18:errors.append('raw task count')
 for t in suite['tasks']:
  rows=t['example_rows']+t['held_out_rows'];arg=t['parameter'];fam=t['oracle_kind']
  if len(t['example_rows'])!=4 or len(t['held_out_rows'])!=3:errors.append(f"{t['id']}: split sizes")
  if len({json.dumps(x['inputs'],sort_keys=True) for x in rows})!=7:errors.append(f"{t['id']}: duplicate inputs")
  for x in rows:
   checked+=1;y=oracle(fam,x['inputs']['s'],arg)
   if y!=x['expected']:errors.append(f"{t['id']}: fixture oracle mismatch")
 arms=('main','no_retrieval','no_retrieval_escalated','main_replay');maps={a:{r['task_id']:r for r in raw['cases'][a]} for a in arms}
 for a in arms:
  if len(maps[a])!=18:errors.append(f'{a}: arm task count')
 for t in suite['tasks']:
  for arm in arms:
   r=maps[arm].get(t['id'])
   if not r:errors.append(f"{arm}/{t['id']}: missing outcome");continue
   if r.get('family')!=t['family']:errors.append(f"{arm}/{t['id']}: family mismatch")
   if r.get('status')=='accepted':
    if r.get('ir') is None:errors.append(f"{arm}/{t['id']}: accepted without IR");continue
    scored=[]
    for x in t['held_out_rows']:
     ev=p4.prog_eval(r['ir'],dict(x['inputs']));got=ev.get('result');ok=ev.get('halted') is True and ev.get('trap') is None and p4.agree(got,x['expected'])
     scored.append({'inputs':x['inputs'],'expected':x['expected'],'got':got,'ok':bool(ok),'trap':ev.get('trap')})
    exact=all(x['ok'] for x in scored)
    if exact!=(r.get('outcome')=='accepted_holdout_ok'):errors.append(f"{arm}/{t['id']}: heldout verdict mismatch")
    if len(r.get('holdout',{}).get('rows',[]))!=3:errors.append(f"{arm}/{t['id']}: missing saved holdout rows")
 replay_mismatches=[tid for tid in maps['main'] if maps['main'][tid]['outcome']!=maps['main_replay'][tid]['outcome']]
 result={'schema':'StringCompositionFreshPbeV1Analysis','passed':not errors,'errors':errors,'tasks':len(suite['tasks']),'oracle_rows_checked':checked,'main_replay_outcome_mismatches':replay_mismatches,'arms':{a:{'n':len(maps[a]),'exact_holdout':sum(r['outcome']=='accepted_holdout_ok' for r in maps[a].values()),'accepted_wrong':sum(r['outcome']=='accepted_holdout_fail' for r in maps[a].values()),'gaps':sum(r['outcome']=='gapped' for r in maps[a].values())} for a in arms},'hashes':{'fixture':sha(FIXTURE),'raw':sha(RAW),'analyzer':sha(Path(__file__))}}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2));return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
