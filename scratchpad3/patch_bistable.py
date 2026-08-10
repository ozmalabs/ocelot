"""RUNG 3B — add the BISTABLE (hysteretic) plasticity term to dv_oja_learn,
and its two knobs to DorsalParams. Authoring script; emits graph data."""
import json, copy

P = "seeds/vision_dorsal.json"
d = json.load(open(P))
d["version"] = "1.1.0"

def A(node, key):
    return {"type": "Attr", "node": node, "key": key}
def PARAM(key):
    return A({"type": "Pick", "source": {"type": "NodesOfType", "node_type": "DorsalParams"}}, key)
def V(n): return {"type": "Var", "name": n}
def L(x): return {"type": "Lit", "value": x}

# ---- knobs as GRAPH DATA, both 0.0 = OFF = the committed rung-3 rule exactly.
dp = d["nodes"][0]["attrs"]
dp["bistable"] = 0.0
dp["bi_eta"] = 0.0
dp["comment"] += (
 " RUNG 3B ADDS TWO KNOBS, BOTH 0.0 BY DEFAULT (= the committed rung-3 rule,"
 " byte-identically: the bistable term is multiplied by `bistable`, so at 0.0 it"
 " contributes exactly +0.0 and every rung-3 number reproduces). bistable: 1.0"
 " arms the HYSTERETIC/BISTABLE plasticity term in dv_oja_learn. bi_eta: its"
 " rate. WHY THIS EXISTS — the rung-3 confirmatory run (n=100, seeds 4000-4099)"
 " measured, not inferred, that NEITHER waves NOR moving experience build"
 " direction selectivity here, and named the cause: OJA'S FIXED POINT IS THE"
 " LEADING PRINCIPAL COMPONENT OF THE TIME-AVERAGED INPUT COVARIANCE, and"
 " natural motion is direction-ISOTROPIC on average, so a contraction to the"
 " mean of an isotropic distribution IS the mean and the mean has no direction."
 " No parameter of the rung-3 rule can fix that (eta, P2, max_delay, delay_tol"
 " are frozen and stay frozen); the REQUIRED property is symmetry-breaking"
 " faster than the averaging timescale. bi_eta is set by a positive control"
 " ONLY, exactly as rung 3 fixed eta=2e-3 — a control that contains no arm and"
 " no hypothesis.")

# ---- the term.
syns = {"type": "InNeighbours", "node": V("u"), "edge_type": "dpost", "any_type": False}
m = {"type": "Div",
     "a": {"type": "Sum", "source": syns, "var_name": "sy2", "value": A(V("sy2"), "weight")},
     "b": {"type": "Plus", "items": [{"type": "Count", "source": syns}, L(1e-9)]}}
w = A(V("s"), "weight")
mm = {"type": "Let", "name": "m", "value": m, "body": None}   # placeholder if Let is needed

# Let-free form (m recomputed in each factor; pure, so identical).
def M(): return copy.deepcopy(m)

bistable_term = {"type": "Times", "items": [
    PARAM("bistable"),
    PARAM("bi_eta"),
    {"type": "Div",
     "a": {"type": "Times", "items": [
         {"type": "Minus", "a": w, "b": M()},                                        # (w - m)
         {"type": "Minus", "a": {"type": "Times", "items": [L(2.0), M()]}, "b": w},  # (2m - w)
         w,                                                                          # w
     ]},
     "b": {"type": "Plus", "items": [                                                # 4m^2 (+eps)
         {"type": "Times", "items": [L(4.0), M(), M()]}, L(1e-12)]}},
]}

rule = [r for r in d["rules"] if r["name"] == "dv_oja_learn"][0]
eff = [e for e in rule["effects"] if e[1] == "s" and e[2] == "weight"][0]
old = eff[3]["__term__"]
assert old["type"] == "Plus"
eff[3]["__term__"] = {"type": "Plus", "items": list(old["items"]) + [bistable_term]}

rule["comment"] += (
 "\n\nRUNG 3B — THE BISTABLE/HYSTERETIC TERM (gated on DorsalParams.bistable,"
 " 0.0 by default, so at 0.0 it is exactly +0.0 and this rule is byte-identically"
 " the committed rung-3 Oja rule).\n\n"
 "THE DEFECT IT ATTACKS, measured not inferred (VISION_RUNG3_PREREG.md OUTCOME,"
 " n=100, fresh seeds 4000-4099): Oja's rule is LINEAR in x with a UNIQUE"
 " attractor — the leading principal component of the TIME-AVERAGED input"
 " covariance. Natural motion is direction-isotropic ON AVERAGE, so that average"
 " has no direction, and the rule converges to it however much coherent motion"
 " each individual epoch contains. `normal` beat the untrained floor by +0.0061"
 " (1.2% of the 0.489 dynamic range) and `dark` by +0.0096. The stability that"
 " rescued rung 2 from nine transient-measured failures is exactly what forbids"
 " rung 3: A CONTRACTION TO THE MEAN OF AN ISOTROPIC DISTRIBUTION IS THE MEAN.\n\n"
 "THE TERM, and it is one sentence: bi_eta * (w - m)(2m - w)w / (2m)^2, where m"
 " is the MEAN weight over this unit's own synapses (a Fold over its dpost"
 " neighbours — the unit's own aggregate, nothing global). Its zeros are w=0,"
 " w=m and w=2m; it is NEGATIVE for 0<w<m and POSITIVE for m<w<2m. So m — THE"
 " MEAN — IS AN UNSTABLE FIXED POINT, A REPELLER, and the stable ones are 0 and"
 " 2m. That is the most direct possible negation of the measured diagnosis:"
 " Oja's attractor is the mean; this makes the mean the one place a weight"
 " cannot stay. A synapse that is transiently above its unit's mean is LATCHED"
 " up rather than averaged back down, so a locally-consistent direction — the"
 " ~20-step drift epoch, the wave sweep — is committed to before the isotropic"
 " average can erase it. Once latched, the unit responds best to that direction,"
 " therefore WINS the winner-take-all on that direction, therefore learns it"
 " further: the positive feedback the diagnosis asked for ('a neuron must lock"
 " onto a LOCALLY consistent direction and keep it').\n\n"
 "IT IS SCALE-FREE ON PURPOSE, and that is why it adds ONE knob and not four. A"
 " textbook bistable rule needs an absolute threshold and an absolute ceiling"
 " (w_min, theta_b, w_max), and all three would be free parameters begging to be"
 " swept — which is the parameter search this rung is forbidden. Here the"
 " threshold IS the unit's own mean and the ceiling IS twice it, both recomputed"
 " every update from the unit's own state, so the term has no absolute scale and"
 " cannot be tuned by choosing one. It also self-corrects: weights above 2m are"
 " pushed back DOWN toward 2m, so the term is bounded and cannot run away.\n\n"
 "ASSERTED BIOLOGY, not convenience. Single synapses express LTP in an"
 " ALL-OR-NONE, bistable fashion rather than by graded averaging (Petersen,"
 " Malenka, Nicoll & Hopfield 1998), and bistable/hysteretic synaptic switches"
 " are the standard account of how a synapse retains a transient correlation"
 " against ongoing noise (Lisman 1985's CaMKII switch; Fusi's cascade). A purely"
 " graded synapse is the one that cannot hold a memory of a passing event, which"
 " is precisely what rung 3 measured.\n\n"
 "WHY NOT THE ANTI-HEBBIAN LATERAL FIRST (the other named candidate, and rung"
 " 4's vm_burst_lateral is a precedent for lateral interactions in this tree):"
 " because it does not attack the diagnosis. Any rule LINEAR in x has an"
 " averaging attractor; lateral decorrelation changes WHICH average a unit"
 " converges to (which principal component), it does not make an average"
 " directional. The local Foldiak form w <- w(1 - eta*y_v^2) - eta*y_v*x has"
 " fixed point w = -xbar/ybar — i.e. MINUS the mean, still the mean. The form"
 " that would genuinely deflate onto a lower component is Sanger's, which needs"
 " a synapse to read the WINNER's weight vector and is therefore not local; the"
 " local Rubner-Tavan form needs the lateral term to modify the OUTPUT inside the"
 " fixpoint, which races dv_burst_winner's Argmax over the same dact. Bistability"
 " needs no new graph structure, no lateral wiring, no adapter change and no"
 " race — and it is NONLINEAR IN w, which is the property the diagnosis actually"
 " demands.")

json.dump(d, open(P, "w"), indent=1)
print("patched", P, "->", d["version"])
