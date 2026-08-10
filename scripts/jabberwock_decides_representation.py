"""THE JABBERWOCK DECIDES THE FORK, SECOND INVOCATION (representation fork).

commit 23f76f3e ("RUN 23 -- continuous-novelty minting CANNOT diversify the vocabulary
either") ends the five-run wall (runs 19-23: token-refit, coverage-constrained refit,
coarse priors, fine priors, continuous minting -- all starve on the SAME stroke-identity
ceiling) with its own fork statement, quoted verbatim below and reused as this script's
Step-1 fact 10:

    "THE FORK (creator's call, per the pre-registered protocol): (a) richer per-part
    FEATURES into the base signature (velocity/curvature profiles, junction dynamics --
    more information per part, not more parts); (b) a BPL-style continuous primitive
    library (parameter-space clustering of sub-stroke trajectories -- a different
    quantization AXIS, ~hundreds of spline tokens); (c) declare vocabulary-dependent
    levers closed and pursue the verdict layer's own residuals at scale; (d) the
    jabberwock decides -- the fork-decision protocol (d2cd7bed) exists and worked."

This is (d), exercised a second time, on the (a)/(b)/(c) representation fork. It follows
`scripts/jabberwock_decides_ink_frontier.py` (commit d2cd7bed)'s protocol EXACTLY, widened
from two branches to three: evidence-as-verbatim-quoted-facts through the agent's OWN
`author_signature` RelationCue mechanism, symmetric branch encoding (each branch =
exactly one verbatim claim clause + one cited analogy-source commit, same arity, same
rigor), dual-path verdict (held `ShapeDecode`/`TransformDecode` coverage/fit, AND held
`AntiUnifyWitness`/`FixedCount` analogical closest-shape) against BOTH the three-branch
codebook and the agent's full held ShapeSignature codebook, held `Argmax` only, ties and
disagreements REPORTED not resolved, donkey=0, deterministic.

PROTOCOL (five steps, matching the precedent and the design doc exactly):

  1. EVIDENCE AS GRAPH DATA -- ten facts, each a VERBATIM quote from a committed commit
     message (cited inline: the five-run wall e43fba60/5bca81be/d46ac9b3/9762130f/
     23f76f3e, the 80.5 standing 2c669fd1, and the run-16 "bins propose, continuous
     decides" law as committed to CLAUDE.md -- the same CLAUDE.md-as-source move the
     precedent script's own fact 4 used). Run through `reflective_faculty.author_signature`,
     unioned (deduped) into ONE evidence relation-system. No editorializing: fact TEXT is
     copy-pasted from `git log` / `CLAUDE.md`, not paraphrased by this script.
  2. BRANCHES AS CANDIDATE SHAPES -- Branch A, B, C are each authored from EXACTLY the
     same two ingredients, same mechanism, same rigor: (i) the branch's ONE claim clause,
     verbatim from 23f76f3e's own fork statement (fact 10 above -- clauses (a), (b), (c)
     respectively -- clause (c) is quoted WITHOUT the "+ the transfer gate" gloss the
     outer task brief added, because that phrase is not present in 23f76f3e's text and
     this script's non-negotiable is copy-paste, not paraphrase; disclosed again in the
     run's closing self-audit), and (ii) the ONE analogy-source commit message the design
     brief cites for that branch (picking the more apt of the two offered where two were
     offered -- each choice is commented at its `_SOURCE_COMMIT` definition below). No
     branch gets extra material another doesn't.
  3. THE DECISION IS THE AGENT'S HELD OPERATOR -- two independent paths, both against BOTH
     the three-branch codebook (a throwaway scratch substrate, nothing persisted) and the
     agent's OWN full held ShapeSignature codebook (208 real nodes: math_capability_shapes
     + stroke_shapes + character_shapes -- so "neither" is a real, competing candidate):
       (a) COVERAGE/FIT: `ShapeDecode` + `TransformDecode`.
       (b) ANALOGICAL: `AntiUnifyWitness` (template + per-instance diff witnesses) +
           `FixedCount`, mirroring `seeds/shape_decode_loop.json`'s own `closest_held_shape`
           mechanism but keeping the witnessed differences for the trace.
     Each path's final pick is a held `Argmax` Term over a 4-way literal list
     [branch_a, branch_b, branch_c, neither]. Ties are detected (by inspecting the SAME
     scores handed to Argmax -- reporting, not deciding) and printed, never silently broken.
  4. VOICE -- skipped, honestly, for the same reason as the precedent: this script boots a
     bare `boot_core()` (no conversation/intent/psychology seeds), and no describe/produce
     pipeline is wired for that substrate.
  5. EXECUTE -- explicitly NOT done here. This script only produces and prints the
     verdict; the chosen branch's build is a separate, later task once the verdict is
     committed.

Gate genre: deterministic, PASS/FAIL = "a verdict was produced by held machinery with zero
Python decisions on the path" (WALL / TIE / disagreement all count as a produced verdict --
only an unhandled exception, or Argmax genuinely unable to run, is FAIL). donkey=0: no torch
or any teacher-model import anywhere on this path; asserted at the end.

Run:  PYTHONPATH=.:runners/dsl/python python -m scripts.jabberwock_decides_representation
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import substrate_rs as srs  # noqa: E402  (scratch substrate for the branch-only codebook)
from substrate.boot_core import boot_core  # noqa: E402
from substrate.seed_loader import manifest_for  # noqa: E402
from domains import reflective_faculty as rf  # noqa: E402

SEP = "=" * 100
WILD = "·?·"  # the "\xb7?\xb7" wild marker every AntiUnify/Covers/ShapeDecode call in this codebase uses


# =============================================================================================
# STEP 1 MATERIAL -- ten facts, each a verbatim excerpt from a committed commit message (or,
# for fact 9, from the committed CLAUDE.md paragraph that carries the run-16 law -- the exact
# move the precedent script's own fact 4 used for its Omniglot-arc CLAUDE.md paragraph). Every
# fact is cited by commit hash right here, in code, next to the text it names.
# =============================================================================================

FACT_TEXTS: dict[int, str] = {
    # commit e43fba60 (RUN 19): unconstrained token-refit is actively harmful, not neutral --
    # strictness-is-the-signal recurs one level up, at the likelihood/scoring level.
    1: ("TOKEN-REFIT unconstrained is ACTIVELY HARMFUL (25.5% — attractor programs "
        "cheaply explain any query; STRICTNESS IS THE SIGNAL recurring at the LIKELIHOOD "
        "level)"),
    # commit 5bca81be (RUN 20): even a mechanism-proven fix to the token-refit family
    # doesn't convert -- the family is subordinate to the representation, not the verdict.
    2: ("the token-refit family is subordinate to representation: parse-marginal remains "
        "the only winning verdict; next lever improves THE WINNER (learned spatial "
        "priors), not its rivals"),
    # commit d46ac9b3 (RUN 21): the same wall named across three different roads.
    3: ("ALL THREE roads from 80.5% hit the SAME wall: the 7-quantum identity space is "
        "too collapsed to carry conditioning information."),
    # commit 9762130f (RUN 22): four roads now, still the same wall; the vocabulary itself
    # is fingered as the binding constraint.
    4: ("FOUR runs (19-22) have now hit the SAME identity-grain ceiling from four angles "
        "— the binding constraint is the VOCABULARY (7 quanta, 1 dominant), and the "
        "next lever is LEARN-side: CONTINUOUS-NOVELTY MINTING"),
    # commit 23f76f3e (RUN 23): the fifth road (continuous-novelty minting) also fails --
    # and fails the SAME way, by collapsing into the dominant family.
    5: ("mints fire but cascade into nested near-duplicates of the SAME dominant family "
        "(86.4% share at the most aggressive threshold; vocab 6-7 vs the >=20 bar)"),
    # commit 23f76f3e: the five-angle wall, named in full.
    6: ("THE FIVE-ANGLE WALL, complete: token-refit (19), coverage-constrained refit (20), "
        "coarse priors (21), fine priors (22), continuous minting (23) — every "
        "BPL-ism starves on stroke-identity information this featureset provably does not "
        "carry."),
    # commit 23f76f3e: the compression claim survives the five failed angles -- it is a
    # fact about the representation, not a tuning artifact.
    7: ("the compression claim survives — the featureset genuinely SEES real strokes "
        "as ~1-7 families; that is a FACT about the representation, measured five ways, "
        "not a tuning failure"),
    # commit 2c669fd1 (RUN 17b): the 80.5% standing this whole five-run wall was measured
    # against.
    8: ("PARSE MARGINALIZATION at full dwell scores 80.5% [76.3,84.1] at n=400 — "
        "CI-SEPARATED from everything (+11.7pp over SC+TPS full dwell) and CI-TOUCHING "
        "the 81.5% Family-A anchor"),
    # CLAUDE.md, gamma-substrate (committed; the "RUN 16 RECONCILIATION (7743c2de)"
    # paragraph): the continuous-beats-quantized law the arc measured at the verdict layer.
    9: ("THE SYNTHESIS: earned quanta are the LEARNING/PROPOSAL layer (codebook growth, "
        "composition +21pp, transforms, writer dims); strong continuous geometry is the "
        'VERDICT layer — "bins propose, continuous decides," measured.'),
    # commit 23f76f3e: the fork statement itself -- the origin of all three branch claims
    # below, included here as evidence too (it is the fact that FRAMES the decision).
    10: ("THE FORK (creator's call, per the pre-registered protocol): (a) richer per-part "
         "FEATURES into the base signature (velocity/curvature profiles, junction "
         "dynamics — more information per part, not more parts); (b) a BPL-style "
         "continuous primitive library (parameter-space clustering of sub-stroke "
         "trajectories — a different quantization AXIS, ~hundreds of spline tokens); "
         "(c) declare vocabulary-dependent levers closed and pursue the verdict layer's "
         "own residuals at scale; (d) the jabberwock decides — the fork-decision "
         "protocol (d2cd7bed) exists and worked."),
}

FACT_CITATIONS: dict[int, str] = {
    1: "commit e43fba60 (RUN 19 -- token-refit unconstrained is actively harmful)",
    2: "commit 5bca81be (RUN 20 -- mechanism proven, accuracy wash)",
    3: "commit d46ac9b3 (RUN 21 -- spatial priors representation-bound)",
    4: "commit 9762130f (RUN 22 -- the pre-registered STOP fires)",
    5: "commit 23f76f3e (RUN 23 -- mints cascade into near-duplicates)",
    6: "commit 23f76f3e (RUN 23 -- the five-angle wall, named)",
    7: "commit 23f76f3e (RUN 23 -- the compression claim survives)",
    8: "commit 2c669fd1 (RUN 17b -- the waypoint is reached, 80.5% standing)",
    9: "CLAUDE.md, gamma-substrate (committed; the RUN 16 RECONCILIATION paragraph, commit 7743c2de)",
    10: "commit 23f76f3e (RUN 23 -- the fork statement itself)",
}


# =============================================================================================
# STEP 2 MATERIAL -- Branch A / B / C, each exactly one claim clause (verbatim from 23f76f3e's
# own fork statement, fact 10 above) + exactly one cited analogy-source commit message
# (verbatim from `git log`). Same arity (2 texts each), same mechanism, no extra material for
# any side.
#
# Analogy-source picks (each offered a choice of two in the design brief; the choice made and
# why is commented at each definition -- this IS the symmetry-relevant judgment call, made
# once, disclosed, not re-litigated per branch):
# =============================================================================================

BRANCH_A_NAME = "branch_a_richer_features"
# Verbatim, clause (a) of 23f76f3e's fork statement (fact 10).
BRANCH_A_CLAIM = ("richer per-part FEATURES into the base signature (velocity/curvature "
                   "profiles, junction dynamics — more information per part, not more "
                   "parts)")
# Choice: b48407ce (energy-channel front-end fix, POSITIVE result) vs 25f30e63 ("THE
# FRONT-END", a later and more thorough study of the SAME question -- does a richer/learned
# front-end lift a ceiling -- reaching a DECISIVE, NEGATIVE verdict for frame-level richness).
# Picked 25f30e63: it is the more apt precedent (it directly tests "richer per-frame/per-part
# features, does the representation improve" -- branch A's exact claim -- across FIVE lever
# variants: delta, LDA, SFA, and a borrowed wav2vec2 capacity ceiling) and it is the LATER,
# more comprehensive, and more decisive word on the question; b48407ce's earlier positive
# result is a single successful lever inside a narrower ablation that 25f30e63 supersedes
# ("634e394f proved 0.93 is the intrinsic ceiling... this chapter tests whether a
# RICHER/LEARNED front-end lifts it"). Choosing the more apt-but-less-flattering source over
# the more apt-but-flattering one is the same discipline the precedent script applied when it
# cited ffa12c7b (a decisive NEGATIVE result on the tested mechanism) for its own Branch B.
BRANCH_A_SOURCE_COMMIT = "25f30e63"
BRANCH_A_SOURCE_TITLE = ("THE FRONT-END — learned/richer acoustic representation does "
                          "NOT lift order-1 past 0.93; decisive HONEST FORK: 0.93 is the "
                          "genuine isolated-word frame-feature ceiling, the residual needs "
                          "higher-order context")
BRANCH_A_SOURCE_TEXT = """THE FRONT-END — learned/richer acoustic representation does NOT lift order-1 past 0.93; decisive HONEST FORK: 0.93 is the genuine isolated-word frame-feature ceiling, the residual needs higher-order context

634e394f proved 0.93 is the intrinsic ceiling of the 32-band/100fps cochleagram (feature, not
normalization). This chapter tests whether a RICHER/LEARNED front-end lifts it: make coarticulated +
cross-speaker instances of a word SNAP together while distinct words stay SEPARATE. Levers, all donkey=0
at inference, matched-granularity clustering + rank-based cross metrics (the 2 rigor lessons):

  A  raw+DELTA (cheap richness) — velocity appended.
  B1 LDA (contrastive/discriminative, closed-form numpy): Fisher projection on the 0.93 DTW pseudo-clusters
     (weak same-word positives) — pull same-cluster frames together, push distinct apart.
  B2 SFA (temporal-predictive slow features, closed-form numpy): the slowest linear subspace.
  C  wav2vec2 BORROWED capacity ceiling: features computed in an ISOLATED torch subprocess (MMS_FA for word
     boundaries + true speaker/context), stored as DATA; the analyze process is torch-free (donkey=0
     verified: no torch/torchaudio/wav2vec2 in sys.modules). PCA-24 of the borrowed 768-d, DTW-clustered.

Self-contained: my own extraction subprocess builds the held-out eval cache (word, coch, w2v[T,768], TRUE
speaker, left/right word) -> BOTH cross-speaker AND cross-context gates on identical tokens. Memory: 32x32 /
768x768 scatter, chunked kmeans (no (N,K,D)), bounded/greedy DTW leader clustering, float32, ulimit-14Gi;
analyze peak 1.62 GiB, extract peak 3.19 GiB.

DECISIVE RESULT — no front-end lever lifts the order-1 ceiling or the coarticulation/speaker RESIDUAL:
• LINEAR numpy: on CLEAN phonebank LDA 0.764 / SFA 0.793 beat raw 0.728 (beats shuffled-label control 0.708)
  — but this is SAME-DISTRIBUTION overfit: on the held-out eval cache they DON'T beat raw (LDA 0.510 vs
  0.508) and they WORSEN the actual residual — cross-speaker NN LDA 0.167 vs raw 0.183, cross-context 0.228
  vs 0.250, and R3 margin LDA -0.020 vs raw +0.042. A linear reweight adds no invariance (SFA also collapses
  word-discrimination d' 1.40).
• BORROWED wav2vec2 (nonlinear CAPACITY CEILING): does NOT lift it either — eval order-1 -0.076, cross-
  context -0.083, R3 -0.116, discrimination d' 1.17 vs 1.63 (all DROP). It helps ONLY cross-SPEAKER NN
  (+0.045 — its trained speaker-invariance, the already-characterized R1 axis) at the cost of word-
  discrimination. Contextualized/smoothed SSL frames cluster ISOLATED words WORSE under DTW.

VERDICT: 0.93 is near the GENUINE audio-information ceiling for isolated-word frame clustering — distinct
words intrinsically overlap at the frame level; the coarticulation/context residual is NOT a frame-
representation problem (neither earned-linear nor borrowed-nonlinear frames fix it) but needs higher-order
SEQUENCE/context (order-2/3). The frame front-end is EXHAUSTED at 0.93. NOT irreducible: the quantified
next lever is higher-order context, not a richer frame. Caveat (honest): wav2vec2 tested as PCA-24 under
DTW; full-dim/native-distance untested for DTW cost — but order-1 AND discrimination both DROP, so the
direction is clear. donkey=0 at inference verified; shuffled-label control confirms the linear "gain" is
same-distribution, not generalizable invariance.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"""

BRANCH_B_NAME = "branch_b_continuous_primitive_library"
# Verbatim, clause (b) of 23f76f3e's fork statement (fact 10).
BRANCH_B_CLAIM = ("a BPL-style continuous primitive library (parameter-space clustering of "
                   "sub-stroke trajectories — a different quantization AXIS, ~hundreds "
                   "of spline tokens)")
# Choice: 8ae8666e (DTW-trajectory quantization SNAP, "word-form IS a quantized N-D curve")
# vs 7743c2de (run-16 continuous-beats-quantized reconciliation, SC+TPS as the VERDICT
# layer). Picked 8ae8666e: it is the structurally exact analogy -- it builds a continuous
# primitive representation (the frame-sequence TRAJECTORY) and QUANTIZES it via a held
# DtwTo Term over greedy-leader clustering ("parameter-space clustering of ... trajectories",
# branch B's own words) to get a library of trajectory-classes. 7743c2de's SC+TPS result is a
# real, positive precedent for "continuous beats quantized" but it is a VERDICT/comparator
# lever (deciding between existing candidates), not a LIBRARY-BUILDING lever (minting new
# primitives by clustering trajectories) -- fact 9 above already carries 7743c2de's law into
# the evidence set, so citing it again as branch B's OWN analogy source would double-count the
# same precedent on one side of the fork; 8ae8666e is the non-overlapping, more literal match.
BRANCH_B_SOURCE_COMMIT = "8ae8666e"
BRANCH_B_SOURCE_TITLE = ("QUANTIZATION-SNAP order-1 — the word-form IS a quantized N-D "
                          "CURVE (creator's reframe CONFIRMED)")
BRANCH_B_SOURCE_TEXT = """QUANTIZATION-SNAP order-1 — the word-form IS a quantized N-D CURVE (creator's reframe CONFIRMED). Represent each word token as its cochleagram FRAME-SEQUENCE (the trajectory/curve), quantize by TRAJECTORY similarity via the held DtwTo Rust Term (greedy leader clustering, MinOver/Argmin over leader nodes = 1 evaluate/token, memory-bounded, no NxN). RESULT (LibriSpeech dev-clean, 1500 tokens, peak 0.91 GiB, donkey=0): DTW-trajectory quantization lifts earned order-1 purity to 0.93 — the SNAP across REPRESENTATION: raw-pool 0.30 -> lossy phone-STRING 0.66 (b48407ce) -> N-D CURVE 0.93 -> teacher 0.99. Using the actual trajectory + DTW snaps same-word curves to near-ceiling, confirming word-form = quantized trajectory. HONEST nuances: (i) the FIT-RESOLUTION sweep (T frames 3..20) is GRADUAL not a sharp threshold — DTW is robust to resolution (even T=3 snaps ~0.85); the phase transition is the REPRESENTATION (pooled/string/curve), not temporal fit; (ii) the earned low-dim MANIFOLD (train_ae, 0.86-0.88) does NOT beat the raw N-D curve on CLEAN data (raw+DTW already snaps; the manifold's value is speaker-invariance on noisy/cross-speaker); (iii) GATES: order-1 purity 0.93 is the robust result, gate-C is n-limited (flipped 0.47>scaffolded-0.435 at N=1800, null at N=1500 as 'the' fragments into pure sub-clusters). Remaining lift to 0.99 = cross-speaker variance (speaker-invariant curve space). donkey=0 verified (DtwTo held Rust Term, AE from-scratch numpy, no allosaurus/torch in sys.modules; transcript/nltk-POS scoring-only). Reused DtwTo + articulatory_bottleneck.train_ae + decisive-test gates. regression clean (only my new script; parallel churn untouched)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"""

BRANCH_C_NAME = "branch_c_close_corridor_verdict_scale"
# Verbatim, clause (c) of 23f76f3e's fork statement (fact 10). NOTE: the outer task brief's
# framing of this branch appended "+ the transfer gate" -- that phrase is NOT present in
# 23f76f3e's text, so it is excluded from the authored claim (copy-paste discipline, not
# paraphrase); disclosed again in the closing self-audit.
BRANCH_C_CLAIM = "declare vocabulary-dependent levers closed and pursue the verdict layer's own residuals at scale"
# Choice: f0fae1fe (RUN 15, "the powered gate corrects the arc" — same ink arc, same run
# numbering, explicitly declares "the representation-grain corridor is exhausted end to end")
# vs 06ffe21f (an EARLIER, different arc's conclusion -- "agent executes its recommendation
# ... arc concludes at 78%", pre-dating the run-1..23 numbering by more than a week and a
# different featureset generation). Picked f0fae1fe: it is the closer precedent in every way
# that matters -- same arc, same "corridor exhausted" language branch C's claim itself uses,
# and it is the run that FIRST established the "declare closed, the next lever is a different
# featureset" pattern branch C proposes reusing at the verdict layer instead.
BRANCH_C_SOURCE_COMMIT = "f0fae1fe"
BRANCH_C_SOURCE_TITLE = ("RUN 15 — THE POWERED GATE CORRECTS THE ARC: honest ceiling "
                          "26.8% [22.6,31.3] on 10 alphabets ... ONE fact survives "
                          "CI-separated: COMPOSITION, +21pp over multiset; Branch B "
                          "(junction blend) nulls — the corridor is exhausted end to end")
BRANCH_C_SOURCE_TEXT = """RUN 15 — THE POWERED GATE CORRECTS THE ARC: honest ceiling 26.8% [22.6,31.3] on 10 alphabets (the 4-alphabet set was an easy subset); EVERY post-composition delta was 1-3 episodes of noise (AbS/dwell/appearance/rel2/sub-strokes ALL inside each other's CIs at n=400; rel2 — run 9's 'loser' — is numerically TOP at power); ONE fact survives CI-separated: COMPOSITION, +21pp over multiset; Branch B (junction blend) nulls — the corridor is exhausted end to end

PHASE 1 (n=400: 10 sorted-name alphabets x R=2 x 20 episodes, runtime clause fired and
logged; Wilson 95% CIs): multiset 5.0 [3.3,7.6]; composed 26.0 [21.9,30.5]; AbS K=5
28.0 [23.8,32.6]; delta=0 26.8; adopted+appearance 26.8 [22.6,31.3]; rel2 28.7
[24.5,33.4]; +substroke 27.0. coverage@5 = 54.5% (the one stable historical number).
CONCLUSION AUDIT, plainly: AbS gain INCONCLUSIVE (direction held, not separated); dwell
INCONCLUSIVE (direction REVERSED); appearance gain EVAPORATES to +0.0; composition null
STILL NULL; rel2 null REVISED (top arm — the run-9 'ties broke wrong' story was noise).
The historical 33.8/37.5/38.8/41.2 point estimates all lie OUTSIDE the powered CIs.
WHAT SURVIVES: arrangement-composition (+21pp, hugely separated), ~54% recall@5, a 5.0%
truly proposal-blind tail (20/400 rank 16+), the saturation facts (7 stroke / 4
sub-stroke quanta), the control chain (33.8/37.5/38.8/41.2 all still reproduce EXACTLY
on the original protocol — the machinery is deterministic; the EVAL SET was the error).

PHASE 2 — Branch B continuous (junction-blended rendering, endpoint-anchored taper
J=0.15 as data, flag off byte-identical, decisive synthetic gate proves the mechanism):
26.8% vs 26.8%, not one verdict changed over 400 episodes. HONEST NULL WITH POWER. Both
fork branches (A run 14, B run 15) built, measured, null — the representation-grain
corridor is exhausted end to end.

THE ARC'S REAL LEDGER, restated under power: one architectural lever PROVEN (character
composition = the sd loop one level up, +21pp CI-separated); the mechanisms of the
others are all REAL at the synthetic-gate level (round-trip rendering, tie-breaking,
dwell scheduling) but their accuracy VALUE on this benchmark was an artifact of an
underpowered 80-episode gate — the design's own measurement-problem statement, vindicated
against the arc itself. Next lever, if any: a different featureset, not a further
transform of this one.

Gates: 88/88 composition+ink+substroke (7 new); migrated bench 714 green. Invariants:
saturations PASS, OOV 0%, donkey=0, all reproductions exact. Runtime 1227s.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"""

BRANCHES = [
    (BRANCH_A_NAME, BRANCH_A_CLAIM, BRANCH_A_SOURCE_COMMIT, BRANCH_A_SOURCE_TITLE, BRANCH_A_SOURCE_TEXT),
    (BRANCH_B_NAME, BRANCH_B_CLAIM, BRANCH_B_SOURCE_COMMIT, BRANCH_B_SOURCE_TITLE, BRANCH_B_SOURCE_TEXT),
    (BRANCH_C_NAME, BRANCH_C_CLAIM, BRANCH_C_SOURCE_COMMIT, BRANCH_C_SOURCE_TITLE, BRANCH_C_SOURCE_TEXT),
]


# =============================================================================================
# Mechanical helpers -- glue code calling HELD Terms. None of these contain a decision over
# graph state; every ranking is done by a real `Argmax` Term call, every score by a real
# `ShapeDecode`/`TransformDecode`/`AntiUnifyWitness`/`FixedCount` Term call.
# =============================================================================================

def _author(sub, name: str, text: str) -> list:
    """Install a scratch Concept carrying `text` as its `definition`, then run the agent's OWN
    held signature-authoring mechanism over it (`reflective_faculty.author_signature` -- the
    exact function that authors every ShapeSignature already in this codebase). Mechanical
    I/O (one node write + one call to an existing, unmodified held function) -- no new
    matching logic, no decision."""
    sub.add_node("Concept", {"name": name, "definition": text})
    sig, _defn, _cname = rf.author_signature(sub, name)
    return sig or []


def _dedup_union(sig_lists) -> list:
    """Mechanical set-union-with-order, exactly as `author_signature` itself dedups within one
    text. No decision -- a relation is either already present or it isn't."""
    seen = set()
    out = []
    for sig in sig_lists:
        for rel in sig:
            key = tuple(rel)
            if key not in seen:
                seen.add(key)
                out.append(list(rel))
    return out


def _lit(value):
    return {"type": "Lit", "value": value}


def _shape_decode(native, goal_sig, *, codebook_type="ShapeSignature", exclude=None,
                   beam=3, max_steps=8, cand_k=3):
    term = {"type": "ShapeDecode", "goal": _lit([list(r) for r in goal_sig]),
            "codebook_type": codebook_type, "beam": beam, "max_steps": max_steps,
            "cand_k": cand_k}
    if exclude:
        term["exclude"] = _lit([str(e) for e in exclude])
    return native.evaluate(term, {})


def _transform_decode(native, goal_sig, *, codebook_type="ShapeSignature", exclude=None,
                       max_dims=6):
    term = {"type": "TransformDecode", "goal": _lit([list(r) for r in goal_sig]),
            "codebook_type": codebook_type, "max_dims": max_dims}
    if exclude:
        term["exclude"] = _lit([str(e) for e in exclude])
    return native.evaluate(term, {})


def _coverage_fraction(goal_sig, decode_result: dict) -> float:
    """Pure arithmetic on already-Rust-decided output (covered_count / goal_relations) --
    mechanical read-out, not a decision."""
    total = int(decode_result.get("goal_relations") or len(goal_sig) or 0)
    if total == 0:
        return 0.0
    covered = int(decode_result.get("covered_count") or 0)
    return covered / total


def _antiunify_witness(native, sig_a, sig_b):
    """The analogical path's core call: `AntiUnifyWitness` (template + per-instance witness
    diffs) then `FixedCount` on the template (shared-leaves score) -- the SAME two-Term
    sequence `seeds/shape_decode_loop.json`'s own `closest_held_shape` mechanism runs (there
    via plain `AntiUnify`; here via the witness-preserving twin, so the diff is inspectable).
    `values` is passed as an ORDERED `Lit` list (not a `SetT`), so `sigmas[0]`/`sigmas[1]`
    are unambiguously (a's diff, b's diff)."""
    n = min(len(sig_a), len(sig_b))
    if n == 0:
        return [], [{}, {}], 0
    a = [list(x) for x in sig_a[:n]]
    b = [list(x) for x in sig_b[:n]]
    template, sigmas = native.evaluate(
        {"type": "AntiUnifyWitness", "values": _lit([a, b]), "wild": WILD}, {})
    fixed = native.evaluate({"type": "FixedCount", "pattern": _lit(template), "wild": WILD}, {})
    try:
        fixed = int(fixed)
    except Exception:
        fixed = 0
    return template, sigmas, fixed


def _held_argmax(native, pairs):
    """The ONE place a winner is chosen: a real `Argmax` Term over a literal `[score, label]`
    list Python only ASSEMBLED (every `score` already came from a held Term call above).
    Exactly `domains/reflective_faculty.py::learn_term_for_concern`'s pattern."""
    if not pairs:
        return None
    return native.evaluate(
        {"type": "Argmax", "source": _lit(pairs), "var_name": "c",
         "value": {"type": "IndexAt", "seq": {"type": "Var", "name": "c"},
                   "index": _lit(0)},
         "default": None}, {})


def _tied_labels(pairs):
    """Reporting-only: which candidates share the top score. Inspects the SAME numbers
    handed to `_held_argmax` above -- it does not re-decide anything (the actual pick is
    always the Argmax Term's), it only says out loud when more than one candidate was
    tied for that pick."""
    if not pairs:
        return []
    best = max(p[0] for p in pairs)
    return [p[1] for p in pairs if p[0] == best]


def _fmt_sig(sig, indent="      "):
    if not sig:
        return indent + "(empty -- no held RelationCue fired)"
    return "\n".join(f"{indent}{tuple(r)}" for r in sig)


# =============================================================================================
def main() -> int:
    print(SEP)
    print("THE JABBERWOCK DECIDES THE FORK (second invocation) -- REPRESENTATION")
    print("richer per-part features  vs  continuous primitive library  vs  close the corridor")
    print(SEP)

    # ---- boot: core + the RelationCue lexicon + the agent's OWN held ShapeSignature codebook
    s, ag = boot_core()
    native = s._inner
    rf._ensure_shape_decode_loop(s, native, ag)          # math_capability_shapes + self_design_axis
    native.load_seed_manifest(manifest_for("relation_vocabulary"), ag)   # the RelationCue lexicon
    native.load_seed_manifest(manifest_for("stroke_shapes"), ag)         # the earned stroke codebook
    native.load_seed_manifest(manifest_for("character_shapes"), ag)      # the earned character codebook

    held_sigs = rf._load_shape_signatures(s)   # {name: (kind, signature, concept_or_faculty)}
    print(f"\nBooted: core + relation_vocabulary + math_capability_shapes + stroke_shapes + "
          f"character_shapes -> {len(held_sigs)} held ShapeSignature nodes "
          f"(the agent's OWN codebook the 'neither' path competes against).")

    # =========================================================================================
    # STEP 1 -- EVIDENCE AS GRAPH DATA
    # =========================================================================================
    print(f"\n{SEP}\nSTEP 1 -- EVIDENCE AS GRAPH DATA (verbatim commit-message / CLAUDE.md "
          f"facts, run through the held RelationCue signature-authoring mechanism)\n{SEP}")
    fact_sigs = {}
    for i in sorted(FACT_TEXTS):
        fact_sigs[i] = _author(s, f"repr_frontier_fact_{i}", FACT_TEXTS[i])
        print(f"\n  FACT {i}  [{FACT_CITATIONS[i]}]")
        print(f"    text: {FACT_TEXTS[i]}")
        print(f"    fired relations:\n{_fmt_sig(fact_sigs[i], indent='      ')}")
    evidence_sig = _dedup_union(fact_sigs.values())
    print(f"\n  EVIDENCE (union of all {len(FACT_TEXTS)} facts, deduped, {len(evidence_sig)} "
          f"relations):")
    print(_fmt_sig(evidence_sig))

    # =========================================================================================
    # STEP 2 -- BRANCHES AS CANDIDATE SHAPES (same vocabulary, same mechanism, same rigor)
    # =========================================================================================
    print(f"\n{SEP}\nSTEP 2 -- BRANCHES AS CANDIDATE SHAPES\n{SEP}")

    branch_sigs = {}
    for name, claim, src_commit, src_title, src_text in BRANCHES:
        claim_sig = _author(s, f"{name}_claim", claim)
        source_sig = _author(s, f"{name}_source", src_text)
        branch_sig = _dedup_union([claim_sig, source_sig])
        branch_sigs[name] = branch_sig

        print(f"\n  {name.upper()}")
        print(f"    claim (verbatim, 23f76f3e's own fork statement): {claim!r}")
        print(f"      fired relations:\n{_fmt_sig(claim_sig)}")
        print(f"    analogy source [commit {src_commit}: {src_title!r}]")
        print(f"      fired relations:\n{_fmt_sig(source_sig)}")
        print(f"    {name.upper()} SIGNATURE (union, {len(branch_sig)} relations):")
        print(_fmt_sig(branch_sig))
        if not branch_sig:
            print(f"    DISCLOSURE: {name} fires ZERO held RelationCue relations from its "
                  f"claim+source text. Honest -- not forced (mirrors the precedent run's "
                  f"disclosure for its own Branch A, which still won).")

    # scratch, episode-scoped codebook holding ONLY the three branches (nothing persists; the
    # main substrate `s` never sees these three nodes) -- the same instance-scoped scratch
    # substrate precedent the ink-frontier run applied.
    scratch = srs.Substrate()
    for name, _claim, _c, _t, _tx in BRANCHES:
        scratch.add_node("ShapeSignature", {"name": name, "kind": "frontier_branch",
                                             "signature": json.dumps(branch_sigs[name])})
    scratch_native = scratch._inner
    branch_names = [b[0] for b in BRANCHES]

    # =========================================================================================
    # STEP 3a -- COVERAGE/FIT PATH (ShapeDecode + TransformDecode)
    # =========================================================================================
    print(f"\n{SEP}\nSTEP 3a -- COVERAGE/FIT PATH (held ShapeDecode / TransformDecode)\n{SEP}")

    cov_pairs = []
    for name in branch_names:
        others = [n for n in branch_names if n != name]
        decode_solo = _shape_decode(scratch_native, evidence_sig, exclude=others)
        td_solo = _transform_decode(scratch_native, evidence_sig, exclude=others)
        cov = _coverage_fraction(evidence_sig, decode_solo)
        cov_pairs.append([cov, name])
        print(f"\n  {name} solo (other two branches excluded from the 3-shape codebook):")
        print(f"    ShapeDecode:     coverage={cov:.3f} ({decode_solo.get('covered_count')}/"
              f"{decode_solo.get('goal_relations')})  total_fit={decode_solo.get('total_fit')}  "
              f"plan={decode_solo.get('ordered_parts')}  residual={decode_solo.get('residual')}")
        print(f"    TransformDecode: explained={td_solo.get('explained')}  "
              f"base={td_solo.get('base')}  dims={td_solo.get('dims')}  "
              f"deltas={td_solo.get('deltas')}  identity={td_solo.get('identity')}")

    decode_all = _shape_decode(scratch_native, evidence_sig)   # all three available, informational only
    print(f"\n  All three branches available (composed plan, INFORMATIONAL ONLY -- not a "
          f"decision input): plan={decode_all.get('ordered_parts')}  "
          f"total_fit={decode_all.get('total_fit')}  "
          f"coverage={_coverage_fraction(evidence_sig, decode_all):.3f}")

    decode_full = _shape_decode(native, evidence_sig)          # main substrate: real codebook
    td_full = _transform_decode(native, evidence_sig)
    cov_full = _coverage_fraction(evidence_sig, decode_full)
    full_parts = list(decode_full.get("ordered_parts") or [])
    full_label = f"neither -- best held coverage uses {full_parts!r}" if full_parts else \
                 "neither -- no held shape covers any evidence relation"

    print(f"\n  Full held codebook ({len(held_sigs)} real ShapeSignature nodes -- "
          f"math_capability_shapes + stroke_shapes + character_shapes; branches ABSENT):")
    print(f"    ShapeDecode:     coverage={cov_full:.3f} ({decode_full.get('covered_count')}/"
          f"{decode_full.get('goal_relations')})  total_fit={decode_full.get('total_fit')}  "
          f"plan={full_parts}  residual={decode_full.get('residual')}")
    print(f"    TransformDecode: explained={td_full.get('explained')}  base={td_full.get('base')}  "
          f"dims={td_full.get('dims')}  deltas={td_full.get('deltas')}  identity={td_full.get('identity')}")

    coverage_pairs = cov_pairs + [[cov_full, full_label]]
    coverage_pick = _held_argmax(native, coverage_pairs)
    coverage_tied = _tied_labels(coverage_pairs)
    print(f"\n  COVERAGE-PATH candidates: {coverage_pairs}")
    print(f"  COVERAGE-PATH held Argmax pick: {coverage_pick}")
    if len(coverage_tied) > 1:
        print(f"  COVERAGE-PATH TIE at top score {max(p[0] for p in coverage_pairs):.3f}: "
              f"{coverage_tied}")

    # =========================================================================================
    # STEP 3b -- ANALOGICAL PATH (AntiUnifyWitness + FixedCount, closest_held_shape's mechanism)
    # =========================================================================================
    print(f"\n{SEP}\nSTEP 3b -- ANALOGICAL PATH (held AntiUnifyWitness + FixedCount)\n{SEP}")

    fixed_by_name = {}
    for name in branch_names:
        tmpl, wit, fixed = _antiunify_witness(native, evidence_sig, branch_sigs[name])
        fixed_by_name[name] = fixed
        print(f"\n  evidence <-> {name}: shared_leaves(FixedCount)={fixed}")
        print(f"    template: {tmpl}")
        print(f"    witness (evidence's diff-map): {wit[0] if wit else {}}")
        print(f"    witness ({name}'s diff-map): {wit[1] if len(wit) > 1 else {}}")

    # closest_held_shape over the FULL real codebook -- Python only iterates to compute each
    # candidate's Rust-computed score; the winner is the held Argmax below, exactly
    # `seeds/shape_decode_loop.json`'s own mechanism, generalized to keep the witness diffs.
    held_pairs = []
    held_detail = {}
    for name, (_kind, sig, _src) in held_sigs.items():
        _tmpl, _wit, fixed = _antiunify_witness(native, evidence_sig, sig)
        held_pairs.append([fixed, name])
        held_detail[name] = (_tmpl, _wit, fixed)
    closest_held_pick = _held_argmax(native, held_pairs) if held_pairs else None
    closest_held_name = closest_held_pick[1] if closest_held_pick else None
    closest_held_fixed = closest_held_pick[0] if closest_held_pick else 0
    top5 = sorted(held_pairs, key=lambda p: -p[0])[:5]
    print(f"\n  closest_held_shape over the FULL {len(held_sigs)}-node codebook "
          f"(top 5 by shared_leaves): {top5}")
    print(f"  closest_held_shape held Argmax pick: {closest_held_pick}")
    if closest_held_name is not None:
        _tmpl, _wit, _fx = held_detail[closest_held_name]
        print(f"    template vs {closest_held_name!r}: {_tmpl}")

    analogical_label_neither = (f"neither -- closest held shape is {closest_held_name!r} "
                                 f"(shared_leaves={closest_held_fixed})")
    analogical_pairs = [[fixed_by_name[n], n] for n in branch_names] + \
                       [[closest_held_fixed, analogical_label_neither]]
    analogical_pick = _held_argmax(native, analogical_pairs)
    analogical_tied = _tied_labels(analogical_pairs)
    print(f"\n  ANALOGICAL-PATH candidates: {analogical_pairs}")
    print(f"  ANALOGICAL-PATH held Argmax pick: {analogical_pick}")
    if len(analogical_tied) > 1:
        print(f"  ANALOGICAL-PATH TIE at top score {max(p[0] for p in analogical_pairs)}: "
              f"{analogical_tied}")

    # =========================================================================================
    # STEP 4 -- VOICE (skipped, honestly)
    # =========================================================================================
    print(f"\n{SEP}\nSTEP 4 -- VOICE\n{SEP}")
    print("  Skipped: this script boots bare `boot_core()` (core cognition only -- no "
          "conversation/intent/psychology seeds), and no describe/produce pipeline is wired "
          "for that substrate. Standing up one would be new machinery for this task to build, "
          "which the brief does not license. Honest skip, not a faked utterance.")

    # =========================================================================================
    # FINAL VERDICT -- printed, not resolved. Agreement between the two paths (with neither
    # path internally tied) is the only case that collapses to a single label; anything else
    # (a tie within a path, or the two paths naming different winners) is reported as-is.
    # =========================================================================================
    print(f"\n{SEP}\nFINAL VERDICT\n{SEP}")

    def _label_of(pick):
        return pick[1] if pick else None

    coverage_label = _label_of(coverage_pick)
    analogical_label = _label_of(analogical_pick)
    coverage_clean = coverage_label if len(coverage_tied) <= 1 else None
    analogical_clean = analogical_label if len(analogical_tied) <= 1 else None

    print(f"  coverage/fit path  -> {coverage_label!r}"
          + (" (TIED, not a clean pick)" if coverage_clean is None else ""))
    print(f"  analogical path    -> {analogical_label!r}"
          + (" (TIED, not a clean pick)" if analogical_clean is None else ""))

    if coverage_clean is not None and coverage_clean == analogical_clean:
        print(f"\n  BOTH PATHS AGREE: {coverage_clean!r}")
        print("  THE JABBERWOCK'S VERDICT: " + coverage_clean)
        verdict_kind = "AGREEMENT"
    else:
        print("\n  THE PATHS DO NOT CLEANLY AGREE (a tie in at least one path, and/or the two "
              "paths naming different winners). Per the non-negotiable, this disagreement/tie "
              "IS the verdict -- it is reported here, not resolved by this script:")
        print(f"    coverage/fit path candidates: {coverage_pairs} -> pick {coverage_pick}")
        print(f"    analogical path candidates:   {analogical_pairs} -> pick {analogical_pick}")
        print("  THE JABBERWOCK'S VERDICT: TIE / DISAGREEMENT (see above) -- not resolved here.")
        verdict_kind = "TIE_OR_DISAGREEMENT"

    # =========================================================================================
    # donkey=0 + gate PASS/FAIL
    # =========================================================================================
    donkey_modules = ("torch", "torchaudio", "tensorflow", "allosaurus", "whisper",
                       "faster_whisper", "ctranslate2", "transformers")
    loaded = [m for m in donkey_modules if m in sys.modules]
    assert not loaded, f"donkey!=0: {loaded} present in sys.modules"
    print(f"\ndonkey=0 verified: none of {donkey_modules} present in sys.modules.")

    print(f"\n{SEP}")
    print(f"GATE: PASS -- a verdict ({verdict_kind}) was produced by held machinery "
          f"(ShapeDecode/TransformDecode/AntiUnifyWitness/FixedCount/Argmax); zero Python "
          f"decisions on the path.")
    print("EXECUTION: explicitly NOT performed by this script -- the verdict is reported "
          "for the caller to commit; building the chosen branch is a separate, later task.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
