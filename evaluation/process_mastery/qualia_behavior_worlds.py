"""Independent finite later-task worlds for the P17 behavioral panel."""
from __future__ import annotations

import random


ACTION_MAPS = {
    "tool_contact": {"repair": (0,), "continue": (0,)},
    "social_request_repair": {"repair-request": (0,), "normal-response": (0,)},
}


def task(family: str, seed: int):
    if family not in ACTION_MAPS:
        raise ValueError(f"unsupported P17 family: {family}")
    rng = random.Random(seed)
    if family == "tool_contact":
        feature_key, feature_family = "tool-contact-pattern", "tool_contact"
        feature_value, good_action = rng.choice((
            ("rough", "repair"), ("smooth", "continue")))
    else:
        feature_key, feature_family = "social-repair-pattern", "social_request_repair"
        feature_value, good_action = rng.choice((
            ("repair-needed", "repair-request"), ("repair-not-needed", "normal-response")))
    return {"family": family, "seed": int(seed), "initial_state": (0,), "goal_state": (1,),
            "primitive_affordances": ACTION_MAPS[family], "legal_actions_by_state": {"0": sorted(ACTION_MAPS[family])},
            "feature_key": feature_key, "feature_family": feature_family,
            "feature_value": feature_value, "expected_action": good_action,
            "context_id": f"context-{seed % 7}"}
