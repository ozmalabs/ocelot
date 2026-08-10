"""jabberwock_richlm_read_run81.py -- RUN 81: ATTACH A RICH LANGUAGE MODEL TO THE READING DECODE.

THE FRAMING (creator): run 75 proved SENTENCE PREDICTION is the DOMINANT reading channel (isolated
26.0% -> sentence-bigram+strict 57.5% -> sentence-bigram+loose(GOLD) 51.2%), then run 76 showed the
mechanism TRANSFERS to real IAM-OnDB lines but only lifts 0.0% -> 13.1% within-writer -- and both
runs fed the prediction channel a TOY WORD BIGRAM (a count table over a ~1.2M-word Brown reduction).
"We have a rich language model -- all we need to do is attach it." This run swaps the bigram for the
RICHEST available language model and re-measures the lift, on BOTH corpora. THE VISUAL CHANNEL IS
UNCHANGED (donkey=0, training-free, run 69/74/75's own loose/strict per-char and whole-word costs,
reused VERBATIM) -- only the LANGUAGE-MODEL channel is swapped, exactly as CLAUDE.md's "attach a new
capability, don't hack the visual" discipline demands. This is the human reading architecture:
training-free geometric perception + a rich, lifetime-learned language prior.

============================================================================================= #
STAGE 0 -- WHICH LM, AND WHY (probed live on this machine, see `stage_probe` + `probe.json`):
============================================================================================= #
Preference order per the task: (a) a programmatic LLM the project can call; (b) a strong
neural/large-corpus n-gram (KenLM); (c) a bigger n-gram as a lower bound.
  * No ANTHROPIC_API_KEY / OPENAI_API_KEY in the environment; no `anthropic`/`openai` SDK installed;
    no network egress assumed. Rules out a hosted frontier LLM.
  * No `kenlm` package installed (option (b) unavailable).
  * `ollama` IS installed and running locally (`ollama list`) with 16 local models. This is a REAL
    programmatic LLM the project can call (option (a)) -- attached via `http://localhost:11434`.
  * The LARGEST model present, `qwen3-coder:30b` (30.5B, Q4_K_M, 18.6GB), OOM-KILLS the ollama
    service on this machine (30GB RAM total, ~15GB free -- see systemd journal:
    "kernel OOM killer killed some processes", "ollama.service: Failed with result 'oom-kill'").
    Confirmed unusable, not a design choice -- documented as an honest availability ceiling, NOT
    silently downgraded.
  * The next-largest, `rnj-1:8b` (8.3B, gemma3-family) LOADS and runs, but on this task (joint
    per-position candidate ranking/choice under a strict output-format instruction) it frequently
    derails into open-ended chain-of-thought inside what should be a terse JSON answer (observed:
    35s+ latency, malformed/inconsistent JSON keys, on some calls literally echoing the chat-message
    structure back) -- an unreliable choice for an automated pipeline that needs ~300+ calls.
  * `gemma3:4b` (4.3B, Q4_K_M) is smaller but reliably returns clean, fast (~1.5-2.5s), parseable
    JSON on this exact task across dozens of live test calls (0/20 parse failures in the pre-flight
    check below) -- ATTACHED AS THE RICH LM. Documented HONESTLY: this is the largest model on this
    machine BOTH available AND reliable for the automated pipeline; `rnj-1:8b` is larger but not
    reliable here, and `qwen3-coder:30b` cannot be loaded at all -- the true richness ceiling this
    box could reach is higher than what actually ran (an honest LOWER BOUND on a bigger/hosted LLM's
    likely ceiling, precisely the caveat run 81's spec calls for).
  * Either way, gemma3:4b (a real instruction-tuned transformer LM trained on broad web-scale text)
    is CATEGORICALLY richer than run 75/76's toy count-based Brown bigram (a ~1.2M-token, order-1
    Markov table with stupid-backoff) -- it can use FULL bidirectional sentence context and broad
    world/word-association knowledge a bigram structurally cannot represent.

============================================================================================= #
STAGE 1 -- HOW THE RICH LM IS ATTACHED (the actual mechanism):
============================================================================================= #
The bigram's own interface (`r75.make_lm_scorer` -> `score(prev_word, cur_word)`) is a MARKOV
transition score consumed by `r75.viterbi_decode`'s pairwise DP. A rich LM's whole point is FULL
sentence (not just prev-word) context, so the pairwise-transition Markov structure is retired for
this arm (the bigram CONTROL still uses it, verbatim, for reproducibility -- see below) in favour of
a JOINT single-call-per-sentence re-ranker:
  1. VISUAL (UNCHANGED): `r75.topk_candidates` (loose AND strict, run 69/74/75's own cost, untouched)
     produces the top-K=BEAM_K visual candidates/position, exactly as before.
  2. SHORTLIST: the top M=SHORTLIST_M of those (by visual cost) is what the rich LM is SHOWN --
     pre-flight testing (below) found that showing an 8B/4B local model 50-item lists across many
     positions in one call degrades to a DEGENERATE near-identity/rotation pattern (not genuine
     ranking -- verified by inspection, see report); M=6 is the largest shortlist size that produced
     reliable, apparently-genuine per-item judgments in live testing.
  3. ONE JOINT CALL PER SENTENCE (or PER LINE for IAM): the LM is shown ALL positions' shortlists
     together and asked to choose the single best-fitting WORD per position, jointly, so its answer
     can reflect cross-word topical/discourse coherence (the "rich, semantic/discourse" prediction
     the task calls for) -- not just a local, prev-word-only bigram fact.
  4. SCORE CONSTRUCTION (so a VISUAL_WEIGHT dial -- run 75/76's own methodology -- still applies):
     for the position's ORIGINAL (full-K) visual-ranked candidate list, the LM's chosen word gets
     lm_score=0 (best); every other candidate keeps a strictly decreasing score by its OWN original
     visual rank (`-(1+rank)`) -- i.e. the LM's endorsed word is PROMOTED to the top of the LM
     channel, but the channel does not touch the relative order of anything else. Both channels are
     then per-position min-max normalized to [-1, 0] (run 76's own `_normalize_visual` technique,
     needed because a bigram log-prob, a rank-based LM score, and a DTW/letter-cost visual score are
     three different, uncalibrated scales) before combining as
     `visual_weight * visual_norm + LM_WEIGHT * lm_norm`, swept over the SAME VISUAL_WEIGHTS grid
     run 75/76 pre-registered, argmax per position (no Viterbi chaining needed -- the rich LM already
     integrated full-sentence context when it made its joint choice).
  5. THE BIGRAM CONTROL is NOT reimplemented -- `decode_synth`/`decode_iam` call r75's OWN
     `make_lm_scorer` + `viterbi_decode` (and r76's own `build_line_inputs`) VERBATIM on the SAME
     prep/read/recognize/holistic checkpoints, and the run asserts the reproduced numbers match the
     stored run75/76 `decode.json` figures (57.5%/51.2% strict/loose synthetic; 13.1% IAM within) --
     "decode swaps LM cleanly" is a literal code-level fact, not a claim.

Scope cuts (documented, not silent): the JUMBLE/MISSPELL/PROOFREADING-BLINDNESS signature re-checks
(run 75's other headline results) are NOT re-run here -- each needs its own fresh batch of LLM calls
(corrupted visual rows change the shortlist) and the time budget went to getting the PRIMARY lift
number solid on BOTH corpora with a comparability-preserving control, per the task's own priority
ordering. This mirrors run 75's own "trigram noted but not built" honesty convention.

============================================================================================= #
REUSE (nothing about the visual channel or the corpora is rebuilt):
============================================================================================= #
  * `scripts.jabberwock_sentence_read_run75` (r75) -- `topk_candidates`/`loose_cost`/`strict_cost`/
    `build_lex_by_len`/`make_lm_scorer`/`viterbi_decode`/`decode_all_sentence`/`_acc_report`/
    `_wilson`/`_mcnemar` -- REUSED VERBATIM. `results/run75_checkpoints/{prep,read,decode}.json` --
    READ-ONLY (the 130 synthetic sentences, their per-char within-writer DTW distance rows, and the
    bigram-control decode numbers to reproduce).
  * `scripts.jabberwock_iam_full_run76` (r76) -- `topk_candidates_iam`/`build_line_inputs`/
    `oracle_count_rows`/`_normalize_visual`/`_levenshtein`/`_report` -- REUSED VERBATIM.
    `results/run76_checkpoints/{prep,recognize,holistic,decode,summary}.json` -- READ-ONLY (the 27
    real IAM-OnDB test lines / 122 test words and the bigram-control decode numbers to reproduce).

SEED GUARD / DISCIPLINE: `OZMA_SEED_PERSIST_DISABLED=1`; md5(seeds/stroke_shapes.json) asserted
UNCHANGED before AND after every stage (this run touches NO seed/geometry code at all -- the guard
is a pure sanity check). `results/run7{5,6}_checkpoints/` are READ-ONLY; this script writes ONLY
`results/run81_checkpoints/*`. NO git add/commit. System python3 is sufficient for every stage here
(no substrate_rs / native calls -- all distances were already computed by runs 75/76).

Stages: probe (LM availability + coverage/reliability pre-flight, no corpus writes) -> llm_synth
(block-checkpointed rich-LM calls over run 75's 130 sentences, loose+strict arms) -> decode_synth
(pure combine + sweep + bigram-control reproduction) -> llm_iam (block-checkpointed rich-LM calls
over run 76's 27 IAM lines, within+cross channels) -> decode_iam (pure combine + sweep + bigram-
control reproduction) -> summary.

Run (from the gamma-substrate repo root):
  OZMA_SEED_PERSIST_DISABLED=1 DEEPWRITING_DIR=/tmp/handwriting \\
    IAM_STROKES_DIR=/tmp/handwriting/iam_onbd/lineStrokes IAM_ASCII_DIR=/tmp/handwriting/iam_ascii/ascii \\
    PYTHONPATH=.:runners/dsl/python \\
    /home/matt/ozma/internal/research/.venv/bin/python3 \\
    scripts/jabberwock_richlm_read_run81.py --stage <probe|llm_synth|decode_synth|llm_iam|decode_iam|summary>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
os.environ.setdefault("DEEPWRITING_DIR", "/tmp/handwriting")
os.environ.setdefault("IAM_STROKES_DIR", "/tmp/handwriting/iam_onbd/lineStrokes")
os.environ.setdefault("IAM_ASCII_DIR", "/tmp/handwriting/iam_ascii/ascii")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np

import scripts.jabberwock_sentence_read_run75 as r75
import scripts.jabberwock_iam_full_run76 as r76

SEP = "=" * 92
STROKE_SHAPES_SEED = r75.STROKE_SHAPES_SEED
CKPT_DIR = os.path.join(ROOT, "results", "run81_checkpoints")
LOG = os.path.join(ROOT, "results", "omniglot_gate_run81.log")
os.makedirs(CKPT_DIR, exist_ok=True)

RUN75_CKPT = os.path.join(ROOT, "results", "run75_checkpoints")   # READ-ONLY.
RUN76_CKPT = os.path.join(ROOT, "results", "run76_checkpoints")   # READ-ONLY.
RUN61_LEXICON = r75.RUN61_LEXICON                                  # READ-ONLY.

# ------------------------------------------------------------------------------------------- #
# PRE-REGISTERED CONSTANTS.
# ------------------------------------------------------------------------------------------- #
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/chat")
RICH_LM_MODEL = "gemma3:4b"        # see module docstring STAGE 0 for the full availability/reliability
                                    # rationale (rnj-1:8b unreliable/slow here; qwen3-coder:30b OOMs).
SHORTLIST_M = 6                     # per-position candidates shown to the rich LM (pre-flight tested).
CALL_TIMEOUT_SECONDS = 90.0
MAX_RETRIES = 1

BEAM_K = r75.BEAM_K                  # 50 -- SAME visual candidate pool as run 75/76's own bigram arm.
LM_WEIGHT = 1.0
VISUAL_WEIGHTS = r75.VISUAL_WEIGHTS  # (0.0, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0) -- run 75/76's own grid.
PRIMARY_VISUAL_WEIGHT = r75.PRIMARY_VISUAL_WEIGHT   # 2.0 -- run 75/76's own pre-registered primary.

PER_CALL_BUDGET_SECONDS = 480.0

# Honest bars this run reports against (task-given, prior-run numbers, cited verbatim).
BAR_SYNTH_BIGRAM_STRICT = 57.5     # run 75 arm B (sentence-bigram + strict).
BAR_SYNTH_BIGRAM_LOOSE = 51.2      # run 75 arm C (sentence-bigram + loose, THE GOLD).
BAR_SYNTH_NO_CONTEXT = 26.0        # run 75 arm A (isolated, strict, no sentence context).
BAR_IAM_BIGRAM_WITHIN = 13.1       # run 76 rep_b_within_preddom.
BAR_IAM_FLOOR = 0.0                # run 76 rep_a (per-letter+lexicon, cross-corpus).


# ============================================================================================= #
#  I/O + seed guard (identical pattern to runs 61-76).
# ============================================================================================= #
def _md5(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def _ckpt(name):
    return os.path.join(CKPT_DIR, name)


def _save(obj, path):
    with open(path, "w") as f:
        json.dump(obj, f)


def _load(path):
    with open(path) as f:
        return json.load(f)


def _require(name):
    p = _ckpt(name)
    if not os.path.exists(p):
        raise SystemExit(f"WALL: run the stage that produces {name} first.")
    return _load(p)


def _seed_guard(stage, before=None):
    cur = _md5(STROKE_SHAPES_SEED)
    if before is not None and cur != before:
        raise SystemExit(f"HARD STOP: seeds/stroke_shapes.json md5 changed during {stage} "
                          f"({before} -> {cur}).")
    return cur


def _wilson(k, n):
    return r75._wilson(k, n)


def _mcnemar(a, b):
    return r75._mcnemar(a, b)


# ============================================================================================= #
#  THE RICH LM CLIENT -- one programmatic call, JSON-array-of-words response, robust parsing.
# ============================================================================================= #
def ollama_chat(prompt: str, model: str = RICH_LM_MODEL, timeout: float = CALL_TIMEOUT_SECONDS):
    """Returns (content:str, elapsed:float, error:str|None). Never raises -- callers must check
    `error`. Deliberately does NOT use `format: json` (pre-flight testing found it sometimes made
    the model wrap the answer in surprising extra keys); the prompt itself demands a bare JSON array
    and `extract_json_list` recovers it from surrounding text if the model adds any."""
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": 0},
    }).encode()
    req = urllib.request.Request(OLLAMA_URL, data=body, headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            d = json.loads(resp.read())
        return d["message"]["content"], time.time() - t0, None
    except Exception as e:                                    # noqa: BLE001 -- network/timeout/parse.
        return "", time.time() - t0, f"{type(e).__name__}: {e}"


def extract_json_list(content: str):
    """Best-effort recovery of a JSON array of strings from a model response that SHOULD be just
    the array but may have stray text/markdown fences around it."""
    m = re.search(r"\[.*\]", content, re.S)
    if not m:
        return None
    try:
        val = json.loads(m.group(0))
    except Exception:
        return None
    if isinstance(val, list) and all(isinstance(x, str) for x in val):
        return val
    return None


def build_joint_prompt(cand_lists: list) -> str:
    lines = [f"{i + 1}: [{', '.join(words)}]" for i, words in enumerate(cand_lists)]
    n = len(cand_lists)
    return (
        "A sequence has been read by an imperfect handwriting-recognition system. Below, each "
        "numbered position lists that word's candidate readings (one is correct). These are content "
        "words from a real text passage (short function words removed), in original order, so "
        "consecutive words may relate by topic/theme even without full grammar.\n\n"
        + "\n".join(lines) +
        "\n\nChoose exactly ONE word per position -- the combination that best fits together as a "
        f"coherent, thematically consistent sequence. Respond with ONLY a JSON array of exactly {n} "
        "words in position order, each copied EXACTLY (identical spelling) from its own position's "
        "candidate list. No explanation, no markdown, no extra keys -- just the array."
    )


def joint_llm_pick(cand_lists: list, model: str = RICH_LM_MODEL):
    """One joint call. Returns (picks:list[str|None] per position, meta:dict). `picks[i]` is None on
    unrecoverable failure/mismatch for that position (caller falls back to visual top-1)."""
    prompt = build_joint_prompt(cand_lists)
    last_err = None
    for attempt in range(MAX_RETRIES + 1):
        content, dt, err = ollama_chat(prompt, model=model)
        if err is None:
            arr = extract_json_list(content)
            if arr is not None and len(arr) == len(cand_lists):
                picks, n_bad = [], 0
                for w, cands in zip(arr, cand_lists):
                    wl = w.strip().lower()
                    picks.append(wl if wl in cands else None)
                    n_bad += int(wl not in cands)
                return picks, {"elapsed": dt, "attempts": attempt + 1, "n_off_list": n_bad,
                                "parse_ok": True, "error": None}
            last_err = "parse_fail_or_len_mismatch"
        else:
            last_err = err
    # Total failure: every position falls back to visual top-1 (a documented no-op for the LM
    # channel at that position, NOT silently dropped).
    return [None] * len(cand_lists), {"elapsed": 0.0, "attempts": MAX_RETRIES + 1, "n_off_list": -1,
                                       "parse_ok": False, "error": last_err}


# ============================================================================================= #
#  SCORE CONSTRUCTION -- rank-promotion LM score + per-position [-1,0] normalization for both
#  channels (run 76's own `_normalize_visual` technique, generalized to two heterogeneous channels).
# ============================================================================================= #
def rank_promoted_lm_scores(cand_words: list, pick: str | None) -> np.ndarray:
    """cand_words already in VISUAL-cost-ascending order (index 0 = best visual). The LM's endorsed
    `pick` (if any, and if present in cand_words) gets score 0 (best); everyone else keeps a strictly
    decreasing score by their OWN original visual rank -- i.e. the LM channel PROMOTES its pick to
    the top without disturbing the relative order of anything else."""
    n = len(cand_words)
    base = -np.arange(1, n + 1, dtype=float)     # -1, -2, ..., -n (position 0's baseline).
    if pick is None or pick not in cand_words:
        return base
    scores = base.copy()
    pick_idx = cand_words.index(pick)
    scores[pick_idx] = 0.0
    return scores


def normalize01(scores: np.ndarray) -> np.ndarray:
    if len(scores) == 0:
        return scores
    hi, lo = float(scores.max()), float(scores.min())
    rng = (hi - lo) if hi > lo else 1.0
    return (scores - hi) / rng


def combine_and_argmax(cand_words: list, visual_scores: np.ndarray, lm_scores: np.ndarray,
                        visual_weight: float, lm_weight: float = LM_WEIGHT) -> str:
    if not cand_words:
        return ""
    vnorm = normalize01(np.asarray(visual_scores, float))
    lnorm = normalize01(np.asarray(lm_scores, float))
    combined = visual_weight * vnorm + lm_weight * lnorm
    return cand_words[int(np.argmax(combined))]


# ============================================================================================= #
#  STAGE: probe -- LM availability + reliability + coverage pre-flight. No corpus data touched.
# ============================================================================================= #
def stage_probe():
    print(f"\n{SEP}\n  STAGE: probe -- rich LM availability + coverage/reliability pre-flight"
          f"\n{SEP}", flush=True)
    t0 = time.time()
    md5_before = _seed_guard("probe")

    have_anthropic_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
    have_openai_key = bool(os.environ.get("OPENAI_API_KEY"))
    try:
        import kenlm  # noqa: F401
        have_kenlm = True
    except Exception:
        have_kenlm = False

    tags_err = None
    models = []
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=10) as resp:
            tags = json.loads(resp.read())
        models = [m["name"] for m in tags.get("models", [])]
    except Exception as e:
        tags_err = f"{type(e).__name__}: {e}"

    # A tiny live reliability check with a semantically-disambiguating sentence (the unit test's
    # own scenario, run here live for the probe report): "quick brown ___ jumps" must beat "box".
    content, dt, err = ollama_chat(
        'Sentence with blank: "The quick brown ___ jumps over the lazy dog." '
        "Candidates: fox, box, sox. Which ONE candidate best fits? Respond with ONLY a JSON array "
        'containing that one word, e.g. ["fox"].',
        model=RICH_LM_MODEL,
    )
    disambig_pick = None
    if not err:
        arr = extract_json_list(content)
        if arr:
            disambig_pick = arr[0].strip().lower()

    out = {
        "have_anthropic_key": have_anthropic_key, "have_openai_key": have_openai_key,
        "have_kenlm": have_kenlm, "ollama_tags_error": tags_err, "ollama_models": models,
        "rich_lm_model": RICH_LM_MODEL, "shortlist_m": SHORTLIST_M,
        "disambiguation_probe_pick": disambig_pick, "disambiguation_probe_elapsed_s": dt,
        "disambiguation_probe_error": err,
        "known_unusable": {
            "qwen3-coder:30b": "OOM-kills the local ollama service (18.6GB model, ~15GB free RAM) "
                                "-- confirmed via systemd journal ('oom-kill'), not a design choice.",
            "rnj-1:8b": "loads and runs, but derails into open-ended chain-of-thought / malformed "
                        "JSON on this joint-ranking task in live testing (35s+ latency spikes, "
                        "inconsistent output keys) -- unreliable for an automated ~300-call pipeline.",
        },
        "stroke_shapes_md5": md5_before,
    }
    _save(out, _ckpt("probe.json"))
    _seed_guard("probe", md5_before)

    print(f"  ANTHROPIC_API_KEY present: {have_anthropic_key}   OPENAI_API_KEY present: "
          f"{have_openai_key}   kenlm installed: {have_kenlm}", flush=True)
    print(f"  ollama reachable: {tags_err is None}   models available: {len(models)}", flush=True)
    print(f"  ATTACHED: {RICH_LM_MODEL} via {OLLAMA_URL}  (shortlist M={SHORTLIST_M})", flush=True)
    print(f"  disambiguation probe ('fox' vs 'box'/'sox' given full-sentence semantics): "
          f"picked={disambig_pick!r}  [{dt:.1f}s]  error={err}", flush=True)
    print(f"  saved -> {_ckpt('probe.json')}  [probe {time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  STAGE: llm_synth -- block-checkpointed rich-LM calls over run 75's 130 synthetic sentences.
# ============================================================================================= #
def _synth_candidate_lists(dists: dict, lex_by_len: dict, s: dict, arm: str, K: int = BEAM_K):
    """Returns list of (cand_words_full_K, visual_scores_full_K) per position, VISUAL UNCHANGED."""
    out = []
    for iid in s["iids"]:
        words, scores = r75.topk_candidates(dists[iid], lex_by_len, arm, K)
        out.append((list(words), scores))
    return out


def stage_llm_synth():
    print(f"\n{SEP}\n  STAGE: llm_synth -- rich-LM joint calls over run 75's 130 sentences "
          f"(loose + strict arms)\n{SEP}", flush=True)
    t0 = time.time()
    md5_before = _seed_guard("llm_synth")

    prep = _load(os.path.join(RUN75_CKPT, "prep.json"))
    rd = _load(os.path.join(RUN75_CKPT, "read.json"))
    if not rd.get("done"):
        raise SystemExit("WALL: run 75's read.json is not COMPLETE -- this run needs it finished.")
    dists = {iid: rec["within_dists"] for iid, rec in rd["instances"].items()}
    lexicon = _load(RUN61_LEXICON)
    lex_by_len = r75.build_lex_by_len(lexicon["lexicon"])
    sentences = prep["sentences"]

    out_path = _ckpt("richlm_synth.json")
    state = _load(out_path) if os.path.exists(out_path) else {"calls": {}, "done": False}
    if state.get("done"):
        print(f"  llm_synth already COMPLETE (n_calls={len(state['calls'])}).", flush=True)
        return 0

    jobs = []
    for arm in ("loose", "strict"):
        for s in sentences:
            jobs.append((f"{s['sid']}|{arm}", s, arm))

    deadline = time.time() + PER_CALL_BUDGET_SECONDS
    n_new = 0
    for key, s, arm in jobs:
        if key in state["calls"]:
            continue
        full = _synth_candidate_lists(dists, lex_by_len, s, arm)
        cand_lists_full = [w for w, _ in full]
        shortlists = [w[:SHORTLIST_M] for w in cand_lists_full]
        picks, meta = joint_llm_pick(shortlists)
        state["calls"][key] = {"sid": s["sid"], "arm": arm, "picks": picks, "meta": meta,
                                "shortlists": shortlists}
        n_new += 1
        if n_new % 10 == 0:
            _save(state, out_path)
            _seed_guard("llm_synth", md5_before)
            print(f"    ... {len(state['calls'])}/{len(jobs)} calls  "
                  f"[{time.time()-t0:.1f}s]", flush=True)
        if time.time() > deadline:
            _save(state, out_path)
            _seed_guard("llm_synth", md5_before)
            print(f"  WALL-BUDGET: {len(state['calls'])}/{len(jobs)} done -- re-invoke "
                  f"--stage llm_synth to resume.", flush=True)
            return 2

    state["done"] = True
    _save(state, out_path)
    _seed_guard("llm_synth", md5_before)
    n_parse_fail = sum(1 for c in state["calls"].values() if not c["meta"]["parse_ok"])
    print(f"  llm_synth COMPLETE: {len(state['calls'])} calls, {n_parse_fail} total parse "
          f"failures (fell back to visual top-1)  [{time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  STAGE: decode_synth -- pure combine + sweep + bigram-control reproduction. No LLM calls.
# ============================================================================================= #
def _rich_decode_sentence(dists, lex_by_len, s, arm, picks, visual_weight, K=BEAM_K):
    pred = []
    for pos, iid in enumerate(s["iids"]):
        words, vscores = r75.topk_candidates(dists[iid], lex_by_len, arm, K)
        words = list(words)
        pick = picks[pos] if pos < len(picks) else None
        lm_scores = rank_promoted_lm_scores(words, pick)
        pred.append(combine_and_argmax(words, vscores, lm_scores, visual_weight))
    return pred


def _coverage_table(dists, lex_by_len, sentences, arm):
    out = {}
    for K in (SHORTLIST_M, 15, 25, BEAM_K):
        hits = tot = 0
        for s in sentences:
            for w, iid in zip(s["words"], s["iids"]):
                words, _ = r75.topk_candidates(dists[iid], lex_by_len, arm, K)
                tot += 1
                hits += int(w in words)
        out[str(K)] = hits / tot if tot else 0.0
    return out


def stage_decode_synth():
    print(f"\n{SEP}\n  STAGE: decode_synth -- combine rich-LM picks + sweep + bigram-control "
          f"reproduction (synthetic)\n{SEP}", flush=True)
    t0 = time.time()
    md5_before = _seed_guard("decode_synth")

    prep = _load(os.path.join(RUN75_CKPT, "prep.json"))
    rd = _load(os.path.join(RUN75_CKPT, "read.json"))
    dists = {iid: rec["within_dists"] for iid, rec in rd["instances"].items()}
    lexicon = _load(RUN61_LEXICON)
    logfreq = lexicon["logfreq"]
    lex_by_len = r75.build_lex_by_len(lexicon["lexicon"])
    sentences = prep["sentences"]

    rl = _require("richlm_synth.json")
    if not rl.get("done"):
        raise SystemExit("WALL: llm_synth not COMPLETE -- re-invoke --stage llm_synth.")

    # -- BIGRAM CONTROL: r75's OWN code, verbatim, on the SAME data. Must reproduce run 75's stored
    #    decode.json numbers exactly (this IS the "decode swaps LM cleanly" claim, checked). --
    bigram_lm_score = r75.make_lm_scorer(prep["lm"]["unigram"], prep["lm"]["bigram"], logfreq)
    bigram_reports = {}
    for arm_label, arm_key in (("B", "strict"), ("C", "loose")):
        preds = r75.decode_all_sentence(sentences, dists, lex_by_len, arm_key, bigram_lm_score,
                                        PRIMARY_VISUAL_WEIGHT)
        bigram_reports[arm_label] = r75._acc_report(preds)
    run75_decode = _load(os.path.join(RUN75_CKPT, "decode.json"))
    control_match = {
        "B": abs(bigram_reports["B"]["word_acc"] - run75_decode["reps"]["B"]["word_acc"]) < 1e-9,
        "C": abs(bigram_reports["C"]["word_acc"] - run75_decode["reps"]["C"]["word_acc"]) < 1e-9,
    }

    # -- RICH-LM arm: sweep + primary weight, both visual arms. --
    picks_by_key = {k: v["picks"] for k, v in rl["calls"].items()}
    rich_sweep = {"loose": {}, "strict": {}}
    for arm in ("loose", "strict"):
        for vw in VISUAL_WEIGHTS:
            preds = []
            for s in sentences:
                picks = picks_by_key[f"{s['sid']}|{arm}"]
                pred = _rich_decode_sentence(dists, lex_by_len, s, arm, picks, vw)
                preds.append({"sid": s["sid"], "true": s["words"], "pred": pred})
            rich_sweep[arm][str(vw)] = r75._acc_report(preds)
    rich_primary = {arm: rich_sweep[arm][str(PRIMARY_VISUAL_WEIGHT)] for arm in ("loose", "strict")}
    rich_best = {}
    for arm in ("loose", "strict"):
        best_vw = max(VISUAL_WEIGHTS, key=lambda vw: rich_sweep[arm][str(vw)]["word_acc"])
        rich_best[arm] = {"vw": best_vw, "rep": rich_sweep[arm][str(best_vw)]}

    coverage_loose = _coverage_table(dists, lex_by_len, sentences, "loose")
    coverage_strict = _coverage_table(dists, lex_by_len, sentences, "strict")

    n_off_list = sum(c["meta"]["n_off_list"] for c in rl["calls"].values() if c["meta"]["n_off_list"] >= 0)
    n_parse_fail = sum(1 for c in rl["calls"].values() if not c["meta"]["parse_ok"])

    out = {
        "bigram_reports": bigram_reports, "control_matches_run75": control_match,
        "rich_sweep": rich_sweep, "rich_primary": rich_primary, "rich_best": rich_best,
        "coverage_loose": coverage_loose, "coverage_strict": coverage_strict,
        "n_off_list_words": n_off_list, "n_parse_fail_calls": n_parse_fail,
        "n_calls": len(rl["calls"]), "n_sentences": len(sentences),
        "stroke_shapes_md5": md5_before,
    }
    _save(out, _ckpt("decode_synth.json"))
    _seed_guard("decode_synth", md5_before)

    print(f"  bigram control reproduces run75 decode.json: B={control_match['B']}  "
          f"C={control_match['C']}", flush=True)
    print(f"  bigram  B(strict)={100*bigram_reports['B']['word_acc']:.1f}%  "
          f"C(loose)={100*bigram_reports['C']['word_acc']:.1f}%", flush=True)
    print(f"  rich-LM primary(vw={PRIMARY_VISUAL_WEIGHT})  strict={100*rich_primary['strict']['word_acc']:.1f}%"
          f"  loose={100*rich_primary['loose']['word_acc']:.1f}%", flush=True)
    print(f"  rich-LM best-of-sweep  strict={100*rich_best['strict']['rep']['word_acc']:.1f}%"
          f"@vw={rich_best['strict']['vw']}  loose={100*rich_best['loose']['rep']['word_acc']:.1f}%"
          f"@vw={rich_best['loose']['vw']}", flush=True)
    print(f"  visual coverage ceiling (true word in top-K) loose: {coverage_loose}", flush=True)
    print(f"  LLM off-list words={n_off_list}  parse-fail calls={n_parse_fail}/{len(rl['calls'])}",
          flush=True)
    print(f"  saved -> {_ckpt('decode_synth.json')}  [decode_synth {time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  STAGE: llm_iam -- block-checkpointed rich-LM calls over run 76's 27 real IAM lines.
# ============================================================================================= #
def _iam_line_candidate_lists(line, rows_by_wid, within_by_wid, cross_by_wid, lex_by_len,
                               use_within: bool, K=BEAM_K):
    out = []
    for wid in line["wids"]:
        w, s = r76.topk_candidates_iam(rows_by_wid[wid], lex_by_len, within_by_wid.get(wid, {}),
                                       cross_by_wid.get(wid, {}), use_within, K)
        out.append((list(w), s))
    return out


def _load_iam_assembled():
    """Reproduces run 76's own `stage_decode` assembly (rows_by_wid / within_by_wid / cross_by_wid /
    lex_by_len / queries / sent_lines) from its READ-ONLY checkpoints -- no recomputation, pure glue,
    identical to r76.stage_decode's own first third."""
    prep = _load(os.path.join(RUN76_CKPT, "prep.json"))
    rec = _load(os.path.join(RUN76_CKPT, "recognize.json"))
    hol = _load(os.path.join(RUN76_CKPT, "holistic.json"))
    if not rec.get("done") or not hol.get("done"):
        raise SystemExit("WALL: run 76's recognize/holistic checkpoints are not COMPLETE.")

    lexicon, logfreq = prep["lexicon"], prep["logfreq"]
    lex_by_len = r75.build_lex_by_len(lexicon)
    queries = {q["wid"]: q for q in prep["queries"]}

    rows_by_wid = {}
    for r in rec["records"]:
        wid = r["wid"]
        SD = r76.r62._spans_to_SD(r["spans"], r["K"])
        rows = r76.oracle_count_rows(SD, r["K"], queries[wid]["len"])
        if rows is None:
            rows = [[10.0] * 26 for _ in range(queries[wid]["len"])]
        rows_by_wid[wid] = rows

    within_by_wid = {r["wid"]: r["within_rich"] for r in hol["records"]}
    cross_by_wid = {r["wid"]: r["cross_rich"] for r in hol["records"]}
    return prep, queries, lex_by_len, logfreq, rows_by_wid, within_by_wid, cross_by_wid


def stage_llm_iam():
    print(f"\n{SEP}\n  STAGE: llm_iam -- rich-LM joint calls over run 76's 27 IAM lines "
          f"(within + cross channels)\n{SEP}", flush=True)
    t0 = time.time()
    md5_before = _seed_guard("llm_iam")

    prep, queries, lex_by_len, logfreq, rows_by_wid, within_by_wid, cross_by_wid = _load_iam_assembled()
    sent_lines = prep["sent_lines"]

    out_path = _ckpt("richlm_iam.json")
    state = _load(out_path) if os.path.exists(out_path) else {"calls": {}, "done": False}
    if state.get("done"):
        print(f"  llm_iam already COMPLETE (n_calls={len(state['calls'])}).", flush=True)
        return 0

    jobs = []
    for channel, use_within in (("within", True), ("cross", False)):
        for line in sent_lines:
            jobs.append((f"{line['line_id']}|{channel}", line, use_within))

    deadline = time.time() + PER_CALL_BUDGET_SECONDS
    n_new = 0
    for key, line, use_within in jobs:
        if key in state["calls"]:
            continue
        full = _iam_line_candidate_lists(line, rows_by_wid, within_by_wid, cross_by_wid, lex_by_len,
                                         use_within)
        shortlists = [w[:SHORTLIST_M] for w, _ in full]
        picks, meta = joint_llm_pick(shortlists)
        state["calls"][key] = {"line_id": line["line_id"], "channel": ("within" if use_within
                                else "cross"), "picks": picks, "meta": meta, "shortlists": shortlists}
        n_new += 1
        if n_new % 5 == 0:
            _save(state, out_path)
            _seed_guard("llm_iam", md5_before)
            print(f"    ... {len(state['calls'])}/{len(jobs)} calls  "
                  f"[{time.time()-t0:.1f}s]", flush=True)
        if time.time() > deadline:
            _save(state, out_path)
            _seed_guard("llm_iam", md5_before)
            print(f"  WALL-BUDGET: {len(state['calls'])}/{len(jobs)} done -- re-invoke "
                  f"--stage llm_iam to resume.", flush=True)
            return 2

    state["done"] = True
    _save(state, out_path)
    _seed_guard("llm_iam", md5_before)
    n_parse_fail = sum(1 for c in state["calls"].values() if not c["meta"]["parse_ok"])
    print(f"  llm_iam COMPLETE: {len(state['calls'])} calls, {n_parse_fail} total parse failures "
          f"(fell back to visual top-1)  [{time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  STAGE: decode_iam -- pure combine + sweep + bigram-control reproduction. No LLM calls.
# ============================================================================================= #
def stage_decode_iam():
    print(f"\n{SEP}\n  STAGE: decode_iam -- combine rich-LM picks + sweep + bigram-control "
          f"reproduction (real IAM)\n{SEP}", flush=True)
    t0 = time.time()
    md5_before = _seed_guard("decode_iam")

    prep, queries, lex_by_len, logfreq, rows_by_wid, within_by_wid, cross_by_wid = _load_iam_assembled()
    sent_lines = prep["sent_lines"]
    line_wids = sorted({wid for line in sent_lines for wid in line["wids"]})

    rl = _require("richlm_iam.json")
    if not rl.get("done"):
        raise SystemExit("WALL: llm_iam not COMPLETE -- re-invoke --stage llm_iam.")

    # -- BIGRAM CONTROL: r76's OWN `build_line_inputs` + r75's `viterbi_decode`, verbatim. --
    bigram_lm_score = r75.make_lm_scorer(prep["lm"]["unigram"], prep["lm"]["bigram"], logfreq)

    def _bigram_preds(use_within, vw):
        preds = {}
        for line in sent_lines:
            wids = line["wids"]
            cand_words, vscores, trans = r76.build_line_inputs(
                wids, rows_by_wid, within_by_wid, cross_by_wid, lex_by_len, bigram_lm_score,
                use_within)
            seq = r75.viterbi_decode(cand_words, vscores, trans, LM_WEIGHT, vw)
            for wid, p in zip(wids, seq):
                preds[wid] = p
        return preds

    def _acc(preds, wids):
        ok = sum(1 for wid in wids if preds.get(wid) == queries[wid]["word"])
        return ok / max(1, len(wids))

    bigram_within = _bigram_preds(True, PRIMARY_VISUAL_WEIGHT)
    bigram_cross = _bigram_preds(False, PRIMARY_VISUAL_WEIGHT)
    bigram_acc = {"within": _acc(bigram_within, line_wids), "cross": _acc(bigram_cross, line_wids)}
    run76_decode = _load(os.path.join(RUN76_CKPT, "decode.json"))
    control_match_within = abs(bigram_acc["within"]
                               - run76_decode["sweep"]["within"][str(PRIMARY_VISUAL_WEIGHT)]) < 1e-9
    control_match_cross = abs(bigram_acc["cross"]
                              - run76_decode["sweep"]["cross"][str(PRIMARY_VISUAL_WEIGHT)]) < 1e-9

    # -- RICH-LM arm: sweep + primary weight, within + cross channels. --
    picks_by_key = {k: v["picks"] for k, v in rl["calls"].items()}

    def _rich_preds(use_within, vw):
        channel = "within" if use_within else "cross"
        preds = {}
        for line in sent_lines:
            picks = picks_by_key[f"{line['line_id']}|{channel}"]
            for pos, wid in enumerate(line["wids"]):
                w, vscores = r76.topk_candidates_iam(
                    rows_by_wid[wid], lex_by_len, within_by_wid.get(wid, {}), cross_by_wid.get(wid, {}),
                    use_within, BEAM_K)
                w = list(w)
                pick = picks[pos] if pos < len(picks) else None
                lm_scores = rank_promoted_lm_scores(w, pick)
                preds[wid] = combine_and_argmax(w, vscores, lm_scores, vw)
        return preds

    rich_sweep = {"within": {}, "cross": {}}
    for channel, use_within in (("within", True), ("cross", False)):
        for vw in VISUAL_WEIGHTS:
            preds = _rich_preds(use_within, vw)
            rich_sweep[channel][str(vw)] = _acc(preds, line_wids)
    rich_primary = {ch: rich_sweep[ch][str(PRIMARY_VISUAL_WEIGHT)] for ch in ("within", "cross")}
    rich_best = {}
    for ch in ("within", "cross"):
        best_vw = max(VISUAL_WEIGHTS, key=lambda vw: rich_sweep[ch][str(vw)])
        rich_best[ch] = {"vw": best_vw, "acc": rich_sweep[ch][str(best_vw)]}

    n_off_list = sum(c["meta"]["n_off_list"] for c in rl["calls"].values() if c["meta"]["n_off_list"] >= 0)
    n_parse_fail = sum(1 for c in rl["calls"].values() if not c["meta"]["parse_ok"])

    out = {
        "bigram_acc": bigram_acc,
        "control_matches_run76": {"within": control_match_within, "cross": control_match_cross},
        "rich_sweep": rich_sweep, "rich_primary": rich_primary, "rich_best": rich_best,
        "n_off_list_words": n_off_list, "n_parse_fail_calls": n_parse_fail,
        "n_calls": len(rl["calls"]), "n_lines": len(sent_lines), "n_test_words_in_lines": len(line_wids),
        "stroke_shapes_md5": md5_before,
    }
    _save(out, _ckpt("decode_iam.json"))
    _seed_guard("decode_iam", md5_before)

    print(f"  bigram control reproduces run76 decode.json sweep@{PRIMARY_VISUAL_WEIGHT}: "
          f"within={control_match_within}  cross={control_match_cross}", flush=True)
    print(f"  bigram   within={100*bigram_acc['within']:.1f}%  cross={100*bigram_acc['cross']:.1f}%",
          flush=True)
    print(f"  rich-LM primary(vw={PRIMARY_VISUAL_WEIGHT})  within={100*rich_primary['within']:.1f}%"
          f"  cross={100*rich_primary['cross']:.1f}%", flush=True)
    print(f"  rich-LM best-of-sweep  within={100*rich_best['within']['acc']:.1f}%"
          f"@vw={rich_best['within']['vw']}  cross={100*rich_best['cross']['acc']:.1f}%"
          f"@vw={rich_best['cross']['vw']}", flush=True)
    print(f"  LLM off-list words={n_off_list}  parse-fail calls={n_parse_fail}/{len(rl['calls'])}",
          flush=True)
    print(f"  saved -> {_ckpt('decode_iam.json')}  [decode_iam {time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  REPORTING / VERDICT.
# ============================================================================================= #
def stage_summary():
    print(f"\n{SEP}\n  STAGE: summary -- RUN 81 SCOREBOARD (RICH LM ATTACHED TO THE READING DECODE)"
          f"\n{SEP}", flush=True)
    md5_now = _seed_guard("summary")
    probe = _require("probe.json")
    ds = _require("decode_synth.json")
    di = _require("decode_iam.json")
    print(f"  SEED-GUARD: seeds/stroke_shapes.json md5 = {md5_now}  "
          f"(== probe capture {probe['stroke_shapes_md5']}: {md5_now == probe['stroke_shapes_md5']})",
          flush=True)

    print(f"\n  STAGE 0: LM attached = {probe['rich_lm_model']}  (via local ollama)", flush=True)
    print(f"  qwen3-coder:30b unusable: {probe['known_unusable']['qwen3-coder:30b']}", flush=True)
    print(f"  rnj-1:8b unreliable here: {probe['known_unusable']['rnj-1:8b']}", flush=True)

    print(f"\n  {'SYNTHETIC (run 75 setup)':<46}{'word_acc':>10}{'vs bar':>10}", flush=True)
    print(f"  {'no-context (arm A, bar)':<46}{BAR_SYNTH_NO_CONTEXT:>9.1f}%", flush=True)
    print(f"  {'bigram + strict (arm B, bar)':<46}{BAR_SYNTH_BIGRAM_STRICT:>9.1f}%", flush=True)
    print(f"  {'bigram + loose  (arm C, bar, GOLD)':<46}{BAR_SYNTH_BIGRAM_LOOSE:>9.1f}%", flush=True)
    print(f"  {'bigram + strict (THIS RUN, reproduced)':<46}"
          f"{100*ds['bigram_reports']['B']['word_acc']:>9.1f}%  match={ds['control_matches_run75']['B']}",
          flush=True)
    print(f"  {'bigram + loose  (THIS RUN, reproduced)':<46}"
          f"{100*ds['bigram_reports']['C']['word_acc']:>9.1f}%  match={ds['control_matches_run75']['C']}",
          flush=True)
    print(f"  {'RICH-LM + strict (primary vw=2.0)':<46}"
          f"{100*ds['rich_primary']['strict']['word_acc']:>9.1f}%", flush=True)
    print(f"  {'RICH-LM + loose  (primary vw=2.0)':<46}"
          f"{100*ds['rich_primary']['loose']['word_acc']:>9.1f}%", flush=True)
    print(f"  {'RICH-LM + strict (best-of-sweep)':<46}"
          f"{100*ds['rich_best']['strict']['rep']['word_acc']:>9.1f}%  "
          f"@vw={ds['rich_best']['strict']['vw']}", flush=True)
    print(f"  {'RICH-LM + loose  (best-of-sweep)':<46}"
          f"{100*ds['rich_best']['loose']['rep']['word_acc']:>9.1f}%  "
          f"@vw={ds['rich_best']['loose']['vw']}", flush=True)
    print(f"  visual coverage ceiling loose: {ds['coverage_loose']}", flush=True)

    print(f"\n  {'REAL IAM (run 76 setup)':<46}{'word_acc':>10}", flush=True)
    print(f"  {'per-letter floor (arm A, bar)':<46}{BAR_IAM_FLOOR:>9.1f}%", flush=True)
    print(f"  {'bigram within-writer (bar)':<46}{BAR_IAM_BIGRAM_WITHIN:>9.1f}%", flush=True)
    print(f"  {'bigram within (THIS RUN, reproduced)':<46}"
          f"{100*di['bigram_acc']['within']:>9.1f}%  match={di['control_matches_run76']['within']}",
          flush=True)
    print(f"  {'bigram cross  (THIS RUN, reproduced)':<46}"
          f"{100*di['bigram_acc']['cross']:>9.1f}%  match={di['control_matches_run76']['cross']}",
          flush=True)
    print(f"  {'RICH-LM within (primary vw=2.0)':<46}{100*di['rich_primary']['within']:>9.1f}%",
          flush=True)
    print(f"  {'RICH-LM cross  (primary vw=2.0)':<46}{100*di['rich_primary']['cross']:>9.1f}%",
          flush=True)
    print(f"  {'RICH-LM within (best-of-sweep)':<46}{100*di['rich_best']['within']['acc']:>9.1f}%  "
          f"@vw={di['rich_best']['within']['vw']}", flush=True)
    print(f"  {'RICH-LM cross  (best-of-sweep)':<46}{100*di['rich_best']['cross']['acc']:>9.1f}%  "
          f"@vw={di['rich_best']['cross']['vw']}", flush=True)

    # -- verdict. --
    synth_win = (ds["rich_best"]["loose"]["rep"]["word_acc"] * 100 > BAR_SYNTH_BIGRAM_LOOSE
                and ds["rich_best"]["strict"]["rep"]["word_acc"] * 100 > BAR_SYNTH_BIGRAM_STRICT)
    iam_win = di["rich_best"]["within"]["acc"] * 100 > BAR_IAM_BIGRAM_WITHIN
    verdict = "WIN" if (synth_win and iam_win) else ("PARTIAL" if (synth_win or iam_win) else "NULL")

    out = {
        "rich_lm_model": probe["rich_lm_model"],
        "synth": {
            "bar_no_context": BAR_SYNTH_NO_CONTEXT, "bar_bigram_strict": BAR_SYNTH_BIGRAM_STRICT,
            "bar_bigram_loose": BAR_SYNTH_BIGRAM_LOOSE,
            "bigram_reproduced": {k: v["word_acc"] * 100 for k, v in ds["bigram_reports"].items()},
            "control_matches_run75": ds["control_matches_run75"],
            "rich_primary_pct": {k: v["word_acc"] * 100 for k, v in ds["rich_primary"].items()},
            "rich_best_pct": {k: v["rep"]["word_acc"] * 100 for k, v in ds["rich_best"].items()},
            "rich_best_vw": {k: v["vw"] for k, v in ds["rich_best"].items()},
            "coverage_loose": ds["coverage_loose"],
            "win": synth_win,
        },
        "iam": {
            "bar_floor": BAR_IAM_FLOOR, "bar_bigram_within": BAR_IAM_BIGRAM_WITHIN,
            "bigram_reproduced_pct": {k: v * 100 for k, v in di["bigram_acc"].items()},
            "control_matches_run76": di["control_matches_run76"],
            "rich_primary_pct": {k: v * 100 for k, v in di["rich_primary"].items()},
            "rich_best_pct": {k: v["acc"] * 100 for k, v in di["rich_best"].items()},
            "rich_best_vw": {k: v["vw"] for k, v in di["rich_best"].items()},
            "win": iam_win,
        },
        "verdict": verdict,
        "stroke_shapes_md5": md5_now,
    }
    _save(out, _ckpt("verdict.json"))
    _save(out, _ckpt("summary.json"))
    print(f"\n  VERDICT: {verdict}  (synth_win={synth_win}  iam_win={iam_win})", flush=True)
    print(f"  saved -> {_ckpt('verdict.json')}", flush=True)
    print(f"\n{SEP}\n  RUN 81 COMPLETE -- see final agent report.\n{SEP}", flush=True)
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", required=True,
                    choices=["probe", "llm_synth", "decode_synth", "llm_iam", "decode_iam", "summary"])
    args = p.parse_args()
    return {"probe": stage_probe, "llm_synth": stage_llm_synth, "decode_synth": stage_decode_synth,
            "llm_iam": stage_llm_iam, "decode_iam": stage_decode_iam,
            "summary": stage_summary}[args.stage]()


if __name__ == "__main__":
    sys.exit(main())
