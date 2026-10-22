"""P8 runner development adapter gate."""
from evaluation.process_mastery.linear_p8_v1 import run
from evaluation.process_mastery.analyze_linear_p8_v1 import analyze

def test_p8_development_adapters_produce_real_outcomes():
 p=run(self_check=True);assert p['metadata']['registered_draw'] is False
 assert len(p['records'])==6
 assert all(r['status'] in ('COMPLETED','UNSUPPORTED') for r in p['records'])
 assert any(r['family']=='finite_mechanism' and r['profile']=='learned' and r['outcome']=='identified' for r in p['records'])
 assert analyze(p)['n_records']==6
