#!/usr/bin/env python3
"""Post-capture audit of structural diversity in returned behavior classes."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/coverage_aware_class_return_v1_lock_20261003.json'
RAW=ROOT/'evaluation/reports/coverage_aware_class_return_v1_20261003.json'
BASE=ROOT/'evaluation/reports/coverage_aware_class_return_v1_1_analysis_20261004.json'
DEDLOCK=ROOT/'evaluation/substrate_capability/term_deduplication_class_return_v1_lock_20261004.json'
DEDRAW=ROOT/'evaluation/reports/term_deduplication_class_return_v1_20261004.json'
DEDAN=ROOT/'evaluation/reports/term_deduplication_class_return_v1_analysis_20261004.json'
RECEIPT=ROOT/'evaluation/reports/thoughtexperiment_coverage_class_receipt_v1_20261004.json'
RECEIPT_LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_coverage_class_receipt_v1_lock_20261004.json'
RECEIPT_ANALYSIS=ROOT/'evaluation/reports/thoughtexperiment_coverage_class_receipt_v1_analysis_20261004.json'
OUT=ROOT/'evaluation/reports/term_deduplication_class_return_v1_1_analysis_20261004.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'))
def main():
 lock=json.loads(LOCK.read_text());raw=json.loads(RAW.read_text());base=json.loads(BASE.read_text());dl=json.loads(DEDLOCK.read_text());dr=json.loads(DEDRAW.read_text());da=json.loads(DEDAN.read_text());rec=json.loads(RECEIPT.read_text());rl=json.loads(RECEIPT_LOCK.read_text());ra=json.loads(RECEIPT_ANALYSIS.read_text());errors=[];rows=[]
 if raw.get('lock_sha256')!=sha(LOCK) or raw.get('sources')!=lock.get('sources'):errors.append('baseline source lock mismatch')
 if not base.get('passed') or base.get('capture_sha256')!=sha(RAW):errors.append('baseline replay analysis invalid')
 if dr.get('lock_sha256')!=sha(DEDLOCK) or dr.get('sources')!=dl.get('sources'):errors.append('dedup source lock mismatch')
 if not da.get('passed') or da.get('capture_sha256')!=sha(DEDRAW):errors.append('dedup replay analysis invalid')
 for source_lock,label in ((dl,'dedup'),(rl,'receipt')):
  for rel,want in source_lock.get('sources',{}).get('files',{}).items():
   p=ROOT/rel
   if not p.exists() or sha(p)!=want:errors.append(f'{label} source drift: {rel}')
 if rec.get('lock_sha256')!=sha(RECEIPT_LOCK) or rec.get('sources')!=rl.get('sources') or not ra.get('passed') or ra.get('capture_sha256')!=sha(RECEIPT):errors.append('class receipt evidence invalid')
 ded={(w['task'],w['worker']):w for w in dr['workers']};receipts={(w['task'],w['worker']):w for w in rec['workers']}
 for w in raw['workers']:
  key=(w['task'],w['worker']);r=w['result']
  if r.get('decision')!='behavior_class':continue
  survivors=r.get('survivors',[]);terms={canon(h['term']) for h in survivors};receipt=receipts.get(key,{})
  ids=receipt.get('expected_member_ids',[]);rt={canon(t) for t in receipt.get('returned_terms',{}).values()}
  dres=ded.get(key,{}).get('result',{})
  if len(terms)!=1:errors.append(f'baseline returned multiple exact terms {key}')
  if set(ids)!={h['id'] for h in survivors} or rt!=terms:errors.append(f'receipt membership does not preserve term identity {key}')
  if dres.get('decision')=='behavior_class':errors.append(f'class decision remains after dedup {key}')
  rows.append({'task':key[0],'worker':key[1],'baseline_member_ids':[h['id'] for h in survivors],
    'baseline_returned_candidate_count':len(survivors),'distinct_canonical_terms':len(terms),
    'receipt_member_edges':len(ids),'receipt_distinct_terms':len(rt),'deduplicated_decision':dres.get('decision'),
    'baseline_labels':r.get('calls'),'deduplicated_labels':dres.get('calls')})
 if len(rows)!=5:errors.append(f'expected 5 baseline class returns, found {len(rows)}')
 report={'schema':'TermDeduplicationClassReturnV1_1Analysis','passed':not errors,'errors':errors,
  'input_hashes':{'upstream_lock':sha(LOCK),'upstream_capture':sha(RAW),'upstream_analysis':sha(BASE),'dedup_lock':sha(DEDLOCK),'dedup_capture':sha(DEDRAW),'dedup_analysis':sha(DEDAN),'class_receipt_lock':sha(RECEIPT_LOCK),'class_receipt_capture':sha(RECEIPT),'class_receipt_analysis':sha(RECEIPT_ANALYSIS)},
  'analyzer_sha256':sha(Path(__file__)),'result':{'baseline_class_panels':len(rows),'panels_with_four_ids_one_term':sum(r['baseline_returned_candidate_count']==4 and r['distinct_canonical_terms']==1 for r in rows),
  'class_receipt_panels_with_duplicate_term_members':sum(r['receipt_member_edges']>r['receipt_distinct_terms'] for r in rows),
  'deduplicated_replay_decisions':{d:sum(r['deduplicated_decision']==d for r in rows) for d in sorted({r['deduplicated_decision'] for r in rows})}},'rows':rows,
  'interpretation':'The original five class-return outcomes and their graph receipts contain repeated candidate IDs for one canonical Term each. They demonstrate duplicate-entry handling and graph transport, not equivalence among structurally distinct hypotheses.'}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':not errors,'errors':errors,'result':report['result']},sort_keys=True));return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
