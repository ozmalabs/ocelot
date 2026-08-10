"""tests/test_frame_weights_migrated.py — RUN 30 migration-equivalence gates: the creator's
representation-reform directive ("all weights are not vectors, they are edges to other nodes
— weights are relative, order n and log scaled" + "a frame is N dimensions/axes with relative
weighting") made concrete over `domains/arrangement_codebook.py`'s run-29 stability weights.

Run 29 persisted 3,032 stability weights as a `relation_weights` DICT in one node attr —
invisible to `run_rules`, so the weight-update arithmetic ran in Python (a CLAUDE.md
violation in spirit — the metric itself WAS cognition). This suite gates the reform
(`domains/frame_weights.py` + `seeds/frame_weights.json`): a quantum's arrangement signature
is now a graph-resident FRAME (a Frame node + one FrameAxis node per relation key, log-scaled
weight as a node attr — the SAME "mirror an edge's weight on the node it points at" pattern
`domains/frame.py` already established, since `substrate_rs` does not expose per-edge attrs
for read-back), and every weight UPDATE is a graph rule (`fw_update`/`fw_pool`,
`seeds/frame_weights.json`) reading AxisEvidence data the adapter writes mechanically —
never Python arithmetic on the weight itself.

REPRESENTATION vs DYNAMICS — an honest scope note up front: the STORED representation is
log-scaled and every update is performed by a graph rule (gates (a)/(b)/(f)/(g) below). The
update FORMULA itself is run 29's own fixed EMA-toward-bound recompute
(`w' = (1-step)*w + step*target`), evaluated via `Log(Exp(w) combined affinely)` inside the
rule rather than a literal `log_weight += constant` — chosen DELIBERATELY so gate (a) and
`scripts/jabberwock_omniglot_run30_frames.py`'s own gate can hold this reform to an EXACT
numeric match against run 29's dict-path output (pre-registered as an equality, not merely a
same-ranking approximation). A literal order-independent `log_weight += const` update was
built and rejected: it is a DIFFERENT dynamic (geometric-EMA-toward-bound vs. linear-then-
clamped-in-log) that cannot reproduce run 29's specific multi-step numbers except by
coincidence. Gate (d) below tests what IS true of the chosen design — determinism and
per-evidence-node idempotence — and states plainly that the EMA recompute is intentionally
RECENCY-WEIGHTED (order-dependent), not commutative log-addition; this is the one place the
"log-additive" phrase in the run-30 brief is realized as "log-scaled, rule-driven" rather than
literal commutative addition, and is called out explicitly rather than silently claimed.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

import pytest

pytest.importorskip("substrate_rs")

import substrate_rs as srs
from substrate.boot_core import boot_core
from domains import arrangement_codebook as ac
from domains import character_compose as cc
from domains import frame as fr
from domains import frame_weights as fw
from domains import reflective_faculty as rf
from domains.teach import teach as _real_teach


@pytest.fixture(autouse=True)
def _isolate_seed_writes(tmp_path, monkeypatch):
    """Redirect teach() persistence to a tmp dir — unit-test mints must never land in the
    boot seed (seeds/character_shapes.json); the live graph install is unaffected. Same
    pattern `tests/test_arrangement_codebook_migrated.py` already establishes — MANDATORY for
    any test that can mint, per this run's own instructions."""
    monkeypatch.setattr(
        cc, "teach",
        lambda *a, **k: _real_teach(*a, **{**k, "seeds_dir": tmp_path}))


def _boot():
    s, ag = boot_core()
    native = s._inner
    rf._ensure_shape_decode_loop(s, native, ag)
    return s, ag, native


def _sig(rel0: tuple, rel1: tuple) -> list:
    """Same minimal two-stroke composed-signature fixture
    `tests/test_arrangement_codebook_migrated.py::_sig` already establishes."""
    return [["strokeq", 0, "a"], ["strokeq", 1, "b"],
            ["rel", 0, *rel0], ["rel", 1, *rel1],
            ["cpose_x", 1], ["cpose_y", 2], ["cpose_o", 3], ["cpose_s", 4]]


def _reference_ema(n_reps: int, *, step=ac.DEFAULT_STABILITY_STEP, min_w=ac.MIN_WEIGHT,
                    max_w=ac.MAX_WEIGHT, agree_pattern=None) -> float:
    """A plain, independent re-implementation of run 29's OWN dict-path EMA formula (the
    reference this suite holds the graph-rule implementation to) — NOT imported from
    `arrangement_codebook.py` (that would test the module against itself)."""
    w = max_w  # DEFAULT_WEIGHT == MAX_WEIGHT == 1.0 in this module's own constants.
    seq = agree_pattern if agree_pattern is not None else [False] * n_reps
    for agree in seq:
        w = min(max_w, w + step * (max_w - w)) if agree else max(min_w, w - step * (w - min_w))
    return w


# ===========================================================================
# (a) EQUIVALENCE — the frame-edge weighting reproduces the dict-path weighted scores/values
# to numeric tolerance, on the run-29-style unit fixture.
# ===========================================================================
def test_equivalence_matches_reference_ema_to_tight_tolerance():
    s, ag, native = _boot()
    ref_sig = _sig((1, 2, 3, 4), (5, 6, 7, 8))
    quantum = ac.mint_or_recognize_character_reading(s, ref_sig)["name"]
    unstable_obs = _sig((1, 2, 3, 4), (5, 6, 99, 8))   # ONLY rel:1:o ever mismatches.

    for _ in range(25):
        ac.update_relation_stability(s, quantum, ref_sig, unstable_obs)

    weights = ac.relation_weights(s, quantum)
    expected_unstable = _reference_ema(25, agree_pattern=[False] * 25)
    expected_stable = _reference_ema(25, agree_pattern=[True] * 25)
    assert weights["rel:1:o"] == pytest.approx(expected_unstable, abs=1e-9)
    assert weights["rel:0:x"] == pytest.approx(expected_stable, abs=1e-9)
    assert expected_stable == pytest.approx(ac.MAX_WEIGHT, abs=1e-9)


def test_equivalence_matches_reference_ema_on_a_mixed_agree_disagree_sequence():
    """A less trivial sequence than "always agree" / "always disagree" — alternating, THEN a
    run of disagreements — reproduces the SAME recency-weighted EMA the reference formula
    computes, applied in the SAME order (see this module's own top-of-file scope note: this
    design is intentionally order-DEPENDENT, matching run 29's own EMA exactly)."""
    s, ag, native = _boot()
    ref_sig = _sig((1, 2, 3, 4), (5, 6, 7, 8))
    quantum = ac.mint_or_recognize_character_reading(s, ref_sig)["name"]
    match_obs = ref_sig
    mismatch_obs = _sig((1, 2, 3, 4), (5, 6, 99, 8))

    pattern = [True, False, True, False, False, False, True, False, False, True]
    for agree in pattern:
        ac.update_relation_stability(s, quantum, ref_sig, mismatch_obs if not agree else match_obs)

    weights = ac.relation_weights(s, quantum)
    expected = _reference_ema(len(pattern), agree_pattern=pattern)
    assert weights["rel:1:o"] == pytest.approx(expected, abs=1e-9)


def test_weighted_arrangement_score_ranking_matches_dict_path_semantics():
    """The INDUCED ranking/score (not just the raw weight) matches: down-weighting a
    proven-unstable relation raises the arrangement score for an observation whose only
    disagreement is on that exact relation — the SAME behavioural gate `tests/
    test_arrangement_codebook_migrated.py`'s own gate 4 already holds the dict-path
    implementation to, re-run here against the frame-based one for equivalence."""
    s, ag, native = _boot()
    ref_sig = _sig((1, 2, 3, 4), (5, 6, 7, 8))
    quantum = ac.mint_or_recognize_character_reading(s, ref_sig)["name"]
    unstable_obs = _sig((1, 2, 3, 4), (5, 6, 99, 8))

    baseline = ac.weighted_arrangement_score(s, quantum, ref_sig, unstable_obs)
    n = baseline["n"]
    unweighted_score = (n - 1) / n
    assert baseline["score"] == pytest.approx(unweighted_score)

    for _ in range(25):
        ac.update_relation_stability(s, quantum, ref_sig, unstable_obs)
    learned = ac.weighted_arrangement_score(s, quantum, ref_sig, unstable_obs)
    assert learned["score"] > baseline["score"]

    expected_w = _reference_ema(25, agree_pattern=[False] * 25)
    # 11 of the 12 relation keys match (contribute their own weight, all at the ceiling); the
    # one mismatching key (rel:1:o) contributes 0 to the numerator but its OWN (fallen) weight
    # still counts toward the denominator -- matched_weight / total_weight.
    expected_score = (11 * 1.0) / (11 * 1.0 + expected_w)
    assert learned["score"] == pytest.approx(expected_score, abs=1e-9)


# ===========================================================================
# (b) RULES DO THE UPDATE — no Python arithmetic computes a new weight value; the weight only
# changes after a graph rule (`fw_update`) has had a chance to run.
# ===========================================================================
def test_no_python_arithmetic_computes_the_weight_value_source_audit():
    """Source audit: run 29's own EMA arithmetic idiom (`cur + step *`, `cur - step *`,
    `min(max_weight`, `max(min_weight`) must be ABSENT from `arrangement_codebook.py` — that
    computation now lives ONLY in `seeds/frame_weights.json`'s `fw_update` rule (a Term
    evaluated inside `run_rules`, never Python)."""
    src = Path(ac.__file__).read_text()
    for pattern in (r"cur\s*\+\s*step\s*\*", r"cur\s*-\s*step\s*\*",
                    r"min\(max_weight", r"max\(min_weight"):
        assert not re.search(pattern, src), f"found banned EMA arithmetic pattern {pattern!r}"
    # The banned argmin/argmax / min-max-with-key / bare-list-isinstance patterns this
    # codebase's OWN existing audits already check must stay clean too (re-affirmed here since
    # this run edited the file).
    assert not re.search(r"\.arg(?:min|max)\(|(?<!\w)np\.arg(?:min|max)\b", src, re.IGNORECASE)


def test_no_python_arithmetic_in_frame_weights_module_source_audit():
    src = Path(fw.__file__).read_text()
    banned = re.compile(r"\.arg(?:min|max)\(|(?<!\w)np\.arg(?:min|max)\b", re.IGNORECASE)
    assert not banned.search(src)
    minmax_key = re.compile(r"(?<!\w)(?:min|max)\(.*?key\s*=", re.IGNORECASE)
    assert not minmax_key.search(src)


def test_weight_unchanged_until_run_rules_fires():
    """Writing an AxisEvidence node is a pure mechanical graph write — the axis's own
    `log_weight` must NOT change until `run_rules` actually fires `fw_update`."""
    s, ag, native = _boot()
    ref_sig = _sig((1, 2, 3, 4), (5, 6, 7, 8))
    quantum = ac.mint_or_recognize_character_reading(s, ref_sig)["name"]
    node = ac._quantum_node(s, quantum)
    frame_node = fw._frame_node_by_key(s, fw.quantum_frame_key(quantum))
    assert frame_node is not None

    before = fw.axis_weight(s, frame_node, "rel:1:o")
    axis = fw._axis_node_in_frame(s, frame_node, "rel:1:o")
    fw.write_axis_evidence(s, axis, agree=False)
    still_before = fw.axis_weight(s, frame_node, "rel:1:o")
    assert still_before == pytest.approx(before), "the mechanical write alone must not move the weight"

    native.run_rules()
    after = fw.axis_weight(s, frame_node, "rel:1:o")
    assert after < before, "only run_rules (fw_update) may move the weight"


# ===========================================================================
# (c) RELATIVE — weights within a frame compare only against siblings; a uniform positive
# rescaling of every axis's weight in a frame leaves the WEIGHTED SCORE invariant (the score
# formula is a ratio of a frame's own weights against each other, never an absolute scale).
# ===========================================================================
def test_weights_are_relative_uniform_rescale_leaves_score_invariant():
    s, ag, native = _boot()
    ref_sig = _sig((1, 2, 3, 4), (5, 6, 7, 8))
    quantum = ac.mint_or_recognize_character_reading(s, ref_sig)["name"]
    frame_node = fw._frame_node_by_key(s, fw.quantum_frame_key(quantum))
    obs = _sig((1, 2, 3, 4), (5, 6, 99, 8))     # rel:1:o mismatches, everything else matches.

    def _set_all_weights(scale: float):
        for nid in s.neighbours(frame_node, fw.IN_AXIS_EDGE):
            name = s.node(nid)["attrs"].get("name")
            # Two DISTINCT relative magnitudes for the (matching) stable axes vs the
            # (mismatching) rel:1:o axis, both scaled by `scale` -- a uniform rescale of the
            # WHOLE frame's own weight vector.
            base = 0.2 if name == "rel:1:o" else 0.8
            s.set_attr(nid, "log_weight", math.log(base * scale))

    _set_all_weights(1.0)
    score_1x = ac.weighted_arrangement_score(s, quantum, ref_sig, obs)["score"]
    _set_all_weights(0.1)     # every weight scaled down by 10x, SAME relative ratios.
    score_small = ac.weighted_arrangement_score(s, quantum, ref_sig, obs)["score"]
    _set_all_weights(3.0)     # every weight scaled UP by 3x, SAME relative ratios.
    score_large = ac.weighted_arrangement_score(s, quantum, ref_sig, obs)["score"]

    assert score_1x == pytest.approx(score_small, abs=1e-9)
    assert score_1x == pytest.approx(score_large, abs=1e-9)
    # Discriminative: a NON-uniform rescale (only the mismatching axis's relative weight
    # changes) DOES move the score -- proving the invariance above is about relativity, not a
    # formula that ignores weights altogether.
    s.set_attr(fw._axis_node_in_frame(s, frame_node, "rel:1:o"), "log_weight", math.log(0.8))
    score_changed = ac.weighted_arrangement_score(s, quantum, ref_sig, obs)["score"]
    assert score_changed != pytest.approx(score_1x, abs=1e-6)


# ===========================================================================
# (d) DETERMINISM + PER-EVIDENCE-NODE IDEMPOTENCE — see this file's own top-of-file scope note
# for why this is NOT an order-independence claim (the EMA recompute is intentionally
# recency-weighted, chosen to exactly reproduce run 29's own numbers).
# ===========================================================================
def test_update_is_idempotent_per_evidence_node():
    """Re-running `run_rules` again after an evidence node has already been applied must NOT
    move the weight a second time (the `fw_update` rule's own `applied` guard)."""
    s, ag, native = _boot()
    ref_sig = _sig((1, 2, 3, 4), (5, 6, 7, 8))
    quantum = ac.mint_or_recognize_character_reading(s, ref_sig)["name"]
    frame_node = fw._frame_node_by_key(s, fw.quantum_frame_key(quantum))
    axis = fw._axis_node_in_frame(s, frame_node, "rel:1:o")

    fw.write_axis_evidence(s, axis, agree=False)
    native.run_rules()
    once = fw.axis_weight(s, frame_node, "rel:1:o")
    native.run_rules()
    native.run_rules()
    twice = fw.axis_weight(s, frame_node, "rel:1:o")
    assert twice == pytest.approx(once, abs=1e-12), (
        "an already-applied AxisEvidence node must never be re-applied by a later run_rules call")


def test_update_is_deterministic_same_sequence_same_result():
    """The SAME evidence sequence from a fresh quantum reproduces the SAME final weight —
    deterministic graph-rule arithmetic, no hidden randomness."""
    def _run():
        s, ag, native = _boot()
        ref_sig = _sig((1, 2, 3, 4), (5, 6, 7, 8))
        quantum = ac.mint_or_recognize_character_reading(s, ref_sig)["name"]
        pattern = [True, False, False, True, False]
        obs_match, obs_mismatch = ref_sig, _sig((1, 2, 3, 4), (5, 6, 99, 8))
        for agree in pattern:
            ac.update_relation_stability(s, quantum, ref_sig, obs_match if agree else obs_mismatch)
        return ac.relation_weights(s, quantum)["rel:1:o"]

    assert _run() == pytest.approx(_run(), abs=1e-12)


def test_order_dependence_is_the_documented_recency_weighted_ema_not_a_regression():
    """Honest documentation-as-test: this design's EMA recompute IS order-dependent (recency-
    weighted), a DELIBERATE choice (see module docstring) to reproduce run 29's own numbers
    exactly — NOT a bug. Two evidence sequences that are permutations of each other (same
    agree/disagree multiset, different order) give DIFFERENT final weights."""
    def _run(pattern):
        s, ag, native = _boot()
        ref_sig = _sig((1, 2, 3, 4), (5, 6, 7, 8))
        quantum = ac.mint_or_recognize_character_reading(s, ref_sig)["name"]
        obs_match, obs_mismatch = ref_sig, _sig((1, 2, 3, 4), (5, 6, 99, 8))
        for agree in pattern:
            ac.update_relation_stability(s, quantum, ref_sig, obs_match if agree else obs_mismatch)
        return ac.relation_weights(s, quantum)["rel:1:o"]

    w_agree_first = _run([True, False])
    w_disagree_first = _run([False, True])
    assert w_agree_first != pytest.approx(w_disagree_first, abs=1e-6), (
        "if these ever match to tight tolerance, the update stopped being the recency-weighted "
        "EMA this module's docstring documents -- re-verify against _reference_ema before "
        "treating that as an improvement, it would also change the run-29 reproduction numbers")


# ===========================================================================
# (e) SHARED-FRAME POOLING — matches run-29's own pooled-prior numbers on its fixture.
# ===========================================================================
def test_pooled_reliability_matches_reference_mean_of_linear_weights():
    s, ag, native = _boot()
    sig_a = _sig((1, 2, 3, 4), (5, 6, 7, 8))
    quantum_a = ac.mint_or_recognize_character_reading(s, sig_a)["name"]
    sig_b = _sig((9, 9, 9, 9), (1, 1, 1, 1))
    quantum_b = ac.mint_or_recognize_character_reading(s, sig_b)["name"]

    unstable_obs_a = _sig((1, 2, 3, 4), (5, 6, 99, 8))
    unstable_obs_b = _sig((99, 9, 9, 9), (1, 1, 1, 1))
    for _ in range(25):
        ac.update_relation_stability(s, quantum_a, sig_a, unstable_obs_a)
        ac.update_relation_stability(s, quantum_b, sig_b, unstable_obs_b)

    prior = ac.pooled_relation_kind_reliability(s)
    w_a = ac.relation_weights(s, quantum_a)
    w_b = ac.relation_weights(s, quantum_b)
    expected_o = (w_a["rel:0:o"] + w_a["rel:1:o"] + w_b["rel:0:o"] + w_b["rel:1:o"]) / 4.0
    expected_x = (w_a["rel:0:x"] + w_a["rel:1:x"] + w_b["rel:0:x"] + w_b["rel:1:x"]) / 4.0
    assert prior["o"] == pytest.approx(expected_o, abs=1e-9)
    assert prior["x"] == pytest.approx(expected_x, abs=1e-9)
    assert prior["y"] == pytest.approx(ac.MAX_WEIGHT, abs=1e-9)
    assert ac.MIN_WEIGHT < prior["o"] < ac.MAX_WEIGHT


def test_pooled_frame_is_a_distinct_frame_node_from_every_quantum_frame():
    s, ag, native = _boot()
    sig_a = _sig((1, 2, 3, 4), (5, 6, 7, 8))
    quantum_a = ac.mint_or_recognize_character_reading(s, sig_a)["name"]
    ac.pooled_relation_kind_reliability(s)
    pooled = fw._frame_node_by_key(s, fw.POOLED_FRAME_KEY)
    per_quantum = fw._frame_node_by_key(s, fw.quantum_frame_key(quantum_a))
    assert pooled is not None and per_quantum is not None
    assert pooled != per_quantum
    # Both are the SAME reused node TYPE (`domains.frame`'s own "Frame") -- not a parallel type.
    assert s.node(pooled)["type"] == fr._FRAME_TYPE == s.node(per_quantum)["type"]


# ===========================================================================
# (f) PERSISTENCE — frame + axes + weight edges survive the full
# graph_to_dict/grammar_to_json/export_rules round trip, AND remain LIVE (a freshly-written
# evidence node on the reloaded graph is still picked up by the reloaded fw_update rule).
# ===========================================================================
def _save_graph(s, path: str) -> None:
    blob = {"graph": s.graph_to_dict(), "grammar": s.grammar_to_json(),
            "rules": s._inner.export_rules()}
    with open(path, "w") as f:
        json.dump(blob, f)


def _load_graph(path: str):
    with open(path) as f:
        blob = json.load(f)
    s = srs.Substrate()
    s.graph_from_dict(blob["graph"])
    for p in blob["grammar"]["productions"]:
        try:
            s._inner.add_production(p)
        except Exception:
            pass
    if "rules" in blob:
        s._inner.import_rules(blob["rules"])
    return s


def test_frame_and_weights_persist_and_stay_live_across_save_load(tmp_path):
    s, ag, native = _boot()
    ref_sig = _sig((1, 2, 3, 4), (5, 6, 7, 8))
    quantum = ac.mint_or_recognize_character_reading(s, ref_sig)["name"]
    unstable_obs = _sig((1, 2, 3, 4), (5, 6, 99, 8))
    for _ in range(10):
        ac.update_relation_stability(s, quantum, ref_sig, unstable_obs)
    weights_before = ac.relation_weights(s, quantum)
    assert weights_before["rel:1:o"] < ac.DEFAULT_WEIGHT

    path = str(tmp_path / "run30_frame_graph.json")
    _save_graph(s, path)
    s2 = _load_graph(path)

    weights_after = ac.relation_weights(s2, quantum)
    assert weights_after == weights_before, (
        "Frame/FrameAxis nodes + in_dim/has_frame edges are plain graph data -- they must "
        "survive the SAME graph_to_dict/grammar_to_json/export_rules round trip every other "
        "run-26..29 checkpoint already relies on")

    # LIVE, not just static: further evidence on the reloaded graph is still applied by the
    # reloaded fw_update rule (proves the RULE itself round-tripped via export_rules/
    # import_rules, not merely the node/edge data).
    for _ in range(10):
        ac.update_relation_stability(s2, quantum, ref_sig, unstable_obs)
    weights_further = ac.relation_weights(s2, quantum)
    assert weights_further["rel:1:o"] < weights_after["rel:1:o"], (
        "the reloaded graph's fw_update rule must still fire on NEW evidence")


# ===========================================================================
# (g) ENGINE-GOTCHA GUARD — 40 synthetic quanta live: no cross-talk between quanta's own axes,
# no run_rules matching breakage at this scale (the writer arc's own documented gotcha: "two
# same-type incoming edges on one node can break run_rules matching for that edge type").
# ===========================================================================
def test_forty_quanta_scale_no_cross_talk_no_matching_breakage():
    s, ag, native = _boot()
    quanta = []
    for i in range(40):
        # stroke 0's per-slot values grow LINEARLY in i (delta 13*(i-i') between any two
        # quanta); stroke 1's grow QUADRATICALLY (delta 7*(i^2-i'^2)) -- the two strokes'
        # own per-slot deltas can never coincide for i != i' (13 == 7*(i+i') has no integer
        # solution), so TransformDecode's own (predicate,slot)-pooled consistency check can
        # never explain one of these as identity + one uniform delta on another -- every one
        # is a genuinely novel arrangement, unlike a uniform "+1 to everything" sequence (which
        # WOULD legitimately recognize-under-transformation rather than mint, correctly).
        rel0 = tuple(13 * i + s for s in range(4))
        rel1 = tuple(7 * i * i + 3 * s for s in range(4))
        sig = _sig(rel0, rel1)
        res = ac.mint_or_recognize_character_reading(s, sig)
        assert res["minted"] is True, f"quantum {i} must mint as a distinct arrangement"
        quanta.append((res["name"], sig))

    assert ac.character_vocabulary_report(s)["total"] == 40

    # Destabilize rel:1:o on the EVEN-indexed quanta only; leave the ODD-indexed quanta
    # untouched -- the cross-talk check is that the ODD quanta's weights stay at
    # DEFAULT_WEIGHT (no bleed from the even quanta's own updates onto a shared axis node).
    for i, (name, sig) in enumerate(quanta):
        if i % 2 == 0:
            mismatched = list(sig)
            # Flip stroke 1's orientation slot only (index 2 of the second "rel" entry).
            mismatched = [list(r) for r in mismatched]
            for r in mismatched:
                if r[0] == "rel" and r[1] == 1:
                    r[4] = 999
            for _ in range(5):
                ac.update_relation_stability(s, name, sig, mismatched)

    for i, (name, sig) in enumerate(quanta):
        weights = ac.relation_weights(s, name)
        assert len(weights) == 12, f"quantum {i} must hold exactly its own 12 relation axes"
        if i % 2 == 0:
            assert weights["rel:1:o"] < ac.DEFAULT_WEIGHT, f"quantum {i} must show the fall"
        else:
            assert weights["rel:1:o"] == pytest.approx(ac.DEFAULT_WEIGHT), (
                f"quantum {i} must be UNTOUCHED by another quantum's own updates -- cross-talk")
        # Every OTHER axis on every quantum stays at the ceiling (nothing else was destabilized).
        for key, w in weights.items():
            if key != "rel:1:o" or i % 2 != 0:
                assert w == pytest.approx(ac.MAX_WEIGHT), f"quantum {i} axis {key} unexpectedly moved"

    # No matching breakage: the pooled prior (which scans every FrameAxis across all 40
    # quanta) still computes cleanly and lands strictly between the floor and ceiling for the
    # destabilized kind, at the ceiling for every untouched kind.
    prior = ac.pooled_relation_kind_reliability(s)
    assert ac.MIN_WEIGHT < prior["o"] < ac.MAX_WEIGHT
    assert prior["x"] == pytest.approx(ac.MAX_WEIGHT)
    assert prior["y"] == pytest.approx(ac.MAX_WEIGHT)
    assert prior["s"] == pytest.approx(ac.MAX_WEIGHT)


# ===========================================================================
# Frame-type reuse — the run-30 directive's own instruction: check first whether the
# substrate already has Frame conventions, reuse them if they fit, document + use a distinct
# type if not.
# ===========================================================================
def test_reuses_domains_frame_frame_type_but_not_its_shared_dimension_type():
    s, ag, native = _boot()
    ref_sig = _sig((1, 2, 3, 4), (5, 6, 7, 8))
    quantum = ac.mint_or_recognize_character_reading(s, ref_sig)["name"]
    frame_node = fw._frame_node_by_key(s, fw.quantum_frame_key(quantum))
    assert s.node(frame_node)["type"] == "Frame" == fr._FRAME_TYPE
    for nid in s.neighbours(frame_node, fw.IN_AXIS_EDGE):
        assert s.node(nid)["type"] == "FrameAxis", (
            "axes are a DISTINCT type from domains.frame's own 'Dimension' -- Dimension nodes "
            "are documented shared vocabulary reused BY NAME across many frames, which is "
            "wrong for a per-quantum-local relation axis (see domains/frame_weights.py's own "
            "module docstring for the full reasoning)")
