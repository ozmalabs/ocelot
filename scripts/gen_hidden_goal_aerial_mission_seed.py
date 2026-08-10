"""Author graph-native learning and selection for hidden-goal aerial search."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def V(name): return {"type": "Var", "name": name}
def L(value): return {"type": "Lit", "value": value}
def A(var, key): return {"type": "Attr", "node": V(var), "key": key}
def P0(var, key): return {"type": "Plus", "items": [A(var, key), L(0.0)]}
def Plus(*items): return {"type": "Plus", "items": list(items)}
def Minus(a, b): return {"type": "Minus", "a": a, "b": b}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def And(*items): return {"type": "And", "items": list(items)}
def Neighbours(var, edge): return {"type": "Neighbours", "node": V(var), "edge_type": edge}
def Filter(source, var, predicate): return {"type": "Filter", "source": source, "var_name": var, "predicate": predicate}
def Argmax(source, var, value, default): return {"type": "Argmax", "source": source, "var_name": var, "value": value, "default": default}
def T(term): return {"__term__": term}


MODELS = Neighbours("episode", "has_hidden_goal_action_model")


def learn_rule():
    return {
        "name": "hga_learn_opaque_search_action",
        "area": "aerial_search_learning",
        "latency_class": "soft_realtime",
        "match": [
            ["episode", "has_hidden_goal_calibration_trial", "trial"],
            ["trial", "tests_hidden_goal_action", "model"],
            ["trial", "has_hidden_goal_calibration_outcome", "outcome"],
        ],
        "where": Eq(P0("outcome", "processed"), L(0.0)),
        "effects": [
            ["set_attr", "model", "mean_progress", T(P0("outcome", "progress_delta"))],
            ["set_attr", "model", "mean_emission", T(P0("outcome", "emission_delta"))],
            ["set_attr", "model", "experience_count", 1.0],
            ["set_attr", "outcome", "processed", 1.0],
        ],
    }


def locate_rule():
    return {
        "name": "hga_bind_hidden_signal_as_goal",
        "area": "aerial_search",
        "latency_class": "hard_realtime",
        "match": [
            ["agent", "has_hidden_goal_policy", "policy"],
            ["agent", "has_hidden_goal_episode", "episode"],
        ],
        "where": And(
            Eq(P0("episode", "goal_located"), L(0.0)),
            Gt(P0("episode", "state_signal_strength"), P0("policy", "signal_threshold")),
        ),
        "effects": [
            ["set_attr", "episode", "goal_located", 1.0],
            ["set_attr", "episode", "located_x", T(P0("episode", "state_x"))],
            ["set_attr", "episode", "located_y", T(P0("episode", "state_y"))],
        ],
    }


def choose_rule():
    search = Filter(MODELS, "candidate", Lt(P0("candidate", "mean_emission"), L(0.5)))
    payload = Filter(MODELS, "candidate", Gt(P0("candidate", "mean_emission"), L(0.5)))
    best_search = Argmax(search, "candidate", Plus(P0("candidate", "mean_progress"), P0("candidate", "experience_count")), V("episode"))
    best_payload = Argmax(payload, "candidate", P0("candidate", "mean_emission"), V("episode"))
    return {
        "name": "hga_choose_search_or_goal_marker",
        "area": "aerial_search",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["agent", "has_hidden_goal_policy", "policy"],
            ["agent", "has_hidden_goal_episode", "episode"],
            ["episode", "has_hidden_goal_action_model", "model"],
        ],
        "where": And(
            Eq(P0("episode", "action_ready"), L(0.0)),
            Gt(P0("episode", "request_seq"), P0("episode", "decision_seq")),
            Eq(
                P0("model", "ordinal"),
                {"type": "Attr", "node": {
                    "type": "IfThenElse",
                    "cond": Gt(P0("episode", "goal_located"), L(0.5)),
                    "then": best_payload,
                    "other": best_search,
                }, "key": "ordinal"},
            ),
        ),
        "effects": [
            ["set_attr", "episode", "selected_token", T(A("model", "token"))],
            ["set_attr", "episode", "decision_seq", T(P0("episode", "request_seq"))],
            ["set_attr", "episode", "action_ready", 1.0],
        ],
    }


def manifest():
    return {
        "id": "hidden_goal_aerial_mission",
        "version": "1.0.0",
        "depends_on": [],
        "area": "aerial_search",
        "latency_class": "hard_realtime",
        "nodes": [{"local_id": 1, "type": "HiddenGoalPolicy", "attrs": {"signal_threshold": 0.05}}],
        "edges": [{"src": {"role": "agent_root"}, "type": "has_hidden_goal_policy", "tgt": {"local": 1}, "attrs": {}}],
        "productions": [],
        "rules": [learn_rule(), locate_rule(), choose_rule()],
    }


def main():
    path = ROOT / "seeds" / "hidden_goal_aerial_mission.json"
    path.write_text(json.dumps(manifest(), indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
