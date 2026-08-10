"""jabberwock_realwordread_run64.py -- RUN 64: THE DECISIVE BEST-CASE cursive-char reading test.

THE MISSING BEST CASE of the recognizer 2x2 (see results/omniglot_gate_run63.log's own closing
diagnosis). The 2x2 crosses RECOGNIZER STRENGTH x BANK CORPUS:

    recognizer \\ bank        WITHIN-corpus (DeepWriting)     CROSS-corpus (IAM)
    weak per-stroke           run 62: 14-26% char             --
    raw whole-figure          run 63: 33% ISOLATED            run 63: 3% (chance)
    STRONG parse-marginal     >>> RUN 64 (this) <<<           --

Run 62 = weak(per-stroke) + within(DeepWriting) = 14-26% char on connected cursive.
Run 63 = raw-whole-figure + cross-corpus(IAM) = 3% (chance) connected; 33% within-corpus ISOLATED.
RUN 64 = the FULL PARSE-MARGINAL pipeline (run 16/17's 80.5% Omniglot recognizer) + WITHIN-corpus
DeepWriting connected chars. If even THIS floors (<~35% char), the training-free-exemplar-matching
wall on cursive is established honestly (a genuine donkey=0 boundary: cursive char-spans carry
ligature strokes isolated-exemplar-matching can't absorb -- this is WHY the field uses trained
sequence models). If it lifts char accuracy materially, language context can deliver real word
reading (run 61: 67% char -> 78% word) and the recognizer was the gap.

THE RECOGNIZER SWAP (lever #2 from run 63's closing note): NOT run 63's whole-figure
`SmoothDeformDist` concatenation (which corrupts multi-stroke shape). The FULL STAGED
`recognition_graph` pipeline: `abs_read.stage_parse_char` (corner-split canonical parts at a theta
grid + whole-figure AxS feature) on each character's raw points + `abs_read.parse_marginal_verdict`
(`recognition_graph.predict_smooth_marginal_sc_term` -- smoothdeform whole + part_w*marginal-part
+ sc_w*shape-context, marginalised over parse hypotheses). This is the codebook-INDEPENDENT verdict
(run 26/27's own verified fact: corner-split + SC+TPS marginalization over RAW points, no learned
codebook needed), reused VERBATIM -- this script only STAGES DeepWriting ink into it (mechanical:
each char's connected-ink strokes -> a temp Omniglot-format motor file -> the SAME `stage_parse_
char` every Family-A eval script already calls). NOTHING in abs_read/recognition_graph modified.

CORPUS: WITHIN-corpus DeepWriting (`domains.deepwriting_world`, run 62's loader). Char exemplars are
cut from CONNECTED words (soc boundaries) so the bank is CONNECTED-FORM (right for cursive, not
isolated). Cross-writer: bank exemplars from BACKGROUND writers, disjoint from the HELD-OUT test-
word writers (the SAME `writer_split` run 62 used, same seeds).

STAGE 1 -- CHAR RECOGNITION (Path 1, char segmentation GIVEN -- THE DECISIVE RECOGNIZER NUMBER):
  26-way (lowercase a-z, the actual label space of the lowercase words) closed-set char accuracy on
  within-corpus DeepWriting connected chars, cross-writer, n>=300 chars, with parse-marginal.
  Bank staged ONCE (M exemplars/class as Concept candidates); each query char staged as a Mark;
  `parse_marginal_verdict`'s held Argmax picks the winning candidate -> its class. Headline:
  does parse-marginal MATERIALLY beat run 62's 14% and run 63's 33% on connected cursive?

STAGE 2 -- WORD READING (only if STAGE 1 char acc > 35%): per-char parse-marginal 62-class error
  vector (`parse_marginal_pair_error`, min over each class's exemplars) -> run 61 lexicon-collapse,
  no-context vs context, n>=200 words. Contingent: if STAGE 1 floors, the visual channel proposes
  chance and there is nothing for the (validated) reading machinery to collapse -- STAGE 2 is moot.

donkey=0: parse-marginal is one-shot geometry (no trained net); the lexicon is read-only Brown+
WordNet count data. SEED GUARD: OZMA_SEED_PERSIST_DISABLED=1; every stage asserts
md5(seeds/stroke_shapes.json) UNCHANGED before+after.

Stages: prep -> recognize_char -> summary   (STAGE 2: decode_words, gated on STAGE 1 clearing).
Run:
  OZMA_SEED_PERSIST_DISABLED=1 DEEPWRITING_DIR=/tmp/handwriting PYTHONPATH=.:runners/dsl/python \\
    /home/matt/ozma/internal/research/.venv/bin/python3 scripts/jabberwock_realwordread_run64.py --stage <S>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import tempfile
import time
from collections import Counter, defaultdict

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
os.environ.setdefault("DEEPWRITING_DIR", "/tmp/handwriting")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np

import scripts.jabberwock_wordread_run61 as r61
import scripts.jabberwock_realwordread_run62 as r62
from domains import deepwriting_world as dww

SEP = "=" * 92
CKPT_DIR = os.path.join(ROOT, "results", "run64_checkpoints")
os.makedirs(CKPT_DIR, exist_ok=True)
STROKE_SHAPES_SEED = os.path.join(ROOT, "seeds", "stroke_shapes.json")
SYMBOLS = dww.CANON_SYMBOLS                    # == DIGILETS order; run61 decoders use this order.

# ------------------------------------------------------------------------------------------- #
#  PRE-REGISTERED CONSTANTS (bank/split seeds byte-identical to run 62).
# ------------------------------------------------------------------------------------------- #
SPLIT = "training"                 # the large split (34.5k samples, 207 writers with words).
WRITER_SPLIT_SEED = 20260706
N_BACKGROUND_FRAC = 0.5            # half the writers -> bank exemplars; other half -> test words.
BANK_M = 3                        # exemplars per class (== run 62/63).
BANK_SEED = 20260711
N_TEST = 240                      # test words (>= 200 pre-reg).
WORD_SELECT_SEED = 20260712
WORD_MIN_LEN, WORD_MAX_LEN = 3, 8

# STAGE 1 -- 26-way lowercase (the actual label space of the lowercase test words). Chance = 3.85%.
LOWER_CLASSES = list(range(10, 36))      # canonical 62-class ids for 'a'..'z'.
N_TEST_CHARS = 400                       # decisive-recognizer char sample (>= 300 pre-reg).

# Parse-marginal recipe = abs_read's own defaults (run 17b's 80.5% Omniglot recipe): theta grid
# (55, 70, 85), part_w 0.25, sc_w 1.6, beta 2.0. Not overridden -- the strongest verdict, verbatim.

FREQ_PRIOR_ALPHA = 0.0            # PRIMARY lexicon arm: flat (uniform over valid words).

# Pre-registered WIN/FLOOR threshold on the DECISIVE char-accuracy number.
FLOOR_CHAR_ACC = 0.35            # STAGE 1 must clear this for parse-marginal to be a WIN and for
                                  # STAGE 2 (word reading) to be worth running.

PER_CALL_BUDGET_SECONDS = 450.0
INF = math.inf


# ------------------------------------------------------------------------------------------- #
#  I/O + seed guard.
# ------------------------------------------------------------------------------------------- #
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
    return r61._wilson_ci(k, n)


# ------------------------------------------------------------------------------------------- #
#  MECHANICAL: DeepWriting connected-ink strokes -> a temp Omniglot-format motor file, so the
#  SAME `abs_read.stage_parse_char` (which reads a path via `omniglot_world.load_strokes` +
#  `.trajectory`) every Family-A eval script already calls can stage it, verbatim. Pure host I/O
#  (START header, BREAK-separated strokes, "x,y" per point) -- no decision, no graph state.
# ------------------------------------------------------------------------------------------- #
def write_omni_file(strokes, path):
    """Serialise a list of (m_i, 2) point arrays to Omniglot motor format (the format
    `omniglot_world.load_strokes` parses: 'START', 'BREAK'-separated strokes, 'x,y' per point)."""
    with open(path, "w") as f:
        f.write("START\n")
        for si, s in enumerate(strokes):
            if si:
                f.write("BREAK\n")
            for p in np.asarray(s, float).reshape(-1, 2):
                f.write(f"{float(p[0])},{float(p[1])}\n")


# ============================================================================================= #
#  STAGE: prep -- DeepWriting load, cross-writer split, test words + bank glyph pool.
#  (Mirrors run 62's own prep exactly; the only new output is that per-char queries are also the
#   STAGE-1 recognition units. Written to run64_checkpoints -- run62_checkpoints stays read-only.)
# ============================================================================================= #
def stage_prep():
    print(f"\n{SEP}\n  STAGE: prep (DeepWriting load + cross-writer split + word selection)\n{SEP}")
    t0 = time.time()
    md5_before = _seed_guard("prep")
    print(f"  seeds/stroke_shapes.json md5 (before): {md5_before}")

    lex, logfreq, brown_counts = r62._build_lexicon()
    lexset = set(lex)
    print(f"  lexicon (Brown+WordNet, len {WORD_MIN_LEN}-{WORD_MAX_LEN}) = {len(lex)}  "
          f"[{time.time()-t0:.1f}s]", flush=True)

    dw = dww.load_deepwriting(SPLIT)
    print(f"  DeepWriting '{SPLIT}': {dw['n']} samples  [{time.time()-t0:.1f}s]", flush=True)
    words = dww.extract_words(dw, min_len=WORD_MIN_LEN, max_len=WORD_MAX_LEN,
                              lowercase_only=True, complete_only=True, lexicon=lexset)
    glyphs = dww.extract_char_glyphs(dw)
    print(f"  complete in-lex words = {len(words)} (writers "
          f"{len({w['writer'] for w in words})});  char glyphs = {len(glyphs)}  "
          f"[{time.time()-t0:.1f}s]", flush=True)

    # cross-writer split: background writers -> bank; held-out writers -> test words.
    bg_words, ho_words = dww.writer_split(words, n_background_frac=N_BACKGROUND_FRAC,
                                          seed=WRITER_SPLIT_SEED)
    bg_writers = {w["writer"] for w in bg_words}
    ho_writers = {w["writer"] for w in ho_words}
    # bank glyphs come from BACKGROUND writers ONLY (disjoint from test-word writers), lowercase.
    bank_glyphs = [g for g in glyphs
                   if g["writer"] in bg_writers and g["class"] in set(LOWER_CLASSES)]
    print(f"  bank writers={len(bg_writers)}  test-word writers={len(ho_writers)}  "
          f"disjoint={bg_writers.isdisjoint(ho_writers)}  lowercase bank glyphs={len(bank_glyphs)}",
          flush=True)

    # select N_TEST test words from held-out writers (seeded shuffle).
    rng = np.random.default_rng(WORD_SELECT_SEED)
    order = rng.permutation(len(ho_words))
    sel = [ho_words[int(i)] for i in order[:N_TEST]]
    print(f"  selected test words: {len(sel)}  len-dist="
          f"{sorted(Counter(len(w['word']) for w in sel).items())}", flush=True)
    print(f"  sample: {[w['word'] for w in sel[:24]]}")

    def _ser_word(w):
        return {"writer": w["writer"], "word": w["word"], "sample": w["sample"],
                "char_segs": [{"class": c["class"], "symbol": c["symbol"],
                               "strokes": [np.asarray(s, float)[:, :2].tolist() for s in c["strokes"]]}
                              for c in w["char_segs"]]}

    out = {"lexicon": lex, "logfreq": logfreq,
           "brown_unigram": {w: int(brown_counts[w]) for w in lex if w in brown_counts},
           "test_words": [_ser_word(w) for w in sel],
           "bank_glyph_pool": [{"writer": g["writer"], "class": g["class"],
                                "strokes": [np.asarray(s, float)[:, :2].tolist() for s in g["strokes"]]}
                               for g in bank_glyphs],
           "bank_writers": sorted(bg_writers), "test_writers": sorted(ho_writers),
           "stroke_shapes_md5": md5_before}
    _save(out, _ckpt("prep.json"))
    _seed_guard("prep", md5_before)
    # report total available query chars
    n_chars = sum(len(w["char_segs"]) for w in out["test_words"])
    print(f"  total query chars available (all lowercase) = {n_chars}", flush=True)
    print(f"  saved -> {_ckpt('prep.json')}  [prep {time.time()-t0:.1f}s]")
    return 0


# ------------------------------------------------------------------------------------------- #
#  Bank staging (deterministic): M exemplars per lowercase class from the background pool. Each
#  exemplar -> a temp Omniglot file -> a `stage_parse_char` candidate Concept, `name`=its class.
#  Staged ONCE per invocation into one fresh scratch substrate (the parse-marginal Argmax scans
#  every Concept{is_word:1}); a query Mark is added per char, evaluated, its winner's `name` read.
# ------------------------------------------------------------------------------------------- #
def _select_bank(pool):
    """Deterministic M-exemplar-per-lowercase-class selection (seeded). Returns
    {class: [strokes,...]}."""
    by_class = defaultdict(list)
    for g in pool:
        if g["class"] in set(LOWER_CLASSES):
            by_class[g["class"]].append(g)
    rng = np.random.default_rng(BANK_SEED)
    bank = {}
    for c in LOWER_CLASSES:
        insts = by_class.get(c, [])
        if not insts:
            bank[c] = []
            continue
        idx = rng.choice(len(insts), size=min(BANK_M, len(insts)), replace=False)
        bank[c] = [insts[int(i)]["strokes"] for i in idx]
    return bank


def _stage_bank(scratch, bank, tmpdir, ar):
    """Stage every bank exemplar as a candidate Concept; returns {node_id: class}. Also returns
    a class->[node_id] index for the per-class pair-error read-off (STAGE 2)."""
    node2class = {}
    class2nodes = defaultdict(list)
    for c in LOWER_CLASSES:
        for j, strokes in enumerate(bank[c]):
            p = os.path.join(tmpdir, f"bank_{c}_{j}.txt")
            write_omni_file(strokes, p)
            node = ar.stage_parse_char(scratch, p, is_query=False, name=str(c))
            node2class[node] = c
            class2nodes[c].append(node)
    return node2class, dict(class2nodes)


def _query_units(test_words):
    """Flatten test words into per-char query units (in word/char order). Each unit carries the
    strokes, true class, source word + char index + writer -- the STAGE-1 recognition units."""
    units = []
    for wi, w in enumerate(test_words):
        for ci, cs in enumerate(w["char_segs"]):
            units.append({"qid": len(units), "word": w["word"], "writer": w["writer"],
                          "wi": wi, "char_idx": ci, "true_class": cs["class"],
                          "strokes": cs["strokes"]})
    return units


# ============================================================================================= #
#  STAGE: recognize_char -- THE DECISIVE STAGE. 26-way parse-marginal char accuracy on connected
#  cursive, cross-writer, given segmentation. Block-checkpointed + resumable.
# ============================================================================================= #
def stage_recognize_char():
    print(f"\n{SEP}\n  STAGE: recognize_char (26-way PARSE-MARGINAL char accuracy, connected "
          f"cursive)\n{SEP}")
    t0 = time.time()
    md5_before = _seed_guard("recognize_char")
    import substrate_rs as srs
    from domains import abs_read as ar
    prep = _require("prep.json")

    bank = _select_bank(prep["bank_glyph_pool"])
    n_bank = sum(len(v) for v in bank.values())
    empty = [SYMBOLS[c] for c in LOWER_CLASSES if not bank[c]]
    print(f"  bank: {n_bank} exemplars over {len(LOWER_CLASSES)} lowercase classes "
          f"(M={BANK_M})  empty classes: {empty}", flush=True)

    units = _query_units(prep["test_words"])[:N_TEST_CHARS]
    print(f"  query chars (given seg, cross-writer): {len(units)}  "
          f"true-class dist top: "
          f"{Counter(SYMBOLS[u['true_class']] for u in units).most_common(8)}", flush=True)

    out_path = _ckpt("recognize_char.json")
    state = _load(out_path) if os.path.exists(out_path) else {"records": [], "done": False}
    if state.get("done"):
        print(f"  recognize_char already COMPLETE (n={len(state['records'])}).")
        _report_char(state)
        return 0
    done_ids = {r["qid"] for r in state["records"]}

    tmpdir = tempfile.mkdtemp(prefix="run64_")
    scratch = srs.Substrate()
    node2class, _ = _stage_bank(scratch, bank, tmpdir, ar)
    print(f"  bank staged: {len(node2class)} candidate Concepts  [{time.time()-t0:.1f}s]",
          flush=True)

    qp = os.path.join(tmpdir, "query.txt")
    deadline = time.time() + PER_CALL_BUDGET_SECONDS
    n_new = 0
    for u in units:
        if u["qid"] in done_ids:
            continue
        write_omni_file(u["strokes"], qp)
        qn = ar.stage_parse_char(scratch, qp, is_query=True)
        w = ar.parse_marginal_verdict(scratch, qn)
        pred = node2class.get(w, -1) if w is not None else -1
        state["records"].append({"qid": u["qid"], "true_class": u["true_class"],
                                  "pred_class": int(pred), "word": u["word"],
                                  "writer": u["writer"], "char_idx": u["char_idx"]})
        n_new += 1
        if n_new % 40 == 0:
            _save(state, out_path)
            _seed_guard("recognize_char", md5_before)
            k = sum(1 for r in state["records"] if r["pred_class"] == r["true_class"])
            print(f"    ... {len(state['records'])}/{len(units)}  running char_acc="
                  f"{100*k/len(state['records']):.1f}%  [{time.time()-t0:.1f}s]", flush=True)
            if time.time() > deadline:
                _save(state, out_path)
                print(f"  WALL-BUDGET: {len(state['records'])}/{len(units)} done -- "
                      f"re-invoke --stage recognize_char to resume.", flush=True)
                _seed_guard("recognize_char", md5_before)
                return 2

    state["done"] = True
    _save(state, out_path)
    _seed_guard("recognize_char", md5_before)
    print(f"  recognized {len(state['records'])} chars  [{time.time()-t0:.1f}s]", flush=True)
    _report_char(state)
    return 0


def _report_char(state):
    recs = state["records"]
    n = len(recs)
    k = sum(1 for r in recs if r["pred_class"] == r["true_class"])
    acc = k / n if n else 0.0
    ci = _wilson(k, n)
    # per-class recall (top confusions)
    per_class = defaultdict(lambda: [0, 0])
    conf = Counter()
    for r in recs:
        per_class[r["true_class"]][1] += 1
        if r["pred_class"] == r["true_class"]:
            per_class[r["true_class"]][0] += 1
        else:
            conf[(SYMBOLS[r["true_class"]],
                  SYMBOLS[r["pred_class"]] if r["pred_class"] >= 0 else "?")] += 1
    print(f"\n  === STAGE 1: CHAR RECOGNITION (parse-marginal, 26-way, connected cursive) ===")
    print(f"  n={n}  char_acc={100*acc:.1f}%  95% CI [{100*ci[0]:.1f}, {100*ci[1]:.1f}]  "
          f"(chance 3.85%)")
    print(f"  COMPARISON: run 62 per-stroke ~14% | run 63 raw whole-figure 33% (ISOLATED) | "
          f"run 16/17 Omniglot 80.5%")
    verdict = "WIN (parse-marginal clears the cursive floor)" if acc > FLOOR_CHAR_ACC else \
              "FLOOR (parse-marginal ALSO floors on connected cursive)"
    print(f"  -> STAGE-1 VERDICT (threshold {100*FLOOR_CHAR_ACC:.0f}%): {verdict}")
    # a few per-class recalls + top confusions for the honest picture
    best = sorted(((v[0] / v[1], SYMBOLS[c], v[0], v[1]) for c, v in per_class.items() if v[1] >= 3),
                  reverse=True)[:6]
    print(f"  best per-class recall (>=3 samples): "
          + ", ".join(f"{s}:{100*a:.0f}%({k}/{t})" for a, s, k, t in best))
    print(f"  top confusions (true->pred): "
          + ", ".join(f"{a}->{b}:{n_}" for (a, b), n_ in conf.most_common(8)))
    return acc


# ============================================================================================= #
#  STAGE 2: decode_words -- per-char parse-marginal 62-class error vector (min over each class's
#  exemplars, via parse_marginal_pair_error) -> run 61 lexicon-collapse. GATED: only meaningful if
#  STAGE 1 cleared the floor. Block-checkpointed + resumable.
# ============================================================================================= #
def _char_error_vector(scratch, qn, class2nodes, ar):
    """62-length error vector: entry[c] = min over class c's exemplars of parse_marginal_pair_error
    (lower = better geometric fit); non-lowercase classes get a large sentinel so run 61's argmin/
    lexicon decoders (which only read lowercase indices 10..35) behave. LOWER is better -> matches
    run 61's DISTANCE convention (decode_no_context argmin, decode_lexicon summed-min)."""
    vec = [1e6] * 62
    for c in LOWER_CLASSES:
        best = INF
        for node in class2nodes.get(c, []):
            e = ar.parse_marginal_pair_error(scratch, qn, node)
            if e < best:
                best = e
        vec[c] = float(best if best != INF else 1e6)
    return vec


def stage_decode_words(force=False):
    print(f"\n{SEP}\n  STAGE: decode_words (STAGE 2 -- lexicon-collapse word reading)\n{SEP}")
    t0 = time.time()
    md5_before = _seed_guard("decode_words")
    prep = _require("prep.json")
    rc = _require("recognize_char.json")
    if not rc.get("done"):
        print("  WALL: recognize_char not COMPLETE -- run STAGE 1 to completion first.")
        return 1
    s1 = _report_char(rc)
    if s1 <= FLOOR_CHAR_ACC and not force:
        print(f"\n  STAGE-1 FLOORED ({100*s1:.1f}% <= {100*FLOOR_CHAR_ACC:.0f}%): the visual "
              f"channel proposes chance, so lexicon-collapse has nothing to collapse. STAGE 2 is "
              f"MOOT (run 63's own finding). Skipping (pass --force to run anyway).")
        _seed_guard("decode_words", md5_before)
        return 0

    import substrate_rs as srs
    from domains import abs_read as ar
    lexicon = prep["lexicon"]
    logfreq = prep["logfreq"]
    lex_by_len = r61._lex_by_len(lexicon)
    bank = _select_bank(prep["bank_glyph_pool"])

    out_path = _ckpt("decode_words.json")
    state = _load(out_path) if os.path.exists(out_path) else {"per_word": [], "done": False}
    if state.get("done"):
        print(f"  decode_words already COMPLETE (n={len(state['per_word'])}).")
        _report_words(state)
        return 0
    done_wi = {d["wi"] for d in state["per_word"]}

    tmpdir = tempfile.mkdtemp(prefix="run64d_")
    scratch = srs.Substrate()
    _, class2nodes = _stage_bank(scratch, bank, tmpdir, ar)
    print(f"  bank staged for pair-error read-off  [{time.time()-t0:.1f}s]", flush=True)

    qp = os.path.join(tmpdir, "query.txt")
    deadline = time.time() + PER_CALL_BUDGET_SECONDS
    words = prep["test_words"]
    n_new = 0
    for wi, w in enumerate(words):
        if wi in done_wi:
            continue
        dists = []
        for cs in w["char_segs"]:
            write_omni_file(cs["strokes"], qp)
            qn = ar.stage_parse_char(scratch, qp, is_query=True)
            dists.append(_char_error_vector(scratch, qn, class2nodes, ar))
        nc = r61.decode_no_context(dists, SYMBOLS)
        lx = r61.decode_lexicon(dists, len(w["word"]), lex_by_len, logfreq, FREQ_PRIOR_ALPHA)
        state["per_word"].append({"wi": wi, "word": w["word"], "no_context": nc, "lexicon": lx})
        n_new += 1
        if n_new % 10 == 0:
            _save(state, out_path)
            _seed_guard("decode_words", md5_before)
            print(f"    ... {len(state['per_word'])}/{len(words)}  [{time.time()-t0:.1f}s]",
                  flush=True)
            if time.time() > deadline:
                _save(state, out_path)
                print(f"  WALL-BUDGET: {len(state['per_word'])}/{len(words)} done -- re-invoke.",
                      flush=True)
                _seed_guard("decode_words", md5_before)
                return 2

    state["done"] = True
    _save(state, out_path)
    _seed_guard("decode_words", md5_before)
    _report_words(state)
    return 0


def _char_acc(pred, true):
    n = min(len(pred), len(true))
    return sum(1 for i in range(n) if pred[i] == true[i]), len(true)


def _report_words(state):
    pw = state["per_word"]
    n = len(pw)
    nc_w = sum(1 for d in pw if d["no_context"] == d["word"])
    lx_w = sum(1 for d in pw if d["lexicon"] == d["word"])
    nc_c = lx_c = tot_c = 0
    nc_flags, lx_flags = [], []
    for d in pw:
        a, t = _char_acc(d["no_context"], d["word"])
        b, _ = _char_acc(d["lexicon"], d["word"])
        nc_c += a
        lx_c += b
        tot_c += t
        nc_flags.append(d["no_context"] == d["word"])
        lx_flags.append(d["lexicon"] == d["word"])
    print(f"\n  === STAGE 2: WORD READING (parse-marginal + lexicon, n={n} words) ===")
    hdr = f"  {'reader':<34}{'word_acc':>11}{'word_CI':>16}{'char_acc':>11}"
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))

    def row(lab, kw, kc):
        ci = _wilson(kw, n)
        print(f"  {lab:<34}{100*kw/n if n else 0:>9.1f}%"
              f"{f'[{100*ci[0]:.1f},{100*ci[1]:.1f}]':>16}{100*kc/tot_c if tot_c else 0:>9.1f}%")
    row("no-context (per-char argmin)", nc_w, nc_c)
    row("LEXICON-COLLAPSE", lx_w, lx_c)
    mc = r61._mcnemar(nc_flags, lx_flags)
    print(f"  McNemar (lexicon vs no-context): fixed={mc['fixed']} broken={mc['broken']} "
          f"p={mc['p']:.3g}")


# ============================================================================================= #
#  STAGE: summary
# ============================================================================================= #
def stage_summary():
    print(f"\n{SEP}\n  STAGE: summary -- RUN 64 SCOREBOARD (DECISIVE CURSIVE CHAR READING)\n{SEP}")
    md5_now = _seed_guard("summary")
    prep = _require("prep.json")
    print(f"\n  SEED-GUARD: seeds/stroke_shapes.json md5 = {md5_now}  "
          f"(== prep capture {prep['stroke_shapes_md5']}: {md5_now == prep['stroke_shapes_md5']})")
    rc = _require("recognize_char.json")
    s1 = _report_char(rc)
    dp = _ckpt("decode_words.json")
    if os.path.exists(dp):
        st = _load(dp)
        if st.get("done"):
            _report_words(st)
    print(f"\n  THE 2x2 (recognizer strength x bank corpus):")
    print(f"    weak per-stroke  + within (run 62 DeepWriting):   14-26% char")
    print(f"    raw whole-figure + within (run 63 ISOLATED):      33% char")
    print(f"    raw whole-figure + cross  (run 63 IAM):           ~3% char (chance)")
    print(f"    STRONG parse-marginal + within (RUN 64):          {100*s1:.1f}% char  <<< THIS")
    print(f"\n{SEP}\n  RUN 64 COMPLETE -- see final agent report.\n{SEP}")
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", required=True,
                   choices=["prep", "recognize_char", "decode_words", "summary"])
    p.add_argument("--force", action="store_true", help="run decode_words even if STAGE 1 floored")
    args = p.parse_args()
    if args.stage == "prep":
        return stage_prep()
    if args.stage == "recognize_char":
        return stage_recognize_char()
    if args.stage == "decode_words":
        return stage_decode_words(force=args.force)
    if args.stage == "summary":
        return stage_summary()
    return 1


if __name__ == "__main__":
    sys.exit(main())
