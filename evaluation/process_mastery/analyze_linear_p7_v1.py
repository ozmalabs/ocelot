"""Mechanical summaries for the frozen linear P7 scorecard."""
from __future__ import annotations
import argparse,json
from collections import Counter,defaultdict
from pathlib import Path

def analyze(payload):
    if payload.get('schema')!='pmb-scorecard-v1': raise ValueError('expected pmb-scorecard-v1')
    records=payload.get('records')
    if not isinstance(records,list) or any(r.get('status') is None for r in records): raise ValueError('missing trial status')
    by=defaultdict(list)
    for r in records: by[(r.get('family'),r.get('profile'))].append(r)
    result={}
    for (fam,profile),rows in sorted(by.items()):
      completed=[r for r in rows if r['status']=='COMPLETED']
      result[f'{fam}/{profile}']={'n':len(rows),'statuses':dict(Counter(r['status'] for r in rows)),
        'pass':sum(bool(r.get('external_outcome',{}).get('pass')) for r in completed),
        'source_leaks':sum(int(r.get('source_leaks',0)) for r in rows),
        'coverage':len(completed)/len(rows) if rows else None}
    return {'schema':'pmb-linear-p7-analysis-v1','phase':payload.get('metadata',{}).get('phase'),
      'split':payload.get('metadata',{}).get('split'),'n_records':len(records),'families':result}

def main():
    p=argparse.ArgumentParser();p.add_argument('scorecard',nargs='?',type=Path);p.add_argument('--self-check',action='store_true');a=p.parse_args()
    if a.self_check:
      sample={'schema':'pmb-scorecard-v1','metadata':{'phase':'linear-p7-v1'},'records':[{'family':'x','profile':'on','status':'COMPLETED','external_outcome':{'pass':True}}]}
      assert analyze(sample)['families']['x/on']['pass']==1
      print('linear_p7 analyzer self-check: PASS');return
    if not a.scorecard:p.error('scorecard required')
    print(json.dumps(analyze(json.loads(a.scorecard.read_text())),indent=2,sort_keys=True))
if __name__=='__main__':main()
