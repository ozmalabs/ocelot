#!/usr/bin/env python3
"""Independent integrity checks and descriptive summaries for partition scale."""
import hashlib,json,random,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_bigville_partition_scale_v1_20260926.json'
LOCK=ROOT/'evaluation/substrate_capability/bigville_partition_scale_lock_20260926.json'
SIZES=(100,250,500);REPS=3;SAMPLES=31;SEED=20260928
FILES=['scripts/substrate_bigville_partition_scale_v1.py','scripts/analyze_substrate_bigville_partition_scale_v1.py','docs/research/engine_substrate/SUBSTRATE_BIGVILLE_PARTITION_SCALE_PREREG_20260926.md','seeds/bigville_cast100.json','worlds/bigville_can_beliefs.py','domains/engine_provenance.py','runners/dsl/src/graph.rs','runners/dsl/src/py.rs','runners/dsl/src/substrate.rs','runners/dsl/python/substrate_rs/_native.build.json']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 d=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());runs=d['workers'];expected=[(n,r) for n in SIZES for r in range(REPS)];random.Random(SEED).shuffle(expected)
 checks={'raw_matches_lock':d['locked_inputs']==lock['locked_inputs'],'lock_hash_matches':d['lock_sha256']==sha(LOCK),'source_hashes_match_lock':lock['locked_inputs']['files_sha256']=={p:sha(ROOT/p) for p in FILES},'native_hash_matches':d['native']['sha256']==sha(Path(d['native']['path'])),'protocol_tag':d['protocol']=='BIGVILLE_PARTITION_SCALE_V1','worker_count_9':len(runs)==9,'unique_worker_pids':len({r['pid'] for r in runs})==9,'exact_random_schedule':d['schedule']==[list(x) for x in expected]}
 cells={(r['size'],r['replicate']):r for r in runs};checks['balanced_size_replicates']=len(cells)==9 and all((n,r) in cells for n in SIZES for r in range(REPS))
 shape=True;timings=True;edges=True
 for x in runs:
  n=x['size'];shape &= x['resident_count']==n and x['concept_count']==5*n and x['component_count']==n and x['owner_frame_sizes']==[5]*n
  edges &= x['directed_edge_count']==10*n
  timings &= len(x['resident_build_samples_ns'])==n and all(v>0 for v in x['resident_build_samples_ns']) and all(len(x[k])==SAMPLES and all(isinstance(v,int) and v>=0 for v in x[k]) for k in ('owner_discovery_samples_ns','edge_extraction_samples_ns','component_derivation_samples_ns','composed_partition_samples_ns'))
 checks['live_partition_shape_and_sizes']=bool(shape);checks['expected_authored_edge_count']=bool(edges);checks['timing_sample_counts']=bool(timings)
 summaries=[]
 for n in SIZES:
  xs=[cells[n,r] for r in range(REPS)]
  med=lambda key:statistics.median([statistics.median(x[key]) if isinstance(x[key],list) else x[key] for x in xs])
  summaries.append({'frames':n,'concepts':5*n,'graph_build_total_ns_median':statistics.median(x['resident_build_total_ns'] for x in xs),'per_frame_build_ns_median':statistics.median(x['resident_build_total_ns']/n for x in xs),'owner_discovery_ns_median':med('owner_discovery_samples_ns'),'edge_extraction_ns_median':med('edge_extraction_samples_ns'),'component_derivation_ns_median':med('component_derivation_samples_ns'),'composed_partition_ns_median':med('composed_partition_samples_ns'),'peak_rss_kib_median':statistics.median(x['peak_rss_kib'] for x in xs),'process_ranges_ns':{key:[min(x[key] if isinstance(x[key],int) else statistics.median(x[key]) for x in xs),max(x[key] if isinstance(x[key],int) else statistics.median(x[key]) for x in xs)] for key in ('resident_build_total_ns','owner_discovery_samples_ns','edge_extraction_samples_ns','component_derivation_samples_ns','composed_partition_samples_ns')}})
 out={'raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'checks':checks,'all_checks_pass':all(checks.values()),'summaries':summaries,'claim_boundary':'three fresh processes at each of 100/250/500 repeated authored Bigville five-Concept frames; graph assembly and live partition derivation timed separately; controlled scale evidence only, with one template and disconnected baseline components'}
 path=ROOT/'evaluation/reports/substrate_bigville_partition_scale_v1_analysis_20260926.json';path.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'analysis':str(path),'all_checks_pass':out['all_checks_pass'],'failed':[k for k,v in checks.items() if not v],'summaries':summaries},indent=2))
if __name__=='__main__':main()
