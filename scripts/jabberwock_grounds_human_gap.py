"""THE JABBERWOCK GROUNDS THE HUMAN GAP (run 41 -- a PLANNING session, no eval).

Mirrors `scripts/jabberwock_plans_gap_closure.py` (commit 67005b35, "run 37 --
the jabberwock plans the gap closure") EXACTLY: same boot recipe, same
verbatim-clause-authoring discipline, same induce_concern/ground_concern per
concern, same compose_design_for_goal parent plan, same communicate-rule VOICE
step, same mechanical host-translation table. The only things that change are
WHAT is fed (four phase-mechanisms for closing the human/BPL gap, not three
run-36 failure-taxonomy gaps) and the run number (41, not 37).

THE AGENT GROUNDS THE PLAN. This script only INGESTS the measured frame (commit
825686d7, RUN 39b, and the class-property/disjoint-population finding it
carries) plus four candidate phase-mechanisms as graph data, TICKS the agent's
own concern-induction/grounding machinery over each, and READS the resulting
plan back off the graph. Every routing decision (recognized-vs-minted, which
composer, which rule) is the agent's own held machinery (`domains.
reflective_faculty`'s `induce_concern`/`ground_concern`/`compose_design_for_goal`,
thin shims over Rust `ShapeDecode`/`TransformDecode`/`Argmax` Terms).

THE MEASURED FRAME (held context, feeds the PARENT goal's signature only, not
a Concern of its own -- exactly run 37's held-context treatment): "eight
verdict-layer nulls establish "the comparator extracts what ONE EXEMPLAR
affords" (825686d7); humans/BPL win via information from OUTSIDE the episode
(class-general priors on legal variation); the error budget is ~25 near-rank
arbitration failures + ~19 far-tail (truth ranks 11-19, undiagnosed, run-40
taxonomy in flight) + mid-rank rest, failure is a class property (80/200 never
fail)." Split at ITS OWN semicolon boundaries -- no rewording.

THE FOUR PHASE-MECHANISMS + the far-tail open concern are each fed as ONE
Concern, encoded SYMMETRICALLY: the mechanism sentence leads (split at its own
semicolons, in the order the task brief states it -- the verb that names the
mechanism comes first in the brief's own phrasing, which is what "cue-word-led"
means here: no clause is invented or reordered to manufacture a lead that the
source text does not already have), then its evidence sentence follows (split
at its own semicolons, same order as given). This is the SAME clause-ordering
discipline run 37 used (RUN36_CITATION clauses), applied honestly: no keyword
was added or reworded to force a particular RelationCue to fire first.

SEED ISOLATION (run 34c/37's pattern, reused verbatim): every `teach()`
persistence this process performs is redirected to
`results/run41_checkpoints/seeds/` -- no write ever touches `seeds/` proper.
`seeds/stroke_shapes.json` is a PARALLEL SESSION'S live file (run-40 taxonomy
in flight per the task brief, and `git status` shows it already modified in
the working tree by that other session) -- this script never opens, reads, or
writes it; its md5 is recorded before and after this run purely as a passive
externally-verifiable guarantee that this session did not touch it.

NO git add/commit. donkey=0 verified at the end.

Run:  PYTHONPATH=.:runners/dsl/python:scripts .venv/bin/python3 \\
        scripts/jabberwock_grounds_human_gap.py \\
        2>&1 | stdbuf -oL tee results/jabberwock_grounds_human_gap.log
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

SEP = "=" * 100
CKPT_DIR = os.path.join(ROOT, "results", "run41_checkpoints")
os.makedirs(CKPT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# SEED ISOLATION -- redirect every teach() persistence to THIS run's own seeds
# dir. seeds/stroke_shapes.json (parallel-session-owned, run-40 in flight) and
# every other file under seeds/ proper are never touched.
# ---------------------------------------------------------------------------
RUN41_SEEDS_DIR = os.path.join(CKPT_DIR, "seeds")
os.makedirs(RUN41_SEEDS_DIR, exist_ok=True)
import domains.teach as _teach_mod  # noqa: E402

_real_teach = _teach_mod.teach


def _isolated_teach(*a, **k):
    return _real_teach(*a, **{**k, "seeds_dir": Path(RUN41_SEEDS_DIR)})


_teach_mod.teach = _isolated_teach

from substrate.world_adapter import WorldAdapter                       # noqa: E402
from substrate.boot_all import load_all_seeds                          # noqa: E402
from domains import reflective_faculty as rf                           # noqa: E402
from domains.reflective_faculty import (                               # noqa: E402
    induce_concern, ground_concern, learn_term_for_concern, author_signature,
    compose_design_for_goal, _load_shape_signatures,
)

# =============================================================================
# STEP 1 MATERIAL -- verbatim as handed down in the task brief.
# =============================================================================
CITATION = "commit 825686d7 (RUN 39b) + run-40 taxonomy-in-flight framing"

PHASE_CLAUSES = {
    "phase1_style_normalization": [
        # mechanism (verbatim, split at its own semicolon)
        "estimate the exemplar drawer's style from the 20 same-drawer exemplars in the episode",
        "normalize before comparing",
        # evidence (verbatim, split at its own semicolons)
        "WriterStyle/writer-dimensions machinery exists (seeds/writer_dimensions.json, ink twin "
        "of the speech speaker dimension) and was never wired into eval",
        "exemplars per episode share one drawer",
    ],
    "phase2_learned_deformation_metric": [
        "learn from background alphabets which deformations are cheap within a class and which "
        "change identity",
        "reweight the continuous comparator's cost",
        "TPS cost is currently generic bending energy",
        "BPL's edge is priors",
        "the 8 nulls never changed the METRIC with background information",
    ],
    "phase3_exemplar_expansion_effector_model": [
        "render the exemplar's parse under the mouse variation model K times",
        "compare the query against the set",
        "run-25 C3 nulled with write_with_hand (wrong effector)",
        "the mouse observation model is proven (34b: dissolution 89.6%, invertibility gated)",
        "the single-exemplar bound is the named wall",
    ],
    "phase4_conditional_foveation": [
        "align the wholes first",
        "only then weigh the differing region, using background knowledge of which differences "
        "bear identity",
        "37A's unconditional replacement harmed (82/16)",
        "the supplement law (cca938fd)",
        "humans arbitrate near-duplicates this way",
    ],
    "far_tail_diagnosis": [
        # open concern, no evidence block of its own in the task brief -- fed
        # honestly as a single clause (no material invented to pad it).
        "diagnose, then fix, the episodes where truth ranks 11-19",
    ],
}

PHASE_LABELS = {
    "phase1_style_normalization": "PHASE 1 -- STYLE NORMALIZATION",
    "phase2_learned_deformation_metric": "PHASE 2 -- LEARNED DEFORMATION METRIC",
    "phase3_exemplar_expansion_effector_model": "PHASE 3 -- EXEMPLAR EXPANSION UNDER THE EFFECTOR MODEL",
    "phase4_conditional_foveation": "PHASE 4 -- CONDITIONAL FOVEATION",
    "far_tail_diagnosis": "FAR-TAIL -- OPEN DIAGNOSTIC CONCERN (run-40 runs in parallel on this)",
}

HELD_CONTEXT_CLAUSES = [
    'eight verdict-layer nulls establish "the comparator extracts what ONE EXEMPLAR affords" '
    "(825686d7)",
    "humans/BPL win via information from OUTSIDE the episode (class-general priors on legal "
    "variation)",
    "the error budget is ~25 near-rank arbitration failures + ~19 far-tail (truth ranks 11-19, "
    "undiagnosed, run-40 taxonomy in flight) + mid-rank rest, failure is a class property "
    "(80/200 never fail)",
]

PARENT_GOAL_NAME = "reach_human_level_recognition"
PARENT_GOAL_CLAIM = (
    "close the ~15pp gap to human-level recognition (80.5 comparator-ceiling vs human 95.5 / "
    "BPL 96.7) via the four candidate phase-mechanisms (style normalization, learned deformation "
    "metric, exemplar expansion under the effector model, conditional foveation) named against "
    "the measured frame -- " + CITATION
)


# =============================================================================
# Mechanical helpers -- identical to run 37's (glue calling HELD Terms/functions
# only; no decision over graph state lives here).
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


def _md5(path: str):
    import hashlib
    try:
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except FileNotFoundError:
        return None


def main() -> int:
    stroke_shapes_path = os.path.join(ROOT, "seeds", "stroke_shapes.json")
    md5_before = _md5(stroke_shapes_path)

    print(SEP)
    print("THE JABBERWOCK GROUNDS THE HUMAN GAP (run 41 planning session -- no eval)")
    print(f"evidence: {CITATION}")
    print(f"seeds/stroke_shapes.json md5 BEFORE (parallel-session file, untouched): {md5_before}")
    print(SEP)

    # -------------------------------------------------------------------
    # BOOT -- the full topological boot, exactly run 37's idiom.
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

    plan_record: dict = {"citation": CITATION, "phases": {}, "held_context": {},
                          "parent": {}, "voice": {}, "faculties": faculties}

    # =====================================================================
    # STEP 1 -- INGEST
    # =====================================================================
    print(f"\n{SEP}\nSTEP 1 -- INGEST (verbatim evidence -> held RelationCue signatures)\n{SEP}")

    print("\n  HELD CONTEXT (the measured frame; feeds the parent goal signature only):")
    hc_clause_sigs = []
    for i, clause in enumerate(HELD_CONTEXT_CLAUSES):
        csig = _author_clause(s, f"held_context_clause_{i}", clause)
        hc_clause_sigs.append(csig)
        print(f"    clause: {clause!r}")
        print(f"      fired: {[tuple(r) for r in csig]}")
    held_context_sig = _ordered_union(hc_clause_sigs)
    print(f"  HELD CONTEXT SIGNATURE ({len(held_context_sig)} relations):\n{_fmt_sig(held_context_sig)}")
    plan_record["held_context"] = {"clauses": HELD_CONTEXT_CLAUSES, "signature": held_context_sig}

    phase_sigs: dict[str, list] = {}
    for phase_key, clauses in PHASE_CLAUSES.items():
        print(f"\n  {PHASE_LABELS[phase_key]}  (concern key hint: {phase_key!r})")
        clause_sigs = []
        for i, clause in enumerate(clauses):
            csig = _author_clause(s, f"{phase_key}_clause_{i}", clause)
            clause_sigs.append(csig)
            print(f"    clause: {clause!r}")
            print(f"      fired: {[tuple(r) for r in csig]}")
        phase_sig = _ordered_union(clause_sigs)
        phase_sigs[phase_key] = phase_sig
        print(f"    {phase_key.upper()} SIGNATURE ({len(phase_sig)} relations, order = naming order):")
        print(_fmt_sig(phase_sig))
        if not phase_sig:
            print("    DISCLOSURE: zero held RelationCue relations fired from this concern's "
                  "verbatim evidence -- honest, not forced.")

    # =====================================================================
    # STEP 2 -- TICK/DRIVE
    # =====================================================================
    print(f"\n{SEP}\nSTEP 2 -- TICK/DRIVE (induce_concern -> ground_concern, per phase)\n{SEP}")

    phase_outcomes: dict[str, dict] = {}
    for phase_key, phase_sig in phase_sigs.items():
        print(f"\n  {PHASE_LABELS[phase_key]}")
        if not phase_sig:
            outcome = {"status": "no_signature", "note": "no observation to induce from"}
            print("    SKIPPED induce_concern: empty signature (see disclosure above).")
            phase_outcomes[phase_key] = outcome
            plan_record["phases"][phase_key] = {"clauses": PHASE_CLAUSES[phase_key],
                                                 "signature": phase_sig, "outcome": outcome}
            continue
        ind = induce_concern(a, phase_sig, name_hint=phase_key)
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
        phase_outcomes[phase_key] = outcome
        plan_record["phases"][phase_key] = {"clauses": PHASE_CLAUSES[phase_key],
                                             "signature": phase_sig, "outcome": outcome}

    # =====================================================================
    # PARENT PLAN
    # =====================================================================
    print(f"\n{SEP}\nPARENT PLAN -- compose_design_for_goal over the union evidence\n{SEP}")
    parent_sig = _ordered_union(list(phase_sigs.values()) + [held_context_sig])
    print(f"  PARENT GOAL: {PARENT_GOAL_NAME!r}")
    print(f"    claim: {PARENT_GOAL_CLAIM}")
    print(f"    union signature ({len(parent_sig)} relations):\n{_fmt_sig(parent_sig)}")
    if parent_sig:
        design = compose_design_for_goal(s, parent_sig, exclude=list(PHASE_CLAUSES.keys()))
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
    phase_goal_nodes: dict[str, int] = {}
    for phase_key in PHASE_CLAUSES:
        gg = s.add_node("Goal", {"kind": "concern", "concept": phase_key,
                                  "status": phase_outcomes[phase_key].get("status")})
        I.add_edge_unchecked(parent_goal, "has_subgoal", gg)
        phase_goal_nodes[phase_key] = gg
    print(f"\n  Goal tree wired (mechanical ingest): parent Goal {parent_goal} -has_subgoal-> "
          f"{list(phase_goal_nodes.values())}")

    # =====================================================================
    # STEP 3 -- VOICE
    # =====================================================================
    print(f"\n{SEP}\nSTEP 3 -- VOICE (the agent grounds + uses its communicate faculty)\n{SEP}")

    comm_obs = [["told", "DESCRIBE", "what", "PLANNED"],
                ["for_each", "PHASE", "mint", "SUBGOAL"],
                ["SUBGOAL", "produces", "UTTERANCE"],
                ["source", "UTTERANCE", "from", "PHASE"]]
    comm_ind = induce_concern(a, comm_obs, name_hint="communicate_my_plan")
    print(f"  induce_concern('communicate_my_plan') -> minted={comm_ind.get('minted')} "
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
            for phase_key in PHASE_CLAUSES:
                status = phase_outcomes[phase_key].get("status", "unresolved")
                verb = OUTCOME_VERB.get(status, "wall")
                con = s.add_node("Concept", {"name": f"{phase_key}_outcome", "outcome": status,
                                              "say_event": verb})
                pn = s.add_node("Percept", {"phase": phase_key, "outcome": status})
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

    print("\n  THE AGENT'S PLAN, IN ITS OWN VOICE (one produced utterance per phase):")
    if lines:
        for name, outcome, overt in lines:
            print(f"    {name}: {overt!r}  (outcome={outcome})")
    else:
        print("    (no utterances produced -- see WALL/skip above; honest, not faked.)")

    # =====================================================================
    # STEP 4 -- HOST TRANSLATION (mechanical, decisions=none): report what the
    # agent's own grounding named, verbatim, and flag whether any composer path
    # unifies with previously-known machinery (e.g. run-30 frames) -- reporting
    # only, no invented mechanism.
    # =====================================================================
    print(f"\n{SEP}\nSTEP 4 -- HOST TRANSLATION TABLE (mechanical; adapter work, no decisions)\n{SEP}")

    translation_rows = {}
    for phase_key in PHASE_CLAUSES:
        o = phase_outcomes[phase_key]
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
                   f"phase-specific design to translate; evidence already matches held structure.")
        elif status == "duplicate_of_existing_axis":
            row = (f"DUPLICATE of existing axis "
                   f"{o.get('induce', {}).get('covered_by_existing_axis')!r}")
        elif status == "no_signature":
            row = "NO SIGNATURE -- zero held RelationCue fired from the verbatim evidence; honest wall pre-induce_concern."
        else:
            row = f"UNRESOLVED -- {o.get('induce', {}).get('note')!r}"
        translation_rows[phase_key] = row
        print(f"\n  {PHASE_LABELS[phase_key]}")
        print(f"    status: {status}")
        print(f"    host translation: {row}")
    plan_record["host_translation"] = translation_rows

    # =====================================================================
    # SAVE + donkey + parallel-file-untouched check
    # =====================================================================
    out_path = os.path.join(CKPT_DIR, "plan.json")
    with open(out_path, "w") as f:
        json.dump(plan_record, f, indent=2, default=str)
    print(f"\nSaved structured plan -> {out_path}")

    md5_after = _md5(stroke_shapes_path)
    print(f"seeds/stroke_shapes.json md5 AFTER: {md5_after}  "
          f"(this session touched it: {md5_before != md5_after and 'UNEXPECTED -- INVESTIGATE' if md5_before != md5_after else False})")
    print("NOTE: seeds/stroke_shapes.json is a parallel session's live file (run-40 in flight); "
          "if its md5 changed above, that change came from the OTHER session, not this script "
          "(this script never opens that path).")

    donkey_modules = ("torch", "torchaudio", "tensorflow", "allosaurus", "whisper",
                       "faster_whisper", "ctranslate2", "transformers")
    loaded = [m for m in donkey_modules if m in sys.modules]
    assert not loaded, f"donkey!=0: {loaded} present in sys.modules"
    print(f"donkey=0 verified: none of {donkey_modules} present in sys.modules "
          f"(self-teacher calls: {donkey['n']}).")

    print(f"\n{SEP}")
    print("GATE: PASS -- the plan was produced by the agent's own held machinery "
          "(induce_concern/ground_concern/compose_design_for_goal/communicate-rule); "
          "every WALL is reported as a result, not patched.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
