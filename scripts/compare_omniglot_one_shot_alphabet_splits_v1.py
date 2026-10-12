#!/usr/bin/env python3
"""Exploratory unpaired alphabet-cluster comparison of Omniglot split analyses."""
import hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
EVAL=ROOT/'evaluation/reports/omniglot_one_shot_current_v1_2_20260929_analysis.json'
BG=ROOT/'evaluation/reports/omniglot_one_shot_background_v1_20260929_analysis.json'
OUT=ROOT/'evaluation/reports/omniglot_one_shot_alphabet_split_comparison_v1_20260929.json'
SEED=2910;DRAWS=10000

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def clusters(analysis,system):
 d=analysis['systems'][system]['by_alphabet'];return [(v['correct'],v['total']) for _,v in sorted(d.items())]
def main():
 a=json.loads(EVAL.read_text());b=json.loads(BG.read_text())
 if not a.get('integrity_pass') or not b.get('integrity_pass'):raise SystemExit('both source analyses must pass integrity')
 if a['systems']['pointset']['total']!=2000 or b['systems']['pointset']['total']!=2000:raise SystemExit('unexpected query totals')
 rng=np.random.default_rng(SEED);result={}
 for system in ('ordered_dtw','pointset','deformable'):
  ac=np.array(clusters(a,system),dtype=np.int64);bc=np.array(clusters(b,system),dtype=np.int64)
  ia=rng.integers(0,len(ac),size=(DRAWS,len(ac)));ib=rng.integers(0,len(bc),size=(DRAWS,len(bc)))
  av=ac[ia,0].sum(1)/ac[ia,1].sum(1);bv=bc[ib,0].sum(1)/bc[ib,1].sum(1);delta=bv-av
  ea=a['systems'][system]['accuracy'];ba=b['systems'][system]['accuracy']
  result[system]={'evaluation_accuracy':ea,'background_accuracy':ba,'background_minus_evaluation_points':100*(ba-ea),
   'unpaired_alphabet_cluster_bootstrap_95ci_points':[float(x*100) for x in np.quantile(delta,[.025,.975])],
   'evaluation_alphabet_clusters':len(ac),'background_alphabet_clusters':len(bc)}
 out={'analysis_type':'exploratory_unpaired_split_comparison','evaluation_analysis_sha256':sha(EVAL),'background_analysis_sha256':sha(BG),
  'seed':SEED,'bootstrap_draws':DRAWS,'results':result,
  'interpretation_limit':'The split comparison was computed after each independently locked panel was analyzed; it was not a preregistered confirmatory contrast. Broad cluster intervals are inconclusive about small accuracy changes.'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
