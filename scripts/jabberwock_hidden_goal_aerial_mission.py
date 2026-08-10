"""Run a graph-native hidden-goal aerial search and flare-marking mission."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
for _path in (ROOT, ROOT / "runners" / "dsl" / "python"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from domains.embodied_graph_transducer import add_unchecked_edge as _edge  # noqa: E402
from domains.hidden_goal_landscape_world import HiddenGoalLandscapeWorld  # noqa: E402
from substrate.world_adapter import WorldAdapter  # noqa: E402


def run_hidden_goal_mission(*, maximum_steps: int = 60) -> dict:
    if maximum_steps < 1:
        raise ValueError("maximum_steps must be positive")
    agent = WorldAdapter(seeds=("hidden_goal_aerial_mission",))
    episode = agent.s.add_node("HiddenGoalEpisode", {
        "request_seq": 0.0,
        "decision_seq": 0.0,
        "action_ready": 0.0,
        "goal_located": 0.0,
        "state_signal_strength": 0.0,
        "state_x": 0.0,
        "state_y": 0.0,
    })
    _edge(agent, agent.agent, "has_hidden_goal_episode", episode)
    world = HiddenGoalLandscapeWorld()
    models = []
    for option in world.actuator_options():
        model = agent.s.add_node("HiddenGoalActionModel", {
            "token": option["token"],
            "ordinal": option["ordinal"],
            "mean_progress": 0.0,
            "mean_emission": 0.0,
            "experience_count": 0.0,
            "semantics": "unknown",
        })
        _edge(agent, episode, "has_hidden_goal_action_model", model)
        models.append(model)

    # Reset-bounded causal calibration is simulator-safe world transduction.
    for ordinal, model in enumerate(models):
        before = world.reset()
        after = world.step(world.actuator_options()[ordinal]["token"])
        trial = agent.s.add_node("HiddenGoalCalibrationTrial", {})
        outcome = agent.s.add_node("HiddenGoalCalibrationOutcome", {
            "progress_delta": (
                after["route_progress"] - before["route_progress"]
            ),
            "emission_delta": (
                after["payload_emission_count"]
                - before["payload_emission_count"]
            ),
            "processed": 0.0,
        })
        _edge(agent, episode, "has_hidden_goal_calibration_trial", trial)
        _edge(agent, trial, "tests_hidden_goal_action", model)
        _edge(agent, trial, "has_hidden_goal_calibration_outcome", outcome)
        agent.tick()

    observation = world.reset()
    trace = []
    for request_seq in range(1, maximum_steps + 1):
        position = observation["position"]
        for key, value in {
            "state_x": float(position[0]),
            "state_y": float(position[1]),
            "state_signal_strength": float(observation["signal_strength"]),
            "request_seq": float(request_seq),
            "action_ready": 0.0,
        }.items():
            agent.inner.set_attr(episode, key, value)
        agent.tick()
        attrs = agent.s.node(episode)["attrs"]
        if float(attrs.get("action_ready", 0.0)) != 1.0:
            raise RuntimeError("graph emitted no hidden-goal mission action")
        token = str(attrs["selected_token"])
        observation = world.step(token)
        trace.append({
            "request_seq": request_seq,
            "position": list(observation["position"]),
            "terrain_height": observation["terrain_height"],
            "signal_strength": observation["signal_strength"],
            "goal_located": float(attrs["goal_located"]),
            "selected_token": token,
            "flare_count": observation["payload_emission_count"],
            "goal_marked": observation["goal_marked"],
        })
        if observation["goal_marked"] == 1.0:
            break
    return {
        "target_location_exposed_to_graph": False,
        "goal_marked": observation["goal_marked"],
        "steps": len(trace),
        "flare_count": observation["payload_emission_count"],
        "located_position": [
            agent.s.node(episode)["attrs"].get("located_x"),
            agent.s.node(episode)["attrs"].get("located_y"),
        ],
        "models": [
            {
                key: agent.s.node(model)["attrs"].get(key)
                for key in (
                    "token",
                    "ordinal",
                    "mean_progress",
                    "mean_emission",
                    "semantics",
                )
            }
            for model in models
        ],
        "trace": trace,
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--maximum-steps", type=int, default=60)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    result = run_hidden_goal_mission(maximum_steps=args.maximum_steps)
    payload = json.dumps(result, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
