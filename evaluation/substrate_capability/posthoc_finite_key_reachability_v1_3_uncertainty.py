#!/usr/bin/env python3
"""Post-hoc paired bootstrap sensitivity summary for the v1.3 capture."""
from __future__ import annotations
import hashlib,json,random,statistics
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CAPTURE=ROOT/'evaluation/reports/finite_key_reachability_profile_v1_3_20261005.json'
OUT=ROOT/'evaluation/reports/finite_key_reachability_profile_v1_3_uncertainty_posthoc_20261005.json'
SEED=20261005;BOOTSTRAPS=50000
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 raw=json.loads(CAPTURE.read_text());groups=defaultdict(list)
 for c in raw['cases']:
  for q,s in c['sweep'].items():groups[(c['topology'],q)].append(s['profile_total_wall_ns']/s['direct_total_wall_ns'])
 rng=random.Random(SEED);summary={}
 for (topology,q),ratios in sorted(groups.items()):
  samples=sorted(statistics.median(rng.choices(ratios,k=len(ratios))) for _ in range(BOOTSTRAPS))
  summary[f'{topology}:N=128:Q={q}']={'paired_repetitions':len(ratios),'median_paired_ratio':statistics.median(ratios),'percentile_bootstrap_95_ci_median_ratio':[samples[int(.025*BOOTSTRAPS)],samples[int(.975*BOOTSTRAPS)]],'favorable_repetitions':sum(r<1 for r in ratios)}
 out={'schema':'FiniteKeyReachabilityV1_3PosthocBootstrap','capture_sha256':sha(CAPTURE),'seed':SEED,'bootstrap_resamples':BOOTSTRAPS,'resampling_unit':'paired repetition ratio within topology and query count','interval':'percentile 95% bootstrap interval for median paired ratio; post-hoc exploratory, not preregistered','summary':summary}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'capture_sha256':out['capture_sha256'],'output':OUT.relative_to(ROOT).as_posix(),'summary':summary},indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
