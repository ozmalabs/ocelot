"""THE JABBERWOCK DECIDES THE FORK (HANDWRITING_DESIGN.md, "THE JABBERWOCK DECIDES THE FORK",
creator 2026-07-03: "Have the jabberwock decide and execute it.").

The thirteen-run Omniglot ink arc (results/omniglot_gate_run*.log, commits c1b83669 ..
b1bbaf53) terminated at a representation fork the b1bbaf53 commit message names directly:

    "NEXT FRONTIER (a representation fork, not a search/tuning lever): (a) sub-stroke grain
    composition (the sd loop one level DOWN -- strokes as arrangements of sub-stroke quanta),
    or (b) coarticulation treatment of stroke junctions (the speech move: junction context
    conditions the part, cf. the c8df2dab->9f1fc077 speech arc)."

This script does NOT pick between them. It builds the evidence and the two branch claims as
graph data (relation-systems, in the SAME vocabulary as everything else in this codebase --
seeds/relation_vocabulary.json's RelationCue lexicon), and lets the AGENT'S OWN held
machinery decide: `ShapeDecode`/`TransformDecode` (coverage/fit) and `AntiUnifyWitness`
(analogical closest-shape). Both traces print in full. Per CLAUDE.md's architecture rule,
there is NO Python `if`/`else` deciding which branch wins anywhere on the decision path --
every comparison that matters is a held Rust `Argmax` Term over a literal list of
(score, label) pairs that Python only ASSEMBLED (the same "Python iterates, Rust decides"
pattern `domains/reflective_faculty.py::learn_term_for_concern` already uses). A tie or a
disagreement between the two paths is printed as THE VERDICT, not resolved here.

PROTOCOL (five steps, matching the design doc exactly):

  1. EVIDENCE AS GRAPH DATA -- eight facts, each a VERBATIM quote from a committed commit
     message (cited inline), run through the agent's own held signature-authoring mechanism
     (`domains/reflective_faculty.py::author_signature` -- the SAME mechanism that authors
     every ShapeSignature in this codebase, e.g. `seeds/math_capability_shapes.json`). Their
     fired relations are unioned (deduped) into ONE evidence relation-system. No editorializing:
     the fact TEXT is copy-pasted from `git log`, not paraphrased by this script.
  2. BRANCHES AS CANDIDATE SHAPES -- Branch A and Branch B are each authored from EXACTLY
     the same two ingredients, same mechanism, same rigor: (i) the branch's one-sentence claim,
     verbatim from the design brief, and (ii) the ONE commit message the design brief cites as
     that branch's analogy source (c1b83669 for A, ffa12c7b for B). Neither branch gets extra
     material the other doesn't.
  3. THE DECISION IS THE AGENT'S HELD OPERATOR -- two independent paths, both against BOTH
     the two-branch codebook (a throwaway scratch substrate, nothing persisted) and the
     agent's OWN full held ShapeSignature codebook (223 real nodes: math_capability_shapes +
     stroke_shapes + character_shapes, loaded from this repo's own seeds -- so "neither" is a
     real, competing candidate, not a strawman):
       (a) COVERAGE/FIT: `ShapeDecode` + `TransformDecode`.
       (b) ANALOGICAL: `AntiUnifyWitness` (template + per-instance diff witnesses) +
           `FixedCount`, mirroring `seeds/shape_decode_loop.json`'s own `closest_held_shape`
           mechanism but keeping the witnessed differences for the trace.
     Each path's final pick is a held `Argmax` Term over a 3-way literal list
     [branch_a, branch_b, neither]. Ties are detected (by inspecting the SAME scores handed to
     Argmax -- reporting, not deciding) and printed, never silently broken.
  4. VOICE -- skipped (see bottom of `main`): no ready describe/produce pipeline is wired for
     a bare `boot_core()` substrate (no conversation/intent/psychology seeds loaded), and
     bolting one on for this script would be new machinery, which this task does not license.
     Honest skip, not a faked utterance.
  5. EXECUTE -- explicitly NOT done here. This script only produces and prints the verdict;
     the chosen branch's build is out of scope (a separate, later task once the verdict is
     committed).

Gate genre: deterministic, PASS/FAIL = "a verdict was produced by held machinery with zero
Python decisions on the path" (WALL / TIE / disagreement all count as a produced verdict --
only an unhandled exception, or Argmax genuinely unable to run, is FAIL). donkey=0: no torch
or any teacher-model import anywhere on this path; asserted at the end.

Run:  PYTHONPATH=.:runners/dsl/python python -m scripts.jabberwock_decides_ink_frontier
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
WILD = "·?·"  # "·?·" == the "\xb7?\xb7" wild marker every AntiUnify/Covers/ShapeDecode call in this codebase uses


# =============================================================================================
# STEP 1 MATERIAL -- eight facts, each a verbatim excerpt from a committed commit message.
# Every fact is cited by commit hash right here, in code, next to the text it names (the
# non-negotiable: "cite the source commit/log line for each relation in comments").
# =============================================================================================

FACT_TEXTS: dict[int, str] = {
    # commit b1bbaf53 ("RUN 13 -- INSTANCE-CONDITIONING NULLS BOTH WAYS ..."): quantized-
    # representation saturation -- an exemplar's own strokes add no geometry beyond the shared
    # quantum classes.
    1: ("at 0% OOV with exact fine-tier matching, an exemplar's own strokes re-quantize "
        "BYTE-IDENTICAL to their global quanta: at this grain, exemplars carry NO quantized "
        "geometry beyond the 7 shared classes."),
    # commit a6c7740f ("RUN 12 -- SECOND MODALITY WINS, TARGETED WIDEN LOSES ..."): the one
    # continuous (non-quantized) lever -- appearance / PointSetDist -- is the one that worked.
    2: ("appearance proposals (held PointSetDist ink-vs-ink, top-3 unioned) lift one-shot "
        "38.8% -> 41.2% at mean budget 4.28. MODALITY OVERLAP: appearance added a candidate "
        "the structural shortlist lacked on 79/80 episodes (98.8%) -- a genuinely "
        "non-overlapping search angle."),
    # commit a6c7740f: the far tail is blind to every search modality tried.
    3: ("FAR TAIL: 0/3 of the proposal-blind cases reachable by ANY arm -- structure-blind, "
        "appearance-blind, width-blind."),
    # CLAUDE.md (committed, gamma-substrate), the Omniglot-arc paragraph: the stroke inventory
    # is tiny; identity is carried by arrangement, not by the stroke vocabulary.
    4: "real strokes occupy ~5-7 quantized classes (identity lives in ARRANGEMENT).",
    # commit 9f1fc077 ("DYNAMIC QUANTIZATION -- segmentation BY REVERSE QUANTIZATION ..."):
    # boundaries emerge from the decode itself, never a static pre-cut.
    5: ("DYNAMIC QUANTIZATION -- segmentation BY REVERSE QUANTIZATION (word-shapes decode the "
        "stream; boundaries EMERGE). word-shapes COMPETE, boundaries EMERGE at the best-match "
        "transitions; an OOV/filler shape absorbs unmatched spans. NO static pre-cut."),
    # commit accb0d47 ("RUN 6 -- EAGER CHILD MINTING lands additive-safe and measures +0.0pp
    # ..."): per-dimension refinement found almost no within-tier variation to mint against.
    6: ("EAGER CHILD MINTING lands additive-safe and measures +0.0pp, an honest null that "
        "RELOCATES the frontier: real strokes occupy ~5-7 quantized classes with almost NO "
        "within-class variation (3 children/3000 strokes) -- the 33.8% is carried by "
        "ARRANGEMENT, and arrangement fidelity is now the residual."),
    # commits 97d54623 ("RUNS 7+8 -- ARRANGEMENT FIDELITY measured three ways; STRICTNESS IS
    # THE SIGNAL ...") + e6a467e8 ("RUN 9 -- rel2 BREAKS THE TIES AND STILL LOSES ..."):
    # strictness-is-the-signal, measured negative (softer scoring) three separate times.
    7: ("STRICTNESS IS THE SIGNAL (naive joint-consistency 33.8% beats per-stroke assignment "
        "30.0% and arrangement-only assignment 30.0%). Branch table verdict: 'ties drop, "
        "accuracy doesn't' -- the ties are broken by long-range quantization noise, not by "
        "signal."),
    # commit a6c7740f: "a different search angle beats more of the same angle" -- at the
    # object-recognition level AND at the meta (lever-choice) level.
    8: ("a DIFFERENT search angle beats more of the same angle, at the meta-level too. "
        "Different angles and better architecture move the frontier; more of the same never "
        "does."),
}

FACT_CITATIONS: dict[int, str] = {
    1: "commit b1bbaf53 (RUN 13 -- instance-conditioning nulls both ways)",
    2: "commit a6c7740f (RUN 12 -- second modality wins)",
    3: "commit a6c7740f (RUN 12 -- far tail)",
    4: "CLAUDE.md, gamma-substrate (committed; the Omniglot-arc paragraph)",
    5: "commit 9f1fc077 (segmentation by reverse quantization)",
    6: "commit accb0d47 (RUN 6 -- eager child minting, honest null)",
    7: "commits 97d54623 (RUNS 7+8) + e6a467e8 (RUN 9) -- strictness is the signal",
    8: "commit a6c7740f (RUN 12 -- different angle beats more of the same)",
}


# =============================================================================================
# STEP 2 MATERIAL -- Branch A / Branch B, each exactly one claim quote (verbatim from the
# design brief handed down for this task) + exactly one cited analogy-source commit message
# (verbatim from `git log`). Same arity (2 texts each), same mechanism, no extra material for
# either side.
# =============================================================================================

# Verbatim from the design brief's "THE JABBERWOCK DECIDES THE FORK" section, step 2.
BRANCH_A_NAME = "branch_a_substroke_composition"
BRANCH_A_CLAIM = "the part is itself an arrangement; identity one level down; the sd loop recurses"
BRANCH_A_SOURCE_COMMIT = "c1b83669"
BRANCH_A_SOURCE_TITLE = ("CHARACTER COMPOSITION -- the SAME loop one level up carries "
                          "one-shot Omniglot ABOVE CHANCE")
BRANCH_A_SOURCE_TEXT = """CHARACTER COMPOSITION -- the SAME loop one level up carries one-shot Omniglot ABOVE CHANCE: 33.8% vs 5% (shuffled 2.5%), ablation +28.8pp = composition's measured value; transform-explanation restored 100%; a latent tuple-vs-list bug had made refinement child-minting INERT on real ink (fixed)

The 26df120c residual closed. A character is an order-N object of stroke quanta +
RELATIVE poses, and its signature is ShapeSignature-format (strokeq + rel + cpose
relations in the character frame) -- so characters ARE quanta of stroke-arrangements,
minted/recognized through the UNCHANGED sd rules (kind='character'; no new Rust, no new
sd machinery). The recursion is real: same decode loop at stroke grain and character
grain.

Levers landed:
(b) POSE READ-OFF IN ALL TIERS: coarse/DtwTo recognitions now splice observed pose onto
the parent's stored seg and run the same TransformDecode read-off as the fine tier --
transform-explanation rate restored 6.9% -> 100.0%.
(a) REFINEMENT-TREE IDENTITY: the deepest-matching child id is the stroke's identity in
downstream signatures (family/refine provenance attrs). EN ROUTE, A REAL BUG:
_fine_seg_relations filtered isinstance(list) but live native.evaluate() returns
TUPLES -- the refinement rung's child-minting was silently INERT on real ink (every
_refine_or_note returned None). Fixed (both sites); LEARN codebook now folds jitter
into coarse+children properly (28 -> 7 top-level quanta, honest side effect of the fix,
not tuning).
(c) COMPOSITION (domains/character_compose.py): character frame = translate+rotate+
scale-normalized; strokeq/rel/cpose relations quantized with the existing bins
vocabulary; grow_character_quantum via teach (seeds/character_shapes.json, mechanical
byproduct like stroke_shapes).

GATES (tests/test_character_composition_migrated.py, 5 + audit): T/L/+ from an
IDENTICAL stroke multiset (tie proven) classify correctly by arrangement -- the lever-(c)
proof; whole-character translate/scale recognize via the unchanged sd_transform_decode
with zero mint; pose read-off proven restored (unfixed signature proven NOT to explain);
child-id identity; character sd loop mints exactly once then recognizes. Old ink gates
20/20 unchanged. Migrated bench 642 -> 648 green (canonical env; the venv lacks
cv2/chess).

OMNIGLOT THIRD RUN (same protocol/caps, 148.9s, results/omniglot_gate_composition_rerun
.log): ONE-SHOT COMPOSED 33.8% vs 5% chance, shuffled control 2.5% (below chance) --
real, non-artifactual. Multiset ablation control: exactly chance (5.0%/5.0%) -- with 7
top-level quanta multiset ties dominate; the +28.8pp delta IS composition's measured
contribution. OOV 0%, LEARN saturation PASS, donkey=0. Run trajectory: 2.5% (exact-
match, 81% OOV) -> 3.8% (coarseness, signal appears) -> 33.8% (arrangement) -- each
gate's named residual was the next commit's lever.

NEXT RESIDUALS (named): character-level rung 1 handles translate/scale but combined
rotate+scale+translate exceeds the seeded max_dims=2 and cpose_x/y are axis-aligned-
bbox-relative (not rotation-invariant) -- same self-bbox limitation strokes carry;
absolute accuracy is bounded by the tiny stroke vocabulary (7 top-level quanta) --
richer refinement-child discrimination is the natural next lever."""

BRANCH_B_NAME = "branch_b_junction_coarticulation"
BRANCH_B_CLAIM = ("context conditions the part at its boundary; the junction carries the "
                   "signal; segment-and-recognize jointly")
BRANCH_B_SOURCE_COMMIT = "ffa12c7b"
BRANCH_B_SOURCE_TITLE = ("R1 closed DECISIVELY -- TRUE-speaker + PIECEWISE VTLN + SCORED "
                          "broadcast: residual is COARTICULATION, not VTL")
BRANCH_B_SOURCE_TEXT = """R1 closed DECISIVELY -- TRUE-speaker + PIECEWISE VTLN + SCORED broadcast: residual is COARTICULATION, not VTL

eef431b7 left R1 on an honest fork: VTLN was positive-control-validated (removes 114% of a KNOWN
injected tract warp) but did NOT beat additive-delta on the phonebank -- plausibly the PSEUDO-speaker
confound (phonebank has no speaker IDs, so the test used timbre k-means groups that are internally
mixed, under-fitting a single per-group warp). This closes it by removing the confound and finishing
the two named levers + the never-scored broadcast payoff.

BUILD: re-extract cochleagrams from the RAW LibriSpeech tree with TRUE per-utterance speaker IDs
(from /home/matt/data/LibriSpeech/dev-clean/<SPEAKER>/...); per-TRUE-speaker linear VTLN AND a PIECEWISE
per-formant-region warp (3 band regions, greedy 2-pass grid). SCORE the broadcast tier (Sesame,
streamed) order-1 purity against whisper word-timestamp labels. donkey=0: the DECISION path (VTLN =
numpy freq-warp, clustering = held DtwTo Rust Term) is torch-free; MMS_FA alignment + whisper run in
ISOLATED subprocesses that write UNCOMMITTED scratch cochleagram caches (never committed, regenerable);
the analyze process imports NO torch/torchaudio/allosaurus/faster_whisper (verified in sys.modules).
Memory: streamed per-utterance, ulimit-14Gi, float32; extract peak 2.7 GiB, analyze peak 0.88 GiB.

Fixed a measurement confound from eef431b7: snap_scan picks a DIFFERENT tau per mode, so its
cross-speaker purity is not comparable across modes (coarser clustering inflates agreement). Replaced
with a FAIR tau-free metric: same-word cross-speaker nearest-neighbour RECALL (toward 1.0/0.99) +
same-word cross-speaker DTW distance.

DECISIVE RESULT (6 true speakers, 1600 tokens): with TRUE IDs + piecewise warp, NO normalization beats
raw on the fair metric -- NN-recall raw 0.283 -> delta 0.294 -> vtln 0.289 -> piecewise 0.294, and the
SHUFFLED-speaker control (0.294) TIES delta/piecewise (the warp contributes nothing). KEY INSIGHT: delta
compresses cross-speaker DISTANCE hugely (0.765->0.416, -46%) yet NN-recall does NOT rise (0.28->0.29) --
a GLOBAL speaker transform (additive OR multiplicative VTL) rescales all distances but does NOT fix
same-word-vs-different-word RANKING. The cross-speaker residual is therefore NOT the multiplicative VTL
warp and NOT primarily the additive offset -- it is COARTICULATION/phonetic-context (the same word differs
by sentence context). Broadcast CONFIRMS: scored order-1 purity does NOT lift (raw 0.640 -> VTLN 0.591).
Phonetics preserved (o1-purity 0.408 unchanged; gate-C spec 0.409 vs base 0.290/sh 0.270 FLIP on
true-speaker data). donkey=0 True.

The VTLN machinery is validated but LOW-LEVERAGE on real speech: the lever definitively shifts to
CONTEXT-modeling (R2 frame-coverage / R3 category), NOT speaker-normalization. NOT irreducible -- named
precisely as coarticulation/phonetic-context, the next build target. Either outcome was decisive; this is
the negative one, cleanly established with true speaker labels + a fair metric + a scored broadcast tier."""


# =============================================================================================
# Mechanical helpers -- glue code calling HELD Terms. None of these contain a decision over
# graph state; every ranking is done by a real `Argmax` Term call, every score by a real
# `ShapeDecode`/`TransformDecode`/`AntiUnifyWitness`/`FixedCount` Term call.
# =============================================================================================

def _author(sub, name: str, text: str) -> list:
    """Install a scratch Concept carrying `text` as its `definition`, then run the agent's OWN
    held signature-authoring mechanism over it (`reflective_faculty.author_signature` -- the
    exact function that authors every ShapeSignature already in this codebase, e.g.
    `seeds/math_capability_shapes.json`). Mechanical I/O (one node write + one call to an
    existing, unmodified held function) -- no new matching logic, no decision."""
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
    mechanical read-out, not a decision (mirrors `induce_concern`'s own mechanical field
    reads of terminal decode status)."""
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
    are unambiguously (a's diff, b's diff) -- Set iteration order is not a contract this
    script should lean on."""
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
    tied for that pick, per the non-negotiable that a tie must be surfaced, not hidden
    behind whatever tie-break the Argmax Term's implementation happens to apply."""
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
    print("THE JABBERWOCK DECIDES THE FORK")
    print("sub-stroke grain composition  vs  junction coarticulation of stroke boundaries")
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
    print(f"\n{SEP}\nSTEP 1 -- EVIDENCE AS GRAPH DATA (verbatim commit-message facts, run through "
          f"the held RelationCue signature-authoring mechanism)\n{SEP}")
    fact_sigs = {}
    for i in sorted(FACT_TEXTS):
        fact_sigs[i] = _author(s, f"ink_frontier_fact_{i}", FACT_TEXTS[i])
        print(f"\n  FACT {i}  [{FACT_CITATIONS[i]}]")
        print(f"    text: {FACT_TEXTS[i]}")
        print(f"    fired relations:\n{_fmt_sig(fact_sigs[i], indent='      ')}")
    evidence_sig = _dedup_union(fact_sigs.values())
    print(f"\n  EVIDENCE (union of all 8 facts, deduped, {len(evidence_sig)} relations):")
    print(_fmt_sig(evidence_sig))

    # =========================================================================================
    # STEP 2 -- BRANCHES AS CANDIDATE SHAPES (same vocabulary, same mechanism, same rigor)
    # =========================================================================================
    print(f"\n{SEP}\nSTEP 2 -- BRANCHES AS CANDIDATE SHAPES\n{SEP}")

    a_claim_sig = _author(s, "branch_a_claim", BRANCH_A_CLAIM)
    a_source_sig = _author(s, "branch_a_source", BRANCH_A_SOURCE_TEXT)
    branch_a_sig = _dedup_union([a_claim_sig, a_source_sig])

    b_claim_sig = _author(s, "branch_b_claim", BRANCH_B_CLAIM)
    b_source_sig = _author(s, "branch_b_source", BRANCH_B_SOURCE_TEXT)
    branch_b_sig = _dedup_union([b_claim_sig, b_source_sig])

    print(f"\n  BRANCH A -- sub-stroke composition ({BRANCH_A_NAME})")
    print(f"    claim (design brief, verbatim): {BRANCH_A_CLAIM!r}")
    print(f"      fired relations:\n{_fmt_sig(a_claim_sig)}")
    print(f"    analogy source [commit {BRANCH_A_SOURCE_COMMIT}: {BRANCH_A_SOURCE_TITLE!r}]")
    print(f"      fired relations:\n{_fmt_sig(a_source_sig)}")
    print(f"    BRANCH A SIGNATURE (union, {len(branch_a_sig)} relations):")
    print(_fmt_sig(branch_a_sig))

    print(f"\n  BRANCH B -- junction coarticulation ({BRANCH_B_NAME})")
    print(f"    claim (design brief, verbatim): {BRANCH_B_CLAIM!r}")
    print(f"      fired relations:\n{_fmt_sig(b_claim_sig)}")
    print(f"    analogy source [commit {BRANCH_B_SOURCE_COMMIT}: {BRANCH_B_SOURCE_TITLE!r}]")
    print(f"      fired relations:\n{_fmt_sig(b_source_sig)}")
    print(f"    BRANCH B SIGNATURE (union, {len(branch_b_sig)} relations):")
    print(_fmt_sig(branch_b_sig))

    if not branch_a_sig and not branch_b_sig:
        print("\n  WALL: neither branch's claim+source text grounds to ANY held RelationCue. "
              "Honest -- not forced.")

    # scratch, episode-scoped codebook holding ONLY the two branches (nothing persists; the
    # main substrate `s` never sees these two nodes) -- the run-13 "instance-scoped scratch
    # substrate" precedent (b1bbaf53 / a6c7740f) applied here to keep the branch-only decode
    # cleanly separated from the agent's real held codebook.
    scratch = srs.Substrate()
    scratch.add_node("ShapeSignature", {"name": BRANCH_A_NAME, "kind": "frontier_branch",
                                         "signature": json.dumps(branch_a_sig)})
    scratch.add_node("ShapeSignature", {"name": BRANCH_B_NAME, "kind": "frontier_branch",
                                         "signature": json.dumps(branch_b_sig)})
    scratch_native = scratch._inner

    # =========================================================================================
    # STEP 3a -- COVERAGE/FIT PATH (ShapeDecode + TransformDecode)
    # =========================================================================================
    print(f"\n{SEP}\nSTEP 3a -- COVERAGE/FIT PATH (held ShapeDecode / TransformDecode)\n{SEP}")

    decode_a = _shape_decode(scratch_native, evidence_sig, exclude=[BRANCH_B_NAME])
    decode_b = _shape_decode(scratch_native, evidence_sig, exclude=[BRANCH_A_NAME])
    decode_both = _shape_decode(scratch_native, evidence_sig)          # informational only
    decode_full = _shape_decode(native, evidence_sig)                  # main substrate: real codebook

    td_a = _transform_decode(scratch_native, evidence_sig, exclude=[BRANCH_B_NAME])
    td_b = _transform_decode(scratch_native, evidence_sig, exclude=[BRANCH_A_NAME])
    td_full = _transform_decode(native, evidence_sig)

    cov_a = _coverage_fraction(evidence_sig, decode_a)
    cov_b = _coverage_fraction(evidence_sig, decode_b)
    cov_full = _coverage_fraction(evidence_sig, decode_full)
    full_parts = list(decode_full.get("ordered_parts") or [])
    full_label = f"neither -- best held coverage uses {full_parts!r}" if full_parts else \
                 "neither -- no held shape covers any evidence relation"

    print(f"\n  Branch A solo (Branch B excluded from the 2-shape codebook):")
    print(f"    ShapeDecode:     coverage={cov_a:.3f} ({decode_a.get('covered_count')}/"
          f"{decode_a.get('goal_relations')})  total_fit={decode_a.get('total_fit')}  "
          f"plan={decode_a.get('ordered_parts')}  residual={decode_a.get('residual')}")
    print(f"    TransformDecode: explained={td_a.get('explained')}  base={td_a.get('base')}  "
          f"dims={td_a.get('dims')}  deltas={td_a.get('deltas')}  identity={td_a.get('identity')}")

    print(f"\n  Branch B solo (Branch A excluded from the 2-shape codebook):")
    print(f"    ShapeDecode:     coverage={cov_b:.3f} ({decode_b.get('covered_count')}/"
          f"{decode_b.get('goal_relations')})  total_fit={decode_b.get('total_fit')}  "
          f"plan={decode_b.get('ordered_parts')}  residual={decode_b.get('residual')}")
    print(f"    TransformDecode: explained={td_b.get('explained')}  base={td_b.get('base')}  "
          f"dims={td_b.get('dims')}  deltas={td_b.get('deltas')}  identity={td_b.get('identity')}")

    print(f"\n  Both branches available (composed plan, INFORMATIONAL ONLY -- not a decision "
          f"input): plan={decode_both.get('ordered_parts')}  total_fit={decode_both.get('total_fit')}  "
          f"coverage={_coverage_fraction(evidence_sig, decode_both):.3f}")

    print(f"\n  Full held codebook ({len(held_sigs)} real ShapeSignature nodes -- "
          f"math_capability_shapes + stroke_shapes + character_shapes; branches ABSENT):")
    print(f"    ShapeDecode:     coverage={cov_full:.3f} ({decode_full.get('covered_count')}/"
          f"{decode_full.get('goal_relations')})  total_fit={decode_full.get('total_fit')}  "
          f"plan={full_parts}  residual={decode_full.get('residual')}")
    print(f"    TransformDecode: explained={td_full.get('explained')}  base={td_full.get('base')}  "
          f"dims={td_full.get('dims')}  deltas={td_full.get('deltas')}  identity={td_full.get('identity')}")

    coverage_pairs = [[cov_a, BRANCH_A_NAME], [cov_b, BRANCH_B_NAME], [cov_full, full_label]]
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

    tmpl_a, sig_a_wit, fixed_a = _antiunify_witness(native, evidence_sig, branch_a_sig)
    tmpl_b, sig_b_wit, fixed_b = _antiunify_witness(native, evidence_sig, branch_b_sig)
    print(f"\n  evidence <-> Branch A: shared_leaves(FixedCount)={fixed_a}")
    print(f"    template: {tmpl_a}")
    print(f"    witness (evidence's diff-map): {sig_a_wit[0] if sig_a_wit else {}}")
    print(f"    witness (Branch A's diff-map): {sig_a_wit[1] if len(sig_a_wit) > 1 else {}}")
    print(f"\n  evidence <-> Branch B: shared_leaves(FixedCount)={fixed_b}")
    print(f"    template: {tmpl_b}")
    print(f"    witness (evidence's diff-map): {sig_b_wit[0] if sig_b_wit else {}}")
    print(f"    witness (Branch B's diff-map): {sig_b_wit[1] if len(sig_b_wit) > 1 else {}}")

    # closest_held_shape over the FULL real codebook -- Python only iterates to compute each
    # candidate's Rust-computed score (`_antiunify_witness`/`FixedCount`); the winner is the
    # held Argmax below, exactly `seeds/shape_decode_loop.json`'s own mechanism, generalized to
    # keep the witness diffs.
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
    analogical_pairs = [[fixed_a, BRANCH_A_NAME], [fixed_b, BRANCH_B_NAME],
                         [closest_held_fixed, analogical_label_neither]]
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
          "which the brief does not license ('skip cleanly if the language seeds make it "
          "heavy'). Honest skip, not a faked utterance.")

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
