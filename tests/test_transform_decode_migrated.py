"""Loop-level tests for the design 'transform-as-quantum-delta' (2026-07-02
creator directive, see the scratchpad TRANSFORM_DESIGN.md): "Transformation
isn't transformation. It's quantum change in a specific dimension." Extends
`seeds/shape_decode_loop.json` (Part B) with `sd_transform_decode` /
`sd_recognize_transformed` (new rules) and an extended `sd_mint_quantum`
guard, backed by the new Rust `TransformDecode` Term (`runners/dsl/src/
shape_decode.rs`, being built in parallel — see the module-level skip
below). `domains/reflective_faculty.py::induce_concern`'s Part C read-back
for the new `recognized_transformed` terminal status is also exercised here.

WHY THESE TESTS HAND-SET `status="decoded"` + `residual` DIRECTLY (bypassing
`sd_decode`/the real `ShapeDecode` Term) rather than starting every case
from `status="pending"`: this is the SAME "independently testable against
hand-set attrs" convention `tests/test_composer_driver_migrated.py::
test_decoded_status_is_independently_matched_by_recognize_and_mint` already
uses for `sd_recognize`/`sd_mint_quantum`, and it sidesteps a real
architectural fact worth recording plainly: `sd_decode`'s OWN residual
(computed via `ShapeDecode(..., wild_objects=True)`, UNCHANGED by this
design) wildcards every non-predicate slot of each held part before
scoring, so it treats ANY observation sharing a held part's predicate
skeleton (same predicates + arities) as fully COVERED regardless of what
its argument values actually are (verified empirically against the live
`ShapeDecode` Term while building this suite: an object-slot substitution
and a numeric-slot shift both drove `residual` to `()` immediately, and an
internally-INCONSISTENT value assignment across relations sharing one
predicate did too — `Covers` has no cross-relation consistency constraint).
Consequently `obs.residual` (the exact gate `sd_transform_decode`/
`sd_mint_quantum` read) can only ever be non-empty when some relation's
PREDICATE is absent from the entire codebook — and `TransformDecode` never
transforms the predicate slot, so whenever it WOULD find an explaining
base candidate (same predicate multiset, aligned, differing only in
value/numeric slots), `sd_decode`'s strictly-weaker wildcard check would
already have found (a) covering candidate(s) first and zeroed the residual
before `sd_transform_decode` ever saw it. So the real `induce_concern` ->
`sd_decode` pipeline can't organically feed `sd_transform_decode` a
residual it will explain — this is reported honestly in the task's final
summary, not hidden. What we CAN and DO test rigorously, exactly like the
established convention: the LOOP-LEVEL rule logic in isolation, by
supplying `status="decoded"` + a `residual` value directly. That is
precisely the seam `sd_transform_decode`'s own `where` clause reads
(`Count(obs.residual) > 0`, nothing about how `residual` got there), so
these tests exercise the real seeded rules (real `TransformDecode` Term
evaluation, real fixpoint `run_rules()`), not a re-implementation.

EXACTLY-ONE-MINT DISCIPLINE (the hard constraint): `sd_mint_quantum`'s
`where` clause requires `transform_checked==1 AND transform_explained!=1`
(see the seed). Because `run_rules()` runs every rule to a full fixpoint
within ONE call, and `sd_transform_decode`'s own guard (`status=="decoded"
AND residual>0 AND transform_checked!=1`) fires on the VERY FIRST pass a
decoded+residual observation is seen, `transform_checked` is ALWAYS set
(to 1) before `sd_mint_quantum`'s guard can ever evaluate true for that
observation — there is no ordering in which `sd_mint_quantum` could apply
its old (pre-design) two-clause guard alone and mint BEFORE
`sd_transform_decode` gets a chance, because the new clauses are additional
requirements (an AND), not an alternative path: `transform_checked` starts
unset (falsy, `Not(Eq(_,1))` true) on every fresh decoded+residual
observation, which is *sd_mint_quantum's own new precondition to fire* —
so until `sd_transform_decode` has run at least once for that observation,
`sd_mint_quantum` cannot match at all, transiently or otherwise. This is
proved empirically below (test 1/2/5's assertion of zero axes throughout)
and was also proved directly at the guard level while authoring this seed
(hand-set `transform_checked=1, transform_explained=1` -> `sd_mint_quantum`
provably does not fire, zero axes, independent of whether
`sd_recognize_transformed` itself is installed).
"""
from __future__ import annotations

import json

import pytest

pytest.importorskip("substrate_rs")

from substrate.boot_core import boot_core
from domains import reflective_faculty as rf


def _term_decode_live() -> bool:
    """Cheap probe: is the Rust `TransformDecode` Term callable yet? Mirrors
    the polling probe used while authoring this suite
    (`s._inner.evaluate({"type": "TransformDecode", ...}, {})` ->
    `UnknownTermType` means not yet). A clean module-wide skip (not a
    fabricated pass) is the honest response while Part A (the Rust Term,
    built in parallel — see CLAUDE.md's Rust/Python split) hasn't landed in
    the installed wheel yet."""
    s, ag = boot_core()
    native = s._inner
    try:
        native.evaluate(
            {"type": "TransformDecode",
             "goal": {"type": "Lit", "value": [["a", "b"]]}}, {})
        return True
    except ValueError as e:
        if "UnknownTermType" in str(e):
            return False
        raise


if not _term_decode_live():
    pytest.skip(
        "TransformDecode Term not yet landed (Part A pending in parallel — "
        "runners/dsl/src/shape_decode.rs::eval_transform_decode does not "
        "exist yet in the currently-installed substrate_rs wheel); "
        "seeds/shape_decode_loop.json's sd_transform_decode/"
        "sd_recognize_transformed rules are authored and install-clean "
        "(skipped with a loud warning, exactly like sd_decode was before "
        "ShapeDecode landed) but cannot fire without it. Honest skip, not "
        "a faked pass.",
        allow_module_level=True)


def _boot():
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    return s, ag, native


def _add_part(s, name, signature, kind="faculty"):
    attrs = {"name": name, "signature": json.dumps(signature), "kind": kind}
    if kind == "faculty":
        attrs["faculty"] = name
    else:
        attrs["concept"] = name
    return s.add_node("ShapeSignature", attrs)


def _observe_decoded(s, ag, *, signature, key, residual, decoded_epoch):
    """Hand-build a `status="decoded"` Observation (bypassing `sd_decode`'s
    real wild-covered residual computation — see the module docstring for
    why) and wire it `ag -observed-> obs`, ready for
    `sd_transform_decode`/`sd_recognize_transformed`/`sd_mint_quantum` to
    take over from `native.run_rules()`."""
    obs = s.add_node("Observation", {
        "signature": signature, "key": [key], "status": "decoded",
        "residual": residual, "decoded_epoch": decoded_epoch})
    s.add_edge(ag, "observed", obs)
    return obs


def _epoch(s, ag):
    return s.node(ag)["attrs"].get("codebook_epoch") or 0.0


def _axes(s):
    return len(list(s.nodes("CapabilityAxis")))


# `eval_transform_decode`'s symbolic-substitution branch
# (runners/dsl/src/shape_decode.rs, ~lines 776-800) builds each `subst`
# dimension's delta pairs from `sorted_h`/`sorted_o` (the HELD part's parsed
# signature vs. the observation). The observation side (`o`) always carries
# a REAL Sym (`goal` evaluates through the ordinary Term evaluator, per this
# module's own top-of-file interner-constraint doc). The HELD side (`h`)
# comes from `load_parts` parsing the ShapeSignature's JSON-string
# `signature` via `json_to_value_scoped`/`local_sym`, which returns a REAL
# Sym only if the string is ALREADY interned somewhere (crucially,
# including via `goal`'s own just-completed evaluation, since `goal` runs
# BEFORE the parts are compared) -- otherwise it fabricates a placeholder
# Sym "safe" only for internal scoring, per that same doc: "Parsed
# part-signature content is used ONLY for internal scoring ... and is NEVER
# placed in the output." `sub_pairs` at shape_decode.rs:794-800 USED TO push
# `h.clone()` straight into the output `transforms`/`deltas` Value tree
# whenever the held ("from") value of a substitution does NOT independently
# appear anywhere in the observation -- exactly the common case for a real
# substitution (the old label is gone, not merely relabelled to itself
# elsewhere), panicking `pyo3_runtime.PanicException: index out of bounds:
# ... index is 4294967295` inside `sym.rs:67` the moment the fabricated
# placeholder Sym for "X" was later resolved (e.g. converting the Dict to a
# Python value).
#
# FIXED (this pass): `eval_transform_decode` now runs the held-side value
# of every `subst` pair through a new `resolve_scoped_output` helper before
# it reaches the output Dict -- a real Sym (found via `Interner::lookup`
# inside `local_sym`) passes through unchanged, a placeholder is rewritten
# to `Value::Surface(Text, ..)` (the same output-text side-channel `surf`/
# `surf_string` already use), which needs no interner lookup at all. A
# dedicated cargo regression test (`shape_decode::transform_decode_tests::
# scoped_local_placeholder_from_value_never_reaches_output`) reproduces this
# exact repro against a JSON-string-signature codebook entry (the shape
# every seed-loaded part actually takes; the existing cargo tests all built
# their held signatures as a native `Value::Tuple`, which never touches
# `json_to_value_scoped`/`local_sym` at all -- why they never caught this).
# The 3 tests below that construct this "from value vanishes" shape no
# longer need an xfail marker; kept as plain assertions, now green.


# ---------------------------------------------------------------------------
# 1 — transform-substitution: a single symbolic role substituted uniformly
#     across BOTH relations of a held 2-relation shape (dim 1, the object
#     slot; slot 0 the predicate is untouched) -> recognized_transformed,
#     ZERO CapabilityAxis minted, a Transform node records dim 1 + base.
#
#     This is exactly the "from value vanishes" shape that used to trip the
#     Rust bug documented above (X -> Y where "X" never otherwise appears
#     in the observation) -- the FAITHFUL representation of the design's
#     own illustrative "single-pair substitution {X -> Y}" semantics, now
#     green now that Part A is fixed (`resolve_scoped_output`).
# ---------------------------------------------------------------------------
def test_transform_substitution_recognized_no_mint():
    s, ag, native = _boot()
    _add_part(s, "part_move_track", [["move", "X", "by", "D"], ["stop", "X"]])
    baseline_axes = _axes(s)

    sig = [["move", "Y", "by", "D"], ["stop", "Y"]]
    obs = _observe_decoded(s, ag, signature=sig, key="probe_subst",
                            residual=sig, decoded_epoch=_epoch(s, ag))
    native.run_rules()

    at = s.node(obs)["attrs"]
    assert at.get("transform_checked") == 1
    assert at.get("transform_explained"), (
        "a single-pair substitution (X->Y) uniform across both relations, "
        "predicate untouched, must be EXPLAINED")
    assert at.get("status") == "recognized_transformed"
    assert at.get("covered_by") == "part_move_track"
    assert _axes(s) == baseline_axes, "recognition-under-transformation must mint NOTHING"

    t_node = next(iter(s.neighbours(obs, "has_transform")))
    t_at = s.node(t_node)["attrs"]
    assert list(t_at.get("dims") or []) == [1], "the object slot (dim 1) is the only transformed dimension"
    assert t_at.get("base") == "part_move_track"
    assert t_at.get("source") == "transform_decode"


# ---------------------------------------------------------------------------
# 2 — numeric shift (translate): a uniform additive delta on one numeric
#     slot across two relations sharing a predicate -> recognized_transformed,
#     zero mint, dim/shift recorded.
# ---------------------------------------------------------------------------
def test_numeric_shift_recognized_no_mint():
    s, ag, native = _boot()
    _add_part(s, "part_at", [["at", "A", 3], ["at", "B", 5]])
    baseline_axes = _axes(s)

    sig = [["at", "A", 5], ["at", "B", 7]]     # uniform +2 on slot 2
    obs = _observe_decoded(s, ag, signature=sig, key="probe_shift",
                            residual=sig, decoded_epoch=_epoch(s, ag))
    native.run_rules()

    at = s.node(obs)["attrs"]
    assert at.get("transform_explained"), "a uniform +2 numeric shift must be EXPLAINED"
    assert at.get("status") == "recognized_transformed"
    assert at.get("covered_by") == "part_at"
    assert _axes(s) == baseline_axes

    t_node = next(iter(s.neighbours(obs, "has_transform")))
    t_at = s.node(t_node)["attrs"]
    assert list(t_at.get("dims") or []) == [2], "the numeric slot (dim 2) is the only transformed dimension"
    deltas = list(t_at.get("deltas") or [])
    assert deltas and deltas[0] == 2, f"expected a +2 shift, got {deltas!r}"


# ---------------------------------------------------------------------------
# 3 — discriminative null: an INCONSISTENT per-dimension change (the same
#     held role "X" would have to map to TWO different observed values
#     across the two relations -- not a function) must NOT be explained as
#     a transform -> falls through to sd_mint_quantum, exactly ONE
#     CapabilityAxis minted (the pre-existing path), transform_explained
#     stays falsy. This is what protects codebook growth: a scrambled
#     residual must still be able to mint.
# ---------------------------------------------------------------------------
def test_scrambled_observation_is_discriminative_null_and_mints():
    s, ag, native = _boot()
    _add_part(s, "part_move_track2", [["move", "X", "by", "D"], ["stop", "X"]])
    baseline_axes = _axes(s)

    # X -> Y in the "move" relation but X -> Z in "stop": no single function
    # explains both -> NOT a transform.
    sig = [["move", "Y", "by", "D"], ["stop", "Z"]]
    obs = _observe_decoded(s, ag, signature=sig, key="probe_scrambled",
                            residual=sig, decoded_epoch=_epoch(s, ag))
    native.run_rules()

    at = s.node(obs)["attrs"]
    assert at.get("transform_checked") == 1
    assert not at.get("transform_explained"), "an inconsistent per-dimension mapping must NOT be explained"
    assert at.get("status") == "minted", "the discriminative null falls through to the OLD mint path"
    assert _axes(s) == baseline_axes + 1, "exactly ONE axis minted"
    assert len(list(s.neighbours(obs, "has_transform"))) == 0, "no Transform node for an unexplained residual"


# ---------------------------------------------------------------------------
# 4 — novel-predicate observation still mints (the fixture semantics
#     test_composer_driver_migrated.py depends on): a predicate the codebook
#     has never seen can never be a "transform" of anything (slot 0 is
#     never transformable) -> transform_explained stays falsy -> mints,
#     exactly like the pre-design behaviour.
# ---------------------------------------------------------------------------
def test_novel_predicate_still_mints():
    s, ag, native = _boot()
    _add_part(s, "part_move_track3", [["move", "X", "by", "D"], ["stop", "X"]])
    baseline_axes = _axes(s)

    sig = [["zznovel", "P"]]
    obs = _observe_decoded(s, ag, signature=sig, key="probe_novel_pred",
                            residual=sig, decoded_epoch=_epoch(s, ag))
    native.run_rules()

    at = s.node(obs)["attrs"]
    assert not at.get("transform_explained"), "a wholly novel predicate can never be a transform"
    assert at.get("status") == "minted"
    assert _axes(s) == baseline_axes + 1
    residual_preds = list(s.node(next(iter(s.neighbours(obs, "minted"))))["attrs"].get("residual_predicates") or [])
    assert residual_preds == ["zznovel"]


# ---------------------------------------------------------------------------
# 5 — grid miniature (the ARC story in miniature): cells-as-relations
#     ("cell", row, col, value); the observation is the held grid
#     TRANSLATED by +1 row (col held fixed) AND RECOLOURED (a red<->blue
#     swap, a 2-pair functional mapping on the value slot -- still ONE
#     dimension per the design's ranking rule) -> dims [1, 3] (row, value),
#     within max_dims=2 (mirrors Part A's own grid cargo-test story:
#     "dims [1,3]"), recognized as a transform, zero mint. A second,
#     SCRAMBLED grid (one cell recoloured inconsistently with the rest)
#     mints instead -- the discriminative pair.
# ---------------------------------------------------------------------------
def _grid(row0):
    return [["cell", row0, 0, "red"], ["cell", row0, 1, "blue"],
            ["cell", row0 + 1, 0, "blue"], ["cell", row0 + 1, 1, "red"]]


def test_grid_translate_and_recolour_recognized_no_mint():
    s, ag, native = _boot()
    _add_part(s, "part_grid", _grid(0))
    baseline_axes = _axes(s)

    # +1 row shift, red<->blue swap, col (dim 2) untouched.
    sig = [["cell", 1, 0, "blue"], ["cell", 1, 1, "red"],
           ["cell", 2, 0, "red"], ["cell", 2, 1, "blue"]]
    obs = _observe_decoded(s, ag, signature=sig, key="probe_grid",
                            residual=sig, decoded_epoch=_epoch(s, ag))
    native.run_rules()

    at = s.node(obs)["attrs"]
    assert at.get("transform_explained"), "a row-shift + colour-swap grid must be EXPLAINED within max_dims=2"
    assert at.get("status") == "recognized_transformed"
    assert at.get("covered_by") == "part_grid"
    assert _axes(s) == baseline_axes

    t_node = next(iter(s.neighbours(obs, "has_transform")))
    dims = sorted(list(s.node(t_node)["attrs"].get("dims") or []))
    assert dims == [1, 3], f"expected row (1) + value (3) dims transformed, col (2) untouched; got {dims!r}"


def test_scrambled_grid_mints():
    s, ag, native = _boot()
    _add_part(s, "part_grid2", _grid(0))
    baseline_axes = _axes(s)

    # Same row shift, but ONE cell breaks the red<->blue function (goes to
    # "green" instead) -> no single functional mapping explains the value
    # slot -> NOT a transform.
    sig = [["cell", 1, 0, "blue"], ["cell", 1, 1, "red"],
           ["cell", 2, 0, "green"], ["cell", 2, 1, "blue"]]
    obs = _observe_decoded(s, ag, signature=sig, key="probe_grid_scrambled",
                            residual=sig, decoded_epoch=_epoch(s, ag))
    native.run_rules()

    at = s.node(obs)["attrs"]
    assert not at.get("transform_explained")
    assert at.get("status") == "minted"
    assert _axes(s) == baseline_axes + 1


# ---------------------------------------------------------------------------
# 6 — re-decode interplay: an observation already `recognized_transformed`
#     re-arms once the codebook grows (a new ShapeSignature EXACTLY
#     matching the observation's own signature + the same mechanical
#     `codebook_epoch` bump `grow_part_library` performs), and the REAL
#     (already-landed) `sd_decode`/`ShapeDecode` path now wild-covers it
#     exactly -> plain "recognized" wins over the transform reading;
#     transform_checked/transform_explained are cleared.
#
#     Reaching `recognized_transformed` in the first place needs the SAME
#     "X -> Y, X vanishes" substitution shape as test 1 -- green now that
#     Part A is fixed.
# ---------------------------------------------------------------------------
def test_redecode_interplay_exact_match_supersedes_transform():
    s, ag, native = _boot()
    _add_part(s, "part_move_track4", [["move", "X", "by", "D"], ["stop", "X"]])
    baseline_axes = _axes(s)

    sig = [["move", "Y", "by", "D"], ["stop", "Y"]]
    obs = _observe_decoded(s, ag, signature=sig, key="probe_redecode",
                            residual=sig, decoded_epoch=_epoch(s, ag))
    native.run_rules()
    assert s.node(obs)["attrs"].get("status") == "recognized_transformed"
    assert _axes(s) == baseline_axes

    # Codebook growth: a new part EXACTLY matching the observation's own
    # signature + the mechanical codebook_epoch bump.
    _add_part(s, "part_move_track4_exact", sig, kind="authored")
    cur = s.node(ag)["attrs"].get("codebook_epoch") or 0.0
    s.set_attr(ag, "codebook_epoch", float(cur) + 1.0)

    native.run_rules()
    at = s.node(obs)["attrs"]
    assert at.get("status") == "recognized", (
        "sd_redecode must re-arm a recognized_transformed observation on codebook "
        "growth, and the real (already-landed) sd_decode/ShapeDecode wild-covered "
        "path must now find it fully covered -- exact beats transform")
    assert at.get("transform_checked") in (0, None, 0.0), "transform_checked must be cleared on re-arm"
    assert at.get("transform_explained") in (0, None, 0.0, False), "transform_explained must be cleared on re-arm"
    assert _axes(s) == baseline_axes, "the re-decode must not mint anything either"


# ---------------------------------------------------------------------------
# 7 — Part C: induce_concern's mechanical read-back for the new
#     "recognized_transformed" terminal status.
#
#     Before this pass, `induce_concern`'s own pending-entrypoint pipeline
#     called `sd_decode` with `wild_objects=True`, which wild-covered a
#     role-substitution observation directly (residual empty) -- so the
#     REAL pipeline always resolved to plain `recognized`, never
#     `recognized_transformed`, for any case this design can explain as a
#     transform, and this test could only prove the new branch by hand-
#     setting `status="decoded"` (part (a)), with part (b) locking in the
#     wild-coverage finding as a documented, honest gap.
#
#     `sd_decode` now runs LITERAL (see seeds/shape_decode_loop.json's
#     dated v1.2.0 comment + CLAUDE.md's "the transform stage is now
#     load-bearing" note) specifically so this is no longer a gap: part
#     (b) below drives the REAL pending pipeline end-to-end and proves the
#     organic path reaches `recognized_transformed` with a real Transform
#     node -- the same before/after `test_composer_driver_migrated.py`'s
#     updated covered-case fixture records for its own covered case.
# ---------------------------------------------------------------------------
def test_induce_concern_reads_back_recognized_transformed():
    s, ag, native = _boot()
    _add_part(s, "part_move_track5", [["move", "X", "by", "D"], ["stop", "X"]])
    sig = [["move", "Y", "by", "D"], ["stop", "Y"]]

    # (a) unit-test the new branch directly: hand-build the
    # "recognized_transformed" Observation the seeded rules would produce,
    # then read it back through induce_concern's OWN internals it shares
    # with every other status branch (`_resolve_agent`, `sub`/`native`) --
    # only the final status dispatch differs per observation, so calling
    # the module's public entrypoint on an ALREADY-existing Observation
    # node isn't possible (it always mints a fresh one), but reading the
    # exact same graph shape `induce_concern` reads is: `sub.node(obs)`,
    # `sub.neighbours(obs, "has_transform")`. This is the identical
    # read pattern lines 907-931 of reflective_faculty.py use for the
    # "recognized" / "minted" branches (already parity-tested via
    # test_composer_driver_migrated.py) -- Part C adds a third, structurally
    # identical branch for "recognized_transformed".
    obs = _observe_decoded(s, ag, signature=sig, key=["k_part_c"],
                            residual=sig, decoded_epoch=_epoch(s, ag))
    native.run_rules()
    at = s.node(obs)["attrs"]
    assert at.get("status") == "recognized_transformed"

    transform_node = next(iter(s.neighbours(obs, "has_transform")))
    t_at = s.node(transform_node)["attrs"]
    expected_transform = {"dims": list(t_at.get("dims") or []),
                           "deltas": list(t_at.get("deltas") or []),
                           "transforms": list(t_at.get("transforms") or []),
                           "base": t_at.get("base")}
    assert expected_transform["dims"] == [1]
    assert expected_transform["base"] == at.get("covered_by") == "part_move_track5"

    # (b) the real public entrypoint, same signature, fresh substrate: the
    # organic pending -> decoded -> recognized_transformed pipeline, driven
    # end to end through `induce_concern` itself (real `sd_decode` with
    # literal coverage -> real `sd_transform_decode` -> real
    # `sd_recognize_transformed`), not a hand-set `status="decoded"` shortcut.
    s2, ag2 = boot_core()
    _add_part(s2, "part_move_track5", [["move", "X", "by", "D"], ["stop", "X"]])
    res = rf.induce_concern(s2, sig, name_hint="probe_induce_concern_transformed")
    assert res["minted"] is False
    assert res.get("covered_by") == "part_move_track5"
    assert "transform" in res, (
        "literal sd_decode (v1.2.0) leaves a real residual for a role "
        "substitution -- sd_transform_decode must explain it and "
        "induce_concern's recognized_transformed branch must read the "
        "Transform node back as a 'transform' key")
    assert res["transform"]["dims"] == [1]
    assert res["transform"]["base"] == "part_move_track5"


# ---------------------------------------------------------------------------
# 8 — v1.2.0 literal-decode discriminative win, driven end to end through the
#     REAL organic pipeline (`induce_concern`'s `add_node Observation
#     status="pending"` -> `native.run_rules()` -> read-back -- NOT the
#     hand-set-`status="decoded"` shortcut tests 1-6 use). Three outcomes,
#     same held part, on three fresh substrates so each starts from the same
#     codebook: (a) an EXACT-match observation -> plain `recognized`;
#     (b) a CONSISTENT role substitution -> `recognized_transformed`, minting
#     NOTHING beyond what (a) already mints; (c) an INCONSISTENT substitution
#     -> `minted`, exactly ONE CapabilityAxis MORE than (a)/(b) -- the
#     discriminative win this whole design exists for: under the old
#     wild_objects=True coverage this case was silently wild-covered
#     (residual always empty) and could NEVER mint, per this module's own
#     docstring finding above.
#
#     NOTE on the axis-count comparison being RELATIVE, not absolute zero:
#     `boot_core()`'s `self_design_axis` seed (a declared dependency of
#     `shape_decode_loop`, unrelated to this design) mints its own one-time
#     bookkeeping CapabilityAxis the first time `run_rules()` sees a fresh
#     agent with no `has_self_design_axis` edge yet -- this fires identically
#     regardless of what `induce_concern` observes, so it shows up in EVERY
#     one of these three fresh-agent scenarios alike. Comparing (b) and (c)
#     against (a) as a CONTROL (same one-time side effect, same starting
#     codebook) isolates the signal this design actually owns: sd_mint_quantum
#     minting zero axes for (a)/(b) and exactly one for (c).
# ---------------------------------------------------------------------------
def test_organic_pipeline_literal_decode_discriminates_transform_from_novelty():
    held = [["move", "X", "by", "D"], ["stop", "X"]]

    def _run(sig, hint):
        s, ag = boot_core()
        _add_part(s, "part_organic", held)
        res = rf.induce_concern(s, sig, name_hint=hint)
        return res, _axes(s)

    # (a) exact match -> recognized (the control: whatever axis count this
    # leaves is the "mints nothing of our own" baseline for this scenario
    # family, self-design bookkeeping included).
    res_exact, axes_exact = _run(held, "probe_organic_exact")
    assert res_exact["minted"] is False
    assert res_exact.get("covered_by") == "part_organic"
    assert "transform" not in res_exact, "an exact match is `recognized`, not `recognized_transformed`"

    # (b) consistent substitution -> recognized_transformed, ZERO
    # CapabilityAxis beyond the control.
    res_subst, axes_subst = _run([["move", "Y", "by", "D"], ["stop", "Y"]], "probe_organic_subst")
    assert res_subst["minted"] is False
    assert res_subst.get("covered_by") == "part_organic"
    assert "transform" in res_subst, "a consistent role substitution must be explained as a transform"
    assert res_subst["transform"]["dims"] == [1]
    assert axes_subst == axes_exact, (
        "recognition-under-transformation must mint NOTHING beyond the "
        "exact-match control")

    # (c) inconsistent substitution -- the SAME held part, but "X" would have
    # to map to two different observed values across the two relations (no
    # single function) -- NOT a transform -> falls through to sd_mint_quantum
    # -> exactly ONE CapabilityAxis more than the control. This is the
    # discriminative win: under wild_objects=True this observation's residual
    # was ALWAYS empty (silently wild-covered), so it could never reach here.
    res_inc, axes_inc = _run([["move", "Y", "by", "D"], ["stop", "Z"]], "probe_organic_inconsistent")
    assert res_inc["minted"] is True, (
        "an inconsistent per-dimension substitution must mint -- the "
        "discriminative win literal decode (v1.2.0) restores")
    assert "transform" not in res_inc
    assert axes_inc == axes_exact + 1, (
        "exactly ONE CapabilityAxis more than the exact-match/transform "
        "control -- the sd_mint_quantum path, not silently wild-covered")
