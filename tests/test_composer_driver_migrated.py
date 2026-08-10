"""Part D parity/regression tests for the composer/driver graph migration
(see the migration design doc: `compose_design_for_goal`/`induce_concern` ->
the Rust `ShapeDecode` Term + `seeds/shape_decode_loop.json`; `ground_concern`'s
7-way dispatch -> `seeds/composer_dispatch.json`'s seeded `composer_pick`
Program; `QuestionDriver.drive` -> the graph-resident `question_driving` seed +
reflex).

These tests reuse `tests/fixtures/composer_driver_parity/capture.py`'s own
`capture_*` functions verbatim (the SAME code that produced the frozen
fixtures) so they exercise the REAL migrated Python
(`reflective_faculty.compose_design_for_goal` / `induce_concern` /
`ground_concern`, `question_driver.QuestionDriver.drive`), which are thin
shims driven through the Rust `ShapeDecode` Term / the seeded rule loop
(`native.run_rules()` / `tick()`), not a Python reimplementation of the
matching logic. See `tests/fixtures/composer_driver_parity/README.md` for the
fixtures' own determinism notes.

Two masked (non-bug) instabilities, both explained where they're masked below:

  - `driver.json`'s `gap_path.emission.subgoal_is_wall` — a `wiki_local`
    title-search nondeterminism for the bare word "would", pre-existing and
    documented in the fixture README (not a driver/comprehension issue).
  - `induce_concern.json`'s uncovered-case `axis_id` — a NodeID string. This
    is an EXPECTED side effect of the migration itself (not nondeterminism):
    post-migration `induce_concern` loads three extra seeds
    (`math_capability_shapes`/`self_design_axis`/`shape_decode_loop`, via
    `_ensure_shape_decode_loop`) before minting, which shifts node-id
    allocation relative to the frozen fixture (captured against the
    PRE-migration Python, which loaded no such seeds before minting).
    Confirmed stable (same value) across repeated fresh-process runs in this
    environment; only the *value* differs from the frozen fixture, no other
    field does.

DELIBERATE SEMANTIC CHANGE (2026-07-02, creator directive "transformation is
quantum change in a specific dimension" — see seeds/shape_decode_loop.json's
v1.2.0 comment and tests/fixtures/composer_driver_parity/README.md):
`sd_decode`'s `ShapeDecode` invocations flip from `wild_objects=true` to
LITERAL, making the new `sd_transform_decode`/`sd_recognize_transformed`
stage load-bearing. `induce_concern.json`'s `covered` case (an object-renamed
match: `part_move`'s `X`/`D` fillers renamed to `Y`/`Z` in the observation)
used to be recognized as an EXACT match (wild_objects wildcarded the object
slots away); it is now recognized-UNDER-A-TRANSFORM instead (status
`recognized_transformed`, a `transform` key with `dims`/`deltas`/`transforms`
recording the X->Y, D->Z substitutions) — `minted` stays `False` and
`covered_by` stays `"part_move"`, so the discriminative-null guarantee this
fixture exists to protect is UNCHANGED; only the recognition PATH (exact vs
transform) is more precise now. The fixture's `covered.result` was
regenerated against the live (post-upgrade) `induce_concern`; `uncovered` and
`parts` are confirmed byte-identical to before (this design never touches
the novel-predicate/no-coverage path). See
`tests/test_transform_decode_migrated.py`'s own organic-pipeline tests for
the general case this one fixture instance is a specific example of.
"""
from __future__ import annotations

import importlib.util
import json
import os

import pytest

pytest.importorskip("substrate_rs")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE_DIR = os.path.join(ROOT, "tests", "fixtures", "composer_driver_parity")


def _load_capture_module():
    spec = importlib.util.spec_from_file_location(
        "composer_driver_parity_capture", os.path.join(FIXTURE_DIR, "capture.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


capture = _load_capture_module()


def _fixture(name: str):
    with open(os.path.join(FIXTURE_DIR, name)) as f:
        return json.load(f)


@pytest.fixture(autouse=True)
def _programs_json_guard():
    """`ground_concern`'s PATH-2 (`generate_from_residual`) calls
    `teach_program` -> `teach(..., category="programs")`, which APPENDS to
    `seeds/programs.json` (persisted host I/O, by design). Snapshot + restore
    the file's exact bytes around every test in this module (the same
    `_ProgramsJsonGuard` precedent `capture.py` itself uses), regardless of
    whether the working tree is already dirty there."""
    guard = capture._ProgramsJsonGuard()
    with guard:
        yield


# ---------------------------------------------------------------------------
# 1 — ShapeDecode parity vs composer.json (all 3 cases). This is the LITERAL
#     path (`wild_objects=False` by default) — must stay byte-identical,
#     unaffected by the `induce_concern` `wild_objects` fix.
# ---------------------------------------------------------------------------
def test_shape_decode_composer_parity():
    result = capture.capture_composer()
    expected = _fixture("composer.json")
    assert result == expected


# ---------------------------------------------------------------------------
# 2 — induce_concern parity vs induce_concern.json: covered -> no mint
#     (recognized_transformed since v1.2.0's literal-decode upgrade —
#     `covered_by` matches and a `transform` reading records the object-slot
#     substitution, see the module docstring's dated note; `minted=False` is
#     the discriminative-null guarantee this case protects, unchanged);
#     uncovered -> CapabilityAxis with matching residual_predicates (axis_id
#     masked, see module docstring).
# ---------------------------------------------------------------------------
def test_induce_concern_parity():
    result = capture.capture_induce_concern()
    expected = _fixture("induce_concern.json")

    assert result["covered"] == expected["covered"], (
        "the covered case must be byte-identical against the fixture: a "
        "wildcard-coverage REGRESSION (recognizing ANY predicate-skeleton "
        "match regardless of consistency) would show up here as minted=True, "
        "and a transform-decode regression would show up as a missing/wrong "
        "'transform' reading or a wrong status")

    result_uncovered = json.loads(json.dumps(result["uncovered"]))
    expected_uncovered = json.loads(json.dumps(expected["uncovered"]))
    result_uncovered["result"].pop("axis_id", None)
    expected_uncovered["result"].pop("axis_id", None)
    assert result_uncovered == expected_uncovered


# ---------------------------------------------------------------------------
# 3 — the DYNAMIC QUANTIZATION loop end-to-end (the new capability the
#     dequantize/dynamic-quantize reframe buys): a partially-covered
#     observation decodes -> mints; codebook growth (a new ShapeSignature
#     covering the residual + the SAME mechanical `codebook_epoch` bump
#     `grow_part_library` performs — the design doc's documented "direct
#     ShapeSignature add" alternative, since authoring via `grow_part_library`
#     itself needs a held Concept definition, orthogonal to what's under
#     test here) re-arms the observation via `sd_redecode` -> re-decodes ->
#     recognizes. Exactly ONE CapabilityAxis is minted throughout (the
#     re-decode must NOT mint a second one).
#
#     DELIBERATE SEMANTIC CHANGE (v1.2.0 literal decode, see the module
#     docstring's dated note): the "move" relation now reuses `part_move`'s
#     OWN literal fillers (`X`/`D`) rather than distinct ones (`P`/`Q`) --
#     under the retired `wild_objects=True` coverage this didn't matter (any
#     filler covered), but literal decode requires an EXACT relation match,
#     so a genuinely partially-covered observation must literally match the
#     covering part on the relations it DOES cover, leaving only the truly
#     novel `zzznew` relation as residual (the case this test is actually
#     about) -- otherwise sd_transform_decode/sd_mint_quantum would (rightly,
#     per the new discriminative semantics) treat the "move" relation's
#     filler mismatch as additional residual too, which is a DIFFERENT test
#     (see test_transform_decode_migrated.py's organic-pipeline test for
#     that). Likewise `part_zzz`'s filler is `X` (matching the observation's
#     own `zzznew` arg literally), not the old wildcard-only placeholder
#     `"ANY"`.
# ---------------------------------------------------------------------------
def test_dynamic_quantization_loop_mints_then_recognizes_on_regrowth():
    from substrate.boot_core import boot_core
    from domains import reflective_faculty as rf

    s, ag = boot_core()
    s.add_node("ShapeSignature", {
        "name": "part_move",
        "signature": json.dumps([["move", "X", "by", "D"], ["stop", "X"]]),
        "kind": "faculty", "faculty": "part_move"})
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)

    baseline_axes = len(list(s.nodes("CapabilityAxis")))

    obs = s.add_node("Observation", {
        "signature": [["move", "X", "by", "D"], ["zzznew", "X"]],
        "key": ["probe_dynamic_quant"], "status": "pending"})
    s.add_edge(ag, "observed", obs)

    native.run_rules()
    status_after_mint = s.node(obs)["attrs"].get("status")
    assert status_after_mint == "minted", (
        "a partially-covered observation ('zzznew' held by nothing) must mint, "
        "not recognize -- the discriminative pair to the covered case in "
        "test_induce_concern_parity above")
    axes_after_mint = len(list(s.nodes("CapabilityAxis")))
    assert axes_after_mint == baseline_axes + 1, "exactly one axis minted"

    minted_axis = next(iter(s.neighbours(obs, "minted")))
    residual_preds = list(s.node(minted_axis)["attrs"].get("residual_predicates") or [])
    assert residual_preds == ["zzznew"]

    # Codebook growth: a new part covering the residual predicate + the SAME
    # mechanical codebook_epoch bump `grow_part_library` performs. Literal
    # decode needs the SAME literal filler ("X") the observation's own
    # residual relation carries -- see the deliberate-change note above.
    s.add_node("ShapeSignature", {
        "name": "part_zzz", "kind": "authored",
        "signature": json.dumps([["zzznew", "X"]]), "concept": "zzz"})
    cur = s.node(ag)["attrs"].get("codebook_epoch") or 0.0
    s.set_attr(ag, "codebook_epoch", float(cur) + 1.0)

    native.run_rules()
    status_after_regrowth = s.node(obs)["attrs"].get("status")
    assert status_after_regrowth == "recognized", (
        "sd_redecode must re-arm the minted observation (status back to pending) "
        "once the codebook_epoch has grown, and sd_decode/sd_recognize must "
        "re-cover it now that the codebook holds a part for 'zzznew'")

    axes_after_regrowth = len(list(s.nodes("CapabilityAxis")))
    assert axes_after_regrowth == baseline_axes + 1, (
        "the re-decode on a now-covered observation must NOT mint a second axis "
        "(the sd_mint_quantum 'already minted' guard holds across re-decodes)")


def test_decoded_status_is_independently_matched_by_recognize_and_mint():
    """`decoded` is a real, separately-matched status in the rule set (not
    merely folded transiently into pending/minted) — verified exactly as the
    seed's own comments say it can be: `sd_recognize` and `sd_mint_quantum`
    are each independently testable against a hand-set `status="decoded"`
    Observation, without going through `sd_decode` at all. This is the
    intermediate leg of the pending -> decoded -> {minted | recognized}
    walk the end-to-end test above exercises naturally (there, one
    `run_rules()` call chains sd_decode + sd_recognize/sd_mint_quantum to a
    full fixpoint within a single call, so `decoded` is not independently
    OBSERVABLE mid-fixpoint from Python — it is independently ADDRESSABLE by
    the rule set, which is what this test proves)."""
    from substrate.boot_core import boot_core
    from domains import reflective_faculty as rf

    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)

    # Both hand-set Observations below also set `decoded_epoch` to the
    # agent's current `codebook_epoch` — real Observations always get this
    # from `sd_decode`'s own effect; skipping it (as a hand-set fixture that
    # starts at "decoded" without ever going through sd_decode would) makes
    # `sd_redecode`'s `Lt(decoded_epoch, codebook_epoch)` compare against a
    # MISSING attr, which is not this test's concern (that rule is unchanged
    # by this migration's fix) and would spuriously re-arm the observation.
    epoch = s.node(ag)["attrs"].get("codebook_epoch") or 0.0

    # sd_recognize's own branch: decoded + empty residual -> recognized.
    obs_r = s.add_node("Observation", {
        "signature": [["move", "P", "by", "Q"]], "key": ["k_decoded_recognize"],
        "status": "decoded", "residual": [], "decoded_epoch": epoch})
    s.add_edge(ag, "observed", obs_r)
    native.run_rules()
    assert s.node(obs_r)["attrs"].get("status") == "recognized"

    # sd_mint_quantum's own branch: decoded + non-empty residual -> minted.
    baseline = len(list(s.nodes("CapabilityAxis")))
    obs_m = s.add_node("Observation", {
        "signature": [["zznovel", "P"]], "key": ["k_decoded_mint"],
        "status": "decoded", "residual": [["zznovel", "P"]], "decoded_epoch": epoch})
    s.add_edge(ag, "observed", obs_m)
    native.run_rules()
    assert s.node(obs_m)["attrs"].get("status") == "minted"
    assert len(list(s.nodes("CapabilityAxis"))) == baseline + 1


# ---------------------------------------------------------------------------
# 4 — ground_concern dispatch parity vs ground_concern.json: the 7
#     relation-head cases install the same-named rules as the fixture; PATH-2
#     (feedback) and the no-cue wall are covered too. Plus the priority-order
#     case: multiple grounded heads present -> the highest-priority composer
#     wins, matching the old ordered if/elif chain (comprehend, priority 1,
#     beats distribute, priority 7 — seeds/composer_dispatch.json).
# ---------------------------------------------------------------------------
def _strip_rule_bookkeeping(obj):
    """Drop ABSOLUTE rule index/count bookkeeping (``rule_idx``,
    ``rule_count_before``/``rule_count_after``) that legitimately shifts when the
    base seed-set grows (the dual-process-core seeds added ~114 rules), while
    keeping the composer's actual DECISION — the minted rule body, ``served_by``,
    and ``rule_count_delta`` — compared. Same masking idiom as ``axis_id``
    (induce_concern) / ``subgoal_is_wall`` (question_driver) above. Per CLAUDE.md
    a baseline is a body, never a count: the old assert baked in ``rule_idx: 20``,
    which any unrelated seed addition breaks."""
    if isinstance(obj, dict):
        return {
            k: _strip_rule_bookkeeping(v)
            for k, v in obj.items()
            if k not in ("rule_idx", "rule_count_before", "rule_count_after")
        }
    if isinstance(obj, list):
        return [_strip_rule_bookkeeping(v) for v in obj]
    return obj


def test_ground_concern_dispatch_parity():
    result = capture.capture_ground_concern()
    expected = _fixture("ground_concern.json")
    # The minted rule body + rule_count_delta (== 1) still compare exactly; only
    # the absolute list positions/counts are masked (they float with the base
    # seed-set, e.g. the dual-process-core rules), so this still fails on a real
    # dispatch regression (wrong rule, wrong delta) but not on seed growth.
    assert _strip_rule_bookkeeping(result) == _strip_rule_bookkeeping(expected)


def test_ground_concern_priority_order_multi_head():
    res = capture._mint_axis_and_ground("induced_multi_head", ["comprehend", "distribute"])
    assert res["installed_rule_names"] == ["comprehend_describe_directive_induced_multi_head"], (
        "both 'comprehend' (priority 1) and 'distribute' (priority 7) ground to "
        "real relation heads here (seeds/composer_dispatch.json) -- the seeded "
        "composer_pick Program's Argmin-by-priority must pick 'comprehension', "
        "matching the OLD 7-way ordered if/elif chain's comprehend-first order")
    assert res["result"]["path"] == "compose_comprehension_rule"
    assert res["result"]["form"] == "comprehension_rule"
    assert res["rule_count_delta"] == 1


# ---------------------------------------------------------------------------
# 5 — QuestionDriver parity vs driver.json for all 6 pack shapes (world/know/
#     meta/compound/contrast/gap_path). Reuses capture.py's pack construction
#     verbatim (ELLIPTIC_PACK, wiki_local know/compound/contrast, the
#     boot_reflective_substrate meta/gap_path substrates) via
#     `capture.capture_driver()`. Masks the one documented unstable field
#     (gap_path's first gap-grounding subgoal's is_wall — wiki_local search
#     nondeterminism, see module docstring / the fixture README).
# ---------------------------------------------------------------------------
def test_question_driver_parity():
    result = capture.capture_driver()
    expected = _fixture("driver.json")

    result_masked = json.loads(json.dumps(result))
    expected_masked = json.loads(json.dumps(expected))
    result_masked["gap_path"]["emission"]["subgoal_is_wall"] = None
    expected_masked["gap_path"]["emission"]["subgoal_is_wall"] = None

    assert result_masked == expected_masked
