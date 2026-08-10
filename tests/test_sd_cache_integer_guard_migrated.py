"""Static boundary gate for the SD report-cache fast path.

The cognitive core is integer/symbolic. Physical and sensor interfaces may
carry floats, but SD scheduling, identity and cache invalidation must not
introduce floating-point state or arithmetic.
"""
from pathlib import Path
import json
import re

from substrate.boot_core import boot_core


ROOT = Path(__file__).resolve().parents[1]


def _between(text: str, start: str, end: str) -> str:
    return text.split(start, 1)[1].split(end, 1)[0]


def test_sd_report_cache_control_path_is_integer_native():
    term = (ROOT / "runners/dsl/src/term.rs").read_text(encoding="utf-8")
    cache = _between(term, "struct SdCacheKey", "/// Concept registry")

    forbidden = re.compile(r"\bf(?:32|64)\b|\bas\s+f(?:32|64)\b")
    assert not forbidden.search(cache), "SD cache control introduced floating point"
    assert "u64" in cache
    assert "serde_json" not in cache, "cache identity must not cross a float-capable JSON boundary"


def test_codebook_change_between_effects_invalidates_the_report():
    """Memoization cannot turn sequential graph effects into a stale view."""
    s, agent = boot_core()
    native = s._inner
    native.add_production({
        "src": {"type": "Agent", "var": "agent"},
        "edge_type": "has_sd_cache_probe",
        "tgt": {"type": "SdCacheProbe", "var": "probe"},
        "provenance": "test:sd_cache_invalidation",
    })
    signature = [["step", "left"], ["step", "right"]]
    probe = s.add_node("SdCacheProbe", {"signature": signature, "status": "pending"})
    s.add_edge(agent, "has_sd_cache_probe", probe)

    def covered_count():
        return {"__term__": {
            "type": "ShapeDecode",
            "goal": {"type": "Attr", "node": {"type": "Var", "name": "probe"},
                     "key": "signature"},
            "field": "covered_count",
        }}

    native.add_rule({
        "name": "sd_cache_invalidation_probe",
        "match_type": "SdCacheProbe",
        "match": [["agent", "has_sd_cache_probe", "probe"]],
        "where": {"type": "Eq",
                  "a": {"type": "Attr", "node": {"type": "Var", "name": "probe"},
                        "key": "status"},
                  "b": {"type": "Lit", "value": "pending"}},
        "effects": [
            ["set_attr", "probe", "covered_before", covered_count()],
            ["add_node", "part", "ShapeSignature", {
                "name": "new_part", "kind": "faculty", "faculty": "new_part",
                "signature": json.dumps(signature),
            }],
            ["set_attr", "probe", "covered_after", covered_count()],
            ["set_attr", "probe", "status", "done"],
        ],
    })

    native.run_rules()
    attrs = s.node(probe)["attrs"]
    assert attrs["covered_before"] is None
    assert attrs["covered_after"] == len(signature)
