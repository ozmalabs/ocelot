"""Shape-residual future-manifold contracts."""
import json, os, pytest
pytest.importorskip("substrate_rs")
from substrate.world_adapter import WorldAdapter
from domains.information_commitment import assess
from domains.future_option_risk import evaluate_future_manifold
ROOT=os.path.dirname(os.path.dirname(__file__))
def _fresh():
 a=WorldAdapter(seeds=())
 for n in ("cognitive_areas","information_commitment"): a.inner.load_seed_manifest(json.load(open(os.path.join(ROOT,"seeds",n+ ".json"))),a.agent)
 return a
def _slice(t, width=1, info=0, cells=None): return {"time":t,"cells":cells or {"core":{"weight":width,"information":info,"metadata":{}}},"links":[]}
def _m(): return {"manifold_id":"m1","required_horizon":2,"minimum_width":1,"maximum_information_loss":0,"required_tube":[_slice(0),_slice(1),_slice(2)]}
def _p(**kw): return {"manifold_id":"m1","action_count":0,"intervention_magnitude":0,"projected_tube":[_slice(0),_slice(1),_slice(2)],**kw}
def _c(kind,**kw): return {"name":kind,"expected_goal_work":1,"projection":_p(),**kw}
def test_shape_residual_vetoes_and_pure_order():
 assert evaluate_future_manifold(_m(),_p(projected_tube=[_slice(0),_slice(1)])).reason=="insufficient_temporal_coverage"
 assert evaluate_future_manifold(_m(),_p(projected_tube=[_slice(0),_slice(1),_slice(2,width=2)])).reason=="outside_future_manifold"
 loss_m={**_m(),"required_tube":[_slice(0),_slice(1),_slice(2,info=1)]}
 assert evaluate_future_manifold(loss_m,_p()).reason=="excess_information_loss"
def test_objective_cannot_buy_shape_residual_violation():
 bad=_p(projected_tube=[_slice(0),_slice(1),_slice(2,width=2)])
 out=assess(_fresh(),manifold=_m(),wait=_c("wait"),refine=_c("refine"),commit=_c("commit",expected_goal_work=10**18,projection=bad))
 assert out["decision"]=="wait"

def test_topology_only_escape_is_not_hidden_by_zero_width():
 p=_p(projected_tube=[_slice(0),_slice(1),{**_slice(2),"cells":{"core":{"weight":1,"information":0,"metadata":{}},"extra":{"weight":0,"information":0,"metadata":{}}},"links":[{"source":"core","target":"extra","information":1}]}])
 assert evaluate_future_manifold(_m(),p).reason=="outside_future_manifold"
 out=assess(_fresh(),manifold=_m(),wait=_c("wait"),refine=_c("refine"),commit=_c("commit",expected_goal_work=10**18,projection=p))
 assert out["decision"]=="wait"
def test_lower_intervention_and_ordinal_are_deterministic():
 out=assess(_fresh(),manifold=_m(),wait=_c("wait",projection=_p(intervention_magnitude=0.1)),refine=_c("refine",expected_goal_work=10**18,projection=_p(intervention_magnitude=1)),commit=_c("commit",expected_goal_work=10**19,projection=_p(intervention_magnitude=1)))
 assert out["decision"]=="wait"
def test_missing_projection_or_unvalidated_direct_graph_fails_closed():
 with pytest.raises(ValueError): assess(_fresh(),manifold=_m(),wait={},refine=_c("refine"),commit=_c("commit"))
