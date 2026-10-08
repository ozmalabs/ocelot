#!/usr/bin/env python3
"""Independent semantic and lifecycle checks for learned cue integration."""
import hashlib,itertools,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
LOCK=ROOT/'evaluation/substrate_capability/learned_numeric_cue_composer_integration_v1_lock_20261003.json'
DATA=ROOT/'evaluation/reports/learned_numeric_cue_composer_integration_v1_20261003.json'
LEARN_LOCK=ROOT/'evaluation/substrate_capability/numeric_opposition_relation_learning_v1_1_lock_20261003.json'
LEARN_DATA=ROOT/'evaluation/reports/numeric_opposition_relation_learning_v1_1_20261003.json'
OUT=ROOT/'evaluation/reports/learned_numeric_cue_composer_integration_v1_analysis_20261003.json'
MAP={'ax':'actual_dx','ay':'actual_dy','ex':'expected_dx','ey':'expected_dy'}
VECTOR={'Up':(-1.,0.),'Down':(1.,0.),'Left':(0.,-1.),'Right':(0.,1.),'Stay':(0.,0.)}
ALLOWED={'Var','Attr','Lit','Eq','And','Neg'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def expected_where(term):
 def bind(x):
  if isinstance(x,dict):
   if x.get('type')=='Var':return {'type':'Attr','node':{'type':'Var','name':'residual'},'key':MAP[x['name']]}
   return {k:bind(v) for k,v in x.items()}
  if isinstance(x,(list,tuple)):return [bind(v) for v in x]
  return x
 A=lambda key:{'type':'Attr','node':{'type':'Var','name':'residual'},'key':key}
 L=lambda value:{'type':'Lit','value':value}
 return {'type':'And','items':[{'type':'Eq','a':A('schema'),'b':L('outcome_residual.v1')},bind(term),
   {'type':'Eq','a':A('cue_derived'),'b':L(0)}]}
def expected_truth(task):
 a=VECTOR.get(task.get('actual'));e=VECTOR.get(task.get('expected'))
 return a is not None and e is not None and e[0]==-a[0] and e[1]==-a[1]
def main():
 from substrate_rs import _native
 lock=json.loads(LOCK.read_text());data=json.loads(DATA.read_text());learn_lock=json.loads(LEARN_LOCK.read_text());learn=json.loads(LEARN_DATA.read_text())
 rows=data.get('workers',[]);errors=[]
 if data.get('lock_sha256')!=sha(LOCK):errors.append('integration lock hash mismatch')
 if data.get('sources')!=lock.get('sources'):errors.append('integration source map mismatch')
 if learn.get('lock_sha256')!=sha(LEARN_LOCK) or learn.get('sources')!=learn_lock.get('sources'):errors.append('learner evidence linkage mismatch')
 if len(lock['learned_terms'])!=5 or len(lock['tasks'])!=13 or len(rows)!=65:errors.append('term/task/worker count mismatch')
 expected_learn={r['worker']:r for r in learn['workers']};expected_by_cell={}
 for term in lock['learned_terms']:
  source=expected_learn.get(term['worker'])
  if source is None or source['term']!=term['term'] or term['sha256']!=digest(term['term']):errors.append(f"term {term['worker']}: not the frozen learned AST")
 native=_native.Substrate();rows_sorted=sorted(rows,key=lambda r:(r['term_index'],r['task_index']))
 for r in rows_sorted:
  ti,ki=r['term_index'],r['task_index'];task=lock['tasks'][ki];term=lock['learned_terms'][ti]['term'];c=r['candidate'];b=r['baseline'];p=r['primary']
  key=(ti,ki);expected_by_cell[key]=r
  if r['task']!=task:errors.append(f'{key}: task mismatch')
  if r.get('learned_term')!=term or r.get('learned_term_sha256')!=digest(term):errors.append(f'{key}: learned term mismatch')
  if r.get('bound_rule_where')!=expected_where(term):errors.append(f'{key}: bound native rule differs from learned AST')
  if not r.get('source_stable') or r.get('source_before')!=lock['sources'] or r.get('source_after')!=lock['sources']:errors.append(f'{key}: source drift')
  if b.get('proposal_built') or not b.get('branch_changed'):errors.append(f'{key}: invalid/no-op baseline')
  if not(c.get('branch_changed') and c.get('native_rule_fired')==c.get('derived_cue')):errors.append(f'{key}: candidate branch/cue execution failed')
  if c.get('derived_cue')!=expected_truth(task):errors.append(f'{key}: cue precision/recall mismatch')
  if c.get('axis_count')!=(1 if expected_truth(task) else 0):errors.append(f'{key}: axis cardinality mismatch')
  if not(p.get('unchanged_during_branch') and p.get('rules_unchanged_during_branch')
      and p.get('revision_unchanged_during_branch') and p.get('only_residual_returned')):errors.append(f'{key}: primary isolation/return failed')
  if not c.get('target_rule_preserved_in_primary') or not c.get('primary_rule_store_unchanged_during_compose'):
   errors.append(f'{key}: primary target/rule mutation')
  if task['kind']=='opposite':
   score=c.get('heldout_score') or {}
   if not(c.get('proposal_built') and c.get('operator')=='flip_comparison' and c.get('target')=='hop_descend_gradient'):
    errors.append(f'{key}: positive proposal mismatch')
   if not(score.get('oracle_pass') and score.get('receipt_verified') and score.get('primary_preserved')):
    errors.append(f'{key}: held-out task utility failed')
  elif task['kind']=='absent_target':
   if not c.get('derived_cue') or c.get('proposal_built'):errors.append(f'{key}: absent-target control failed')
  elif c.get('proposal_built'):errors.append(f'{key}: false proposal on negative control')
 if len(expected_by_cell)!=65:errors.append('duplicate or missing integration cell')
 positives=[r for r in rows if r['task']['kind']=='opposite'];ordinary=[r for r in rows if r['task']['kind'] not in ('opposite','absent_target')]
 absent=[r for r in rows if r['task']['kind']=='absent_target']
 summary={'terms':5,'task_cases_per_term':13,'cells':len(rows),'positive_cells':len(positives),
  'ordinary_negative_cells':len(ordinary),'target_absent_cells':len(absent),
  'cue_true_positive':sum(bool(r['candidate']['derived_cue']) for r in positives),
  'cue_false_positive':sum(bool(r['candidate']['derived_cue']) for r in ordinary),
  'cue_target_absent_positive':sum(bool(r['candidate']['derived_cue']) for r in absent),
  'heldout_repair_passes':sum(bool((r['candidate'].get('heldout_score') or {}).get('oracle_pass')) for r in positives),
  'false_proposals':sum(bool(r['candidate']['proposal_built']) for r in ordinary+absent),
  'primary_isolation_returns':sum(bool(r['primary'].get('unchanged_during_branch') and r['primary'].get('only_residual_returned')) for r in rows),
  'median_branch_fork_ms':statistics.median(r['fork_ns'] for r in rows)/1e6,
  'median_native_induction_ms':statistics.median(r['candidate']['induction_ns'] for r in rows)/1e6,
  'median_composer_grounding_ms':statistics.median(r['candidate']['ground_ns'] for r in rows)/1e6,
  'median_heldout_scoring_ms':statistics.median([r['candidate']['score_ns'] for r in positives])/1e6,
  'median_prior_term_acquisition_ms':statistics.median(t['search_wall_ns'] for t in lock['learned_terms'])/1e6,
  'amortized_acquisition_ms_per_case_at_13_uses':statistics.median(t['search_wall_ns'] for t in lock['learned_terms'])/13/1e6}
 result={'schema':'LearnedNumericCueComposerIntegrationV1Analysis','measurement_integrity_pass':not errors,
  'integration_gate_pass':not errors,'errors':errors,'summary':summary,
  'input_hashes':{'lock_sha256':sha(LOCK),'capture_sha256':sha(DATA),'learner_capture_sha256':sha(LEARN_DATA)}}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
