"""Mechanical summaries for the frozen P8 scorecard."""
from __future__ import annotations
import argparse,json
from collections import Counter,defaultdict
from pathlib import Path

def analyze(payload):
 if payload.get('schema')!='pmb-scorecard-v1':raise ValueError('expected pmb-scorecard-v1')
 rows=payload.get('records')
 if not isinstance(rows,list) or any(r.get('status') is None for r in rows):raise ValueError('missing status')
 by=defaultdict(list)
 for r in rows:by[(r.get('family'),r.get('profile'))].append(r)
 families={}
 for (fam,profile),rs in sorted(by.items()):
  completed=[r for r in rs if r['status']=='COMPLETED']
  families[f'{fam}/{profile}']={'n':len(rs),'statuses':dict(Counter(r['status'] for r in rs)),'pass':sum(bool(r.get('external_outcome',{}).get('pass')) for r in completed),'coverage':len(completed)/len(rs) if rs else None,'interactions':sum(r.get('interactions',0) for r in rs)}
 return {'schema':'pmb-linear-p8-analysis-v1','phase':payload.get('metadata',{}).get('phase'),'split':payload.get('metadata',{}).get('split'),'n_records':len(rows),'families':families}
def main():
 p=argparse.ArgumentParser();p.add_argument('scorecard',nargs='?',type=Path);p.add_argument('--self-check',action='store_true');a=p.parse_args()
 if a.self_check:
  sample={'schema':'pmb-scorecard-v1','metadata':{},'records':[{'family':'x','profile':'y','status':'COMPLETED','external_outcome':{'pass':True}}]};assert analyze(sample)['families']['x/y']['pass']==1;print('linear_p8 analyzer self-check: PASS');return
 if not a.scorecard:p.error('scorecard required')
 print(json.dumps(analyze(json.loads(a.scorecard.read_text())),indent=2,sort_keys=True))
if __name__=='__main__':main()
