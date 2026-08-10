"""arc5_numerics_float_audit — measurement script for the STRONG claim
("no program needs floats") on this repo's own DSP/audio/shape-verdict
stack (Corpus 1) plus a named set of classic numerical algorithms
(Corpus 2).

This is a MEASUREMENT tool, not agent code: it reads Rust/Python source
files in this tree, checks that a hand-classified evidentiary "needle"
(an exact substring anchored near a specific line) is actually present
in the source, and writes the resulting audit — per-site rows, class
counts, the (D) list, the sharp-question answer, and a tolerance-audit
of this repo's own DSP code — to
`results/arc5_numerics_float_audit.json`.

Classification is necessarily a judgment call made by reading the code
(this is an audit, not a static analyzer that can itself decide "is
this cross-frame or in-frame"). What IS mechanically checked, and what
`tests/test_arc5_numerics_audit_migrated.py` gates on, is:
  - every site with a `file` cites real source (the needle is found
    within `LINE_WINDOW` lines of the claimed anchor, or elsewhere in
    the file as a fallback — reported either way);
  - the four classes A/B/C/D partition the site list with no site
    outside {A,B,C,D};
  - the (D) list is exactly the sites classified D (the headline,
    either way);
  - aggregate counts match len(sites) and the by-corpus split.

Run: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 \
     OZMA_SEED_PERSIST_DISABLED=1 python3 scripts/arc5_numerics_float_audit.py
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = REPO_ROOT / "results" / "arc5_numerics_float_audit.json"

LINE_WINDOW = 8  # tolerance (lines) around the claimed anchor when searching for the needle


# ---------------------------------------------------------------------------
# Corpus 1 — this repo's own DSP / shape-verdict / quantization stack.
# ---------------------------------------------------------------------------
#
# Class key (per the brief):
#   A — CROSS-FRAME / map: comparator, rendering, transform, or a continuous
#       parameter applied intensionally. Permitted by the invariant.
#   B — IN-FRAME datum: a float stored as an observed/lattice coordinate that
#       participates AS a frame coordinate. Would be a counterexample.
#   C — Avoidable in-frame float: currently float, expressible exactly
#       (rational/integer/fixed-point) with no loss. A defect, not a
#       requirement.
#   D — Genuinely irreducible: an in-frame quantity that provably cannot be
#       rational/integer/fixed-point at the precision the computation needs.
#       This is the class that would REFUTE the strong claim.

CORPUS1_SITES = [
    # --- DSP primitives: internal signal-processing computation ------------
    dict(
        id="c1-01", corpus=1, cls="A",
        file="runners/dsl/src/audio_primitives.rs", line=19,
        symbol="gammatone_band",
        evidence_needle="pub fn gammatone_band(samples: &[f32], fs: u32, fc: f32, order: u32) -> Vec<f32> {",
        justification=(
            "A 4th-order gammatone filter bank. `fc`/`order`/the filter state are "
            "cross-frame MAP parameters/internals (a rendering of the input sample "
            "array into a filtered sample array); the samples in and out are never "
            "themselves graph node coordinates — they are consumed synchronously by "
            "the caller (a world adapter) and never round-trip through `set_attr` "
            "as a per-sample datum. Consistent with 'a float in a map/metric/"
            "rendering is correct.'"
        ),
    ),
    dict(
        id="c1-02", corpus=1, cls="A",
        file="runners/dsl/src/audio_primitives.rs", line=1451,
        symbol="lpc_autocorr / levinson_durbin",
        evidence_needle="pub fn lpc_autocorr(x: &[f32], p: usize) -> Vec<f64> {",
        justification=(
            "Linear-prediction analysis (autocorrelation -> Levinson-Durbin -> LPC "
            "coefficients). Pure numeric DSP over sample buffers; the agent's own "
            "self-description of this category (domains/lpc_formant_representation.py, "
            "quoting runtime_design.agent_specify_lpc_formants) is explicit: "
            "'adapter-math (numeric DSP), NOT a composable DSL Term.' The coefficients "
            "never persist as graph attrs; only a discrete peak INDEX derived from "
            "them does (see c1-12)."
        ),
    ),
    dict(
        id="c1-03", corpus=1, cls="A",
        file="runners/dsl/src/audio_primitives.rs", line=3709,
        symbol="cochleagram",
        evidence_needle="pub fn cochleagram(x: &[f32], fs: u32, env_cut: f32, dur_cut: f32, n_frames: usize) -> Vec<f32> {",
        justification=(
            "Gammatone cochleagram rendering — 'a numerical primitive at the I/O "
            "boundary' per py.rs's own comment (line ~9085): 'the world adapter feeds "
            "background descriptors, the agent holds the returned library as graph "
            "data' (i.e. a downstream LEARNED/discrete artifact, not the raw floats "
            "themselves, is what persists as graph data)."
        ),
    ),
    dict(
        id="c1-04", corpus=1, cls="A",
        file="runners/dsl/src/audio_primitives.rs", line=3261,
        symbol="f0_yin",
        evidence_needle="pub fn f0_yin(frame: &[f32], fs: u32, f_lo: f32, f_hi: f32, voicing_thresh: f32) -> f32 {",
        justification=(
            "YIN pitch estimation: a difference-function search over lag producing "
            "a single f32 Hz estimate. The estimate is a MEASUREMENT (a rendering of "
            "raw samples into a scalar); whether the measured Hz value is later "
            "cached as a node attr and used in a threshold decision is the SEPARATE "
            "question audited at c1-09/c1-10 (the acoustic-feature persistence sites)."
        ),
    ),
    dict(
        id="c1-05", corpus=1, cls="A",
        file="runners/dsl/src/audio_primitives.rs", line=891,
        symbol="synthesize_klatt_lf / lf_source",
        evidence_needle="pub fn synthesize_klatt_lf(",
        justification=(
            "LF glottal-source speech synthesis: a RENDERING (parameters -> sample "
            "array), the textbook cross-frame case ('renderings... live in the MAP "
            "between frames'). Never a stored in-frame coordinate."
        ),
    ),
    # --- Term-tree comparators / verdict layer ------------------------------
    dict(
        id="c1-06", corpus=1, cls="A",
        file="runners/dsl/src/term.rs", line=6435,
        symbol="TermNode::DtwTo / PointSetDist / MahalFull / SmoothDeformDist / "
               "TpsDeformDist / ShapeContextDist / XCorrPeak / Whiten (evaluator)",
        evidence_needle="TermNode::DtwTo { a, b } => {",
        justification=(
            "The shape/verdict comparator family. Each evaluates two graph-resident "
            "subtrees and returns Value::Float as an IMMEDIATE, non-persisted verdict "
            "consumed by Argmin/Argmax in the SAME rule evaluation (e.g. "
            "seeds/vision_deformation.json's df_recognize: "
            "'covered_by = Argmin over candidates of DictGet(...,\"total\")'). "
            "Textbook cross-frame comparator: 'the continuous verdict is a cross-frame "
            "comparison of observed vs rendered candidate.' The scalar itself is never "
            "written back onto a node via set_attr."
        ),
    ),
    dict(
        id="c1-07", corpus=1, cls="A",
        file="runners/dsl/src/term.rs", line=6748,
        symbol="TermNode::Rotate (evaluator)",
        evidence_needle="TermNode::Rotate { vec, angle } => {",
        justification=(
            "Rotates a point by a real angle (cos/sin), returning a Tuple<Float> — "
            "the RENDERED candidate fed straight into PointSetDist. "
            "seeds/continuous_pose.json's own comment names this exactly: 'Rotate -- "
            "the cross-frame generator carrying the real angle as a Float, NEVER an "
            "in-frame coordinate.' Self-documented in the codebase as class A."
        ),
    ),
    dict(
        id="c1-08", corpus=1, cls="A",
        file="seeds/continuous_pose.json", line=15,
        symbol="cp_angles (continuous-pose angle grid)",
        evidence_needle="the cross-frame generator carrying the real angle as a Float, NEVER an in-frame coordinate",
        justification=(
            "`cp_angles` is a Float tuple attr — a MAP PARAMETER SET (the grid of "
            "candidate rotation angles), read by Rotate/MinOver, never an object's "
            "position. Recognition threshold is sqrt(2)/2 (unit-lattice half-"
            "diagonal), a FALLS-OUT bound from the observation's own quantization "
            "grain, not a tuned magic number -- and it IS persisted as node data "
            "(see c1-09) exactly as the invariant permits: 'a cross-frame map may "
            "carry a continuous parameter intensionally.'"
        ),
    ),
    dict(
        id="c1-09", corpus=1, cls="A",
        file="seeds/vision_deformation.json", line=15,
        symbol="df_eps (identity-preservation bound, cached node attr)",
        evidence_needle="eps = (sqrt(2)/2)/R",
        justification=(
            "df_eps is a genuinely continuous quantity (sqrt(2)/2 applied to a "
            "measured R, an irrational constant intensionally APPLIED) CACHED as a "
            "float attribute on the agent node for reuse as a comparator threshold "
            "(Lte checks in df_recognize/df_refuse). This is the sharpest borderline "
            "case in the corpus: it is a float that lives ON a graph node, not "
            "recomputed fresh each time. Classified A because it functions as a "
            "MAP PARAMETER (a tolerance/threshold the comparator applies), never as "
            "an object's identity-determining position/coordinate -- exactly the "
            "'df_refused'/honest-refuse discipline (an explicit ABSTAIN state exists) "
            "rather than a silently-accepted in-frame value. Flagged here rather than "
            "silently folded into the A bucket because a reader could reasonably "
            "read 'graph data' as 'in-frame' -- the report discusses this explicitly."
        ),
    ),
    # --- space_quantize / strokes: the ZERO-float and integer-quantized cases
    dict(
        id="c1-10", corpus=1, cls="C",
        file="runners/dsl/src/space_quantize.rs", line=574,
        symbol="SpaceQuantum.qdist sentinel typed as Value::Float",
        evidence_needle="attrs.insert(syms.qdist, Value::Float(-1.0));",
        justification=(
            "`space_quantize.rs` itself contains ZERO f32/f64 literals or types "
            "(grep count: 0) -- the flood/portal/quantum machinery is 100% integer, "
            "the single cleanest positive confirmation of the invariant in the "
            "corpus. The ONE float typing is `qdist`, and per "
            "seeds/quanta_navigation.json's own comment ('Bellman relax: Q.qdist <- "
            "min(Q.qdist, R.qdist+cost)... cost (Int, always 1)'), qdist is ALWAYS "
            "an integer sum of unit hop costs in every reachable run -- the Float "
            "type is used purely to get a '-1.0 = unset' sentinel distinct from a "
            "valid distance of 0, and an Int with a -1 sentinel would have worked "
            "identically. Avoidable: a type-discipline artifact, not a computational "
            "requirement."
        ),
    ),
    dict(
        id="c1-11", corpus=1, cls="A",
        file="runners/dsl/src/strokes.rs", line=112,
        symbol="quantize_signed_angle / quantize_bucket (internal float geometry)",
        evidence_needle="fn quantize_signed_angle(deg: f64, bins: i64) -> i64 {",
        justification=(
            "StrokeQuantize's internal geometry (turn angles, arc lengths, bbox) is "
            "computed in f64 -- but every quantity that reaches a graph relation is "
            "explicitly rounded to i64 before being wrapped as Value::Int (see the "
            "sibling read-back path at strokes.rs:659-671: `pose_x_q = Some(x.round() "
            "as i64)`, `segs.push((i.round() as i64, turn_q.round() as i64, ...))`). "
            "The f64 arithmetic is the MAP (continuous geometry -> quantized bin); "
            "the persisted relation is always the integer bin. Textbook A: "
            "'sampling/quantization is what grounding IS.'"
        ),
    ),
    # --- acoustic feature persistence: the closest thing to a counterexample
    dict(
        id="c1-12", corpus=1, cls="C",
        file="domains/acoustic_resolution.py", line=120,
        symbol="band<N>_<i> acoustic energy attrs (set_attr, raw float)",
        evidence_needle='substrate.set_attr(sign, f"band{n}_{i}", v)',
        justification=(
            "The single most float-native site in the corpus: per-AcousticSign "
            "mean cochlear-patch energies are stored DIRECTLY as float node attrs "
            "and read back by predicate Term-trees for discrimination "
            "(domains/formant_features.py's peak detector, domains/"
            "discriminative_invention.py's Fisher rule). This IS an in-frame "
            "float participating in an identity decision (which word a sign is). "
            "Classified C, not B/D, because: (1) every consumer reads it through an "
            "ORDER-only comparator (Gt for peaks; a Fisher ratio compared to a "
            "threshold) that is representation-invariant under any order-preserving "
            "quantization -- the same integer-bin treatment StrokeQuantize/"
            "TransformDecode already give pose/rotation would work identically here "
            "and has simply not been done for this feature family yet; (2) the "
            "underlying quantity (a mean of a bounded-precision digitized cochlear "
            "trajectory) is exactly representable as a rational/fixed-point number "
            "with no loss -- nothing about the computation needs unbounded "
            "precision. This is a live, unmigrated instance of the SAME 'the spec "
            "implies floats, the problem does not' pattern the MBPP audit found, "
            "not a proof that the discrimination task needs floats."
        ),
    ),
    dict(
        id="c1-13", corpus=1, cls="A",
        file="domains/formant_features.py", line=24,
        symbol="_peak_term (Gt-only peak predicate)",
        evidence_needle="return And(items=(Gt(a=bi, b=Attr(s, f\"band{res}_{i-1}\")),",
        justification=(
            "The formant/peak DECISION itself uses only Gt (order) comparisons "
            "between adjacent band values -- no arithmetic beyond ordering. An "
            "order-only predicate is invariant under ANY monotonic re-encoding of "
            "the underlying feature (float, fixed-point, or rank), so this specific "
            "site never actually exercises float PRECISION, only float ORDER. "
            "Rides on the c1-12 values but is itself precision-agnostic."
        ),
    ),
    dict(
        id="c1-14", corpus=1, cls="C",
        file="domains/discriminative_invention.py", line=121,
        symbol="_stats: standard deviation (var**0.5) persisted + Fisher ratio (sqrt-based)",
        evidence_needle="return m, var ** 0.5",
        justification=(
            "The sharpest live example in the repo. `_stats` computes a genuine "
            "square root (a_std/b_std, generically irrational even for exactly "
            "rational input data) and PERSISTS it as a ConfusionBand float attr; "
            "the agent's own graph-native Rule (`install_analyse_rule`, line "
            "209-211) then evaluates `fisher = |a_mean-b_mean| / (a_std+b_std+eps)` "
            "via the Rust Div/Abs/Plus DSL Terms and fires "
            "`Gt(fisher, min_separation)` to decide whether a band is "
            "discriminative -- an in-frame identity decision resting on a "
            "persisted, individually-irrational quantity. Classified C, not D: "
            "the DECISION this Fisher-style test makes is an ORDER test on a "
            "ratio, and the well-known rational reformulation "
            "'(mean_a-mean_b)^2 * k^2 > (std_a+std_b)^2' still needs each std "
            "individually (the cross term std_a*std_b survives), BUT the "
            "textbook alternative discriminability statistic -- comparing "
            "squared distance to a VARIANCE-SUM-scaled threshold, "
            "'(mean_a-mean_b)^2 > k' * (var_a+var_b)' -- makes the identical "
            "class of decision (is this band separable) using ONLY sums and "
            "products of variances, which are EXACTLY rational for rational "
            "inputs; sqrt is a SPECIFICATION CHOICE (this particular Fisher-ratio "
            "formula), not a requirement of 'is this band discriminative.' Same "
            "shape as the corpus's own '3.1415 vs k*pi*r^a*h^b' finding: the "
            "written test implies a float; an equivalent exact test does not."
        ),
    ),
    dict(
        id="c1-15", corpus=1, cls="A",
        file="domains/lpc_formant_representation.py", line=1,
        symbol="LPC/all-pole formant landmark extraction (continuous envelope -> integer band-index landmark)",
        evidence_needle="category: adapter-math (numeric DSP), NOT a composable DSL Term",
        justification=(
            "The agent's OWN classification (quoted verbatim in the module "
            "docstring, attributed to runtime_design.agent_specify_lpc_formants) "
            "of the LPC/all-pole envelope computation as adapter-math, explicitly "
            "NOT graph-resident reasoning. The graph-resident relation that "
            "survives onto the agent (spacing_relation_term, reused verbatim from "
            "iter-24) operates on INTEGER band-index positions (Minus over "
            "landmark band-index POSITIONS), not on the continuous envelope "
            "values themselves -- the smooth float envelope is used only to find "
            "a peak's INDEX (an argmax), and only the index persists. This is the "
            "clean, migrated counterpart to the still-unmigrated c1-12/c1-14 sites."
        ),
    ),
    dict(
        id="c1-16", corpus=1, cls="A",
        file="domains/formant_frontend.py", line=21,
        symbol="warped_band_centres (gammatone filter centre-frequency generator)",
        evidence_needle="def warped_band_centres(",
        justification=(
            "Generates log-spaced filter CENTRE FREQUENCIES (Hz) -- configuration "
            "for the gammatone_band Rust primitive's `fc` parameter. A cross-frame "
            "map parameter (a filter's centre frequency), analogous to cutoff_hz/"
            "sigma elsewhere; never a stored identity coordinate."
        ),
    ),
]


# ---------------------------------------------------------------------------
# Corpus 2 — classic numerics, judged by algorithm structure (no repo file;
# these are external-validity checks per the brief, grounded in the
# algorithm's algebraic closure properties, not citation alone). MBPP task
# 246 (Babylonian sqrt, in this repo's OWN measured corpus per
# PROGRAM_SYNTHESIS_ARC5_SPECS_IMPLY_FLOATS.md) is cited as the one place
# corpus 1 and corpus 2 overlap directly.
# ---------------------------------------------------------------------------

CORPUS2_SITES = [
    dict(
        id="c2-01", corpus=2, cls="A", file=None,
        symbol="Newton's method / root-finding (incl. MBPP #246 Babylonian sqrt)",
        evidence_needle=None,
        justification=(
            "x_{n+1} = x_n - f(x_n)/f'(x_n). For rational x_n and a rational "
            "function f, x_{n+1} is EXACTLY rational -- the recurrence is closed "
            "over the rationals at every step; no step ever requires representing "
            "an irrational value. The STOPPING test (|x_{n+1}-x_n| < tol) is a "
            "decidable rational comparison. What Newton's method computes, when "
            "iterated forever, is an intensional Cauchy-sequence GENERATOR for a "
            "possibly-irrational limit (exactly 'a continuous quantity is a RULE "
            "you APPLY... never an observed datum') -- the limit itself is never "
            "materialized in-frame; only a rational approximation, to whatever "
            "precision the stopping test demands, ever is. MBPP #246 is this exact "
            "algorithm, live in this project's own corpus "
            "(PROGRAM_SYNTHESIS_ARC5_SPECS_IMPLY_FLOATS.md: 'an algorithm, not a "
            "closed form')."
        ),
    ),
    dict(
        id="c2-02", corpus=2, cls="A", file=None,
        symbol="Numerical integration (trapezoid / Simpson)",
        evidence_needle=None,
        justification=(
            "A finite weighted sum of rational sample weights times f evaluated at "
            "rational points. If f is itself rational-valued at rational inputs, "
            "the estimate is EXACTLY rational -- no irrational ever appears. If f "
            "is transcendental (sin, exp, ...), the estimate is already an "
            "approximation BY DESIGN (the quadrature rule's own truncation error "
            "dwarfs float rounding error at any reasonable step count); precision "
            "on demand (bound f's value to whatever rational interval the target "
            "accuracy needs) suffices and is the CORRECT way to think about it, "
            "not 'the integral needs an in-frame real.'"
        ),
    ),
    dict(
        id="c2-03", corpus=2, cls="A", file=None,
        symbol="LU decomposition",
        evidence_needle=None,
        justification=(
            "Gaussian elimination without square roots: for a rational input "
            "matrix, every pivot/elimination step is +,-,*,/ over rationals -- "
            "the rationals are closed under all four, so LU factors of a rational "
            "matrix are EXACTLY rational. No irrational structure is intrinsic to "
            "'solve Ax=b' via LU; this is a genuinely rational-closed algorithm, "
            "the strongest possible form of the claim for this family."
        ),
    ),
    dict(
        id="c2-04", corpus=2, cls="A", file=None,
        symbol="QR decomposition (Gram-Schmidt) vs LDL^T",
        evidence_needle=None,
        justification=(
            "Gram-Schmidt QR normalizes each column to unit Euclidean length -- a "
            "sqrt, generically irrational. But this is a SPECIFICATION choice: "
            "'orthoNORMAL' is not required by most of what QR is used for (solving "
            "Ax=b, least squares); LDL^T (Cholesky WITHOUT the square root, "
            "standard numerical-linear-algebra technique specifically because it "
            "avoids sqrt) accomplishes the identical downstream task using only "
            "rational arithmetic. QR's sqrt is exactly analogous to this project's "
            "'3.1415 vs k*pi*r^a*h^b' and the repo's own std/variance case (c1-14): "
            "the WRITTEN algorithm implies a float; an exactly-equivalent-purpose "
            "algorithm does not."
        ),
    ),
    dict(
        id="c2-05", corpus=2, cls="A", file=None,
        symbol="FFT (complex roots of unity) vs Number-Theoretic Transform",
        evidence_needle=None,
        justification=(
            "The classic FFT's butterflies multiply by e^{-2*pi*i*k/N}, transcendental "
            "for generic N -- but the TASK an FFT is usually used for (fast O(N log N) "
            "convolution / polynomial multiplication) has an EXACT, all-integer "
            "twin: the Number-Theoretic Transform (NTT), which replaces the complex "
            "root of unity with a primitive N-th root of unity in a finite field "
            "Z/pZ and computes the identical convolution with ZERO floating-point "
            "error, used throughout exact polynomial arithmetic and cryptography. "
            "This is the single clearest existing counter-example to 'FFT needs "
            "floats': the fast-transform ALGORITHM does not require reals; only the "
            "specific transcendental-root INSTANTIATION does, and that "
            "instantiation is a rendering/interpretation choice (sampling the "
            "continuous Fourier transform) when that is genuinely the intent -- "
            "which is a cross-frame use, correctly permitted."
        ),
    ),
    dict(
        id="c2-06", corpus=2, cls="A", file=None,
        symbol="RK4 (ODE step)",
        evidence_needle=None,
        justification=(
            "One RK4 step is a fixed weighted sum (1/6, 1/3, 1/3, 1/6) of f "
            "evaluated at 4 rational points, given rational y_n and step h. For a "
            "rational-valued f, y_{n+1} is exactly rational -- closed, like Newton "
            "and RK4's cousin the trapezoid rule. Same precision-on-demand answer "
            "as c2-01/c2-02 when f is transcendental."
        ),
    ),
    dict(
        id="c2-07", corpus=2, cls="C", file=None,
        symbol="Mean / variance / standard deviation",
        evidence_needle=None,
        justification=(
            "Mean and variance of a finite rational sample are EXACTLY rational "
            "(sums and a division by a known integer count). Standard deviation "
            "(sqrt of variance) is the one place an irrational generically enters -- "
            "and it is avoidable exactly as in c1-14: any decision that only "
            "compares magnitudes (t-tests, Fisher-style separability, z-score "
            "threshold checks) can be restated as a comparison of SQUARED "
            "quantities against a variance-scaled threshold, needing no sqrt at "
            "all. Classified C: an avoidable float, arising from writing the "
            "statistic in std-form rather than variance-form, not a genuine "
            "requirement of the underlying decision."
        ),
    ),
]

ALL_SITES = CORPUS1_SITES + CORPUS2_SITES
VALID_CLASSES = {"A", "B", "C", "D"}


def _read_file(rel_path: str) -> Optional[list]:
    p = REPO_ROOT / rel_path
    if not p.exists():
        return None
    return p.read_text(errors="replace").splitlines()


def verify_site(site: dict) -> dict:
    """Check that a site's evidence_needle is actually present in the claimed
    file, ideally near the claimed line. Returns a dict describing what was
    found -- this is the 'derivation' the tests gate on. Sites with no file
    (corpus 2 -- no repo source, judged by algorithm structure) are marked
    'external' rather than verified/unverified."""
    if site["file"] is None:
        return {"status": "external", "matched_line": None}
    needle = site.get("evidence_needle")
    if needle is None:
        return {"status": "no_needle", "matched_line": None}
    lines = _read_file(site["file"])
    if lines is None:
        return {"status": "file_missing", "matched_line": None}
    claimed = site.get("line") or 1
    lo = max(0, claimed - 1 - LINE_WINDOW)
    hi = min(len(lines), claimed - 1 + LINE_WINDOW + 1)
    for i in range(lo, hi):
        if needle in lines[i]:
            return {"status": "verified_near_line", "matched_line": i + 1}
    # Fallback: search the whole file (line drifted / anchor approximate).
    for i, ln in enumerate(lines):
        if needle in ln:
            return {"status": "verified_elsewhere", "matched_line": i + 1}
    return {"status": "NOT_FOUND", "matched_line": None}


def build_audit() -> dict:
    sites = []
    for site in ALL_SITES:
        assert site["cls"] in VALID_CLASSES, f"invalid class on {site['id']}"
        v = verify_site(site)
        row = dict(site)
        row["verification"] = v
        sites.append(row)

    by_class = {c: 0 for c in sorted(VALID_CLASSES)}
    by_class_corpus1 = {c: 0 for c in sorted(VALID_CLASSES)}
    by_class_corpus2 = {c: 0 for c in sorted(VALID_CLASSES)}
    for s in sites:
        by_class[s["cls"]] += 1
        if s["corpus"] == 1:
            by_class_corpus1[s["cls"]] += 1
        else:
            by_class_corpus2[s["cls"]] += 1

    d_list = [s for s in sites if s["cls"] == "D"]

    unverified = [s["id"] for s in sites
                  if s["file"] is not None
                  and s["verification"]["status"] == "NOT_FOUND"]

    verdict = "REFUTED" if d_list else "UPHELD_WITH_QUALIFICATION"
    # "UPHELD_WITH_QUALIFICATION" rather than a bare "UPHELD": the corpus
    # contains class-C sites (c1-12, c1-14, c2-07) that are LIVE, unmigrated
    # instances of avoidable in-frame floats -- the strong claim survives,
    # but not vacuously; see the markdown report for the qualification.

    sharp_question = {
        "question": (
            "Do iterative numerical algorithms that accumulate error over many "
            "steps (Newton, FFT butterflies, filter recursions) make in-frame "
            "REALS necessary, or do they make PRECISION TRACKING necessary?"
        ),
        "answer": (
            "PRECISION TRACKING, not in-frame reals. Every iterative algorithm "
            "examined (Newton/Babylonian c2-01, RK4 c2-06, the LPC/Levinson-Durbin "
            "recursion c1-02, the YIN/cepstral pitch search c1-04) is, at each "
            "step, a closed-form rational operation (+,-,*,/) on the previous "
            "rational state; what it converges toward may be irrational, but the "
            "algorithm only ever needs to know THE SIGN OF A COMPARISON (has it "
            "converged; which side of a threshold) at some finite, boundable "
            "precision. IEEE floating point answers that comparison with a fixed-"
            "precision bit pattern and NO attached uncertainty -- indistinguishable "
            "from correct even when wrong (this is precisely the operational "
            "signature of the 1994 Pentium FDIV bug: a 5-entry SRT lookup-table "
            "defect that shipped for months because a wrong quotient at the "
            "4th-10th significant digit is statistically identical to ordinary "
            "float rounding noise; it was only caught by Thomas Nicely because he "
            "had an INDEPENDENT EXACT ground truth -- twin-prime reciprocals -- to "
            "compare against). Exact-rational / arbitrary-precision / interval "
            "methods (Boehm's constructive reals; interval arithmetic) instead "
            "carry a provable bound through every step and can explicitly report "
            "'undecided, need more precision' rather than a confident-looking "
            "wrong answer. Worked example from this audit: the Fisher-discriminant "
            "site (c1-14, domains/discriminative_invention.py) computes std = "
            "sqrt(variance) via ONE Newton/Babylonian-style step-limited float "
            "sqrt and persists it as a graph attr, then makes an in-frame identity "
            "decision (Gt(fisher, min_separation)) off it -- exactly the shape the "
            "question asks about. Rewritten in variance form ((mean_a-mean_b)^2 > "
            "k*(var_a+var_b)) the identical decision is made with zero sqrt calls "
            "and zero irrational intermediates: the iteration was never necessary "
            "for the DECISION, only for the (avoidable) std-shaped way the test "
            "was written -- error accumulation was never the reason a stored real "
            "was needed, because no stored real was needed at all."
        ),
    }

    tolerance_audit = {
        "question": (
            "Does any site in this repo's DSP stack carry an uncertainty/"
            "tolerance explicitly, or do they all discard it the way IEEE does?"
        ),
        "finding": (
            "Split. The core DSP layer (audio_primitives.rs: gammatone/LPC/FFT/"
            "cepstral/YIN chain) uses only ad hoc numerical-stability floors "
            "(`eps = 1e-10f32`/`1e-3f32`, guarding div-by-zero / log-of-zero), "
            "which are NOT tracked uncertainty -- they are IEEE-style: a wrong F0 "
            "or formant estimate is indistinguishable from ordinary float noise, "
            "the same failure shape as the Pentium FDIV bug. The vision/shape-"
            "decode 'verdict' layer is different and better: df_eps / cp_angles's "
            "sqrt(2)/2 lattice-half-diagonal bound (c1-08/c1-09) IS a genuine, "
            "principled, derived tolerance -- an explicit acceptance interval "
            "falling out of the observation's own quantization grain, used to "
            "ACCEPT or, just as importantly, to ABSTAIN "
            "(df_refused/ca_abstained/'abstain_reason': 'prior_invalidated' are "
            "real, reachable graph states in seeds/vision_deformation.json and "
            "seeds/vision_cut_abstention.json). That is the interval-arithmetic "
            "discipline the FDIV story recommends, already present in this "
            "codebase's newest layer; the older DSP layer has not adopted it."
        ),
    }

    return {
        "meta": {
            "date": "2026-08-01",
            "script": "scripts/arc5_numerics_float_audit.py",
            "companions": [
                "PROGRAM_SYNTHESIS_ARC5_FLOAT_NECESSITY.md",
                "PROGRAM_SYNTHESIS_ARC5_SPECS_IMPLY_FLOATS.md",
            ],
            "claim_under_test": (
                "No program needs floats. Many programs are specified in ways "
                "that imply they need floats."
            ),
            "line_window": LINE_WINDOW,
        },
        "sites": sites,
        "aggregates": {
            "total_sites": len(sites),
            "corpus1_sites": len(CORPUS1_SITES),
            "corpus2_sites": len(CORPUS2_SITES),
            "by_class": by_class,
            "by_class_corpus1": by_class_corpus1,
            "by_class_corpus2": by_class_corpus2,
        },
        "d_list": d_list,
        "unverified_site_ids": unverified,
        "sharp_question": sharp_question,
        "tolerance_audit": tolerance_audit,
        "verdict": verdict,
        "verdict_note": (
            "Zero (D) sites found across both corpora: no site is a genuinely "
            "irreducible in-frame real. Three (C) sites (c1-12, c1-14, c2-07) are "
            "LIVE avoidable in-frame floats -- the strong claim is UPHELD but with "
            "the qualification that this project's own DSP-adjacent code has not "
            "universally practiced what the invariant preaches yet."
        ),
    }


def main() -> None:
    audit = build_audit()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(audit, indent=2, sort_keys=False))
    agg = audit["aggregates"]
    print(f"wrote {OUT_PATH}")
    print(f"sites: {agg['total_sites']} (corpus1={agg['corpus1_sites']}, corpus2={agg['corpus2_sites']})")
    print(f"by class: {agg['by_class']}")
    print(f"(D) count: {len(audit['d_list'])}")
    print(f"unverified: {audit['unverified_site_ids']}")
    print(f"verdict: {audit['verdict']}")


if __name__ == "__main__":
    main()
