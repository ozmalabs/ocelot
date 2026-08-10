"""test_vision_floor_migrated — Stage 1 gates for the developmental
vision floor (donkey=0, the plan's "Stage 1 gates").

Five gates, mirroring the plan's S1 verification:

  1. ChangeDetect byte-parity: a known 3x3 image + 3x3 Sobel-x kernel;
     the Rust Term's valid cross-correlation == scipy.signal.correlate2d
     (mode='valid'). Codifies the T7 Rust self-test as a permanent gate
     (the convolve math is a Rust Term, not cv2).
  2. Tabula-rasa boot: boot_core() + load_seeds_into([... "vision_floor"])
     — NOT the vision_*.json encyclopedic seeds. Ingest a synthetic
     structured image via domains/vision_world.py; tick; the grown kernel
     codebook (sense -kept_kernel-> Kernel, minted by the REUSED
     keep_discriminative_kernel rule from sensory_convolution) contains
     a CENTER-SURROUND-SIGN kernel AND an ORIENTED kernel — the biology
     EMERGED, measured via the kept weights' SIGN STRUCTURE (center vs
     surround opposition; row/col sign gradient), NOT asserted by seed
     name.
  3. Dorsal/ventral dual codebook_scope: two distinct scopes (motion vs
     identity) exist over the one ShapeDecode (VentralScope +
     DorsalScope nodes, distinct pathways); AND the dorsal motion stream
     is FUNCTIONAL — a frame-pair wires prev_frame, vf_temporal_diff
     fires the TemporalDiff Term, producing the event/motion stream.
  4. browser.py rule-driven: worlds/browser.py no longer calls fb_sample
     from Python control flow — the only 'fb_sample' is the RULE-EFFECT
     string inside the agent-authored look-rule (closed loop, the
     test_rule_driven_look.py precedent). The WHEN-to-sample decision is
     the agent's rule, not a host call.
  5. No Python thresholds: scan domains/vision_world.py + the
     vision_floor.json RULES for bare numeric decision thresholds;
     every knob must be graph data (SamplingGeometry attrs /
     TunableParameter), never a Python literal or a rule where-clause
     literal. Findings are collected and reported (the test does not
     paper over a real violation — it surfaces it).

Honesty rule: if the biology did not emerge, the gate FAILS and reports
exactly what was kept — the gate's job is to surface the gap, not hide
it. The known pre-existing migrated-bench failures (POS cold-slab,
NOT vision-related) are expected elsewhere; this file is vision-only.
"""
from __future__ import annotations

import json
import os
import re
import sys

import pytest

pytest.importorskip("substrate_rs")
np = pytest.importorskip("numpy")
scipy_signal = pytest.importorskip("scipy.signal", reason="scipy needed for parity")

from substrate_rs import Attr, Lit, Term, Vec  # noqa: E402

import domains.seed_registry  # noqa: E402,F401 -- populates REGISTRY on import
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains.vision_world import VisionWorld  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VISION_FLOOR_SEED = os.path.join(ROOT, "seeds", "vision_floor.json")
BROWSER_PY = os.path.join(ROOT, "worlds", "browser.py")
VISION_WORLD_PY = os.path.join(ROOT, "domains", "vision_world.py")


# ---------------------------------------------------------------------------
# 1. ChangeDetect byte-parity (Rust Term == scipy valid cross-correlation)
# ---------------------------------------------------------------------------


def test_changedetect_byte_parity_with_scipy_valid():
    """The Rust ChangeDetect Term IS the convolve math (no cv2). Its
    valid cross-correlation of a known 3x3 image against a 3x3 Sobel-x
    kernel must equal scipy.signal.correlate2d(mode='valid') exactly.

    ChangeDetect takes a flat image buffer + a flat kernel + a dims
    Tuple [h, w, kh, kw, stride]; kernel weights are read off a
    graph-resident Kernel node via Attr (the agent OWNS the receptive
    field as graph data). Returns a Tuple<f64> of the valid response,
    row-major.
    """
    s = __import__("substrate_rs").Substrate()
    image = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]], dtype=float)
    kernel = np.array([[1, 0, -1], [2, 0, -2], [1, 0, -1]], dtype=float)
    expected = scipy_signal.correlate2d(image, kernel, mode="valid").flatten().tolist()

    nid = s.add_node("Kernel", {"weights": kernel.flatten().tolist(),
                                "kh": 3.0, "kw": 3.0})
    term = Term(
        "ChangeDetect",
        image_vals=Lit(image.flatten().tolist()),
        kernel_weights=Attr(Lit(nid), "weights"),
        dims=Vec([Lit(3), Lit(3), Lit(3), Lit(3), Lit(1)]),
    )
    resp = list(s.evaluate(term))
    assert len(resp) == len(expected), f"len mismatch {len(resp)} != {len(expected)}"
    assert all(abs(a - b) < 1e-9 for a, b in zip(resp, expected)), (
        f"ChangeDetect != scipy valid: {resp} vs {expected}")


def test_changedetect_stride_and_shape_contract():
    """The T7 contract: out = ((h-kh)/stride+1) * ((w-kw)/stride+1),
    row-major; a stride-2 5x5 / 3x3 case has exactly one output. Also
    documents the VALID (no-pad) note — the output is SMALLER than a
    cv2.filter2D 'same' response, by design."""
    s = __import__("substrate_rs").Substrate()
    image = np.arange(25, dtype=float).reshape(5, 5)
    kernel = np.array([[1, 0, -1], [2, 0, -2], [1, 0, -1]], dtype=float)
    expected = scipy_signal.correlate2d(image, kernel, mode="valid").flatten().tolist()
    nid = s.add_node("Kernel", {"weights": kernel.flatten().tolist(),
                                "kh": 3.0, "kw": 3.0})
    term = Term(
        "ChangeDetect",
        image_vals=Lit(image.flatten().tolist()),
        kernel_weights=Attr(Lit(nid), "weights"),
        dims=Vec([Lit(5), Lit(5), Lit(3), Lit(3), Lit(1)]),
    )
    resp = list(s.evaluate(term))
    assert len(resp) == 9, f"expected 3x3=9 valid outputs, got {len(resp)}"
    assert all(abs(a - b) < 1e-9 for a, b in zip(resp, expected))


# ---------------------------------------------------------------------------
# 2. Tabula-rasa boot — biology EMERGED (measured by sign structure)
# ---------------------------------------------------------------------------


def _structured_image():
    """A synthetic 6x6 image sliced into 4 labelled 3x3 windows
    (stride 3): W0 a bright centre blob (centre-surround responds), W1
    a vertical edge (oriented), W2 a horizontal edge (oriented), W3 a
    uniform patch. Each window becomes its own labelled Field, so
    keep_discriminative_kernel's spread metric varies across them — the
    kept kernels are chosen by image statistics, not by hand."""
    img = np.zeros((6, 6), dtype=float)
    # W0 (rows 0-2, cols 0-2): bright centre -> centre-surround response.
    img[1, 1] = 9.0
    # W1 (rows 0-2, cols 3-5): vertical edge (dark left, bright right).
    img[0:3, 5] = 9.0
    # W2 (rows 3-5, cols 0-2): horizontal edge (bright top, dark bottom).
    img[3, 0:3] = 9.0
    # W3 (rows 3-5, cols 3-5): uniform mid-gray.
    img[3:6, 3:6] = 3.0
    return img


def _is_center_surround(weights):
    """Sign-structure classifier (NOT a name check): a kernel is
    center-surround-sign iff the centre weight has the OPPOSITE sign to
    the mean of the 8-element surround AND the centre is the larger-
    magnitude element — the DoG / LGN ON-or-OFF-centre shape biology
    rediscovers. Matches the sensory_convolution 'centre_surround' node
    by its SIGN PATTERN, not its name."""
    w = list(weights)
    if len(w) != 9:
        return False
    centre = w[4]
    surround = [w[i] for i in range(9) if i != 4]
    smean = sum(surround) / 8.0
    if abs(centre) < 1e-9 or abs(smean) < 1e-9:
        return False
    return (centre > 0) != (smean > 0) and abs(centre) > abs(smean)


def _is_oriented(weights):
    """Sign-structure classifier (NOT a name check): a kernel is
    oriented-sign iff there is a consistent sign gradient along ONE
    axis — sum(left col) and sum(right col) have opposite signs
    (vertical-edge / Gabor), OR sum(top row) and sum(bottom row) have
    opposite signs (horizontal-edge). This is the V1-simple-cell shape
    (a bar at a preferred orientation). Captures edge_axis1 / onset /
    offset / diagonal by SIGN PATTERN, not by name."""
    w = list(weights)
    if len(w) != 9:
        return False
    k = [w[0:3], w[3:6], w[6:9]]
    left = sum(k[r][0] for r in range(3))
    right = sum(k[r][2] for r in range(3))
    top = sum(k[0][c] for c in range(3))
    bottom = sum(k[2][c] for c in range(3))
    vert = (left > 0) != (right > 0) and abs(left - right) > 1e-9
    horiz = (top > 0) != (bottom > 0) and abs(top - bottom) > 1e-9
    return vert or horiz


def test_floor_selects_discriminative_kernels_from_the_designed_pool():
    """Boot ONLY the core + vision_floor closure (vision_floor depends_on
    sensory_convolution / shape_decode_loop / motor_core / reflex_core —
    NOT the vision_*.json encyclopedic prose seeds). Ingest one
    structured image; tick. The kept codebook (sense -kept_kernel->
    Kernel) contains a center-surround-sign kernel and an oriented-sign
    kernel.

    RENAMED + RESCOPED 2026-07-16 (was
    `test_tabula_rasa_boot_grows_center_surround_and_oriented_kernels`,
    billed as "THE HEADLINE GATE ... biology EMERGED from image
    statistics"). That claim is RETRACTED and this test no longer makes
    it. What it actually gates is SELECTION FROM A HAND-DESIGNED POOL:

      * `sensory_convolution` ships six `designed: 1.0` kernels, two of
        them literally `centre_surround` (DoG weights) and `edge_axis1`
        (oriented). No rule anywhere mints a Kernel, so the pool never
        grows — the assertions below find what the seed planted.
      * `keep_discriminative_kernel` gates on response VARIANCE across
        fields, not on structure: injected garbage kernels are kept just
        as readily as the biological ones.
      * The sign classifiers above cannot support an emergence claim
        either way — random Gaussian kernels pass them ~50-75% of the
        time, and an ideal Gabor FAILS `_is_oriented`. They are kept
        here only because they do pin the two SEEDED kernels by shape
        rather than by name, which is all this test now claims.

    Genuine growth (mint-on-residual + Oja's rule) lives in
    `seeds/vision_growth.json`; it is measured spectrally, against a
    random-kernel control AND a raw-image-patch control, in
    `tests/test_vision_growth_migrated.py`. See "The T9/T11 retraction"
    in VISION_DEVELOPMENT_ARC.md."""
    s, agent = boot_core()
    load_seeds_into(s, agent, ["vision_floor"])

    # Sanity: the encyclopedic vision_*.json prose seeds are NOT loaded.
    installed = {s.node(n)["attrs"].get("id") for n in s.nodes("Seed")}
    assert "vision_perception" not in installed
    assert "vision_foundation" not in installed
    assert "vision_floor" in installed

    vw = VisionWorld(s, agent)
    img = _structured_image()
    vw.ingest(img.flatten().tolist(), 6, 6, kh=3, kw=3, stride=3)

    steps = s.tick(10_000)
    assert steps >= 1, "tick made no progress — vision_floor rules never fired"

    kept = vw.kept_kernels()
    assert len(kept) > 0, (
        "no kernel was kept — keep_discriminative_kernel never fired")

    # Every kept kernel is one of the six SEEDED, hand-designed ones: the
    # pool has no other members, because no rule mints a Kernel. Pinning
    # this makes the test's real scope explicit — if growth ever lands in
    # this seed, this assertion is what will (correctly) fail.
    assert all(s.node(kn)["attrs"].get("designed") == 1.0 for kn, _, _ in kept), (
        "a non-designed kernel appeared in vision_floor's kept codebook — "
        "growth now exists here and this SELECTION-scoped test must be "
        "re-scoped (see seeds/vision_growth.json)")

    cs = [(kn, w) for kn, w, _ in kept if w is not None and _is_center_surround(w)]
    ori = [(kn, w) for kn, w, _ in kept if w is not None and _is_oriented(w)]
    assert cs, (
        f"no CENTER-SURROUND-SIGN kernel was kept from the designed pool; "
        f"kept = {[(name, list(w)) for _, w, name in kept]}")
    assert ori, (
        f"no ORIENTED-SIGN kernel was kept from the designed pool; "
        f"kept = {[(name, list(w)) for _, w, name in kept]}")
    # Classified by SIGN STRUCTURE rather than by seed name, so a renamed
    # kernel with the same shape still passes. NOTE this is a weak
    # property, NOT evidence of emergence: random kernels pass these
    # classifiers ~50-75% of the time (see the docstring).
    assert _is_center_surround(list(cs[0][1]))
    assert _is_oriented(list(ori[0][1]))


# ---------------------------------------------------------------------------
# 3. Dorsal/ventral dual codebook_scope
# ---------------------------------------------------------------------------


def test_dual_codebook_scopes_exist_and_motion_stream_is_functional():
    """Dorsal (motion) and ventral (identity) are functionally distinct:
    two scope nodes over the one ShapeDecode (VentralScope +
    DorsalScope, distinct pathways). AND the dorsal motion stream
    FIRES — a frame-pair wires prev_frame, vf_temporal_diff runs the
    TemporalDiff Term, producing the event/motion stream (b-a). Motion
    is BETWEEN frames (cross-frame), never in-frame coords."""
    s, agent = boot_core()
    load_seeds_into(s, agent, ["vision_floor"])
    vw = VisionWorld(s, agent)

    img = _structured_image()
    f1 = vw.ingest(img.flatten().tolist(), 6, 6, kh=3, kw=3, stride=3)
    s.tick(10_000)

    # Second frame + wire the temporal chain the vf_temporal_diff rule
    # matches on (img -prev_frame-> prev).
    img2 = img.copy()
    img2[1, 1] = 0.0      # the centre-surround peak disappears
    img2[0:3, 5] = 0.0    # the vertical edge moves
    f2 = vw.ingest(img2.flatten().tolist(), 6, 6, kh=3, kw=3, stride=3)
    s.add_edge(f2, "prev_frame", f1)
    s.tick(10_000)

    # (a) two distinct scopes exist over the ShapeDecode.
    ventral = [(n, s.node(n)["attrs"]) for n in s.nodes("VentralScope")]
    dorsal = [(n, s.node(n)["attrs"]) for n in s.nodes("DorsalScope")]
    assert len(ventral) >= 1 and len(dorsal) >= 1, (
        "dual codebook_scope not present — expected VentralScope + DorsalScope")
    v_path = ventral[0][1].get("pathway")
    d_path = dorsal[0][1].get("pathway")
    assert v_path != d_path, (
        f"the two scopes are not distinct: ventral={v_path} dorsal={d_path}")

    # (b) the dorsal motion stream is FUNCTIONAL: vf_temporal_diff fired
    # the TemporalDiff Term and produced a motion stream on the current
    # frame (the temporal face of ChangeDetect, "process deltas before
    # pixels").
    a2 = s.node(f2)["attrs"]
    assert a2.get("has_motion") == 1.0, (
        "vf_temporal_diff never fired — the dorsal motion stream is "
        "declarative-only, not functional")
    motion = a2.get("motion")
    assert motion is not None and len(motion) > 0, "motion stream is empty"
    # TemporalDiff is b-a: the disappearing peak -> a negative delta there.
    assert any(v < -1e-6 for v in motion), (
        "motion stream has no negative delta — TemporalDiff didn't compute b-a")


# ---------------------------------------------------------------------------
# 4. browser.py rule-driven look (no host fb_sample)
# ---------------------------------------------------------------------------


def test_browser_look_is_rule_driven_not_host_fb_sample():
    """worlds/browser.py no longer calls fb_sample from Python control
    flow — the WHEN-to-sample decision is the agent's own look-rule
    (the composed wants_look shape, test_rule_driven_look.py precedent).
    The ONLY 'fb_sample' in the file is the RULE-EFFECT string inside
    the agent-authored look-rule's effects list, never a live
    `.fb_sample(` method call. Detected by tokenising: a real call is a
    NAME 'fb_sample' immediately preceded by '.' and followed by '(';
    inside a string literal 'fb_sample' is a STRING token, not a NAME,
    so it doesn't false-trigger."""
    src = open(BROWSER_PY, encoding="utf-8").read()
    calls = _find_fb_sample_calls(src)
    assert not calls, (
        "browser.py calls fb_sample from Python live code — the look is "
        "NOT rule-driven (CLAUDE.md violation): " + repr(calls))
    # The rule-effect form DOES appear (the agent's own look-rule fires
    # fb_sample as an EFFECT, not a host call).
    assert '"fb_sample"' in src, (
        "expected the rule-driven look-rule's fb_sample EFFECT string "
        "to be present in browser.py")


def _find_fb_sample_calls(src: str) -> list:
    """Return [(line, col)] for every live Python `.fb_sample(` call
    (a NAME 'fb_sample' preceded by OP '.' and followed by OP '(').
    String/comment occurrences are not NAME tokens, so they are ignored."""
    import io as _io
    import tokenize
    try:
        toks = list(tokenize.tokenize(_io.BytesIO(src.encode("utf-8")).readline))
    except (tokenize.TokenError, IndentationError):
        return []
    trivial = {tokenize.ENCODING, tokenize.NEWLINE, tokenize.NL,
               tokenize.INDENT, tokenize.DEDENT, tokenize.COMMENT,
               tokenize.ENDMARKER}
    real = [(t) for t in toks if t.type not in trivial]
    calls = []
    for i, t in enumerate(real):
        if t.type == tokenize.NAME and t.string == "fb_sample":
            prev = real[i - 1] if i > 0 else None
            nxt = real[i + 1] if i + 1 < len(real) else None
            if (prev is not None and prev.type == tokenize.OP and prev.string == "."
                    and nxt is not None and nxt.type == tokenize.OP and nxt.string == "("):
                calls.append((t.start[0], t.start[1]))
            elif (nxt is not None and nxt.type == tokenize.OP and nxt.string == "("):
                # bare fb_sample( call (no preceding '.') — also a host call
                calls.append((t.start[0], t.start[1]))
    return calls


# ---------------------------------------------------------------------------
# 5. No Python thresholds — scan + report (does not paper over)
# ---------------------------------------------------------------------------


def test_no_python_thresholds_in_vision_floor_rules_or_adapter(capsys):
    """Every knob is graph data (SamplingGeometry attrs / TunableParameter),
    never a Python literal or a rule where-clause literal.

    2026-07-20 — REWRITTEN, AND THE REASON MATTERS MORE THAN THE REWRITE.

    The version this replaces was TWO REGEXES, and the gate audit
    (`VISION_GATE_AUDIT_RESULTS.md`) measured it INERT on 4 of 7 threshold
    spellings while it printed `(none — every knob is graph data)` into the
    ORACLE'S OUTPUT ON EVERY RUN. That line is the most-read artifact in the
    arc, and it was a confident absence claim from an instrument that could
    not see most of what it claimed to cover:

      * half of it — the seed where-clause scan — collected findings, PRINTED
        them, and was NEVER ASSERTED. The assert filtered to the other
        category, so that half COULD NOT FAIL.
      * the other half was `\\b(if|elif|while)\\b...` over EXACTLY ONE FILE:
        blind to a name-bound literal, `return x > 0.5`, `min(x, 0.5)`, a
        default argument, an assert, a ternary and a comprehension guard.

    THE CLAIM WAS TRUE AND UNEARNED. Both halves measure clean TODAY (0 and 0,
    checked before this rewrite), so making the gate live costs no count and
    changes no number — it converts an unchecked assertion into a checked one.
    That is the whole edit: the line now means what a reader takes it to mean.

    Category (b) is delegated to `scripts/gate_audit.py`, which checks the
    INVARIANT rather than a spelling of it — *no path runs from an
    author-written value to a decision sink* — via transitive closure over
    bindings (not source-by-token), parent-context sink typing (not
    sink-by-context), and AST identity (not region-by-substring). Its findings
    are TIERED, not filtered: T1 is a chosen cut point and FAILS; T2/T3 and
    UNRESOLVED are REPORTED IN FULL and do not fail, because an untiered flood
    is a gate that cries wolf and gets routed around. UNRESOLVED is never
    dropped — a check that passes with unknown sinks has verified nothing.

    THE STRICTNESS BOUNDARY, STATED BECAUSE A READER WOULD OTHERWISE INFER IT
    WRONG. Positive-controlled by planting one defect per spelling the old
    regex could not see (2026-07-20, supervisor):

        name-bound literal   `_CUT = 0.37; if x > _CUT`   -> T1, FAILS
        return comparison    `return x > 0.42`            -> T1, FAILS
        default argument     `def f(x, cut=0.29)`         -> T1, FAILS
        seed where-clause    a `Lit` in a rule's `where`  -> FAILS (half (a),
                                which in the old gate COULD NOT FAIL AT ALL)
        min/max bound        `min(x, 0.63)`               -> T2, REPORTED,
                                DOES NOT FAIL

    That last row is not an oversight and it is not blindness — the plant is
    printed verbatim with its literal, and it is graded T2 because a clip is
    usually a representation limit. Failing on it would rebuild the untiered
    flood the audit MEASURED as a broken instrument (`np.clip(a, 0, 255)`
    shouting as loudly as a tuned cut point). **A min/max bound hiding a real
    threshold is a KNOWN RESIDUAL of this gate, visible in its output, not
    silently admitted.** Restoring the tree turns all six green again.
    """
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    from gate_audit import audit_source

    findings = []
    reported = []

    # (a) vision_floor.json RULES — a where-clause literal IS a decision
    # threshold (the floor gates on graph ATTRS like figure_threshold).
    # THIS HALF NOW ASSERTS. It measured 0 before the change.
    seed = json.load(open(VISION_FLOOR_SEED, encoding="utf-8"))
    for rule in seed.get("rules", []):
        where = rule.get("where")
        if where is None:
            continue
        nums = re.findall(r"(?<![\w.\"])-?\d+\.?\d*(?![\w.\"])",
                          json.dumps(where))
        if nums:
            findings.append(
                f"vision_floor rule '{rule.get('name')}' where-clause "
                f"has numeric literal(s): {nums}")

    # (b) domains/vision_world.py — reachability, not a regex.
    vw_src = open(VISION_WORLD_PY, encoding="utf-8").read()
    authored, unresolved = audit_source(vw_src, "domains/vision_world.py")
    for f in authored:
        line = (f"vision_world.py:{f.lineno} [{f.tier}] {f.expr} "
                f"({f.detail})")
        (findings if f.tier == "T1" else reported).append(line)
    for f in unresolved:
        reported.append(f"vision_world.py:{f.lineno} [UNRESOLVED] {f.expr} "
                        f"({f.detail}) — COUNTED, NOT DROPPED")

    with capsys.disabled():
        print("\n[no-python-thresholds scan — reachability, not regex]")
        print("  checked: vision_floor.json where-clauses (asserted) + "
              "domains/vision_world.py (author-value -> decision-sink paths)")
        for f in findings:
            print("  VIOLATION -", f)
        for r in reported:
            print("  reported  -", r)
        if not findings and not reported:
            print("  (none — CHECKED by reachability, incl. the name-bound, "
                  "return, min/max and default-arg spellings the previous "
                  "regex could not see. FAILS on T1 + seed literals; a "
                  "min/max bound is reported, not failed.)")

    assert not findings, (
        "author-written values reach decision sinks (§13 / CLAUDE.md): "
        + "; ".join(findings))


# ---------------------------------------------------------------------------
# 6. Region-as-belief — interior inherited (not painted per-point) +
#    contradiction splits (creator steer #2, "fill as belief, not painting")
# ---------------------------------------------------------------------------


def test_region_as_belief_interior_inherited_and_contradiction_splits():
    """REGION-AS-BELIEF gate (creator steer #2). A Region is a persistent
    observation BELIEF (the quanta_navigation precedent: unknown=absence,
    first-class; the map is a belief, not per-cell storage). Two assertions,
    both against graph state (no Python decision):

      (a) after exposure + a figure signal, a Region belief forms whose
          interior is NOT sampled per-point — only the Region node + its
          boundary (cy/cx/drow/dcol) + grounding_label + confidence exist.
          NO per-interior-patch nodes are minted under the Region (the
          Region IS the label for its interior; interior inherited, not
          painted).

      (b) a contradictory residual WITHIN a held Region (contradiction_residual
          > contradiction_threshold, graph data) SPLITS it: a new
          CapabilityAxis is minted for the sub-region (sd_mint_quantum
          precedent) AND the original Region's interior belief is revised
          (interior_inherited -> 0.0; split=1.0).

    The figure-ground signal (f.residual) and the contradiction signal
    (r.contradiction_residual) are upstream-populated preconditions (the
    stage0-2 prediction-error currency, exactly like sd_decode reads
    obs.signature which induce_concern sets). The RULES decide: vf_figure_ground
    mints the Region belief; vf_surface_labelling binds the grounding_label;
    vf_contradiction_split mints the CapabilityAxis + revises the belief.
    """
    s, agent = boot_core()
    load_seeds_into(s, agent, ["vision_floor"])
    vw = VisionWorld(s, agent)
    img = _structured_image()
    vw.ingest(img.flatten().tolist(), 6, 6, kh=3, kw=3, stride=3)
    s.tick(10_000)  # kernels emerge (keep_discriminative_kernel)

    # The figure-ground signal = prediction residual (stage0-2 surprise
    # currency, upstream-populated like sd_decode reads obs.signature).
    # Set a residual on one Field exceeding figure_threshold (0.5) — the
    # precondition vf_figure_ground reads. The rule DECIDES to mint a
    # Region belief; this only sets the upstream signal.
    fields = list(s.nodes("Field"))
    assert fields, "no Fields minted by ingest"
    fig_field = fields[0]
    s.set_attr(fig_field, "residual", 0.9)
    s.tick(10_000)

    # (a) A Region belief formed: a Region node exists with interior_inherited,
    # boundary geometry (cy/cx/drow/dcol), grounding_label, confidence.
    regions = list(s.nodes("Region"))
    assert regions, (
        "no Region belief formed — vf_figure_ground didn't mint a Region "
        "(the region-as-belief semantics didn't emerge)")
    r = regions[0]
    ra = s.node(r)["attrs"]
    assert ra.get("interior_inherited") == 1.0, (
        f"Region interior_inherited != 1.0 — the interior is not marked as "
        f"inherited belief: {ra}")
    assert ra.get("cy") is not None and ra.get("cx") is not None, (
        f"Region has no boundary geometry (cy/cx): {ra}")
    assert ra.get("drow") is not None and ra.get("dcol") is not None, (
        f"Region has no boundary half-extents (drow/dcol): {ra}")
    assert ra.get("grounding_label") is not None, (
        f"Region has no grounding_label (hypothesis H) — vf_surface_labelling "
        f"didn't bind the ventral codebook entry: {ra}")
    assert ra.get("confidence") is not None, (
        f"Region has no confidence: {ra}")

    # The interior is NOT sampled per-point: the Region IS the label for its
    # interior. There are NO per-interior-patch nodes under the Region (the
    # only Patch nodes are the sensory-convolution input patches under
    # Fields, not interior-sample patches under Regions).
    region_patches = []
    for rn in s.nodes("Region"):
        for nbr in s.neighbours(rn, "has_patch"):
            region_patches.append(nbr)
        for nbr in s.neighbours(rn, "has_interior_patch"):
            region_patches.append(nbr)
    assert not region_patches, (
        f"per-interior-patch nodes exist under a Region — the interior is "
        f"NOT inherited-as-belief (it was painted per-point): {region_patches}")

    # (b) Contradiction splits: a residual WITHIN the held Region contradicting
    # H (contradiction_residual > contradiction_threshold, graph data) mints
    # a new CapabilityAxis (the sub-region quantum = split) and revises the
    # original Region's interior belief (interior_inherited -> 0.0).
    axes_before = len(list(s.nodes("CapabilityAxis")))
    s.set_attr(r, "contradiction_residual", 0.95)  # > contradiction_threshold (0.8)
    s.tick(10_000)
    axes_after = len(list(s.nodes("CapabilityAxis")))
    assert axes_after > axes_before, (
        "contradiction did not mint a CapabilityAxis — vf_contradiction_split "
        "didn't fire (the region did not split)")
    ra2 = s.node(r)["attrs"]
    assert ra2.get("interior_inherited") != 1.0, (
        f"the original Region's interior belief was not revised after the "
        f"split (interior_inherited still 1.0): {ra2}")
    assert ra2.get("split") == 1.0, (
        f"the Region was not marked split: {ra2}")
    # The sub-region axis is wired to the Region via has_subregion.
    subregion_axes = s.neighbours(r, "has_subregion")
    assert subregion_axes, (
        "the split CapabilityAxis is not wired to the Region via has_subregion")


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-q"]))
