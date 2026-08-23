"""STAGE A'S REFUSAL — gate for `stage_a::rule_is_derivable`.

`STAGE_A_RESULTS.md` §5f falsified Stage A on `mo_flood`: its proposals are
write-disjoint and read-dependent, `conflicts()` compares write sets, and no
refinement of a write-set relation can see a read-write dependency. The remedy
§5f reached for was per-proposal READ sets, which means instrumenting every graph
read during effect evaluation.

§5g takes the other branch: Stage A does not have to DECIDE those rules, only to
REFUSE them, and refusing is free because `RewriteRule::derive_access` already
computes a static per-rule read set and write set for the batch-apply slice. A
rule whose two sets intersect is refused; everything else is still speculated on.

These tests pin the three things that can silently go wrong with that:

  * the falsifier stays closed;
  * a probe that MEANS to exercise Stage A actually does (the trap below);
  * cross-rule dependence is not a hazard, so the refusal need not cover it.
"""
from __future__ import annotations

import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
pytest.importorskip("substrate_rs")
import sys

sys.path.insert(0, str(ROOT / "scripts"))
import substrate_rs._native as native            # noqa: E402
from substrate.boot_core import boot_core        # noqa: E402

L = lambda v: {"type": "Lit", "value": v}                                    # noqa: E731
A = lambda var, key: {"type": "Attr", "node": {"type": "Var", "name": var}, "key": key}  # noqa: E731


def _run(seed, *, stage_a, n_items=25, hub_attrs=None):
    """Install `seed`, hang `n_items` Items off one Hub, settle, report."""
    native.stage_a_enable(bool(stage_a))
    native.stage_a_reset()
    try:
        s, _ag = boot_core()
        s.add_production({"provenance": "test:stage_a_refusal",
                          "src": {"type": "Hub", "var": "h"},
                          "edge_type": "holds",
                          "tgt": {"type": "Item", "var": "i"}})
        s._inner.load_seed_manifest(seed)
        hub = s.add_node("Hub", dict(hub_attrs or {"armed": 1.0}))
        for _ in range(n_items):
            it = s.add_node("Item", {"k": 0.0, "done": 0.0})
            s.add_edge(hub, "holds", it)
        steps = s.tick(100_000)
        got = {
            "k": sum(1 for c in s.nodes("Item")
                     if float(s.node(c)["attrs"].get("k", 0.0)) > 0.5),
            "done": sum(1 for c in s.nodes("Item")
                        if float(s.node(c)["attrs"].get("done", 0.0)) > 0.5),
            "steps": steps,
        }
        return got, native.stage_a_stats()
    finally:
        native.stage_a_enable(False)


# A depends on the hub's attr; B depends on what A wrote. NEITHER rule's own read
# set meets its own write set, so both are genuinely derivable -- which is what
# makes this a real test of cross-rule dependence rather than of the refusal.
_CROSS_RULE = {
    "id": "stage_a_xrule", "version": "1.0.0", "depends_on": [],
    "rules": [
        {"name": "xr_a", "match": [["h", "holds", "it"]],
         "where": {"type": "Gt", "a": A("h", "armed"), "b": L(0.5)},
         "effects": [["set_attr_if_different", "it", "k", 1.0]]},
        {"name": "xr_b", "match": [["h", "holds", "it"]],
         "where": {"type": "Gt", "a": A("it", "k"), "b": L(0.5)},
         "effects": [["set_attr_if_different", "it", "done", 1.0]]},
    ],
}

# The same dependency written the natural way, with idempotence guards. Both
# rules now read the key they write, so BOTH are refused.
_GUARDED = {
    "id": "stage_a_guarded", "version": "1.0.0", "depends_on": [],
    "rules": [
        {"name": "g_a", "match": [["h", "holds", "it"]],
         "where": {"type": "Lt", "a": A("it", "k"), "b": L(0.5)},
         "effects": [["set_attr", "it", "k", {"__term__": L(1.0)}]]},
        {"name": "g_b", "match": [["h", "holds", "it"]],
         "where": {"type": "And", "items": [
             {"type": "Gt", "a": A("it", "k"), "b": L(0.5)},
             {"type": "Lt", "a": A("it", "done"), "b": L(0.5)}]},
         "effects": [["set_attr", "it", "done", {"__term__": L(1.0)}]]},
    ],
}


def test_a_rule_that_reads_the_key_it_writes_is_refused():
    """The predicate, observed through the engine's own counter.

    Every rule in `_GUARDED` guards on the key it writes -- the ordinary way to
    make a rule idempotent -- so Stage A must decline all of them and speculate
    on none."""
    _got, stats = _run(_GUARDED, stage_a=True)
    assert stats["excluded_drains"] > 0, "nothing was refused"
    assert stats["proposals"] == 0, (
        f"{stats['proposals']} proposals built for rules that read what they "
        f"write -- the refusal is not firing")


def test_a_probe_that_means_to_exercise_stage_a_must_actually_do_so():
    """THE TRAP, pinned. It cost a wrong conclusion once and would again.

    The first cross-rule probe used idempotence guards, so BOTH its rules were
    refused, Stage A never ran, and the two modes agreed VACUOUSLY. An agreement
    measured with `proposals == 0` says nothing whatever about Stage A.

    So the cross-rule fixture must be shown to be live before its agreement is
    allowed to mean anything."""
    _got, stats = _run(_CROSS_RULE, stage_a=True)
    assert stats["proposals"] > 0, (
        "the cross-rule fixture built no proposals -- it is inert, and any "
        "both-modes agreement it reports is vacuous")


def test_cross_rule_dependence_is_not_a_stage_a_hazard():
    """B reads exactly what A writes, and the modes must still agree.

    A drain is ONE rule (`attempt_one_rule(&mut self, rule_idx)`), and Stage A's
    staging is scoped inside it, so B's drain begins after A's has committed.
    Stage A removes INTRA-drain, SAME-rule visibility and nothing else -- which
    is why the refusal is a per-rule predicate and does not need to reason about
    pairs."""
    off, off_stats = _run(_CROSS_RULE, stage_a=False)
    on, on_stats = _run(_CROSS_RULE, stage_a=True)
    assert on_stats["proposals"] > 0, "fixture inert; see the trap test above"
    assert off_stats["proposals"] == 0, "Stage A ran with the flag off"
    assert on == off, (
        f"cross-rule dependence diverged under Stage A: {on} vs {off}")
    assert on["k"] == on["done"] == 25, (
        f"the dependency did not propagate at all: {on}")


# §5c's minimal FOLD reproduction. The `seen` guard means each binding fires
# exactly once, so there is no later pass for the fixpoint to accumulate in --
# which is why the under-count never heals itself.
_FOLD = {
    "id": "stage_a_fold", "version": "1.0.0", "depends_on": [],
    "rules": [
        {"name": "fold_count", "match": [["c", "counts", "it"]],
         "where": {"type": "Lt", "a": A("it", "seen"), "b": L(0.5)},
         "effects": [
             ["set_attr", "it", "seen", {"__term__": L(1.0)}],
             ["set_attr", "c", "total",
              {"__term__": {"type": "Plus", "items": [A("c", "total"), L(1.0)]}}],
         ]},
    ],
}


def _fold_total(stage_a, n):
    native.stage_a_enable(bool(stage_a))
    native.stage_a_reset()
    try:
        s, _ag = boot_core()
        s.add_production({"provenance": "test:stage_a_fold",
                          "src": {"type": "Counter", "var": "c"},
                          "edge_type": "counts",
                          "tgt": {"type": "Item", "var": "i"}})
        s._inner.load_seed_manifest(_FOLD)
        c = s.add_node("Counter", {"total": 0.0})
        for _ in range(n):
            it = s.add_node("Item", {"seen": 0.0})
            s.add_edge(c, "counts", it)
        s.tick(100_000)
        return float(s.node(c)["attrs"].get("total", 0.0))
    finally:
        native.stage_a_enable(False)


@pytest.mark.parametrize("n", [5, 20, 50])
def test_a_fold_over_bindings_does_not_silently_under_count(n):
    """§5c's shape — the half of this fix with NO visible symptom.

    Propagation had a falsifier: the parallax suite went red. Fold does not.
    §5c: "Stage A silently under-counts every fold-over-bindings rule, and
    `steps` is identical, so nothing in the iteration profile signals it." It
    recorded ON total = 1.0 at every size against an OFF total of n.

    The rule reads `total` and writes `total`, so the refusal must decline it and
    the count must come back. Asserted against `n` directly rather than against
    the OFF run, so a fixture that silently stopped counting in BOTH modes
    could not pass."""
    assert _fold_total(False, n) == float(n), "the OFF baseline is itself wrong"
    assert _fold_total(True, n) == float(n), (
        f"Stage A under-counted a fold: got {_fold_total(True, n)}, expected {n} "
        f"(§5c's silent divergence has reopened)")


def test_the_falsifier_stays_closed():
    """§5f's own reproduction, as a standing gate.

    `mo_flood` is the rule that falsified Stage A, and it is refused by the
    predicate. This asserts the observable §5f used -- the parallax efference
    suite passing in BOTH modes -- rather than re-deriving the mechanism."""
    import subprocess
    import os

    target = "tests/test_parallax_efference_migrated.py"
    out = {}
    for mode, env_on in (("off", False), ("on", True)):
        env = dict(os.environ)
        env.pop("OZMA_STAGE_A", None)
        if env_on:
            env["OZMA_STAGE_A"] = "1"
        r = subprocess.run(
            [sys.executable, "-m", "pytest", target, "-q", "--tb=no", "-p", "no:randomly"],
            cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=1800)
        out[mode] = r.returncode
    assert out["off"] == 0, "the falsifier fixture is red with Stage A OFF"
    assert out["on"] == 0, (
        "STAGE A FALSIFIER HAS REOPENED: test_parallax_efference_migrated fails "
        "with OZMA_STAGE_A=1 (§5f's reproduction)")
