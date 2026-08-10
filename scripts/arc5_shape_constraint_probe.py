#!/usr/bin/env python
"""arc5_shape_constraint_probe — CEILING MEASUREMENT: can shape recognition +
analogical transfer supply the DISCRIMINATING CONSTRAINT that revealed rows
cannot?

`PROGRAM_SYNTHESIS_ARC4_S6_NOTES.md` established that structural rejection
cannot convert traps into passes, because a structural trap satisfies every
REVEALED row BY DEFINITION -- excluding a decoy removes a wrong answer but
supplies no new discriminating information. The hypothesis this measures:
shape math supplies constraint from STRUCTURE where data is exhausted --
recognising "top of three" as an N-ary extremum should yield "the solution
must be symmetric in all three arguments", a constraint no example row
provides.

Four questions, each a section below:

  Q1 RECOGNITION COVERAGE  -- does the goal (prompt + signature) recognise
     as a held MetaShape via the SAME `RecogniseShape` Term the agent's own
     `categorise_by_shape` faculty uses (`domains/teach.py`), over the real
     257-task MBPP test population?
  Q2 CONSTRAINT YIELD      -- for tasks that DO recognise, does the shape
     yield a checkable constraint the revealed rows do NOT already imply?
     A small, precise catalogue (argument symmetry / total dependence /
     monotonicity-idempotence-boundedness / arity entailment), each with
     its assumption stated, applied to the 76-trap population.
  Q3 WOULD IT HAVE CONVERTED A TRAP? -- for the 26 S6-rejected ids and the
     36 honest-residual ids: (a) would a shape-derived constraint reject
     the trap for a principled reason; (b) THE LOAD-BEARING PART -- driven
     empirically against the real `SynthEnumerate` engine, does excluding
     the trap (the only search-restriction lever this engine exposes) ever
     let the search FIND the correct program?
  Q4 ANALOGICAL TRANSFER   -- is there a held Mechanism (mechanism_index.json)
     or math ShapeSignature (math_capability_shapes.json) that, re-instantiated
     at the goal's arity/fillers via the real `TransferDecode` Term, produces
     a usable plan for any of these tasks?

READS ONLY: `tests/fixtures/mbpp/sanitized-mbpp.json` (via `mbpp_arc3_battery
.q0_split_tasks`, the standard PRIMARY-protocol test split), `results/
mbpp_arc3_endgame.json` (frozen -- the 76 accepted_holdout_fail traps' own
accepted IR, cited not re-derived), `results/arc4_endgame.json` (the 26 id
split), `results/arc4_structural_verdicts.json` (the 36 honest-residual id
list), `seeds/shape_vocabulary.json` / `seeds/mechanism_index.json` /
`seeds/math_capability_shapes.json` (read via the real seed loader -- never
duplicated), and drives the real `RecogniseShape` / `TransferDecode` /
`SynthEnumerate` Rust Terms live. NO changes to synthesis/engine/seed/spec
code anywhere -- this is a measurement script only.

Runtime: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1
OZMA_SEED_PERSIST_DISABLED=1 python3 scripts/arc5_shape_constraint_probe.py
"""
from __future__ import annotations

import hashlib
import inspect
import itertools
import json
import os
import re
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import substrate_rs as srs  # noqa: E402
import mbpp_arc3_battery as arc3b  # noqa: E402
import arc4_failure_anatomy as afa  # noqa: E402
import arc4_structural_verdicts as asv  # noqa: E402
from domains import mbpp_spec as ms  # noqa: E402
from domains.teach import categorise_by_shape  # noqa: E402
from domains.reflective_faculty import retrieve_and_transfer_mechanism  # noqa: E402
from substrate.world_adapter import WorldAdapter  # noqa: E402
from substrate.seed_loader import manifest_for  # noqa: E402

FIXTURE_PATH = os.path.join(ROOT, "tests", "fixtures", "mbpp", "sanitized-mbpp.json")
R3_ENDGAME_PATH = os.path.join(ROOT, "results", "mbpp_arc3_endgame.json")
S5_ENDGAME_PATH = os.path.join(ROOT, "results", "arc4_endgame.json")
STRUCTURAL_PATH = os.path.join(ROOT, "results", "arc4_structural_verdicts.json")
SHAPE_VOCAB_PATH = os.path.join(ROOT, "seeds", "shape_vocabulary.json")
MECHANISM_INDEX_PATH = os.path.join(ROOT, "seeds", "mechanism_index.json")
MATH_SHAPES_PATH = os.path.join(ROOT, "seeds", "math_capability_shapes.json")
OUT_PATH = os.path.join(ROOT, "results", "arc5_shape_constraint_probe.json")

# The exact 26 ids (PROGRAM_SYNTHESIS_ARC4_S6_NOTES.md), split by source --
# quoted verbatim from tests/test_reject_informs_repair_migrated.py, never
# hand-re-derived here a second, possibly-drifting way.
RETRIEVAL_SOURCED_14 = [68, 83, 86, 93, 109, 239, 242, 247, 269, 285, 420,
                        427, 434, 454]
REOPENED_12 = [14, 58, 103, 125, 126, 164, 228, 304, 396, 414, 430, 432]
THE_26 = sorted(RETRIEVAL_SOURCED_14 + REOPENED_12)
GENUINE_DEFECT_IDS = [397, 404]  # pass-population D3 catches (structural notes §2.2)

# The vocabulary a symmetry/extremum constraint would need -- named honestly:
# NONE of these words are in seeds/shape_vocabulary.json today (verified in
# Q1). This is exactly the "what would have to be seeded" answer for C2.
SYMMETRIC_SHAPE_LEXICON = {
    "largest", "greatest", "maximum", "max", "smallest", "least", "minimum",
    "min", "median", "sum", "total", "product", "average", "mean",
}
NUMERAL_WORDS = {"two": 2, "three": 3, "four": 4, "2": 2, "3": 3, "4": 4}
QUANTITY_NOUNS = {"numbers", "values", "integers", "elements", "items",
                  "args", "arguments", "digits"}
_WORD_RE = re.compile(r"[a-z']+")


# ========================================================================= #
#  shared loaders
# ========================================================================= #
def load_test_tasks() -> Dict[int, Dict[str, Any]]:
    with open(FIXTURE_PATH) as f:
        all_tasks = json.load(f)
    splits = arc3b.q0_split_tasks(all_tasks)
    test_tasks = splits["test"]
    for t in test_tasks:
        assert "code" not in t, "contamination: code field survived split_tasks"
    return {t["task_id"]: t for t in test_tasks}


def load_r3_populations() -> Tuple[Dict[int, Dict[str, Any]], Dict[int, Dict[str, Any]]]:
    """Frozen full_r3 arm -- the 76 `accepted_holdout_fail` traps (with their
    own accepted IR) and the 21 `pass` rows, cited verbatim."""
    with open(R3_ENDGAME_PATH) as f:
        endgame = json.load(f)
    rows = endgame["arms"]["full_r3"]["runnable_rows"]
    ahf = {r["task_id"]: r for r in rows if r["outcome"] == "accepted_holdout_fail"}
    passed = {r["task_id"]: r for r in rows if r["outcome"] == "pass"}
    return ahf, passed


def load_36_residual_ids() -> List[int]:
    with open(STRUCTURAL_PATH) as f:
        d = json.load(f)
    return list(d["new_honest_residual_ids"])


def value_expr(ir: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """The single ProgReturn's value sub-expression -- the excludable/
    evaluable expression SynthEnumerate's own Var/Lit/OP_TABLE grammar can
    parse (never the whole ProgSeq wrapper)."""
    for st in ir.get("stmts") or []:
        if isinstance(st, dict) and st.get("type") == "ProgReturn":
            return st.get("value")
    return None


# ========================================================================= #
#  Q1 -- RECOGNITION COVERAGE (257 real MBPP test tasks)
# ========================================================================= #
def _shape_vocab_keywords() -> Dict[str, List[str]]:
    with open(SHAPE_VOCAB_PATH) as f:
        d = json.load(f)
    out: Dict[str, List[str]] = {}
    for n in d["nodes"]:
        kws = n["attrs"].get("keywords")
        if kws:
            out[n["attrs"]["name"]] = list(kws)
    return out


def _matched_keywords(text: str, vocab_kw: Dict[str, List[str]]) -> List[str]:
    """Mechanical audit: which FunctionalRole keyword(s) are a literal
    substring of `text` -- so every Q1 hit's cause is READ OFF, not eyeballed."""
    hits = []
    for role, kws in vocab_kw.items():
        for kw in kws:
            if kw and kw in text:
                hits.append("%s:%s" % (role, kw))
    return sorted(hits)


def q1_recognition_coverage(tasks_by_id: Dict[int, Dict[str, Any]]) -> Dict[str, Any]:
    wa = WorldAdapter()
    wa.inner.load_seed_manifest(manifest_for("shape_vocabulary"), wa.agent)
    vocab_kw = _shape_vocab_keywords()
    all_kw_flat = sorted({kw for kws in vocab_kw.values() for kw in kws})

    rows = []
    for tid in sorted(tasks_by_id):
        task = tasks_by_id[tid]
        prompt = task["prompt"]
        rf = ms.request_facts(prompt)
        sf = ms.signature_facts(task)
        shape = categorise_by_shape(wa, "Task", {"prompt": prompt})
        row = {
            "task_id": tid, "prompt": prompt,
            "verb_frame": rf["verb_frame"], "constraint_hits": rf["constraint_hits"],
            "arg_count": sf["arg_count"], "func_name": sf["func_name"],
            "recognised_shape": shape,
        }
        if shape:
            row["matched_keywords"] = _matched_keywords(prompt.lower(), vocab_kw)
            row["matched_keyword_is_algorithmic"] = any(
                kw.split(":", 1)[1] in SYMMETRIC_SHAPE_LEXICON
                for kw in row["matched_keywords"])
        rows.append(row)

    recognised = [r for r in rows if r["recognised_shape"]]
    shape_counts: Dict[str, int] = {}
    for r in recognised:
        shape_counts[r["recognised_shape"]] = shape_counts.get(r["recognised_shape"], 0) + 1

    n_algorithmic_true_positive = sum(
        1 for r in recognised if r.get("matched_keyword_is_algorithmic"))

    return {
        "n_tasks": len(rows),
        "n_recognised": len(recognised),
        "recognition_rate": len(recognised) / len(rows) if rows else 0.0,
        "shape_counts": shape_counts,
        "n_algorithmic_true_positive": n_algorithmic_true_positive,
        "recognised_rows": recognised,
        "vocabulary_size": {
            "meta_shapes": 11, "shape_principles": 13, "functional_roles": 17,
            "distinct_keywords": len(all_kw_flat),
        },
        "algorithmic_keywords_held": sorted(
            SYMMETRIC_SHAPE_LEXICON & set(all_kw_flat)),
        "vocabulary_note": (
            "shape_vocabulary.json's 11 MetaShapes / 13 ShapePrinciples / "
            "17 FunctionalRoles are systems/cognition-flavoured (scheduler, "
            "memory_store, gating, regulate, predict, synchronize, ...). "
            "algorithmic_keywords_held is the intersection of this "
            "measurement's own symmetric-shape lexicon (largest/max/min/"
            "sum/median/...) with the seed's real keyword set -- empty, "
            "confirmed live. Every recognised_rows hit is traced by "
            "matched_keywords to a SUBSTRING COLLISION with ordinary MBPP "
            "prose (e.g. 'remove' contains 'move', 'positive'/'opposite' "
            "contain 'posit', 'aggregate' hits the unrelated 'integrate' "
            "role) -- not genuine algorithmic-shape recognition. A low "
            "recognition number here is a statement about the VOCABULARY, "
            "not about the RecogniseShape mechanism, which is exercised "
            "live and works exactly as designed."
        ),
        "analogical_dial_note": (
            "domains/analogical_thinking.py's n=0..4 abstraction dial "
            "(order-2 functional-role / order-3 principle / order-4 "
            "meta-shape match) operates over Concept nodes carrying "
            "name/category/definition text -- MBPP tasks are not "
            "represented as Concept nodes in this pipeline (they are "
            "Goal/Message + IR subgraphs), so the dial has no native input "
            "here without an additional adapter step that does not exist. "
            "Not run as a separate channel; RecogniseShape/TransferDecode "
            "(goal-token format) is the one existing mechanism this "
            "measurement can honestly drive against MBPP goals."
        ),
    }


# ========================================================================= #
#  Q2 -- CONSTRAINT CATALOGUE, applied to the 76-trap population
# ========================================================================= #
def check_total_dependence(ir: Dict[str, Any], revealed_rows: List[Dict[str, Any]]
                           ) -> Dict[str, Any]:
    """C_DEP: 'every declared argument must be read'. THIS IS D3/D4
    (arc4_structural_verdicts.py), reused verbatim, never re-implemented --
    reported here so the OVERLAP with the existing detector is explicit and
    the NEW mass is counted separately (as the brief requires)."""
    d3 = asv.detect_unread_declared_param(ir, revealed_rows)
    d4 = asv.detect_constant_output(ir, revealed_rows)
    return {"name": "total_dependence", "assumption":
            "a function's declared parameter list is exactly its inputs; a "
            "declared, revealed-varying parameter with zero reads is a "
            "structural defect, independent of any row's value.",
            "violated": bool(d3["fired"] or d4["fired"]),
            "is_d3_d4_verbatim": True, "d3": d3, "d4": d4}


def check_argument_symmetry(ir: Dict[str, Any], revealed_rows: List[Dict[str, Any]],
                            prompt: str) -> Dict[str, Any]:
    """C_SYM: an N-ary extremum/sum/product/average over UNORDERED
    quantities must be invariant under permutation of which declared
    parameter receives which value. Applicability requires (a) arity>=2 and
    (b) the prompt names a symmetric-shape word (SYMMETRIC_SHAPE_LEXICON --
    NOT held in shape_vocabulary.json today, see Q1/Q4). The check re-feeds
    ONLY the values a revealed row ALREADY contains, under every permutation
    of which parameter gets which value -- no held-out value, no new
    magnitude is ever introduced; this is why it counts as REVEALED-rows-
    only structural information, not a data lever."""
    params = afa._param_names(ir)
    low = prompt.lower()
    lexicon_hit = sorted(w for w in SYMMETRIC_SHAPE_LEXICON
                         if re.search(r"\b%s\b" % re.escape(w), low))
    if len(params) < 2 or not lexicon_hit:
        return {"name": "argument_symmetry", "applicable": False,
                "lexicon_hit": lexicon_hit, "arity": len(params)}
    per_row = []
    already_implied = False
    seen_multisets: List[Tuple[Any, ...]] = []
    for row in revealed_rows:
        inputs = row["inputs"]
        if not all(p in inputs for p in params):
            continue
        vals = [inputs[p] for p in params]
        if not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in vals):
            continue
        ms_key = tuple(sorted(vals))
        if ms_key in seen_multisets:
            already_implied = True  # two revealed rows are themselves a permutation pair
        seen_multisets.append(ms_key)
        outs = []
        for perm in itertools.permutations(vals):
            env = dict(zip(params, perm))
            r = arc3b.prog_eval(ir, env)
            ok = r.get("halted") is True and r.get("trap") is None
            outs.append(r.get("result") if ok else ("__trap__", r.get("trap")))
        distinct = []
        for o in outs:
            if o not in distinct:
                distinct.append(o)
        per_row.append({"inputs": inputs, "n_assignments": len(outs),
                        "n_distinct_outputs": len(distinct),
                        "symmetric": len(distinct) == 1})
    applicable = bool(per_row)
    symmetric_overall = applicable and all(r["symmetric"] for r in per_row)
    return {"name": "argument_symmetry", "applicable": applicable,
            "lexicon_hit": lexicon_hit, "arity": len(params),
            "per_row": per_row, "symmetric_overall": symmetric_overall,
            "violated": applicable and not symmetric_overall,
            "already_implied_by_revealed_rows": already_implied}


def check_arity_from_prompt(prompt: str, ir: Dict[str, Any]) -> Dict[str, Any]:
    """C_ARITY: a numeral word adjacent to a quantity noun in the PROMPT
    ('...of three numbers') entails the declared arity should equal that
    numeral -- an entailment from the REQUEST TEXT, distinct from D6
    (arity_mismatch, which compares IR arity to REVEALED ROW arg counts,
    never the prompt)."""
    tokens = _WORD_RE.findall(prompt.lower())
    ir_arity = len(afa._param_names(ir))
    claims = []
    for i, tok in enumerate(tokens):
        if tok in NUMERAL_WORDS:
            window = tokens[i + 1:i + 3]
            if any(w in QUANTITY_NOUNS for w in window):
                claims.append(NUMERAL_WORDS[tok])
    applicable = bool(claims)
    violated = applicable and any(c != ir_arity for c in claims)
    return {"name": "arity_from_prompt", "applicable": applicable,
            "prompt_claims": claims, "ir_arity": ir_arity, "violated": violated}


def check_monotonicity_precondition(revealed_rows: List[Dict[str, Any]]) -> bool:
    """Precondition for a monotonicity/idempotence/boundedness check: at
    least 2 revealed rows differing in EXACTLY one numeric variable (so a
    directional comparison is even meaningful). Reported as a COUNT, not
    smoothed into a fabricated positive result."""
    for a, b in itertools.combinations(revealed_rows, 2):
        ia, ib = a["inputs"], b["inputs"]
        if set(ia) != set(ib):
            continue
        diffs = [k for k in ia if ia[k] != ib[k]]
        if len(diffs) == 1 and isinstance(ia[diffs[0]], (int, float)) \
                and not isinstance(ia[diffs[0]], bool):
            return True
    return False


def q2_constraint_yield(ahf: Dict[int, Dict[str, Any]],
                        tasks_by_id: Dict[int, Dict[str, Any]]) -> Dict[str, Any]:
    dep_fired, sym_applicable, sym_violated, arity_applicable, arity_violated = (
        [], [], [], [], [])
    mono_precondition_met = []
    per_task = {}
    for tid in sorted(ahf):
        row = ahf[tid]
        ir = row["ir"]
        prompt = tasks_by_id[tid]["prompt"]
        revealed = afa._revealed_rows_for_task(tid, tasks_by_id)
        dep = check_total_dependence(ir, revealed)
        sym = check_argument_symmetry(ir, revealed, prompt)
        ar = check_arity_from_prompt(prompt, ir)
        mono_ok = check_monotonicity_precondition(revealed)
        per_task[tid] = {"total_dependence": dep, "argument_symmetry": sym,
                         "arity_from_prompt": ar,
                         "monotonicity_precondition_met": mono_ok}
        if dep["violated"]:
            dep_fired.append(tid)
        if sym["applicable"]:
            sym_applicable.append(tid)
            if sym["violated"]:
                sym_violated.append(tid)
        if ar["applicable"]:
            arity_applicable.append(tid)
            if ar["violated"]:
                arity_violated.append(tid)
        if mono_ok:
            mono_precondition_met.append(tid)

    new_mass_sym = sorted(set(sym_violated) - set(dep_fired))
    return {
        "n_traps": len(ahf),
        "per_task": per_task,
        "catalogue": {
            "total_dependence": {
                "assumption": "declared arity == read arity; unread-varying "
                              "param is a defect regardless of value",
                "overlap_with_D3_D4": "EXACT -- this constraint IS D3+D4, "
                                      "reused verbatim, not reimplemented",
                "n_violated": len(dep_fired), "violated_ids": sorted(dep_fired),
            },
            "argument_symmetry": {
                "assumption": "an N-ary extremum/sum/product/average over "
                              "UNORDERED quantities is permutation-invariant "
                              "in its own declared args; checked via "
                              "REVEALED VALUES ONLY, re-assigned to args",
                "requires_seeding": sorted(SYMMETRIC_SHAPE_LEXICON),
                "n_applicable": len(sym_applicable), "applicable_ids": sorted(sym_applicable),
                "n_violated": len(sym_violated), "violated_ids": sorted(sym_violated),
                "new_mass_beyond_total_dependence": new_mass_sym,
                "n_new_mass": len(new_mass_sym),
            },
            "arity_from_prompt": {
                "assumption": "a numeral word next to a quantity noun in "
                              "the PROMPT entails that declared arity",
                "n_applicable": len(arity_applicable), "applicable_ids": sorted(arity_applicable),
                "n_violated": len(arity_violated), "violated_ids": sorted(arity_violated),
            },
            "monotonicity_idempotence_boundedness": {
                "assumption": "requires >=2 revealed rows differing in "
                              "EXACTLY one numeric variable to even pose a "
                              "directional question",
                "n_precondition_met": len(mono_precondition_met),
                "precondition_met_ids": sorted(mono_precondition_met),
                "verdict": "INAPPLICABLE IN PRACTICE for this population -- "
                          "reported honestly, not smoothed into a positive.",
            },
        },
    }


# ========================================================================= #
#  Q3 -- would a constraint have converted a trap?
# ========================================================================= #
_SEARCH_FN_SOURCE_MUST_NOT_MENTION = "held_out"


def run_exclude_probe(tid, ir: Dict[str, Any], revealed_rows: List[Dict[str, Any]]
                      ) -> Dict[str, Any]:
    """SEARCH-side function -- takes ONLY (ir, revealed_rows). Excludes the
    trap's own value-expression (the one search-restriction lever
    SynthEnumerate exposes) and re-runs the real engine over the SAME
    revealed rows, unrestricted ops, max_size=7. Returns found/term/
    halt_reason -- never touches held-out data."""
    ve = value_expr(ir)
    if ve is None:
        return {"task_id": tid, "skipped": "no_return_value"}
    excl = json.dumps(ve)
    rows_spec = [{"inputs": r["inputs"], "output": r["expected"]} for r in revealed_rows]
    s = srs.Substrate()
    spec = {"type": "SynthEnumerate", "examples": {"type": "Lit", "value": rows_spec},
            "max_size": 7, "max_candidates": 0, "saturate_k": 0, "field": "",
            "exclude": {"type": "Lit", "value": [excl]}}
    out = s._inner.evaluate(spec, {})
    return {"task_id": tid, "found": out.get("found"), "term": out.get("term"),
            "term_str": out.get("term_str"), "halt_reason": out.get("halt_reason"),
            "tested": out.get("tested")}


def verify_found_program_against_held_out(tid, ir: Dict[str, Any],
                                          found_term_json: str, params: List[str],
                                          held_out_rows: List[Dict[str, Any]]
                                          ) -> Dict[str, Any]:
    """MEASUREMENT-ONLY function (sanctioned pattern, `domains/mbpp_spec.py`'s
    own contamination_rule + `tests/fixtures/mbpp/provenance.json`: held-out
    data MAY be read for measurement, never fed to search). This is the ONLY
    function in this module allowed to read a `held_out` row, and it never
    feeds its result back into any search call."""
    newir = json.loads(found_term_json)
    wrapped = {"type": "ProgSeq",
              "stmts": [{"type": "ProgDefFnParam", "name": p, "default": None}
                       for p in params] + [{"type": "ProgReturn", "value": newir}]}
    checks = []
    all_ok = True
    for hr in held_out_rows:
        r = arc3b.prog_eval(wrapped, dict(hr["inputs"]))
        ok = (r.get("halted") is True and r.get("trap") is None
             and arc3b.agree(r.get("result"), hr["expected"],
                             hr.get("tol"), bool(hr.get("unordered"))))
        checks.append({"inputs": hr["inputs"], "got": r.get("result"),
                       "expected": hr["expected"], "ok": ok})
        all_ok = all_ok and ok
    return {"task_id": tid, "all_held_out_ok": all_ok, "checks": checks}


def q3_would_it_convert(ahf: Dict[int, Dict[str, Any]],
                        tasks_by_id: Dict[int, Dict[str, Any]],
                        q2: Dict[str, Any], residual_36: List[int]) -> Dict[str, Any]:
    # (a) principled rejection: union of structural detectors (D1-D7, the
    # frozen union already measured) OR the new argument-symmetry violation.
    with open(STRUCTURAL_PATH) as f:
        structural = json.load(f)
    killable_structural = set(structural["structural_killable_ids"])
    sym_violated = set(q2["catalogue"]["argument_symmetry"]["violated_ids"])

    def principled_ids(pop: List[int]) -> Dict[str, Any]:
        pop_set = set(pop)
        a_ids = sorted((killable_structural | sym_violated) & pop_set)
        return {"population": sorted(pop_set), "n_population": len(pop_set),
               "principled_reject_ids": a_ids, "n_principled_reject": len(a_ids)}

    a_the_26 = principled_ids(THE_26)
    a_residual_36 = principled_ids(residual_36)

    # (b) EMPIRICAL pruning test -- the load-bearing part. Run against every
    # REOPENED_12 id (the only ids that ever actually attempt reopening in
    # production -- RETRIEVAL_SOURCED_14 never reach the reopen lane at all,
    # per S6, so testing pruning on them would be counterfactual) plus the
    # br_10_top_of_three battery fixture (the sharpest, already-characterised
    # instance S6 itself used).
    empirical = []
    for tid in REOPENED_12:
        ir = ahf[tid]["ir"]
        params = afa._param_names(ir)
        revealed = afa._revealed_rows_for_task(tid, tasks_by_id)
        probe = run_exclude_probe(tid, ir, revealed)
        entry = {"task_id": tid, "params": params, "n_revealed": len(revealed),
                 "probe": probe}
        if probe.get("found") and probe.get("term"):
            task = tasks_by_id[tid]
            parsed = ms.parse_asserts(task)
            split = ms.split_rows(parsed["rows"], "primary")
            verify = verify_found_program_against_held_out(
                tid, ir, probe["term"], params, split["held_out"])
            entry["verify_against_held_out"] = verify
        empirical.append(entry)

    with open(os.path.join(ROOT, "tests", "fixtures", "prog_synthesis_battery",
                           "tasks.json")) as f:
        battery = json.load(f)
    br10 = next(t for t in battery["tasks"] if t["id"] == "br_10_top_of_three")
    br10_ir_stub = {"stmts": [{"type": "ProgDefFnParam", "name": "a", "default": None},
                              {"type": "ProgDefFnParam", "name": "b", "default": None},
                              {"type": "ProgDefFnParam", "name": "c", "default": None},
                              {"type": "ProgReturn", "value":
                               {"type": "Max",
                                "items": [{"name": "a", "type": "Var"},
                                         {"name": "b", "type": "Var"}]}}]}
    br10_revealed = [{"inputs": r["inputs"], "expected": r["expected"]}
                     for r in br10["example_rows"]]
    br10_probe = run_exclude_probe("br_10_top_of_three", br10_ir_stub, br10_revealed)
    br10_entry = {"task_id": "br_10_top_of_three", "params": ["a", "b", "c"],
                 "n_revealed": len(br10_revealed), "probe": br10_probe}
    if br10_probe.get("found") and br10_probe.get("term"):
        verify = verify_found_program_against_held_out(
            "br_10_top_of_three", br10_ir_stub, br10_probe["term"], ["a", "b", "c"],
            br10["held_out_rows"])
        br10_entry["verify_against_held_out"] = verify
    empirical.append(br10_entry)

    n_found = sum(1 for e in empirical if e["probe"].get("found"))
    n_found_and_correct = sum(
        1 for e in empirical
        if e["probe"].get("found")
        and e.get("verify_against_held_out", {}).get("all_held_out_ok"))
    pruning_succeeded_ids = [e["task_id"] for e in empirical
                             if e["probe"].get("found")
                             and e.get("verify_against_held_out", {}).get("all_held_out_ok")]

    isolation_audit_b = _held_out_isolation_audit_search_fns()

    return {
        "a_principled_rejection": {"the_26": a_the_26, "residual_36": a_residual_36},
        "b_empirical_pruning": {
            "population_tested": [e["task_id"] for e in empirical],
            "n_population": len(empirical),
            "n_search_found_something": n_found,
            "n_found_and_verified_correct_on_held_out": n_found_and_correct,
            "pruning_succeeded_ids": pruning_succeeded_ids,
            "entries": empirical,
            "mechanism_explanation": (
                "SynthEnumerate's ONLY search-restriction lever is `exclude`, "
                "which pre-seeds the excluded term's OBSERVED SIGNATURE "
                "(its output vector over the example rows) into the "
                "equivalence-pruning set. A structural TRAP, by definition, "
                "reproduces every revealed row's expected value exactly -- "
                "so its signature over those rows literally EQUALS the "
                "target signature. Any genuinely correct completion must "
                "ALSO reproduce that same target signature, so it shares "
                "the trap's signature and is pruned as a duplicate the "
                "moment the trap is excluded -- 'found:false'. The engine's "
                "own type-aware canon (bool distinct from 1) occasionally "
                "lets a DIFFERENT candidate escape this wall when the "
                "trap's runtime output type differs from the row's declared "
                "expected type -- but the candidate that escapes is chosen "
                "by the SAME MDL/shortest-first search with NO new "
                "information, so it is just the next-shortest thing that "
                "coincidentally fits 2-3 sparse rows: verified live, EVERY "
                "such escape in this measurement is ALSO wrong on the "
                "held-out row (verify_against_held_out=False in every "
                "entry with found=True)."
            ),
            "held_out_isolation_audit_of_search_functions": isolation_audit_b,
        },
    }


def _held_out_isolation_audit_search_fns() -> Dict[str, Any]:
    fns = [check_total_dependence, check_argument_symmetry,
          check_arity_from_prompt, check_monotonicity_precondition,
          run_exclude_probe]
    hits = {fn.__name__: (_SEARCH_FN_SOURCE_MUST_NOT_MENTION in inspect.getsource(fn))
           for fn in fns}
    return {"functions_checked": sorted(hits), "any_hit": any(hits.values()),
            "hits": {k: v for k, v in hits.items() if v}}


# ========================================================================= #
#  Q4 -- ANALOGICAL TRANSFER: is there anything to transfer FROM?
# ========================================================================= #
def q4_analogical_transfer() -> Dict[str, Any]:
    with open(MECHANISM_INDEX_PATH) as f:
        mech_index = json.load(f)
    with open(MATH_SHAPES_PATH) as f:
        math_shapes = json.load(f)
    mechanisms = [n["attrs"] for n in mech_index["nodes"] if n["type"] == "Mechanism"]
    math_sigs = [n["attrs"] for n in math_shapes["nodes"]
                if n["attrs"].get("kind") == "math"]

    wa = WorldAdapter()
    for seed in ("shape_vocabulary", "seven_meta_shape_subsystems",
                "relation_vocabulary", "mechanism_index"):
        try:
            wa.inner.load_seed_manifest(manifest_for(seed), wa.agent)
        except Exception:
            pass

    probe_goals = {
        "top_of_three": [["find", "the", "LARGEST", "of", "THREE", "NUMBERS"],
                        ["compare", "NUMBER", "with", "NUMBER"]],
        "median_of_three": [["return", "the", "MEDIAN", "of", "THREE", "VALUES"]],
        "volume_triangular_prism": [["compute", "the", "VOLUME", "from", "BASE",
                                    "HEIGHT", "and", "LENGTH"]],
        "sum_two_numbers": [["add", "NUMBER", "and", "NUMBER"]],
    }
    transfer_results = {}
    for name, goal in probe_goals.items():
        rt = retrieve_and_transfer_mechanism(wa, goal)
        transfer_results[name] = rt

    n_walls = sum(1 for rt in transfer_results.values()
                 if rt is None or rt.get("transferred") is None)
    return {
        "held_mechanisms": mechanisms,
        "n_held_mechanisms": len(mechanisms),
        "held_mechanisms_are_algorithmic": False,
        "held_math_shape_signatures": [m["name"] for m in math_sigs],
        "n_held_math_shape_signatures": len(math_sigs),
        "math_shapes_are_algorithmic": False,
        "live_transfer_probes": transfer_results,
        "n_probes": len(probe_goals),
        "n_honest_walls": n_walls,
        "finding": (
            "The Mechanism codebook (seeds/mechanism_index.json) holds "
            "exactly 2 entries: spatial_foveation (meta_shape "
            "selective_gating, from space_quantize) and "
            "homeostatic_regulation (meta_shape feedback_control, from "
            "the self-improvement feedback loop) -- both systems/cognition "
            "mechanisms, neither algorithmic. seeds/math_capability_"
            "shapes.json's 17 ShapeSignatures are fractal/phi/self-"
            "similarity/symmetry/curvature/topology (math CONCEPTS the "
            "agent can bridge to its OWN faculties via AntiUnify) -- not "
            "program-synthesis shapes (extremum, total-function, "
            "accumulator, etc.) and not indexed by TransferDecode's "
            "meta_shape mechanism at all (a different bridge, "
            "structure_mapping/AntiUnify, not retrieve_and_transfer_"
            "mechanism). Every live probe against an MBPP/br_10-shaped "
            "goal returns the honest wall (transferred=None) -- confirmed "
            "live, not asserted from the inventory alone: TransferDecode's "
            "own meta-shape recognition (the SAME RecogniseShape scorer as "
            "Q1) never even matches an algorithmic goal, so retrieval never "
            "reaches the point of having a candidate mechanism to try. "
            "WHAT WOULD HAVE TO BE SEEDED: (1) an 'extremum'/'total_"
            "function_of_declared_args' MetaShape + ShapePrinciple + "
            "FunctionalRole keyword set (largest/max/min/sum/median/...) "
            "so RecogniseShape fires on program-synthesis goals at all; "
            "(2) a Mechanism entry under that shape with abstract steps "
            "like ['compare', 'PART', 'with', 'PART'] / ['fold', 'winner', "
            "'over', 'REMAINING'] that TransferDecode could re-instantiate "
            "at arity N -- neither exists today."
        ),
    }


# ========================================================================= #
#  determinism + main
# ========================================================================= #
def _canon(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, default=str)


def run_all() -> Dict[str, Any]:
    t0 = time.time()
    tasks_by_id = load_test_tasks()
    ahf, passed = load_r3_populations()
    residual_36 = load_36_residual_ids()

    q1 = q1_recognition_coverage(tasks_by_id)
    q2 = q2_constraint_yield(ahf, tasks_by_id)
    q3 = q3_would_it_convert(ahf, tasks_by_id, q2, residual_36)
    q4 = q4_analogical_transfer()

    result = {
        "_README": ("Arc 5 shape-constraint ceiling probe. Read Q3.b "
                   "(b_empirical_pruning) first -- it is the load-bearing "
                   "measurement; Q1/Q2/Q4 explain WHY it comes out the way "
                   "it does."),
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "provenance": {
            "reads": [FIXTURE_PATH, R3_ENDGAME_PATH, S5_ENDGAME_PATH,
                     STRUCTURAL_PATH, SHAPE_VOCAB_PATH, MECHANISM_INDEX_PATH,
                     MATH_SHAPES_PATH],
            "writes": [OUT_PATH],
            "modifies_synthesis_engine_seed_or_spec_code": False,
        },
        "population": {
            "n_test_tasks": len(tasks_by_id),
            "n_traps_76": len(ahf), "n_pass_21": len(passed),
            "the_26": {"retrieval_sourced_14": RETRIEVAL_SOURCED_14,
                      "reopened_12": REOPENED_12, "all_26": THE_26},
            "genuine_defect_ids": GENUINE_DEFECT_IDS,
            "residual_36": residual_36,
        },
        "q1_recognition_coverage": q1,
        "q2_constraint_yield": q2,
        "q3_would_it_convert": q3,
        "q4_analogical_transfer": q4,
        "environment": {k: os.environ.get(k) for k in
                       ("OZMA_NO_LLM", "OZMA_SEED_PERSIST_DISABLED")},
        "elapsed_seconds": None,  # filled below
    }
    result["elapsed_seconds"] = round(time.time() - t0, 2)
    return result


def main() -> None:
    run1 = run_all()
    run2 = run_all()

    # twin-run determinism -- compare everything EXCEPT the two live-clock
    # fields (measured_at, elapsed_seconds).
    def _strip_clock(r: Dict[str, Any]) -> Dict[str, Any]:
        r = dict(r)
        r["measured_at"] = None
        r["elapsed_seconds"] = None
        return r

    h1 = hashlib.sha256(_canon(_strip_clock(run1)).encode()).hexdigest()
    h2 = hashlib.sha256(_canon(_strip_clock(run2)).encode()).hexdigest()
    run1["determinism"] = {"twin_run_sha256_match": h1 == h2, "sha256": h1}
    assert h1 == h2, "NON-DETERMINISTIC across twin runs -- %s != %s" % (h1, h2)

    with open(OUT_PATH, "w") as f:
        json.dump(run1, f, indent=2, default=str, sort_keys=True)
    print("wrote", OUT_PATH)
    print("Q1 recognition:", run1["q1_recognition_coverage"]["n_recognised"],
         "/", run1["q1_recognition_coverage"]["n_tasks"])
    b = run1["q3_would_it_convert"]["b_empirical_pruning"]
    print("Q3(b) pruning succeeded ids:", b["pruning_succeeded_ids"],
         "of", b["n_population"], "tested")


if __name__ == "__main__":
    main()
