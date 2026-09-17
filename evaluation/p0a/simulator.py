"""The one deterministic fixture effect, never enabled by a P0-A manifest."""
from __future__ import annotations

from .canonical import ProtocolError, sha256

METHOD = "simulator.counter.advance.v1"


def normalized_args(args: dict) -> dict:
    if set(args) != {"steps"} or type(args["steps"]) is not int or not 0 <= args["steps"] <= 100:
        raise ProtocolError("invalid simulator arguments")
    return {"steps": args["steps"]}


def preview(state: dict, args: dict) -> tuple[dict, str]:
    normal = normalized_args(args)
    result = {"counter": int(state.get("counter", 0)) + normal["steps"],
              "steps": normal["steps"]}
    return result, sha256(result)


def invoke(state: dict, args: dict) -> tuple[dict, str]:
    result, result_hash = preview(state, args)
    state["counter"] = result["counter"]
    return result, result_hash
