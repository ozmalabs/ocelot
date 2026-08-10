"""Gates for the SD-LOOP VISION rung (seeds 18000-18999).

PREREG: `VISION_SDLOOP_PREREG.md` (+ ADDENDUM, the orbit law).
RESULTS: `VISION_SDLOOP_RESULTS.md`. RUNNER: `scripts/sdloop_vision_measure.py`.

PROTOCOL §12: run by explicit file name, never `-k vision` (which substring-matches
"pro**vision**al").
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import domains.reflective_faculty as rf  # noqa: E402
import domains.sdloop_vision as SV  # noqa: E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402

pytest.importorskip("numpy")


def _sdloop_boot():
    s, ag = boot_core()
    native = rf._native_eval2(s)
    load_seeds_into(s, ag, ["vision_sdloop"])
    if s.node(ag)["attrs"].get("codebook_epoch") is None:
        s.set_attr(ag, "codebook_epoch", 0.0)
    return s, ag, native


def _mints(s):
    return SV.codebook_state(s)["mints"]


# --------------------------------------------------------------------------- #
#  PROTOCOL §9 — the seed ships INERT
# --------------------------------------------------------------------------- #
def test_seed_is_inert_without_vq_observations():
    """`load_all_seeds` GLOBS seeds/*.json, so vision_sdloop auto-loads into EVERY boot.
    `vq_grow_quantum` is guarded on `obs.vq == 1`, which nothing but this rung's adapter
    sets — so on any other boot it cannot match and installs nothing."""
    s, ag, native = _sdloop_boot()
    before = SV.codebook_state(s)
    obs = s.add_node("Observation", {                 # a NON-vq observation
        "signature": [["cell", 0, 0, "red"]], "key": ["not_vq"],
        "dim_types": ["pred", "coord:r", "coord:c", "val"], "status": "pending"})
    s.add_edge(ag, "observed", obs)
    native.run_rules()
    grown = [n for n in s.nodes("ShapeSignature")
             if s.node(n)["attrs"].get("vq_grown") == 1.0]
    assert grown == [], "vq_grow_quantum fired on a non-vq Observation — the seed is NOT inert"
    assert SV.codebook_state(s)["latent_dims"] == before["latent_dims"]


# --------------------------------------------------------------------------- #
#  THE ENGINE DEFECT this rung found — pinned so it cannot rot silently
# --------------------------------------------------------------------------- #
def test_shapesignature_named_by_StringConcat_LOADS_into_the_codebook():
    """**FIXED 2026-07-17.** This gate previously pinned the DEFECT; it now pins the fix.

    The defect: `StringConcat` evaluates to `Value::Surface(Text)` — term.rs in its own
    words, *"evaluate() can't intern new Syms, the same reason StringConcat returns Surface
    rather than Str"* — while `load_parts` (shape_decode.rs) read the codebook name as
    `let Value::Str(name_sym) = &nv else { continue }`, with **no Surface arm**. A
    ShapeSignature whose `name` a RULE built by concatenation was silently skipped: no
    error, no warning, the part simply was not in the codebook and every later observation
    re-minted against a codebook that never grew. This rung hit it first-hand — all four
    LATTICE orientations minted, which reads exactly like *"the core loop cannot fold
    orientation"* when it was a harness artifact. **No gate caught it; a human noticed 0°
    and 180° are the same bar and it minted twice.**

    THE FIX (`str_shaped` / `string_attr_or_panic` in shape_decode.rs): the reader now
    accepts BOTH `Str` and `Surface(Text)` — the SAME contract `graph_rules.rs::as_str`,
    `term.rs::eq_with_string_coercion`, and this file's own `td_val_to_string` already
    implemented. A `Str` name reads byte-identically to before; a name that is present but
    NOT string-shaped now **panics** instead of vanishing (see the companion test below).

    Its predecessor's own words were *"the day it is fixed, this gate fires and the
    workaround can be revisited"* — it fired, and this is that revision.
    """
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    sig = [["on", 0, 0], ["on", 0, 1], ["on", 1, 0]]

    # A part whose name is a real interned Str -> LOADS.
    s.add_node("ShapeSignature", {"name": "str_named", "kind": "faculty",
                                  "faculty": "str_named", "signature": json.dumps(sig)})
    r = native.evaluate({"type": "ShapeDecode", "goal": {"type": "Lit", "value": sig}})
    assert r.get("covered_count") == 3, "an interned-Str-named part must load"

    # The SAME part, named via StringConcat by a rule -> silently DROPPED.
    s2, ag2 = boot_core()
    native2 = rf._native_eval2(s2)
    rf._ensure_shape_decode_loop(s2, native2, ag2)
    src = s2.add_node("Observation", {"signature": [list(x) for x in sig], "key": ["k1"],
                                      "status": "inert_probe"})
    s2.add_edge(ag2, "observed", src)
    native2.add_rule({
        "name": "probe_concat_name", "match_type": "Observation",
        "match": [["ag", "observed", "obs"]],
        "where": {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "obs"},
                                      "key": "status"}, "b": {"type": "Lit", "value": "inert_probe"}},
        "effects": [
            ["add_node", "ss", "ShapeSignature", {
                "name": {"__term__": {"type": "StringConcat", "parts": [
                    {"type": "Lit", "value": "concat_"},
                    {"type": "IndexAt", "seq": {"type": "Attr", "node": {"type": "Var", "name": "obs"},
                                                "key": "key"}, "index": {"type": "Lit", "value": 0}}]}},
                "kind": "faculty",
                "signature": {"__term__": {"type": "Attr", "node": {"type": "Var", "name": "obs"},
                                           "key": "signature"}}}],
            ["set_attr", "obs", "status", "probe_done"]],
    })
    native2.run_rules()
    made = [n for n in s2.nodes("ShapeSignature")
            if str(s2.node(n)["attrs"].get("name", "")).startswith("concat_")]
    assert made, "the rule must have CREATED the node"
    r2 = native2.evaluate({"type": "ShapeDecode", "goal": {"type": "Lit", "value": sig}})
    assert r2.get("covered_count") == 3, (
        "REGRESSION: a StringConcat-named ShapeSignature must be VISIBLE to load_parts. "
        "Getting 0/None here means the Surface(Text) arm has been lost from "
        "`str_shaped` — the codebook silently stops growing for any part a RULE names, "
        "which is what nearly produced a false paradigm negative for this rung.")


def test_a_codebook_name_of_the_WRONG_TYPE_is_LOUD_not_silently_skipped():
    """**The generalisation, and the more valuable half of the fix.**

    The type fix alone would leave the disease: `continue`-on-unexpected-type is a SILENT
    WRONG ANSWER. It is the same shape as `.get('Name','')` returning `''`, as `osi()`'s
    `if (a+b) > 1e-9 else 0.0` scoring a DEAD cell a flawless floor (§1.1), and as `Pick`
    silently returning one of N (now `PickUnique`, which panics — and caught the very next
    author within hours).

    So an unhandled value type must ERROR, not skip. The line is INAPPLICABLE vs MALFORMED:
    an ABSENT attr is a legitimate skip (not every node of the type is a part), but an attr
    that is PRESENT and unreadable is a graph the loader cannot honour, and silence there is
    indistinguishable from the part not existing — which is precisely the failure that cost
    this rung a near-miss false negative.
    """
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    sig = [["on", 0, 0], ["on", 0, 1], ["on", 1, 0]]
    # `name` is an Int — not string-shaped, and not "inapplicable": malformed.
    s.add_node("ShapeSignature", {"name": 12345, "kind": "faculty", "faculty": "x",
                                  "signature": json.dumps(sig)})
    with pytest.raises(BaseException) as ei:
        native.evaluate({"type": "ShapeDecode", "goal": {"type": "Lit", "value": sig}})
    msg = str(ei.value)
    assert "not a string-shaped Value" in msg, (
        "the loader must NAME the offending attr and value, not skip it: got " + msg[:200])


# --------------------------------------------------------------------------- #
#  §1 clause 1 — the FLOOR must MINT
# --------------------------------------------------------------------------- #
def test_scrambled_support_mints_every_time():
    """A loop that mints nothing is DEAD, not smart (FM-0). Unstructured support ->
    no held shape explains it -> every observation mints."""
    s, ag, native = _sdloop_boot()
    rng = np.random.default_rng(18001)
    for i in range(6):
        cells = rng.choice(256, size=40, replace=False)
        sig = [["on", int(p) // 16, int(p) % 16] for p in cells]
        SV.ingest(s, ag, sig, "scram_%d" % i)
        native.run_rules()
    assert _mints(s) == 6, "scrambled input must mint EVERY time — the floor proves the loop is alive"


# --------------------------------------------------------------------------- #
#  The headline behaviour, on synthetic exact-lattice input (no retina needed)
# --------------------------------------------------------------------------- #
def test_exact_lattice_rotation_is_recognized_zero_mint_with_a_latent_dimension():
    """The rotated-tromino precedent, on THIS rung's own encoding + growth rule:
    an L-shape and its exact 90deg lattice rotation cost ONE quantum, not two."""
    s, ag, native = _sdloop_boot()
    L = [["on", 0, 0], ["on", 0, 1], ["on", 1, 0]]
    SV.ingest(s, ag, L, "L_base")
    native.run_rules()
    assert _mints(s) == 1

    ROT = [["on", 0, 0], ["on", 0, 1], ["on", 1, 1]]   # L rotated by 90 on the lattice
    o2 = SV.ingest(s, ag, ROT, "L_rot")
    native.run_rules()
    r = SV.read_outcome(s, o2)
    assert _mints(s) == 1, "an exact lattice rotation must mint NOTHING (it is a transform)"
    assert r["status"] == "recognized_transformed"
    assert r["covered_by"] == "L_base", "must be explained AS the held shape"
    assert r["generator"] == "rotation90"
    assert "latent:rotation90" in SV.codebook_state(s)["latent_names"]
    assert r["dim_checked"] == 1, "proof rung 1 ran and FAILED first (Occam order preserved)"


def test_vq_grow_quantum_is_load_bearing():
    """§1 clause 5 / §13.2: toggle the growth rule; D must be non-zero. Without it the
    codebook cannot grow from the loop's own mints and the SAME shape re-mints forever."""
    L = [["on", 0, 0], ["on", 0, 1], ["on", 1, 0]]
    ROT = [["on", 0, 0], ["on", 0, 1], ["on", 1, 1]]

    s, ag, native = _sdloop_boot()                      # growth ON
    for k, sig in (("a", L), ("b", ROT)):
        SV.ingest(s, ag, sig, "on_%s" % k)
        native.run_rules()
    on_mints = _mints(s)

    s2, ag2 = boot_core()                               # growth OFF (seed not loaded)
    native2 = rf._native_eval2(s2)
    rf._ensure_shape_decode_loop(s2, native2, ag2)
    for k, sig in (("a", L), ("b", ROT)):
        SV.ingest(s2, ag2, sig, "off_%s" % k)
        native2.run_rules()
    off_mints = _mints(s2)

    assert on_mints == 1 and off_mints == 2
    assert abs(on_mints - off_mints) > 0, "D == 0 => decorative => STOP (§13.2)"


# --------------------------------------------------------------------------- #
#  THE ORBIT LAW (PREREG-2) — the rung's headline, and its honest scope
# --------------------------------------------------------------------------- #
def test_orbit_law_arithmetic_matches_the_measured_mint_counts():
    """`predicted_orbits` is computed from the HELD generators, never fitted. These are the
    numbers the confirmatory run hit on 10/10 fresh seeds with zero variance."""
    from sdloop_vision_measure import predicted_orbits
    for N, expected in ((2, 1), (3, 2), (4, 2), (6, 2), (12, 4), (8, 3), (9, 5), (36, 10)):
        ths = [i * 180.0 / N for i in range(N)]
        assert predicted_orbits(ths) == expected, "orbit law wrong at N=%d" % N


def test_orbit_law_asymptote_is_a_bounded_fold_NOT_a_dimension():
    """**The scope that kills the naive positive.** The held group has order 4, so orbits
    are at most 4 and mints -> N/4. A TRUE orientation dimension would give O(1) mints at
    every N. Orientation did NOT become a dimension; the square lattice's symmetry group
    performed a bounded <=4x fold and the remainder minted."""
    from sdloop_vision_measure import predicted_orbits
    for N in (12, 36, 72, 180):
        ths = [i * 180.0 / N for i in range(N)]
        got = predicted_orbits(ths)
        assert got >= N / 4.0, "orbit count can never beat N/4 — the group has order 4"
        assert got > 1, "mints must GROW with N: this is not a dimensional collapse"
