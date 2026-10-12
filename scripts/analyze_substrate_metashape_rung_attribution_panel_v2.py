#!/usr/bin/env python3
"""Independent integrity and per-family rung-attribution analysis."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/metashape_rung_attribution_panel_v2_20260927.json'
LOCK=ROOT/'evaluation/substrate_capability/metashape_rung_attribution_panel_v2_lock_20260927.json'
OUT=ROOT/'evaluation/reports/metashape_rung_attribution_panel_v2_analysis_20260927.json'
FAMILIES=('FrameBindingProbe','MotionRuleProbe','ResourceTransferProbe','GoalTraceProbe')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def is_match(x):return x.get('status') in ('recognized','recognized_prior')
def main():
 raw=json.loads(RAW.read_text());locked=json.loads(LOCK.read_text())['locked_inputs'];runs=raw['runs']
 integrity={'raw_lock_matches':raw['locked_inputs']==locked==raw['post_run_inputs'],'eight_workers':len(runs)==8,'unique_pids':len({r.get('pid') for r in runs})==8,'two_workers_each':all(sum(r.get('family')==f for r in runs)==2 for f in FAMILIES),'all_source_stable':all(r.get('source_stable') and r.get('locked_inputs_before')==locked==r.get('locked_inputs_after') for r in runs),'boot_ok':all(r.get('seed_boot',{}).get('loaded',0)>0 and not r.get('seed_boot',{}).get('failures') for r in runs),'records_complete':all(len(r.get('training',[]))==2 and len(r.get('heldout',[]))==5 for r in runs),'artifact_hashes':locked['explicit_files'].get('scripts/substrate_metashape_rung_attribution_panel_v2.py')==sha(ROOT/'scripts/substrate_metashape_rung_attribution_panel_v2.py') and locked['explicit_files'].get('scripts/analyze_substrate_metashape_rung_attribution_panel_v2.py')==sha(Path(__file__))}
 by={}
 for family in FAMILIES:
  rs=[r for r in runs if r.get('family')==family];rows=[]
  for r in rs:
   h={x['label']:x for x in r.get('heldout',[])};target=r.get('new_shape_names',[])
   pos=h.get('positive',{});negs=[x for x in r.get('heldout',[]) if x['label']!='positive']
   rows.append({'replicate':r.get('replicate'),'training_new_shape_names':target,'training_minted_count':len(target),'positive_status':pos.get('status'),'positive_covered_by':pos.get('covered_by'),'positive_target_match':bool(target and pos.get('covered_by')==target[0] and pos.get('status')=='recognized'),'negative_count':len(negs),'negative_any_rung_attributions':sum(is_match(x) for x in negs),'negative_target_coverage':sum(x.get('covered_by') in target for x in negs if target),'negative_statuses':{x['label']:x.get('status') for x in negs},'training_ns':[x['elapsed_ns'] for x in r.get('training',[])],'heldout_ns':{x['label']:x['elapsed_ns'] for x in r.get('heldout',[])},'peak_rss_bytes':r.get('peak_rss_bytes')})
  by[family]={'replicate_count':len(rs),'worker_rows':rows,'training_mint_rate':sum(x['training_minted_count']==1 for x in rows)/len(rows) if rows else None,'positive_exact_transfer_rate':sum(x['positive_target_match'] for x in rows)/len(rows) if rows else None,'negative_any_rung_false_attributions':sum(x['negative_any_rung_attributions'] for x in rows),'negative_target_shape_coverages':sum(x['negative_target_coverage'] for x in rows),'negative_probes_total':sum(x['negative_count'] for x in rows)}
 out={'schema_version':1,'raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'integrity_checks':integrity,'integrity_pass':all(integrity.values()),'by_family':by,'claim_boundary':'Counts describe only this authored, locked schema discrimination panel. Recognized-prior attribution is kept separate from structural exact transfer; no semantic error rate or natural prevalence is implied.'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT.relative_to(ROOT)),'integrity_pass':out['integrity_pass'],'families':{k:{'mint_rate':v['training_mint_rate'],'positive_exact':v['positive_exact_transfer_rate'],'false_prior_or_structural':v['negative_any_rung_false_attributions'],'negative_n':v['negative_probes_total']} for k,v in by.items()}},indent=2))
 if not out['integrity_pass']:raise SystemExit('analysis integrity failed')
if __name__=='__main__':main()
