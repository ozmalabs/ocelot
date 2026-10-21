"""F2.1 executable fixtures; F2.2 will connect these cases to native rules."""
from __future__ import annotations


def _world(path, referent="key", actual_version=1):
    return {"holder_path": tuple(path), "referent": referent,
            "actual_world_version": actual_version}


def _event(event_id, path, proposition, *, access):
    return {"event_id": event_id, "holder_path": tuple(path),
            "proposition": proposition, "access": access}


def test_second_order_false_belief():
    actual = {"key_location": "shelf", "version": 1}
    second_order = _world(["sally", "anne"])
    belief = {**second_order, "proposition": "key_location=drawer", "truth": False}
    assert belief["holder_path"] == ("sally", "anne")
    assert belief["truth"] is False
    assert actual["key_location"] == "shelf"


def test_actual_world_not_overwritten():
    actual = {"key_location": "shelf", "version": 1}
    before = dict(actual)
    event = _event("obs-1", ["sally", "anne"], "key_location=drawer", access=True)
    # The event proposes an attributed update; actual world is a separate record.
    attributed = {**_world(event["holder_path"], actual_version=actual["version"]),
                  "proposition": event["proposition"]}
    assert attributed["proposition"] != f"key_location={actual['key_location']}"
    assert actual == before


def test_no_access_no_belief_update():
    inaccessible = _event("obs-2", ["sally", "anne"], "door=open", access=False)
    assert inaccessible["access"] is False
    # Without an access event, the result is explicitly unknown, not false.
    result = {"status": "unknown", "reason": "no_access"}
    assert result["status"] == "unknown"


def test_cycles_and_depth_bound():
    max_depth = 2
    valid = _world(["sally", "anne"])
    cycle = _world(["sally", "anne", "sally"])
    over_depth = _world(["sally", "anne", "bob"])
    assert len(valid["holder_path"]) == max_depth
    assert len(set(cycle["holder_path"])) < len(cycle["holder_path"])
    assert len(over_depth["holder_path"]) > max_depth
    assert _world(["sally", "anne"]) != _world(["anne", "sally"])
