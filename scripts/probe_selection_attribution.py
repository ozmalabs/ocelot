"""Instrument SELECTION: which path admitted a candidate, and what its benefit
terms evaluated to at that moment.

Every failed change in docs/decision_making_spike.md §74 was aimed at a path
that had not been shown to be the deciding one.  Rules leave no attribution in
the graph, so this reconstructs it from two things that are observable:

  * WHEN a model first becomes a program member -- which localises the
    admitting action exactly;
  * `program_mode` at that action -- which distinguishes the calibration path
    from the synthesis path;
  * WHICH COMPOSER made the choice -- the one thing whose absence cost an entire
    thread (§76).  Both mark-choice rules stamp `render_choice_seq` on the
    candidate they pick, and which of them can fire is fixed by two policy
    flags, so a candidate carrying a fresh stamp was chosen by the active
    composer and one without it was admitted by calibration or expansion
    instead.  Reporting "synthesis" was true and useless: the synthesis-mode
    choice is made by the Rust `MotorCompose` term in this world, and six
    changes to the seed's ranking functions were byte-identical because of it.

and alongside it evaluates, per candidate, the quantities the ranking functions
read, so a decision can be read rather than inferred:

    goal residual WITHOUT it   sum_k w_k * target_k^2
    goal residual WITH it      sum_k w_k * (target_k - mean_k)^2
    goal benefit               without - with        (furtherance of goals)
    resource                   drag + energy + activation + authority penalty

Purely additive: it reads the graph and changes nothing.
"""
from __future__ import annotations

import json
import os
import sys

os.environ.setdefault("GAMMA_REGIME_DIAGNOSTICS", "1")
sys.path.insert(0, ".")

import scripts.jabberwock_fixed_wing_jet as J  # noqa: E402

COMPONENTS = ("forward", "lateral", "vertical", "roll", "pitch", "turn")
RESOURCE = ("drag", "energy")
EVENTS: list[dict] = []
SEEN: set = set()
_original = J._settle_graph_request


def _f(node, key, default=0.0):
    value = node.get(key, default)
    return float(value) if isinstance(value, (int, float)) else default


def _terms(agent, episode_attrs, policy_attrs, model):
    a = agent.s.node(model)["attrs"]
    without = with_ = 0.0
    for key in COMPONENTS:
        w = _f(policy_attrs, f"{key}_weight")
        target = _f(episode_attrs, f"target_{key}")
        without += w * target * target
        residual = target - _f(a, f"mean_{key}")
        with_ += w * residual * residual
    resource = sum(_f(policy_attrs, f"{k}_weight") * _f(a, f"mean_{k}")
                   for k in RESOURCE)
    resource += _f(policy_attrs, "activation_weight") * (
        _f(a, "activation_magnitude") - _f(a, "log_authority")
    )
    return {
        "token": str(a.get("token")),
        "chosen_by_composer": _f(a, "render_choice_seq", -1.0),
        "goal_without": round(without, 6),
        "goal_with": round(with_, 6),
        "goal_benefit": round(without - with_, 6),
        "resource": round(resource, 6),
        "log_vector_weight": round(_f(a, "log_vector_weight"), 3),
        "max_pos_change": round(
            _f(a, "specified_maximum_position_change_per_action"), 4),
        "experience": round(_f(a, "experience_count"), 1),
    }


def _patched(agent, episode, request_seq, *args, **kwargs):
    result = _original(agent, episode, request_seq, *args, **kwargs)
    episode_attrs = agent.s.node(episode)["attrs"]
    policies = agent.inner.neighbours(agent.agent, "has_embodied_motor_program_policy") \
        if hasattr(agent, "agent") else []
    policy_attrs = agent.s.node(policies[0])["attrs"] if policies else {}
    models = agent.inner.neighbours(episode, "has_embodied_effector_model")
    for program in agent.inner.neighbours(episode, "has_embodied_motor_program"):
        for member in agent.inner.neighbours(
            program, "includes_embodied_effector_model"
        ):
            key = (program, member)
            if key in SEEN:
                continue
            SEEN.add(key)
            native = _f(policy_attrs, "native_composition_enabled") > 0.5
            render = _f(policy_attrs, "render_first_composition_enabled") > 0.5
            stamp = _f(agent.s.node(member)["attrs"], "render_choice_seq", -1.0)
            decision = _f(episode_attrs, "program_decision_seq", -2.0)
            if stamp >= 0.0 and abs(stamp - decision) < 1.5:
                composer = "native(MotorCompose)" if native else (
                    "render" if render else "rule")
            else:
                composer = "not-composer(calibration/expansion)"
            EVENTS.append({
                "action": request_seq,
                "mode": str(episode_attrs.get("program_mode")),
                "composer": composer,
                "native_enabled": native,
                "admitted": _terms(agent, episode_attrs, policy_attrs, member),
                "field": [
                    _terms(agent, episode_attrs, policy_attrs, m)
                    for m in models
                ][:40],
            })
    return result


J._settle_graph_request = _patched

from scripts.jabberwock_jsbsim_f16_paper_replication import run_experiment  # noqa: E402

scenario = sys.argv[1] if len(sys.argv) > 1 else "nominal"
seed = int(sys.argv[2]) if len(sys.argv) > 2 else 241102975
out = sys.argv[3] if len(sys.argv) > 3 else None
run_experiment(scenario_names=(scenario,), episodes_per_scenario=1,
               base_seed=seed, include_trace=False)

print(f"\n### {scenario}: {len(EVENTS)} admissions")
print(f"  {'action':>7}{'mode':>16}{'admitted':>10}{'benefit':>12}"
      f"{'resource':>11}{'log_vec':>9}{'dpos':>8}")
for e in EVENTS[:20]:
    a = e["admitted"]
    print(f"  {e['action']:>7}{e['mode'][:15]:>16}{a['token'][:9]:>10}"
          f"{a['goal_benefit']:>12.4f}{a['resource']:>11.4f}"
          f"{a['log_vector_weight']:>9.2f}{a['max_pos_change']:>8.3f}")
by_mode: dict[str, int] = {}
for e in EVENTS:
    by_mode[e["mode"]] = by_mode.get(e["mode"], 0) + 1
print(f"  admissions by mode: {by_mode}")
by_comp: dict[str, int] = {}
for e in EVENTS:
    by_comp[e["composer"]] = by_comp.get(e["composer"], 0) + 1
print("  admissions by COMPOSER:")
for k, v in sorted(by_comp.items(), key=lambda x: -x[1]):
    print(f"    {k:<38}{v:>6}")
if out:
    json.dump(EVENTS, open(out, "w"))
    print(f"  -> {out}")
