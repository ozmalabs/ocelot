"""Run the pre-registered held-out Phase 3 extended-thinking evaluation."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from substrate.boot_core import CORE_SEEDS
from substrate.world_adapter import WorldAdapter
from evaluation.substrate_capability import extended_thinking_instances_v1 as instances


def _nodes(agent, kind):
    return [n for n in agent.s.nodes(kind)]


def _edge(agent, src, edge_type, tgt):
    try:
        agent.inner.add_edge_unchecked(src, edge_type, tgt, {})
    except TypeError:
        agent.inner.add_edge_unchecked(src, edge_type, tgt)


def _add_sample(agent, epoch):
    sample = agent.s.add_node("NetworkModeSample", {
        "epoch": float(epoch), "exteroceptive_load": 0.0, "task_demand": 0.0,
        "interoceptive_urgency": 0.0, "uncertainty": 0.2,
        "idle_duration": 0.0, "status": "raw",
    })
    _edge(agent, agent.agent, "has_network_mode_sample", sample)


def _add_observation(agent, case):
    codebook_epoch = agent.s.node(agent.agent)["attrs"].get("codebook_epoch", 0.0)
    obs = agent.s.add_node("Observation", {
        "signature": case["goal"], "key": ["extended_thinking", case["family"], case["seed"]],
        "status": "decoded", "residual": case["goal"],
        "decoded_epoch": codebook_epoch, "dim_types": case["dim_types"],
    })
    _edge(agent, agent.agent, "observed", obs)
    return obs


def _boot(arm):
    agent = WorldAdapter(seeds=CORE_SEEDS + ("thinking_budget", "extended_thinking", "inference_ladder_record"))
    policy = next(n for n in agent.inner.neighbours(agent.agent, "has_extended_thinking_policy")
                  if agent.s.node(n)["attrs"].get("name") == "core_extended_thinking_policy")
    budget = next(n for n in agent.inner.neighbours(agent.agent, "has_thinking_budget")
                  if agent.s.node(n)["attrs"].get("name") == "core_thinking_budget")
    agent.s.set_attr(policy, "enabled", 1.0 if arm == "et_on" else 0.0)
    agent.s.set_attr(budget, "enabled", 1.0 if arm == "et_on" else 0.0)
    agent.s.set_attr(budget, "capacity", 16.0)
    agent.s.set_attr(budget, "remaining", 16.0)
    agent.s.set_attr(budget, "refill_per_epoch", 2.0)
    agent.s.set_attr(agent.agent, "codebook_epoch", 0.0)
    return agent, budget


def _settle(agent, obs, start_epoch):
    for epoch in range(start_epoch, start_epoch + 20):
        _add_sample(agent, epoch)
        agent.tick()
        status = agent.s.node(obs)["attrs"].get("status")
        if status in {"recognized_transformed", "recognized", "recognized_duplicate"}:
            return epoch + 1
        episodes = [agent.s.node(n)["attrs"] for n in _nodes(agent, "ExtendedThinkingEpisode")]
        if episodes and all(x.get("status") == "settled" for x in episodes) and status == "minted":
            return epoch + 1
    return start_epoch + 20


def _episode_stats(agent):
    episodes = [agent.s.node(n)["attrs"] for n in _nodes(agent, "ExtendedThinkingEpisode")]
    requests = [agent.s.node(n)["attrs"] for n in _nodes(agent, "ExtendedThinkingStepRequest")]
    return (sum(int(x.get("steps", 0)) for x in episodes),
            sum(float(x.get("cost", 0.0)) for x in requests if x.get("debited_epoch") is not None),
            sum(int(x.get("status") in {"approved", "consumed"}) for x in requests),
            sum(x.get("status") == "consumed" for x in requests), episodes)


def _arm_result(case, arm):
    agent, budget = _boot(arm)
    agent.s.add_node("ShapeSignature", {
        "name": f"held_{case['family']}_{case['seed']}",
        "signature": json.dumps(case["base"]), "kind": "faculty",
        "faculty": f"held_{case['family']}_{case['seed']}", "dim_types": case["dim_types"],
    })
    obs = _add_observation(agent, case)
    _settle(agent, obs, 1)
    attrs = agent.s.node(obs)["attrs"]
    first_steps, spent, approved_first, applied_first, first_eps = _episode_stats(agent)
    lease_count_first = len(_nodes(agent, "ToleranceRelaxLease"))
    first = {"solved": attrs.get("status") == "recognized_transformed",
             "status": attrs.get("status"), "steps": first_steps, "budget_spent": spent,
             "accepted_at_relaxed": attrs.get("accepted_at_relaxed"),
             "accepted_rung": attrs.get("accepted_rung"),
             "approved_requests": approved_first,
             "applied_steps": lease_count_first,
             "funding_upper_bound": 96.0,
             "false_accept": attrs.get("status") == "recognized_transformed" and case["family"].startswith("control")}

    second_obs = _add_observation(agent, case)
    _settle(agent, second_obs, 21)
    second_attrs = agent.s.node(second_obs)["attrs"]
    second_steps_total, spent_total, approved_total, applied_total, second_eps = _episode_stats(agent)
    lease_count_total = len(_nodes(agent, "ToleranceRelaxLease"))
    second = {"solved": second_attrs.get("status") == "recognized_transformed",
              "status": second_attrs.get("status"),
              "steps": max(0, second_steps_total - first_steps),
              "budget_spent": max(0.0, spent_total - spent),
              "approved_requests": max(0, approved_total - approved_first),
              "applied_steps": max(0, lease_count_total - lease_count_first),
              "accepted_at_relaxed": second_attrs.get("accepted_at_relaxed"),
              "episodes_added": max(0, len(second_eps) - len(first_eps))}
    agent.close()
    return {"arm": arm, "first": first, "second": second}


def run(prereg_hash: str, first: int, end: int) -> dict:
    base_seed = int(prereg_hash[:8], 16)
    rows = []
    for i in range(int(first), int(end)):
        seed = base_seed + 7919 * i
        cases = [("A", instances.family_a(seed)), ("B", instances.family_b(seed))]
        if i < 100:
            cases.extend([("control_a", instances.control_a(seed)),
                          ("control_b_value_noise", instances.control_b_value_noise(seed)),
                          ("control_b_quadratic", instances.control_b_quadratic(seed))])
        for family, case in cases:
            case["draw_index"] = i
            on = _arm_result(case, "et_on")
            off = _arm_result(case, "et_off")
            rows.append({"family": family, "seed": seed, "draw_index": i,
                         "et_on": on, "et_off": off})
    return {"protocol": "extended_thinking_heldout_v1", "prereg_hash": prereg_hash,
            "first": int(first), "end": int(end), "rows": rows}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 3:
        raise SystemExit("usage: extended_thinking_heldout_v1.py <prereg_hash> <first> <end>")
    prereg_hash, first, end = argv[0], int(argv[1]), int(argv[2])
    if end < first:
        raise SystemExit("end must be >= first")
    report = run(prereg_hash, first, end)
    out_dir = ROOT / "evaluation" / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"extended_thinking_heldout_v1_{prereg_hash[:8]}_d{first}-{end}.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
