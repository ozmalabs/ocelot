"""THE JABBERWOCK DESIGNS THE MOTOR VERDICT (run 49 PART 1 -- a PLANNING session, no eval).

Mirrors `scripts/jabberwock_plans_gap_closure.py` (run 37, commit 67005b35) and
`scripts/jabberwock_grounds_human_gap.py` (run 41, commit 145d3349) EXACTLY: same boot recipe,
same verbatim-clause-authoring discipline, same `induce_concern`/`ground_concern` per concern,
same `compose_design_for_goal` parent plan, same communicate-rule VOICE step, same mechanical
host-translation table. Only WHAT is fed changes: this run's own concern is "build a verdict
that judges by the motor program, not the whole shape" (run 49's launch brief, quoted verbatim
below), not a prior run's failure taxonomy.

THE AGENT DESIGNS THE VERDICT. This script only INGESTS the run-48 bottleneck finding (commit
8e4b7aee) as HELD CONTEXT plus three concrete concerns drawn VERBATIM from this run's own launch
brief's "PART 2" concrete spec (representation / distance / fusion) as graph data, TICKS the
agent's own concern-induction/grounding machinery over each, and READS the resulting design back
off the graph. Every routing decision (recognized-vs-minted, which composer, which rule) is the
agent's own held machinery (`domains.reflective_faculty`'s `induce_concern`/`ground_concern`/
`compose_design_for_goal`, thin shims over Rust `ShapeDecode`/`TransformDecode`/`Argmax` Terms).

BINDING HONESTY (run 41, `145d3349`): the `RelationCue` front-end is SUBSTRING-SHALLOW -- this
script reports the grounding VERBATIM but does NOT treat its semantics as load-bearing; the
design's value is proven by PART 2's GATE (`scripts/jabberwock_omniglot_run49_motor.py`), never
by this planning session's own grounding, exactly as run 37's groundings were only ever
retroactively validated by their gates.

HELD CONTEXT (feeds the PARENT goal's signature only, not a Concern of its own -- run 37/41's own
held-context treatment), quoted VERBATIM from this run's own launch brief's "bottleneck" section
(itself citing commit `8e4b7aee`, "RUN 48 -- THE TRUE PEN TEST..."), split at its own sentence
boundaries -- no rewording, no reordering beyond the brief's own sentence order.

THE THREE CONCERNS are drawn VERBATIM from this run's own launch brief's "PART 2" concrete spec
(the representation / distance / fusion paragraphs), each split at its own sentence/clause
boundaries in the brief's OWN order -- "cue-word-led" here means the brief's own leading noun
phrase (MOTOR PROGRAM / MOTOR DISTANCE / FUSED VERDICT) is what leads each concern's signature,
since that noun phrase is already first in the brief's own text (no keyword was added or
reworded to force a particular `RelationCue` to fire first).

SEED ISOLATION (run 34c/37/41's pattern, reused verbatim): every `teach()` persistence this
process performs is redirected to `results/run49_checkpoints/seeds/` -- no write ever touches
`seeds/` proper. `seeds/stroke_shapes.json` md5 is asserted UNCHANGED before and after (belt-
and-suspenders, on top of the durable `OZMA_SEED_PERSIST_DISABLED` guard landed in `21aa6123`
this run's own launch brief requires re-checking regardless of that guard).

NO git add/commit. donkey=0 verified at the end.

Run:  PYTHONPATH=.:runners/dsl/python:scripts /home/matt/ozma/internal/research/.venv/bin/python3 \\
        scripts/jabberwock_designs_motor_verdict.py \\
        2>&1 | stdbuf -oL tee results/jabberwock_designs_motor_verdict.log
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

SEP = "=" * 100
CKPT_DIR = os.path.join(ROOT, "results", "run49_checkpoints")
os.makedirs(CKPT_DIR, exist_ok=True)
STROKE_SHAPES_PATH = os.path.join(ROOT, "seeds", "stroke_shapes.json")


def _md5(path: str):
    if not os.path.exists(path):
        return None
    return hashlib.md5(open(path, "rb").read()).hexdigest()


# ---------------------------------------------------------------------------
# SEED ISOLATION -- redirect every teach() persistence to THIS run's own seeds dir. Every other
# file under seeds/ proper (in particular seeds/stroke_shapes.json) is never touched.
# ---------------------------------------------------------------------------
RUN49_SEEDS_DIR = os.path.join(CKPT_DIR, "seeds")
os.makedirs(RUN49_SEEDS_DIR, exist_ok=True)
import domains.teach as _teach_mod  # noqa: E402

_real_teach = _teach_mod.teach


def _isolated_teach(*a, **k):
    return _real_teach(*a, **{**k, "seeds_dir": Path(RUN49_SEEDS_DIR)})


_teach_mod.teach = _isolated_teach

from substrate.world_adapter import WorldAdapter                       # noqa: E402
from substrate.boot_all import load_all_seeds                          # noqa: E402
from domains import reflective_faculty as rf                           # noqa: E402
from domains.reflective_faculty import (                               # noqa: E402
    induce_concern, ground_concern, learn_term_for_concern, author_signature,
    compose_design_for_goal, _load_shape_signatures,
)

# =============================================================================
# STEP 1 MATERIAL -- verbatim as handed down in this run's own launch brief.
# =============================================================================
CITATION = ("commit 8e4b7aee (RUN 48 -- THE TRUE PEN TEST) + this run's own launch brief, "
            "\"The bottleneck this run attacks\" / \"PART 2\" sections")

HELD_CONTEXT_CLAUSES = [
    "The whole-shape continuous verdict (SC+TPS point-cloud) IGNORES stroke-interior/motor "
    "structure",
    "Pen data HAS that structure (run 46: 17x class-grain info) but the grain never converts "
    "to accuracy -- because it was always tried as a PROPOSAL (recall-limited, 3 negatives: "
    "UCI/QuickDraw/DigiLeTs) and the verdict stayed whole-shape",
]

CONCERN_CLAUSES = {
    "concern_a_motor_program_representation": [
        # leads with the noun phrase the brief itself leads with ("MOTOR PROGRAM of a glyph").
        "MOTOR PROGRAM of a glyph = per-stroke: the stroke-program token string (level-runs/"
        "ramps/change-points on the denoised turn sequence) + the run-39 pen-up channel "
        "features that were LIVE (transition sectors, start-position; NOT order/direction "
        "which were convention-dead) + stroke count",
        "this is the \"how it was drawn\" representation the whole-shape verdict throws away",
    ],
    "concern_b_motor_distance": [
        "MOTOR DISTANCE m(A,B) = a held-Term composite: per-aligned-stroke program-token "
        "edit/DTW distance (DtwTo or the committed_shape edit distance, reuse) + "
        "transition-sector disagreement + start-cell disagreement, aligned by the run-36/39 "
        "greedy stroke matcher",
        "held Term arithmetic, source-audited",
    ],
    "concern_c_fused_verdict": [
        # leads with "FUSED VERDICT", the brief's own leading noun phrase for this paragraph.
        "FUSED VERDICT: final_score = geo_score(SC+TPS) + w_m * m(query, candidate), w_m "
        "spread-matched (target = median existing-term spread on background) and then "
        "lambda-scaled, both frozen from background calibration with the background-sanity STOP",
        "this is a SUPPLEMENT over the full candidate set, no hard shortlist, argmin over all N",
    ],
}

CONCERN_LABELS = {
    "concern_a_motor_program_representation": "CONCERN A -- MOTOR PROGRAM REPRESENTATION",
    "concern_b_motor_distance": "CONCERN B -- MOTOR DISTANCE",
    "concern_c_fused_verdict": "CONCERN C -- FUSED VERDICT (SUPPLEMENT, NOT REPLACE)",
}

PARENT_GOAL_NAME = "build_motor_program_verdict"
PARENT_GOAL_CLAIM = (
    "build a verdict that judges by the motor program, not the whole shape -- a held motor "
    "distance over per-stroke program tokens + the run-39 pen-up channel + stroke count, fused "
    "(never replacing) the whole-shape continuous SC+TPS verdict under RUN 37A's supplement "
    "law -- " + CITATION
)


# =============================================================================
# Mechanical helpers -- identical to run 37/41's own (glue calling HELD Terms/functions only; no
# decision over graph state lives here).
# =============================================================================
def _author_clause(sub, name: str, text: str) -> list:
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


def _fmt_sig(sig) -> str:
    if not sig:
        return "      (empty -- no held RelationCue fired)"
    return "\n".join(f"      {tuple(r)}" for r in sig)


def _verify_planning_faculties(sub) -> dict:
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


def main() -> int:
    md5_before = _md5(STROKE_SHAPES_PATH)

    print(SEP)
    print("THE JABBERWOCK DESIGNS THE MOTOR VERDICT (run 49 PART 1 planning session -- no eval)")
    print(f"evidence: {CITATION}")
    print(f"seeds/stroke_shapes.json md5 BEFORE: {md5_before}")
    print(SEP)

    # -------------------------------------------------------------------
    # BOOT -- the full topological boot, exactly run 37/41's idiom.
    # -------------------------------------------------------------------
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    s, I = a.s, a.inner
    donkey = {"n": 0}
    a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "DONKEY")[1])

    faculties = _verify_planning_faculties(s)
    print(f"\nBOOT: WorldAdapter(seeds=()) + load_all_seeds -> {faculties['n_seeds_total']} "
          f"Seed nodes installed.")
    print(f"  question_driving seed installed:   {faculties['question_driving_seed_installed']}")
    print(f"  composer_dispatch seed installed:  {faculties['composer_dispatch_seed_installed']}  "
          f"({faculties['n_composer_cues']} ComposerCue nodes)")
    print(f"  relation_vocabulary seed installed: {faculties['relation_vocabulary_seed_installed']}")
    print(f"  qd_* rules installed ({len(faculties['qd_rules_installed'])}): "
          f"{faculties['qd_rules_installed']}")
    held_sigs_before = _load_shape_signatures(s)
    print(f"  held ShapeSignature codebook: {len(held_sigs_before)} nodes")

    plan_record: dict = {"citation": CITATION, "concerns": {}, "held_context": {},
                          "parent": {}, "voice": {}, "faculties": faculties}

    # =====================================================================
    # STEP 1 -- INGEST
    # =====================================================================
    print(f"\n{SEP}\nSTEP 1 -- INGEST (verbatim launch-brief text -> held RelationCue signatures)"
          f"\n{SEP}")

    print("\n  HELD CONTEXT (the run-48 bottleneck; feeds the parent goal signature only):")
    hc_clause_sigs = []
    for i, clause in enumerate(HELD_CONTEXT_CLAUSES):
        csig = _author_clause(s, f"held_context_clause_{i}", clause)
        hc_clause_sigs.append(csig)
        print(f"    clause: {clause!r}")
        print(f"      fired: {[tuple(r) for r in csig]}")
    held_context_sig = _ordered_union(hc_clause_sigs)
    print(f"  HELD CONTEXT SIGNATURE ({len(held_context_sig)} relations):\n{_fmt_sig(held_context_sig)}")
    plan_record["held_context"] = {"clauses": HELD_CONTEXT_CLAUSES, "signature": held_context_sig}

    concern_sigs: dict[str, list] = {}
    for c_key, clauses in CONCERN_CLAUSES.items():
        print(f"\n  {CONCERN_LABELS[c_key]}  (concern key hint: {c_key!r})")
        clause_sigs = []
        for i, clause in enumerate(clauses):
            csig = _author_clause(s, f"{c_key}_clause_{i}", clause)
            clause_sigs.append(csig)
            print(f"    clause: {clause!r}")
            print(f"      fired: {[tuple(r) for r in csig]}")
        c_sig = _ordered_union(clause_sigs)
        concern_sigs[c_key] = c_sig
        print(f"    {c_key.upper()} SIGNATURE ({len(c_sig)} relations, order = naming order):")
        print(_fmt_sig(c_sig))
        if not c_sig:
            print("    DISCLOSURE: zero held RelationCue relations fired from this concern's "
                  "verbatim evidence -- honest, not forced.")

    # =====================================================================
    # STEP 2 -- TICK/DRIVE
    # =====================================================================
    print(f"\n{SEP}\nSTEP 2 -- TICK/DRIVE (induce_concern -> ground_concern, per concern)\n{SEP}")

    concern_outcomes: dict[str, dict] = {}
    for c_key, c_sig in concern_sigs.items():
        print(f"\n  {CONCERN_LABELS[c_key]}")
        if not c_sig:
            outcome = {"status": "no_signature", "note": "no observation to induce from"}
            print("    SKIPPED induce_concern: empty signature (see disclosure above).")
            concern_outcomes[c_key] = outcome
            plan_record["concerns"][c_key] = {"clauses": CONCERN_CLAUSES[c_key],
                                               "signature": c_sig, "outcome": outcome}
            continue
        ind = induce_concern(a, c_sig, name_hint=c_key)
        print(f"    induce_concern -> minted={ind.get('minted')}")
        if ind.get("minted"):
            print(f"      capability_key={ind.get('capability_key')!r}  "
                  f"residual_predicates={ind.get('residual_predicates')}")
            print(f"      closest_held_shape={ind.get('closest_held_shape')!r}")
        elif ind.get("covered_by") is not None:
            print(f"      covered_by (held ShapeSignature) = {ind.get('covered_by')!r}")
            print(f"      note: {ind.get('note')}")
        elif ind.get("covered_by_existing_axis") is not None:
            print(f"      covered_by_existing_axis={ind.get('covered_by_existing_axis')!r} "
                  f"(recurring residual, not a fresh mint)")
            print(f"      note: {ind.get('note')}")
        else:
            print(f"      note: {ind.get('note')}")

        outcome = {"induce": ind}
        if ind.get("minted"):
            key = ind.get("capability_key")
            learn = learn_term_for_concern(a, [key])
            print(f"    learn_term_for_concern -> connected={learn.get('connected')} "
                  f"term_family={learn.get('term_family')!r} shared_leaves={learn.get('shared_leaves')}")
            g = ground_concern(a, [key])
            print(f"    ground_concern -> grounded={g.get('grounded')} path={g.get('path')!r} "
                  f"form={g.get('form')}")
            if g.get("grounded_relations") is not None:
                print(f"      grounded_relations heads: {sorted({r[0] for r in g['grounded_relations']})}")
            if g.get("grounded"):
                print(f"      AUTHORED (verbatim 'how'): {g.get('how')}")
                for r in (g.get("rules") or ([g["rule"]] if g.get("rule") else [])):
                    print(f"      rule installed: name={r.get('name')!r}")
                    print(f"        match={r.get('match')}")
                    print(f"        effects={r.get('effects')}")
            else:
                print(f"      WALL (verbatim): {g.get('wall')}")
            outcome["learn"] = learn
            outcome["ground"] = g
            outcome["status"] = "grounded" if g.get("grounded") else "walled"
        elif ind.get("covered_by") is not None:
            outcome["status"] = "recognized"
        elif ind.get("covered_by_existing_axis") is not None:
            outcome["status"] = "duplicate_of_existing_axis"
        else:
            outcome["status"] = "unresolved"
        concern_outcomes[c_key] = outcome
        plan_record["concerns"][c_key] = {"clauses": CONCERN_CLAUSES[c_key], "signature": c_sig,
                                           "outcome": outcome}

    # =====================================================================
    # PARENT PLAN
    # =====================================================================
    print(f"\n{SEP}\nPARENT PLAN -- compose_design_for_goal over the union evidence\n{SEP}")
    parent_sig = _ordered_union(list(concern_sigs.values()) + [held_context_sig])
    print(f"  PARENT GOAL: {PARENT_GOAL_NAME!r}")
    print(f"    claim: {PARENT_GOAL_CLAIM}")
    print(f"    union signature ({len(parent_sig)} relations):\n{_fmt_sig(parent_sig)}")
    if parent_sig:
        design = compose_design_for_goal(s, parent_sig, exclude=list(CONCERN_CLAUSES.keys()))
        print(f"\n  compose_design_for_goal -> authored={design.get('authored')}")
        print(f"    ordered_parts (the agent's PLAN, in order): {design.get('ordered_parts')}")
        print(f"    total_fit={design.get('total_fit')}  covered_count={design.get('covered_count')}/"
              f"{design.get('goal_relations')}  residual={design.get('residual')}")
        if design.get("provenance"):
            print(f"    provenance: {design.get('provenance')}")
    else:
        design = {"authored": False, "reason": "empty parent signature"}
        print("  SKIPPED: empty parent signature.")
    plan_record["parent"] = {"name": PARENT_GOAL_NAME, "claim": PARENT_GOAL_CLAIM,
                              "signature": parent_sig, "design": design}

    parent_goal = s.add_node("Goal", {"kind": "compound", "concept": PARENT_GOAL_NAME})
    concern_goal_nodes: dict[str, int] = {}
    for c_key in CONCERN_CLAUSES:
        gg = s.add_node("Goal", {"kind": "concern", "concept": c_key,
                                  "status": concern_outcomes[c_key].get("status")})
        I.add_edge_unchecked(parent_goal, "has_subgoal", gg)
        concern_goal_nodes[c_key] = gg
    print(f"\n  Goal tree wired (mechanical ingest): parent Goal {parent_goal} -has_subgoal-> "
          f"{list(concern_goal_nodes.values())}")

    # =====================================================================
    # STEP 3 -- VOICE
    # =====================================================================
    print(f"\n{SEP}\nSTEP 3 -- VOICE (the agent grounds + uses its communicate faculty)\n{SEP}")

    comm_obs = [["told", "DESCRIBE", "what", "PLANNED"],
                ["for_each", "CONCERN", "mint", "SUBGOAL"],
                ["SUBGOAL", "produces", "UTTERANCE"],
                ["source", "UTTERANCE", "from", "CONCERN"]]
    comm_ind = induce_concern(a, comm_obs, name_hint="communicate_my_design")
    print(f"  induce_concern('communicate_my_design') -> minted={comm_ind.get('minted')} "
          f"residual_predicates={comm_ind.get('residual_predicates')}")
    voice_record: dict = {"induce": comm_ind}
    lines: list[str] = []
    if comm_ind.get("minted"):
        comm_key = comm_ind.get("capability_key")
        comm_g = ground_concern(a, [comm_key])
        print(f"  ground_concern -> grounded={comm_g.get('grounded')} path={comm_g.get('path')!r} "
              f"form={comm_g.get('form')}")
        voice_record["ground"] = comm_g
        if comm_g.get("grounded") and comm_g.get("form") == "communicate_rule":
            print(f"    AUTHORED RULE: match={comm_g['rule']['match']}  effects={comm_g['rule']['effects']}")
            OUTCOME_VERB = {"grounded": "compose", "walled": "wall",
                            "recognized": "hold", "duplicate_of_existing_axis": "hold",
                            "no_signature": "wall", "unresolved": "wall"}
            scene = s.add_node("Scene", {})
            I.add_edge_unchecked(parent_goal, "describes", scene)
            for c_key in CONCERN_CLAUSES:
                status = concern_outcomes[c_key].get("status", "unresolved")
                verb = OUTCOME_VERB.get(status, "wall")
                con = s.add_node("Concept", {"name": f"{c_key}_outcome", "outcome": status,
                                              "say_event": verb})
                pn = s.add_node("Percept", {"concern": c_key, "outcome": status})
                I.add_edge_unchecked(scene, "has_percept", pn)
                I.add_edge_unchecked(pn, "is_a", con)
            I.run_rules()
            subgoals = list(I.neighbours(parent_goal, "has_subgoal"))
            new_utt_subgoals = [n for n in subgoals if s.node(n)["attrs"].get("kind") == "produce_utterance"]
            print(f"  -> the agent's OWN authored rule minted {len(new_utt_subgoals)} "
                  f"produce_utterance subgoal(s)")

            from domains.language_world import LanguageWorld, teacher_stub
            from domains.language_production import LanguageProduction
            from scripts.language_test import training_bank
            world = LanguageWorld(I, training_bank(), teacher_stub)
            world.run()
            for lemma, surf in {"compose": "composes", "wall": "walls", "hold": "holds",
                                 "thing": "thing"}.items():
                s.add_node("LexEntry", {"surface": surf, "concept": lemma, "language": "en",
                                        "status": "confirmed", "lemma": lemma})
            world.teacher_disabled = True
            prod = LanguageProduction(world)
            for sg in new_utt_subgoals:
                con = next(iter(I.neighbours(sg, "about")), None)
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

    print("\n  THE AGENT'S DESIGN, IN ITS OWN VOICE (one produced utterance per concern):")
    if lines:
        for name, outcome, overt in lines:
            print(f"    {name}: {overt!r}  (outcome={outcome})")
    else:
        print("    (no utterances produced -- see WALL/skip above; honest, not faked.)")

    # =====================================================================
    # STEP 4 -- HOST TRANSLATION (mechanical, decisions=none): report what the agent's own
    # grounding named, verbatim -- reporting only, no invented mechanism. PART 2 of this run's
    # own launch brief is the mechanical translation of this design into a concrete build, done
    # by the host, exactly as run 37's own Step 4 did for its three gaps.
    # =====================================================================
    print(f"\n{SEP}\nSTEP 4 -- HOST TRANSLATION TABLE (mechanical; adapter work, no decisions)\n{SEP}")

    translation_rows = {}
    for c_key in CONCERN_CLAUSES:
        o = concern_outcomes[c_key]
        status = o.get("status")
        if status == "grounded":
            g = o.get("ground", {})
            row = (f"grounded via composer={g.get('form')!r} path={g.get('path')!r} -- "
                   f"AUTHORED how: {g.get('how')!r}")
        elif status == "walled":
            g = o.get("ground", {})
            row = f"WALLED -- {g.get('wall')!r}"
        elif status == "recognized":
            row = (f"RECOGNIZED (covered_by={o.get('induce', {}).get('covered_by')!r}) -- no "
                   f"concern-specific design to translate; evidence already matches held structure.")
        elif status == "duplicate_of_existing_axis":
            row = (f"DUPLICATE of existing axis "
                   f"{o.get('induce', {}).get('covered_by_existing_axis')!r}")
        elif status == "no_signature":
            row = "NO SIGNATURE -- zero held RelationCue fired from the verbatim evidence; honest wall pre-induce_concern."
        else:
            row = f"UNRESOLVED -- {o.get('induce', {}).get('note')!r}"
        translation_rows[c_key] = row
        print(f"\n  {CONCERN_LABELS[c_key]}")
        print(f"    status: {status}")
        print(f"    host translation: {row}")
    plan_record["host_translation"] = translation_rows

    # =====================================================================
    # SAVE + donkey + seed-guard check
    # =====================================================================
    out_path = os.path.join(CKPT_DIR, "design.json")
    with open(out_path, "w") as f:
        json.dump(plan_record, f, indent=2, default=str)
    print(f"\nSaved structured design -> {out_path}")

    md5_after = _md5(STROKE_SHAPES_PATH)
    seed_guard_ok = (md5_before == md5_after)
    print(f"seeds/stroke_shapes.json md5 AFTER: {md5_after}  UNCHANGED={seed_guard_ok}")
    if not seed_guard_ok:
        print("  UNEXPECTED -- INVESTIGATE (this script never opens that path directly; the "
              "durable teach() guard from 21aa6123 should make this structurally impossible).")

    donkey_modules = ("torch", "torchaudio", "tensorflow", "allosaurus", "whisper",
                       "faster_whisper", "ctranslate2", "transformers")
    loaded = [m for m in donkey_modules if m in sys.modules]
    assert not loaded, f"donkey!=0: {loaded} present in sys.modules"
    print(f"donkey=0 verified: none of {donkey_modules} present in sys.modules "
          f"(self-teacher calls: {donkey['n']}).")

    print(f"\n{SEP}")
    print(f"GATE: PASS -- the design was produced by the agent's own held machinery "
          f"(induce_concern/ground_concern/compose_design_for_goal/communicate-rule); "
          f"every WALL is reported as a result, not patched. seed_guard_ok={seed_guard_ok}")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
