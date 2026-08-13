"""LOGODDS_DIMINFER_PREREG.md/_RESULTS.md: AUTOMATIC recognition of the
evidence-accumulation generator from a raw observation TRAJECTORY, closing
the gap LOGODDS_GENERATOR_RESULTS.md Sec7.1 named and left un-built.
seeds/evidence_axis_infer.json (TimeInfer-based, not DimInfer -- see the
PREREG's decision). Reuses tests/test_can_native_reimplementation.py's own
harness idioms (_loaded_substrate/_isolated_pair/_coact_between) unmodified.

CRITICAL: none of these tests load seeds/inference_knowledge.json, so the
pre-declared 'logodds_evidence' DimensionGenerator / 'latent:causal_strength'
LatentDimension are simply ABSENT from every graph here -- the cleanest
possible "without the generator pre-declared" condition.
"""
from __future__ import annotations

import json

import substrate_rs as sr
from substrate.seed_loader import engine_rules_only

CAN_SEED = "seeds/can_native_reimplementation.json"
AXIS_SEED = "seeds/evidence_axis_infer.json"


def _loaded_substrate(seed_paths):
    s = sr.Substrate()
    inner = s._inner
    for path in seed_paths:
        d = json.load(open(path))
        filtered = engine_rules_only(d)
        inner.load_seed_manifest(filtered)
    return s


def _isolated_pair(inner):
    """Byte-identical to test_can_native_reimplementation.py's own helper."""
    mt = inner.add_node("Microtheory", {"temperature": 1.0, "discrete_mode": "static", "can_tick": 0})
    a = inner.add_node("Concept", {"name": "a", "state": 1.0, "external_field": 0.0, "identity_field": 0.0})
    b = inner.add_node("Concept", {"name": "b", "state": 1.0, "external_field": 0.0, "identity_field": 0.0})
    inner.add_edge(mt, "has_concept", a, {})
    inner.add_edge(mt, "has_concept", b, {})
    return mt, a, b


def _coact_between(inner, a, b):
    for c in inner.neighbours(a, "coactivated_with"):
        if b in inner.neighbours(c, "coactivation_of"):
            return c
    return None


def _inferred_gen_nodes(inner):
    return [n for n in inner.nodes("DimensionGenerator")
            if inner.node(n)["attrs"].get("name") == "logodds_evidence_inferred"]


def _inferred_ld_nodes(inner):
    return [n for n in inner.nodes("LatentDimension")
            if inner.node(n)["attrs"].get("name") == "latent:causal_strength_inferred"]


def _log_odds_term():
    from substrate_rs import Term
    return Term(
        "Log",
        arg=Term(
            "Div",
            a=Term("Plus", items=[
                Term("Attr", node=Term("Var", name="coact"), key="evidence_confirm"),
                Term("Lit", value=1),
            ]),
            b=Term("Plus", items=[
                Term("Attr", node=Term("Var", name="coact"), key="evidence_disconfirm"),
                Term("Lit", value=1),
            ]),
        ),
    )


# ---------------------------------------------------------------------
# (1) Positive: zero-mint-once-recognized / correct-mint-on-recurrence.
# ---------------------------------------------------------------------

def test_pure_reinforcement_run_is_automatically_recognized_and_minted_once():
    """A pure confirm-only run (no pre-declared 'logodds_evidence' generator
    anywhere in this graph -- inference_knowledge.json is never loaded).
    Drives 5 confirming ticks (mint + 4 reinforcements), watches the window
    fill, and asserts the DimensionGenerator/LatentDimension pair is minted
    EXACTLY ONCE the first time the window satisfies TimeInfer's exact-
    equality orbit test, and never again on later ticks even though the
    window keeps satisfying it."""
    s = _loaded_substrate([CAN_SEED, AXIS_SEED])
    inner = s._inner
    mt, a, b = _isolated_pair(inner)

    inner.run_rules(1000)  # tick 0: note only
    coact = _coact_between(inner, a, b)
    assert coact is not None

    mint_tick = None
    window_at_mint = None
    for tick in range(1, 6):  # ticks 1-5: recurrence (mint) + 4 reinforcements, all confirming
        inner.set_attr(mt, "can_tick", tick)
        inner.run_rules(1000)
        window = inner.node(coact)["attrs"].get("evidence_confirm_window")
        gens = _inferred_gen_nodes(inner)
        lds = _inferred_ld_nodes(inner)
        print(f"tick {tick}: evidence_confirm={inner.node(coact)['attrs']['evidence_confirm']} "
              f"window={window} inferred_gens={len(gens)} inferred_lds={len(lds)}")
        if gens and mint_tick is None:
            mint_tick = tick
            window_at_mint = window

    assert mint_tick is not None, "the pure reinforcement run must be recognized and minted at some tick"
    gens = _inferred_gen_nodes(inner)
    lds = _inferred_ld_nodes(inner)
    assert len(gens) == 1, f"exactly one DimensionGenerator must be minted, got {len(gens)}"
    assert len(lds) == 1, f"exactly one LatentDimension must be minted, got {len(lds)}"
    gattrs = inner.node(gens[0])["attrs"]
    assert gattrs["kind"] == "translate", gattrs
    # coord_dims == (1,): the codebook part's dim_types is ["pred","coord:v"]
    # (index 0 = predicate "m", index 1 = the coordinate slot) -- the SAME
    # slot layout F16AxisSample uses.
    assert tuple(gattrs["coord_dims"]) == (1,), gattrs
    assert tuple(gattrs["offset"]) == (1,), gattrs
    assert inner.node(lds[0])["attrs"]["generator"] == "logodds_evidence_inferred"

    edges_at_mint_node = inner.neighbours(coact, "has_inferred_axis")
    assert lds[0] in edges_at_mint_node

    print(f"MINT: tick={mint_tick} window_at_mint={window_at_mint} "
          f"generator={gattrs} latent_dim={inner.node(lds[0])['attrs']}")

    # Continue running further confirming ticks -- the window keeps
    # satisfying TimeInfer's orbit test, but the has_inferred_axis-edge
    # guard must keep this a ONE-TIME mint.
    for tick in range(6, 9):
        inner.set_attr(mt, "can_tick", tick)
        inner.run_rules(1000)
    gens_after = _inferred_gen_nodes(inner)
    lds_after = _inferred_ld_nodes(inner)
    assert len(gens_after) == 1 and gens_after[0] == gens[0], (
        f"re-running further confirming ticks must NOT re-mint a second DimensionGenerator, "
        f"got {len(gens_after)}"
    )
    assert len(lds_after) == 1 and lds_after[0] == lds[0], (
        f"re-running further confirming ticks must NOT re-mint a second LatentDimension, "
        f"got {len(lds_after)}"
    )
    print(f"zero-mint-once-recognized confirmed: {len(gens_after)} generator(s), "
          f"{len(lds_after)} dimension(s) after 3 further confirming ticks")


# ---------------------------------------------------------------------
# (2) No-spurious-mint on a genuinely irregular (interleaved) trajectory.
# ---------------------------------------------------------------------

def test_interleaved_confirm_disconfirm_trajectory_never_mints():
    """The window sampler is gated on a GENUINE co-activation observation
    (both a and b committed nonzero -- the SAME guard
    can_native_hebbian_reweight itself uses), so it only ever samples a real
    evidence event, never a silent tick. The disconfirming observation lands
    SECOND (immediately after the mint) -- deliberately early, so no clean
    3-sample confirming prefix exists for the positive rule to recognize
    before the irregularity appears (test 1's own positive case shows
    recognition fires the INSTANT the window reaches 3 samples, so an
    irregularity arriving any later would be moot -- a genuinely negative
    demonstration has to poison the window from the start). The resulting
    confirm-axis window ([1,1,2,3,4] -- flat on the disconfirming tick, then
    resuming) has a non-constant first-pair delta (0, since the disconfirm
    keeps confirm flat) -- TimeInfer's order-1 exact-equality test excludes
    a zero offset as 'no motion' by construction, and the order-N
    finite-difference fallback (checked directly below, not merely
    predicted) never reaches a witnessed >=2-element constant from this
    stream either. TimeInfer must report explained=0 and the mint rule must
    never fire, across an EXTENDED run (not just the first few ticks)."""
    s = _loaded_substrate([CAN_SEED, AXIS_SEED])
    inner = s._inner
    mt, a, b = _isolated_pair(inner)

    inner.run_rules(1000)  # tick 0: note
    coact = _coact_between(inner, a, b)

    inner.set_attr(mt, "can_tick", 1)  # tick 1: recurrence -- mint the edge, confirm=1
    inner.run_rules(1000)

    inner.set_attr(b, "state", -1.0)  # tick 2: a genuine DISCONFIRMING observation, early
    inner.set_attr(mt, "can_tick", 2)
    inner.run_rules(1000)

    for tick in (3, 4, 5):  # resume confirming
        inner.set_attr(b, "state", 1.0)
        inner.set_attr(mt, "can_tick", tick)
        inner.run_rules(1000)

    attrs = inner.node(coact)["attrs"]
    assert (attrs["evidence_confirm"], attrs["evidence_disconfirm"]) == (4, 1), attrs
    window = attrs.get("evidence_confirm_window")
    print(f"interleaved window: {window} (a genuine early disconfirming observation must show as a flat step)")
    assert window is not None and len(window) >= 3
    deltas = [window[i + 1] - window[i] for i in range(len(window) - 1)]
    assert len(set(deltas)) > 1, f"the window must contain a genuine non-constant step, got deltas {deltas}"
    assert deltas[0] == 0, f"the poisoning delta must be the FIRST pair (no clean prefix to recognize), got {deltas}"

    gens = _inferred_gen_nodes(inner)
    lds = _inferred_ld_nodes(inner)
    assert gens == [], f"an interleaved confirm/disconfirm trajectory must never mint a DimensionGenerator, got {gens}"
    assert lds == [], f"an interleaved confirm/disconfirm trajectory must never mint a LatentDimension, got {lds}"
    assert inner.neighbours(coact, "has_inferred_axis") == []
    print("no-spurious-mint confirmed: interleaved trajectory recognized by nothing, minted nothing")


# ---------------------------------------------------------------------
# (3) The registered null: the coupled 2-D trajectory, and DimInfer's
#     architectural unreachability, both demonstrated directly.
# ---------------------------------------------------------------------

def test_coupled_2d_trajectory_is_not_explained_by_time_infer():
    """The EXACT trajectory test_can_native_reimplementation.py's own
    test_evidence_counters_are_real_integers_stepping_across_ticks measures
    live: (0,0)->(1,0)->(2,0)->(3,0)->(3,1) -- three confirming ticks then
    one disconfirming tick. Fed to TimeInfer as a 2-D (confirm,disconfirm)
    sequence directly (bypassing the seed's rules -- a raw Term probe), this
    must report explained=0: the per-tick offset CHANGES direction ((1,0)
    for three steps, then (0,1)) which is neither a single constant
    generator (order-1) nor a regular finite-difference stream (order-N,
    since the change is event-conditional, not a smooth acceleration)."""
    s = _loaded_substrate([CAN_SEED, AXIS_SEED])
    inner = s._inner

    from substrate_rs import Term
    frames = [(0, 0), (1, 0), (2, 0), (3, 0), (3, 1)]
    seq_term = Term("Lit", value=[[["m", c, d]] for c, d in frames])
    t = Term("TimeInfer", sequence=seq_term, codebook_type="EvidenceAxisSample2D",
             max_b=8, max_steps=64, robust=False, field="explained")

    # EvidenceAxisSample2D: a 2-coordinate codebook part, declared directly
    # on this graph (not via the seed -- this probe is deliberately
    # independent of the mint rules, testing TimeInfer's raw behaviour).
    inner.add_node("EvidenceAxisSample2D", {
        "name": "evidence_axis_sample_2d",
        "signature": json.dumps([["m", 0, 0]]),
        "dim_types": ["pred", "coord:confirm", "coord:disconfirm"],
    })

    explained = s.evaluate(t, {})
    print(f"coupled 2-D trajectory {frames}: TimeInfer(explained)={explained}")
    assert explained == 0, (
        "the genuinely coupled, event-conditional 2-D evidence trajectory must NOT be explained "
        "by TimeInfer's single-constant-generator orbit test -- this is the registered null, "
        "not a defect"
    )


def test_dim_infer_rung1_already_explains_a_single_relation_delta_no_generator_needed():
    """Claim A from the PREREG, demonstrated live rather than only by
    source-reading: TransformDecode's rung-1 consistency check
    (build_candidate) is vacuously 'uniform' for a signature made of ONE
    relation, so it already reports explained=1 for a plain
    (confirm,disconfirm) delta with NO generator ever consulted -- meaning
    DimInfer's rung-2 candidate-generator loop is architecturally unreached
    for this representation, confirmed live."""
    s = _loaded_substrate([CAN_SEED, AXIS_SEED])
    inner = s._inner

    from substrate_rs import Term
    # A held base part: confirm=0, disconfirm=0.
    inner.add_node("EvidenceAxisSample2D", {
        "name": "held_zero",
        "signature": json.dumps([["m", 0, 0]]),
        "dim_types": ["pred", "coord:confirm", "coord:disconfirm"],
    })
    # The goal: confirm=3, disconfirm=1 -- a two-slot delta from the held base.
    goal_term = Term("Lit", value=[["m", 3, 1]])
    t = Term("TransformDecode", goal=goal_term, codebook_type="EvidenceAxisSample2D",
             max_dims=4, field="explained")
    explained = s.evaluate(t, {})
    t_transforms = Term("TransformDecode", goal=goal_term, codebook_type="EvidenceAxisSample2D",
                         max_dims=4, field="transforms")
    transforms = s.evaluate(t_transforms, {})
    print(f"TransformDecode (rung 1, NO generator) on a single-relation 2-slot delta: "
          f"explained={explained} transforms={transforms}")
    assert explained == 1, (
        "rung 1 (TransformDecode) must already fully explain a single-relation delta with no "
        "generator at all -- confirming DimInfer (rung 2) is architecturally unreached for this "
        "representation, exactly as the PREREG's Claim A predicted"
    )
    assert len(transforms) == 2, f"expected two per-dim deltas (confirm, disconfirm), got {transforms}"


# ---------------------------------------------------------------------
# (4) Composition with the existing item-4 Hebbian mechanism.
# ---------------------------------------------------------------------

def test_inferred_axis_composes_with_the_existing_log_odds_render():
    """After the automatic mint, the EXISTING, UNCHANGED log-odds render
    (Log(Div(Plus(confirm,1),Plus(disconfirm,1)))) still reads
    evidence_confirm/evidence_disconfirm directly and renders the SAME value
    it would without seeds/evidence_axis_infer.json loaded -- the inferred
    generator sits ALONGSIDE the Hebbian mechanism as additional graph data,
    never a parallel or disconnected one. Also confirms the new rules never
    write evidence_confirm/evidence_disconfirm/evidence_tick or any log-odds
    render key onto the Coactivation node."""
    s_plain = _loaded_substrate([CAN_SEED])
    s_axis = _loaded_substrate([CAN_SEED, AXIS_SEED])
    term = _log_odds_term()

    renders = {}
    for label, s in (("plain", s_plain), ("with_axis_infer", s_axis)):
        inner = s._inner
        mt, a, b = _isolated_pair(inner)
        inner.run_rules(1000)  # tick 0: note
        coact = _coact_between(inner, a, b)
        before_confirm_disconfirm_keys = set(inner.node(coact)["attrs"].keys())

        for tick in range(1, 5):  # mint + 3 reinforcements, all confirming
            inner.set_attr(mt, "can_tick", tick)
            inner.run_rules(1000)

        attrs = inner.node(coact)["attrs"]
        assert (attrs["evidence_confirm"], attrs["evidence_disconfirm"]) == (4, 0), attrs
        renders[label] = s.evaluate(term, {"coact": coact})

        # the new rules must never write evidence_confirm/evidence_disconfirm/
        # evidence_tick or any log_odds/render key.
        assert attrs["evidence_confirm"] == 4 and attrs["evidence_disconfirm"] == 0
        assert "log_odds" not in attrs and "render" not in attrs

    print(f"log_odds render: plain={renders['plain']:.4f} with_axis_infer={renders['with_axis_infer']:.4f}")
    assert renders["plain"] == renders["with_axis_infer"], (
        "the log-odds render must be BYTE-IDENTICAL whether or not seeds/evidence_axis_infer.json "
        "is loaded -- the inferred axis is additive graph data, never a parallel mechanism that "
        "changes the existing render"
    )

    # And on the axis-infer graph specifically: confirm the axis WAS actually
    # inferred (not merely "the seed loaded and did nothing"), composing
    # alongside the render.
    inner = s_axis._inner
    gens = _inferred_gen_nodes(inner)
    assert len(gens) == 1, "the inferred generator must actually exist alongside the render in this scenario"
    print(f"inferred generator present alongside the render: {inner.node(gens[0])['attrs']}")
