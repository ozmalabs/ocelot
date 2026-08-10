"""jabberwock_wordread_run61.py -- RUN 61: LANGUAGE-CONTEXT WORD READING (the pivot to the real
goal -- read handwriting at human-equivalent level).

THE THESIS: human-level handwriting READING is context-driven. Isolated-character recognition
(this arc's 20-way ceiling, homoglyph-capped -- run 48/56/57) is NOT the human bottleneck; humans
read WORDS with LANGUAGE CONTEXT (a lexicon / word-frequency prior), which resolves the
homoglyph / near-duplicate ambiguity that geometry ALONE cannot. This run TESTS whether language
context closes the gap between per-character accuracy and human-level WORD reading.

THE MECHANISM (this arc's own two-model / context-prior thread, memory `two_model_communication`):
a LEXICON is a PEAKED MESSAGE PRIOR over letter sequences -- exactly the Bayesian-listener prior
that resolved shared-context communication. The visual channel (the character geometry recognizer)
carries the per-character posterior WITH ITS UNCERTAINTY; the lexicon prior re-weights the whole
word. "Bins propose, continuous decides" (run 16) at the WORD level: geometry proposes per-char
candidates, LANGUAGE decides the word.

REUSE (this arc's convention -- run 45 importing run 44b, run 48 importing run 47):
  * `domains.pen_world.load_digilets_samples` / `digilets_writer_split` -- the DigiLeTs pen corpus
    (77 writers x 62 classes x 5 instances, from run 48).
  * `scripts.jabberwock_omniglot_run47_pendata.ps.program_score` -- the per-stroke SC+TPS geometry
    verdict (the run 56 "GUARD"/strong continuous recognizer). `_stroke_point_sets_from_arrays`
    for the mechanical stroke->point-set adapter. NOTHING in run 47/48 is modified.

CHARACTER RECOGNIZER (visual channel, one-shot-bank): a cross-writer EXEMPLAR BANK of M instances
per class is drawn from the BACKGROUND writers; a query glyph is scored (`program_score`, LOWER =
better) against every bank exemplar, per-class distance = min over that class's exemplars. The
per-char distance vector over all 62 classes IS the visual posterior (with its uncertainty). The
candidate alphabet is the FULL 62 classes (digits + both letter cases) ON PURPOSE -- that is what
makes homoglyph confusion possible: a lowercase 'o' query is near-tied with 'O'/'0', a lowercase
'l' with 'I'/'1', 's' with 'S'/'5' -- the geometry cannot break these ties in isolation.

WORDS (synthetic composition, stated plainly): each test word is composed as a SEQUENCE of REAL
DigiLeTs lowercase glyph instances, one per letter, all sampled from a SINGLE held-out WORD WRITER
(disjoint from the bank writers -- genuine cross-writer). This SKIPS cursive segmentation (a
separate, solved-in-principle problem): each character is a pre-segmented glyph and the word length
is known. The simplification isolates the CONTEXT question -- it does NOT model joined cursive ink.
Words are drawn from the corpus's most-frequent common words (Brown), so they are IN-VOCABULARY
(OOV reading is a separate concern, stated).

TWO READERS on the SAME words, the SAME per-char distances:
  (A) NO-CONTEXT: per-character argmin over all 62 classes -> word. (Isolated-char baseline
      extended to words; expected LOW ~ per_char_acc^word_len, and homoglyph-capped.)
  (B) WITH-CONTEXT (lexicon, the peaked prior): over LEXICON words of the SAME length, choose the
      one minimizing summed per-char distance (optionally + a Brown unigram-frequency prior). The
      lexicon is over LOWERCASE words, so the decode is intrinsically constrained to lowercase
      sequences -> it RESOLVES the case/digit homoglyph ambiguity geometry cannot.
  (B') WITH-CONTEXT (open-vocab char-bigram LM): a softer middle -- Viterbi over 62 classes with a
      Brown character-bigram transition. Open-vocabulary context, NO lexicon constraint. Isolates
      "any language model helps" from "the lexicon constraint helps".

LEXICON / LM SOURCE (donkey=0 -- NO trained neural LM): WordNet lowercase alphabetic lemma names
(~77k) UNION the Brown vocabulary = the decode search space; Brown unigram counts = the frequency
prior + the source of the "most-frequent N words" test set; Brown character bigrams = the char-LM.
All count-based, offline, mechanical -- no neural language model anywhere.

MEASURE (the table FIRST): word accuracy + character accuracy, NO-CONTEXT vs WITH-CONTEXT. THE KEY
QUESTION: does context DRAMATICALLY lift word accuracy, and specifically -- of the isolated-char
errors that are HOMOGLYPH/near-duplicate confusions, what fraction does in-word context FIX?
PRE-REGISTERED: context is VALIDATED (a WIN) if WITH-CONTEXT (lexicon) word accuracy is >= 2x
NO-CONTEXT word accuracy AND >= 50% of the NO-CONTEXT homoglyph char-errors are resolved. A NULL
(the per-char recognizer too weak even for lexicon rescue, or the composition unrealistic) is
reported as such, with which cause.

SEED GUARD (this arc's binding rule): `OZMA_SEED_PERSIST_DISABLED=1` at import; every stage asserts
md5(seeds/stroke_shapes.json) UNCHANGED before AND after. This run WRITES no seeds and TRAINS
nothing -- the recognizer is one-shot geometry, the lexicon is read-only count data.

EXECUTION (ops law, binding): every invocation <=540s FOREGROUND, checkpointed under
`results/run61_checkpoints/` (every other `results/run*_checkpoints/` is READ-ONLY reference;
parallel-session files untouched). `.venv` python for stages needing `substrate_rs` (recognize);
system `python3` fine for pure stages (build_lexicon, decode, summary, unit tests). NEVER run in
background; NEVER end a turn with a live process.

Run (from the gamma-substrate repo root):
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python3 \\
      scripts/jabberwock_wordread_run61.py --stage <STAGE>
Stages, in dependency order:
  build_lexicon -> bank -> recognize -> decode -> summary
  (build_lexicon/decode/summary are pure-python; bank/recognize need substrate_rs.)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time
from collections import Counter, defaultdict

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np

SEP = "=" * 92
EPS = 1e-9
CKPT_DIR = os.path.join(ROOT, "results", "run61_checkpoints")
os.makedirs(CKPT_DIR, exist_ok=True)
STROKE_SHAPES_SEED = os.path.join(ROOT, "seeds", "stroke_shapes.json")

# ------------------------------------------------------------------------------------------- #
# PRE-REGISTERED CONSTANTS (stated before any number is computed).
# ------------------------------------------------------------------------------------------- #
N_BACKGROUND_WRITERS = 38          # bank (exemplar) writers; the other 39 are WORD writers, disjoint.
WRITER_SPLIT_SEED = 20260706
BANK_M = 3                         # exemplars per class in the cross-writer bank.
BANK_SEED = 20260711
N_WORDS = 300                      # test words.
WORD_MIN_LEN, WORD_MAX_LEN = 3, 8
WORD_SELECT_SEED = 20260712
WORD_WRITER_SEED = 20260713
FREQ_PRIOR_ALPHA = 0.0             # PRIMARY lexicon arm: FLAT lexicon (uniform over valid words) --
                                   # the cleanest "peaked prior = uniform over the lexicon". A
                                   # frequency-weighted arm (alpha>0) is reported alongside.
FREQ_PRIOR_ALPHA_WEIGHTED = 1.0    # secondary arm: + Brown unigram log-frequency prior.

# WIN thresholds (pre-registered).
WIN_WORD_ACC_RATIO = 2.0           # WITH-CONTEXT word acc >= 2x NO-CONTEXT word acc.
WIN_HOMOGLYPH_RESOLVED = 0.50      # >= 50% of NO-CONTEXT homoglyph char-errors resolved.

# HOMOGLYPH GROUPS -- reproduced VERBATIM from run 48 (`HOMOGLYPH_GROUPS`), the authoritative
# definition for this corpus: pairs intrinsically confusable IN ISOLATION even for a human.
HOMOGLYPH_GROUPS = [
    ("0", "O", "o"), ("1", "l", "I"), ("2", "Z", "z"), ("5", "S", "s"),
    ("6", "G"), ("8", "B"), ("9", "g", "q"),
    ("c", "C"), ("k", "K"), ("p", "P"), ("u", "U"), ("v", "V"), ("w", "W"), ("x", "X"),
]
SYMBOL_TO_HG = {sym: gid for gid, grp in enumerate(HOMOGLYPH_GROUPS) for sym in grp}


def _is_homoglyph_pair(a: str, b: str) -> bool:
    ga, gb = SYMBOL_TO_HG.get(a), SYMBOL_TO_HG.get(b)
    return ga is not None and ga == gb


# ------------------------------------------------------------------------------------------- #
# Symbol <-> class maps (DIGILETS_SYMBOLS = [0-9] + [a-z] + [A-Z]).
# ------------------------------------------------------------------------------------------- #
def _sym_maps():
    from domains import pen_world as pw
    sym2c = {pw.DIGILETS_SYMBOLS[c]: c for c in range(62)}
    return pw.DIGILETS_SYMBOLS, sym2c


def _lower_class(ch: str) -> int:
    """Class id of a lowercase letter 'a'..'z' -> 10..35."""
    return 10 + (ord(ch) - ord("a"))


# ------------------------------------------------------------------------------------------- #
# I/O + seed guard.
# ------------------------------------------------------------------------------------------- #
def _md5(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def _ckpt(name: str) -> str:
    return os.path.join(CKPT_DIR, name)


def _save_json(obj, path: str) -> None:
    with open(path, "w") as f:
        json.dump(obj, f)


def _load_json(path: str):
    with open(path) as f:
        return json.load(f)


def _seed_guard(stage: str, before: str | None = None) -> str:
    cur = _md5(STROKE_SHAPES_SEED)
    if before is not None and cur != before:
        raise SystemExit(f"HARD STOP: seeds/stroke_shapes.json md5 changed during {stage} "
                         f"({before} -> {cur}).")
    return cur


def _wilson_ci(k: int, n: int, z: float = 1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def _mcnemar(a_correct: list, b_correct: list) -> dict:
    """b vs a: fixed = a wrong & b right; broken = a right & b wrong."""
    fixed = sum(1 for ca, cb in zip(a_correct, b_correct) if (not ca) and cb)
    broken = sum(1 for ca, cb in zip(a_correct, b_correct) if ca and (not cb))
    n = fixed + broken
    # exact binomial two-sided p under 0.5.
    if n == 0:
        p = 1.0
    else:
        from math import comb
        k = min(fixed, broken)
        p = min(1.0, 2.0 * sum(comb(n, i) for i in range(0, k + 1)) / (2 ** n))
    return {"fixed": fixed, "broken": broken, "p": p}


# ============================================================================================= #
#  STAGE: build_lexicon -- WordNet + Brown -> lexicon, frequency prior, char bigram, test words.
# ============================================================================================= #
def _load_brown_counts() -> Counter:
    from nltk.corpus import brown
    return Counter(w.lower() for w in brown.words() if w.isalpha())


def _load_wordnet_lemmas() -> set:
    from nltk.corpus import wordnet as wn
    return {l for l in wn.all_lemma_names() if l.isalpha() and l.islower()}


def stage_build_lexicon():
    print(f"\n{SEP}\n  STAGE: build_lexicon (WordNet + Brown, donkey=0 count-based)\n{SEP}")
    t0 = time.time()
    md5_before = _seed_guard("build_lexicon")
    print(f"  seeds/stroke_shapes.json md5 (before): {md5_before}")

    brown = _load_brown_counts()
    wn_lemmas = _load_wordnet_lemmas()
    # LEXICON = lowercase alpha words from either source, length in [MIN, wider cap for decode].
    lex = {w for w in (set(brown) | wn_lemmas)
           if w.isalpha() and w.islower() and WORD_MIN_LEN <= len(w) <= WORD_MAX_LEN}
    print(f"  brown vocab={len(brown)}  wordnet lemmas={len(wn_lemmas)}  "
          f"lexicon(len {WORD_MIN_LEN}-{WORD_MAX_LEN})={len(lex)}  [{time.time()-t0:.1f}s]")

    # Frequency prior (Brown unigram, add-1 smoothed; words absent from Brown get the floor).
    total = sum(brown.values())
    logfreq = {w: math.log((brown.get(w, 0) + 1) / (total + len(lex))) for w in lex}

    # Character-bigram LM from Brown (over lowercase words, with ^/$ boundaries).
    bigram = Counter()
    unigram = Counter()
    for w, c in brown.items():
        if not (w.isalpha() and w.islower()):
            continue
        s = "^" + w + "$"
        for i in range(len(s) - 1):
            bigram[(s[i], s[i + 1])] += c
            unigram[s[i]] += c

    # Test words: most-FREQUENT Brown words of the right length, IN lexicon. Bias to include
    # homoglyph-stressing words (containing prone lowercase letters) but selection is by frequency
    # so the set is a realistic common-word sample, not cherry-picked.
    prone = {sym for grp in HOMOGLYPH_GROUPS for sym in grp if sym.islower()}
    cand = [(w, brown[w]) for w in brown
            if w.isalpha() and w.islower() and WORD_MIN_LEN <= len(w) <= WORD_MAX_LEN and w in lex]
    cand.sort(key=lambda x: -x[1])
    top = [w for w, _ in cand[:2000]]
    rng = np.random.default_rng(WORD_SELECT_SEED)
    # take the most-frequent N, but ensure >= 60% contain a homoglyph-prone letter (they nearly
    # all do -- reported, not forced beyond the natural rate).
    words = top[:N_WORDS]
    n_prone = sum(any(ch in prone for ch in w) for w in words)
    print(f"  test words: {len(words)}  (min freq in set = {brown[words[-1]]})  "
          f"containing a homoglyph-prone lowercase letter: {n_prone}/{len(words)} "
          f"({100*n_prone/len(words):.0f}%)")
    print(f"  sample words: {words[:20]}")

    out = {"lexicon": sorted(lex), "logfreq": logfreq,
           "bigram": {f"{a}|{b}": c for (a, b), c in bigram.items()},
           "unigram": dict(unigram), "words": words,
           "n_prone_words": n_prone, "brown_total": total,
           "stroke_shapes_md5": md5_before}
    _save_json(out, _ckpt("lexicon.json"))
    _seed_guard("build_lexicon", md5_before)
    print(f"  saved -> {_ckpt('lexicon.json')}  [build_lexicon {time.time()-t0:.1f}s]")
    return 0


def _require_lexicon() -> dict:
    p = _ckpt("lexicon.json")
    if not os.path.exists(p):
        raise SystemExit("WALL: run --stage build_lexicon first.")
    return _load_json(p)


# ============================================================================================= #
#  STAGE: bank -- cross-writer exemplar bank (M per class from BACKGROUND writers).
# ============================================================================================= #
def stage_bank():
    print(f"\n{SEP}\n  STAGE: bank (cross-writer exemplar bank, {BANK_M}/class from BACKGROUND "
          f"writers)\n{SEP}")
    t0 = time.time()
    md5_before = _seed_guard("bank")
    from domains import pen_world as pw
    samples = pw.load_digilets_samples()
    background, heldout = pw.digilets_writer_split(samples, n_background=N_BACKGROUND_WRITERS,
                                                   seed=WRITER_SPLIT_SEED)
    bg_writers = sorted({s["writer_id"] for s in background})
    ho_writers = sorted({s["writer_id"] for s in heldout})
    print(f"  n_bank_writers={len(bg_writers)}  n_word_writers={len(ho_writers)}  "
          f"disjoint={set(bg_writers).isdisjoint(ho_writers)}")

    by_class = defaultdict(list)
    for s in background:
        by_class[s["class"]].append(s)
    rng = np.random.default_rng(BANK_SEED)
    bank = {}          # class -> list of (writer_id, instance) identity for reproducibility
    for c in range(62):
        insts = by_class[c]
        idx = rng.choice(len(insts), size=min(BANK_M, len(insts)), replace=False)
        bank[c] = [{"writer_id": insts[int(i)]["writer_id"], "instance": insts[int(i)]["instance"]}
                   for i in idx]
    n_ent = sum(len(v) for v in bank.values())
    print(f"  bank entries: {n_ent} (target {62*BANK_M})  [{time.time()-t0:.1f}s]")

    out = {"bank": {str(c): bank[c] for c in range(62)},
           "bank_writers": bg_writers, "word_writers": ho_writers,
           "stroke_shapes_md5": md5_before}
    _save_json(out, _ckpt("bank.json"))
    _seed_guard("bank", md5_before)
    print(f"  saved -> {_ckpt('bank.json')}  [bank {time.time()-t0:.1f}s]")
    return 0


def _require_bank() -> dict:
    p = _ckpt("bank.json")
    if not os.path.exists(p):
        raise SystemExit("WALL: run --stage bank first.")
    return _load_json(p)


# ------------------------------------------------------------------------------------------- #
# Composition + recognition helpers (importable; reused by tests).
# ------------------------------------------------------------------------------------------- #
def _index_by_writer_class(samples: list) -> dict:
    idx: dict = {}
    for s in samples:
        idx.setdefault(s["writer_id"], {}).setdefault(s["class"], []).append(s)
    return idx


def compose_word(word: str, writer_id: str, wc_index: dict, rng) -> list:
    """Compose a word as a SEQUENCE of real DigiLeTs lowercase glyph instances, all from ONE
    held-out writer. Returns a list of {sym, class, strokes} per character. Pre-segmented (no
    cursive join); word length known. Mechanical -- no decision."""
    out = []
    for ch in word:
        c = _lower_class(ch)
        insts = wc_index[writer_id][c]
        s = insts[int(rng.integers(0, len(insts)))]
        out.append({"sym": ch, "class": c, "strokes": s["strokes"], "instance": s["instance"]})
    return out


def char_distance_vector(query_pointsets, bank_pointsets) -> list:
    """Per-class distance vector over all 62 classes: dist_c = min over class c's bank exemplars of
    `program_score(query, exemplar)` (LOWER = better). The visual posterior with its uncertainty."""
    import scripts.jabberwock_omniglot_run47_pendata as run47
    dists = []
    for c in range(62):
        best = math.inf
        for ps in bank_pointsets[c]:
            if not ps:
                continue
            sc = run47.ps.program_score(query_pointsets, ps)
            if sc < best:
                best = sc
        dists.append(float(best if best != math.inf else 1e6))
    return dists


# ============================================================================================= #
#  STAGE: recognize -- compose words, per-char 62-class distance vectors. THE expensive stage.
# ============================================================================================= #
def stage_recognize():
    print(f"\n{SEP}\n  STAGE: recognize (compose words + per-char 62-class geometry distances)\n{SEP}")
    t0 = time.time()
    md5_before = _seed_guard("recognize")
    import scripts.jabberwock_omniglot_run47_pendata as run47
    from domains import pen_world as pw

    lex = _require_lexicon()
    bankspec = _require_bank()
    words = lex["words"]
    word_writers = bankspec["word_writers"]

    samples = pw.load_digilets_samples()
    by_wi = {(s["writer_id"], s["instance"], s["class"]): s for s in samples}
    wc_index = _index_by_writer_class([s for s in samples if s["writer_id"] in set(word_writers)])

    # Bank point-sets (precompute once).
    bank_ps = {}
    for c in range(62):
        entries = bankspec["bank"][str(c)]
        pss = []
        for e in entries:
            s = by_wi[(e["writer_id"], e["instance"], c)]
            pss.append(run47._stroke_point_sets_from_arrays(s["strokes"]))
        bank_ps[c] = pss

    # Resume support: load any partial lattice.
    lat_path = _ckpt("lattices.json")
    done = {}
    if os.path.exists(lat_path):
        prev = _load_json(lat_path)
        if prev.get("bank_md5") == bankspec["stroke_shapes_md5"]:
            done = {d["word"]: d for d in prev.get("lattices", [])}
            print(f"  resuming: {len(done)} words already recognized")

    rng = np.random.default_rng(WORD_WRITER_SEED)
    lattices = []
    n_new = 0
    for wi, word in enumerate(words):
        if word in done:
            lattices.append(done[word])
            continue
        writer = word_writers[int(rng.integers(0, len(word_writers)))]
        chars = compose_word(word, writer, wc_index, rng)
        char_dists = []
        for ch in chars:
            q = run47._stroke_point_sets_from_arrays(ch["strokes"])
            char_dists.append(char_distance_vector(q, bank_ps))
        lattices.append({"word": word, "writer": writer,
                         "true_classes": [ch["class"] for ch in chars],
                         "dists": char_dists})
        n_new += 1
        if n_new % 25 == 0:
            print(f"    ... recognized {wi+1}/{len(words)} words  [{time.time()-t0:.1f}s]",
                  flush=True)
            _save_json({"bank_md5": bankspec["stroke_shapes_md5"], "lattices": lattices,
                        "partial": True}, lat_path)
            _seed_guard("recognize", md5_before)

    _save_json({"bank_md5": bankspec["stroke_shapes_md5"], "lattices": lattices,
                "partial": False}, lat_path)
    _seed_guard("recognize", md5_before)
    print(f"  recognized {len(lattices)} words ({n_new} new)  [{time.time()-t0:.1f}s]")
    print(f"  saved -> {lat_path}")
    return 0


def _require_lattices() -> dict:
    p = _ckpt("lattices.json")
    if not os.path.exists(p):
        raise SystemExit("WALL: run --stage recognize first.")
    d = _load_json(p)
    if d.get("partial"):
        raise SystemExit("WALL: recognize incomplete (partial lattices). Re-run --stage recognize.")
    return d


# ============================================================================================= #
#  DECODERS (pure, importable, reused by tests).
# ============================================================================================= #
def decode_no_context(dists: list, symbols: list) -> str:
    """Per-position argmin over all 62 classes -> predicted symbol string."""
    return "".join(symbols[int(np.argmin(d))] for d in dists)


def decode_lexicon(dists: list, true_len: int, lex_by_len: dict, logfreq: dict,
                   alpha: float) -> str:
    """WITH-CONTEXT: over LEXICON words of the SAME length, choose the one MINIMIZING summed
    per-char distance (- alpha * logfreq, i.e. + alpha*(-logfreq) as a cost). The lexicon is
    lowercase -> the decode is constrained to lowercase sequences -> homoglyphs resolve."""
    cands = lex_by_len.get(true_len, [])
    if not cands:
        return ""
    D = np.asarray(dists)                       # (L, 62)
    best_w, best_cost = "", math.inf
    for w in cands:
        cls = [_lower_class(ch) for ch in w]
        cost = float(sum(D[i, cls[i]] for i in range(true_len)))
        if alpha:
            cost -= alpha * logfreq.get(w, math.log(1.0 / (len(cands) + 1)))
        if cost < best_cost:
            best_cost, best_w = cost, w
    return best_w


def decode_char_bigram(dists: list, symbols: list, log_trans, beta: float) -> str:
    """WITH-CONTEXT (open-vocab char-bigram LM): Viterbi over 62 classes with a Brown character-
    bigram transition. Emission = -dist (converted to a log-score via -beta*dist). No lexicon.
    `log_trans(prev_sym, cur_sym)` returns a bigram log-prob (prev='^' at the start)."""
    L = len(dists)
    lower_syms = [symbols[c] for c in range(62)]
    # emission log-score per class = -beta * dist.
    emis = [[-beta * dists[i][c] for c in range(62)] for i in range(L)]
    # Viterbi.
    prev_score = [emis[0][c] + log_trans("^", lower_syms[c]) for c in range(62)]
    prev_bp = [[0] * 62 for _ in range(L)]
    for i in range(1, L):
        cur = [-math.inf] * 62
        for c in range(62):
            best_p, best_s = 0, -math.inf
            for p in range(62):
                s = prev_score[p] + log_trans(lower_syms[p], lower_syms[c])
                if s > best_s:
                    best_s, best_p = s, p
            cur[c] = best_s + emis[i][c]
            prev_bp[i][c] = best_p
        prev_score = cur
    # backtrace (+ end boundary).
    end = [prev_score[c] + log_trans(lower_syms[c], "$") for c in range(62)]
    last = int(np.argmax(end))
    seq = [last]
    for i in range(L - 1, 0, -1):
        last = prev_bp[i][last]
        seq.append(last)
    seq.reverse()
    return "".join(lower_syms[c] for c in seq)


# ============================================================================================= #
#  STAGE: decode -- run both readers, compute the table + homoglyph resolution.
# ============================================================================================= #
def _lex_by_len(lexicon: list) -> dict:
    d = defaultdict(list)
    for w in lexicon:
        d[len(w)].append(w)
    return d


def _make_log_trans(bigram: dict, unigram: dict):
    V = 28  # 26 letters + ^ + $
    def lt(a: str, b: str) -> float:
        num = bigram.get(f"{a}|{b}", 0) + 1
        den = unigram.get(a, 0) + V
        return math.log(num / den)
    return lt


def _char_acc(pred: str, true: str) -> tuple:
    n = min(len(pred), len(true))
    correct = sum(1 for i in range(n) if pred[i] == true[i])
    return correct, len(true)


def stage_decode():
    print(f"\n{SEP}\n  STAGE: decode (NO-CONTEXT vs WITH-CONTEXT readers)\n{SEP}")
    t0 = time.time()
    md5_before = _seed_guard("decode")
    symbols, _ = _sym_maps()
    lex = _require_lexicon()
    lat = _require_lattices()
    lexicon = lex["lexicon"]
    logfreq = lex["logfreq"]
    lex_by_len = _lex_by_len(lexicon)
    log_trans = _make_log_trans(lex["bigram"], lex["unigram"])

    per_word = []
    # accumulators
    nc_word_ok = lx_word_ok = lxf_word_ok = bi_word_ok = 0
    nc_char_ok = lx_char_ok = lxf_char_ok = bi_char_ok = 0
    n_char_total = 0
    homo_errs = 0            # NO-CONTEXT char errors that are homoglyph confusions
    homo_resolved_lx = 0     # of those, lexicon (flat) gets right
    homo_resolved_bi = 0
    nc_correct_flags, lx_correct_flags, bi_correct_flags = [], [], []

    for L in lat["lattices"]:
        word = L["word"]
        dists = L["dists"]
        tl = len(word)
        nc = decode_no_context(dists, symbols)
        lx = decode_lexicon(dists, tl, lex_by_len, logfreq, FREQ_PRIOR_ALPHA)
        lxf = decode_lexicon(dists, tl, lex_by_len, logfreq, FREQ_PRIOR_ALPHA_WEIGHTED)
        bi = decode_char_bigram(dists, symbols, log_trans, beta=1.0)

        nc_word_ok += (nc == word); lx_word_ok += (lx == word)
        lxf_word_ok += (lxf == word); bi_word_ok += (bi == word)
        nc_correct_flags.append(nc == word)
        lx_correct_flags.append(lx == word)
        bi_correct_flags.append(bi == word)

        cnc, tot = _char_acc(nc, word); clx, _ = _char_acc(lx, word)
        clxf, _ = _char_acc(lxf, word); cbi, _ = _char_acc(bi, word)
        nc_char_ok += cnc; lx_char_ok += clx; lxf_char_ok += clxf; bi_char_ok += cbi
        n_char_total += tot

        # homoglyph resolution accounting (per char position).
        for i, ch in enumerate(word):
            if i < len(nc) and nc[i] != ch and _is_homoglyph_pair(ch, nc[i]):
                homo_errs += 1
                if i < len(lx) and lx[i] == ch:
                    homo_resolved_lx += 1
                if i < len(bi) and bi[i] == ch:
                    homo_resolved_bi += 1

        per_word.append({"word": word, "writer": L["writer"], "nc": nc, "lx": lx,
                         "lxf": lxf, "bi": bi})

    n = len(lat["lattices"])
    def acc(k, tot): return k / tot if tot else 0.0
    rep = {
        "n_words": n, "n_chars": n_char_total,
        "no_context": {"word_acc": acc(nc_word_ok, n), "word_ci": list(_wilson_ci(nc_word_ok, n)),
                       "char_acc": acc(nc_char_ok, n_char_total), "word_correct": nc_word_ok},
        "lexicon_flat": {"word_acc": acc(lx_word_ok, n), "word_ci": list(_wilson_ci(lx_word_ok, n)),
                         "char_acc": acc(lx_char_ok, n_char_total), "word_correct": lx_word_ok},
        "lexicon_freq": {"word_acc": acc(lxf_word_ok, n), "word_ci": list(_wilson_ci(lxf_word_ok, n)),
                         "char_acc": acc(lxf_char_ok, n_char_total), "word_correct": lxf_word_ok},
        "char_bigram_lm": {"word_acc": acc(bi_word_ok, n), "word_ci": list(_wilson_ci(bi_word_ok, n)),
                           "char_acc": acc(bi_char_ok, n_char_total), "word_correct": bi_word_ok},
        "homoglyph": {"nc_homoglyph_char_errors": homo_errs,
                      "resolved_by_lexicon_flat": homo_resolved_lx,
                      "resolved_by_char_bigram": homo_resolved_bi,
                      "frac_resolved_lexicon": (homo_resolved_lx / homo_errs) if homo_errs else 0.0,
                      "frac_resolved_bigram": (homo_resolved_bi / homo_errs) if homo_errs else 0.0},
        "mcnemar_lexicon_vs_nocontext": _mcnemar(nc_correct_flags, lx_correct_flags),
        "mcnemar_bigram_vs_nocontext": _mcnemar(nc_correct_flags, bi_correct_flags),
    }
    # WIN verdict (pre-registered).
    nc_wa = rep["no_context"]["word_acc"]; lx_wa = rep["lexicon_flat"]["word_acc"]
    ratio = (lx_wa / nc_wa) if nc_wa > 0 else math.inf
    frac_res = rep["homoglyph"]["frac_resolved_lexicon"]
    rep["verdict"] = {
        "word_acc_ratio": ratio, "word_acc_ratio_bar": WIN_WORD_ACC_RATIO,
        "homoglyph_resolved": frac_res, "homoglyph_resolved_bar": WIN_HOMOGLYPH_RESOLVED,
        "win": bool(ratio >= WIN_WORD_ACC_RATIO and frac_res >= WIN_HOMOGLYPH_RESOLVED),
    }
    _save_json({"report": rep, "per_word": per_word}, _ckpt("decode.json"))
    _seed_guard("decode", md5_before)
    _print_decode(rep)
    print(f"  saved -> {_ckpt('decode.json')}  [decode {time.time()-t0:.1f}s]")
    return 0


def _print_decode(rep: dict) -> None:
    print(f"\n  === WORD + CHARACTER ACCURACY (n_words={rep['n_words']}, "
          f"n_chars={rep['n_chars']}) ===")
    hdr = f"  {'reader':<26}{'word_acc':>12}{'word_CI':>18}{'char_acc':>12}"
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for key, lab in (("no_context", "(A) NO-CONTEXT"),
                     ("lexicon_flat", "(B) LEXICON (flat)"),
                     ("lexicon_freq", "(B) LEXICON (+freq)"),
                     ("char_bigram_lm", "(B') char-bigram LM")):
        r = rep[key]
        ci = f"[{100*r['word_ci'][0]:.1f},{100*r['word_ci'][1]:.1f}]"
        print(f"  {lab:<26}{100*r['word_acc']:>10.1f}%{ci:>18}{100*r['char_acc']:>10.1f}%")
    h = rep["homoglyph"]
    print(f"\n  HOMOGLYPH RESOLUTION: of {h['nc_homoglyph_char_errors']} NO-CONTEXT homoglyph "
          f"char-errors,")
    print(f"    lexicon(flat) resolves {h['resolved_by_lexicon_flat']} "
          f"({100*h['frac_resolved_lexicon']:.1f}%);  "
          f"char-bigram resolves {h['resolved_by_char_bigram']} "
          f"({100*h['frac_resolved_bigram']:.1f}%)")
    mlx, mbi = rep["mcnemar_lexicon_vs_nocontext"], rep["mcnemar_bigram_vs_nocontext"]
    print(f"  McNemar lexicon vs no-context: fixed={mlx['fixed']} broken={mlx['broken']} "
          f"p={mlx['p']:.3g}")
    print(f"  McNemar bigram  vs no-context: fixed={mbi['fixed']} broken={mbi['broken']} "
          f"p={mbi['p']:.3g}")
    v = rep["verdict"]
    print(f"\n  VERDICT (pre-registered: word_acc ratio >= {v['word_acc_ratio_bar']}x AND "
          f">= {100*v['homoglyph_resolved_bar']:.0f}% homoglyph resolved):")
    print(f"    word_acc ratio (lexicon/no-context) = {v['word_acc_ratio']:.2f}x  "
          f"(bar {v['word_acc_ratio_bar']}x)")
    print(f"    homoglyph resolved = {100*v['homoglyph_resolved']:.1f}%  "
          f"(bar {100*v['homoglyph_resolved_bar']:.0f}%)")
    print(f"    -> {'WIN: language context closes the reading gap' if v['win'] else 'NULL'}")


def _require_decode() -> dict:
    p = _ckpt("decode.json")
    if not os.path.exists(p):
        raise SystemExit("WALL: run --stage decode first.")
    return _load_json(p)


# ============================================================================================= #
#  STAGE: summary
# ============================================================================================= #
def stage_summary():
    print(f"\n{SEP}\n  STAGE: summary -- RUN 61 SCOREBOARD (LANGUAGE-CONTEXT WORD READING)\n{SEP}")
    md5_now = _seed_guard("summary")
    lex = _require_lexicon()
    dec = _require_decode()
    print(f"\n  SEED-GUARD: seeds/stroke_shapes.json md5 = {md5_now}  "
          f"(== build_lexicon capture {lex['stroke_shapes_md5']}: "
          f"{md5_now == lex['stroke_shapes_md5']})")
    _print_decode(dec["report"])
    # a few illustrative homoglyph rescues
    print(f"\n  ILLUSTRATIVE RESCUES (NO-CONTEXT vs LEXICON):")
    shown = 0
    for pw in dec["per_word"]:
        if pw["nc"] != pw["word"] and pw["lx"] == pw["word"]:
            print(f"    {pw['word']:<10}  no-context='{pw['nc']}'  ->  lexicon='{pw['lx']}'")
            shown += 1
            if shown >= 12:
                break
    print(f"\n{SEP}\n  RUN 61 COMPLETE -- see final agent report.\n{SEP}")
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", required=True,
                   choices=["build_lexicon", "bank", "recognize", "decode", "summary"])
    args = p.parse_args()
    fn = {"build_lexicon": stage_build_lexicon, "bank": stage_bank, "recognize": stage_recognize,
          "decode": stage_decode, "summary": stage_summary}[args.stage]
    return fn()


if __name__ == "__main__":
    sys.exit(main())
