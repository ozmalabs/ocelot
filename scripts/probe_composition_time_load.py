"""At every deliberation, what is worst = current_load / safe_load?

The log price is zero below 1.0 and, above it, is dominated by the CURRENT
load -- which every candidate shares.  This reads both, per action, so the
"zero or constant" claim is measured rather than deduced.
"""
import os, sys, json
os.environ["GAMMA_REGIME_DIAGNOSTICS"] = "1"
sys.path.insert(0, ".")
import scripts.jabberwock_fixed_wing_jet as J

LOADS = ["normal_load","peak_force","impulse","impact_energy","thermal_load",
         "dynamic_pressure","roll_moment","pitch_moment","yaw_moment",
         "heat_flux","skin_temperature"]
ROWS = []
_original = J._settle_graph_request

def _patched(agent, episode, request_seq, *a, **k):
    r = _original(agent, episode, request_seq, *a, **k)
    at = agent.s.node(episode)["attrs"]
    worst, who = 0.0, None
    for L in LOADS:
        safe = at.get(f"state_safe_{L}") or 0.0
        if not safe > 0: continue
        cur = abs(at.get(f"state_current_{L}") or 0.0)
        if cur / safe > worst: worst, who = cur / safe, L
    ROWS.append({"a": request_seq, "worst": worst, "load": who,
                 "lim": at.get("structural_limits_enabled"),
                 "esc": at.get("authority_escape_mode"),
                 "dec": at.get("regime_rung_decade")})
    return r

J._settle_graph_request = _patched
from scripts.jabberwock_jsbsim_f16_paper_replication import run_experiment
run_experiment(scenario_names=(sys.argv[1],), episodes_per_scenario=1,
               base_seed=int(sys.argv[2]), include_trace=False)
json.dump(ROWS, open(f"{os.environ['P']}/worst_{sys.argv[1]}.json","w"))
