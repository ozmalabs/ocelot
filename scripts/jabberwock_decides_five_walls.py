"""THE JABBERWOCK DECIDES THE FORK, THIRD INVOCATION (five-walls fork).

The jabberwock's SECOND fork decision (`scripts/jabberwock_decides_representation.py`,
commit f492c1b1) DECLINED both representation rebuilds it was offered ("neither: my held
codebook explains the evidence" on the coverage path; branch C -- "close the corridor,
pursue the verdict layer" -- on the analogy path; disagreement reported per protocol,
operational convergence: no rebuild). Since then, FIVE independent runs (25/26-27/28/29/31)
have each hit a wall from a different angle, all pointing the same direction: verdict
saturated, reading never mints, span-shredding shields the grain, import is calibration
not geometry, geometry residual unreachable from the render side. The creator's instruction:
"re-pose the fork to the jabberwock with the new evidence and execute the decision."

This is the fork-decision protocol (d2cd7bed / f492c1b1) exercised a THIRD time, on a
three-way fork (Representation change / Transfer to speech / Consolidate), following the
exact structure of both precedents:

  1. EVIDENCE AS GRAPH DATA -- the five walls, each a VERBATIM quote (as handed down in the
     task brief, itself copy-pasted from the named commit's own message -- copy-paste
     discipline, not paraphrase) run through the agent's own held signature-authoring
     mechanism (`domains/reflective_faculty.py::author_signature`). Deduped union -> ONE
     evidence relation-system, exactly the precedents' Step 1.
  2. BRANCHES AS CANDIDATE SHAPES -- Option R / Option T / Option C are each authored from
     EXACTLY the same two ingredients, same mechanism, same rigor: (i) the option's ONE
     definition clause, verbatim from the task brief's "OPTION R / OPTION T / OPTION C"
     paragraphs; (ii) the option's ONE counter-evidence block, verbatim from the task
     brief's "Against R / Against T / Against C" paragraphs. This differs from the first
     two precedents' second ingredient (a freshly-picked analogy-source commit) only
     because THIS task brief already hands down a dedicated, symmetric counter-evidence
     block per option and explicitly names symmetry as the requirement ("COUNTER-EVIDENCE
     -- symmetry demands these be encoded with equal care") -- reusing that supplied
     material, rather than picking a fourth new commit per branch, is the more literal
     "copy-paste, don't paraphrase, don't add material one side doesn't have" reading of
     the same non-negotiable the precedents established. Both precedents also happily used
     UNFLATTERING/negative-result sources as a branch's second ingredient (representation
     fork's branch A cited a decisive NEGATIVE finding on its own claim; ink-frontier's
     branch B cited ffa12c7b, a NEGATIVE result), so grounding each option in ITS OWN
     counter-evidence is squarely inside that precedent, not outside it. No option gets
     extra material another doesn't: same two-ingredient arity, same authoring call.
  3. THE DECISION IS THE AGENT'S HELD OPERATOR -- two independent paths, both against BOTH
     the three-branch codebook (a throwaway scratch substrate, nothing persisted) and the
     agent's OWN full held ShapeSignature codebook (thousands of real nodes -- so "neither"
     is a real, competing candidate):
       (a) COVERAGE/FIT: `ShapeDecode` + `TransformDecode`.
       (b) ANALOGICAL: `AntiUnifyWitness` (template + per-instance diff witnesses) +
           `FixedCount`, mirroring `seeds/shape_decode_loop.json`'s own `closest_held_shape`
           mechanism but keeping the witnessed differences for the trace.
     Each path's final pick is a held `Argmax` Term over a 4-way literal list
     [option_r, option_t, option_c, neither]. Ties are detected (by inspecting the SAME
     scores handed to Argmax -- reporting, not deciding) and printed, never silently broken.
  4. VOICE -- skipped, honestly, for the same reason as both precedents: this script boots
     a bare `boot_core()` (no conversation/intent/psychology seeds), and no describe/produce
     pipeline is wired for that substrate.
  5. EXECUTE -- explicitly NOT performed here. This script prints, for the WINNING option
     only, one paragraph of "what execution means" -- mechanically derived from that
     option's own definition clause (a fixed, pre-written lookup keyed by option name, not
     a decision over graph state) -- and stops. Building the winning option is a separate,
     later task once the verdict is committed.

Gate genre: deterministic, PASS/FAIL = "a verdict was produced by held machinery with zero
Python decisions on the path" (WALL / TIE / disagreement all count as a produced verdict --
only an unhandled exception, or Argmax genuinely unable to run, is FAIL). donkey=0: no torch
or any teacher-model import anywhere on this path; asserted at the end.

Run:  PYTHONPATH=.:runners/dsl/python python3 -m scripts.jabberwock_decides_five_walls \
        2>&1 | tee results/jabberwock_decides_five_walls.log
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
# STEP 1 MATERIAL -- the five walls, each a verbatim excerpt as handed down in the task brief
# (itself copy-pasted from the named commit's own message). Cited by commit hash right here.
# =============================================================================================

FACT_TEXTS: dict[int, str] = {
    # commit 6da31cee (RUN 25): the verdict layer, six independent nulls deep.
    1: ("SIX independent nulls... the ~80.5-81.5 number is this featureset's verdict-layer "
        "ceiling"),
    # commit 41afebb7 (RUNS 26-27): the homework loop reads at the wrong grain -- reading
    # never mints because the fallback tier has no calibrated "I don't know".
    2: ("READING NEVER MINTS -- the 7-quantum stroke ladder's dtw fallback always matches "
        "-- and the grain mismatch: residual at ARRANGEMENT grain"),
    # commit 9ca19365 (RUN 28): the segmenter shields the grain from ever seeing novelty,
    # and identity is collapsed into essentially one family.
    3: ("SPAN-SHREDDING shields the grain -- at min_span=2 the lattice re-cuts any "
        "unfamiliar shape into familiar fragments before the rejection tier sees it; "
        "identity collapse \"10,230/10,231 spans in ONE family\""),
    # commit 0da44354 (RUN 29): consumption is wired and it teaches by nulling precisely --
    # what was imported is calibration, not geometry.
    4: ("what was imported is CALIBRATION not GEOMETRY... down-weighting is measurement "
        "calibration, not repair; the unweighted 0.8356 never moves"),
    # commit bb9e0fe4 (RUN 31): both creator-named render-side attacks null; the geometry
    # residual is not reachable from that side -- the fidelity ceiling, measured a fifth way.
    5: ("THE GEOMETRY RESIDUAL IS NOT REACHABLE FROM THE RENDER SIDE... the ~0.84 "
        "unweighted round-trip is this quantized featureset's FIDELITY CEILING -- the "
        "practice-loop twin of the verdict ceiling, the sub-quantum signal (run 13's "
        "terminus) measured from a fifth direction"),
}

FACT_CITATIONS: dict[int, str] = {
    1: "commit 6da31cee (RUN 25 -- verdict saturated, six independent nulls)",
    2: "commit 41afebb7 (RUNS 26-27 -- the homework loop, reading never mints)",
    3: "commit 9ca19365 (RUN 28 -- span-shredding shields the grain)",
    4: "commit 0da44354 (RUN 29 -- consumption wired, calibration not geometry)",
    5: "commit bb9e0fe4 (RUN 31 -- geometry residual unreachable from the render side)",
}


# =============================================================================================
# STEP 2 MATERIAL -- Option R / Option T / Option C, each exactly one claim clause (verbatim
# from the task brief's own "OPTION R/T/C" paragraphs) + exactly one counter-evidence block
# (verbatim from the task brief's own "Against R/T/C" paragraphs). Same arity (2 texts each),
# same mechanism, no extra material for any side.
# =============================================================================================

OPTION_R_NAME = "option_r_representation_change"
OPTION_R_CLAIM = ("attack the bin grain itself (sub-quantum featureset: finer/adaptive "
                   "quantization or continuous-valued relations in the learning/proposal "
                   "layer)")
OPTION_R_COUNTER_LABEL = "counter-evidence against R (task brief, verbatim)"
OPTION_R_COUNTER = (
    "f492c1b1's own grounds (the agent already declined rebuilds once); run 14 (9f10cf74) "
    "\"sub-stroke codebook collapses to 4 quanta — the saturation RECURSES downward\"; "
    "run 9/14's law \"added quantized relations at longer range carry cross-drawer "
    "noise... at TWO independent grains\"; run 16 (7743c2de) \"bins propose, continuous "
    "decides\" — the CONTINUOUS verdict layer ALREADY harvests sub-bin signal (SC+TPS full "
    "dwell 84.8 at 50-way), so a finer featureset must beat an existing consumer of the "
    "same signal; run 25: \"only architecture moved the frontier; metric surgery never did\"."
)

OPTION_T_NAME = "option_t_transfer_to_speech"
OPTION_T_CLAIM = (
    "carry the earned domain-general machinery (homework loop, frames/weight-edges, CFAR "
    "novelty calibration, arrangement codebook) to SPEECH — the reading↔speaking loop is "
    "the architecture's own frame (\"you get better at speaking by reading\"; one model "
    "looped back), and the speech arc has named open problems these tools address "
    "(weak-teacher bootstrap null 8b54bc3a, real-audio decode Wall B, salience-residual "
    "loop 4bca77bc)"
)
OPTION_T_COUNTER_LABEL = "counter-evidence against T (task brief, verbatim)"
OPTION_T_COUNTER = (
    "the speech-side teacher is weak (8b54bc3a: \"bootstrap ~19% < AbS-alone ~22-24%\"); "
    "cross-domain transfer of structure is proven but acceleration was an honest null "
    "there; leaving ink now leaves the 96.7-BPL target unattempted at the representation "
    "level."
)

OPTION_C_NAME = "option_c_consolidate"
OPTION_C_CLAIM = ("accept the measured ceilings (80.5 verdict / 96.7 zero-adaptation "
                   "transfer / 0.84 fidelity), write the arc up as complete, no new build")
OPTION_C_COUNTER_LABEL = "counter-evidence against C (task brief, verbatim)"
OPTION_C_COUNTER = (
    "the creator's standing frame \"there is no impractical grind: speech is HARD but "
    "TRACTABLE\" (tractable-not-impractical, 2026-06-30) — a ceiling on ONE featureset is "
    "not a terminus for the CAPABILITY; the machinery is built to be re-aimed, and "
    "consolidation forecloses measurement."
)

OPTIONS = [
    (OPTION_R_NAME, OPTION_R_CLAIM, OPTION_R_COUNTER_LABEL, OPTION_R_COUNTER),
    (OPTION_T_NAME, OPTION_T_CLAIM, OPTION_T_COUNTER_LABEL, OPTION_T_COUNTER),
    (OPTION_C_NAME, OPTION_C_CLAIM, OPTION_C_COUNTER_LABEL, OPTION_C_COUNTER),
]

# What execution means for each option, IF it wins -- one paragraph each, mechanically
# derived from that option's own definition clause above (a fixed lookup by name, not a
# decision over graph state; printed only for the winner).
EXECUTION_MEANING = {
    OPTION_R_NAME: (
        "EXECUTION (Option R -- representation change): a run-32 sub-quantum featureset "
        "gate. Build the sub-quantum lever the option's own clause names -- either finer/"
        "adaptive quantization of the existing StrokeQuantize bins, or continuous-valued "
        "relations threaded through the learning/proposal layer (strokeq/rel/cpose) while "
        "leaving the verdict layer's SC+TPS continuous comparator untouched -- arm it "
        "behind a flag, byte-identical with the flag off, and gate it on the SAME "
        "protected control the five walls were measured against (n=400, powered Wilson "
        "CIs, weighted vs unweighted arrangement, coverage@5) so a null reproduces the "
        "0.8356/0.84 ceiling exactly and a real lift is CI-separated from it, per the "
        "counter-evidence's own bar: it must beat the existing continuous-verdict "
        "consumer of the same signal, not merely move a quantized proxy metric."
    ),
    OPTION_T_NAME: (
        "EXECUTION (Option T -- transfer to speech): a speech-homework transfer gate. "
        "Re-point the SAME four domain-general modules the ink arc earned -- the homework "
        "loop (mark/assign/babble/cycle), the Frame weight-edge machinery (log-odds "
        "reliability per axis), the CFAR novelty-calibration threshold, and the "
        "arrangement-grain codebook growth path -- at the speech substrate's named open "
        "walls (8b54bc3a's weak-teacher bootstrap null, the real-audio decode Wall B, and "
        "4bca77bc's salience-residual loop), wire them behind a flag so the ink path stays "
        "byte-identical, and gate on the reading↔speaking loop's OWN falsifiable claim: "
        "grounding one side measurably improves the other (shared-M vs a separate-models "
        "ablation), reporting the transfer honestly even if it nulls the way 8b54bc3a's "
        "acceleration attempt did."
    ),
    OPTION_C_NAME: (
        "EXECUTION (Option C -- consolidate): an arc write-up document. No new build: "
        "compile the ink arc's full ledger (runs 1-31, the five-wall terminus, the "
        "80.5% verdict ceiling / 96.7% zero-adaptation transfer / 0.84 unweighted "
        "fidelity ceiling, and every honest null and its named cause) into a single "
        "closing document, cite every commit verbatim rather than re-deriving the "
        "numbers, and stop -- leaving the machinery in place, unexercised, for a future "
        "re-aim rather than a further ink-arc build."
    ),
}


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
    print("THE JABBERWOCK DECIDES THE FORK (third invocation) -- FIVE WALLS")
    print("representation change  vs  transfer to speech  vs  consolidate")
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
    # STEP 1 -- EVIDENCE AS GRAPH DATA (the five walls)
    # =========================================================================================
    print(f"\n{SEP}\nSTEP 1 -- EVIDENCE AS GRAPH DATA (the five walls, verbatim commit-message "
          f"facts, run through the held RelationCue signature-authoring mechanism)\n{SEP}")
    fact_sigs = {}
    for i in sorted(FACT_TEXTS):
        fact_sigs[i] = _author(s, f"five_walls_fact_{i}", FACT_TEXTS[i])
        print(f"\n  FACT {i}  [{FACT_CITATIONS[i]}]")
        print(f"    text: {FACT_TEXTS[i]}")
        print(f"    fired relations:\n{_fmt_sig(fact_sigs[i], indent='      ')}")
    evidence_sig = _dedup_union(fact_sigs.values())
    print(f"\n  EVIDENCE (union of all {len(FACT_TEXTS)} facts, deduped, {len(evidence_sig)} "
          f"relations):")
    print(_fmt_sig(evidence_sig))

    # =========================================================================================
    # STEP 2 -- OPTIONS AS CANDIDATE SHAPES (same vocabulary, same mechanism, same rigor)
    # =========================================================================================
    print(f"\n{SEP}\nSTEP 2 -- OPTIONS AS CANDIDATE SHAPES\n{SEP}")

    option_sigs = {}
    for name, claim, counter_label, counter_text in OPTIONS:
        claim_sig = _author(s, f"{name}_claim", claim)
        counter_sig = _author(s, f"{name}_counter", counter_text)
        option_sig = _dedup_union([claim_sig, counter_sig])
        option_sigs[name] = option_sig

        print(f"\n  {name.upper()}")
        print(f"    claim (verbatim, task brief's own OPTION paragraph): {claim!r}")
        print(f"      fired relations:\n{_fmt_sig(claim_sig)}")
        print(f"    {counter_label}: {counter_text!r}")
        print(f"      fired relations:\n{_fmt_sig(counter_sig)}")
        print(f"    {name.upper()} SIGNATURE (union, {len(option_sig)} relations):")
        print(_fmt_sig(option_sig))
        if not option_sig:
            print(f"    DISCLOSURE: {name} fires ZERO held RelationCue relations from its "
                  f"claim+counter-evidence text. Honest -- not forced.")

    # scratch, episode-scoped codebook holding ONLY the three options (nothing persists; the
    # main substrate `s` never sees these three nodes) -- the same instance-scoped scratch
    # substrate precedent both prior fork-decision scripts applied.
    scratch = srs.Substrate()
    for name, _claim, _cl, _ct in OPTIONS:
        scratch.add_node("ShapeSignature", {"name": name, "kind": "frontier_branch",
                                             "signature": json.dumps(option_sigs[name])})
    scratch_native = scratch._inner
    option_names = [o[0] for o in OPTIONS]

    # =========================================================================================
    # STEP 3a -- COVERAGE/FIT PATH (ShapeDecode + TransformDecode)
    # =========================================================================================
    print(f"\n{SEP}\nSTEP 3a -- COVERAGE/FIT PATH (held ShapeDecode / TransformDecode)\n{SEP}")

    cov_pairs = []
    for name in option_names:
        others = [n for n in option_names if n != name]
        decode_solo = _shape_decode(scratch_native, evidence_sig, exclude=others)
        td_solo = _transform_decode(scratch_native, evidence_sig, exclude=others)
        cov = _coverage_fraction(evidence_sig, decode_solo)
        cov_pairs.append([cov, name])
        print(f"\n  {name} solo (other two options excluded from the 3-shape codebook):")
        print(f"    ShapeDecode:     coverage={cov:.3f} ({decode_solo.get('covered_count')}/"
              f"{decode_solo.get('goal_relations')})  total_fit={decode_solo.get('total_fit')}  "
              f"plan={decode_solo.get('ordered_parts')}  residual={decode_solo.get('residual')}")
        print(f"    TransformDecode: explained={td_solo.get('explained')}  "
              f"base={td_solo.get('base')}  dims={td_solo.get('dims')}  "
              f"deltas={td_solo.get('deltas')}  identity={td_solo.get('identity')}")

    decode_all = _shape_decode(scratch_native, evidence_sig)   # all three available, informational only
    print(f"\n  All three options available (composed plan, INFORMATIONAL ONLY -- not a "
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
          f"math_capability_shapes + stroke_shapes + character_shapes; options ABSENT):")
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
    for name in option_names:
        tmpl, wit, fixed = _antiunify_witness(native, evidence_sig, option_sigs[name])
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
    analogical_pairs = [[fixed_by_name[n], n] for n in option_names] + \
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

    verdict_option = None
    if coverage_clean is not None and coverage_clean == analogical_clean:
        print(f"\n  BOTH PATHS AGREE: {coverage_clean!r}")
        print("  THE JABBERWOCK'S VERDICT: " + coverage_clean)
        verdict_kind = "AGREEMENT"
        verdict_option = coverage_clean
    else:
        print("\n  THE PATHS DO NOT CLEANLY AGREE (a tie in at least one path, and/or the two "
              "paths naming different winners). Per the non-negotiable, this disagreement/tie "
              "IS the verdict -- it is reported here, not resolved by this script:")
        print(f"    coverage/fit path candidates: {coverage_pairs} -> pick {coverage_pick}")
        print(f"    analogical path candidates:   {analogical_pairs} -> pick {analogical_pick}")
        print("  THE JABBERWOCK'S VERDICT: TIE / DISAGREEMENT (see above) -- not resolved here.")
        verdict_kind = "TIE_OR_DISAGREEMENT"

    # =========================================================================================
    # EXECUTION MEANING -- printed ONLY if a clean single-option verdict was reached, via a
    # fixed lookup keyed by the winning option's name (not a decision over graph state; the
    # decision already happened above, this only formats its consequence).
    # =========================================================================================
    print(f"\n{SEP}\nWHAT EXECUTION MEANS\n{SEP}")
    if verdict_option in EXECUTION_MEANING:
        print(f"  {EXECUTION_MEANING[verdict_option]}")
    else:
        print(f"  No single option cleanly won ({verdict_kind}), so no execution-meaning "
              f"paragraph is printed -- per protocol, a tie/disagreement is reported back to "
              f"the creator, not broken here.")

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
    print("EXECUTION: explicitly NOT performed by this script -- the verdict (and, if clean, "
          "its execution-meaning paragraph) is reported for the caller to commit; building "
          "the chosen option is a separate, later task.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
