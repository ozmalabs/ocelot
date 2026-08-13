"""Live Class-A/Class-B demonstration for A9, through the REAL loaded
seed's REAL compose_experiment_mint_parametric rule (fired via
rf.ground_concern, the genuine production dispatch seam). Mirrors
SEED_PICK_STRUCTURAL_FALLBACK_RESULTS.md's own methodology exactly (real
authored rule's own extracted Term, evaluated directly against a real
CapabilityAxis) -- required because a KNOWN, pre-existing, unrelated engine
gotcha (the second-order minted rule not reliably re-firing via a second
run_rules() pass in this harness -- see test_vary_bare_graph_rule_fires_
and_picks_skip_seeds, red identically before this rung's edit) blocks the
full "second rule also fires" path.
"""
import json
import sys

sys.path.insert(0, ".")
sys.path.insert(0, "runners/dsl/python")

from substrate.boot_core import boot_core
from substrate.seed_loader import manifest_for
from substrate.boot_all import _seed_keywords_text
import domains.reflective_faculty as rf
from domains import seed_signature as ssig


class _Agent:
    def __init__(self, s, agent_node):
        self.s = s
        self.inner = s._inner
        self.agent = agent_node


def fresh_agent():
    s, agent_node = boot_core()
    ag = _Agent(s, agent_node)
    ag.s._inner.load_seed_manifest(manifest_for("relation_vocabulary"), ag.agent)
    return ag


def axis(ag, tag, preds):
    return ag.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "capability_keys": [tag], "induced": 1.0,
        "residual_predicates": preds, "from_observation": 1.0, "source": "concern_induction",
    })


def find_delta_term(rule, key):
    """Locate the {'__term__': ...} payload for SeedDelta attr `key` inside
    a minted rule's effects -- mirrors test_seed_signature_structural_
    fallback.py's own _extract_skip_id_term, generalised to either key."""
    for e in rule.get("effects", []):
        if isinstance(e, list) and len(e) == 4 and e[0] == "add_node" and e[2] == "SeedDelta":
            v = e[3].get(key)
            if isinstance(v, dict) and "__term__" in v:
                return v["__term__"]
    return None


def get_mint_rule(ag, tag):
    res = rf.ground_concern(ag, [tag])
    assert res.get("served_by") == "graph", res
    mint = next(r for r in res["rules"] if r["name"].startswith("author_experiment_from_residual_"))
    return mint


REAL_SEED = "investigation_loop"
CLASS_A_WORD = "has_plan"     # SEED_PICK_STRUCTURAL_FALLBACK_RESULTS.md's own measured probe
CLASS_B_WORD = "committed"    # from _CLASS_B_PROBES for seed 'abandon_on_stuck'
CLASS_B_SEED = "abandon_on_stuck"


def real_kw_and_sig(seed_id):
    manifest = manifest_for(seed_id)
    kw = _seed_keywords_text(seed_id, manifest)
    return kw, manifest


def main():
    print("=== A9 live demonstration (through the REAL loaded, edited seed) ===")

    # ---- sanity: probes are genuinely disjoint on this file's own data ----
    kw_a, manifest_a = real_kw_and_sig(REAL_SEED)
    assert CLASS_A_WORD not in kw_a, (REAL_SEED, kw_a)
    kw_b, manifest_b = real_kw_and_sig(CLASS_B_SEED)
    assert CLASS_B_WORD in kw_b, (CLASS_B_SEED, kw_b)
    print(f"[setup] real keywords_text({REAL_SEED!r}) lacks {CLASS_A_WORD!r}: OK")
    print(f"[setup] real keywords_text({CLASS_B_SEED!r}) contains {CLASS_B_WORD!r}: OK")

    # ================= CLASS A: primary abstains, fallback recovers =======
    ag = fresh_agent()
    tag = "a9_classA"
    # candidate pool: the REAL target seed + one distractor real seed, both
    # skippable, both with their REAL boot-time keywords_text.
    ag.s.add_node("SeedSummary", {"seed_id": REAL_SEED, "keywords_text": kw_a, "skippable": 1.0})
    kw_distractor, _ = real_kw_and_sig("grid_navigation")
    ag.s.add_node("SeedSummary", {"seed_id": "grid_navigation", "keywords_text": kw_distractor, "skippable": 1.0})
    n_touched = ssig.ensure_seed_signature(ag.s)
    print(f"[Class A setup] ensure_seed_signature minted {n_touched} where_signature_json attrs")
    for n in ag.s.nodes("SeedSummary"):
        at = ag.s.node(n)["attrs"]
        if at.get("seed_id") == REAL_SEED:
            sig_json = at.get("where_signature_json") or ""
            assert CLASS_A_WORD in sig_json, f"{REAL_SEED}'s real where_signature_json must contain {CLASS_A_WORD!r}"
            print(f"[Class A setup] {REAL_SEED}'s where_signature_json genuinely contains {CLASS_A_WORD!r}: OK")

    axis(ag, tag, ["test", "vary", "send", "judge", CLASS_A_WORD])
    mint = get_mint_rule(ag, tag)
    print(f"[Class A] real minted rule: {mint['name']!r} (from the REAL, live, edited compose_experiment_mint_parametric)")

    for key in ("skip_seed_id", "skip_seeds"):
        term = find_delta_term(mint, key)
        assert term is not None, f"minted rule's SeedDelta must carry a {key} __term__"
        probe_axis = axis(ag, f"{tag}_probe_{key}", [CLASS_A_WORD])
        picked = ag.inner.evaluate(term, {"axis": probe_axis})
        if key == "skip_seeds":
            picked_seed = json.loads(picked)[0] if picked and picked != "[]" else None
        else:
            picked_seed = picked or None
        print(f"[Class A] {key} Term (extracted from the REAL rule) picked: {picked_seed!r}")
        assert picked_seed == REAL_SEED, (key, picked_seed, REAL_SEED)
    print("[Class A] PASS -- structural fallback recovered the real target seed on BOTH skip_seeds and skip_seed_id, "
          "via the REAL rule the REAL live compose_experiment_mint_parametric rule authored.")

    # ================= CLASS B: primary already matches, unchanged ========
    ag2 = fresh_agent()
    tag2 = "a9_classB"
    ag2.s.add_node("SeedSummary", {"seed_id": CLASS_B_SEED, "keywords_text": kw_b, "skippable": 1.0})
    kw_distractor2, _ = real_kw_and_sig("grid_navigation")
    ag2.s.add_node("SeedSummary", {"seed_id": "grid_navigation", "keywords_text": kw_distractor2, "skippable": 1.0})
    # deliberately do NOT call ensure_seed_signature -- Class B must not need it
    axis(ag2, tag2, ["test", "vary", "send", "judge", CLASS_B_WORD])
    mint2 = get_mint_rule(ag2, tag2)
    for key in ("skip_seed_id", "skip_seeds"):
        term = find_delta_term(mint2, key)
        probe_axis = axis(ag2, f"{tag2}_probe_{key}", [CLASS_B_WORD])
        picked = ag2.inner.evaluate(term, {"axis": probe_axis})
        picked_seed = (json.loads(picked)[0] if key == "skip_seeds" and picked and picked != "[]" else (picked or None))
        print(f"[Class B] {key} Term picked: {picked_seed!r} (where_signature_json NEVER primed)")
        assert picked_seed == CLASS_B_SEED, (key, picked_seed, CLASS_B_SEED)
    print("[Class B] PASS -- primary keywords_text pick alone recovered the seed; fallback never needed "
          "(where_signature_json was never even minted for this agent).")

    print("=== A9 demonstration complete: GO on both copies (skip_seeds, skip_seed_id) ===")


if __name__ == "__main__":
    main()
