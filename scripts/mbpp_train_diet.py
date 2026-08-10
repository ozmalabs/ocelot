#!/usr/bin/env python
"""mbpp_train_diet — Arc 2 Q3: THE PAIRED DIET.

PROGRAM_SYNTHESIS_ARC2_PLAN.md Q3 — the arc's central phase, and the
LLM-analog training step arc 1 never had data for: grow the proposer's
three learned layers (chunks, triggers, bigrams) from the MBPP **TRAIN**
split (task_id >= 601, 120 tasks) *with their prompts*, so triggers are
finally earned from co-occurring request words instead of derived from
code alone (P7-C's own honesty clause / 2/15-cueable finding,
`PROGRAM_SYNTHESIS_P7C.md` sec2.3/sec6).

CONTAMINATION (absolute — the arc's credibility). This script reads ONLY
`tests/fixtures/mbpp/sanitized-mbpp.json` tasks with `task_id >= 601`
(the train split). It never reads a test-split (`task_id` in [11,510])
prompt or code field in ANY learning path — `tests/
test_mbpp_contamination_migrated.py` (the existing list-gate) and this
phase's own equivalent scan (`tests/test_mbpp_diet_migrated.py`) both
re-verify this from the shipped artifacts, not from this script's own
bookkeeping.

REUSE, NOT FORK (CLAUDE.md discipline + the task brief's own instruction):
  - chunk extraction is the UNCHANGED P7-C fixed walk
    (`domains.prog_chunk_growth.chunk_candidates` / `chunk_record` /
    `ground_template_for` / `cue_exclusion_reason`) — this script supplies
    a different TASK POPULATION (MBPP train instead of the P2/P3 repo
    corpus) and a different TRIGGER SOURCE (paired prompts instead of code
    words), never a different extraction walk;
  - support-threshold + AntiUnify dedup + the family-collapse adoption
    rule are the UNCHANGED `scripts.prog_chunk_mine` functions
    (`support_curve` / `apply_threshold_rule` / `dedup` / `family_counts`
    / `median` / `modal_lits` / `Engine`), imported, never reimplemented;
    ONE registered addition (a corpus-size fallback, documented at its own
    call site) for the 1%-quantile rule when the train corpus's recurring-
    type population is too small for the ceil(1%) target to mean anything;
  - the entry-function resolution (`resolve_entry`) is the UNCHANGED
    Q0-B histogram function, imported;
  - bigram grain is the SAME "head" projection
    `domains.prog_synthesis.ensure_construction_bigrams` boards at
    (`prog_ir_signature.statement_signature(s)[0][1]` — the raw statement
    type name) and the SAME add-1-smoothed `trans_logp` formula
    (`ln((c+1)/(prev_total+|V|))`), computed directly from train IR
    top-level sequences (no sd-loop merge needed at this grain: P4-B's own
    "head" projection IS this raw statement-type label, so this script
    mines it directly rather than re-running the corpus-scale merge loop);
  - request-text normalization is `domains.mbpp_spec.request_facts`
    (Q2's shared spec layer) — trigger/affinity tokens are scored from its
    `request_body` (the verb-frame-stripped residual), never the raw
    prompt string with its "write a function to" boilerplate.

Run:
  PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 \
      OZMA_SEED_PERSIST_DISABLED=1 python scripts/mbpp_train_diet.py

Env knobs (recorded in the artifact — no silent caps):
  MTD_ONCE=1   skip the second (determinism-evidence) run
"""
from __future__ import annotations

import hashlib
import json
import math
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

from domains import prog_ir_emit  # noqa: E402
from domains import prog_ir_signature as pis  # noqa: E402
from domains import prog_chunk_growth as pcg  # noqa: E402
from domains import mbpp_spec  # noqa: E402
from domains.code_writing import _STOPWORDS  # noqa: E402
from mbpp_blocker_histogram import resolve_entry, task_split  # noqa: E402
import prog_chunk_mine as ckm  # noqa: E402  (reused: Engine, dedup, threshold rule)

FIXTURE_PATH = os.path.join(ROOT, "tests", "fixtures", "mbpp", "sanitized-mbpp.json")
STARTER_CODEBOOK_PATH = os.path.join(ROOT, "seeds", "code_write_constructions.json")
OUT_RESULTS = os.path.join(ROOT, "results", "mbpp_train_diet.json")
OUT_SEED = os.path.join(ROOT, "seeds", "mbpp_train_diet.json")

TOP_K_TRIGGERS = 5      # kept trigger tokens per chunk
TOP_K_AFFINITY = 5      # kept cue tokens per starter-construction affinity row
N_HOLDOUT = 20          # leave-N-out probe holdout size (of the 120 train tasks)

_WORD_RE = re.compile(r"[a-z']+")


def log(*a):
    print("[mbpp-diet]", *a, flush=True)


# --------------------------------------------------------------------------- #
#  Load — TRAIN split only (task_id >= 601). Never reads a test-split row.
# --------------------------------------------------------------------------- #
def load_train_tasks() -> List[Dict[str, Any]]:
    with open(FIXTURE_PATH) as f:
        tasks = json.load(f)
    train = [t for t in tasks if task_split(t["task_id"]) == "train"]
    train.sort(key=lambda t: t["task_id"])
    return train


def tokenize(text: str) -> List[str]:
    """Mechanical: lowercase word tokens, stopwords dropped — the SAME
    `_content_tokens` prep the write codebook already applies, minus the
    UPPERCASE step (kept lowercase here for arithmetic scoring; converted
    to UPPERCASE only at the point a token becomes a `trigger_tokens`
    entry, to match the goal-token case convention `ps_propose` matches
    against)."""
    return [w for w in _WORD_RE.findall(text.lower()) if w and w not in _STOPWORDS]


# --------------------------------------------------------------------------- #
#  Pass 1 — emit + entry resolution over a given task-id population.
# --------------------------------------------------------------------------- #
def emit_pass(tasks: List[Dict[str, Any]]) -> Tuple[Dict[int, Dict[str, Any]],
                                                     Dict[int, str], List[Dict[str, Any]]]:
    """-> (task_ir: {task_id: ir}, task_prompt: {task_id: prompt}, rows).
    A task's `code` contributes chunks/bigrams ONLY when `emit_prog_ir`
    accepts the WHOLE function (`ok: True`) — the arc-1 miner's own scope
    (`scripts/prog_chunk_mine.py::extract`: `if not r.get("ok"): ...
    continue`). CHECKED, per the task brief's instruction to verify
    whether partial/residual sub-spans are supported: `emit_prog_ir` is an
    all-or-nothing function-level translator (no statement-level partial
    IR mode exists in `domains/prog_ir_emit.py`), and the arc-1 miner never
    attempts one either — a function with ANY blocker contributes ZERO
    chunks/bigram statements here, exactly as it did for the P2/P3 corpus.
    This is a real, honestly-reported ceiling on this phase's mined mass,
    not a Q3 defect."""
    task_ir: Dict[int, Dict[str, Any]] = {}
    task_prompt: Dict[int, str] = {}
    rows: List[Dict[str, Any]] = []
    for t in tasks:
        tid = t["task_id"]
        task_prompt[tid] = t["prompt"]
        entry_name, _tree, _defs, err = resolve_entry(t["code"], t["test_list"])
        if entry_name is None:
            rows.append({"task_id": tid, "ok": False,
                         "reason": "entry_resolve:%s" % err})
            continue
        r = prog_ir_emit.emit_prog_ir(t["code"], name=entry_name)
        if not r.get("ok"):
            rows.append({"task_id": tid, "ok": False, "reason": "emit_blocked",
                         "entry": entry_name, "blockers": r.get("blockers")})
            continue
        task_ir[tid] = r["ir"]
        rows.append({"task_id": tid, "ok": True, "entry": entry_name})
    return task_ir, task_prompt, rows


# --------------------------------------------------------------------------- #
#  Chunk mining — same extraction walk, threshold, dedup as P7-C; TRIGGERS
#  come from paired prompts (this phase's whole point), not code words.
# --------------------------------------------------------------------------- #
def mine_chunk_types(task_ir: Dict[int, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    types: Dict[str, Dict[str, Any]] = {}
    for tid in sorted(task_ir):
        for rec in pcg.chunk_candidates(task_ir[tid]):
            k = rec["chunk_key"]
            row = types.get(k)
            if row is None:
                row = {"rec": rec, "support": 0, "task_ids": set(), "lits": {}}
                types[k] = row
            row["support"] += 1
            row["task_ids"].add(tid)
            lit_key = json.dumps(rec["lit_values"], sort_keys=True, separators=(",", ":"))
            row["lits"][lit_key] = row["lits"].get(lit_key, 0) + 1
    return types


def apply_threshold_with_small_corpus_fallback(curve: List[Dict[str, int]]) -> Dict[str, Any]:
    """The UNCHANGED P7-C registered rule (`ckm.apply_threshold_rule`), plus
    ONE registered addition for this much smaller corpus (120 programs vs
    P7-C's 4099): if the recurring-type population itself is < 8, the
    1%-quantile target (ceil(0.01*recurring)) is too small a number to
    mean anything and the existing floor (lower s* until kept>=8) cannot
    fire either (there is no s with kept>=8 to find) — the task brief's own
    registered fallback for this case: s* = 2 (keep EVERY recurring type),
    reported as `corpus_too_small_fallback: True`, never silently."""
    thr = ckm.apply_threshold_rule(curve)
    if thr["recurring_types"] < 8:
        recurring_curve_at_2 = sum(r["n_types"] for r in curve if r["support"] >= 2)
        thr = dict(thr, s_star=2, kept_at_s_star=recurring_curve_at_2,
                   corpus_too_small_fallback=True)
    else:
        thr["corpus_too_small_fallback"] = False
    return thr


def mine_chunks(task_ir: Dict[int, Dict[str, Any]], task_prompt: Dict[int, str],
                idf_universe_prompts: Dict[int, str]) -> Dict[str, Any]:
    """Mine the idiom-grain chunk layer over `task_ir`'s population, with
    trigger tokens scored against `idf_universe_prompts` (the population
    global document frequency is computed over — the FULL mining scope for
    the shipped diet, or the mine-only 100 for the leave-N-out probe, never
    the probe's held-out 20)."""
    eng = ckm.Engine()
    types = mine_chunk_types(task_ir)
    curve = ckm.support_curve(types)
    thr = apply_threshold_with_small_corpus_fallback(curve)
    s_star = thr["s_star"]

    kept = []
    for k in sorted(types):
        row = types[k]
        if row["support"] >= s_star:
            kept.append({"chunk_key": k, "labels": row["rec"]["labels"],
                         "rels": row["rec"]["rels"], "support": row["support"],
                         "rec": row["rec"], "lits": row["lits"]})
    kept.sort(key=lambda r: (-r["support"], r["chunk_key"]))

    fam_pre = ckm.family_counts(kept)
    surv23, joins23 = ckm.dedup(kept, eng, num=2, den=3)
    surv56, joins56 = ckm.dedup(kept, eng, num=5, den=6)
    fam23 = ckm.family_counts(surv23)
    multi = [f for f, n in fam_pre.items() if n >= 3]
    med23 = ckm.median([fam23.get(f, 0) for f in multi]) if multi else None
    adopted = "5/6" if (multi and med23 == 1) else "2/3"
    survivors = surv23 if adopted == "2/3" else surv56

    n_train_idf = len(idf_universe_prompts)
    global_df = _doc_freq(idf_universe_prompts)

    chunks = []
    for idx, surv in enumerate(survivors):
        task_ids = set(types[surv["chunk_key"]]["task_ids"])
        for mk in surv["merged_keys"]:
            task_ids |= types[mk]["task_ids"]
        rec = surv["rec"]
        fills = ckm.modal_lits(surv["lits"])
        tmpl = pcg.ground_template_for(rec, fills)
        name = pcg.mbpp_chunk_entry_name(eng.native, rec["labels"][0], rec["n_stmts"], idx)
        scored = _score_tokens(task_ids, task_prompt, global_df, n_train_idf)
        cue_excluded = rec["cue_excluded"]
        top = scored[:TOP_K_TRIGGERS]
        trigger_tokens = [r["token"].upper() for r in top if r["score"] > 0] \
            if cue_excluded is None else []
        chunks.append({
            "name": name,
            "chunk_key": surv["chunk_key"],
            "labels": list(surv["labels"]),
            "n_stmts": rec["n_stmts"],
            "support": int(surv["support"]),
            "args": list(rec["args"]),
            "trigger_tokens": trigger_tokens,
            "derived_prompt_tokens": scored[:TOP_K_TRIGGERS * 2],
            "cue_excluded": cue_excluded,
            "slot_fills": fills,
            "chunk_rels": surv["chunk_rels"],
            "merged_keys": surv["merged_keys"],
            "ground_template": tmpl,
            "source_task_ids": sorted(task_ids),
            "provenance": "mbpp_train_chunk",
        })

    return {
        "support_curve": curve,
        "threshold": thr,
        "dedup": {"criterion_23": {"join_events": joins23, "survivors": len(surv23)},
                  "criterion_56": {"join_events": joins56, "survivors": len(surv56)},
                  "families_pre": fam_pre, "multi_member_families": len(multi),
                  "median_post_23_multi": med23, "adopted": adopted},
        "totals": {
            "candidate_instances": sum(r["support"] for r in types.values()),
            "distinct_chunk_types": len(types),
            "kept_pre_dedup": len(kept),
            "kept_final": len(chunks),
            "cueable": sum(1 for c in chunks if c["cue_excluded"] is None),
            "with_nonzero_trigger": sum(1 for c in chunks if c["trigger_tokens"]),
        },
        "chunks": chunks,
    }


def _doc_freq(prompts: Dict[int, str]) -> Dict[str, int]:
    """Global document frequency: how many prompts (in the given
    population) contain each token at least once — the IDF denominator's
    numerator source, over TRAIN prompts only, never the wider vocabulary
    lists elsewhere in the repo (contamination-safe by construction: this
    dict's keys are only ever words that occur in a TRAIN prompt)."""
    df: Dict[str, int] = {}
    for tid in sorted(prompts):
        body = mbpp_spec.request_facts(prompts[tid])["request_body"]
        for w in set(tokenize(body)):
            df[w] = df.get(w, 0) + 1
    return df


def _score_tokens(task_ids: set, task_prompt: Dict[int, str],
                  global_df: Dict[str, int], n_universe: int) -> List[Dict[str, Any]]:
    """tf-idf-style ratio (arithmetic, not NLP): for each token co-occurring
    with this chunk's task set, score = (fraction of the chunk's OWN tasks
    whose prompt contains the token) * ln(N_universe / global_df[token]).
    global_df is looked up over the IDF universe (may be a strict SUPERSET
    of `task_ids` when scoring the leave-N-out probe's 100-task mine set);
    a token with zero universe occurrences (impossible by construction
    when the universe includes every chunk task) is skipped."""
    local_df: Dict[str, int] = {}
    for tid in sorted(task_ids):
        body = mbpp_spec.request_facts(task_prompt[tid])["request_body"]
        for w in set(tokenize(body)):
            local_df[w] = local_df.get(w, 0) + 1
    n_chunk = len(task_ids)
    scored = []
    for tok, ldf in local_df.items():
        gdf = global_df.get(tok)
        if not gdf:
            continue
        freq_given_chunk = ldf / n_chunk
        idf = math.log(n_universe / gdf)
        scored.append({"token": tok, "local_task_count": ldf,
                       "chunk_task_count": n_chunk, "global_task_count": gdf,
                       "score": round(freq_given_chunk * idf, 6)})
    scored.sort(key=lambda r: (-r["score"], r["token"]))
    return scored


# --------------------------------------------------------------------------- #
#  Bigrams — head grain (raw statement-type labels), the SAME add-1
#  smoothing formula `ensure_construction_bigrams` boards with.
# --------------------------------------------------------------------------- #
def mine_bigrams(task_ir: Dict[int, Dict[str, Any]]) -> Dict[str, Any]:
    counts: Dict[Tuple[str, str], int] = {}
    task_ids_of: Dict[Tuple[str, str], set] = {}
    for tid in sorted(task_ir):
        stmts = pis.function_statements(task_ir[tid])
        labels = [str(pis.statement_signature(s)[0][1]) for s in stmts]
        seq = ["<s>"] + labels + ["</s>"]
        for i in range(len(seq) - 1):
            k = (seq[i], seq[i + 1])
            counts[k] = counts.get(k, 0) + 1
            task_ids_of.setdefault(k, set()).add(tid)

    vocab = {n for (_, n) in counts} | {p for (p, _) in counts if p != "<s>"}
    v = len(vocab)
    prev_tot: Dict[str, int] = {}
    for (p, _n), c in counts.items():
        prev_tot[p] = prev_tot.get(p, 0) + c

    rows = []
    for (p, n) in sorted(counts):
        c = counts[(p, n)]
        rows.append({
            "prev": p, "next": n, "count": int(c),
            "prev_total": int(prev_tot[p]),
            "trans_logp": math.log((c + 1) / (prev_tot[p] + v)),
            "grain": "head", "vocab_size": int(v),
            "source": "mbpp_train_diet.json", "provenance": "mbpp_train",
            "source_task_ids": sorted(task_ids_of[(p, n)]),
        })
    return {"vocab_size": v, "n_functions": len(task_ir), "bigrams": rows}


# --------------------------------------------------------------------------- #
#  Starter-shape affinity — does a train prompt CUE an existing starter
#  construction (max_of_two, sum_of_two, ...)? Structural match: a train
#  task whose ENTIRE body is `return <expr>` and whose role/slot-abstracted
#  `<expr>` is IDENTICAL (shape, not names/literals) to a starter's own
#  `ground_template.term` — the SAME abstraction rule the chunk grain uses,
#  applied one level down (an expression, not a statement window).
# --------------------------------------------------------------------------- #
def _load_starter_shapes() -> List[Dict[str, Any]]:
    with open(STARTER_CODEBOOK_PATH) as f:
        d = json.load(f)
    out = []
    for n in d.get("nodes", []):
        at = n.get("attrs", {})
        if at.get("kind") != "code_write_construction":
            continue
        tmpl = json.loads(at["ground_template"])
        term = tmpl.get("term")
        if term is None:
            continue
        abstract, _lits = pcg.abstract_expr(term)
        key = json.dumps(abstract, sort_keys=True, separators=(",", ":"))
        out.append({"name": at["name"], "key": key})
    return out


def mine_starter_affinity(task_ir: Dict[int, Dict[str, Any]],
                          task_prompt: Dict[int, str],
                          idf_universe_prompts: Dict[int, str]) -> Dict[str, Any]:
    starters = _load_starter_shapes()
    by_key: Dict[str, str] = {}
    for s in starters:
        by_key.setdefault(s["key"], s["name"])   # first-name-wins on a key collision

    matches: Dict[str, set] = {}
    for tid in sorted(task_ir):
        ir = task_ir[tid]
        body = pis.function_statements(ir)
        if len(body) != 1 or str(body[0].get("type")) != "ProgReturn":
            continue
        term = body[0].get("value")
        abstract, _lits = pcg.abstract_expr(term)
        key = json.dumps(abstract, sort_keys=True, separators=(",", ":"))
        name = by_key.get(key)
        if name is not None:
            matches.setdefault(name, set()).add(tid)

    global_df = _doc_freq(idf_universe_prompts)
    n_universe = len(idf_universe_prompts)
    rows = []
    for name in sorted(matches):
        task_ids = matches[name]
        scored = _score_tokens(task_ids, task_prompt, global_df, n_universe)
        for r in scored[:TOP_K_AFFINITY]:
            rows.append({"construction": name, "token": r["token"].upper(),
                         "local_task_count": r["local_task_count"],
                         "matched_task_count": len(task_ids),
                         "global_task_count": r["global_task_count"],
                         "score": r["score"],
                         "source_task_ids": sorted(task_ids)})
    return {"starters_checked": len(starters), "starters_matched": len(matches),
           "matched_construction_names": sorted(matches),
           "affinity_rows": rows}


# --------------------------------------------------------------------------- #
#  One full diet mine over an arbitrary task population (parameterized so
#  the SAME code mines the full 120 AND the leave-N-out probe's 100).
# --------------------------------------------------------------------------- #
def mine_diet(tasks: List[Dict[str, Any]], *,
             idf_universe: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    idf_tasks = idf_universe if idf_universe is not None else tasks
    task_ir, task_prompt, emit_rows = emit_pass(tasks)
    idf_task_ir, idf_prompt, _idf_rows = (
        (task_ir, task_prompt, emit_rows) if idf_universe is None
        else emit_pass(idf_tasks))
    chunks = mine_chunks(task_ir, task_prompt, idf_prompt)
    bigrams = mine_bigrams(task_ir)
    affinity = mine_starter_affinity(task_ir, task_prompt, idf_prompt)
    n_ok = sum(1 for r in emit_rows if r["ok"])
    return {
        "n_tasks": len(tasks),
        "n_emit_ok": n_ok,
        "emit_rate": round(n_ok / len(tasks), 4) if tasks else 0.0,
        "emit_rows": emit_rows,
        "chunks": chunks,
        "bigrams": bigrams,
        "affinity": affinity,
    }


# --------------------------------------------------------------------------- #
#  Seed-manifest construction (node-list, no rules) — installable via
#  `native.load_seed_manifest` (verified generic-node-type support).
# --------------------------------------------------------------------------- #
def build_seed_manifest(diet: Dict[str, Any]) -> Dict[str, Any]:
    nodes = []
    lid = 1
    for row in diet["chunks"]["chunks"]:
        nodes.append({
            "local_id": lid, "type": "ShapeSignature",
            "attrs": {
                "name": row["name"], "kind": "code_write_construction",
                "provenance": "mbpp_train_chunk",
                "chunk_key": row["chunk_key"],
                "chunk_rels": row["chunk_rels"],
                "signature": json.dumps([[t] for t in row["trigger_tokens"]]),
                "trigger_tokens": list(row["trigger_tokens"]),
                "ground_template": json.dumps(row["ground_template"]),
                "spine": 1.0,
                "support": int(row["support"]),
                "source": "mbpp_train_diet.json",
                "source_task_ids": list(row["source_task_ids"]),
            },
        })
        lid += 1
    for row in diet["bigrams"]["bigrams"]:
        nodes.append({
            "local_id": lid, "type": "ConstructionBigram",
            "attrs": dict(row),
        })
        lid += 1
    for i, row in enumerate(diet["affinity"]["affinity_rows"]):
        nodes.append({
            "local_id": lid, "type": "ConstructionAffinity",
            "attrs": {
                "construction": row["construction"], "cue_token": row["token"],
                "local_task_count": row["local_task_count"],
                "matched_task_count": row["matched_task_count"],
                "global_task_count": row["global_task_count"],
                "score": row["score"],
                "source": "mbpp_train_diet.json",
                "source_task_ids": list(row["source_task_ids"]),
            },
        })
        lid += 1
    return {
        "id": "mbpp_train_diet",
        "version": "1.0.0",
        "depends_on": [],
        "description": (
            "Arc 2 Q3: the PAIRED DIET -- chunks + prompt-earned triggers "
            "+ head-grain construction bigrams + starter-shape cue "
            "affinity, mined EXCLUSIVELY from the 120 MBPP TRAIN-split "
            "tasks (task_id>=601) with their prompts. Additive to the "
            "arc-1 corpus-mined chunk/bigram seeds (distinct provenance: "
            "'mbpp_train_chunk' / 'mbpp_train' vs 'chunk_mined' / the "
            "P3-corpus source) -- installing this seed never removes or "
            "rewrites the arc-1 population. Every node carries "
            "source_task_ids (all >=601) for the contamination list-gate. "
            "Built by scripts/mbpp_train_diet.py; see "
            "PROGRAM_SYNTHESIS_ARC2_Q3_NOTES.md."),
        "microtheory": {
            "name": "mbpp_train_diet",
            "description": ("The MBPP-train-mined proposer diet: idiom "
                            "chunks with prompt-co-occurrence triggers, "
                            "construction bigrams, and starter-shape "
                            "cue affinities."),
        },
        "nodes": nodes,
        "edges": [],
        "productions": [],
    }


# --------------------------------------------------------------------------- #
#  Leave-N-out transfer probe (measurement only — NOT the HQ3 verdict).
#  PROTECTED CONTROL (the codebase's standing discipline, H6/H7c precedent):
#  "spine_labels non-empty" is NOT by itself evidence of diet usage — the
#  arc-1 P3-corpus bigrams are ALWAYS present (`ensure_program_synthesis`
#  boards them unconditionally), so a lattice decode can produce a
#  non-empty spine from THAT population alone. Every holdout task is run
#  TWICE — CONTROL (starter codebook + arc-1 bigrams only) and DIET (+ the
#  mine-set-only manifest) — on fresh, independent substrates; "used" is
#  claimed only when the outcome could not have come from CONTROL alone.
# --------------------------------------------------------------------------- #
def _run_probe_arm(t: Dict[str, Any], examples, manifest: Optional[Dict[str, Any]]):
    from domains import prog_synthesis as psy
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    psy.ensure_program_synthesis(s, s._inner, ag)
    installed_nodes = 0
    if manifest is not None:
        installed = s._inner.load_seed_manifest(manifest, ag)
        s.add_node("Seed", {"id": "mbpp_train_diet_probe", "version": "1.0.0"})
        installed_nodes = installed.get("nodes", 0)
    result = psy.synthesize_from_request(s, ag, t["prompt"], examples)
    return {
        "status": result.get("status"),
        "construction": result.get("construction"),
        "rungs": result.get("rungs"),
        "spine_labels": result.get("spine_labels"),
        "manifest_nodes_installed": installed_nodes,
    }


def leave_n_out_probe(all_train_tasks: List[Dict[str, Any]], *,
                      n_holdout: int = N_HOLDOUT) -> Dict[str, Any]:
    """Mine the diet on the first (n-n_holdout) train tasks by task_id;
    probe the pipeline's PRIMARY-protocol behaviour on the LAST n_holdout —
    does diet content get USED (a mined-chunk rung-1/lattice accept or
    gap, or a bigram-influenced spine that DEMONSTRABLY differs from the
    CONTROL arm's own outcome)? This is a train-side MECHANISM probe
    (prereg: "NOT the HQ3 verdict -- that is Q5 on test"), never a
    benchmark accept-rate claim."""
    ordered = sorted(all_train_tasks, key=lambda t: t["task_id"])
    holdout = ordered[-n_holdout:]
    mine_set = ordered[:-n_holdout]

    diet = mine_diet(mine_set)
    manifest = build_seed_manifest(diet)

    rows = []
    for t in holdout:
        tid = t["task_id"]
        parsed = mbpp_spec.parse_asserts(t)
        split = mbpp_spec.split_rows(parsed["rows"], "primary")
        if not split["runnable"]:
            rows.append({"task_id": tid, "used": False,
                         "reason": "protocol_excluded:%s" % split.get("excluded_reason")})
            continue
        examples = [(r["inputs"], r["expected"]) for r in split["revealed"]
                    if "tol" not in r and not r.get("unordered")]
        if not examples:
            rows.append({"task_id": tid, "used": False,
                         "reason": "no_json_safe_revealed_rows"})
            continue

        control = _run_probe_arm(t, examples, None)
        diet_arm = _run_probe_arm(t, examples, manifest)

        used_chunk = bool(diet_arm["construction"]) and \
            str(diet_arm["construction"]).startswith("mck_")
        diverged = ((control["status"], control["construction"],
                    tuple(control["spine_labels"] or [])) !=
                   (diet_arm["status"], diet_arm["construction"],
                    tuple(diet_arm["spine_labels"] or [])))
        rows.append({
            "task_id": tid,
            "used": bool(used_chunk or diverged),
            "used_mined_chunk": used_chunk,
            "diverged_from_control": diverged,
            "control": control,
            "diet": diet_arm,
        })

    return {
        "mine_set_task_ids": [t["task_id"] for t in mine_set],
        "holdout_task_ids": [t["task_id"] for t in holdout],
        "n_mine": len(mine_set), "n_holdout": len(holdout),
        "n_used": sum(1 for r in rows if r.get("used")),
        "rows": rows,
    }


# --------------------------------------------------------------------------- #
#  One full run -> canonical artifact dict (the twin-run determinism unit).
# --------------------------------------------------------------------------- #
def one_run(train_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    diet = mine_diet(train_tasks)
    probe = leave_n_out_probe(train_tasks)
    return {
        "task": "PROGRAM_SYNTHESIS ARC2 Q3 -- the paired diet",
        "registered": "PROGRAM_SYNTHESIS_ARC2_PLAN.md sec2 Q3",
        "version": "1.0.0",
        "scope": {"split": "train", "task_id_rule": ">=601",
                  "n_tasks": diet["n_tasks"]},
        "emit": {"n_emit_ok": diet["n_emit_ok"], "emit_rate": diet["emit_rate"],
                "rows": diet["emit_rows"]},
        "chunks": diet["chunks"],
        "bigrams": diet["bigrams"],
        "affinity": diet["affinity"],
        "leave_n_out_probe": probe,
    }


def _canonical_blob(art: Dict[str, Any]) -> bytes:
    return json.dumps(art, sort_keys=True, separators=(",", ":")).encode()


def main():
    train_tasks = load_train_tasks()
    log("train tasks:", len(train_tasks))

    art1 = one_run(train_tasks)
    h1 = hashlib.sha256(_canonical_blob(art1)).hexdigest()

    if os.environ.get("MTD_ONCE"):
        determinism = {"runs": 1, "sha256": h1, "note": "MTD_ONCE set -- single run, no twin"}
    else:
        log("second run (determinism evidence)...")
        t0 = time.time()
        art2 = one_run(train_tasks)
        h2 = hashlib.sha256(_canonical_blob(art2)).hexdigest()
        determinism = {"runs": 2, "sha256_run1": h1, "sha256_run2": h2,
                       "byte_identical": _canonical_blob(art1) == _canonical_blob(art2),
                       "second_run_elapsed_s": round(time.time() - t0, 1)}
        log("determinism:", determinism)

    art1["determinism"] = determinism
    art1["date"] = "2026-08-01"
    os.makedirs(os.path.dirname(OUT_RESULTS), exist_ok=True)
    with open(OUT_RESULTS, "w") as f:
        json.dump(art1, f, indent=1, sort_keys=True)
        f.write("\n")
    log("wrote", OUT_RESULTS)

    full_diet = mine_diet(train_tasks)
    manifest = build_seed_manifest(full_diet)
    with open(OUT_SEED, "w") as f:
        json.dump(manifest, f, indent=1, sort_keys=True)
        f.write("\n")
    log("wrote", OUT_SEED, "(%d nodes)" % len(manifest["nodes"]))
    log("emit_rate=%.4f chunks=%d cueable=%d with_trigger=%d bigrams=%d affinity_rows=%d"
        % (full_diet["emit_rate"], full_diet["chunks"]["totals"]["kept_final"],
           full_diet["chunks"]["totals"]["cueable"],
           full_diet["chunks"]["totals"]["with_nonzero_trigger"],
           len(full_diet["bigrams"]["bigrams"]), len(full_diet["affinity"]["affinity_rows"])))


if __name__ == "__main__":
    main()
