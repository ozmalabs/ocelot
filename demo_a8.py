"""A8 live demonstration -- through the REAL loaded seed, fired via
rf.ground_concern (the genuine production dispatch seam), not a standalone
Term evaluation. See MAC_FAC_A8_PREREG.md / MAC_FAC_A8_RESULTS.md."""
import json
import sys
sys.path.insert(0, ".")
from domains.engine_provenance import engine_preamble
engine_preamble(strict=False)

from substrate.boot_core import boot_core
from substrate.seed_loader import manifest_for
import domains.reflective_faculty as rf


class _Agent:
    def __init__(self, s, agent_node):
        self.s = s
        self.inner = s._inner
        self.agent = agent_node


def _fresh_agent_with_lexicon():
    s, agent_node = boot_core()
    ag = _Agent(s, agent_node)
    ag.s._inner.load_seed_manifest(manifest_for("relation_vocabulary"), ag.agent)
    return ag


def _agent_with_grid_navigation():
    ag = _fresh_agent_with_lexicon()
    ag.s._inner.load_seed_manifest(manifest_for("grid_navigation"), ag.agent)
    ag.s.add_node("SeedSummary", {"seed_id": "grid_navigation",
                                  "keywords_text": "grid navigation gradient hop descend row col",
                                  "skippable": 1.0})
    return ag


def _axis(ag, tag, preds):
    return ag.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "capability_keys": [tag], "induced": 1.0,
        "residual_predicates": preds, "from_observation": 1.0, "source": "concern_induction",
    })


print("=" * 70)
print("CLASS A: drop_match_edge wins the unfiltered keyword Argmax (score 1,")
print("the only nonzero score) but is structurally INAPPLICABLE to the")
print("picked rule hop_descend_gradient (1 match edge).")
print("=" * 70)
ag = _agent_with_grid_navigation()
tag = "demo_classA_drop"
_axis(ag, tag, ["test", "send", "judge", "structure", "gradient", "drop"])
res = rf.ground_concern(ag, [tag])
sv = res.get("structural_variant")
print("served_by:", res.get("served_by"))
print("structural_variant:", json.dumps(sv, default=str))
assert res.get("served_by") == "graph"
assert sv is not None and sv.get("built") is False
assert sv.get("kind") is None, "drop_match_edge must never be named -- filtered before scoring"
assert "abstained" in sv.get("wall", "")
assert "drop_match_edge" not in sv.get("wall", "")
print("[Class A] PASS -- inapplicable op filtered out, honest abstain, never a wasted attempt")

# confirm the RuleSummary carries the expected applicability flags
picked_rs = next(n for n in ag.s.nodes("RuleSummary")
                  if ag.s.node(n)["attrs"].get("name") == "hop_descend_gradient")
at = ag.s.node(picked_rs)["attrs"]
flags = {k: at.get(k) for k in (
    "applicable_flip_comparison", "applicable_swap_term_leaf",
    "applicable_drop_match_edge", "applicable_add_match_guard")}
print("hop_descend_gradient RuleSummary applicability flags:", flags)
assert flags["applicable_drop_match_edge"] == 0.0
assert flags["applicable_flip_comparison"] == 1.0
assert flags["applicable_swap_term_leaf"] == 1.0
assert flags["applicable_add_match_guard"] == 1.0
print("[Class A] PASS -- precompute stamped the correct four flags on the picked RuleSummary")

print()
print("=" * 70)
print("CLASS B (x3): keyword-best op is ALSO applicable -- must stay")
print("byte-identical before/after the fix (flip / swap / guard).")
print("=" * 70)
for cue, expected_kind in (("flip", "flip_comparison"),
                            ("swap", "swap_term_leaf"),
                            ("guard", "add_match_guard")):
    ag2 = _agent_with_grid_navigation()
    tag2 = "demo_classB_" + cue
    _axis(ag2, tag2, ["test", "send", "judge", "structure", "gradient", cue])
    res2 = rf.ground_concern(ag2, [tag2])
    sv2 = res2.get("structural_variant")
    print(f"[Class B: {cue}] structural_variant:", json.dumps(sv2, default=str))
    assert sv2 is not None and sv2.get("built") is True
    assert sv2.get("kind") == expected_kind
    print(f"[Class B: {cue}] PASS -- unchanged, applicable+keyword-best op still wins")

print()
print("=" * 70)
print("NEGATIVE CONTROL: no grid_navigation loaded at all -- the OUTER")
print("(apick/RuleSummary) Argmax abstains before epick is ever reached.")
print("=" * 70)
ag3 = _fresh_agent_with_lexicon()
tag3 = "demo_negctrl"
_axis(ag3, tag3, ["test", "send", "judge", "structure", "flip"])
res3 = rf.ground_concern(ag3, [tag3])
sv3 = res3.get("structural_variant")
print("structural_variant:", json.dumps(sv3, default=str))
assert sv3 is not None and sv3.get("built") is False
assert "wall" in sv3
print("[Negative control] PASS -- honest abstain, outer pick never reaches epick")

print()
print("ALL A8 LIVE DEMONSTRATIONS PASSED")
