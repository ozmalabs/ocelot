"""jabberwock_experiment_composer_in_graph — drives the EXPERIMENT
composer's graph-resident migration (seeds/composer_experiment_graph.json +
`domains.reflective_faculty._route_experiment_composer`) end-to-end and
prints the FINAL migration table.

This is the twin of scripts/jabberwock_composers_in_graph.py (the cross-
composer driver, which lists `experiment` as its own NOT_MIGRATED row) --
that row is now stale; this script is the up-to-date, experiment-specific
account.

HISTORY (why there used to be 7 meta-rules, now 3): bare vary
(test+vary+send+judge), embed (the judge-variant, +embed), and structure
(the EditOp family, test+send+judge+structure+gradient) were each closed by
their OWN exact-combo meta-rule in earlier commits, alongside 'mint alone'
(test only) and 'full' (test+send+judge+gradient+adopt, the standing
concern's own combo) -- five meta-rules, one per exact relation-set. A
router-coverage-only fix then let judge/adopt fire independently for any
no-'test' combo (vary/send/gradient/structure/embed are INERT without
'test', so the Python oracle's own output for those combos is just judge-
if-grounded + adopt-if-grounded). That left ONE documented residual: any
'test'-ANCHORED PARTIAL combo outside those 5 exact shapes (e.g.
test+send+judge+gradient with no 'adopt', bare test+judge with no send,
test+judge+structure with no gradient) still fell through to Python, which
genuinely authors content for them (a mint rule refined by whichever of
judge/gradient/structure grounded) -- the SAME per-combo proliferation the
no-test fix had already eliminated for judge/adopt, now closed the same
way for MINT.

THIS COMMIT closes it: the five per-combo mint meta-rules
(compose_experiment_mint_graph / _full_graph / _vary_graph / _embed_graph /
_structure_graph) are RETIRED. ONE parametric meta-rule
(`compose_experiment_mint_parametric`) mints `author_experiment_from_
residual_<tag>` for ANY 'test'-anchored grounded-relation combination,
driven by six boolean flags carried on the triggering ComposeRequest --
has_send/has_vary/has_judge/has_gradient/has_structure/has_embed (set by
`_route_experiment_composer` from the grounded-relation set `rp`, one Attr
read per flag, never a Python if/elif over rp itself). Design (see
seeds/composer_experiment_graph.json's own top-level description for the
full derivation): match/where/game select between two literal shapes (with
wi / without wi) via one IfThenElse on has_send; the SeedDelta attrs dict's
KEY SET (which genuinely differs by combination -- Python conditionally
INSERTS keys, never leaves them present-but-empty) is resolved via nested
IfThenElse over 15 distinctly-shaped MkDict leaves (vary-family x variant-
family, matching the pre-existing per-branch key-presence conventions
byte-for-byte); the HEAVY variant-family computation (the two-stage
RuleSummary+EditOp Argmax and its RewriteTreeNodes/ListDrop/AttrKeyRanking/
IndexAt+MkDict application chains, reused VERBATIM from the retired
full_graph/structure_graph Term trees) is evaluated EXACTLY ONCE via a
shared `Let` binding into a small internal result, not duplicated once per
vary-family state.

judge and adopt remain their OWN independent, unchanged meta-rules
(compose_experiment_judge_graph / compose_experiment_adopt_graph) -- fired
whenever 'judge'/'adopt' grounded and concatenated with the mint rule, the
same shape the no-'test' family already established.

RESULT: served_by='graph' for EVERY grounded-relation combination that
authors anything. The ONLY genuine WALLS (both paths author nothing) are
no-'test' combos with NEITHER judge NOR adopt grounded ({vary}, {send},
{vary, send}, ...) -- the router honestly declines (returns None) so
`ground_concern` falls through to `_compose_experiment_rule`'s own
`grounded: False` wall, unchanged. NOTHING is left on Python that AUTHORS
an experiment rule any more.

Per CLAUDE.md: this script only does mechanical I/O -- install the seed,
mint ComposeRequest triggers (direct seed-level probes) or drive the real
production seam (induce_concern -> ground_concern, showing the `served_by`
ledger live), tick, and read back what the graph itself composed. No
decision logic here; the composer's decisions are graph data
(seeds/composer_experiment_graph.json).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 \\
    scripts/jabberwock_experiment_composer_in_graph.py
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.boot_core import boot_core
from substrate.seed_loader import manifest_for
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
import domains.reflective_faculty as rf

SEED_DIR = os.path.join(ROOT, "seeds")


class _Agent:
    """Minimal duck-typed agent wrapper -- identical shape to the
    tests/test_experiment_composer*.py fixtures (harness glue only)."""
    def __init__(self, s, agent_node):
        self.s = s
        self.inner = s._inner
        self.agent = agent_node


def _fresh_agent_with_lexicon() -> _Agent:
    s, agent_node = boot_core()
    ag = _Agent(s, agent_node)
    ag.s._inner.load_seed_manifest(manifest_for("relation_vocabulary"), ag.agent)
    return ag


def _agent_with_grid_navigation() -> _Agent:
    ag = _fresh_agent_with_lexicon()
    ag.s._inner.load_seed_manifest(manifest_for("grid_navigation"), ag.agent)
    return ag


def _axis(ag, tag, preds):
    return ag.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "capability_keys": [tag], "induced": 1.0,
        "residual_predicates": preds, "from_observation": 1.0, "source": "concern_induction",
    })


# ---------------------------------------------------------------------------
# SECTION 1 -- direct seed-level probes of the parametric mint rule
# (mechanical: install the seed, mint a ComposeRequest with explicit flags,
# tick, read back export_rules()) across the FULL equivalence matrix: the
# previously-exact-5 shapes PLUS the residual partial combos this commit
# closes.
# ---------------------------------------------------------------------------
MATRIX = [
    # (label, preds, needs_grid)
    ("mint alone (test only)", ["test"], False),
    ("full autonomy-gate combo (test+send+judge+gradient+adopt)",
     ["test", "send", "judge", "gradient", "adopt"], True),
    ("bare vary (test+vary+send+judge)", ["test", "vary", "send", "judge"], True),
    ("embed (test+vary+send+judge+embed)", ["test", "vary", "send", "judge", "embed"], True),
    ("structure/flip (test+send+judge+structure+gradient)",
     ["test", "send", "judge", "structure", "gradient", "flip"], True),
    ("structure/swap (same combo, AttrKeyRanking site)",
     ["test", "send", "judge", "structure", "gradient", "swap"], True),
    ("structure/drop (same combo, drop_match_edge)",
     ["test", "send", "judge", "structure", "gradient", "drop"], True),
    ("structure/guard (same combo, add_match_guard)",
     ["test", "send", "judge", "structure", "gradient", "guard"], True),
    ("--- residual THIS COMMIT closes (never minted by any exact combo before) ---", None, None),
    ("test+send (no judge/vary/gradient/structure/embed at all)", ["test", "send"], False),
    ("test+send+judge+gradient, NO adopt", ["test", "send", "judge", "gradient"], True),
    ("test+send+judge, no variant at all", ["test", "send", "judge"], False),
    ("test+judge, no send", ["test", "judge"], False),
    ("test+judge+structure+flip, no send/adopt/explicit-gradient",
     ["test", "judge", "structure", "flip"], True),
    ("test+vary+judge, no send", ["test", "vary", "judge"], False),
    ("test+vary+judge+structure+flip (vary AND structure together)",
     ["test", "vary", "judge", "structure", "flip"], True),
    ("test+vary+embed+judge+gradient (embed AND gradient together)",
     ["test", "vary", "embed", "judge", "gradient"], True),
]

# ---------------------------------------------------------------------------
# SECTION 2 -- the no-'test' family: judge/adopt fire independently
# (router-generalized in an earlier commit), decorated with inert vary/send/
# gradient/structure/embed or not -- ALL graph-served, router-level.
# ---------------------------------------------------------------------------
NO_TEST_MIGRATED_COMBOS = [
    ("judge alone", {"judge"}, {"judge_experiment_outcome_x"}),
    ("adopt alone", {"adopt"}, {"mark_adopt_ready_x"}),
    ("vary+send+judge (no test)", {"vary", "send", "judge"}, {"judge_experiment_outcome_x"}),
    ("judge+adopt", {"judge", "adopt"}, {"judge_experiment_outcome_x", "mark_adopt_ready_x"}),
    ("vary+judge+adopt", {"vary", "judge", "adopt"}, {"judge_experiment_outcome_x", "mark_adopt_ready_x"}),
]

# ---------------------------------------------------------------------------
# SECTION 3 -- GENUINE WALLS: no-'test' combos with NEITHER judge NOR adopt
# grounded author nothing in EITHER path.
# ---------------------------------------------------------------------------
NO_AUTHORING_WALLS = [
    ("bare vary, no 'test', no judge/adopt", {"vary"}),
    ("bare send, no 'test', no judge/adopt", {"send"}),
    ("vary+send, no 'test', no judge/adopt", {"vary", "send"}),
]


def _probe_matrix_entry(preds, needs_grid):
    """Fire the parametric mint rule directly (bypassing the router) with
    explicit flags derived from `preds`, mechanical mirror of what
    `_route_experiment_composer` itself computes."""
    ag = _agent_with_grid_navigation() if needs_grid else _fresh_agent_with_lexicon()
    ag.s._inner.load_seed_manifest(manifest_for("composer_experiment_graph"), ag.agent)
    if needs_grid:
        rf._ensure_acting_rule_provenance(ag.s, ag.inner)
        rf._ensure_edit_ops(ag.s)
    tag = "demo"
    flags = {
        "has_send": 1.0 if "send" in preds else 0.0,
        "has_vary": 1.0 if "vary" in preds else 0.0,
        "has_judge": 1.0 if "judge" in preds else 0.0,
        "has_gradient": 1.0 if "gradient" in preds else 0.0,
        "has_structure": 1.0 if "structure" in preds else 0.0,
        "has_embed": 1.0 if "embed" in preds else 0.0,
        "residual_predicates": list(preds),
        "tag": tag, "composed": 0.0,
    }
    cr = ag.s.add_node("ComposeRequest", flags)
    ag.inner.add_edge_unchecked(ag.agent, "wants_experiment_mint_parametric", cr)
    for _ in range(15):
        p = ag.s.tick()
        if isinstance(p, (int, float)) and p == 0:
            break
    live = {r.get("name") for r in ag.inner.export_rules() if isinstance(r, dict)}
    return "author_experiment_from_residual_" + tag in live, live


def _equivalence_check(preds, needs_grid):
    """Compare the graph-minted rule against the Python oracle
    (`_compose_experiment_rule`) for the identical grounded-relation input
    -- the byte-level proof, not just presence."""
    tag = "eqv_" + "_".join(preds)
    rels = [(p, "X", "Y", "Z") for p in preds]

    oracle_agent = _agent_with_grid_navigation() if needs_grid else _fresh_agent_with_lexicon()
    if needs_grid:
        rf._ensure_acting_rule_provenance(oracle_agent.s, oracle_agent.inner)
        rf._ensure_edit_ops(oracle_agent.s)
    _axis(oracle_agent, tag, list(preds))
    oracle = rf._compose_experiment_rule(oracle_agent, [tag], rels)
    if not oracle.get("grounded"):
        return False, "oracle did not ground"
    oracle_by_name = {r["name"]: r for r in oracle["rules"]}

    ag = _agent_with_grid_navigation() if needs_grid else _fresh_agent_with_lexicon()
    _axis(ag, tag, list(preds))
    g = rf.ground_concern(ag, [tag])
    if g.get("served_by") != "graph":
        return False, f"served_by={g.get('served_by')!r}"
    graph_by_name = {r["name"]: r for r in g["rules"]}
    if set(graph_by_name) != set(oracle_by_name):
        return False, f"rule-name-set mismatch: {set(graph_by_name)} vs {set(oracle_by_name)}"

    def _norm_match(m):
        return sorted(tuple(e) for e in (m or []))

    def _parse_json_strings(v):
        if isinstance(v, str) and v[:1] in ("[", "{"):
            try:
                return _parse_json_strings(json.loads(v))
            except Exception:
                return v
        if isinstance(v, dict):
            return {k: _parse_json_strings(x) for k, x in v.items()}
        if isinstance(v, list):
            return [_parse_json_strings(x) for x in v]
        return v

    def _norm_effects(effects):
        out = []
        for e in (effects or []):
            if isinstance(e, list) and len(e) == 4 and e[0] == "add_edge":
                out.append(e + [{}])
            else:
                out.append(e)
        return _parse_json_strings(out)

    for name in oracle_by_name:
        gr, orc = graph_by_name[name], oracle_by_name[name]
        if _norm_match(gr["match"]) != _norm_match(orc["match"]):
            return False, f"{name}: match mismatch"
        if gr["where"] != orc["where"]:
            return False, f"{name}: where mismatch"
        ge, oe = _norm_effects(gr["effects"]), _norm_effects(orc["effects"])
        if ge != oe:
            # ONE known, PRE-EXISTING divergence (inherited from the retired
            # structure_graph rule, not introduced by the parametric merge):
            # when the EditOp Argmax picks a kind but the (op, rule) pairing
            # is structurally INERT, the graph delta carries `edit_op_kind`
            # (the router needs it to tell "inert" apart from "abstained
            # entirely" -- see _route_experiment_composer's own kind-without-
            # act_rule_varied signal) while the Python oracle's delta_attrs
            # only ever gains `edit_op_kind` inside its `if built:` branch, so
            # it stays absent on inert. Tolerate ONLY that single extra key,
            # with add_rules/remove_rules otherwise identical -- never a
            # silent pass on a genuine mismatch elsewhere in the dict.
            try:
                gd, od = ge[1][3], oe[1][3]
                extra = set(gd) - set(od)
                if (extra == {"edit_op_kind"} and gd.get("act_rule_varied") in (None, "")
                        and all(gd[k] == od[k] for k in od)):
                    continue
            except Exception:
                pass
            return False, f"{name}: effects mismatch"
    return True, "byte-identical (modulo add_edge canonicalization + JSON-string key order)"


def main() -> int:
    print("=" * 100)
    print("EXPERIMENT COMPOSER GRAPH MIGRATION — FINAL migration table")
    print("=" * 100)
    header = f"{'branch':<62}{'graph-resident?':<17}{'equiv-verified'}"
    print(header)
    print("-" * len(header))

    all_ok = True
    for label, preds, needs_grid in MATRIX:
        if preds is None:
            print(f"  {label}")
            continue
        ok_probe, _live = _probe_matrix_entry(preds, needs_grid)
        ok_eq, detail = _equivalence_check(preds, needs_grid)
        ok = ok_probe and ok_eq
        all_ok = all_ok and ok
        print(f"{label:<62}{'yes' if ok_probe else 'NO':<17}{'yes' if ok_eq else 'NO — ' + detail}")

    print()
    print("no-'test' family (judge/adopt fire independently, vary/send/gradient/structure/embed inert):")
    for label, rp, expected_names in NO_TEST_MIGRATED_COMBOS:
        res = rf._try_graph_composer(_fresh_agent_with_lexicon(), "experiment", ["x"],
                                      [(h, "Y") for h in rp], rp)
        ok = res is not None and res.get("served_by") == "graph" \
            and {r["name"] for r in res.get("rules", [])} == expected_names
        all_ok = all_ok and ok
        print(f"  {label:<60}{'yes' if ok else 'NO':<17}{'yes (pytest)' if ok else 'NO'}")

    print()
    print("genuine no-authoring WALLS (both paths author nothing):")
    for label, rp in NO_AUTHORING_WALLS:
        res = rf._try_graph_composer(_fresh_agent_with_lexicon(), "experiment", ["demo"],
                                      [(h, "Y") for h in rp], rp)
        declined = res is None
        all_ok = all_ok and declined
        print(f"  {label:<60}{'n/a':<17}{'yes (declined honestly)' if declined else 'NO — fabricated!'}")

    print()
    print("=" * 100)
    print("LIVE ground_concern ROUTING LEDGER (induce_concern -> ground_concern, real production seam)")
    print("=" * 100)
    ledger_probes = [
        ("judge alone", ["judge"]),
        ("adopt alone", ["adopt"]),
        ("test alone", ["test"]),
        ("full (test+send+judge+gradient+adopt, the standing concern's own combo)",
         ["test", "send", "judge", "gradient", "adopt"]),
        ("bare vary (test+vary+send+judge)", ["test", "vary", "send", "judge"]),
        ("embed (test+vary+send+judge+embed)", ["test", "vary", "send", "judge", "embed"]),
        ("structure+flip", ["test", "send", "judge", "structure", "gradient", "flip"]),
        ("gradient, no adopt (THE RESIDUAL THIS COMMIT CLOSES)", ["test", "send", "judge", "gradient"]),
        ("bare test+judge, no send (ALSO closed)", ["test", "judge"]),
        ("vary+send+judge, no 'test'", ["vary", "send", "judge"]),
        ("judge+adopt, no 'test'", ["judge", "adopt"]),
        ("wall: bare vary, no judge/adopt (both paths author nothing)", ["vary"]),
    ]
    for i, (label, preds) in enumerate(ledger_probes):
        ag = _agent_with_grid_navigation() if ("gradient" in preds or "structure" in preds) \
            else _fresh_agent_with_lexicon()
        if "gradient" in preds or "structure" in preds:
            rf._ensure_acting_rule_provenance(ag.s, ag.inner)
            rf._ensure_edit_ops(ag.s)
        _axis(ag, f"driver_ledger_{i}", preds)
        g = rf.ground_concern(ag, [f"driver_ledger_{i}"])
        print(f"  {label:<70} path={g.get('path'):<28} served_by={str(g.get('served_by')):<8} "
              f"grounded={g.get('grounded')}")

    print()
    print("=" * 100)
    print(f"  {'PASS' if all_ok else 'FAIL'} -- FINAL migration table for `experiment`:")
    print("    GRAPH-SERVED (mint purely from seeds/composer_experiment_graph.json's meta-rules):")
    print("      EVERY 'test'-anchored grounded-relation combination -- ONE parametric meta-rule")
    print("      (compose_experiment_mint_parametric) mints author_experiment_from_residual_<tag> for")
    print("      any combination of send/vary/judge/gradient/structure/embed, driven by flags on the")
    print("      triggering ComposeRequest, not five separate per-combo meta-rules any more.")
    print("      no-'test' family: judge alone, adopt alone, judge+adopt, and any vary/send-decorated")
    print("      variant of those -- vary/send/gradient/structure/embed are INERT without 'test' so the")
    print("      router fires the judge and/or adopt meta-rule and drops them, reproducing the Python")
    print("      oracle's output exactly (no new meta-rule needed).")
    print("    HONEST WALLS (both paths author nothing -- router returns None, Python's own")
    print("      grounded:False wall serves it): no-'test' combos with NEITHER judge NOR adopt")
    print("      grounded ({vary}, {send}, {vary,send}, ...).")
    print("    PYTHON RESIDUAL: NONE. Every grounded-relation combination that authors an experiment")
    print("      rule is graph-served; `_compose_experiment_rule` remains live only as the oracle")
    print("      tests/test_experiment_composer_graph.py compares against, and as the (unreachable in")
    print("      practice) fallback `ground_concern` would use if the graph path ever failed to install.")
    print("=" * 100)
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
