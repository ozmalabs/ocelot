"""THE JABBERWOCK DECIDES THE LOOP-FLIP (run 53 -- a FORK-DECISION session, no eval).

Follows the fork-decision protocol EXACTLY, as established by three precedents:
`scripts/jabberwock_decides_ink_frontier.py` (d2cd7bed, two-branch), `scripts/
jabberwock_decides_representation.py` (f492c1b1, three-branch), and `scripts/
jabberwock_decides_five_walls.py` (df70601e, three-option re-pose): evidence-as-
verbatim-quoted-facts through the agent's OWN `author_signature` RelationCue
mechanism, symmetric option encoding (each option = exactly one verbatim claim
clause + one verbatim for/against evidence block, same arity, same rigor for
every option), dual-path verdict (held `ShapeDecode`/`TransformDecode`
coverage/fit, AND held `AntiUnifyWitness`/`FixedCount` analogical closest-shape)
against BOTH a scratch three-option codebook and the agent's full held
ShapeSignature codebook, held `Argmax` only, ties and disagreements REPORTED
not resolved, donkey=0, deterministic.

NEW in this invocation (per this run's own brief): a VOICE step. The three
prior fork-decision scripts skipped voice honestly because they booted a bare
`boot_core()` with no conversation/production pipeline wired. This run's brief
explicitly asks for self-report via `produce()`, so the boot recipe is
upgraded to the FULL topological boot (`WorldAdapter(seeds=()) + load_all_seeds`,
the same recipe `scripts/jabberwock_designs_motor_verdict.py` (run 49 PART 1,
83f91a0e) and `scripts/jabberwock_grounds_human_gap.py` (run 41, 145d3349) use)
-- this is a strict superset of the three decide-precedents' bare-boot_core +
{relation_vocabulary, math_capability_shapes/self_design_axis, stroke_shapes,
character_shapes} codebook (measured: 3.0s, 262 held ShapeSignature nodes), and
it is what makes `induce_concern`/`ground_concern`'s communicate-rule path (and
therefore `LanguageProduction.produce`) available. The VOICE step's plumbing
(induce_concern('communicate_my_...') -> ground_concern -> mint
produce_utterance subgoals -> LanguageWorld + LanguageProduction -> produce())
is copy-pasted from run 49's own working Step 3, generalised from CONCERNS to
OPTIONS.

BINDING HONESTY (run 41, `145d3349`): the `RelationCue` front-end is
SUBSTRING-SHALLOW. This script reports every grounding verbatim but the
DECISION's value is the held `ShapeDecode`-coverage + `AntiUnifyWitness`-
analogy machinery over SYMMETRICALLY-encoded evidence -- ties/disagreements
are reported, never resolved in Python, exactly as all three precedents did.

SEED ISOLATION (run 34c/37/41/49's pattern, reused verbatim): every `teach()`
persistence this process performs is redirected to
`results/run53_checkpoints/seeds/` -- no write ever touches `seeds/` proper.
`OZMA_SEED_PERSIST_DISABLED` is also set explicitly (belt-and-suspenders on
top of the durable guard landed in `21aa6123`, per this run's own instruction
to set it anyway). `seeds/stroke_shapes.json` md5 is asserted UNCHANGED before
and after.

NO git add/commit. donkey=0 verified at the end.

Run:  PYTHONPATH=.:runners/dsl/python:scripts /home/matt/ozma/internal/research/.venv/bin/python3 \\
        scripts/jabberwock_decides_loopflip.py \\
        2>&1 | stdbuf -oL tee results/jabberwock_decides_loopflip.log
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

SEP = "=" * 100
WILD = "\xb7?\xb7"  # the same wild marker every AntiUnify/Covers/ShapeDecode call in this codebase uses
CKPT_DIR = os.path.join(ROOT, "results", "run53_checkpoints")
os.makedirs(CKPT_DIR, exist_ok=True)
STROKE_SHAPES_PATH = os.path.join(ROOT, "seeds", "stroke_shapes.json")


def _md5(path: str):
    if not os.path.exists(path):
        return None
    return hashlib.md5(open(path, "rb").read()).hexdigest()


# =================================================================================================
# SEED ISOLATION -- redirect every teach() persistence to THIS run's own seeds dir (run 49's
# pattern, reused verbatim). Every other file under seeds/ proper (in particular
# seeds/stroke_shapes.json) is never touched.
# =================================================================================================
RUN53_SEEDS_DIR = os.path.join(CKPT_DIR, "seeds")
os.makedirs(RUN53_SEEDS_DIR, exist_ok=True)
import domains.teach as _teach_mod  # noqa: E402

_real_teach = _teach_mod.teach


def _isolated_teach(*a, **k):
    return _real_teach(*a, **{**k, "seeds_dir": Path(RUN53_SEEDS_DIR)})


_teach_mod.teach = _isolated_teach

import substrate_rs as srs                                             # noqa: E402
from substrate.world_adapter import WorldAdapter                       # noqa: E402
from substrate.boot_all import load_all_seeds                          # noqa: E402
from domains import reflective_faculty as rf                           # noqa: E402
from domains.reflective_faculty import (                               # noqa: E402
    induce_concern, ground_concern, author_signature, _load_shape_signatures,
)

# =================================================================================================
# STEP 1 MATERIAL -- held context, six facts, each a VERBATIM excerpt: three bolt-on-exhausted
# runs (45/49/51), the two-separate-pipelines structural discovery (302a27f3, this repo's own
# HEAD), and entries 42/44 of the running creator-memory chronicle
# (ozma_dynamic_quantization_core_loop.md) -- the axiom the whole arc's nulls are read against,
# and the top-down-is-the-missing-piece hypothesis this decision is literally about. Every
# excerpt is cited by commit hash / memory entry number right here, in code, next to the text.
# =================================================================================================

FACT_TEXTS: dict[int, str] = {
    # commit 1ea5a473 (RUN 45): the human-gap campaign's fourth bolt-on phase stops free.
    1: ("CONDITIONAL FOVEATION STOPS AT THE FREE GATE: armed 82.0 vs baseline 88.0 on n=100 "
        "background (-6pp, bound -3pp) -- the background-sanity rule minted in 44a caught its "
        "second would-be-harmful arm at ZERO eval cost, exactly as designed"),
    # commit 83f91a0e (RUN 49): the motor-program bolt-on nulls, and WHY -- a correlated, weaker
    # echo of the same shape information the whole-shape verdict already reads.
    2: ("THE MOTOR VERDICT DOES NOT ADD... a motor-program distance fused into the verdict "
        "nulls -- lambda calibrated to 0.0 monotonically in both regimes (every positive lambda "
        "hurts background 6-25pp)... it is a POSITIVELY-CORRELATED (r=0.48), WEAKER echo... of "
        "the SHAPE information SC+TPS already measures precisely -- spread-matching equalizes "
        "variance NOT discriminative power, so fusing a weaker correlated channel can only "
        "dilute"),
    # commit 2c2ca8c3 (RUN 51): the definitive bolt-on null -- orthogonal-and-real evidence still
    # cannot be added/gated/conditioned in; the conclusion points straight at entry 44.
    3: ("BOLT-ON ARCHITECTURES NOW EXHAUSTED -- three nulls (45 foveation, 49 motor, 51 "
        "relational), 51 DEFINITIVE because the evidence was orthogonal-and-real and STILL "
        "couldn't be added/gated/conditioned in... run 51 proves it cannot be BOLTED ON -- it "
        "must PARTICIPATE in perception (the top-down loop-flip, entry 44)"),
    # commit 302a27f3 (RUN 52, this repo's HEAD): the strong verdict has no parts; two separate
    # pipelines, fused only at the shortlist, never at the score.
    4: ("THE STRONG VERDICT HAS NO PARTS FOR THE CONCEPT TO ATTACH TO... the 80.5 SC+TPS "
        "verdict = parse_marginal_pair_error = Plus[smoothdeform_error, marginal_part_error, "
        "shapecontext_error] -- ALL whole-shape point-cloud geometry, references "
        "character_compose NOWHERE... the +21pp COMPOSITION result (run 3, quantized pipeline "
        "~30-34%) and the 80.5 CONTINUOUS verdict (SC+TPS whole-shape) are TWO SEPARATE "
        "PIPELINES fused only at the SHORTLIST level, never at the score"),
    # memory ozma_dynamic_quantization_core_loop.md, entry 42 (creator, 2026-07-06): the project
    # axiom -- existence proves possibility, so no null can ever prove impossibility.
    5: ("THE PROJECT AXIOM: \"It's the entire thesis of the project -- It's possible. Therefore "
        "with sufficient cleverness it *can* be done. The question is only 'are we clever "
        "enough yet.'\"... existence (the human) proves POSSIBILITY with certainty -> "
        "possibility guarantees SOME cheap implementation exists -> therefore no null can EVER "
        "prove impossibility, only \"not this way / not clever enough yet.\""),
    # memory ozma_dynamic_quantization_core_loop.md, entry 44 (creator question, 2026-07-06):
    # the missing piece is core/architectural -- top-down perception, not a missing primitive.
    6: ("the missing piece is CORE and ARCHITECTURAL, not a missing primitive, and not "
        "handwriting-specific... Perception is TOP-DOWN / theory-laden: the concept shapes the "
        "percept; ours is bottom-up with the concept bolted on as a post-hoc shortlist (which "
        "failed 3x, because a concept consulted AFTER perception can't restructure it)... We're "
        "missing their TOP-DOWN COMPOSITION: fast AMORTIZED inference of a variation-aware "
        "generative CONCEPT, fit to the instance in one cheap pass -- not searched (BPL/MCMC) "
        "nor compared-against (us)"),
}

FACT_CITATIONS: dict[int, str] = {
    1: "commit 1ea5a473 (RUN 45 -- conditional foveation stops free)",
    2: "commit 83f91a0e (RUN 49 -- the motor verdict does not add)",
    3: "commit 2c2ca8c3 (RUN 51 -- bolt-on architectures now exhausted)",
    4: "commit 302a27f3 (RUN 52, this repo's HEAD -- the strong verdict has no parts)",
    5: ("memory ozma_dynamic_quantization_core_loop.md, entry 42 (creator, 2026-07-06 -- "
        "THE PROJECT AXIOM)"),
    6: ("memory ozma_dynamic_quantization_core_loop.md, entry 44 (creator question, "
        "2026-07-06 -- WHAT ARE WE MISSING THAT COGNITION HAS?)"),
}

PARENT_GOAL_NAME = "build_verdict_where_concept_participates_in_perception"
PARENT_GOAL_CLAIM = "build the verdict where the concept participates in perception"


# =================================================================================================
# STEP 2 MATERIAL -- Option A / B / C, each exactly one claim clause (verbatim, this run's own
# launch brief's own "OPTION A/B/C" paragraph, up to "Evidence for:") + exactly one for/against
# evidence block (verbatim, the SAME paragraph's own "Evidence for: ... Against: ..." clause).
# Same arity (2 texts each), same mechanism, no extra material for any side.
# =================================================================================================

OPTION_A_NAME = "option_a_compositional_metric"
OPTION_A_CLAIM = (
    "COMPOSITIONAL-METRIC (incremental): decompose SC+TPS to per-stroke geometry + a "
    "tightness-weighted relational term, summed as ONE verdict; the concept weights the "
    "relational composition. Closest to what exists (reuses SC+TPS per-stroke, run-50 "
    "tightness, greedy stroke matcher)."
)
OPTION_A_EVIDENCE_LABEL = "for/against evidence block (task brief, verbatim)"
OPTION_A_EVIDENCE = (
    "Evidence for: run 3 composition +21pp proves arrangement adds; run 50 relational "
    "orthogonal. Against: run 44 (concept-as-metric at affine level) nulled; run 52 (reweight "
    "composition) nulled -- metric-reweighting has failed twice."
)

OPTION_B_NAME = "option_b_generative_concept_inference"
OPTION_B_CLAIM = (
    "GENERATIVE-CONCEPT INFERENCE (the fuller loop-flip): the concept PREDICTS the parse -- a "
    "per-class generative model (strokes + relations + learned variation) is INFERRED/fit to "
    "the query (amortized, cheap, not MCMC), and the fit quality IS the verdict. The concept "
    "generates the expectation; the query is parsed UNDER it (top-down), not scored after."
)
OPTION_B_EVIDENCE_LABEL = "for/against evidence block (task brief, verbatim)"
OPTION_B_EVIDENCE = (
    "Evidence for: entry 44 (top-down perception is the named missing piece); the human "
    "existence proof; BPL's actual architecture. Against: bigger/harder; risk of needing "
    "search (though entry 42: amortization makes it cheap -- the human proves it)."
)

OPTION_C_NAME = "option_c_predictive_coding_residual"
OPTION_C_CLAIM = (
    "PREDICTIVE-CODING / RESIDUAL loop: the concept predicts the glyph, the RESIDUAL "
    "(prediction error) drives recognition and refinement -- native_collapse's "
    "predict->surprise->learn (which the agent already HAS) run at the PER-DECISION "
    "recognition scale, not just the learning scale."
)
OPTION_C_EVIDENCE_LABEL = "for/against evidence block (task brief, verbatim)"
OPTION_C_EVIDENCE = (
    "Evidence for: native_collapse exists and is domain-general; the residual is already the "
    "framework's 'what I couldn't explain'. Against: never run at per-decision recognition "
    "scale; unproven at this grain."
)

OPTIONS = [
    (OPTION_A_NAME, OPTION_A_CLAIM, OPTION_A_EVIDENCE_LABEL, OPTION_A_EVIDENCE),
    (OPTION_B_NAME, OPTION_B_CLAIM, OPTION_B_EVIDENCE_LABEL, OPTION_B_EVIDENCE),
    (OPTION_C_NAME, OPTION_C_CLAIM, OPTION_C_EVIDENCE_LABEL, OPTION_C_EVIDENCE),
]

OPTION_LABELS = {
    OPTION_A_NAME: "OPTION A -- COMPOSITIONAL-METRIC",
    OPTION_B_NAME: "OPTION B -- GENERATIVE-CONCEPT INFERENCE",
    OPTION_C_NAME: "OPTION C -- PREDICTIVE-CODING / RESIDUAL",
}

# HOST TRANSLATION -- what a run-54 build means for each option IF it wins. Fixed lookup by
# option name (mechanical unpacking of that option's OWN clause + already-named held building
# blocks -- StrokeQuantize, the run-36/39/50 greedy stroke matcher, run-50's held tightness
# prior, native_collapse, the AbS render primitives), never a decision over graph state; printed
# only for a clean single-option verdict.
HOST_TRANSLATION = {
    OPTION_A_NAME: (
        "RUN-54 BUILD SPEC (Option A -- compositional metric): "
        "SEGMENTATION -- reuse the existing StrokeQuantize/committed per-stroke segmentation "
        "unchanged (it already emits per-stroke spans; no new segmenter). "
        "ALIGNMENT -- the existing greedy stroke matcher (run-36/39/50 precedent) pairs query "
        "strokes to exemplar strokes. "
        "COMPOSITION FORM -- a single SUMMED verdict: total = sum_i SC+TPS(stroke_i, "
        "matched_stroke_i) + tightness_weight * relational_term(arrangement), with "
        "tightness_weight read from run-50's held per-relation tightness prior (background-"
        "learned, training-free; the SAME prior run 50 proved orthogonal). "
        "CORPUS -- the SAME Omniglot 20-way protocol (n=400, powered Wilson CIs, background-"
        "sanity gate BEFORE any eval spend), so a null reproduces 80.5 exactly and a real lift "
        "is CI-separated from it, per the counter-evidence's own bar (metric-reweighting has "
        "failed twice already: runs 44 and 52). Flag-gated, byte-identical with the flag off."
    ),
    OPTION_B_NAME: (
        "RUN-54 BUILD SPEC (Option B -- generative-concept inference): "
        "SEGMENTATION -- per-stroke as in Option A, PLUS a per-class generative template: "
        "strokes as parametrized programs, relations as a graph, variation as a learned "
        "per-relation/per-stroke spread (the concept itself IS this template). "
        "ALIGNMENT -- replaced by INFERENCE: the query's points are FIT under each class's "
        "generative template (an amortized closed-form or lightweight per-class optimization, "
        "explicitly NOT MCMC/search) so parsing and scoring happen in the SAME step. "
        "COMPOSITION FORM -- the fit residual under the inferred parse IS the verdict; no "
        "separate summed distance term. "
        "CORPUS -- the SAME protocol, with a background-sanity gate BEFORE eval given the "
        "counter-evidence's named risk (bigger/harder, possible search cost); the FIRST gate "
        "this build must clear is entry-42's own amortization claim -- that the per-class fit "
        "stays cheap -- since that claim is the thing being tested here, not assumed."
    ),
    OPTION_C_NAME: (
        "RUN-54 BUILD SPEC (Option C -- predictive-coding / residual loop): "
        "SEGMENTATION -- per-stroke as in Option A. "
        "ALIGNMENT -- whatever alignment native_collapse's existing per-stroke predict step "
        "already uses; no new matcher. "
        "COMPOSITION FORM -- the concept generates a PREDICTED per-stroke+relational rendering "
        "(reusing the held generative/render primitives already exercised for AbS); "
        "native_collapse's predict->surprise->learn loop is invoked at RECOGNITION time (per "
        "query, per candidate class) instead of only at learning time -- surprise (residual "
        "magnitude) ranks candidates, and a high-surprise result can trigger one refinement "
        "iteration before the final score. "
        "CORPUS -- the SAME protocol; named risk (verbatim, this option's own counter-"
        "evidence): this rung has never been exercised at per-decision grain, so the FIRST "
        "run-54 gate is simply 'does it run and produce a score at all', before any accuracy "
        "claim."
    ),
}


# =================================================================================================
# Mechanical helpers -- glue code calling HELD Terms/functions only. None of these contain a
# decision over graph state; every ranking is done by a real `Argmax` Term call, every score by a
# real `ShapeDecode`/`TransformDecode`/`AntiUnifyWitness`/`FixedCount` Term call.
# =================================================================================================

def _author_clause(sub, name: str, text: str) -> list:
    """Install a scratch Concept carrying `text` as its `definition`, then run the agent's OWN
    held signature-authoring mechanism over it (`reflective_faculty.author_signature`). Mechanical
    I/O (one node write + one call to an existing, unmodified held function) -- no new matching
    logic, no decision."""
    sub.add_node("Concept", {"name": name, "definition": text})
    sig, _defn, _cname = author_signature(sub, name)
    return sig or []


def _ordered_union(sig_lists) -> list:
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
    total = int(decode_result.get("goal_relations") or len(goal_sig) or 0)
    if total == 0:
        return 0.0
    covered = int(decode_result.get("covered_count") or 0)
    return covered / total


def _antiunify_witness(native, sig_a, sig_b):
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
    if not pairs:
        return None
    return native.evaluate(
        {"type": "Argmax", "source": _lit(pairs), "var_name": "c",
         "value": {"type": "IndexAt", "seq": {"type": "Var", "name": "c"},
                   "index": _lit(0)},
         "default": None}, {})


def _tied_labels(pairs):
    if not pairs:
        return []
    best = max(p[0] for p in pairs)
    return [p[1] for p in pairs if p[0] == best]


def _fmt_sig(sig, indent="      "):
    if not sig:
        return indent + "(empty -- no held RelationCue fired)"
    return "\n".join(f"{indent}{tuple(r)}" for r in sig)


def _verify_boot_faculties(sub) -> dict:
    """Unit-check the boot before the decision runs -- mechanical query over Seed/ComposerCue/
    rule nodes, no decision."""
    seed_ids = {sub.node(n)["attrs"].get("seed_id") for n in sub.nodes("SeedSummary")}
    cues = list(sub.nodes("ComposerCue"))
    rule_names = {r.get("name") for r in sub._inner.export_rules() if isinstance(r, dict)}
    qd_rules = sorted(n for n in rule_names if isinstance(n, str) and n.startswith("qd_"))
    return {
        "question_driving_seed_installed": "question_driving" in seed_ids,
        "composer_dispatch_seed_installed": "composer_dispatch" in seed_ids,
        "relation_vocabulary_seed_installed": "relation_vocabulary" in seed_ids,
        "n_composer_cues": len(cues),
        "qd_rules_installed": qd_rules,
        "n_seeds_total": len(seed_ids),
    }


# =================================================================================================
def main() -> int:
    md5_before = _md5(STROKE_SHAPES_PATH)

    print(SEP)
    print("THE JABBERWOCK DECIDES THE LOOP-FLIP (run 53)")
    print("Option A: compositional-metric  vs  Option B: generative-concept inference  vs  "
          "Option C: predictive-coding/residual")
    print(f"seeds/stroke_shapes.json md5 BEFORE: {md5_before}")
    print(SEP)

    # ---------------------------------------------------------------------------------------
    # BOOT -- the full topological boot (run 41/49's idiom), needed for the VOICE step's
    # communicate-rule + produce() pipeline. Strict superset of the three decide-precedents'
    # bare boot_core() + {relation_vocabulary, math_capability_shapes, stroke_shapes,
    # character_shapes} codebook.
    # ---------------------------------------------------------------------------------------
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    s, native = a.s, a.inner
    donkey = {"n": 0}
    a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "DONKEY")[1])

    faculties = _verify_boot_faculties(s)
    held_sigs = _load_shape_signatures(s)
    print(f"\nBOOT: WorldAdapter(seeds=()) + load_all_seeds -> "
          f"{faculties['n_seeds_total']} Seed nodes installed.")
    print(f"  question_driving seed installed:    {faculties['question_driving_seed_installed']}")
    print(f"  composer_dispatch seed installed:   {faculties['composer_dispatch_seed_installed']} "
          f"({faculties['n_composer_cues']} ComposerCue nodes)")
    print(f"  relation_vocabulary seed installed: {faculties['relation_vocabulary_seed_installed']}")
    print(f"  qd_* rules installed ({len(faculties['qd_rules_installed'])}): "
          f"{faculties['qd_rules_installed']}")
    print(f"  held ShapeSignature codebook: {len(held_sigs)} nodes "
          f"(the agent's OWN codebook the 'neither' path competes against)")

    assert faculties["question_driving_seed_installed"], "UNIT CHECK FAILED: question_driving seed missing"
    assert faculties["composer_dispatch_seed_installed"], "UNIT CHECK FAILED: composer_dispatch seed missing"
    assert faculties["relation_vocabulary_seed_installed"], "UNIT CHECK FAILED: relation_vocabulary seed missing"
    assert faculties["n_seeds_total"] > 0, "UNIT CHECK FAILED: zero seeds installed"
    assert len(held_sigs) > 0, "UNIT CHECK FAILED: zero held ShapeSignature nodes"
    print("  UNIT CHECK: PASS -- faculties live, boot verified before the decision.")

    plan_record: dict = {"faculties": faculties, "facts": {}, "options": {}, "coverage": {},
                          "analogical": {}, "verdict": {}, "voice": {}, "host_translation": {}}

    # =========================================================================================
    # STEP 1 -- EVIDENCE AS GRAPH DATA (the six held-context facts)
    # =========================================================================================
    print(f"\n{SEP}\nSTEP 1 -- EVIDENCE AS GRAPH DATA (held context, verbatim commit-message / "
          f"creator-memory facts, run through the held RelationCue signature-authoring "
          f"mechanism)\n{SEP}")
    fact_sigs = {}
    for i in sorted(FACT_TEXTS):
        fact_sigs[i] = _author_clause(s, f"loopflip_fact_{i}", FACT_TEXTS[i])
        print(f"\n  FACT {i}  [{FACT_CITATIONS[i]}]")
        print(f"    text: {FACT_TEXTS[i]}")
        print(f"    fired relations:\n{_fmt_sig(fact_sigs[i])}")
    evidence_sig = _ordered_union(fact_sigs.values())
    print(f"\n  EVIDENCE (union of all {len(FACT_TEXTS)} facts, deduped, {len(evidence_sig)} "
          f"relations):")
    print(_fmt_sig(evidence_sig))
    plan_record["facts"] = {"texts": FACT_TEXTS, "citations": FACT_CITATIONS,
                             "signature": evidence_sig}

    parent_claim_sig = _author_clause(s, PARENT_GOAL_NAME, PARENT_GOAL_CLAIM)
    print(f"\n  PARENT GOAL: {PARENT_GOAL_NAME!r}")
    print(f"    claim (verbatim): {PARENT_GOAL_CLAIM!r}")
    print(f"      fired relations:\n{_fmt_sig(parent_claim_sig)}")
    plan_record["facts"]["parent_goal_claim_signature"] = parent_claim_sig

    # =========================================================================================
    # STEP 2 -- OPTIONS AS CANDIDATE SHAPES (same vocabulary, same mechanism, same rigor)
    # =========================================================================================
    print(f"\n{SEP}\nSTEP 2 -- OPTIONS AS CANDIDATE SHAPES\n{SEP}")

    option_sigs = {}
    for name, claim, ev_label, ev_text in OPTIONS:
        claim_sig = _author_clause(s, f"{name}_claim", claim)
        ev_sig = _author_clause(s, f"{name}_evidence", ev_text)
        option_sig = _ordered_union([claim_sig, ev_sig])
        option_sigs[name] = option_sig

        print(f"\n  {OPTION_LABELS[name]}  ({name})")
        print(f"    definition (verbatim, task brief's own OPTION paragraph): {claim!r}")
        print(f"      fired relations:\n{_fmt_sig(claim_sig)}")
        print(f"    {ev_label}: {ev_text!r}")
        print(f"      fired relations:\n{_fmt_sig(ev_sig)}")
        print(f"    {name.upper()} SIGNATURE (union, {len(option_sig)} relations):")
        print(_fmt_sig(option_sig))
        if not option_sig:
            print(f"    DISCLOSURE: {name} fires ZERO held RelationCue relations from its "
                  f"definition+evidence text. Honest -- not forced.")
        plan_record["options"][name] = {"claim": claim, "evidence": ev_text,
                                         "signature": option_sig}

    # scratch, episode-scoped codebook holding ONLY the three options (nothing persists; the
    # main substrate `s` never sees these three nodes) -- the same instance-scoped scratch
    # substrate all three precedents used.
    scratch = srs.Substrate()
    for name, _claim, _l, _t in OPTIONS:
        scratch.add_node("ShapeSignature", {"name": name, "kind": "frontier_branch",
                                             "signature": json.dumps(option_sigs[name])})
    scratch_native = scratch._inner
    option_names = [o[0] for o in OPTIONS]

    # =========================================================================================
    # STEP 3a -- COVERAGE/FIT PATH (ShapeDecode + TransformDecode)
    # =========================================================================================
    print(f"\n{SEP}\nSTEP 3a -- COVERAGE/FIT PATH (held ShapeDecode / TransformDecode)\n{SEP}")

    cov_pairs = []
    cov_detail = {}
    for name in option_names:
        others = [n for n in option_names if n != name]
        decode_solo = _shape_decode(scratch_native, evidence_sig, exclude=others)
        td_solo = _transform_decode(scratch_native, evidence_sig, exclude=others)
        cov = _coverage_fraction(evidence_sig, decode_solo)
        cov_pairs.append([cov, name])
        cov_detail[name] = {"decode": decode_solo, "transform": td_solo}
        print(f"\n  {name} solo (other two options excluded from the 3-shape codebook):")
        print(f"    ShapeDecode:     coverage={cov:.3f} ({decode_solo.get('covered_count')}/"
              f"{decode_solo.get('goal_relations')})  total_fit={decode_solo.get('total_fit')}  "
              f"plan={decode_solo.get('ordered_parts')}  residual={decode_solo.get('residual')}")
        print(f"    TransformDecode: explained={td_solo.get('explained')}  "
              f"base={td_solo.get('base')}  dims={td_solo.get('dims')}  "
              f"deltas={td_solo.get('deltas')}  identity={td_solo.get('identity')}")

    decode_all = _shape_decode(scratch_native, evidence_sig)  # all three available, informational
    print(f"\n  All three options available (composed plan, INFORMATIONAL ONLY -- not a "
          f"decision input): plan={decode_all.get('ordered_parts')}  "
          f"total_fit={decode_all.get('total_fit')}  "
          f"coverage={_coverage_fraction(evidence_sig, decode_all):.3f}")

    decode_full = _shape_decode(native, evidence_sig)         # main substrate: full real codebook
    td_full = _transform_decode(native, evidence_sig)
    cov_full = _coverage_fraction(evidence_sig, decode_full)
    full_parts = list(decode_full.get("ordered_parts") or [])
    full_label = f"neither -- best held coverage uses {full_parts!r}" if full_parts else \
                 "neither -- no held shape covers any evidence relation"

    print(f"\n  Full held codebook ({len(held_sigs)} real ShapeSignature nodes from the "
          f"complete topological boot; options ABSENT):")
    print(f"    ShapeDecode:     coverage={cov_full:.3f} ({decode_full.get('covered_count')}/"
          f"{decode_full.get('goal_relations')})  total_fit={decode_full.get('total_fit')}  "
          f"plan={full_parts}  residual={decode_full.get('residual')}")
    print(f"    TransformDecode: explained={td_full.get('explained')}  base={td_full.get('base')}  "
          f"dims={td_full.get('dims')}  deltas={td_full.get('deltas')}  "
          f"identity={td_full.get('identity')}")

    coverage_pairs = cov_pairs + [[cov_full, full_label]]
    coverage_pick = _held_argmax(native, coverage_pairs)
    coverage_tied = _tied_labels(coverage_pairs)
    print(f"\n  COVERAGE-PATH candidates: {coverage_pairs}")
    print(f"  COVERAGE-PATH held Argmax pick: {coverage_pick}")
    if len(coverage_tied) > 1:
        print(f"  COVERAGE-PATH TIE at top score {max(p[0] for p in coverage_pairs):.3f}: "
              f"{coverage_tied}")
    plan_record["coverage"] = {"pairs": coverage_pairs, "pick": coverage_pick,
                                "tied": coverage_tied, "detail": cov_detail}

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
    plan_record["analogical"] = {"pairs": analogical_pairs, "pick": analogical_pick,
                                  "tied": analogical_tied, "top5_held": top5}

    # =========================================================================================
    # FINAL VERDICT -- printed, not resolved.
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
    plan_record["verdict"] = {"kind": verdict_kind, "option": verdict_option,
                               "coverage_label": coverage_label, "analogical_label": analogical_label}

    # =========================================================================================
    # STEP 4 -- VOICE (self-report via produce(), run 49's Step 3 plumbing generalised from
    # CONCERNS to OPTIONS)
    # =========================================================================================
    print(f"\n{SEP}\nSTEP 4 -- VOICE (the agent grounds + uses its communicate faculty)\n{SEP}")

    # per-option outcome, derived MECHANICALLY from the verdict already produced above (no new
    # decision -- a fixed lookup keyed by whether an option IS the clean winner, IS a loser next
    # to a clean winner, or the verdict is a tie/disagreement leaving every option undecided).
    option_outcome: dict[str, str] = {}
    if verdict_option in option_names:
        for n in option_names:
            option_outcome[n] = "chosen" if n == verdict_option else "rejected"
    else:
        for n in option_names:
            option_outcome[n] = "undecided"

    OUTCOME_VERB = {"chosen": "choose", "rejected": "reject", "undecided": "hold"}

    parent_goal = s.add_node("Goal", {"kind": "verdict", "concept": PARENT_GOAL_NAME})
    option_goal_nodes: dict[str, int] = {}
    for name in option_names:
        gg = s.add_node("Goal", {"kind": "option", "concept": name,
                                  "status": option_outcome[name]})
        native.add_edge_unchecked(parent_goal, "has_subgoal", gg)
        option_goal_nodes[name] = gg
    print(f"  Goal tree wired (mechanical ingest): parent Goal {parent_goal} -has_subgoal-> "
          f"{list(option_goal_nodes.values())}")
    print(f"  per-option outcome (mechanical readout of the verdict above): {option_outcome}")

    # SAME literal cue-word skeleton run 41/49's own communicate-concern signature uses
    # (`for_each X mint SUBGOAL` / `SUBGOAL produces UTTERANCE` / `source UTTERANCE from X`,
    # unchanged across PHASE/GAP/CONCERN in the three precedent voice-sessions) -- "SUBGOAL"
    # and "UTTERANCE" are the load-bearing cue words the composer's rule-authoring keys on
    # (verified live: substituting "OPTION" for "SUBGOAL" mints zero produce_utterance
    # subgoals, see the run's own honest anomaly note below); only the varying first-slot noun
    # (OPTION here, matching PHASE/GAP/CONCERN there) and the outer "DECIDED" (matching
    # "PLANNED") are customised.
    comm_obs = [["told", "DESCRIBE", "what", "DECIDED"],
                ["for_each", "OPTION", "mint", "SUBGOAL"],
                ["SUBGOAL", "produces", "UTTERANCE"],
                ["source", "UTTERANCE", "from", "OPTION"]]
    comm_ind = induce_concern(a, comm_obs, name_hint="communicate_my_verdict")
    print(f"  induce_concern('communicate_my_verdict') -> minted={comm_ind.get('minted')} "
          f"residual_predicates={comm_ind.get('residual_predicates')}")
    voice_record: dict = {"induce": comm_ind, "option_outcome": option_outcome}
    lines: list = []
    if comm_ind.get("minted"):
        comm_key = comm_ind.get("capability_key")
        comm_g = ground_concern(a, [comm_key])
        print(f"  ground_concern -> grounded={comm_g.get('grounded')} path={comm_g.get('path')!r} "
              f"form={comm_g.get('form')}")
        voice_record["ground"] = comm_g
        if comm_g.get("grounded") and comm_g.get("form") == "communicate_rule":
            print(f"    AUTHORED RULE: match={comm_g['rule']['match']}  "
                  f"effects={comm_g['rule']['effects']}")
            scene = s.add_node("Scene", {})
            native.add_edge_unchecked(parent_goal, "describes", scene)
            for name in option_names:
                verb = OUTCOME_VERB[option_outcome[name]]
                con = s.add_node("Concept", {"name": f"{name}_outcome",
                                              "outcome": option_outcome[name], "say_event": verb})
                pn = s.add_node("Percept", {"option": name, "outcome": option_outcome[name]})
                native.add_edge_unchecked(scene, "has_percept", pn)
                native.add_edge_unchecked(pn, "is_a", con)
            native.run_rules()
            subgoals = list(native.neighbours(parent_goal, "has_subgoal"))
            new_utt_subgoals = [n for n in subgoals
                                 if s.node(n)["attrs"].get("kind") == "produce_utterance"]
            print(f"  -> the agent's OWN authored rule minted {len(new_utt_subgoals)} "
                  f"produce_utterance subgoal(s)")

            from domains.language_world import LanguageWorld, teacher_stub
            from domains.language_production import LanguageProduction
            from scripts.language_test import training_bank
            world = LanguageWorld(native, training_bank(), teacher_stub)
            world.run()
            for lemma, surf in {"choose": "chooses", "reject": "rejects", "hold": "holds",
                                 "thing": "thing"}.items():
                s.add_node("LexEntry", {"surface": surf, "concept": lemma, "language": "en",
                                        "status": "confirmed", "lemma": lemma})
            world.teacher_disabled = True
            prod = LanguageProduction(world)
            for sg in new_utt_subgoals:
                con = next(iter(native.neighbours(sg, "about")), None)
                if con is None:
                    continue
                cat = s.node(con)["attrs"]
                say = cat.get("say_event")
                if not say:
                    continue
                res = prod.produce("en", {"event": say, "agent": "thing", "tense": "present",
                                          "intent": "inform"})
                overt = res.get("overt_speech")
                lines.append((cat.get("name"), cat.get("outcome"), overt))
                print(f"    subgoal about {cat.get('name')!r} (outcome={cat.get('outcome')!r}) "
                      f"-> {overt!r}")
        else:
            print(f"    WALL (verbatim): {comm_g.get('wall')}")
    else:
        print("  the communicate concern did not mint (recognized by an existing held shape "
              f"-- covered_by={comm_ind.get('covered_by')!r}); voice skipped honestly.")
    voice_record["lines"] = lines
    plan_record["voice"] = voice_record

    print("\n  THE AGENT'S SELF-REPORT (one produced utterance per option):")
    if lines:
        for name, outcome, overt in lines:
            print(f"    {name}: {overt!r}  (outcome={outcome})")
    else:
        print("    (no utterances produced -- see WALL/skip above; honest, not faked.)")

    # =========================================================================================
    # STEP 5 -- HOST TRANSLATION (mechanical, decisions=none): printed ONLY for a clean single-
    # option verdict, via a fixed lookup keyed by the winning option's name.
    # =========================================================================================
    print(f"\n{SEP}\nSTEP 5 -- HOST TRANSLATION (mechanical; adapter work, no decisions)\n{SEP}")
    if verdict_option in HOST_TRANSLATION:
        print(f"  {HOST_TRANSLATION[verdict_option]}")
        plan_record["host_translation"] = {verdict_option: HOST_TRANSLATION[verdict_option]}
    else:
        print(f"  No single option cleanly won ({verdict_kind}), so no run-54 build spec is "
              f"printed -- per protocol, a tie/disagreement is reported back to the creator, "
              f"not broken here.")
        plan_record["host_translation"] = {"note": f"no clean verdict ({verdict_kind})"}

    # =========================================================================================
    # SAVE + donkey + seed-guard check
    # =========================================================================================
    out_path = os.path.join(CKPT_DIR, "decision.json")
    with open(out_path, "w") as f:
        json.dump(plan_record, f, indent=2, default=str)
    print(f"\nSaved structured decision -> {out_path}")

    md5_after = _md5(STROKE_SHAPES_PATH)
    seed_guard_ok = (md5_before == md5_after)
    print(f"seeds/stroke_shapes.json md5 AFTER: {md5_after}  UNCHANGED={seed_guard_ok}")
    assert seed_guard_ok, "SEED GUARD FAILED: seeds/stroke_shapes.json was mutated by this run"

    donkey_modules = ("torch", "torchaudio", "tensorflow", "allosaurus", "whisper",
                       "faster_whisper", "ctranslate2", "transformers")
    loaded = [m for m in donkey_modules if m in sys.modules]
    assert not loaded, f"donkey!=0: {loaded} present in sys.modules"
    print(f"donkey=0 verified: none of {donkey_modules} present in sys.modules "
          f"(self-teacher calls: {donkey['n']}).")

    print(f"\n{SEP}")
    print(f"GATE: PASS -- a verdict ({verdict_kind}) was produced by held machinery "
          f"(ShapeDecode/TransformDecode/AntiUnifyWitness/FixedCount/Argmax); zero Python "
          f"decisions on the path. seed_guard_ok={seed_guard_ok}")
    print("EXECUTION: explicitly NOT performed by this script -- the verdict (and, if clean, "
          "its run-54 build spec) is reported for the caller to commit; building the chosen "
          "option is a separate, later task.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
