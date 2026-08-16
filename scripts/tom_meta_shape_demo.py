"""Live demo of TOM_ATTRIBUTED_MENTAL_STATE_META_SHAPE_PREREG.md -- prints
the 5 registered predictions. Output pasted verbatim into the paired
RESULTS doc.
"""
from substrate.boot_core import CORE_SEEDS
from substrate.world_adapter import WorldAdapter

from domains.meta_shape import observe
from domains.tom_meta_shape import (
    register_character_tom_attitude, register_resident_tom_belief,
)

_EXISTING_META_SHAPES = {
    "feedback_control", "associative_recall", "competitive_inhibition",
    "prediction_minus_observation", "hierarchical_invariance_buildup",
    "global_message_passing", "selective_gating", "delayed_persistence",
    "modular_isolation", "relational_structure_match", "spatial_dynamics",
}


def fresh():
    return WorldAdapter(seeds=CORE_SEEDS + ("meta_shape_growth",))


def new_meta_shapes(inner):
    return [inner.node(n)["attrs"] for n in inner.nodes("MetaShape")
            if inner.node(n)["attrs"].get("name") not in _EXISTING_META_SHAPES]


print("=== Prediction 1: character_tom-shaped observation, alone -> residual ===")
a = fresh()
inner = a.inner
oid_ct = register_character_tom_attitude(a, belief_holder="sally", flavor="belief")
attrs = inner.node(oid_ct)["attrs"]
print("status=%s covered_by=%s signature=%s" % (attrs["status"], attrs.get("covered_by"), attrs["signature"]))

print()
print("=== Predictions 2/3: bigville observation mints one shared shape; both converge ===")
oid_bv = register_resident_tom_belief(a, target="alex", aspect="agency_attribution")
bv_attrs = inner.node(oid_bv)["attrs"]
print("bigville obs: status=%s covered_by=%s" % (bv_attrs["status"], bv_attrs.get("covered_by")))
ct_attrs_after = inner.node(oid_ct)["attrs"]
print("character_tom obs, AFTER: status=%s covered_by=%s" % (ct_attrs_after["status"], ct_attrs_after.get("covered_by")))
shapes = new_meta_shapes(inner)
print("newly-minted MetaShape(s):", shapes)

print()
print("=== Prediction 4: an unrelated observation stays residual ===")
oid_unrelated = observe(a, "Concept", {"name": "quintuple", "definition": "multiply by five"})
unrelated_attrs = inner.node(oid_unrelated)["attrs"]
print("status=%s covered_by=%s" % (unrelated_attrs["status"], unrelated_attrs.get("covered_by")))

print()
print("=== Prediction 5: reproducible on a fresh agent, different names/content ===")
a2 = fresh()
register_character_tom_attitude(a2, belief_holder="wendy", flavor="knowledge")
register_resident_tom_belief(a2, target="jo", aspect="agency_attribution")
name2 = new_meta_shapes(a2.inner)[0]["name"]
print("run 1 minted:", shapes[0]["name"])
print("run 2 minted:", name2)
print("match:", shapes[0]["name"] == name2)
