"""Gates for META_SHAPE_ARITY_AND_KEY_SEPARATOR_FIXES (2026-08-12).

TWO defects, both reported `[derived, not run]` by
`docs/research/engine_substrate/SHAPE_TYPE_VOCABULARY_SPIKE.md` and both
reproduced live before being fixed.

**Bug 1 (spike §3.3.1) — meta-shape recognition was ARITY-EXACT.**
`seeds/meta_shape_growth.json`'s rung-1 guard was
`Covers(pattern=cms.signature, instance=obs.signature)`. Both operands are
`Value::List`, so the test landed on `covers_value`'s `Tuple | List` arm, which
requires `pt.len() == it.len()`. A minted k-relation `MetaShape` could therefore
only ever cover an observation with EXACTLY k relations: the same item carrying
one extra attribute missed rung 1 and fell all the way through to `residual`.
The fix is a new Rust Term, `CoversOpen` (`runners/dsl/src/term.rs`,
`covers_open_value`), which reads the OUTER container as a relation SET
(superset-tolerant, injectively matched) while comparing each relation with
`covers_value` UNCHANGED — so a relation stays positional and WILD still
matches anything. `Covers` itself is untouched; only the six `msg_*` guards
moved.

**Bug 2 (spike §7.2) — the `CapabilityAxis` key separator was ambiguous.**
`"induced_" + "_".join(sorted(preds))` uses `_` both BETWEEN predicates and
INSIDE them, so `["a_b","c"]` and `["a","b_c"]` produce one key — and a
collision routes a novel observation to `sd_dedup_existing`
(`status="recognized_duplicate"`). The fix percent-escapes the separator and
the escape introducer, which is injective and leaves every key the tree
currently produces byte-identical.
"""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")

WILD = "·?·"


def _boot_meta_shape_grain():
    """A fresh agent holding ONLY the meta-shape grain's two seeds."""
    from substrate.world_adapter import WorldAdapter
    from substrate.seed_loader import manifest_for

    wa = WorldAdapter()
    for seed in ("shape_vocabulary", "meta_shape_growth"):
        wa.inner.load_seed_manifest(manifest_for(seed), wa.agent)
    return wa


def _last_observation(wa):
    return wa.s.node(list(wa.s.nodes("ShapeObservation"))[-1])["attrs"]


def _mint_the_trade_record_shape(wa):
    """Two same-arity observations recur -> `MetaShapeMint` mints ONE shape."""
    from domains.meta_shape import observe

    observe(wa, "TradeRecord", {"buyer": "alice", "seller": "bob", "lot": "7"})
    observe(wa, "TradeRecord", {"buyer": "carol", "seller": "dave", "lot": "9"})
    minted = [wa.s.node(n)["attrs"]["name"] for n in wa.s.nodes("MetaShape")
              if wa.s.node(n)["attrs"].get("signature")]
    assert minted == ["ms_buyer_is_a_lot_seller"], minted
    return minted[0]


# ----------------------------------------------------------------- Bug 1 ---

def test_headline_a_held_shape_covers_an_observation_with_an_extra_attribute():
    """THE HEADLINE. The spike's own refutation test, run.

    Before the fix this printed `residual` / `covered_by=None`; the fourth
    relation set differs from the held shape by ONE extra attribute, which is
    not novelty — it is the same idiom with an annotation on it.
    """
    from domains.meta_shape import observe

    wa = _boot_meta_shape_grain()
    shape = _mint_the_trade_record_shape(wa)

    observe(wa, "TradeRecord",
            {"buyer": "gary", "seller": "hank", "lot": "13", "note": "anything"})
    at = _last_observation(wa)
    assert len(at["signature"]) == 5, "the probe must actually carry k+1 relations"
    assert at["status"] == "recognized", at
    assert at["covered_by"] == shape, at


def test_negative_control_a_disjoint_item_is_still_a_residual():
    """Open arity must not make coverage vacuous: an item sharing no fixed
    relation with the held shape still reads as a residual."""
    from domains.meta_shape import observe

    wa = _boot_meta_shape_grain()
    _mint_the_trade_record_shape(wa)

    observe(wa, "Concept",
            {"name": "quintuple", "definition": "multiply a number by five"})
    at = _last_observation(wa)
    assert at["status"] == "residual", at
    assert at.get("covered_by") in (None, ""), at


def test_a_strict_subset_is_still_refused():
    """Superset-tolerant, NEVER subset-tolerant — the bar that separates a fix
    from a weakening. `seller` is absent, so the held shape does not apply."""
    from domains.meta_shape import observe

    wa = _boot_meta_shape_grain()
    _mint_the_trade_record_shape(wa)

    observe(wa, "TradeRecord", {"buyer": "kim", "lot": "21"})
    at = _last_observation(wa)
    assert len(at["signature"]) == 3
    assert at["status"] == "residual", at


def test_rung_four_still_grows_the_codebook():
    """The Occam ladder must still be able to MINT. A genuinely different
    predicate set, recurring twice, still earns its own `MetaShape`."""
    from domains.meta_shape import observe

    wa = _boot_meta_shape_grain()
    _mint_the_trade_record_shape(wa)

    observe(wa, "Reading", {"sensor": "a", "value": "3"})
    observe(wa, "Reading", {"sensor": "b", "value": "9"})
    minted = sorted(wa.s.node(n)["attrs"]["name"] for n in wa.s.nodes("MetaShape")
                    if wa.s.node(n)["attrs"].get("signature"))
    assert minted == ["ms_buyer_is_a_lot_seller", "ms_is_a_sensor_value"], minted
    # tranche 2 gate 6: MetaShape mints carry provenance
    for n in wa.s.nodes("MetaShape"):
        a = wa.s.node(n)["attrs"]
        if a.get("signature") and a.get("source") == "meta_shape_growth":
            assert a.get("minted_from_signature"), a
            assert "minted_epoch" in a


def test_the_shared_covers_term_is_unchanged():
    """`CoversOpen` is a SEPARATE Term. `Covers` keeps its exact equal-arity
    semantics, so no other caller in the tree changes behaviour."""
    wa = _boot_meta_shape_grain()
    native = wa.s._inner

    pattern = [["buyer", [WILD]], ["is_a", "traderecord"]]
    instance = [["buyer", "gary"], ["is_a", "traderecord"], ["note", "x"]]

    def ev(kind, pat, inst):
        return native.evaluate({"type": kind,
                                "pattern": {"type": "Lit", "value": pat},
                                "instance": {"type": "Lit", "value": inst},
                                "wild": WILD})

    assert ev("Covers", pattern, instance) is False
    assert ev("CoversOpen", pattern, instance) is True
    # ... and the open form is directional: the longer side as PATTERN fails.
    assert ev("CoversOpen", instance, pattern) is False


def test_the_seed_carries_no_arity_exact_guard_any_more():
    """Source audit: the meta-shape grain's six coverage guards ALL moved. A
    single surviving `Covers` would leave one rung arity-exact and the ladder
    internally inconsistent (rung 1's negation gates rungs 2-4)."""
    import json
    from substrate.seed_loader import manifest_for

    text = json.dumps(manifest_for("meta_shape_growth"))
    assert '"Covers"' not in text
    assert text.count('"CoversOpen"') == 6


# ----------------------------------------------------------------- Bug 2 ---

def test_capability_key_separator_is_injective():
    """The spike's own colliding pair, through the real code path."""
    from domains.reflective_faculty import _key_component

    def key(preds):
        return "induced_" + "_".join(_key_component(p) for p in sorted(preds))

    # BEFORE (the plain join): both are 'induced_a_b_c'.
    assert "_".join(sorted(["a_b", "c"])) == "_".join(sorted(["a", "b_c"]))
    # AFTER: distinct.
    assert key(["a_b", "c"]) != key(["a", "b_c"])
    # The escape introducer is escaped too, else a payload could forge one.
    assert key(["a%b"]) != key(["a%25b"])
    # A doubling scheme would collide on exactly this pair; this one does not.
    assert key(["a_", "b"]) != key(["a", "_b"])


def test_capability_key_values_are_unchanged_for_every_measured_predicate_set():
    """AR4.3: no silent key churn. Every derived key the tree actually produces
    today is byte-identical after the fix — measured over the three
    source-literal observations at the six derived call sites."""
    from domains.reflective_faculty import _key_component

    for preds in (["oscillate", "overshoot", "damp"],
                  ["move", "stop"],
                  ["detect", "type", "pairwise"]):
        old = "induced_" + "_".join(sorted(preds))
        new = "induced_" + "_".join(_key_component(p) for p in sorted(preds))
        assert old == new, (preds, old, new)


def test_induce_concern_still_keys_a_plain_observation_the_same_way():
    """End-to-end through `induce_concern` itself, not a re-implementation of
    the join: a `_`-free predicate set still produces the key it always did."""
    from substrate.boot_core import boot_core
    from domains import reflective_faculty as rf

    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)

    res = rf.induce_concern(s, [["zzzalpha", "X"], ["zzzbeta", "Y"]])
    assert res["capability_key"] == "induced_zzzalpha_zzzbeta", res["capability_key"]
    receipts = [s.node(n)["attrs"] for n in
                s.nodes("NativeReflectiveFacultyReceipt")]
    assert len(receipts) == 1
    assert receipts[0]["provenance"] == (
        "native_rule_readback:shape_decode_loop")
    assert receipts[0]["outcome_source"] == "native_rule_readback"
    assert receipts[0]["python_outcome_selection"] is False
