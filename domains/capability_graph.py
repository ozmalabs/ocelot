"""Capability graph — mechanical host I/O for the agent's self-model of competence
(seeds/capability_graph.json).

The DECISIONS/measures live in the seed rules (leverage propagation, multiplicative
composition, leverage->sufficiency, stage). This module only does mechanical graph
translation: mint capabilities, wire composes_on edges, settle the fixpoint, read the
computed measures back out. No conditional chooses anything here.

`like_but` is the load-bearing constructor: a new domain enters the graph as "like X
but Y" — it composes_on the analogue X (inheriting X's mastered structure) AND on the
shape-matching faculty that recognised the analogy (the meta-skill that FORMED the
edge), carrying only its thin novel proficiency (the Y). That attachment is why
mastered core multiplies into a new field from passing familiarity.
"""
from __future__ import annotations


def _attrs(s, nid):
    return s.node(nid)["attrs"]


def mint_root(s, **policy):
    root = None
    for n in s.nodes("CapabilityRoot"):
        root = n
        break
    if root is None:
        root = s.add_node("CapabilityRoot", {"kind": "capability_root"})
    if not any(True for _ in s.nodes("CapabilityPolicy")):
        attrs = {"kind": "capability_policy", "damping": 0.6, "suff_base": 0.9,
                 "suff_slope": 0.03, "suff_cap": 0.999, "core_leverage": 3.0,
                 "periph_leverage": 1.6, "legibility_structural_base": 0.35,
                 "cost_weight": 0.01, "tier_margin": 2.5, "min_hotness": 1.0}
        attrs.update(policy)
        s.add_node("CapabilityPolicy", attrs)
    return root


def add_capability(s, root, name, own_prof, *, own_value=1.0):
    """A capability with its intrinsic proficiency. Measures init to their identity
    (leverage=own_value, eff_cap=own_prof) so the fixpoint accumulates from a clean base."""
    cap = s.add_node("Capability", {
        "name": str(name), "own_prof": float(own_prof), "own_value": float(own_value),
        "leverage": float(own_value), "eff_cap": float(own_prof),
        "sufficiency": 0.9, "stage": "blob", "genericity": 0.0,
        "cost": 0.0, "hotness": 0.0, "worth": -1.0, "tier_up": 0.0,
        "correctness": -1.0})
    s.add_edge(root, "has_capability", cap, {})
    return cap


def compose(s, a, b):
    """a composes_on b: a is built through b (b is the more foundational)."""
    s.add_edge(a, "composes_on", b, {})


def add_shaped(s, root, name, own_prof, shape, *, own_value=1.0):
    """A capability tagged with a generic SHAPE, so it can be matched across agents
    (two agents 'share' a skill when they hold capabilities of the same shape)."""
    cap = add_capability(s, root, name, own_prof, own_value=own_value)
    s.set_attr(cap, "shape", str(shape))
    return cap


def add_agent(s, name):
    """A mind — an owner of capabilities, and a possible observer/target of modelling."""
    return s.add_node("Agent", {"name": str(name)})


def hold(s, agent, base_shape, frame="native"):
    """The agent holds a skill of `base_shape` in some `frame` (its coordinates). Two
    skills of the same base_shape in different frames are the same structure, one a
    dimensional transform of the other."""
    cap = s.add_node("Capability", {"name": f"{base_shape}@{frame}", "own_prof": 1.0,
                     "own_value": 1.0, "leverage": 1.0, "eff_cap": 1.0,
                     "base_shape": str(base_shape), "frame": str(frame)})
    s.add_edge(agent, "owns", cap, {})
    return cap


def add_frame(s, name, base_shapes):
    """A new frame that requires a set of base-shapes to work in."""
    fr = s.add_node("Frame", {"name": str(name)})
    for b in base_shapes:
        req = s.add_node("Capability", {"name": f"req:{b}", "own_prof": 1.0,
                         "base_shape": str(b), "leverage": 1.0, "eff_cap": 1.0})
        s.add_edge(fr, "requires", req, {})
    return fr


def judge_trial(s, cap, verdict):
    """Record a judged firing of a capability against an oracle: verdict 'supported' or
    'refuted' (the reflex-net judge, generalised). correctness = supported-rate follows."""
    t = s.add_node("CapabilityTrial", {"verdict": str(verdict)})
    s.add_edge(t, "trial_of", cap, {})
    return t


def acquire(s, agent, frame):
    """agent enters frame. cap_frame_acquisition fills in new_skills / transforms /
    new_skill_fraction — the cost split between coordinate-changes and genuinely new skills."""
    a = s.add_node("FrameAcquisition", {"new_skill_fraction": -1.0})
    s.add_edge(a, "by", agent, {})
    s.add_edge(a, "into", frame, {})
    return a


def owns(s, agent, cap):
    s.add_edge(agent, "owns", cap, {})


def model_attempt(s, observer, target_competence):
    """observer tries to model target_competence (a Capability of another agent). The
    cap_model_legibility rule fills in content_overlap / meta_capacity / legibility / magic."""
    m = s.add_node("ModelAttempt", {"magic": -1.0})
    s.add_edge(m, "observer", observer, {})
    s.add_edge(m, "target", target_competence, {})
    return m


def like_but(s, root, name, analogue, novel_prof, *, shape_cap):
    """Enter a new domain as 'like <analogue> but <novel>': attach it to the analogue
    (inherit its mastered structure) and to the shape-matching faculty that recognised
    the analogy, carrying only the thin novel proficiency. Returns the new capability."""
    d = add_capability(s, root, name, novel_prof)
    compose(s, d, analogue)
    compose(s, d, shape_cap)
    return d


def settle(s):
    """Run the graph to fixpoint — leverage propagates up composes_on, effective
    capability multiplies down it, sufficiency + stage follow leverage."""
    native_steps = s.run_rules()
    s.add_node("NativeCapabilityGraphReceipt", {
        "schema": "native_capability_graph_receipt.v1",
        "cluster": "capability_graph.fixpoint_settlement",
        "provenance": "native_rule_readback:capability_graph",
        "native_rule": "capability_graph_native_fixpoint",
        "native_steps": int(native_steps),
        "outcome_source": "native_rule_readback",
        "python_outcome_selection": False,
    })


# --- mechanical readers of the computed self-model ---
def leverage(s, cap):
    return float(_attrs(s, cap).get("leverage", 0.0))


def eff_cap(s, cap):
    return float(_attrs(s, cap).get("eff_cap", 0.0))


def sufficiency(s, cap):
    return float(_attrs(s, cap).get("sufficiency", 0.0))


def stage(s, cap):
    return _attrs(s, cap).get("stage", "blob")


def genericity(s, cap):
    """HOW a capability is expert: the mean leverage of the foundations its mastery
    routes through. High = consolidated onto generic stacks (transfers); low = a
    domain-private tower (brittle)."""
    return float(_attrs(s, cap).get("genericity", 0.0))


def magic(s, model):
    """1 - legibility: the fraction of the target's competence the observer cannot
    reconstruct — the felt 'magic' of another mind."""
    return float(_attrs(s, model).get("magic", 1.0))


def legibility(s, model):
    return float(_attrs(s, model).get("legibility", 0.0))


def new_skill_fraction(s, acquisition):
    """Of the base-shapes a new frame requires, the fraction the agent must learn as
    genuinely NEW skills (rung 4) rather than reach by a dimensional transform of a held
    shape (rung 2). -> 0 for a sufficiently meta-skilled (high-genericity) agent."""
    return float(_attrs(s, acquisition).get("new_skill_fraction", 1.0))


def acquisition_split(s, acquisition):
    a = _attrs(s, acquisition)
    return int(a.get("new_skills", 0)), int(a.get("transforms", 0))


def own_proficiency(s, cap):
    """How good the skill itself is. Efficiency (from cost) by default; correctness (the
    supported-rate of its judged trials) once an oracle has judged it."""
    return float(_attrs(s, cap).get("own_prof", 0.0))


def correctness(s, cap):
    """The supported-rate of a capability's judged trials — its right-answer proficiency.
    -1.0 until an oracle has judged it."""
    return float(_attrs(s, cap).get("correctness", -1.0))


def worth(s, cap):
    """The one cost model at the capability grain: value − cost = leverage − cost_weight·cost."""
    return float(_attrs(s, cap).get("worth", 0.0))


def tier_up(s, cap):
    """Whether the capability clears the cost model's bar to be MASTERED — the same
    decision the net-economy makes to admit a net and the JIT makes to compile a Term."""
    return bool(_attrs(s, cap).get("tier_up", 0.0) >= 1.0)


def most_leveraged(s, root):
    """The meta-skill readout: which capability multiplies the most (highest leverage) —
    what the agent would invest mastery in first."""
    caps = list(s.neighbours(root, "has_capability"))
    if not caps:
        return None
    return max(caps, key=lambda c: leverage(s, c))
